# gscompressor: compress 3DGS scenes by Draco

## Install (PyPI)

```shell
pip install gscompressor
```

(No Linux version because not supported by PyPI: [Binary wheel can't be uploaded on pypi using twine](https://stackoverflow.com/questions/59451069/binary-wheel-cant-be-uploaded-on-pypi-using-twine))

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
