import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pipeline-dsl",
    version="0.3.0",
    author="SAP SE",
    author_email="istio@sap.com",
    description="A Python Pipeline DSL for Concourse",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/SAP/pipeline-dsl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pyyaml",
    ],
    python_requires=">=3.6",
)
