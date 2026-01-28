import os
import platform
import subprocess
import tempfile
from plyfile import PlyData, PlyElement
import numpy as np
import torch
from gaussian_splatting import GaussianModel
from reduced_3dgs.quantization import VectorQuantizer

from . import dracoreduced3dgs

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
        qfeaturerest=30,
        use_executable_backend: bool = False,
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
        self.qfeaturerest = qfeaturerest
        self.use_executable_backend = use_executable_backend

    def save_compressed(self, model: GaussianModel, path: str):
        if self.use_executable_backend:
            self._save_compressed_executable(model, path)
        else:
            self._save_compressed_pyd(model, path)

    def _save_compressed_executable(self, model: GaussianModel, path: str):
        ids_dict, codebook_dict = self.quantizer.quantize(model, update_codebook=False)
        dtype_full = self.quantizer.ply_dtype(model.max_sh_degree)
        data_full = self.quantizer.ply_data(model, ids_dict)
        dtype_rot = max([dtype for name, dtype in dtype_full if 'rot_' in name])
        for i in range(len(dtype_full)):
            if 'rot_' in dtype_full[i][0]:
                dtype_full[i] = (dtype_full[i][0], dtype_rot)
        dtype_f_rest = max([dtype for name, dtype in dtype_full if 'f_rest_' in name])
        for i in range(len(dtype_full)):
            if 'f_rest_' in dtype_full[i][0]:
                dtype_full[i] = (dtype_full[i][0], dtype_f_rest)

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
                "-qfeaturerest", str(self.qfeaturerest),
            ])

        np.savez(
            os.path.join(os.path.splitext(path)[0] + ".codebook.npz"),
            **{k: v.cpu().numpy() for k, v in codebook_dict.items()}
        )

    def _save_compressed_pyd(self, model: GaussianModel, path: str):
        ids_dict, codebook_dict = self.quantizer.quantize(model, update_codebook=False)

        # Extract model attributes (reduced 3DGS format) directly from model and ids_dict
        positions = model._xyz.detach().cpu().numpy().astype(np.float32)  # (N, 3)
        scales = ids_dict["scaling"].cpu().numpy().reshape(-1, 1).astype(np.float32)  # (N, 1)
        rotations = np.column_stack([
            ids_dict["rotation_re"].cpu().numpy(),
            ids_dict["rotation_im"].cpu().numpy()
        ]).astype(np.float32)  # (N, 2)
        opacities = ids_dict["opacity"].cpu().numpy().reshape(-1, 1).astype(np.float32)  # (N, 1)
        features_dc = ids_dict["features_dc"].cpu().numpy().reshape(-1, 1).astype(np.float32)  # (N, 1)
        # features_rest: combine all sh_degrees into (N, 9)
        features_rest_list = [ids_dict[f"features_rest_{sh_degree}"].cpu().numpy() for sh_degree in range(model.max_sh_degree)]
        features_rest = np.column_stack(features_rest_list).astype(np.float32)  # (N, 9)

        # Encode
        encoded = dracoreduced3dgs.encode(
            positions, scales, rotations, opacities, features_dc, features_rest,
            self.compression_level,
            self.qposition, self.qscale, self.qrotation,
            self.qopacity, self.qfeaturedc, self.qfeaturerest
        )

        # Write to file
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(encoded)

        np.savez(
            os.path.join(os.path.splitext(path)[0] + ".codebook.npz"),
            **{k: v.cpu().numpy() for k, v in codebook_dict.items()}
        )

    def load_compressed(self, model: GaussianModel, path: str):
        if self.use_executable_backend:
            return self._load_compressed_executable(model, path)
        else:
            return self._load_compressed_pyd(model, path)

    def _load_compressed_executable(self, model: GaussianModel, path: str):
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

    def _load_compressed_pyd(self, model: GaussianModel, path: str):
        # Read from file
        with open(path, 'rb') as f:
            buffer = f.read()

        # Decode
        pc = dracoreduced3dgs.decode(buffer)

        # Reconstruct ids_dict from decoded data
        device = model._xyz.device
        kwargs = dict(dtype=torch.float32, device=device)

        # Build ids_dict from decoded data
        # The decoded data contains: positions(Nx3), scales(Nx1), rotations(Nx2),
        # opacities(Nx1), features_dc(Nx1), features_rest(Nx9)
        # The values are stored as floats but represent integer indices
        ids_dict = {
            'scaling': torch.tensor(np.round(pc.scales.flatten()).astype(np.int64), device=device, dtype=torch.long),
            'rotation_re': torch.tensor(np.round(pc.rotations[:, 0]).astype(np.int64), device=device, dtype=torch.long),
            'rotation_im': torch.tensor(np.round(pc.rotations[:, 1]).astype(np.int64), device=device, dtype=torch.long),
            'opacity': torch.tensor(np.round(pc.opacities.flatten()).astype(np.int64), device=device, dtype=torch.long),
            'features_dc': torch.tensor(np.round(pc.features_dc.flatten()).astype(np.int64), device=device, dtype=torch.long).unsqueeze(-1),
        }

        # features_rest: Nx9 -> split into 3 sh_degrees, each with Nx3
        features_rest = pc.features_rest  # (N, 9)
        for sh_degree in range(model.max_sh_degree):
            start_idx = sh_degree * 3
            end_idx = start_idx + 3
            ids_dict[f'features_rest_{sh_degree}'] = torch.tensor(
                np.round(features_rest[:, start_idx:end_idx]).astype(np.int64), device=device, dtype=torch.long
            )

        # Load codebook
        codebook_dict = {name: torch.tensor(array, **kwargs) for name, array in np.load(os.path.splitext(path)[0] + ".codebook.npz").items()}
        self._codebook_dict = codebook_dict

        # Get xyz from decoded positions
        xyz = torch.tensor(pc.positions, **kwargs)

        return self.quantizer.dequantize(model, ids_dict, codebook_dict, xyz=xyz, replace=True)
