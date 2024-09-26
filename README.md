# Citation service

Web service for generating citations based on [doi.org](https://doi.org) and [hdl.handle.net](https://hdl.handle.net) URIs.

## Usage

Build service:

```sh
docker build -t citation-service .
```

Run service:

```sh
docker run --rm -p 9000:8080 citation-service
```

Plain-text citation:

    curl -H Accept:text/plain http://localhost:9000/?uri=https://doi.org/10.21105/joss.02123
    Tukiainen et al. (2020). CloudnetPy: A Python package for processing cloud remote sensing data. JOSS, 5(53), 2123. https://doi.org/10.21105/joss.02123

HTML citation:

    curl -H Accept:text/html http://localhost:9000/?uri=https://doi.org/10.21105/joss.02123
    Tukiainen et al. (2020). CloudnetPy: A Python package for processing cloud remote sensing data. <i>JOSS</i>, <i>5</i>(53), 2123. <a href="https://doi.org/10.21105/joss.02123">https://doi.org/10.21105/joss.02123</a>

JSON citation:

    curl -H Accept:application/json http://localhost:9000/?uri=https://doi.org/10.21105/joss.02123
    {"url":"https://doi.org/10.21105/joss.02123","title":"CloudnetPy: A Python package for processing cloud remote sensing data","year":2020,"journal":"JOSS","volume":"5","issue":"53","pages":"2123","authors":"Tukiainen et al."}

## Development

```sh
python3 -m venv venv
source venv/bin/activate
python3 -m pip install .[dev]
```

Running pre-commit checks for all files:

```sh
pre-commit run --all
```
