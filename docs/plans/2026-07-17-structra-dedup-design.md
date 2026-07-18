# Plan: Deduplication semantique Structra — Design

**Date:** 2026-07-17
**Statut:** Approuve

## Contexte

Le pipeline d'extraction de connaissances de Structra produit des `KnowledgeObject` en analysant des documents d'entreprise.
Le systeme extrait differents types metier (Policy, Workflow, Procedure, Constraint, etc.) mais produit actuellement de nombreux doublons.

Objectif: chaque connaissance metier n'apparait qu'une seule fois dans la base.

## Approche multi-niveaux pure (choisie)

Pas d'embeddings, pas de LLM-as-judge.
Toute la logique de deduplication est implementee en Python local avec des regles linguistiques FR.

---

## 1. Architecture & emplacement

Nouveau module `backend/app/dedup/`:

```
backend/app/
├── dedup/
│   ├── __init__.py         # Re-export de la fonction deduplicate()
│   ├── normalizer.py       # Nettoyage FR (ponctuation, accents, casse, lemmatisation, stopwords)
│   ├── fingerprint.py      # Empreintes canoniques multi-niveaux (sha256, token set)
│   ├── similarity.py       # Distances Jaccard, set overlap, multi-set avec synonymes
│   ├── merger.py           # Fusion d'entites + meilleur score + resolution de conflit de label
│   └── pipeline.py         # Orchestration: entry point deduplicate()
```

La deduplication est appelee depuis `pipeline/orchestrator.py` - avant toute persistence en base de donnees. Aucun KnowledgeObject duplique n'est jamais ecrit.

---

## 2. Pipeline interne (4 niveaux en cascade)

```
Ideas extraites (en memoire, avant DB)
        │
        ▼
 ┌─────────────────────────────┐
 │  Niveau 1 — Normalisation   │
 │  (ponctuation, casse,       │
 │   accents, espaces multiples)│
 └──────────────┬──────────────┘
        │
        ▼  hash canonique
 ┌─────────────────────────────┐
 │  Niveau 2 — Groupement exact │
 │  (meme fingerprint)         │
 └──────────────┬──────────────┘
        │
        ▼  pour chaque bucket a >1 element
 ┌─────────────────────────────┐
 │  Niveau 3 — Quasi-doublons   │
 │  (lemmatisation FR +         │
 │   token sort + Jaccard >=0.9)│
 └──────────────┬──────────────┘
        │
        ▼  pour les paires restantes
 ┌─────────────────────────────┐
 │  Niveau 4 — Semantique FR    │
 │  (synonymes + stopwords      │
 │   + patterns de reformulation│
 │   → set overlap >=0.85)      │
 └──────────────┬──────────────┘
        │
        ▼
   Liste fusionnee unique
```

---

## 3. Normalisation (Niveau 1) — `normalizer.py`

### Etapes de nettoyage

| Etape             | Avant                                  | Apres                                  |
|-------------------|----------------------------------------|----------------------------------------|
| Unicode NFKC      | `Creer (cafe)`                         | `creer (cafe)`                         |
| Minuscules        | `LES Depenses`                         | `les depenses`                         |
| Accents (unidecode)| `depourvues`                          | `depourvues`                           |
| Ponctuation       | `categories suivantes :`               | `categories suivantes `                |
| Espaces multiples | `  bon   jour  `                       | `bon jour`                             |
| Lemmatisation FR  | `effectue`, `sont`, `creees`           | `effectuer`, `etre`, `creer`           |
| Stopwords FR      | `les depenses sans justificatif`       | `[depense, justificatif]`              |

### Libraries utilisees

- **spacy** (`fr_core_news_sm`) pour la lemmatisation de qualite (>95 % precision sur FR factuel)
- **nltk** pour les stopwords FR (`stopwords.words('french')`)
- **unicodedata** (stdlib) pour NFKC et removal d'accents

### Stopwords metier additionnels

Mots vides qui n'apportent pas d'information discriminante pour la semantique metier:

```
le, la, les, l', de, du, des, un, une, d', a, au, aux, dans, par, pour, sur,
sous, avec, sans, ou, et, mais, dont, que, qui, ce, c', cette, ces, se, s',
n', ne, pas, est, sont, etre, avoir, il, elle, ils, elles, on, nous, vous,
doit, doivent, doit, doivent, peut, peuvent, faire, fait, ainsi, alors,
egalement, aussi, toujours, jamais, tout, toute, tous, toutes
```

---

## 4. Detection par niveau

### Niveau 2 — Doublons exacts

```python
canonical = normalizer.full_normalize(text)
fingerprint = sha256(canonical)
```

Meme fingerprint = meme idee → groupe.

### Niveau 3 — Quasi-doublons

Pour les paires qui ont echoue le Niveau 2:

