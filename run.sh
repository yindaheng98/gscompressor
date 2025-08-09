#!/bin/bash
pipeline() {
    python -m reduced_3dgs.train \
        -s data/$1/frame1 \
        -d output/$1/frame1 \
        -i $2 \
        --mode camera-densify-prune-shculling \
        --empty_cache_every_step
    python train_nocam0.py \
        -s data/$1/frame1 \
        -d output/$1-quantize/frame1 \
        -i $2 \
        --mode densify-prune-shculling \
        --empty_cache_every_step \
        --load_camera output/$1/frame1/cameras.json
    python -m gscompressor.quantize \
        -s output/$1-quantize/frame1 \
        -d output/$1-gscompress/frame1 \
        -i $2 \
        compress \
        --num_clusters_scaling=1024 \
        --num_clusters_rotation_re=256 \
        --num_clusters_rotation_im=1024 \
        --num_clusters_opacity=256 \
        --num_clusters_features_dc=512 \
        --num_clusters_features_rest 256 128 64
    python -m gscompressor.quantize \
        -s output/$1-quantize/frame1 \
        -d output/$1-gscompress/frame1 \
        -i $2 \
        decompress
    python render_cam0.py \
        -s data/$1/frame1 \
        -d output/$1-gscompress/frame1 \
        -i $2 \
        --mode camera \
        --load_camera output/$1/frame1/cameras.json
}
pipeline basketball 30000