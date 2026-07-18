import re
import unicodedata
from typing import Iterable


BUSINESS_STOPWORDS: set[str] = {
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
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "must",
    "this", "that", "these", "those", "it", "its",
}


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


def _simple_lemma(token: str) -> str:
    """Best-effort stemmer without spacy. Strips common French/English suffixes."""
    t = token.lower()
    if len(t) <= 3:
        return t
    # French
    for suffix in ("ement", "ments", "ation", "tions", "tion", "ances", "ance",
                    "ences", "ence", "ites", "ite", "eurs", "eur", "euses",
                    "euse", "aux", "aux", "ais", "ait", "ent", "ons", "ez",
                    "ont", "ira", "ira", "era", "er", "ir", "re", "e", "s"):
        if t.endswith(suffix) and len(t) - len(suffix) >= 3:
            return t[: -len(suffix)]
    # English
    for suffix in ("tion", "sion", "ment", "ness", "able", "ible", "ful",
                    "less", "ous", "ive", "ing", "ers", "er", "ed", "ly", "es", "s"):
        if t.endswith(suffix) and len(t) - len(suffix) >= 3:
            return t[: -len(suffix)]
    return t


def lemmatize_token(token: str) -> str:
    if len(token) <= 2:
        return token
    return _simple_lemma(token)


def lemmatize_tokens(tokens: list[str]) -> list[str]:
    return [lemmatize_token(t) for t in tokens]


def lemmatize_text(text: str) -> str:
    tokens = text.split()
    return " ".join(lemmatize_tokens(tokens))


def remove_stopwords(tokens: Iterable[str]) -> list[str]:
    return [t for t in tokens if t.lower() not in BUSINESS_STOPWORDS and len(t) > 1]


def token_set(text: str) -> set[str]:
    if not text:
        return set()
    cleaned = normalize_text(text)
    cleaned = strip_accents(cleaned)
    tokens = cleaned.split()
    lemmatized = lemmatize_tokens(tokens)
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
