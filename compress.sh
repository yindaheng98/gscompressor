#!/bin/bash
QP=30
compress() {
    python -m gscompressor.compress \
        -s output/$1/$3 -d output/$2/$3 -i $4 \
        compress --qposition=$QP
    python -m gscompressor.compress \
        -s output/$1/$3 -d output/$2/$3 -i $4 \
        decompress
    python -m lapisgs.render --mode camera \
        -s data/$1 -d output/$2/$3 -i $4 \
        --load_camera output/$2/$3/cameras.json \
        --rescale_factor 1.0
}
compress_scales() {
    compress $1 $2 1x $3
    compress $1 $2 2x $3
    compress $1 $2 4x $3
    compress $1 $2 8x $3
}
compress_scales truck truck-gscompress 30000
quantize() {
    python -m gscompressor.quantize \
        -s output/$1/1x -d output/$2/$3 -i $4 \
        compress --qposition=$QP $VQARGS
    python -m gscompressor.quantize \
        -s output/$1/1x -d output/$2/$3 -i $4 \
        decompress
    python -m lapisgs.render --mode camera \
        -s data/$1 -d output/$2/$3 -i $4 \
        --load_camera output/$2/$3/cameras.json \
        --rescale_factor 1.0
}
VQARGS="
    --num_clusters_scaling=2048 \
    --num_clusters_rotation_re=256 \
    --num_clusters_rotation_im=2048 \
    --num_clusters_opacity=8 \
    --num_clusters_features_dc=8 \
    --num_clusters_features_rest 4 2 2"
quantize truck truck-gscompress vq-bad 30000
VQARGS="
    --num_clusters_scaling=8192 \
    --num_clusters_rotation_re=8192 \
    --num_clusters_rotation_im=8192 \
    --num_clusters_opacity=8192 \
    --num_clusters_features_dc=8192 \
    --num_clusters_features_rest 8192 8192 8192"
quantize truck truck-gscompress vq-good 30000
