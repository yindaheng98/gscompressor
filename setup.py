import os
import platform
import shutil
import subprocess
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name: str, sourcedir: str) -> None:
        super().__init__(name, sources=[])
        self.sourcedir = sourcedir


class CMakeBuild(build_ext):
    def build_extension(self, ext: CMakeExtension) -> None:
        build_temp = os.path.join(os.path.dirname(__file__), "build", ext.name)
        os.makedirs(build_temp, exist_ok=True)
        sourcedir = os.path.abspath(ext.sourcedir)
        cmake_args = [
            "-DCMAKE_BUILD_TYPE=Release",
        ]
        subprocess.check_call(
            ["cmake", sourcedir, *cmake_args], cwd=build_temp
        )
        build_args = ["--config=Release"]
        subprocess.check_call(
            ["cmake", "--build", ".", "--target=draco_encoder", *build_args], cwd=build_temp,
        )
        subprocess.check_call(
            ["cmake", "--build", ".", "--target=draco_decoder", *build_args], cwd=build_temp,
        )
        dst = os.path.join(os.path.dirname(__file__), "gscompressor", ext.name)
        os.makedirs(dst, exist_ok=True)
        if platform.system() == "Windows":
            encoder_src = os.path.join(build_temp, "Release", "draco_encoder.exe")
            decoder_src = os.path.join(build_temp, "Release", "draco_decoder.exe")
            encoder_dst = os.path.join(dst, "draco_encoder.exe")
            decoder_dst = os.path.join(dst, "draco_decoder.exe")
        else:
            encoder_src = os.path.join(build_temp, "draco_encoder")
            decoder_src = os.path.join(build_temp, "draco_decoder")
            encoder_dst = os.path.join(dst, "draco_encoder")
            decoder_dst = os.path.join(dst, "draco_decoder")

        # Copy with error checking
        shutil.copy2(encoder_src, encoder_dst)
        shutil.copy2(decoder_src, decoder_dst)

        # shutil.rmtree(build_temp, ignore_errors=True)


with open("README.md", "r", encoding='utf8') as fh:
    long_description = fh.read()

packages = ['gscompressor'] + ["gscompressor." + package for package in find_packages(where="gscompressor")]

setup(
    name="gscompressor",
    version='1.0.0',
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
    ext_modules=[
        CMakeExtension("draco", sourcedir="submodules/draco3dgs"),
        CMakeExtension("quantization/draco", sourcedir="submodules/dracoreduced3dgs"),
    ],
    cmdclass={"build_ext": CMakeBuild},
    include_package_data=True,
    install_requires=[
        'gaussian-splatting',
        'reduced-3dgs'
    ]
)
