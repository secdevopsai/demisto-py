import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="demisto",
    version="0.0.5",
    author="Ronald Eddings",
    author_email="ron@secdevops.ai",
    description="A Python library for the Demisto API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/secdevopsai/demisto-py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
