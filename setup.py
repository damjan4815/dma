from setuptools import setup, find_packages  # type: ignore

setup(
    name="propylon_document_assessment",
    version="0.0.1",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={
        "": []
    },
    install_requires=[],
)
