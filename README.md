# Citation service

Web service for generating citations based on <doi.org> and <hdl.handle.net> URIs.

## Usage

Run service:

```sh
docker compose up
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
