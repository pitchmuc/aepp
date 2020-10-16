import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aepp",  # Replace with your own username
    version="0.0.7",
    author="Julien Piccini",
    author_email="piccini.julien@gmail.com",
    description="Package to manage AEP API endpoint and some helper functions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pitchmuc/aep",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
        "Development Status :: 2 - Pre-Alpha"
    ],
    python_requires='>=3.7',
    install_requires=['pandas', "requests",
                      "PyJWT", "pathlib2", "pathlib", "PyJWT[crypto]", "PyGreSQL"],
)
