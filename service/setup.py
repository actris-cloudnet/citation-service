from setuptools import find_packages, setup

setup(
    name="citation-service",
    install_requires=["httpx", "fastapi", "uvicorn"],
    packages=find_packages(),
)
