#ifndef __DRACO3DGS_H__
#define __DRACO3DGS_H__

#include <vector>
#include <cstddef>
#include <iostream>
#include "draco/compression/decode.h"
#include "draco/compression/encode.h"
#include "draco/core/encoder_buffer.h"
#include "draco/point_cloud/point_cloud_builder.h"

namespace Draco3DGS
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

    // 3DGS attribute dimensions (fixed)
    constexpr int DIM_POSITION = 3;
    constexpr int DIM_SCALE = 3;
    constexpr int DIM_ROTATION = 4;
    constexpr int DIM_OPACITY = 1;
    constexpr int DIM_FEATURE_DC = 3;
    constexpr int DIM_FEATURE_REST = 45; // SH degree 3: 15 coeffs * 3 channels

    struct PointCloudObject
    {
        std::vector<float> positions;     // Nx3
        std::vector<float> scales;        // Nx3
        std::vector<float> rotations;     // Nx4
        std::vector<float> opacities;     // Nx1
        std::vector<float> features_dc;   // Nx3
        std::vector<float> features_rest; // Nx45
        int num_points;
        decoding_status decode_status;
    };

    struct EncodedObject
    {
        std::vector<unsigned char> buffer;
        encoding_status encode_status;
    };

    template <int N>
    void extract_attr(draco::PointCloud *pc, draco::GeometryAttribute::Type type, std::vector<float> &out, int num_points)
    {
        const int att_id = pc->GetNamedAttributeId(type);
        if (att_id < 0)
            return;
        const auto *att = pc->attribute(att_id);
        out.resize(num_points * N);
        float values[N];
        for (draco::PointIndex i(0); i < num_points; ++i)
        {
            att->ConvertValue<float>(att->mapped_index(i), N, values);
            for (int c = 0; c < N; ++c)
            {
                out[i.value() * N + c] = values[c];
            }
        }
    }

    PointCloudObject decode_point_cloud(const char *buffer, std::size_t buffer_len)
    {
        PointCloudObject obj;
        draco::DecoderBuffer decoderBuffer;
        decoderBuffer.Init(buffer, buffer_len);

        auto type_statusor = draco::Decoder::GetEncodedGeometryType(&decoderBuffer);
        if (!type_statusor.ok())
        {
            obj.decode_status = not_draco_encoded;
            return obj;
        }

        draco::Decoder decoder;
        auto statusor = decoder.DecodePointCloudFromBuffer(&decoderBuffer);
        if (!statusor.ok())
        {
            obj.decode_status = failed_during_decoding;
            return obj;
        }

        auto pc = std::move(statusor).value();
        obj.num_points = pc->num_points();

        extract_attr<DIM_POSITION>(pc.get(), draco::GeometryAttribute::POSITION, obj.positions, obj.num_points);
        extract_attr<DIM_SCALE>(pc.get(), draco::GeometryAttribute::SCALE_3DGS, obj.scales, obj.num_points);
        extract_attr<DIM_ROTATION>(pc.get(), draco::GeometryAttribute::ROTATION_3DGS, obj.rotations, obj.num_points);
        extract_attr<DIM_OPACITY>(pc.get(), draco::GeometryAttribute::OPACITY_3DGS, obj.opacities, obj.num_points);
        extract_attr<DIM_FEATURE_DC>(pc.get(), draco::GeometryAttribute::FEATURE_DC_3DGS, obj.features_dc, obj.num_points);
        extract_attr<DIM_FEATURE_REST>(pc.get(), draco::GeometryAttribute::FEATURE_REST_3DGS, obj.features_rest, obj.num_points);

        obj.decode_status = successful;
        return obj;
    }

    template <int N>
    int add_attr(draco::PointCloudBuilder &pcb, draco::GeometryAttribute::Type type, const std::vector<float> &data, int num_points)
    {
        if (data.empty())
            return -1;
        const int id = pcb.AddAttribute(type, N, draco::DT_FLOAT32);
        for (draco::PointIndex i(0); i < num_points; ++i)
        {
            pcb.SetAttributeValueForPoint(id, i, &data[i.value() * N]);
        }
        return id;
    }

    EncodedObject encode_point_cloud(
        const std::vector<float> &positions,
        const std::vector<float> &scales,
        const std::vector<float> &rotations,
        const std::vector<float> &opacities,
        const std::vector<float> &features_dc,
        const std::vector<float> &features_rest,
        int compression_level,
        int qp, int qscale, int qrotation, int qopacity, int qfeaturedc, int qfeaturerest)
    {
        EncodedObject result;
        const int num_points = positions.size() / DIM_POSITION;
        const int speed = 10 - compression_level;

        draco::PointCloudBuilder pcb;
        pcb.Start(num_points);

        add_attr<DIM_POSITION>(pcb, draco::GeometryAttribute::POSITION, positions, num_points);
        add_attr<DIM_SCALE>(pcb, draco::GeometryAttribute::SCALE_3DGS, scales, num_points);
        add_attr<DIM_ROTATION>(pcb, draco::GeometryAttribute::ROTATION_3DGS, rotations, num_points);
        add_attr<DIM_OPACITY>(pcb, draco::GeometryAttribute::OPACITY_3DGS, opacities, num_points);
        add_attr<DIM_FEATURE_DC>(pcb, draco::GeometryAttribute::FEATURE_DC_3DGS, features_dc, num_points);
        add_attr<DIM_FEATURE_REST>(pcb, draco::GeometryAttribute::FEATURE_REST_3DGS, features_rest, num_points);

        auto pc = pcb.Finalize(true);

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

        draco::EncoderBuffer buffer;
        const draco::Status status = encoder.EncodePointCloudToBuffer(*pc, &buffer);

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

} // namespace Draco3DGS

#endif
