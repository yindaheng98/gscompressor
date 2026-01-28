import os
import platform
import shutil
import subprocess
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext


class NumpyImport:
    def __repr__(self):
        import numpy as np
        return np.get_include()
    __fspath__ = __repr__


class CMakeExtension(Extension):
    def __init__(self, name: str, sourcedir: str, target: str) -> None:
        super().__init__(name, sources=[])
        self.sourcedir = sourcedir
        self.target = target


class CMakeBuild(build_ext):
    def get_ext_filename(self, ext_name):
        for ext in self.extensions:
            if isinstance(ext, CMakeExtension) and ext.name == ext_name:
                name = ext_name.replace('.', os.sep)
                return name + ".exe" if platform.system() == "Windows" else name
        return super().get_ext_filename(ext_name)

    def run(self):
        # Build CMake extensions first (produces static libraries)
        for ext in self.extensions:
            if isinstance(ext, CMakeExtension):
                self.build_cmake_extension(ext)
        # Build Cython extensions
        cython_exts = [ext for ext in self.extensions if not isinstance(ext, CMakeExtension)]
        if cython_exts:
            orig, self.extensions = self.extensions, cython_exts
            build_ext.run(self)
            self.extensions = orig

    def build_cmake_extension(self, ext: CMakeExtension) -> None:
        build_temp = os.path.join(os.path.dirname(__file__), "build", ext.sourcedir)
        os.makedirs(build_temp, exist_ok=True)
        sourcedir = os.path.abspath(ext.sourcedir)
        cmake_args = [
            "-DCMAKE_BUILD_TYPE=Release",
        ]
        subprocess.check_call(
            ["cmake", sourcedir, *cmake_args], cwd=build_temp
        )
        build_args = ["--config", "Release"]
        subprocess.check_call(
            ["cmake", "--build", ".", "--target", ext.target, *build_args], cwd=build_temp,
        )
        libpath = self.get_finalized_command('build_py').build_lib
        dst = os.path.join(libpath, os.path.dirname(self.get_ext_filename(ext.name)))
        print(f"Copying {ext.target} to {dst}")
        os.makedirs(dst, exist_ok=True)
        if platform.system() == "Windows":
            src = os.path.join(build_temp, "Release", f"{ext.target}.exe")
            dst = os.path.join(dst, f"{ext.target}.exe")
        else:
            src = os.path.join(build_temp, ext.target)
            dst = os.path.join(dst, ext.target)

        # Copy with error checking
        shutil.copy2(src, dst)

        # shutil.rmtree(build_temp, ignore_errors=True)


with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

packages = ['gscompressor'] + ["gscompressor." + package for package in find_packages(where="gscompressor")]

setup(
    name="gscompressor",
    version='1.1.0',
    author='yindaheng98',
    author_email='yindaheng98@gmail.com',
    url='https://github.com/yindaheng98/gscompressor',
    description=u'Refactored python training and inference code for 3D Gaussian Splatting',
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=packages,
    package_dir={
        'gscompressor': 'gscompressor',
    },
    setup_requires=['cython', 'numpy'],
    ext_modules=[
        CMakeExtension("gscompressor.draco_encoder", sourcedir="submodules/draco3dgs", target="draco_encoder"),
        CMakeExtension("gscompressor.draco_decoder", sourcedir="submodules/draco3dgs", target="draco_decoder"),
        CMakeExtension("gscompressor.quantization.draco_encoder", sourcedir="submodules/dracoreduced3dgs", target="draco_encoder"),
        CMakeExtension("gscompressor.quantization.draco_decoder", sourcedir="submodules/dracoreduced3dgs", target="draco_decoder"),
        Extension(
            'gscompressor.draco3dgs',
            sources=['./cpython/draco3dgs.pyx'],
            depends=['./cpython/draco3dgs.h'],
            language='c++',
            include_dirs=[str(NumpyImport()), './cpython', './submodules/draco3dgs/src', './build/submodules/draco3dgs'],
            extra_compile_args=['/std:c++17', '/O2'] if platform.system() == "Windows" else ['-std=c++11', '-O3'],
            extra_link_args=['/LIBPATH:' + os.path.abspath('./build/submodules/draco3dgs/Release'), 'draco.lib'] if platform.system() == "Windows"
            else ['-L' + os.path.abspath('./build/submodules/draco3dgs'), '-l:libdraco.a'],
        ),
    ],
    cmdclass={"build_ext": CMakeBuild},
    include_package_data=True,
    install_requires=[
        'gaussian-splatting',
        'reduced-3dgs'
    ]
)
