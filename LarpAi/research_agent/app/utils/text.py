import re
from typing import List


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def truncate(text: str, max_chars: int = 200, suffix: str = "...") -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)].rstrip() + suffix


def extract_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug


def word_count(text: str) -> int:
    return len(text.split())


def strip_html(html: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", html)
    return normalize_whitespace(cleaned)
