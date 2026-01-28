import os
import platform
import tempfile
import subprocess

import torch
from gaussian_splatting import GaussianModel

from . import draco3dgs

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
        qfeaturerest=30,
        use_executable_backend: bool = False,
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
        self.qfeaturerest = qfeaturerest
        self.use_executable_backend = use_executable_backend

    def save_compressed(self, path: str):
        if self.use_executable_backend:
            self._save_compressed_executable(path)
        else:
            self._save_compressed_pyd(path)

    def _save_compressed_executable(self, path: str):
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
                "-qfeaturerest", str(self.qfeaturerest),
            ])

    def _save_compressed_pyd(self, path: str):
        # Extract model attributes
        positions = self._model._xyz.detach().cpu().numpy()  # (N, 3)
        scales = self._model._scaling.detach().cpu().numpy()  # (N, 3)
        rotations = self._model._rotation.detach().cpu().numpy()  # (N, 4)
        opacities = self._model._opacity.detach().cpu().numpy()  # (N, 1)
        features_dc = self._model._features_dc.detach().cpu().numpy().reshape(-1, 3)  # (N, 1, 3) -> (N, 3)
        features_rest = self._model._features_rest.detach().cpu().numpy().reshape(-1, 45)  # (N, 15, 3) -> (N, 45)

        # Encode
        encoded = draco3dgs.encode(
            positions, scales, rotations, opacities, features_dc, features_rest,
            self.compression_level,
            self.qposition, self.qscale, self.qrotation,
            self.qopacity, self.qfeaturedc, self.qfeaturerest
        )

        # Write to file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(encoded)


class Decompressor:
    def __init__(
        self, model: GaussianModel,
        decoder_executable: str = None,
        use_executable_backend: bool = False,
    ):
        self._model = model
        if decoder_executable is None:
            decoder_executable = default_decoder_executable
        self.decoder_executable = decoder_executable
        self.use_executable_backend = use_executable_backend

    def load_compressed(self, path: str):
        if self.use_executable_backend:
            self._load_compressed_executable(path)
        else:
            self._load_compressed_pyd(path)

    def _load_compressed_executable(self, path: str):
        with tempfile.TemporaryDirectory() as temp_dir:
            ply_path = os.path.join(temp_dir, "point_cloud.ply")
            subprocess.check_call([
                self.decoder_executable,
                "-i", path, "-o", ply_path,
            ])
            self._model.load_ply(ply_path)

    def _load_compressed_pyd(self, path: str):
        # Read from file
        with open(path, 'rb') as f:
            buffer = f.read()

        # Decode
        pc = draco3dgs.decode(buffer)

        # Set model attributes
        device = self._model._xyz.device
        self._model._xyz = torch.nn.Parameter(torch.tensor(pc.positions, dtype=torch.float32, device=device))
        self._model._scaling = torch.nn.Parameter(torch.tensor(pc.scales, dtype=torch.float32, device=device))
        self._model._rotation = torch.nn.Parameter(torch.tensor(pc.rotations, dtype=torch.float32, device=device))
        self._model._opacity = torch.nn.Parameter(torch.tensor(pc.opacities, dtype=torch.float32, device=device))
        self._model._features_dc = torch.nn.Parameter(torch.tensor(pc.features_dc.reshape(-1, 1, 3), dtype=torch.float32, device=device))
        self._model._features_rest = torch.nn.Parameter(torch.tensor(pc.features_rest.reshape(-1, 15, 3), dtype=torch.float32, device=device))
