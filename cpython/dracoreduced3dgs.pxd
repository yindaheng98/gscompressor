# cython: language_level=3
from libcpp.vector cimport vector

cdef extern from "dracoreduced3dgs.h" namespace "DracoReduced3DGS":

    cdef enum decoding_status:
        successful, not_draco_encoded, failed_during_decoding

    cdef enum encoding_status:
        successful_encoding, failed_during_encoding

    cdef struct PointCloudObject:
        vector[float] positions
        vector[float] scales
        vector[float] rotations
        vector[float] opacities
        vector[float] features_dc
        vector[float] features_rest
        int num_points
        decoding_status decode_status

    cdef struct EncodedObject:
        vector[unsigned char] buffer
        encoding_status encode_status

    PointCloudObject decode_point_cloud(const char * buffer, size_t buffer_len) except +

    EncodedObject encode_point_cloud(
        const vector[float] & positions,
        const vector[float] & scales,
        const vector[float] & rotations,
        const vector[float] & opacities,
        const vector[float] & features_dc,
        const vector[float] & features_rest,
        int compression_level,
        int qp, int qscale, int qrotation, int qopacity, int qfeaturedc, int qfeaturerest
    ) except +
