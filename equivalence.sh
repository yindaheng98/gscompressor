#!/bin/bash
set -e

SOURCE_DIR="output/truck"
ITERATION="30000"
SH_DEGREE="3"
TEMP_DIR="output/truck-gscompress"
# BASE="python -m gscompressor.compress --sh_degree $SH_DEGREE -s $SOURCE_DIR -i $ITERATION compress"
BASE="python -m gscompressor.quantize --sh_degree $SH_DEGREE -s $SOURCE_DIR -i $ITERATION"
ENC_OPTS="--num_clusters_scaling=1024 --num_clusters_rotation_re=256 --num_clusters_rotation_im=1024 --num_clusters_opacity=256 --num_clusters_features_dc=512 --num_clusters_features_rest=256 --num_clusters_features_rest=128 --num_clusters_features_rest=64"

echo "Source: $SOURCE_DIR, Iteration: $ITERATION"
mkdir -p "$TEMP_DIR"
rm -rf "$TEMP_DIR/*"

# 1. exe encode
$BASE -d "$TEMP_DIR/exe" compress $ENC_OPTS --use_executable_backend

# 2. pyd encode
$BASE -d "$TEMP_DIR/pyd" compress $ENC_OPTS

# copy for cross decoding
cp -r "$TEMP_DIR/exe" "$TEMP_DIR/exe_exe"
cp -r "$TEMP_DIR/exe" "$TEMP_DIR/exe_pyd"
cp -r "$TEMP_DIR/pyd" "$TEMP_DIR/pyd_exe"
cp -r "$TEMP_DIR/pyd" "$TEMP_DIR/pyd_pyd"

# 3. exe encode -> exe decode
$BASE -d "$TEMP_DIR/exe_exe" decompress --use_executable_backend

# 4. exe encode -> pyd decode
$BASE -d "$TEMP_DIR/exe_pyd" decompress

# 5. pyd encode -> exe decode
$BASE -d "$TEMP_DIR/pyd_exe" decompress --use_executable_backend

# 6. pyd encode -> pyd decode
$BASE -d "$TEMP_DIR/pyd_pyd" decompress

# compare
echo "=== DRC MD5 ==="
md5sum "$TEMP_DIR/exe/point_cloud/iteration_$ITERATION/point_cloud.drc"
md5sum "$TEMP_DIR/pyd/point_cloud/iteration_$ITERATION/point_cloud.drc"
echo "=== PLY MD5 ==="
md5sum "$TEMP_DIR/exe_exe/point_cloud/iteration_$ITERATION/point_cloud.ply"
md5sum "$TEMP_DIR/pyd_pyd/point_cloud/iteration_$ITERATION/point_cloud.ply"
md5sum "$TEMP_DIR/exe_pyd/point_cloud/iteration_$ITERATION/point_cloud.ply"
md5sum "$TEMP_DIR/pyd_exe/point_cloud/iteration_$ITERATION/point_cloud.ply"

rm -rf "$TEMP_DIR"
