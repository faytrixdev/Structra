import spacy
import subprocess
import nltk


def bootstrap_dedup_models() -> None:
    """Download required NLP models at startup. Idempotent."""
    try:
        spacy.load("fr_core_news_sm")
    except OSError:
        subprocess.run(["python", "-m", "spacy", "download", "fr_core_news_sm"], check=True)
    nltk.download("stopwords", quiet=True)
