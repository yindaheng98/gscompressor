#ifndef __DRACOREDUCED3DGS_H__
#define __DRACOREDUCED3DGS_H__

#include <vector>
#include <cstddef>
#include <cstring>
#include <iostream>
#include "draco/compression/decode.h"
#include "draco/compression/encode.h"
#include "draco/point_cloud/point_cloud.h"

namespace DracoReduced3DGS
{

    enum decoding_status
    {
        successful,
        not_draco_encoded,
        failed_during_decoding
    };
    enum encoding_status
    {
        successful_encoding,
        failed_during_encoding
    };

    // Reduced 3DGS attribute dimensions (fixed)
    constexpr int DIM_POSITION = 3;
    constexpr int DIM_SCALE = 1;
    constexpr int DIM_ROTATION = 2;
    constexpr int DIM_OPACITY = 1;
    constexpr int DIM_FEATURE_DC = 1;
    constexpr int DIM_FEATURE_REST = 9;

    struct PointCloudObject
    {
        std::vector<float> positions;
        std::vector<int32_t> scales;
        std::vector<int32_t> rotations;
        std::vector<int32_t> opacities;
        std::vector<int32_t> features_dc;
        std::vector<int32_t> features_rest;
        int num_points;
        decoding_status decode_status;
    };

    struct EncodedObject
    {
        std::vector<unsigned char> buffer;
        encoding_status encode_status;
    };

    // Extract attribute data from PointCloud to vector using memcpy (bulk copy)
    // Reference: ply_encoder.cc EncodeData() - uses GetAddress for direct memory access
    template <typename T, int N>
    void extract_attr(draco::PointCloud *pc, draco::GeometryAttribute::Type type, std::vector<T> &out, int num_points)
    {
        const int att_id = pc->GetNamedAttributeId(type);
        if (att_id < 0)
            return;
        const auto *att = pc->attribute(att_id);
        out.resize(num_points * N);
        // Use bulk memcpy when identity mapping (data is contiguous)
        // Reference: geometry_attribute.h GetAddress() returns pointer to contiguous buffer
        if (att->is_mapping_identity())
        {
            std::memcpy(out.data(), att->GetAddress(draco::AttributeValueIndex(0)), num_points * N * sizeof(T));
        }
        else
        {
            // Fallback to per-point copy for non-identity mapping
            for (draco::PointIndex i(0); i < num_points; ++i)
            {
                std::memcpy(&out[i.value() * N], att->GetAddress(att->mapped_index(i)), N * sizeof(T));
            }
        }
    }

    // Add attribute to PointCloud from vector using memcpy (bulk copy)
    // Reference: ply_decoder.cc ReadNamedPropertiesByNameToAttribute()
    template <typename T>
    int add_attr(draco::PointCloud *pc, draco::GeometryAttribute::Type type, const std::vector<T> &data, int num_components, int num_points, draco::DataType dt)
    {
        if (data.empty())
            return -1;
        // Reference: ply_decoder.cc line 178-181
        draco::GeometryAttribute va;
        va.Init(type, nullptr, num_components, dt, false, draco::DataTypeLength(dt) * num_components, 0);
        const int att_id = pc->AddAttribute(va, true, num_points);
        // Bulk copy using memcpy - attribute buffer is contiguous after AddAttribute with identity mapping
        // Reference: geometry_attribute.h SetAttributeValue() writes to byte_pos = index * byte_stride
        std::memcpy(pc->attribute(att_id)->GetAddress(draco::AttributeValueIndex(0)), data.data(), data.size() * sizeof(T));
        return att_id;
    }

