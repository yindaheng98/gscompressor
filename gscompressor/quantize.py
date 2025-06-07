import platform
import torch
import os
import shutil
from gaussian_splatting import GaussianModel
from reduced_3dgs.quantization import ExcludeZeroSHQuantizer as VectorQuantizer
from gscompressor import VectorQuantizationCompressor


def compress(
        sh_degree: int,
        load_ply: str,
        save_drc: str,
        encoder_executable: str,
        compression_level=0,
        qposition=16,
        qscale=16,
        qrotation=16,
        qopacity=16,
        qfeaturedc=16,
        qfeaturesrest=16,
        **kwargs
):
    gaussians = GaussianModel(sh_degree)
    gaussians.load_ply(load_ply)
    compressor = VectorQuantizationCompressor(
        VectorQuantizer(**kwargs),
        encoder_executable=encoder_executable,
        compression_level=compression_level,
        qposition=qposition,
        qscale=qscale,
        qrotation=qrotation,
        qopacity=qopacity,
        qfeaturedc=qfeaturedc,
        qfeaturesrest=qfeaturesrest,
    )
    compressor.save_compressed(gaussians, save_drc)


def decompress(
        sh_degree: int,
        load_drc: str,
        save_ply: str,
        decoder_executable: str,
):
    gaussians = GaussianModel(sh_degree)
    compressor = VectorQuantizationCompressor(
        VectorQuantizer(),
        decoder_executable=decoder_executable)
    compressor.load_compressed(load_drc)
    gaussians.save_ply(save_ply)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--sh_degree", default=3, type=int)
    parser.add_argument("-s", "--source", required=True, type=str)
    parser.add_argument("-d", "--destination", required=True, type=str)
    parser.add_argument("-i", "--iteration", required=True, type=int)
    subparsers = parser.add_subparsers(dest="mode", required=True)
    rootparser = parser
    parser = subparsers.add_parser("compress")
    parser.add_argument("--encoder_executable", default="./build-reduced/Release/draco_encoder.exe" if platform.system() == "Windows" else "./build-reduced/draco_encoder", type=str)
    parser.add_argument("--compression_level", default=0, type=int)
    parser.add_argument("--qposition", default=16, type=int)
    parser.add_argument("--qscale", default=16, type=int)
    parser.add_argument("--qrotation", default=16, type=int)
    parser.add_argument("--qopacity", default=16, type=int)
    parser.add_argument("--qfeaturedc", default=16, type=int)
    parser.add_argument("--qfeaturesrest", default=16, type=int)
    parser.add_argument("--num_clusters", type=int, default=256)
    parser.add_argument("--num_clusters_rotation_re", type=int, default=None)
    parser.add_argument("--num_clusters_rotation_im", type=int, default=None)
    parser.add_argument("--num_clusters_opacity", type=int, default=None)
    parser.add_argument("--num_clusters_scaling", type=int, default=None)
    parser.add_argument("--num_clusters_features_dc", type=int, default=None)
    parser.add_argument("--num_clusters_features_rest", nargs="+", type=int, default=[])
    parser = subparsers.add_parser("decompress")
    parser.add_argument("--decoder_executable", default="./build-reduced/Release/draco_decoder.exe" if platform.system() == "Windows" else "./build-reduced/draco_decoder", type=str)
    args = rootparser.parse_args()
    save_drc = os.path.join(args.destination, "point_cloud", "iteration_" + str(args.iteration), "point_cloud.drc")
    with torch.no_grad():
        match args.mode:
            case "compress":
                compress(
                    sh_degree=args.sh_degree,
                    load_ply=os.path.join(args.source, "point_cloud", "iteration_" + str(args.iteration), "point_cloud.ply"),
                    save_drc=save_drc,
                    encoder_executable=args.encoder_executable,
                    compression_level=args.compression_level,
                    qposition=args.qposition,
                    qscale=args.qscale,
                    qrotation=args.qrotation,
                    qopacity=args.qopacity,
                    qfeaturedc=args.qfeaturedc,
                    qfeaturesrest=args.qfeaturesrest,
                    num_clusters=args.num_clusters,
                    num_clusters_rotation_re=args.num_clusters_rotation_re,
                    num_clusters_rotation_im=args.num_clusters_rotation_im,
                    num_clusters_opacity=args.num_clusters_opacity,
                    num_clusters_scaling=args.num_clusters_scaling,
                    num_clusters_features_dc=args.num_clusters_features_dc,
                    num_clusters_features_rest=args.num_clusters_features_rest
                )
                # Save the compressed model
            case "decompress":
                decompress(
                    sh_degree=args.sh_degree,
                    load_drc=save_drc,
                    save_ply=os.path.join(args.destination, "point_cloud", "iteration_" + str(args.iteration), "point_cloud.ply"),
                    decoder_executable=args.decoder_executable
                )
                shutil.copy2(os.path.join(args.source, "cfg_args"), os.path.join(args.destination, "cfg_args"))
                shutil.copy2(os.path.join(args.source, "cameras.json"), os.path.join(args.destination, "cameras.json"))
                if os.path.exists(os.path.join(args.source, "input.ply")):
                    shutil.copy2(os.path.join(args.source, "input.ply"), os.path.join(args.destination, "input.ply"))
            case _:
                raise ValueError(f"Unknown mode: {args.mode}")
