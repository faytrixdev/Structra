# Deduplication Semantique — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an in-memory semantic deduplication module (4 levels: exact, near-match, semantic FR, merge) integrated before DB persistence in the extraction pipeline.

**Architecture:** New `backend/app/dedup/` package with normalizer, fingerprint, similarity, merger, and pipeline modules. Orchestrator modified to construct KnowledgeObjects in memory, deduplicate them, then persist only unique results.

**Tech Stack:** Python, spacy (fr_core_news_sm), nltk, Pydantic, SQLAlchemy. No embeddings, no LLM calls.

**Design doc:** `docs/plans/2026-07-17-structra-dedup-design.md`

---

### Task 1: Add dependencies and bootstrap

**Files:**
- Modify: `backend/requirements.txt:22-23` (append)
- Create: `backend/app/dedup/__init__.py`
- Create: `backend/app/dedup/bootstrap.py`
- Modify: `backend/main.py:1-6` (add import)

**Step 1: Append spacy and nltk to requirements.txt**

```python
# After line 23 (lxml==5.3.0), add:
spacy==3.7.6
nltk==3.9.1
```

**Step 2: Create dedup package init**

```python
# backend/app/dedup/__init__.py
from app.dedup.pipeline import deduplicate

__all__ = ["deduplicate"]
```

**Step 3: Create bootstrap module for model download**

```python
# backend/app/dedup/bootstrap.py
import subprocess
import nltk


def bootstrap_dedup_models() -> None:
    """Download required NLP models at startup. Idempotent."""
    import spacy
    try:
        spacy.load("fr_core_news_sm")
    except OSError:
        subprocess.run(["python", "-m", "spacy", "download", "fr_core_news_sm"], check=True)
    nltk.download("stopwords", quiet=True)
```

**Step 4: Add bootstrap call to main.py startup**

Insert after line 6 (`from app.api.v1 import auth, ...`):

```python
from app.dedup.bootstrap import bootstrap_dedup_models
```

Insert before line 7 (`app = FastAPI(...)`):

```python
bootstrap_dedup_models()
```

**Step 5: Install dependencies**

Run: `pip install spacy nltk`
Expected: packages installed successfully.

**Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/dedup/__init__.py backend/app/dedup/bootstrap.py backend/main.py
git commit -m "feat(dedup): add spacy/nltk dependencies and bootstrap"
```

---

### Task 2: Normalizer module — text cleaning + lemmatization + stopwords FR

**Files:**
- Create: `backend/app/dedup/normalizer.py`
- Create: `backend/tests/dedup/test_normalizer.py`
- Create: `backend/tests/dedup/__init__.py`
- Create: `backend/tests/__init__.py` (if missing)

**Step 1: Write the failing test**

```python
# backend/tests/dedup/__init__.py (empty)

# backend/tests/dedup/test_normalizer.py
import pytest
from app.dedup.normalizer import (
    strip_accents,
    normalize_text,
    lemmatize_text,
    remove_stopwords,
    canonical_form,
    full_normalize,
)


class TestStripAccents:
    def test_removes_french_accents(self):
        assert strip_accents("depourvues") == "depourvues"
        assert strip_accents("cree") == "cree"
        assert strip_accents("effectue") == "effectue"
        assert strip_accents("remboursees") == "remboursees"

    def test_preserves_non_accented(self):
        assert strip_accents("bonjour") == "bonjour"


class TestNormalizeText:
    def test_lowercases(self):
        assert normalize_text("LES Depenses") == "les depenses"

    def test_removes_punctuation(self):
        assert normalize_text("categories suivantes :") == "categories suivantes"
        assert normalize_text("remboursables : Transport, Hebergement, Repas") == "remboursables  transport  hebergement  repas"

    def test_collapses_spaces(self):
        assert normalize_text("  bon   jour  ") == "bon jour"

    def test_full_normalize(self):
        result = normalize_text("CREER  un  Document  :  maintenant!!!")
        assert result == "creer un document maintenant"


class TestLemmatizeText:
    def test_lemmatizes_conjugations(self):
        assert lemmatize_text("effectue") == "effectuer"
        assert lemmatize_text("sont") == "etre"
        assert lemmatize_text("crée") == "creer"

    def test_lemmatizes_plurals(self):
        assert lemmatize_text("depenses") == "depense"
        assert lemmatize_text("remboursables") == "remboursable"


class TestRemoveStopwords:
    def test_removes_french_stopwords(self):
        tokens = ["les", "depenses", "sans", "justificatif", "valide"]
        result = remove_stopwords(tokens)
        assert "les" not in result
        assert "sans" not in result
        assert "depenses" in result
        assert "justificatif" in result
        assert "valide" in result

    def test_preserves_business_terms(self):
        tokens = ["manager", "remboursement", "politique", "les", "de"]
        result = remove_stopwords(tokens)
        assert result == ["manager", "remboursement", "politique"]


class TestCanonicalForm:
    def test_canonical_normalizes_and_lemmatizes(self):
        result = canonical_form("Les depenses remboursees sont validees")
        assert "depense" in result
        assert "rembourser" in result or "rembourse" in result
        assert "valide" in result or "valider" in result

    def test_canonical_sorts_tokens(self):
        result = canonical_form("A B C")
        tokens = result.split()
        assert tokens == sorted(tokens)


class TestFullNormalize:
    def test_equivalence_examples(self):
        """Two equivalent texts should produce the same normalized form."""
        a = full_normalize("Les depenses sans justificatif valide ne peuvent pas etre remboursees.")
        b = full_normalize("les depenses  SANS justificatif  Valide  ne PEUVENT pas ETRE remboursees!!")
        assert a == b

    def test_quasi_identical_lemmatized(self):
        """Lemmatized forms should be equivalent."""
        a = full_normalize("cree")
        b = full_normalize("creer")
        assert a == b
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/dedup/test_normalizer.py -v`
Expected: all tests FAIL with ImportError (module doesn't exist yet).

**Step 3: Write full implementation**

```python
# backend/app/dedup/normalizer.py
import re
import unicodedata
from typing import Iterable

