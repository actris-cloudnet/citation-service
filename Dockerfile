FROM python:3.10 AS base
RUN pip3 install --upgrade pip

WORKDIR /app

COPY pyproject.toml .
RUN pip install .

FROM base AS dev
EXPOSE 8080
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]

FROM base AS lint
RUN pip install isort mypy black

FROM base AS prod
COPY . /app
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
