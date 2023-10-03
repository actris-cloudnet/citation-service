from setuptools import find_packages, setup

setup(
    name="citation-service",
    setup_requires="wheel",
    install_requires=[
        "h11",
        "httpx",
        "fastapi",
        "pydantic>=1.2.0,<2.0.0",
        "uvicorn",
        "html-sanitizer",
    ],
    extras_require={
        "dev": ["pylint", "pre-commit"],
    },
    packages=find_packages(),
)
