import html
import logging
import re
from html.parser import HTMLParser

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from pydantic.error_wrappers import ErrorWrapper


class Publication(BaseModel):
    title: str | None
    year: int | None
    journal: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    authors: str | None


app = FastAPI()
logger = logging.getLogger(__name__)


def clean_crossref(text: str) -> str:
    """Clean up possible newlines and HTML character references."""
    return " ".join(html.unescape(text).split())


def format_authors(authors: list[str]) -> str:
    if len(authors) <= 2:
        return " & ".join(authors)
    else:
        return authors[0] + " et al."


async def fetch_crossref(doi: str):
    try:
        url = f"https://api.crossref.org/works/{doi}"
        logger.info(f"querying {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()["message"]
    except:
        logger.exception(f"querying {url} failed")
        raise

    try:
        title = clean_crossref(data["title"][0])
    except (KeyError, IndexError):
        title = None
        logger.warning(f"no title in {url}")

    try:
        year = data["published"]["date-parts"][0][0]
    except (KeyError, IndexError):
        year = None
        logger.warning(f"no year in {url}")

    try:
        journal = clean_crossref(data["short-container-title"][0])
    except (KeyError, IndexError):
        try:
            journal = clean_crossref(data["container-title"][0])
        except (KeyError, IndexError):
            journal = None
            logger.warning(f"no journal in {url}")

    try:
        volume = data["volume"]
    except (KeyError, IndexError):
        volume = None
        logger.warning(f"no volume in {url}")

    try:
        issue = data["issue"]
    except (KeyError, IndexError):
        issue = None
        logger.warning(f"no issue in {url}")

    try:
        pages = data["page"]
    except (KeyError, IndexError):
        pages = None
        logger.warning(f"no pages in {url}")

    try:
        authors = format_authors([author["family"] for author in data["author"]])
    except (KeyError, IndexError):
        authors = None
        logger.warning(f"no authors in {url}")

    return Publication(
        title=title,
        year=year,
        journal=journal,
        volume=volume,
        issue=issue,
        pages=pages,
        authors=authors,
    )


class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.year = None
        self.authors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            if attrs.get("name") == "citation_title":
                self.title = attrs.get("content")
            elif attrs.get("name") == "citation_date":
                if date := attrs.get("content"):
                    if m := re.search(r"\d{4}", date):
                        self.year = m[0]
            elif attrs.get("name") == "citation_author":
                if author := attrs.get("content"):
                    last_name = author.split(",")[0].strip()
                    self.authors.append(last_name)


async def fetch_url(url: str):
    try:
        logger.info(f"querying {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            parser = MyHTMLParser()
            parser.feed(response.text)
        return Publication(
            title=parser.title,
            year=parser.year,
            authors=format_authors(parser.authors),
        )
    except:
        logger.exception(f"querying {url} failed")


DOI_RE = r"((https?://)?doi\.org/|doi:)(?P<doi>.*)"
HDL_RE = r"((https?://)?hdl\.handle\.net/|hdl:)(?P<hdl>.*)"


@app.get("/", response_model=Publication)
async def root(uri: str):
    if m := re.match(DOI_RE, uri):
        return await fetch_crossref(m["doi"])
    if m := re.match(HDL_RE, uri):
        return await fetch_url("https://hdl.handle.net/" + m["hdl"])
    raise RequestValidationError(
        [
            ErrorWrapper(
                ValueError("expected doi.org or hdl.handle.net URI"), ("query", "uri")
            )
        ]
    )