import nltk
import spacy

from nltk.corpus import stopwords as nltk_stopwords

_nlp: spacy.Language | None = None
_stopwords_set: set[str] = set()

BUSINESS_STOPWORDS_FR: set[str] = {
    "le", "la", "les", "l", "de", "du", "des", "un", "une", "d",
    "a", "au", "aux", "dans", "par", "pour", "sur", "sous",
    "avec", "sans", "ou", "et", "mais", "dont", "que", "qui",
    "ce", "c", "cette", "ces", "se", "s", "n", "ne", "pas",
    "est", "sont", "etre", "avoir", "faire", "fait", "doit", "peut",
    "il", "elle", "ils", "elles", "on", "nous", "vous",
    "ainsi", "alors", "egalement", "aussi", "toujours", "jamais",
    "tout", "toute", "tous", "toutes",
    "cela", "ceci", "celle", "celui", "celles", "ceux",
    "leur", "leurs", "son", "sa", "ses", "mon", "ma", "mes",
    "ton", "ta", "tes", "notre", "nos", "votre", "vos",
    "peut", "peuvent", "doit", "doivent",
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
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
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
    cleaned = normalize_text(text)
    cleaned = strip_accents(cleaned)
    tokens = cleaned.split()
    lemmatized = [lemmatize_token(t) for t in tokens]
    filtered = remove_stopwords(lemmatized)
    return set(filtered)


def canonical_form(text: str) -> str:
    tokens = token_set(text)
    return " ".join(sorted(tokens))


def full_normalize(text: str) -> str:
    """Full normalization: lowercase, accents removed, punctuation stripped,
    lemmatized, stopwords removed, tokens sorted."""
    return canonical_form(text)
```

**Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/dedup/test_normalizer.py -v`
Expected: ALL pass (PASS marks for all tests).

**Step 5: Commit**

```bash
git add backend/app/dedup/normalizer.py backend/tests/dedup/__init__.py backend/tests/dedup/test_normalizer.py backend/tests/__init__.py
git commit -m "feat(dedup): add normalizer with FR lemmatization, stopwords, canonical form"
```

---

### Task 3: Fingerprint module — canonical fingerprints + grouping

**Files:**
- Create: `backend/app/dedup/fingerprint.py`
- Create: `backend/tests/dedup/test_fingerprint.py`

**Step 1: Write the failing test**

```python
# backend/tests/dedup/test_fingerprint.py
import pytest
from app.dedup.fingerprint import (
    canonical_fingerprint,
    group_by_fingerprint,
)


class TestCanonicalFingerprint:
    def test_identical_texts_same_fingerprint(self):
        a = canonical_fingerprint("Le remboursement sous 7 jours.")
        b = canonical_fingerprint("Le remboursement sous 7 jours.")
        assert a == b

    def test_case_insensitive_same_fingerprint(self):
        a = canonical_fingerprint("CREER")
        b = canonical_fingerprint("créer")
        assert a == b

    def test_different_texts_different_fingerprint(self):
        a = canonical_fingerprint("Le manager valide les demandes.")
        b = canonical_fingerprint("Le service financier rembourse.")
        assert a != b

    def test_punctuation_ignored_same_fingerprint(self):
        a = canonical_fingerprint("Transport, Hebergement, Repas")
        b = canonical_fingerprint("Transport Hebergement Repas")
        assert a == b


class TestGroupByFingerprint:
    def test_groups_exact_duplicates(self):
        items = [
            {"id": "a", "text": "remboursement 7 jours"},
            {"id": "b", "text": "remboursement 7 jours"},
            {"id": "c", "text": "validation manager"},
        ]
        groups = group_by_fingerprint(items, key=lambda x: x["text"])
        assert len(groups) == 2
        group_ids = [sorted(g["id"] for g in grp) for grp in groups]
        assert ["a", "b"] in group_ids
        assert ["c"] in group_ids or ["c"] in [sorted(g["id"] for g in grp) for grp in groups]

    def test_groups_by_canonical_form(self):
        items = [
            {"id": "a", "text": "Creer un compte"},
            {"id": "b", "text": "créer un compte!!"},
            {"id": "c", "text": "Valider les demandes"},
        ]
        groups = group_by_fingerprint(items, key=lambda x: x["text"])
        assert len(groups) == 2

    def test_no_duplicates_single_groups(self):
        items = [
            {"id": "a", "text": "A"},
            {"id": "b", "text": "B"},
            {"id": "c", "text": "C"},
        ]
        groups = group_by_fingerprint(items, key=lambda x: x["text"])
        assert len(groups) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/dedup/test_fingerprint.py -v`
Expected: all tests FAIL with ImportError.

**Step 3: Write implementation**

```python
# backend/app/dedup/fingerprint.py
import hashlib
from collections import defaultdict
from typing import Any, Callable, Hashable, TypeVar

from app.dedup.normalizer import full_normalize

T = TypeVar("T")


def canonical_fingerprint(text: str) -> str:
    normalized = full_normalize(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def group_by_fingerprint(
    items: list[T],
    key: Callable[[T], str],
    fingerprint_fn: Callable[[str], str] = canonical_fingerprint,
) -> list[list[T]]:
    buckets: dict[str, list[T]] = defaultdict(list)
    for item in items:
        fp = fingerprint_fn(key(item))
        buckets[fp].append(item)
    return list(buckets.values())
```

**Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/dedup/test_fingerprint.py -v`
Expected: ALL pass.

**Step 5: Commit**

```bash
git add backend/app/dedup/fingerprint.py backend/tests/dedup/test_fingerprint.py
git commit -m "feat(dedup): add canonical fingerprint with sha256 grouping"
```

---

### Task 4: Similarity module — Jaccard + semantic FR with synonyms

**Files:**
- Create: `backend/app/dedup/similarity.py`
- Create: `backend/tests/dedup/test_similarity.py`

**Step 1: Write the failing test**

```python
# backend/tests/dedup/test_similarity.py
import pytest
from app.dedup.similarity import (
    jaccard_similarity,
    semantic_jaccard,
    are_quasi_identical,
    are_semantically_equivalent,
    SYNONYMS_FR,
    expand_with_synonyms,
)


class TestJaccardSimilarity:
    def test_identical_sets_score_one(self):
        assert jaccard_similarity({"a", "b", "c"}, {"a", "b", "c"}) == 1.0

    def test_disjoint_sets_score_zero(self):
        assert jaccard_similarity({"a", "b"}, {"c", "d"}) == 0.0

    def test_partial_overlap(self):
        score = jaccard_similarity({"a", "b", "c"}, {"a", "b", "d"})
        assert score == pytest.approx(0.5, 0.01)


class TestAreQuasiIdentical:
    def test_identical_after_normalization(self):
        assert are_quasi_identical(
            "Les categories suivantes sont remboursables : Transport professionnel Hebergement professionnel Repas professionnels",
            "Les categories suivantes sont remboursables : Transport professionnel, Hebergement professionnel, Repas professionnels",
        )

    def test_conjugation_lemmatizes(self):
        assert are_quasi_identical("creer", "cree")

    def test_different_meanings_false(self):
        assert not are_quasi_identical(
            "Le manager valide les demandes.",
            "Le service financier rembourse les frais.",
        )


class TestSemanticEquivalence:
    def test_synonym_expansion(self):
        assert "remboursable" in SYNONYMS_FR
        synonyms = expand_with_synonyms({"remboursable"})
        assert "pouvant_etre_rembourse" in synonyms or "eligible_remboursement" in synonyms

    def test_semantic_equivalence_french(self):
        """The flagship example from the spec."""
        assert are_semantically_equivalent(
            "Les depenses sans justificatif valide ne peuvent pas etre remboursees.",
            "Les depenses depourvues d'un justificatif valide ne sont pas remboursables.",
        )

    def test_different_rules_not_equivalent(self):
        assert not are_semantically_equivalent(
            "Les depenses de transport sont remboursees a 100 %.",
            "Les depenses de repas sont remboursees a 50 % de la limite legale.",
        )

    def test_garde_fou_small_intersection(self):
        """Very short texts with high ratio but small absolute overlap."""
        assert not are_semantically_equivalent("manager", "service financier")


class TestSimilarityThresholds:
    def test_quasi_threshold_90(self):
        """Near-identical after lemmatization should pass >= 0.90."""
        score = jaccard_similarity({"depense", "justificatif", "valide"}, {"depense", "justificatif", "valide"})
        assert score >= 0.90
        assert score >= 0.85

    def test_semantic_threshold_85(self):
        """Semantic after synonym expansion should pass >= 0.85."""
        a = {"depense", "justificatif", "valide", "remboursable"}
        b = {"depense", "justificatif", "valide", "pouvant_etre_rembourse"}
        score = jaccard_similarity(a, b)
        # With synonym expansion, both should contain equivalent tokens
        expanded_a = expand_with_synonyms(a)
        expanded_b = expand_with_synonyms(b)
        semantic_score = jaccard_similarity(expanded_a, expanded_b)
        assert semantic_score >= 0.85
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/dedup/test_similarity.py -v`
Expected: all tests FAIL with ImportError.

**Step 3: Write implementation**

```python
# backend/app/dedup/similarity.py
from app.dedup.normalizer import token_set, normalize_text, lemmatize_text


SYNONYMS_FR: dict[str, set[str]] = {
    "depourvu_de": {"sans", "non_muni_de", "ne_pas_avoir"},
    "remboursable": {"pouvant_etre_rembourse", "eligible_remboursement", "pouvant_etre_rembourse", "remboursable"},
    "valider": {"approuver", "autoriser", "valider", "homologuer"},
    "justificatif": {"piece_justificative", "preuve", "document_justificatif", "justificatif"},
    "effectuer": {"realiser", "executer", "proceder_a", "mettre_en_oeuvre", "effectuer"},
    "a_compter_de": {"a_partir_de", "depuis", "apres", "dans_un_delai_de"},
    "ouvrable": {"ouvrable", "ouvre", "travaille", "business_day"},
    "depense": {"frais", "cout", "charge", "depense"},
    "remboursement": {"indemnisation", "defraiement", "restitution", "remboursement"},
    "manager": {"responsable", "chef_de_service", "superieur_hierarchique", "manager"},
    "seuil": {"plafond", "limite", "montant_maximum", "seuil"},
    "conformite": {"respect", "adhesion", "observation", "conformite"},
    "obligatoire": {"requis", "necessaire", "indispensable", "imperatif", "obligatoire"},
    "exclure": {"exempter", "ne_pas_inclure", "exclure"},
    "politique": {"regle", "directive", "politique"},
    "entreprise": {"organisation", "societe", "firme", "entreprise"},
    "collaborateur": {"employe", "salarie", "collaborateur", "membre_du_personnel"},
    "demande": {"requete", "solicitation", "demande"},
    "accord": {"approbation", "autorisation", "consentement", "accord"},
    "delai": {"deadline", "echeance", "date_limite", "delai"},
    "conformement_a": {"selon", "d_apres", "en_vertu_de", "conformement_a"},
    "annuel": {"par_an", "chaque_annee", "annuel"},
    "mensuel": {"par_mois", "chaque_mois", "mensuel"},
    "document": {"fichier", "piece", "document"},
    "signature": {"validation_ecrite", "approbation_formelle", "signature"},
    "notification": {"alerte", "avertissement", "message", "notification"},
    "archive": {"archiver", "conserver", "stocker", "archive"},
    "confidentiel": {"secret", "restreint", "prive", "confidentiel"},
    "achat": {"acquisition", "commande", "achat"},
    "fournisseur": {"prestataire", "vendeur", "partenaire_commercial", "fournisseur"},
    "client": {"acheteur", "partenaire", "client"},
    "budget": {"enveloppe_budgetaire", "allocation", "budget"},
    "exercice_fiscal": {"annee_fiscale", "periode_comptable", "exercice_fiscal"},
    "facture": {"note_de_frais", "releve", "facture"},
    "contrat": {"accord_formel", "convention", "engagement", "contrat"},
    "audit": {"inspection", "verification", "controle", "audit"},
    "sanction": {"penalite", "amende", "consequence", "sanction"},
    "conformite_reglementaire": {"conformite_legale", "respect_des_normes", "conformite_reglementaire"},
    "protection_des_donnees": {"confidentialite_des_donnees", "rgpd", "protection_des_donnees"},
    "force_majeure": {"cas_imprevu", "circonstance_exceptionnelle", "force_majeure"},
}


QUASI_IDENTICAL_THRESHOLD: float = 0.90
SEMANTIC_THRESHOLD: float = 0.85
MIN_ABSOLUTE_INTERSECTION: int = 3


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    if not union:
        return 0.0
    return len(intersection) / len(union)


def expand_with_synonyms(tokens: set[str]) -> set[str]:
    """Expand a set of tokens with their synonym clusters."""
    expanded: set[str] = set(tokens)
    for token in tokens:
        if token in SYNONYMS_FR:
            expanded |= SYNONYMS_FR[token]
        for cluster_key, cluster_tokens in SYNONYMS_FR.items():
            if token in cluster_tokens:
                expanded.add(cluster_key)
                expanded |= cluster_tokens
                break
    return expanded


def semantic_jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute Jaccard with synonym expansion, with safety guard."""
    expanded_a = expand_with_synonyms(tokens_a)
    expanded_b = expand_with_synonyms(tokens_b)

    intersection = (expanded_a & expanded_b)
    union = expanded_a | expanded_b

    if not union:
        return 0.0

    score = len(intersection) / len(union)

    if len(intersection) < MIN_ABSOLUTE_INTERSECTION:
        score = min(score, 0.70)

    return score


def are_quasi_identical(text_a: str, text_b: str) -> bool:
    """Level 3: near-duplicate detection via lemmatized Jaccard >= 0.90."""
    tokens_a = token_set(text_a)
    tokens_b = token_set(text_b)
    return jaccard_similarity(tokens_a, tokens_b) >= QUASI_IDENTICAL_THRESHOLD


def are_semantically_equivalent(text_a: str, text_b: str) -> bool:
    """Level 4: semantic equivalence via synonym-expanded Jaccard >= 0.85."""
    tokens_a = token_set(text_a)
    tokens_b = token_set(text_b)
    return semantic_jaccard(tokens_a, tokens_b) >= SEMANTIC_THRESHOLD
```

**Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/dedup/test_similarity.py -v`
Expected: ALL pass.

**Step 5: Commit**

```bash
git add backend/app/dedup/similarity.py backend/tests/dedup/test_similarity.py
git commit -m "feat(dedup): add similarity module with Jaccard, synonyms FR, semantic thresholds"
```

---

### Task 5: Merger module — fusion with best score + entity union + label conflict

**Files:**
- Create: `backend/app/dedup/merger.py`
- Create: `backend/tests/dedup/test_merger.py`

**Step 1: Write the failing test**

```python
# backend/tests/dedup/test_merger.py
import pytest
from app.dedup.merger import (
    merge_group,
    merge_entities,
    merge_conditions,
    resolve_type_conflict,
    TYPE_PRIORITY,
)
from app.domain.types import KnowledgeType


class TestTypeConflict:
    def test_procedure_beats_concept(self):
        result = resolve_type_conflict(
            KnowledgeType.CONCEPT,
            KnowledgeType.PROCEDURE,
        )
        assert result == KnowledgeType.PROCEDURE

    def test_policy_beats_definition(self):
        result = resolve_type_conflict(
            KnowledgeType.DEFINITION,
            KnowledgeType.POLICY,
        )
        assert result == KnowledgeType.POLICY

    def test_same_type_returns_first(self):
        result = resolve_type_conflict(KnowledgeType.RULE, KnowledgeType.RULE)
        assert result == KnowledgeType.RULE

    def test_type_priority_ordering(self):
        assert TYPE_PRIORITY[KnowledgeType.PROCEDURE] > TYPE_PRIORITY[KnowledgeType.CONCEPT]
        assert TYPE_PRIORITY[KnowledgeType.POLICY] > TYPE_PRIORITY[KnowledgeType.DEFINITION]
        assert TYPE_PRIORITY[KnowledgeType.CONSTRAINT] > TYPE_PRIORITY[KnowledgeType.EVENT]


class TestMergeEntities:
    def test_union_of_different_entities(self):
        entities_a = [
            {"entity_type": "actor", "value": "Manager", "role": "approver"},
        ]
        entities_b = [
            {"entity_type": "actor", "value": "Manager", "role": "approver"},
            {"entity_type": "actor", "value": "Service financier", "role": "processor"},
        ]
        result = merge_entities(entities_a, entities_b)
        assert len(result) == 2
        values = {e["value"] for e in result}
        assert "Manager" in values
        assert "Service financier" in values

    def test_deduplicates_exact_duplicates(self):
        entities_a = [
            {"entity_type": "actor", "value": "Manager", "role": "validator"},
        ]
        entities_b = [
            {"entity_type": "actor", "value": "Manager", "role": "validator"},
        ]
        result = merge_entities(entities_a, entities_b)
        assert len(result) == 1

    def test_keeps_longest_role_for_same_entity(self):
        entities_a = [
            {"entity_type": "actor", "value": "Manager", "role": "HR"},
        ]
        entities_b = [
            {"entity_type": "actor", "value": "Manager", "role": "Human Resources Manager"},
        ]
        result = merge_entities(entities_a, entities_b)
        assert len(result) == 1
        assert result[0]["role"] == "Human Resources Manager"


class TestMergeConditions:
    def test_union_of_different_conditions(self):
        cond_a = [
            {"condition_type": "condition", "description": "Montant > 500"},
        ]
        cond_b = [
            {"condition_type": "condition", "description": "Montant > 500"},
            {"condition_type": "condition", "description": "Justificatif requis"},
        ]
        result = merge_conditions(cond_a, cond_b)
        assert len(result) == 2

    def test_deduplicates_identical(self):
        cond_a = [{"condition_type": "constraint", "description": "Pas de limite"}]
        cond_b = [{"condition_type": "constraint", "description": "Pas de limite"}]
        result = merge_conditions(cond_a, cond_b)
        assert len(result) == 1


class TestMergeGroup:
    def test_picks_highest_confidence(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "short", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
            {"id": "b", "confidence": 0.50, "statement": "longer" * 10, "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
        ]
        result = merge_group(group)
        assert result["id"] == "a"

    def test_tiebreaker_picks_longest_statement(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "short", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
            {"id": "b", "confidence": 0.90, "statement": "this is the longest statement", "type": KnowledgeType.PROCEDURE, "entities": [], "conditions": []},
        ]
        result = merge_group(group)
        assert result["id"] == "b"

    def test_merges_entities_from_all(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [{"entity_type": "actor", "value": "Manager", "role": "val"}], "conditions": []},
            {"id": "b", "confidence": 0.80, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [{"entity_type": "actor", "value": "Service financier", "role": "remb"}], "conditions": []},
        ]
        result = merge_group(group)
        values = {e["value"] for e in result["entities"]}
        assert "Manager" in values
        assert "Service financier" in values

    def test_merges_conditions_from_all(self):
        group = [
            {"id": "a", "confidence": 0.90, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [], "conditions": [{"condition_type": "condition", "description": "A"}]},
            {"id": "b", "confidence": 0.80, "statement": "OK", "type": KnowledgeType.PROCEDURE,
             "entities": [], "conditions": [{"condition_type": "condition", "description": "B"}]},
        ]
        result = merge_group(group)
        assert len(result["conditions"]) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/dedup/test_merger.py -v`
Expected: all tests FAIL with ImportError.

**Step 3: Write implementation**

```python
# backend/app/dedup/merger.py
from copy import deepcopy
from typing import Any

from app.domain.types import KnowledgeType


TYPE_PRIORITY: dict[KnowledgeType, int] = {
    KnowledgeType.PROCEDURE: 100,
    KnowledgeType.POLICY: 95,
    KnowledgeType.RULE: 90,
    KnowledgeType.WORKFLOW: 85,
    KnowledgeType.CONSTRAINT: 80,
    KnowledgeType.OBLIGATION: 75,
    KnowledgeType.PROHIBITION: 70,
    KnowledgeType.RESPONSIBILITY: 65,
    KnowledgeType.REQUIREMENT: 60,
    KnowledgeType.DECISION: 55,
    KnowledgeType.METRIC: 50,
    KnowledgeType.KPI: 50,
    KnowledgeType.DEFINITION: 45,
    KnowledgeType.EXCEPTION: 40,
    KnowledgeType.RISK: 35,
    KnowledgeType.EVENT: 30,
    KnowledgeType.CONCEPT: 25,
}


def resolve_type_conflict(type_a: KnowledgeType, type_b: KnowledgeType) -> KnowledgeType:
    priority_a = TYPE_PRIORITY.get(type_a, 0)
    priority_b = TYPE_PRIORITY.get(type_b, 0)
    if priority_a >= priority_b:
        return type_a
    return type_b


def merge_entities(entities_a: list[dict], entities_b: list[dict]) -> list[dict]:
    seen: dict[tuple[str, str], dict] = {}
    for ent in entities_a + entities_b:
        key = (ent.get("entity_type", ""), ent.get("value", ""))
        if key not in seen:
            seen[key] = ent
        else:
            existing_role = seen[key].get("role") or ""
            new_role = ent.get("role") or ""
            if len(new_role) > len(existing_role):
                seen[key]["role"] = new_role
    return list(seen.values())


def merge_conditions(conds_a: list[dict], conds_b: list[dict]) -> list[dict]:
    seen: dict[tuple[str, str], dict] = {}
    for cond in conds_a + conds_b:
        key = (cond.get("condition_type", ""), cond.get("description", ""))
        seen[key] = cond
    return list(seen.values())


def merge_group(group: list[dict]) -> dict:
    if len(group) == 1:
        return deepcopy(group[0])

    winner = max(group, key=lambda x: (x.get("confidence", 0), len(x.get("statement", ""))))

    merged = deepcopy(winner)

    all_entities: list[dict] = []
    for item in group:
        all_entities.extend(item.get("entities", []))
    merged["entities"] = merge_entities(merged.get("entities", []), all_entities)

    all_conditions: list[dict] = []
    for item in group:
        all_conditions.extend(item.get("conditions", []))
    merged["conditions"] = merge_conditions(merged.get("conditions", []), all_conditions)

    best_type = merged.get("type")
    for item in group:
        item_type = item.get("type")
        if item_type and best_type and item_type != best_type:
            best_type = resolve_type_conflict(best_type, item_type)
    merged["type"] = best_type

    merged_ids = [item.get("id") for item in group if item.get("id") != winner.get("id")]
    merged["metadata"] = merged.get("metadata", {})
    merged["metadata"]["merged_from"] = [
        {"id": item.get("id"), "statement": item.get("statement", ""), "confidence": item.get("confidence", 0)}
        for item in group if item.get("id") != winner.get("id")
    ]

    return merged
```

**Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/dedup/test_merger.py -v`
Expected: ALL pass.

**Step 5: Commit**

```bash
git add backend/app/dedup/merger.py backend/tests/dedup/test_merger.py
git commit -m "feat(dedup): add merger with entity union, label conflict resolution, best-score pick"
```

---

### Task 6: Pipeline module — orchestration of 4 levels

**Files:**
- Create: `backend/app/dedup/pipeline.py`
- Create: `backend/tests/dedup/test_pipeline.py`

**Step 1: Write the failing test**

```python
# backend/tests/dedup/test_pipeline.py
import pytest
from app.dedup.pipeline import deduplicate

DUMMY = {
    "entities": [],
    "conditions": [],
    "confidence": 0.80,
}


def make_item(id: str, statement: str, type: str = "Procedure") -> dict:
    return {
        "id": id,
        "statement": statement,
        "type": type,
        "entities": [],
        "conditions": [],
        "confidence": 0.80,
    }


class TestDeduplicate:
    def test_exact_duplicates_merged(self):
        items = [
            make_item("a", "Le remboursement est effectue sous 7 jours ouvres."),
            make_item("b", "Le remboursement est effectue sous 7 jours ouvres."),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_quasi_duplicates_merged(self):
        items = [
            make_item("a", "Les categories suivantes sont remboursables : Transport Hebergement Repas"),
            make_item("b", "Les categories suivantes sont remboursables : Transport, Hebergement, Repas"),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_conjugation_merged(self):
        items = [
            make_item("a", "creer"),
            make_item("b", "cree"),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_semantic_equivalent_merged(self):
        items = [
            make_item("a", "Les depenses sans justificatif valide ne peuvent pas etre remboursees."),
            make_item("b", "Les depenses depourvues d'un justificatif valide ne sont pas remboursables."),
        ]
        result = deduplicate(items)
        assert len(result) == 1

    def test_distinct_items_preserved(self):
        items = [
            make_item("a", "Le manager valide les demandes de remboursement."),
            make_item("b", "Le service financier traite les paiements."),
            make_item("c", "Les notes de frais doivent etre soumises avant le 5 du mois."),
        ]
        result = deduplicate(items)
        assert len(result) == 3

    def test_mixed_scenario(self):
        items = [
            make_item("a", "remboursement 7 jours"),
            make_item("b", "remboursement 7 jours"),  # exact duplicate of a
            make_item("c", "remboursement  7 jours"),  # quasi-duplicate (spaces)
            make_item("d", "validation manager"),
            make_item("e", "politique de conformite"),
        ]
        result = deduplicate(items)
        assert len(result) == 3

    def test_best_score_kept(self):
        items = [
            {"id": "a", "statement": "X", "type": "Procedure", "confidence": 0.50, "entities": [], "conditions": []},
            {"id": "b", "statement": "X", "type": "Procedure", "confidence": 0.90, "entities": [], "conditions": []},
        ]
        result = deduplicate(items)
        assert len(result) == 1
        assert result[0]["confidence"] == 0.90

    def test_type_conflict_resolved(self):
        items = [
            make_item("a", "Cette politique definit les regles de remboursement.", "Policy"),
            make_item("b", "Cette politique definit les regles de remboursement.", "Definition"),
        ]
        result = deduplicate(items)
        assert len(result) == 1
        assert result[0]["type"] == "Policy"

    def test_entity_union_preserved(self):
        items = [
            {"id": "a", "statement": "Le manager valide.", "type": "Responsibility", "confidence": 0.80,
             "entities": [{"entity_type": "actor", "value": "Manager", "role": "validator"}], "conditions": []},
            {"id": "b", "statement": "Le manager valide.", "type": "Responsibility", "confidence": 0.90,
             "entities": [{"entity_type": "actor", "value": "Service financier", "role": "processor"}], "conditions": []},
        ]
        result = deduplicate(items)
        assert len(result) == 1
        values = {e["value"] for e in result[0]["entities"]}
        assert "Manager" in values
        assert "Service financier" in values

    def test_no_false_positives_on_distinct_short_items(self):
        items = [
            make_item("a", "A"),
            make_item("b", "B"),
            make_item("c", "C"),
        ]
        result = deduplicate(items)
        assert len(result) == 3
```

**Step 2: Run test to verify it fails**

Run: `pytest backend/tests/dedup/test_pipeline.py -v`
Expected: all tests FAIL with ImportError.

**Step 3: Write implementation**

```python
# backend/app/dedup/pipeline.py
from app.dedup.fingerprint import canonical_fingerprint, group_by_fingerprint
from app.dedup.similarity import are_quasi_identical, are_semantically_equivalent
from app.dedup.merger import merge_group


def deduplicate(items: list[dict]) -> list[dict]:
    if not items:
        return []

    all_merged: list[dict] = []

    # Level 2: Exact duplicates via canonical fingerprint
    groups = group_by_fingerprint(items, key=lambda x: x.get("statement", ""))
    level2_result: list[dict] = []
    for group in groups:
        merged = merge_group(group)
        level2_result.append(merged)

    # Level 3 + 4: Near-duplicate and semantic equivalence
    final: list[dict] = []
    merged_indices: set[int] = set()

    for i, item_a in enumerate(level2_result):
        if i in merged_indices:
            continue
        group = [item_a]
        for j, item_b in enumerate(level2_result):
            if j <= i or j in merged_indices:
                continue
            text_a = item_a.get("statement", "")
            text_b = item_b.get("statement", "")
            if are_quasi_identical(text_a, text_b):
                group.append(item_b)
                merged_indices.add(j)
            elif are_semantically_equivalent(text_a, text_b):
                group.append(item_b)
                merged_indices.add(j)

        if len(group) > 1:
            merged = merge_group(group)
            final.append(merged)
        else:
            final.append(item_a)

    return final
```

**Step 4: Run tests to verify they pass**

Run: `pytest backend/tests/dedup/test_pipeline.py -v`
Expected: ALL pass.

**Step 5: Commit**

```bash
git add backend/app/dedup/pipeline.py backend/tests/dedup/test_pipeline.py
git commit -m "feat(dedup): add 4-level pipeline orchestrator deduplicate()"
```

---

### Task 7: Integration into orchestrator.py — dedup before DB persistence

**Files:**
- Modify: `backend/app/pipeline/orchestrator.py:1-95` (add import + restructure persistence loop)

**Step 1: Run existing tests to verify baseline**

Run: `pytest backend/ -v --ignore=backend/venv --ignore=backend/tests 2>&1 | head -30`
Expected: Check state. We don't have existing pipeline tests yet, but we want to verify no imports break.

**Step 2: Modify orchestrator.py**

Replace the knowledge object creation + persistence block (lines ~53-75) with the new in-memory construction + dedup + persistence flow:

```python
# backend/app/pipeline/orchestrator.py

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.models import Document, KnowledgeObject, KnowledgeEntity, KnowledgeCondition, KnowledgeRelation, PipelineLog
from app.domain.types import KnowledgeType, DocumentStatus, RelationType
from app.pipeline.stages import extract_ideas_stage, classify_stage, extract_entities_stage, validate_stage
from app.service.extraction_service import extract_text
from app.dedup import deduplicate


async def run_pipeline(document_id: str):
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = DocumentStatus.EXTRACTING
        db.commit()

        with open(doc.file_path, "rb") as f:
            file_content = f.read()
        text, page_count = await extract_text(doc.file_path, doc.file_type, file_content)
        doc.page_count = page_count
        db.commit()

        doc.status = DocumentStatus.CLEANING
        db.commit()
        cleaned_text = text.strip()

        doc.status = DocumentStatus.SEGMENTING
        db.commit()
        segments = [s.strip() for s in cleaned_text.split("\n\n") if s.strip()]

        doc.status = DocumentStatus.EXTRACTING_IDEAS
        db.commit()
        all_ideas = []
        for segment in segments[:20]:
            ideas = await extract_ideas_stage(str(doc.id), segment, db)
            all_ideas.extend(ideas)

        if not all_ideas:
            doc.status = DocumentStatus.FAILED
            doc.error_message = "No ideas extracted from document"
            db.commit()
            return

        doc.status = DocumentStatus.CLASSIFYING
        db.commit()

        doc.status = DocumentStatus.EXTRACTING_ENTITIES
        db.commit()

        # === NEW: Build all candidate objects in memory ===
        candidate_pairs: list[dict] = []
        for idea in all_ideas:
            try:
                kt = KnowledgeType(idea.get("type", "Concept"))
            except ValueError:
                kt = KnowledgeType.CONCEPT

            classification = await classify_stage(str(doc.id), idea, db)
            entities_data = await extract_entities_stage(str(doc.id), idea.get("statement", ""), db)
            validation = await validate_stage(str(doc.id), {
                "id": str(idea.get("type", "")),
                "type": str(kt),
                "statement": idea.get("statement", ""),
            }, db)

            candidate_pairs.append({
                "id": idea.get("id", str(len(candidate_pairs))),
                "type": str(kt),
                "title": idea.get("statement", "")[:100],
                "statement": idea.get("statement", ""),
                "original_text": idea.get("statement", ""),
                "confidence": classification.get("confidence", validation.get("confidence_score", 0.5)),
                "entities": entities_data.get("entities", []),
                "conditions": entities_data.get("conditions", []),
            })

        # === NEW: Deduplicate before persistence ===
        dedup_result = deduplicate(candidate_pairs)

        # === Persist only unique results ===
        knowledge_ids: list[str] = []
        for item in dedup_result:
            try:
                kt = KnowledgeType(item.get("type", "Concept"))
            except ValueError:
                kt = KnowledgeType.CONCEPT

            ko = KnowledgeObject(
                organization_id=doc.organization_id,
                document_id=doc.id,
                type=kt,
                title=item.get("statement", "")[:100],
                statement=item.get("statement", ""),
                original_text=item.get("original_text", ""),
                confidence=item.get("confidence", 0.5),
                extra_data=item.get("metadata", {}),
            )
            db.add(ko)
            db.flush()

            for ent in item.get("entities", []):
                db.add(KnowledgeEntity(
                    knowledge_id=ko.id,
                    entity_type=ent.get("type", "object"),
                    value=ent.get("value", ""),
                    role=ent.get("role"),
                ))
            for cond in item.get("conditions", []):
                db.add(KnowledgeCondition(
                    knowledge_id=ko.id,
                    condition_type=cond.get("type", "condition"),
                    description=cond.get("description", ""),
                ))
            knowledge_ids.append(str(ko.id))
            db.commit()

        doc.status = DocumentStatus.BUILDING_RELATIONS
        db.commit()
        if len(knowledge_ids) >= 2:
            knowledge_objs = db.query(KnowledgeObject).filter(KnowledgeObject.id.in_(knowledge_ids)).all()
            for i, ko_a in enumerate(knowledge_objs):
                for ko_b in knowledge_objs[i + 1:]:
                    if ko_a.type == ko_b.type:
                        db.add(KnowledgeRelation(
                            source_id=ko_a.id,
                            target_id=ko_b.id,
                            relation_type=RelationType.REFERENCES,
                            confidence=0.5,
                        ))

        doc.status = DocumentStatus.COMPLETED
        db.commit()
    except Exception as e:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = DocumentStatus.FAILED
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()
```

**Step 3: Verify the full dedup test suite still passes**

Run: `pytest backend/tests/dedup/ -v`
Expected: ALL 30+ tests pass.

**Step 4: Verify backend import chain doesn't break**

Run: `python -c "from app.dedup import deduplicate; print('OK')"`
Expected: "OK" (no ImportError).

**Step 5: Commit**

```bash
git add backend/app/pipeline/orchestrator.py
git commit -m "feat(pipeline): integrate deduplication before DB persistence in orchestrator"
```

---

### Task 8: Full integration test — end-to-end pipeline with dedup

**Files:**
- Create: `backend/tests/test_dedup_integration.py`

**Step 1: Write the integration test**

```python
# backend/tests/test_dedup_integration.py
"""
Orchestrator-level integration: verify dedup works in the actual pipeline.
Mock the NLP stage to return known duplicates, then check the orchestrator
produces unique results.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.dedup import deduplicate


class TestDedupIntegration:
    def test_in_memory_dedup_before_persist(self):
        """Simulate what the orchestrator does: build candidates, dedup, persist."""
        candidates = [
            {"id": "1", "type": "Procedure", "statement": "Remboursement sous 7 jours.", "confidence": 0.50, "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "statement": "Remboursement sous 7 jours.", "confidence": 0.90, "entities": [], "conditions": []},
            {"id": "3", "type": "Definition", "statement": "Le manager valide les demandes.", "confidence": 0.80, "entities": [], "conditions": []},
        ]

        deduped = deduplicate(candidates)
        ids = [item["id"] for item in deduped]
        assert len(deduped) < len(candidates)

    def test_entity_merge_preserved_in_dedup(self):
        candidates = [
            {
                "id": "1", "type": "Responsibility", "confidence": 0.80,
                "statement": "Le manager valide les demandes de remboursement.",
                "entities": [{"entity_type": "actor", "value": "Manager", "role": "validator"}],
                "conditions": [],
            },
            {
                "id": "2", "type": "Responsibility", "confidence": 0.90,
                "statement": "Le manager valide les demandes de remboursement.",
                "entities": [{"entity_type": "actor", "value": "Service financier", "role": "processor"}],
                "conditions": [],
            },
        ]
        deduped = deduplicate(candidates)
        assert len(deduped) == 1
        assert len(deduped[0]["entities"]) == 2

    def test_all_french_spec_examples(self):
        """Validate all the specification examples work."""
        # Example 1: exact duplicate
        r1 = deduplicate([
            {"id": "1", "type": "Procedure", "confidence": 0.9,
             "statement": "Le remboursement est effectue sous 7 jours ouvres apres validation financiere.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "confidence": 0.9,
             "statement": "Le remboursement est effectue sous 7 jours ouvres apres validation financiere.",
             "entities": [], "conditions": []},
        ])
        assert len(r1) == 1

        # Example 2: near-duplicate (comma vs no comma in lists)
        r2 = deduplicate([
            {"id": "1", "type": "Procedure", "confidence": 0.9,
             "statement": "Les categories suivantes sont remboursables : Transport professionnel Hebergement professionnel Repas professionnels",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Procedure", "confidence": 0.9,
             "statement": "Les categories suivantes sont remboursables : Transport professionnel, Hebergement professionnel, Repas professionnels",
             "entities": [], "conditions": []},
        ])
        assert len(r2) == 1

        # Example 3: conjugation
        r3 = deduplicate([
            {"id": "1", "type": "Action", "confidence": 0.9, "statement": "creer", "entities": [], "conditions": []},
            {"id": "2", "type": "Action", "confidence": 0.9, "statement": "cree", "entities": [], "conditions": []},
        ])
        assert len(r3) == 1

        # Example 4: semantic (flagship)
        r4 = deduplicate([
            {"id": "1", "type": "Constraint", "confidence": 0.9,
             "statement": "Les depenses sans justificatif valide ne peuvent pas etre remboursees.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Constraint", "confidence": 0.9,
             "statement": "Les depenses depourvues d un justificatif valide ne sont pas remboursables.",
             "entities": [], "conditions": []},
        ])
        assert len(r4) == 1

        # Example 5: same text, conflicting classification
        r5 = deduplicate([
            {"id": "1", "type": "Policy", "confidence": 0.9,
             "statement": "Cette politique definit les regles de remboursement.",
             "entities": [], "conditions": []},
            {"id": "2", "type": "Definition", "confidence": 0.9,
             "statement": "Cette politique definit les regles de remboursement.",
             "entities": [], "conditions": []},
        ])
        assert len(r5) == 1
        assert r5[0]["type"] == "Policy"
```

**Step 2: Run integration test**

Run: `pytest backend/tests/test_dedup_integration.py -v`
Expected: ALL pass.

**Step 3: Run full dedup test suite (unit + integration)**

Run: `pytest backend/tests/dedup/ backend/tests/test_dedup_integration.py -v`
Expected: ALL 35+ tests pass.

**Step 4: Commit**

```bash
git add backend/tests/test_dedup_integration.py
git commit -m "test(dedup): add integration tests covering all spec examples"
```

---

### Task 9: Verification — full test suite pass

**Files:** None (verification only)

**Step 1: Run all dedup tests one more time**

Run: `pytest backend/tests/dedup/ backend/tests/test_dedup_integration.py -v --tb=short`
Expected: ALL tests PASS. Zero failures.

**Step 2: Check import chain**

Run: `python -c "from app.dedup import deduplicate; print('deduplicate ready')"`
Expected: `deduplicate ready`

**Step 3: Verify git status is clean**

Run: `git status`
Expected: All files committed, clean working tree (or only dedup-related changes).

**Step 4: Print summary**

Output:
```
Dedup Implementation Complete

Files created:
  backend/app/dedup/__init__.py
  backend/app/dedup/bootstrap.py
  backend/app/dedup/normalizer.py
  backend/app/dedup/fingerprint.py
  backend/app/dedup/similarity.py
  backend/app/dedup/merger.py
  backend/app/dedup/pipeline.py
  backend/tests/dedup/test_normalizer.py
  backend/tests/dedup/test_fingerprint.py
  backend/tests/dedup/test_similarity.py
  backend/tests/dedup/test_merger.py
  backend/tests/dedup/test_pipeline.py
  backend/tests/test_dedup_integration.py

Files modified:
  backend/requirements.txt (+spacy, nltk)
  backend/main.py (+bootstrap call)
  backend/app/pipeline/orchestrator.py (+dedup before persistence)

Tests: 35+ unit + integration tests, all passing
```

---

## Execution

Plan complete and saved to `docs/plans/2026-07-17-structra-dedup-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration.

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints.

Which approach?