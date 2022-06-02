import html
import re
from html.parser import HTMLParser
from io import StringIO
from typing import Iterable

from html_sanitizer import Sanitizer


def re_char_class(chars: Iterable[str]) -> str:
    special_chars = {"-", "]"}
    return (
        "["
        + "".join((f"\\{char}" if char in special_chars else char) for char in chars)
        + "]"
    )


sub = {
    "0": "₀",
    "1": "₁",
    "2": "₂",
    "3": "₃",
    "4": "₄",
    "5": "₅",
    "6": "₆",
    "7": "₇",
    "8": "₈",
    "9": "₉",
    "+": "₊",
    "−": "₋",
    "-": "₋",
    "=": "₌",
    "(": "₍",
    ")": "₎",
    "a": "ₐ",
    "e": "ₑ",
    "o": "ₒ",
    "x": "ₓ",
    "ə": "ₔ",
    "h": "ₕ",
    "k": "ₖ",
    "l": "ₗ",
    "m": "ₘ",
    "n": "ₙ",
    "p": "ₚ",
    "s": "ₛ",
    "t": "ₜ",
}
sub_trans = str.maketrans(sub)

sup = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
    "+": "⁺",
    "−": "⁻",
    "-": "⁻",
    "=": "⁼",
    "(": "⁽",
    ")": "⁾",
    "i": "ⁱ",
    "n": "ⁿ",
}
sup_trans = str.maketrans(sup)


def unicodize_sub_sup(text_html: str) -> str:
    text_html = re.sub(
        "<sub>(" + re_char_class(sub) + ")</sub>",
        lambda m: m[1].translate(sub_trans),
        text_html,
    )
    text_html = re.sub(
        "<sup>(" + re_char_class(sub) + ")</sup>",
        lambda m: m[1].translate(sup_trans),
        text_html,
    )
    return text_html


def unescape_html(text: str) -> str:
    """Unescape HTML that is possibly escaped multiple times."""
    text = html.unescape(text)
    text = html.unescape(text)
    return text


def sanitize_html(text: str) -> str:
    text = unescape_html(text)
    sanitizer = Sanitizer(
        {
            "tags": {"strong", "em", "sub", "sub"},
            "attributes": {},
            "empty": set(),
            "separate": set(),
        }
    )
    return sanitizer.sanitize(text)


class TagStripper(HTMLParser):  # pylint: disable=W0223
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, data: str):
        self.text.write(data)

    def get_data(self) -> str:
        return self.text.getvalue()


def strip_tags(text_html: str) -> str:
    text_html = sanitize_html(text_html)
    text_html = unicodize_sub_sup(text_html)
    parser = TagStripper()
    parser.feed(text_html)
    return parser.get_data()
