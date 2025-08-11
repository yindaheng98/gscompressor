#!/bin/bash
train() {
    python -m reduced_3dgs.train \
        -s data/$1/frame1 \
        -d output/$1-camera/frame1 \
        -i $2 \
        --mode camera-densify-prune-shculling \
        --empty_cache_every_step
    python train_nocam0.py \
        -s data/$1/frame1 \
        -d output/$1-nocam0/frame1 \
        -i $2 \
        --mode camera-densify-prune-shculling \
        --empty_cache_every_step \
        --load_camera output/$1-camera/frame1/cameras.json \
        -ocamera_rotation_lr_init=0 \
        -ocamera_rotation_lr_final=0 \
        -ocamera_position_lr_init=0 \
        -ocamera_position_lr_final=0 \
        -ocamera_exposure_lr_init=0 \
        -ocamera_exposure_lr_final=0
}
evaluate() {
    python -m gscompressor.quantize \
        -s output/$1-$3/frame1 \
        -d output/$1-$4/frame1 \
        -i $2 \
        compress \
        --num_clusters_scaling=1024 \
        --num_clusters_rotation_re=256 \
        --num_clusters_rotation_im=1024 \
        --num_clusters_opacity=256 \
        --num_clusters_features_dc=512 \
        --num_clusters_features_rest 256 128 64
    python -m gscompressor.quantize \
        -s output/$1-$3/frame1 \
        -d output/$1-$4/frame1 \
        -i $2 \
        decompress > output/$1-$4/frame1/decompress.log
    stat --printf="codebook %s\n" output/$1-$4/frame1/point_cloud/iteration_30000/point_cloud.codebook.npz >> output/$1-$4/frame1/decompress.log
    stat --printf="drc %s\n" output/$1-$4/frame1/point_cloud/iteration_30000/point_cloud.drc >> output/$1-$4/frame1/decompress.log
    python -m gaussian_splatting.render \
        -s data/$1/frame1 \
        -d output/$1-$4/frame1 \
        -i $2 \
        --mode camera \
        --load_camera output/$1-camera/frame1/cameras.json
}
pipeline() {
    train $1 $2
    evaluate $1 $2 nocam0 nocam0-gscompress
}

pipeline basketball 30000
pipeline boxes 30000
pipeline football 30000
pipeline juggle 30000
pipeline softball 30000
pipeline tennis 30000

pipeline discussion 30000
pipeline stepin 30000
pipeline trimming 30000
pipeline vrheadset 30000

pipeline boxing 30000
pipeline taekwondo 30000
pipeline walking 30000

pipeline coffee_martini 30000
pipeline cook_spinach 30000
pipeline cut_roasted_beef 30000
pipeline flame_salmon_1 30000
pipeline flame_steak 30000
pipeline sear_steak 30000
