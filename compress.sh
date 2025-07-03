#!/bin/bash
QP=30
QSCALE=16
QROTATION=16
QOPACITY=16
QFEATUREDC=16
QFEATUREREST=16
compress() {
    python -m gscompressor.compress \
        -s output/$1/$3 -d output/$2/$3 -i $4 \
        compress \
        --qposition=$QP \
        --qscale=$QSCALE \
        --qrotation=$QROTATION \
        --qopacity=$QOPACITY \
        --qfeaturedc=$QFEATUREDC \
        --qfeaturerest=$QFEATUREREST
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
        -s output/$1/$3 -d output/$2/$3-vq-$5 -i $4 \
        compress --qposition=$QP $VQARGS
    python -m gscompressor.quantize \
        -s output/$1/$3 -d output/$2/$3-vq-$5 -i $4 \
        decompress
    python -m lapisgs.render --mode camera \
        -s data/$1 -d output/$2/$3-vq-$5 -i $4 \
        --load_camera output/$2/$3-vq-$5/cameras.json \
        --rescale_factor 1.0
}
VQARGS="
    --num_clusters_scaling=2048 \
    --num_clusters_rotation_re=256 \
    --num_clusters_rotation_im=2048 \
    --num_clusters_opacity=8 \
    --num_clusters_features_dc=8 \
    --num_clusters_features_rest 4 2 2"
quantize_scales() {
    quantize $1 $2 1x $3 bad
    quantize $1 $2 2x $3 bad
    quantize $1 $2 4x $3 bad
    quantize $1 $2 8x $3 bad
}
quantize_scales truck truck-gscompress 30000
VQARGS="
    --num_clusters_scaling=8192 \
    --num_clusters_rotation_re=8192 \
    --num_clusters_rotation_im=8192 \
    --num_clusters_opacity=8192 \
    --num_clusters_features_dc=8192 \
    --num_clusters_features_rest 8192 8192 8192"
quantize_scales() {
    quantize $1 $2 1x $3 good
    quantize $1 $2 2x $3 good
    quantize $1 $2 4x $3 good
    quantize $1 $2 8x $3 good
}
quantize_scales truck truck-gscompress 30000