    PointCloudObject decode_point_cloud(const char *buffer, std::size_t buffer_len)
    {
        PointCloudObject obj;
        draco::DecoderBuffer decoderBuffer;
        decoderBuffer.Init(buffer, buffer_len);

        // Reference: draco_decoder.cc line 89-93
        auto type_statusor = draco::Decoder::GetEncodedGeometryType(&decoderBuffer);
        if (!type_statusor.ok())
        {
            obj.decode_status = not_draco_encoded;
            return obj;
        }

        // Reference: draco_decoder.cc line 110-116
        draco::Decoder decoder;
        auto statusor = decoder.DecodePointCloudFromBuffer(&decoderBuffer);
        if (!statusor.ok())
        {
            obj.decode_status = failed_during_decoding;
            return obj;
        }

        auto pc = std::move(statusor).value();
        obj.num_points = pc->num_points();

        extract_attr<float, DIM_POSITION>(pc.get(), draco::GeometryAttribute::POSITION, obj.positions, obj.num_points);
        extract_attr<int32_t, DIM_SCALE>(pc.get(), draco::GeometryAttribute::SCALE_3DGS, obj.scales, obj.num_points);
        extract_attr<int32_t, DIM_ROTATION>(pc.get(), draco::GeometryAttribute::ROTATION_3DGS, obj.rotations, obj.num_points);
        extract_attr<int32_t, DIM_OPACITY>(pc.get(), draco::GeometryAttribute::OPACITY_3DGS, obj.opacities, obj.num_points);
        extract_attr<int32_t, DIM_FEATURE_DC>(pc.get(), draco::GeometryAttribute::FEATURE_DC_3DGS, obj.features_dc, obj.num_points);
        extract_attr<int32_t, DIM_FEATURE_REST>(pc.get(), draco::GeometryAttribute::FEATURE_REST_3DGS, obj.features_rest, obj.num_points);

        obj.decode_status = successful;
        return obj;
    }

    EncodedObject encode_point_cloud(
        const std::vector<float> &positions,
        const std::vector<int32_t> &scales,
        const std::vector<int32_t> &rotations,
        const std::vector<int32_t> &opacities,
        const std::vector<int32_t> &features_dc,
        const std::vector<int32_t> &features_rest,
        int compression_level,
        int qp, int qscale, int qrotation, int qopacity, int qfeaturedc, int qfeaturerest)
    {
        EncodedObject result;
        const int num_points = positions.size() / DIM_POSITION;
        const int speed = 10 - compression_level;

        // Reference: ply_decoder.cc line 279-280
        draco::PointCloud pc;
        pc.set_num_points(num_points);

        // Add attributes - Reference: ply_decoder.cc DecodeVertexData()
        add_attr<float>(&pc, draco::GeometryAttribute::POSITION, positions, DIM_POSITION, num_points, draco::DT_FLOAT32);
        add_attr<int32_t>(&pc, draco::GeometryAttribute::SCALE_3DGS, scales, DIM_SCALE, num_points, draco::DT_INT32);
        add_attr<int32_t>(&pc, draco::GeometryAttribute::ROTATION_3DGS, rotations, DIM_ROTATION, num_points, draco::DT_INT32);
        add_attr<int32_t>(&pc, draco::GeometryAttribute::OPACITY_3DGS, opacities, DIM_OPACITY, num_points, draco::DT_INT32);
        add_attr<int32_t>(&pc, draco::GeometryAttribute::FEATURE_DC_3DGS, features_dc, DIM_FEATURE_DC, num_points, draco::DT_INT32);
        add_attr<int32_t>(&pc, draco::GeometryAttribute::FEATURE_REST_3DGS, features_rest, DIM_FEATURE_REST, num_points, draco::DT_INT32);

        // Reference: draco_encoder.cc line 390-429
        draco::Encoder encoder;
        encoder.SetSpeedOptions(speed, speed);
        if (qp > 0)
            encoder.SetAttributeQuantization(draco::GeometryAttribute::POSITION, qp);
        if (qscale > 0)
            encoder.SetAttributeQuantization(draco::GeometryAttribute::SCALE_3DGS, qscale);
        if (qrotation > 0)
            encoder.SetAttributeQuantization(draco::GeometryAttribute::ROTATION_3DGS, qrotation);
        if (qopacity > 0)
            encoder.SetAttributeQuantization(draco::GeometryAttribute::OPACITY_3DGS, qopacity);
        if (qfeaturedc > 0)
            encoder.SetAttributeQuantization(draco::GeometryAttribute::FEATURE_DC_3DGS, qfeaturedc);
        if (qfeaturerest > 0)
            encoder.SetAttributeQuantization(draco::GeometryAttribute::FEATURE_REST_3DGS, qfeaturerest);

        // Reference: draco_encoder.cc EncodePointCloudToFile() line 163-170
        draco::EncoderBuffer buffer;
        const draco::Status status = encoder.EncodePointCloudToBuffer(pc, &buffer);

        if (status.ok())
        {
            result.buffer = *reinterpret_cast<const std::vector<unsigned char> *>(buffer.buffer());
            result.encode_status = successful_encoding;
        }
        else
        {
            std::cerr << "Draco encoding error: " << status.error_msg_string() << std::endl;
            result.encode_status = failed_during_encoding;
        }

        return result;
    }

} // namespace DracoReduced3DGS

#endif
