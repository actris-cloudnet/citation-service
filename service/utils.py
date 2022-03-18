import html
import re
from collections.abc import Iterable
from html.parser import HTMLParser
from io import StringIO

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


def unicodize_sub_sup(html):
    html = re.sub(
        "<sub>(" + re_char_class(sub) + ")</sub>",
        lambda m: m[1].translate(sub_trans),
        html,
    )
    html = re.sub(
        "<sup>(" + re_char_class(sub) + ")</sup>",
        lambda m: m[1].translate(sup_trans),
        html,
    )
    return html


def sanitize_html(text: str) -> str:
    # Attempt to fix HTML that is already escaped.
    text = html.unescape(text)
    sanitizer = Sanitizer(
        {
            "tags": {"strong", "em", "sub", "sub"},
            "attributes": {},
            "empty": set(),
            "separate": set(),
        }
    )
    return sanitizer.sanitize(text)


class TagStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self) -> str:
        return self.text.getvalue()


def strip_tags(html):
    html = sanitize_html(html)
    html = unicodize_sub_sup(html)
    parser = TagStripper()
    parser.feed(html)
    return parser.get_data()