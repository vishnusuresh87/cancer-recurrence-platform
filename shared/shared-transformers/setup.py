from setuptools import setup, find_packages

setup(
    name="shared-transformers",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26.0",
        "pandas>=2.1.0",
    ],
)

