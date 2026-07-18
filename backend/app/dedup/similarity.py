from app.dedup.normalizer import token_set, normalize_text, lemmatize_text


SYNONYMS_FR: dict[str, set[str]] = {
    "creer": {"creer", "cree", "creer", "realiser", "etablir", "constituer", "generer"},
    "depourvu_de": {"sans", "non_muni_de", "ne_pas_avoir", "depourvu_de", "depourvue", "depourvues"},
    "remboursable": {"pouvant_etre_rembourse", "eligible_remboursement", "pouvant_etre_rembourse", "remboursable", "remboursee", "rembourser", "rembourses"},
    "valider": {"approuver", "autoriser", "valider", "homologuer", "signer"},
    "justificatif": {"piece_justificative", "preuve", "document_justificatif", "justificatif"},
    "effectuer": {"realiser", "executer", "proceder_a", "mettre_en_oeuvre", "effectuer"},
    "a_compter_de": {"a_partir_de", "depuis", "apres", "dans_un_delai_de", "a_compter_de"},
    "ouvrable": {"ouvrable", "ouvre", "travaille", "business_day", "ouvres"},
    "depense": {"frais", "cout", "charge", "depense", "depenser", "depenses"},
    "remboursement": {"indemnisation", "defraiement", "restitution", "remboursement", "rembourser", "remboursee"},
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

# Auxiliary/modal words that carry no dedup-discriminating meaning.
# They vary between reformulations ("peuvent" vs "sont", "ne ... pas" vs "non")
# and must be neutralized so semantic comparison focuses on content nouns.
NEUTRAL_TOKENS: set[str] = {
    "pouvoir", "etre", "etre", "avoir", "faire", "aller", "venir", "devoir", "vouloir",
    "ne", "pas", "non", "plus", "rien", "jamais", "point", "guère",
    "qui", "que", "dont", "ou", "si", "comme", "lorsque", "quand",
    "cela", "celui", "celle", "ceux", "celles", "ceci",
    "un", "une", "des", "les", "le", "la", "de", "du", "au", "aux",
    "il", "elle", "ils", "elles", "on", "nous", "vous", "je", "tu", "se",
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


def content_tokens(text: str) -> set[str]:
    """Token set with neutral/auxiliary words removed for semantic comparison."""
    from app.dedup.normalizer import strip_accents
    return {
        strip_accents(t)
        for t in token_set(text)
        if strip_accents(t) not in NEUTRAL_TOKENS
    }


def semantic_jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute a symmetric semantic similarity with synonym expansion.

    Uses the Dice coefficient (2*|A∩B| / (|A|+|B|)) which is robust to
    asymmetric synonym expansion (one side expanding more than the other),
    combined with a Jaccard fallback. A safety guard prevents false positives
    on very short texts with high ratio but tiny absolute overlap.
    """
    expanded_a = expand_with_synonyms(tokens_a)
    expanded_b = expand_with_synonyms(tokens_b)

    if not expanded_a and not expanded_b:
        return 1.0
    if not expanded_a or not expanded_b:
        return 0.0

    intersection = expanded_a & expanded_b
    union = expanded_a | expanded_b
    jaccard = len(intersection) / len(union)
    dice = (2 * len(intersection)) / (len(expanded_a) + len(expanded_b))

    score = max(jaccard, dice)

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
    tokens_a = content_tokens(text_a)
    tokens_b = content_tokens(text_b)
    return semantic_jaccard(tokens_a, tokens_b) >= SEMANTIC_THRESHOLD
