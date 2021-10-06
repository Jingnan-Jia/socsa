import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="socsa", # Replace with your own username
    version="0.0.1",
    author="Jingnan",
    author_email="jiajingnan2222@gmail.com",
    description="A package to compute analysis solar cell stability testing results.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Jingnan-Jia/socsa",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[],
)
