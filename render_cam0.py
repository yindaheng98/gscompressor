from typing import Tuple
import torch
import os
from tqdm import tqdm
from os import makedirs
import torchvision
import tifffile
from gaussian_splatting import GaussianModel
from gaussian_splatting.dataset import CameraDataset
from gaussian_splatting.utils import psnr, ssim, unproject
from gaussian_splatting.utils.lpipsPyTorch import lpips
from gaussian_splatting.prepare import prepare_dataset, prepare_gaussians


class OnlyCamera0Dataset(CameraDataset):
    def __init__(self, dataset: CameraDataset):
        self.dataset = dataset

    def to(self, device):
        return self.dataset.to(device)

    def __len__(self):
        return 1  # Exclude the first camera

    def __getitem__(self, idx):
        if idx > 0:
            raise IndexError("Only one camera (the first one) is available in this dataset.")
        return self.dataset[0]


def prepare_rendering(sh_degree: int, source: str, device: str, trainable_camera: bool = False, load_ply: str = None, load_camera: str = None, load_depth=False) -> Tuple[CameraDataset, GaussianModel]:
    dataset = OnlyCamera0Dataset(prepare_dataset(source=source, device=device, trainable_camera=trainable_camera, load_camera=load_camera, load_depth=load_depth))
    gaussians = prepare_gaussians(sh_degree=sh_degree, source=source, device=device, trainable_camera=trainable_camera, load_ply=load_ply)
    return dataset, gaussians


def rendering(dataset: CameraDataset, gaussians: GaussianModel, save: str) -> None:
    os.makedirs(save, exist_ok=True)
    render_path = os.path.join(save, "renders")
    gt_path = os.path.join(save, "gt")
    makedirs(render_path, exist_ok=True)
    makedirs(gt_path, exist_ok=True)
    pbar = tqdm(dataset, desc="Rendering progress")
    with open(os.path.join(save, "quality.csv"), "w") as f:
        f.write("name,psnr,ssim,lpips\n")
    for idx, camera in enumerate(pbar):
        out = gaussians(camera)
        rendering = out["render"]
        gt = camera.ground_truth_image
        psnr_value = psnr(rendering, gt).mean().item()
        ssim_value = ssim(rendering, gt).mean().item()
        lpips_value = lpips(rendering, gt).mean().item()
        pbar.set_postfix({"PSNR": psnr_value, "SSIM": ssim_value, "LPIPS": lpips_value})
        with open(os.path.join(save, "quality.csv"), "a") as f:
            f.write('{0:05d}'.format(idx) + f",{psnr_value},{ssim_value},{lpips_value}\n")
        torchvision.utils.save_image(rendering, os.path.join(render_path, '{0:05d}'.format(idx) + ".png"))
        torchvision.utils.save_image(gt, os.path.join(gt_path, '{0:05d}'.format(idx) + ".png"))


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--sh_degree", default=3, type=int)
    parser.add_argument("-s", "--source", required=True, type=str)
    parser.add_argument("-d", "--destination", required=True, type=str)
    parser.add_argument("-i", "--iteration", required=True, type=int)
    parser.add_argument("--load_camera", default=None, type=str)
    parser.add_argument("--mode", choices=["base", "camera"], default="base")
    parser.add_argument("--device", default="cuda", type=str)
    args = parser.parse_args()
    load_ply = os.path.join(args.destination, "point_cloud", "iteration_" + str(args.iteration), "point_cloud.ply")
    save = os.path.join(args.destination, "ours_{}".format(args.iteration))
    with torch.no_grad():
        dataset, gaussians = prepare_rendering(
            sh_degree=args.sh_degree, source=args.source, device=args.device, trainable_camera=args.mode == "camera",
            load_ply=load_ply, load_camera=args.load_camera, load_depth=True)
        rendering(dataset, gaussians, save)
