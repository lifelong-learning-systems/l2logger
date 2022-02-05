import pathlib
from setuptools import setup, find_packages

# Get the directory of this file
HERE = pathlib.Path(__file__).parent

setup(
    name="l2logger",
    version="1.7.0",
    description="Lifelong learning logger",
    long_description=(HERE / "README.md").read_text(),
    long_description_content_type="text/markdown",
    author="Eric Nguyen",
    author_email="Eric.Nguyen@jhuapl.edu",
    license="MIT",
    python_requires=">=3.6",
    url="https://github.com/darpa-l2m/l2logger",
    download_url="https://github.com/darpa-l2m/l2logger/archive/release-20220121.tar.gz",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=["numpy", "pandas>=1.1.1", "tabulate"],
)
