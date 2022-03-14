FROM python:3.10 AS base
RUN pip3 install --upgrade pip

WORKDIR /app

COPY setup.py .
RUN pip install .

FROM base AS dev
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "80"]

FROM base AS lint
RUN pip install isort mypy black

FROM base AS prod
COPY . /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
