import os
import platform
import tempfile
import subprocess

from gaussian_splatting import GaussianModel


class Compressor:
    def __init__(
        self, model: GaussianModel,
        encoder_executable: str = "./build-vanilla/Release/draco_encoder.exe" if platform.system() == "Windows" else "./build-vanilla/draco_encoder",
        compression_level: int = 0,
        qposition=16,
        qscale=16,
        qrotation=16,
        qopacity=16,
        qfeaturedc=16,
        qfeaturesrest=16,
    ):
        self._model = model
        self.encoder_executable = encoder_executable
        self.compression_level = compression_level
        self.qposition = qposition
        self.qscale = qscale
        self.qrotation = qrotation
        self.qopacity = qopacity
        self.qfeaturedc = qfeaturedc
        self.qfeaturesrest = qfeaturesrest

    def save_compressed(self, path: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            ply_path = os.path.join(temp_dir, "point_cloud.ply")
            self._model.save_ply(ply_path)
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


class Decompressor:
    def __init__(
        self, model: GaussianModel,
        decoder_executable: str = "./build-vanilla/Release/draco_decoder.exe" if platform.system() == "Windows" else "./build-vanilla/draco_decoder",
    ):
        self._model = model
        self.decoder_executable = decoder_executable

    def load_compressed(self, path: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            ply_path = os.path.join(temp_dir, "point_cloud.ply")
            subprocess.check_call([
                self.decoder_executable,
                "-i", path, "-o", ply_path,
            ])
            self._model.load_ply(ply_path)
