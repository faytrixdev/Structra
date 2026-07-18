import logging

logger = logging.getLogger(__name__)


def bootstrap_dedup_models() -> None:
    """No-op. Dedup uses pure-Python normalization now (no spacy/nltk needed)."""
    logger.info("Dedup: pure-Python normalization active (no external NLP models)")
