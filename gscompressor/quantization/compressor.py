import os
import platform
import subprocess
import tempfile
from plyfile import PlyData, PlyElement
import numpy as np
import torch
from gaussian_splatting import GaussianModel
from reduced_3dgs.quantization import VectorQuantizer

default_encoder_executable = os.path.join(os.path.dirname(__file__), "draco_encoder") + (".exe" if platform.system() == "Windows" else "")
default_decoder_executable = os.path.join(os.path.dirname(__file__), "draco_decoder") + (".exe" if platform.system() == "Windows" else "")


class VectorQuantizationCompressor:
    def __init__(
        self,
        quantizer: VectorQuantizer,
        encoder_executable: str = None,
        decoder_executable: str = None,
        compression_level: int = 0,
        qposition=30,
        qscale=30,
        qrotation=30,
        qopacity=30,
        qfeaturedc=30,
        qfeaturesrest=30,
    ):
        self.quantizer = quantizer
        if encoder_executable is None:
            encoder_executable = default_encoder_executable
        if decoder_executable is None:
            decoder_executable = default_decoder_executable
        self.encoder_executable = encoder_executable
        self.decoder_executable = decoder_executable
        self.compression_level = compression_level
        self.qposition = qposition
        self.qscale = qscale
        self.qrotation = qrotation
        self.qopacity = qopacity
        self.qfeaturedc = qfeaturedc
        self.qfeaturesrest = qfeaturesrest

    def save_compressed(self, model: GaussianModel, path: str):
        ids_dict, codebook_dict = self.quantizer.quantize(model, update_codebook=False)
        dtype_full = self.quantizer.ply_dtype(model.max_sh_degree)
        data_full = self.quantizer.ply_data(model, ids_dict)
        dtype_rot = max([dtype for name, dtype in dtype_full if name in ['rot_re', 'rot_im']])
        for i in range(len(dtype_full)):
            if dtype_full[i][0] in ['rot_re', 'rot_im']:
                dtype_full[i] = (dtype_full[i][0], dtype_rot)

        elements = np.rec.fromarrays([data.squeeze(-1) for data in data_full], dtype=dtype_full)
        el = PlyElement.describe(elements, 'vertex')

        with tempfile.TemporaryDirectory() as temp_dir:
            ply_path = os.path.join(temp_dir, "point_cloud.ply")
            PlyData([el]).write(ply_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            subprocess.check_call([
                self.encoder_executable,
                "-i", ply_path, "-o", path,
                "-cl", str(self.compression_level),
                "-qp", str(self.qposition),
                "-qscale", str(self.qscale),
                "-qrotation", str(self.qrotation),
                "-qopacity", str(self.qopacity),
                "-qfeaturedc", str(self.qfeaturedc),
                "-qfeaturerest", str(self.qfeaturesrest),
            ])

        np.savez(
            os.path.join(os.path.splitext(path)[0] + ".codebook.npz"),
            **codebook_dict
        )

    def load_compressed(self, model: GaussianModel, path: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            ply_path = os.path.join(temp_dir, "point_cloud.ply")
            subprocess.check_call([
                self.decoder_executable,
                "-i", path, "-o", ply_path
            ])
            plydata = PlyData.read(ply_path)
            ids_dict = self.quantizer.parse_ids(plydata, model.max_sh_degree, model._xyz.device)
            kwargs = dict(dtype=torch.float32, device=model._xyz.device)
            codebook_dict = {name: torch.tensor(array, **kwargs) for name, array in np.load(os.path.splitext(path)[0] + ".codebook.npz").items()}
            xyz = self.quantizer.parse_xyz(plydata, model._xyz.device)
            self._codebook_dict = codebook_dict
            del plydata
            return self.quantizer.dequantize(model, ids_dict, codebook_dict, xyz=xyz, replace=True)
