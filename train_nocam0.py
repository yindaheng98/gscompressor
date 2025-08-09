import os
import random
import shutil
from typing import List
import torch
from tqdm import tqdm
from gaussian_splatting import GaussianModel
from gaussian_splatting.dataset import CameraDataset
from gaussian_splatting.utils import psnr
from gaussian_splatting.trainer import AbstractTrainer
from gaussian_splatting.prepare import prepare_dataset
from gaussian_splatting.train import save_cfg_args
from reduced_3dgs.quantization import AbstractQuantizer
from reduced_3dgs.prepare import modes, prepare_gaussians, prepare_trainer


class NoCamera0Dataset(CameraDataset):
    def __init__(self, dataset: CameraDataset):
        self.dataset = dataset

    def to(self, device):
        return self.dataset.to(device)

    def __len__(self):
        return len(self.dataset) - 1  # Exclude the first camera

    def __getitem__(self, idx):
        return self.dataset[idx + 1]


def prepare_training(sh_degree: int, source: str, device: str, mode: str, trainable_camera: bool = False, load_ply: str = None, load_camera: str = None, load_depth=False, with_scale_reg=False, quantize: bool = False, load_quantized: str = None, configs={}):
    dataset = NoCamera0Dataset(prepare_dataset(source=source, device=device, trainable_camera=trainable_camera, load_camera=load_camera, load_depth=load_depth))
    gaussians = prepare_gaussians(sh_degree=sh_degree, source=source, device=device, trainable_camera=trainable_camera, load_ply=load_ply)
    trainer, quantizer = prepare_trainer(gaussians=gaussians, dataset=dataset, mode=mode, with_scale_reg=with_scale_reg, quantize=quantize, load_quantized=load_quantized, configs=configs)
    return dataset, gaussians, trainer, quantizer


def training(dataset: CameraDataset, gaussians: GaussianModel, trainer: AbstractTrainer, quantizer: AbstractQuantizer, destination: str, iteration: int, save_iterations: List[int], device: str, empty_cache_every_step=False):
    shutil.rmtree(os.path.join(destination, "point_cloud"), ignore_errors=True)  # remove the previous point cloud
    pbar = tqdm(range(1, iteration+1))
    epoch = list(range(len(dataset)))
    epoch_psnr = torch.empty(3, 0, device=device)
    ema_loss_for_log = 0.0
    avg_psnr_for_log = 0.0
    for step in pbar:
        epoch_idx = step % len(dataset)
        if epoch_idx == 0:
            avg_psnr_for_log = epoch_psnr.mean().item()
            epoch_psnr = torch.empty(3, 0, device=device)
            random.shuffle(epoch)
        idx = epoch[epoch_idx]
        loss, out = trainer.step(dataset[idx])
        if empty_cache_every_step:
            torch.cuda.empty_cache()
        with torch.no_grad():
            ema_loss_for_log = 0.4 * loss.item() + 0.6 * ema_loss_for_log
            epoch_psnr = torch.concat([epoch_psnr, psnr(out["render"], dataset[idx].ground_truth_image)], dim=1)
            if step % 10 == 0:
                pbar.set_postfix({'epoch': step // len(dataset), 'loss': ema_loss_for_log, 'psnr': avg_psnr_for_log, 'n': gaussians._xyz.shape[0]})
        if step in save_iterations:
            save_path = os.path.join(destination, "point_cloud", "iteration_" + str(step))
            os.makedirs(save_path, exist_ok=True)
            gaussians.save_ply(os.path.join(save_path, "point_cloud.ply"))
            dataset.save_cameras(os.path.join(destination, "cameras.json"))
            if quantizer:
                quantizer.save_quantized(gaussians, os.path.join(save_path, "point_cloud_quantized.ply"))
    save_path = os.path.join(destination, "point_cloud", "iteration_" + str(iteration))
    os.makedirs(save_path, exist_ok=True)
    gaussians.save_ply(os.path.join(save_path, "point_cloud.ply"))
    dataset.save_cameras(os.path.join(destination, "cameras.json"))
    if quantizer:
        quantizer.save_quantized(gaussians, os.path.join(save_path, "point_cloud_quantized.ply"))


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--sh_degree", default=3, type=int)
    parser.add_argument("-s", "--source", required=True, type=str)
    parser.add_argument("-d", "--destination", required=True, type=str)
    parser.add_argument("-i", "--iteration", default=30000, type=int)
    parser.add_argument("-l", "--load_ply", default=None, type=str)
    parser.add_argument("--load_camera", default=None, type=str)
    parser.add_argument("--quantize", action='store_true')
    parser.add_argument("--no_depth_data", action='store_true')
    parser.add_argument("--with_scale_reg", action="store_true")
    parser.add_argument("--load_quantized", default=None, type=str)
    parser.add_argument("--mode", choices=list(modes), default="densify-prune-shculling")
    parser.add_argument("--save_iterations", nargs="+", type=int, default=[7000, 30000])
    parser.add_argument("--device", default="cuda", type=str)
    parser.add_argument("--empty_cache_every_step", action='store_true')
    parser.add_argument("-o", "--option", default=[], action='append', type=str)
    args = parser.parse_args()
    save_cfg_args(args.destination, args.sh_degree, args.source)
    torch.autograd.set_detect_anomaly(False)

    configs = {o.split("=", 1)[0]: eval(o.split("=", 1)[1]) for o in args.option}
    dataset, gaussians, trainer, quantizer = prepare_training(
        sh_degree=args.sh_degree, source=args.source, device=args.device, mode=args.mode, trainable_camera="camera" in args.mode,
        load_ply=args.load_ply, load_camera=args.load_camera, load_depth=not args.no_depth_data, with_scale_reg=args.with_scale_reg,
        quantize=args.quantize, load_quantized=args.load_quantized, configs=configs)
    dataset.save_cameras(os.path.join(args.destination, "cameras.json"))
    torch.cuda.empty_cache()
    training(
        dataset=dataset, gaussians=gaussians, trainer=trainer, quantizer=quantizer,
        destination=args.destination, iteration=args.iteration, save_iterations=args.save_iterations,
        device=args.device)
