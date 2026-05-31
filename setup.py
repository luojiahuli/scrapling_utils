from setuptools import setup, find_packages

setup(
    name="scrapling_utils",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["scrapling>=0.4.0"],
    python_requires=">=3.9",
)
