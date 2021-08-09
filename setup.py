import pathlib
from setuptools import setup, find_packages

# Get the directory of this file
HERE = pathlib.Path(__file__).parent

setup(
    name='l2logger',
    version='1.4.0',
    description='Lifelong learning logger',
    long_description=(HERE / 'README.md').read_text(),
    long_description_content_type='text/markdown',
    author='Eric Nguyen',
    author_email='Eric.Nguyen@jhuapl.edu',
    license='UNLICENSED',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'numpy',
        'pandas>=1.1.1',
        'tabulate'
    ]
)
