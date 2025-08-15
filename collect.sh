#!/bin/bash
mkdir -p Ours
root=output
for folder in output/*-nocam0-gscompress; do
    video=$(basename "${folder%-nocam0-gscompress}")
    echo "Processing $video"
    cp output/$video-nocam0/frame1/ours_30000/quality.csv Ours/$video.csv
    cp output/$video-nocam0-gscompress/frame1/decompress.log Ours/$video.log
done