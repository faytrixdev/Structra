import re
import unicodedata
from typing import Iterable

import spacy
import nltk

from nltk.corpus import stopwords as nltk_stopwords

_nlp: spacy.Language | None = None
_stopwords_set: set[str] = set()

BUSINESS_STOPWORDS_FR: set[str] = {
    "le", "la", "les", "l", "de", "du", "des", "un", "une", "d",
    "a", "au", "aux", "dans", "par", "pour", "sur", "sous",
    "avec", "sans", "ou", "et", "mais", "dont", "que", "qui",
    "ce", "cette", "ces", "se", "s", "n", "ne", "pas",
    "est", "sont", "etre", "avoir", "faire", "fait", "doit", "peut",
    "il", "elle", "ils", "elles", "on", "nous", "vous",
    "ainsi", "alors", "egalement", "aussi", "toujours", "jamais",
    "tout", "toute", "tous", "toutes",
    "cela", "ceci", "celle", "celui", "celles", "ceux",
    "leur", "leurs", "son", "sa", "ses", "mon", "ma", "mes",
    "ton", "ta", "tes", "notre", "nos", "votre", "vos",
    "peuvent", "doivent",
}


def _get_nlp() -> spacy.Language:
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("fr_core_news_sm", disable=["parser", "ner"])
    return _nlp


def _get_stopwords() -> set[str]:
    global _stopwords_set
    if not _stopwords_set:
        _stopwords_set = (
            set(nltk_stopwords.words("french")) | BUSINESS_STOPWORDS_FR
        )
    return _stopwords_set


def strip_accents(text: str) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def lemmatize_token(token: str) -> str:
    if len(token) <= 2:
        return token
    doc = _get_nlp()(token)
    if doc and len(doc) > 0:
        return doc[0].lemma_
    return token


def lemmatize_text(text: str) -> str:
    tokens = text.split()
    lemmatized = [lemmatize_token(t) for t in tokens]
    return " ".join(lemmatized)


def remove_stopwords(tokens: Iterable[str]) -> list[str]:
    stops = _get_stopwords()
    return [t for t in tokens if t.lower() not in stops and len(t) > 1]


def token_set(text: str) -> set[str]:
    if not text:
        return set()
    cleaned = normalize_text(text)
    cleaned = strip_accents(cleaned)
    tokens = cleaned.split()
    lemmatized = [lemmatize_token(t) for t in tokens]
    filtered = remove_stopwords(lemmatized)
    return set(filtered)


def canonical_form(text: str) -> str:
    if not text:
        return ""
    tokens = token_set(text)
    return " ".join(sorted(tokens))


def full_normalize(text: str) -> str:
    """Full normalization: lowercase, accents removed, punctuation stripped,
    lemmatized, stopwords removed, tokens sorted. Equivalent to canonical_form."""
    return canonical_form(text)
