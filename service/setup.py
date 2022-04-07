from setuptools import find_packages, setup

setup(
    name="citation-service",
    setup_requires="wheel",
    install_requires=["h11==0.12.0", "httpx", "fastapi", "uvicorn", "html-sanitizer"],
    extras_require={
        "dev": ["pylint", "pre-commit"],
    },
    packages=find_packages(),
)
