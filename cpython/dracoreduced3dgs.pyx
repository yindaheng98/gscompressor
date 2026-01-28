# distutils: language = c++
import numpy as np
from libcpp.vector cimport vector
cimport dracoreduced3dgs
cimport numpy as cnp
cnp.import_array()


class EncodingFailedException(Exception):
    pass


class DecodingFailedException(Exception):
    pass


class PointCloud:
    """Decoded reduced 3DGS point cloud data."""

    def __init__(self, positions, scales, rotations, opacities, features_dc, features_rest):
        self.positions = positions        # Nx3
        self.scales = scales              # Nx1
        self.rotations = rotations        # Nx4
        self.opacities = opacities        # Nx1
        self.features_dc = features_dc    # Nx1
        self.features_rest = features_rest  # Nx9

    @property
    def num_points(self):
        return len(self.positions)


def encode(
    positions not None,
    scales not None,
    rotations not None,
    opacities not None,
    features_dc not None,
    features_rest not None,
    int compression_level=7,
    int qp=11, int qscale=11, int qrotation=11,
    int qopacity=11, int qfeaturedc=11, int qfeaturerest=11
) -> bytes:
    """
    Encode reduced 3DGS point cloud to draco buffer.

    Args:
        positions: Nx3 float array
        scales: Nx1 float array
        rotations: Nx4 float array
        opacities: Nx1 float array
        features_dc: Nx1 float array
        features_rest: Nx9 float array
        compression_level: 0-10, higher = better compression
        qp, qscale, qrotation, qopacity, qfeaturedc, qfeaturerest: quantization bits

    Returns:
        Encoded bytes
    """
    cdef vector[float] pos_vec = np.asarray(positions, dtype=np.float32).ravel()
    cdef vector[float] scale_vec = np.asarray(scales, dtype=np.float32).ravel()
    cdef vector[float] rot_vec = np.asarray(rotations, dtype=np.float32).ravel()
    cdef vector[float] opacity_vec = np.asarray(opacities, dtype=np.float32).ravel()
    cdef vector[float] fdc_vec = np.asarray(features_dc, dtype=np.float32).ravel()
    cdef vector[float] frest_vec = np.asarray(features_rest, dtype=np.float32).ravel()

    encoded = dracoreduced3dgs.encode_point_cloud(
        pos_vec, scale_vec, rot_vec, opacity_vec, fdc_vec, frest_vec,
        compression_level, qp, qscale, qrotation, qopacity, qfeaturedc, qfeaturerest
    )

    if encoded.encode_status == dracoreduced3dgs.successful_encoding:
        return bytes(encoded.buffer)
    raise EncodingFailedException("Failed to encode point cloud")


def decode(bytes buffer) -> PointCloud:
    """
    Decode draco buffer to reduced 3DGS point cloud.

    Args:
        buffer: Encoded draco bytes

    Returns:
        PointCloud with positions(Nx3), scales(Nx1), rotations(Nx4), 
        opacities(Nx1), features_dc(Nx1), features_rest(Nx9)
    """
    obj = dracoreduced3dgs.decode_point_cloud(buffer, len(buffer))

    if obj.decode_status == dracoreduced3dgs.not_draco_encoded:
        raise DecodingFailedException("Input is not draco encoded")
    elif obj.decode_status == dracoreduced3dgs.failed_during_decoding:
        raise DecodingFailedException("Failed to decode buffer")

    n = obj.num_points
    return PointCloud(
        np.asarray(obj.positions).reshape(n, 3),
        np.asarray(obj.scales).reshape(n, 1),
        np.asarray(obj.rotations).reshape(n, 4),
        np.asarray(obj.opacities).reshape(n, 1),
        np.asarray(obj.features_dc).reshape(n, 1),
        np.asarray(obj.features_rest).reshape(n, 9),
    )