```python
tokens_a = sorted(normalize_and_lemmatize(text_a))
tokens_b = sorted(normalize_and_lemmatize(text_b))

set_a = set(tokens_a)
set_b = set(tokens_b)

intersection = set_a & set_b
union = set_a | set_b

jaccard = len(intersection) / len(union)
is_same = jaccard >= 0.90
```

Le tri alphabetique des tokens ignore l'ordre des mots.
La lemmatisation normalise conjugaison + singulier/pluriel.

### Niveau 4 — Semantique FR (synonymes)

Dictionnaire de synonymes domaine entreprise:

```python
SYNONYMS_FR = {
    "depourvu_de": {"sans", "non_muni_de", "ne_pas_avoir"},
    "remboursable": {"pouvant_etre_rembourse", "eligible_remboursement", "pouvant_faire_l_objet_d_un_remboursement"},
    "valider": {"approuver", "autoriser", "valider", "homologuer"},
    "justificatif": {"justificatif", "piece_justificative", "preuve", "document_justificatif"},
    "effectuer": {"realiser", "executer", "proceder_a", "mettre_en_oeuvre"},
    "a_compter_de": {"a_partir_de", "depuis", "apres", "dans_un_delai_de"},
    "ouvrable": {"ouvrable", "ouvre", "travaille", "business_day"},
    "depense": {"frais", "cout", "charge", "depense"},
    "remboursement": {"remboursement", "indemnisation", "defraiement", "restitution"},
    "manager": {"manager", "responsable", "chef_de_service", "superieur_hierarchique"},
    "seuil": {"seuil", "plafond", "limite", "montant_maximum"],
    "conformite": {"conformite", "respect", "adhesion", "observation"},
    "obligatoire": {"obligatoire", "requis", "necessaire", "indispensable", "imperatif"},
    "exclure": {"exclure", "exempter", "ne_pas"},  # mais jamais fusionner avec "inclure" etc.
}
```

Algorithme:

```python
def semantic_jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Calcule Jaccard sur les sets etendus avec synonymes."""
    expanded_a = expand_with_synonyms(tokens_a)
    expanded_b = expand_with_synonyms(tokens_b)

    intersection = (
        (expanded_a & expanded_b) |
        (tokens_a & expanded_b) |
        (expanded_a & tokens_b)
    )
    union = expanded_a | expanded_b

    score = len(intersection) / len(union)

    # Garde-fou: si intersection absolue < 3 tokens, rejeter
    if len(intersection) < 3:
        score = min(score, 0.70)

    return score

is_semantically_equivalent = semantic_jaccard(t_set_a, t_set_b) >= 0.85
```

---

## 5. Fusion — `merger.py`

Pour un groupe de doublons detecte, un seul `KnowledgeObject` est conserve.

### Regles de fusion

1. **Candidat gagnant** : celui avec le `confidence_score` le plus eleve. En cas d'egalite, celui avec le `statement` le plus long.

2. **Entites** : union dedupliquee de toutes les entites du groupe:
   ```python
   all_entities = merge_by_deduplication(entites_a + entites_b + ...)
   # dedup: meme (entity_type, value, role) → garder celle avec role le plus long
   ```

3. **Conditions** : union dedupliquee (meme `condition_type, description`)

4. **Resolution de conflit de classification** :
   ```python
   TYPE_PRIORITY = {
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
   ```
   Le type le plus precis (le plus haut dans la hierarchie) gagne. Un `Procedure` est plus informatif qu'un `Concept`.

5. **Tracabilite**:
   ```python
   winner.metadata["merged_from"] = [
       {"id": ..., "statement": ..., "confidence": ...}
       for obj in group if obj != winner
   ]
   ```

---

## 6. Integration a l'orchestrateur

Modification de `backend/app/pipeline/orchestrator.py`:

**Actuel** (simplifie): chaque `KnowledgeObject` est directement `db.add()` + `db.commit()`.

**Nouveau**: les objets sont construits en memoire, puis passes a la deduplication, et seuls les objets fusionnes sont persistes.

```python
# Extraction d'idees (inchangee)
all_ideas = []
for segment in segments[:20]:
    ideas = await extract_ideas_stage(...)
    all_ideas.extend(ideas)

# === NOUVEAU: Construction en memoire ===
candidate_pairs = []
for idea in all_ideas:
    classification = await classify_stage(...)
    entities_data = await extract_entities_stage(...)
    ko = KnowledgeObject(...)  # construit, pas db.add()
    candidate_pairs.append(CandidatePair(ko, entities_data, classification))

# === NOUVEAU: Deduplication ===
dedup_result = deduplicate(candidate_pairs)

# === Persistence des resultats fusionnes ===
for pair in dedup_result:
    db.add(pair.ko)
    db.flush()
    ko = pair.ko
    for ent in pair.entities_data.get("entities", []):
        db.add(KnowledgeEntity(knowledge_id=ko.id, ...))
    for cond in pair.entities_data.get("conditions", []):
        db.add(KnowledgeCondition(knowledge_id=ko.id, ...))
    db.commit()

# Suite du pipeline (relations, etc.) — inchangée
```

