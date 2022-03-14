import html
import logging
import re
from html.parser import HTMLParser

import httpx
from fastapi import FastAPI, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from pydantic.error_wrappers import ErrorWrapper


class Publication(BaseModel):
    url: str
    title: str | None
    year: int | None
    journal: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    authors: str | None

    def as_text(self):
        parts = [
            (self.authors if self.authors is not None else "N.N.")
            + " ("
            + (str(self.year) if self.year is not None else "n.d.")
            + ")"
        ]
        if self.title is not None:
            parts.append(self.title)
        if self.journal is not None:
            text = self.journal
            if self.volume is not None:
                text += ", " + self.volume
                if self.issue is not None:
                    text += "(" + self.issue + ")"
            if self.pages is not None:
                text += ", " + self.pages
            parts.append(text)
        parts.append(self.url)
        return ". ".join(parts)

    def as_html(self):
        parts = [
            (html.escape(self.authors) if self.authors is not None else "N.N.")
            + " ("
            + (str(self.year) if self.year is not None else "n.d.")
            + ")"
        ]
        if self.title is not None:
            parts.append(html.escape(self.title))
        if self.journal is not None:
            text = "<i>" + html.escape(self.journal) + "</i>"
            if self.volume is not None:
                text += ", <i>" + html.escape(self.volume) + "</i>"
                if self.issue is not None:
                    text += "(" + html.escape(self.issue) + ")"
            if self.pages is not None:
                text += ", " + html.escape(self.pages)
            parts.append(text)
        parts.append(
            '<a href="' + html.escape(self.url) + '">' + html.escape(self.url) + "</a>"
        )
        return ". ".join(parts)

    def as_json(self):
        return {
            "url": self.url,
            "title": self.title,
            "year": self.year,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "authors": self.authors,
        }


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
        url=f"https://doi.org/{doi}",
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
            url=url,
            title=parser.title,
            year=parser.year,
            authors=format_authors(parser.authors),
        )
    except:
        logger.exception(f"querying {url} failed")
        raise


DOI_RE = r"((https?://)?doi\.org/|doi:)(?P<doi>.*)"
HDL_RE = r"((https?://)?hdl\.handle\.net/|hdl:)(?P<hdl>.*)"


def render(publication: Publication, accept: str):
    renderers = {
        "text/plain": lambda: PlainTextResponse(publication.as_text()),
        "text/html": lambda: HTMLResponse(publication.as_html()),
        "application/json": lambda: JSONResponse(publication.as_json()),
    }
    for media_type in accept.split(","):
        media_type = media_type.split(";")[0].strip()
        if media_type in renderers:
            return renderers[media_type]()
    return renderers["text/plain"]()


@app.get("/")
async def root(uri: str, accept: str = Header(default="text/plain")):
    if m := re.match(DOI_RE, uri):
        return render(await fetch_crossref(m["doi"]), accept)
    if m := re.match(HDL_RE, uri):
        return render(await fetch_url("https://hdl.handle.net/" + m["hdl"]), accept)
    raise RequestValidationError(
        [
            ErrorWrapper(
                ValueError("expected doi.org or hdl.handle.net URI"), ("query", "uri")
            )
        ]
    )
