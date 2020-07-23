import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pypeline",
    version="0.0.1",
    author="SAP SE",
    author_email="istio@sap.com",
    description="Concourse Pipeline in Python DSL",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.tools.sap/cki/pypeline",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[ 
        "pyyaml"
    ],
    python_requires='>=3.6',
)