### Impact sur les relations

Les relations `KnowledgeRelation` ne sont pas affectees — elles sont construites apres la deduplication, donc sur les objets deja uniques.

---

## 7. Aspects importants

### Aucune information n'est perdue

La fusion est toujours une **union**:
- Entites additionnelles preservees
- Conditions additionnelles preservees
- Metadata `merged_from` garde la trace de toutes les sources

### Seuls les faux doublons sont elimines

Deux elements ne doivent etre consideres comme distincts que s'ils apportent reellement une nouvelle information.
Le seuil Jaccard 0.85/0.90 est conservateur: seuls les quasi-identiques sont fusionnes.

### Performance

- Complexite: O(n) pour normalisation, O(n log n) pour groupement par fingerprint, O(k²) sur k paires candidates (k << n apres Niveau 2, typiquement k entre 5 et 20).
- Tout en memoire, pas d'appel reseau.
- Pour 100 idees extraites d'un document, la deduplication prend <50 ms.

---

## 8. Tests

### Tests unitaires (`backend/tests/dedup/`)

- `test_normalizer.py`: normalisation FR, lemmatisation, stopwords
- `test_fingerprint.py`: empreintes canoniques, collisions exactes
- `test_similarity.py`: Jaccard, quasi-doublons, exemples semantiques FR
- `test_merger.py`: fusion d'entites, conflit de label, meilleur score
- `test_pipeline.py`: integration des 4 niveaux sur un jeu de test complet

### Tests d'integration

- `tests/test_dedup_integration.py`: execute le pipeline complet sur un document fixture, verifie qu'aucun doublon ne persiste.

### Examples de validation semantique

```python
# Exemple exact
assert dedup_pair(
    "Procedure: Le remboursement est effectue sous 7 jours ouvres apres validation financiere.",
    "Procedure: Le remboursement est effectue sous 7 jours ouvres apres validation financiere."
) == MERGED

# Exemple quasi-doublon (ponctuation + virgules)
assert dedup_pair(
    "Les categories suivantes sont remboursables : Transport professionnel Herbergement professionnel Repas professionnels",
    "Les categories suivantes sont remboursables : Transport professionnel, Herbergement professionnel, Repas professionnels"
) == MERGED

# Exemple lemmatisation (conjugaison)
assert dedup_pair("creer", "cree") == MERGED

# Exemple semantique FR (sans LLM)
assert dedup_pair(
    "Les depenses sans justificatif valide ne peuvent pas etre remboursees.",
    "Les depenses depourvues d'un justificatif valide ne sont pas remboursables."
) == MERGED
# Via: depense+dépensé → meme token, sans=sans, justificatif=justificatif,
# remboursable → meme cluster synonymique, valide=valide

# Exemple complementaire (doit rester distinct)
assert dedup_pair(
    "Les depenses de transport sont remboursees a 100 %.",
    "Les depenses de repas sont remboursees a 50 % de la limite legale."
) == DISTINCT
# Stopwords: Les, de, sont, a, de, la → restent: transport, repas → different

# Niveau fusion: choisir le meilleur score
assert pick_best(0.50, "Le remboursement sous 7 jours"), (0.90, "Le remboursement sous 7 jours") == 0.90
```

---

## 9. Dependances

Ajouter a `requirements.txt`:

```
spacy==3.7.6
nltk==3.9.1
```

Fichier de bootstrap pour l'installation des modeles: `backend/app/dedup/bootstrap.py`

```python
def bootstrap():
    import subprocess
    import nltk
    subprocess.run(["python", "-m", "spacy", "download", "fr_core_news_sm"])
    nltk.download('stopwords')
```

Appele au demarrage du backend dans `main.py`.

---

## 10. Module DS de la structure du fichier

```
backend/app/dedup/
├── __init__.py          # deduplicate()
├── normalizer.py        # clean_text(), lemmatize(), remove_stopwords()
├── fingerprint.py       # canonical_fingerprint(), group_by_fingerprint()
├── similarity.py        # jaccard_similarity(), semantic_jaccard(), SYNONYMS_FR
├── merger.py            # merge_group(), TYPE_PRIORITY
├── pipeline.py          # deduplicate() — orchestre les 4 niveaux
└── bootstrap.py         # download_models()

backend/
├── requirements.txt     # + spacy, nltk
└── main.py              # + appel bootstrap()

backend/pipeline/
└── orchestrator.py      # integration dedup avant persistence
```

---

## 11. Conclusion

Ce design:

- Ne requiert **aucun appel LLM** supplementaire, donc zero cout additionnel
- Traite **tous les niveaux de duplication** identifies (exact, quasi, semantique)
- **Respecte le principe "One idea = One JSON object"** en garantissant l'unicite
- **Preserve toute l'information utile** via la fusion intelligente (union d'entites)
- **Est testable et mesurable** avec des fixtures explicites