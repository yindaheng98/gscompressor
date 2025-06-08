# gscompressor: compress 3DGS scenes by Draco

## Install (Development)

Install [`gaussian-splatting`](https://github.com/yindaheng98/gaussian-splatting).
You can download the wheel from [PyPI](https://pypi.org/project/gaussian-splatting/):
```shell
pip install --upgrade gaussian-splatting
```
Alternatively, install the latest version from the source:
```sh
pip install --upgrade git+https://github.com/yindaheng98/gaussian-splatting.git@master
```

Install [`reduced-3dgs`](https://github.com/yindaheng98/reduced-3dgs).
You can download the wheel from [PyPI](https://pypi.org/project/reduced-3dgs/):
```shell
pip install --upgrade reduced-3dgs
```
Alternatively, install the latest version from the source:
```sh
pip install --upgrade git+https://github.com/yindaheng98/reduced-3dgs.git@main
```

(Optional) Install [`lapis-gs`](https://github.com/yindaheng98/lapis-gs).
You can download the wheel from [PyPI](https://pypi.org/project/lapis-gs/):
```shell
pip install --upgrade lapis-gs
```
Alternatively, install the latest version from the source:
```sh
pip install --upgrade git+https://github.com/yindaheng98/lapis-gs.git@main
```

```shell
git clone --recursive https://github.com/yindaheng98/gscompressor
cd gscompressor
pip install tqdm plyfile tifffile
pip install --target . --upgrade --no-deps .
```

(Optional) If you prefer not to install `gaussian-splatting` and `reduced-3dgs` in your environment, you can install them in your `lapis-gs` directory:
```sh
pip install --target . --no-deps --upgrade git+https://github.com/yindaheng98/gaussian-splatting.git@master
pip install --target . --no-deps --upgrade git+https://github.com/yindaheng98/reduced-3dgs.git@main
pip install --target . --no-deps --upgrade git+https://github.com/yindaheng98/lapis-gs.git@main # Optional
```

## Build

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
