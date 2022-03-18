from setuptools import find_packages, setup

setup(
    name="citation-service",
    install_requires=["httpx", "fastapi", "uvicorn", "html-sanitizer"],
    packages=find_packages(),
)
