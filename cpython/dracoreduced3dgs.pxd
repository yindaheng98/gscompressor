# cython: language_level=3
from libcpp.vector cimport vector
from libc.stdint cimport int32_t


cdef extern from "dracoreduced3dgs.h" namespace "DracoReduced3DGS":

    cdef enum decoding_status:
        successful, not_draco_encoded, failed_during_decoding

    cdef enum encoding_status:
        successful_encoding, failed_during_encoding

    cdef struct PointCloudObject:
        vector[float] positions
        vector[int32_t] scales
        vector[int32_t] rotations
        vector[int32_t] opacities
        vector[int32_t] features_dc
        vector[int32_t] features_rest
        int num_points
        decoding_status decode_status

    cdef struct EncodedObject:
        vector[unsigned char] buffer
        encoding_status encode_status

    PointCloudObject decode_point_cloud(const char * buffer, size_t buffer_len) except +

    EncodedObject encode_point_cloud(
        const vector[float] & positions,
        const vector[int32_t] & scales,
        const vector[int32_t] & rotations,
        const vector[int32_t] & opacities,
        const vector[int32_t] & features_dc,
        const vector[int32_t] & features_rest,
        int compression_level,
        int qp, int qscale, int qrotation, int qopacity, int qfeaturedc, int qfeaturerest
    ) except +
