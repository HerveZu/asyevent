import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()

setup(
    name="asyevent",
    version="0.1.1",
    description="An implementation of events and asynchronous callbacks using decorators.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/HerveZu/asyevent",
    author="Zucchinetti Hervé",
    author_email="herve.zucchinetti@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["asyevent"],
    include_package_data=True,
    install_requires=[],
)
