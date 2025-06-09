import os
import platform
import tempfile
import subprocess

from gaussian_splatting import GaussianModel

default_encoder_executable = os.path.join(os.path.dirname(__file__), "draco_encoder") + (".exe" if platform.system() == "Windows" else "")
default_decoder_executable = os.path.join(os.path.dirname(__file__), "draco_decoder") + (".exe" if platform.system() == "Windows" else "")


class Compressor:
    def __init__(
        self, model: GaussianModel,
        encoder_executable: str = None,
        compression_level: int = 0,
        qposition=30,
        qscale=30,
        qrotation=30,
        qopacity=30,
        qfeaturedc=30,
        qfeaturesrest=30,
    ):
        self._model = model
        if encoder_executable is None:
            encoder_executable = default_encoder_executable
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
        decoder_executable: str = None,
    ):
        self._model = model
        if decoder_executable is None:
            decoder_executable = default_decoder_executable
        self.decoder_executable = decoder_executable

    def load_compressed(self, path: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            ply_path = os.path.join(temp_dir, "point_cloud.ply")
            subprocess.check_call([
                self.decoder_executable,
                "-i", path, "-o", ply_path,
            ])
            self._model.load_ply(ply_path)
