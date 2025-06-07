# gscompressor: compress 3DGS scenes by Draco

## Install

### Build [Draco](https://github.com/yindaheng98/draco3dgs/tree/main) for [vanilla 3DGS](https://github.com/yindaheng98/gaussian-splatting)

```sh
mkdir build-vanilla && cd build-vanilla && cmake ../submodules/draco3dgs -DCMAKE_BUILD_TYPE=Release && cd ../
cmake --build build-vanilla --config Release --target draco_encoder
cmake --build build-vanilla --config Release --target draco_decoder
```

### Build [Draco](https://github.com/yindaheng98/draco3dgs/tree/reduced3dgs) for [Reduced 3DGS](https://github.com/yindaheng98/reduced-3dgs)

```sh
mkdir build-reduced && cd build-reduced && cmake ../submodules/dracoreduced3dgs -DCMAKE_BUILD_TYPE=Release && cd ../
cmake --build build-reduced --config Release --target draco_encoder
cmake --build build-reduced --config Release --target draco_decoder
```
