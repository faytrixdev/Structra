import sys
import spacy
import subprocess
import nltk
import logging

logger = logging.getLogger(__name__)


def bootstrap_dedup_models() -> None:
    """Ensure required NLP models are available at startup. Idempotent.

    Raises RuntimeError if the spaCy model cannot be loaded after attempting a
    download, so the failure surfaces at boot instead of crashing individual
    document-processing jobs mid-pipeline.
    """
    try:
        spacy.load("fr_core_news_sm")
    except OSError:
        logger.info("Downloading fr_core_news_sm model...")
        try:
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "fr_core_news_sm"],
                check=True,
                timeout=120,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            raise RuntimeError(
                "Failed to download required spaCy model 'fr_core_news_sm'. "
                "Run manually: python -m spacy download fr_core_news_sm"
            ) from e
        try:
            spacy.load("fr_core_news_sm")
        except OSError as e:
            raise RuntimeError(
                "spaCy model 'fr_core_news_sm' still unavailable after download. "
                "Run manually: python -m spacy download fr_core_news_sm"
            ) from e
    nltk.download("stopwords", quiet=True)
