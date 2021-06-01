import codecs
import os

import setuptools

def read(rel_path: str):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), 'r') as fp:
        return fp.read()


def get_version(rel_path: str):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aepp",  # Replace with your own username
    version=get_version("aepp/__version__.py"),
    author="Julien Piccini",
    author_email="piccini.julien@gmail.com",
    description="Package to manage AEP API endpoint and some helper functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pitchmuc/aep",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Development Status :: 2 - Pre-Alpha"
    ],
    python_requires='>=3.6',
    install_requires=['pandas', "requests",
                      "PyJWT", "pathlib2", "pathlib", "PyJWT[crypto]", "PyGreSQL"],
)
