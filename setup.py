import pathlib

from setuptools import setup

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()

REQUIRES = (HERE / "requirements.txt").read_text().strip().split("\n")

setup(
    name="BaiduImagesDownload",
    version="2.0.0",
    description="download image from Baidu Image",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/YXL76/BaiduImagesDownload",
    author="YXL",
    author_email="chenxin.lan.76@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    packages=["BaiduImagesDownload"],
    include_package_data=False,
    install_requires=REQUIRES,
)
