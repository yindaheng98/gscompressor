#!/bin/bash
set -e

SOURCE_DIR="output/truck"
ITERATION="30000"
SH_DEGREE="3"
TEMP_DIR="output/truck-gscompress"

echo "Source: $SOURCE_DIR, Iteration: $ITERATION"

# 1. exe encode
python -m gscompressor.compress --sh_degree "$SH_DEGREE" -s "$SOURCE_DIR" -d "$TEMP_DIR/exe" -i "$ITERATION" compress --use_executable_backend

# 2. pyd encode
python -m gscompressor.compress --sh_degree "$SH_DEGREE" -s "$SOURCE_DIR" -d "$TEMP_DIR/pyd" -i "$ITERATION" compress

# compare drc
echo "=== DRC MD5 ==="
md5sum "$TEMP_DIR/exe/point_cloud/iteration_$ITERATION/point_cloud.drc"
md5sum "$TEMP_DIR/pyd/point_cloud/iteration_$ITERATION/point_cloud.drc"

# copy drc for cross decoding
for dir in exe_exe exe_pyd pyd_exe pyd_pyd; do
    mkdir -p "$TEMP_DIR/$dir/point_cloud/iteration_$ITERATION"
done
cp "$TEMP_DIR/exe/point_cloud/iteration_$ITERATION/point_cloud.drc" "$TEMP_DIR/exe_exe/point_cloud/iteration_$ITERATION/"
cp "$TEMP_DIR/exe/point_cloud/iteration_$ITERATION/point_cloud.drc" "$TEMP_DIR/exe_pyd/point_cloud/iteration_$ITERATION/"
cp "$TEMP_DIR/pyd/point_cloud/iteration_$ITERATION/point_cloud.drc" "$TEMP_DIR/pyd_exe/point_cloud/iteration_$ITERATION/"
cp "$TEMP_DIR/pyd/point_cloud/iteration_$ITERATION/point_cloud.drc" "$TEMP_DIR/pyd_pyd/point_cloud/iteration_$ITERATION/"

# 3. exe encode -> exe decode
python -m gscompressor.compress --sh_degree "$SH_DEGREE" -s "$SOURCE_DIR" -d "$TEMP_DIR/exe_exe" -i "$ITERATION" decompress --use_executable_backend

# 4. exe encode -> pyd decode
python -m gscompressor.compress --sh_degree "$SH_DEGREE" -s "$SOURCE_DIR" -d "$TEMP_DIR/exe_pyd" -i "$ITERATION" decompress

# 5. pyd encode -> exe decode
python -m gscompressor.compress --sh_degree "$SH_DEGREE" -s "$SOURCE_DIR" -d "$TEMP_DIR/pyd_exe" -i "$ITERATION" decompress --use_executable_backend

# 6. pyd encode -> pyd decode
python -m gscompressor.compress --sh_degree "$SH_DEGREE" -s "$SOURCE_DIR" -d "$TEMP_DIR/pyd_pyd" -i "$ITERATION" decompress

# 比较ply
echo "=== PLY MD5 ==="
md5sum "$TEMP_DIR/exe_exe/point_cloud/iteration_$ITERATION/point_cloud.ply"
md5sum "$TEMP_DIR/exe_pyd/point_cloud/iteration_$ITERATION/point_cloud.ply"
md5sum "$TEMP_DIR/pyd_exe/point_cloud/iteration_$ITERATION/point_cloud.ply"
md5sum "$TEMP_DIR/pyd_pyd/point_cloud/iteration_$ITERATION/point_cloud.ply"

rm -rf "$TEMP_DIR"
