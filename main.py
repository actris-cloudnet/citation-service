import html
import logging
import re

import httpx
from fastapi import FastAPI, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from pydantic.error_wrappers import ErrorWrapper

from utils import sanitize_html, strip_tags


class Publication(BaseModel):
    url: str
    title: str | None
    published: tuple[int] | tuple[int, int] | tuple[int, int, int] | None
    journal: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    authors: str | None

    def as_text(self):
        parts = [
            (self.authors if self.authors is not None else "N.N.")
            + " ("
            + (str(self.published[0]) if self.published is not None else "n.d.")
            + ")"
        ]
        if self.title is not None:
            parts.append(strip_tags(self.title))
        if self.journal is not None:
            text = self.journal
            if self.volume is not None:
                text += ", " + self.volume
                if self.issue is not None:
                    text += "(" + self.issue + ")"
            if self.pages is not None:
                text += ", " + self.pages.replace("-", "–")
            parts.append(text)
        parts.append(self.url)
        return ". ".join(parts)

    def as_html(self):
        parts = [
            (html.escape(self.authors) if self.authors is not None else "N.N.")
            + " ("
            + (str(self.published[0]) if self.published is not None else "n.d.")
            + ")"
        ]
        if self.title is not None:
            parts.append(self.title)
        if self.journal is not None:
            text = "<i>" + html.escape(self.journal) + "</i>"
            if self.volume is not None:
                text += ", <i>" + html.escape(self.volume) + "</i>"
                if self.issue is not None:
                    text += "(" + html.escape(self.issue) + ")"
            if self.pages is not None:
                text += ", " + html.escape(self.pages.replace("-", "–"))
            parts.append(text)
        parts.append(
            '<a href="' + html.escape(self.url) + '">' + html.escape(self.url) + "</a>"
        )
        return ". ".join(parts)

    def as_json(self):
        return {
            "url": self.url,
            "title": self.title,
            "year": self.published[0] if self.published else None,
            "published": self.published,
            "journal": self.journal,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "authors": self.authors,
        }


app = FastAPI()
logger = logging.getLogger(__name__)


def format_author(author) -> str:
    return author["family"] + ", " + re.sub(r"([^-\s])[^-\s]+", r"\1.", author["given"])


def format_authors(authors: list) -> str:
    if len(authors) == 0:
        return ""
    formatted = [format_author(author) for author in authors]
    if len(authors) == 1:
        return formatted[0]
    return ", ".join(formatted[:-1]) + ", & " + formatted[-1]


async def fetch_crossref(doi: str) -> Publication:
    url = f"https://api.crossref.org/works/{doi}"
    try:
        logger.info(f"querying {url}")
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()["message"]
    except:
        logger.exception(f"querying {url} failed")
        raise

    try:
        title = sanitize_html(data["title"][0])
    except (KeyError, IndexError):
        title = None
        logger.warning(f"no title in {url}")

    try:
        published = tuple(data["published"]["date-parts"][0])
    except (KeyError, IndexError):
        published = None
        logger.warning(f"no published in {url}")

    try:
        journal = strip_tags(data["short-container-title"][0])
    except (KeyError, IndexError):
        try:
            journal = strip_tags(data["container-title"][0])
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
        authors = format_authors(data["author"])
    except (KeyError, IndexError):
        authors = None
        logger.warning(f"no authors in {url}")

    return Publication(
        url=f"https://doi.org/{doi}",
        title=title,
        published=published,
        journal=journal,
        volume=volume,
        issue=issue,
        pages=pages,
        authors=authors,
    )


DOI_RE = r"((https?://)?(dx\.)?doi\.org/|doi:)(?P<doi>.*)"


def render(publication: Publication, accept: str) -> PlainTextResponse:
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
    if match := re.match(DOI_RE, uri):
        return render(await fetch_crossref(match["doi"]), accept)
    raise RequestValidationError(
        [
            ErrorWrapper(
                ValueError("expected doi.org or hdl.handle.net URI"), ("query", "uri")
            )
        ]
    )
