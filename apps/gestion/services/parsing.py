"""
Extraction des champs structurés à partir du texte brut d'une AM (obtenu
via extraction.py — OCR ou lecture directe).

Approche : expressions régulières ciblées sur le gabarit observé dans les
AM réelles (cf. docs/database/conception -- exemples fournis par la
mairie de Nouna). Pas de NLP : le gabarit administratif est suffisamment
stable pour que des règles explicites, simples à expliquer et à défendre,
soient plus fiables qu'un modèle probabiliste sur un aussi petit corpus.

Chaque champ non trouvé reste à None -- à corriger manuellement lors de
l'étape de validation (jamais de fausse certitude affichée).

Correspondance avec les modèles (cf. cadrage fourni sur un exemple réel) :
    numero              -> Autorisation.numero
    date_demande        -> Demande.date_demande
    objet               -> Demande.objet
    date_evenement      -> Manifestation.datetime_debut
    espace              -> Manifestation.espace
    nom_demandeur/prenom_demandeur -> Demandeur.nom / Demandeur.prenom
    cnib_numero/cnib_date -> CNIB.numero / CNIB.date_cnib
    telephone           -> Demandeur.telephone
    lieu_signature/date_autorisation -> Autorisation.date_autorisation
    attribution/fonction -> Habilitation.attribution / Habilitation.fonction
    nom_signataire/prenom_signataire -> Personne.nom / Personne.prenom
    emploi              -> Personne.emploi
    grade               -> Personne.grade
"""
import re
from datetime import date

PATTERN_NUMERO = re.compile(
    r"N[°ºo]\s*([0-9][0-9A-Za-z\-\{\} /]{5,60})", re.IGNORECASE
)
PATTERN_DATE_DEMANDE = re.compile(r"en date du\s+([^;]+?)\s*;")

# Capture en un seul passage : l'objet de la manifestation, la date de
# l'événement (distincte de la date de la demande et de la date de
# signature), et l'espace où elle se déroule -- les trois étaient avant
# mélangés dans un seul bloc "objet", ce qui ne correspondait pas au
# découpage réel des modèles (Demande.objet / Manifestation.datetime_debut
# / Manifestation.espace sont trois champs distincts).
PATTERN_BLOC_MANIFESTATION = re.compile(
    r"d['’]organiser\s+(?P<objet>.+?)\s+le\s+\w+\s+"
    r"(?P<date_evenement>[0-9]{1,2}\s+\w+\s+[0-9]{4})\s+"
    r"(?:sur|à|dans)\s+(?P<espace>.+?)\s*,\s*est accord",
    re.S | re.IGNORECASE,
)

PATTERN_NOM_DEMANDEUR = re.compile(
    r"accord[ée]e?\s+à\s+(?:monsieur|madame)\s+"
    r"([A-ZÀ-Ü][A-Za-zÀ-ÿ'\-]*(?:\s+[A-ZÀ-Ü][A-Za-zÀ-ÿ'\-]*)*)\s*,",
    re.IGNORECASE,
)
PATTERN_CNIB = re.compile(
    r"N[°ºo]\s*([A-Z0-9]{5,15})\s+du\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})"
)
PATTERN_TELEPHONE = re.compile(r"tel\s*:\s*([\d\s]{8,15})", re.IGNORECASE)
PATTERN_LIEU_DATE_SIGNATURE = re.compile(
    r"^([A-ZÀ-Ü][a-zà-ÿ]+),\s*le\s+([0-9]{1,2}\s+\w+\s+[0-9]{4})\s*\.?\s*:?\s*$",
    re.MULTILINE,
)
PATTERN_DEBUT_AMPLIATIONS = re.compile(r"AMPLIATIONS?\s*:?", re.IGNORECASE)
# Marqueur de fin de bloc : le texte du blason/en-tête ("Unité - Progrès -
# Justice") qui suit souvent la liste des ampliations sur le document.
PATTERN_FIN_AMPLIATIONS = re.compile(r"unit[ée]\s*[-–]\s*progr[eè]s", re.IGNORECASE)

MOIS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12,
    "decembre": 12,
}


def normaliser_date_fr(texte_date: str):
    """
    Convertit une date en toutes lettres façon "06 juillet 2024" (avec
    tolérance sur les ordinaux OCR-bruités type "1°r" pour "1er") en
    objet date Python. Retourne None si le format n'est pas reconnu.
    """
    if not texte_date:
        return None
    texte_date = texte_date.strip().lower()
    match = re.search(r"(\d{1,2})\D*\s+(\w+)\s+(\d{4})", texte_date)
    if not match:
        return None
    jour, mois_texte, annee = match.groups()
    mois = MOIS_FR.get(mois_texte)
    if mois is None:
        return None
    try:
        return date(int(annee), mois, int(jour))
    except ValueError:
        return None


def nettoyer_numero(numero_brut: str) -> str:
    """
    Nettoie les artefacts OCR courants sur le numéro d'AM (accolades,
    espaces superflus autour des tirets) sans changer sa structure.
    """
    if not numero_brut:
        return numero_brut
    numero = numero_brut.replace("{", "").replace("}", "")
    numero = re.sub(r"\s*-\s*", "-", numero)
    numero = re.sub(r"\s+", " ", numero).strip()
    return numero


def _est_tout_majuscule(mot: str) -> bool:
    """Vrai si le mot est entièrement en majuscules (accents inclus)."""
    return mot.isupper() and any(c.isalpha() for c in mot)


def split_nom_prenom(texte_nom: str) -> tuple[str, str]:
    """
    Répartit "NACAMBO Soumaïla" ou "Ernest SIMBORO" en (nom, prenom), en se
    basant sur la casse plutôt que sur la position : le(s) mot(s) tout en
    majuscules est/sont le nom de famille (convention administrative
    courante), peu importe qu'il soit écrit avant ou après le prénom.
    Si aucun mot n'est tout en majuscules, retombe sur un simple découpage
    positionnel (premier mot = nom, reste = prénom) à corriger manuellement.
    """
    if not texte_nom:
        return "", ""
    mots = texte_nom.split()
    noms = [m for m in mots if _est_tout_majuscule(m)]
    prenoms = [m for m in mots if not _est_tout_majuscule(m)]
    if noms:
        return " ".join(noms), " ".join(prenoms)
    if len(mots) >= 2:
        return mots[0], " ".join(mots[1:])
    return texte_nom, ""


def parser_champs(texte: str) -> dict:
    """
    Retourne un dictionnaire de champs extraits, chacun potentiellement
    None si non trouvé. Ne lève jamais d'exception sur un champ manquant
    -- l'absence d'info est une donnée en soi (à corriger manuellement).
    """
    resultat = {
        "numero": None,
        "date_demande": None,
        "objet": None,
        "date_evenement": None,
        "espace": None,
        "nom_demandeur": None,
        "prenom_demandeur": None,
        "cnib_numero": None,
        "cnib_date": None,
        "telephone": None,
        "lieu_signature": None,
        "date_autorisation": None,
        "attribution": None,
        "fonction": None,
        "nom_signataire": None,
        "prenom_signataire": None,
        "emploi": None,
        "grade": None,
    }

    if not texte:
        return resultat

    if m := PATTERN_NUMERO.search(texte):
        resultat["numero"] = nettoyer_numero(m.group(1))

    if m := PATTERN_DATE_DEMANDE.search(texte):
        resultat["date_demande"] = normaliser_date_fr(m.group(1))

    if m := PATTERN_BLOC_MANIFESTATION.search(texte):
        resultat["objet"] = re.sub(r"\s+", " ", m.group("objet")).strip()
        resultat["date_evenement"] = normaliser_date_fr(m.group("date_evenement"))
        resultat["espace"] = re.sub(r"\s+", " ", m.group("espace")).strip()

    if m := PATTERN_NOM_DEMANDEUR.search(texte):
        nom_complet = re.sub(r"\s+", " ", m.group(1)).strip()
        nom, prenom = split_nom_prenom(nom_complet)
        resultat["nom_demandeur"] = nom
        resultat["prenom_demandeur"] = prenom

    if m := PATTERN_CNIB.search(texte):
        resultat["cnib_numero"] = m.group(1)
        resultat["cnib_date"] = normaliser_date_fr(m.group(2))

    if m := PATTERN_TELEPHONE.search(texte):
        resultat["telephone"] = re.sub(r"\s+", "", m.group(1))

    if m := PATTERN_LIEU_DATE_SIGNATURE.search(texte):
        resultat["lieu_signature"] = m.group(1)
        resultat["date_autorisation"] = normaliser_date_fr(m.group(2))

    signataire = parser_signataire(texte)
    resultat.update(signataire)

    return resultat


def parser_signataire(texte: str) -> dict:
    """
    Extrait le bloc signataire, situé après la mention lieu/date de
    signature (ex: "Nouna, le 02 juillet 2024"). Approche ligne par ligne
    plutôt que regex globale : ce bloc est très variable en mise en page
    (nombre de lignes de titre, présence ou non d'un tampon qui perturbe
    l'OCR), donc une heuristique séquentielle tolère mieux le bruit qu'un
    unique pattern rigide.

    Repère la ligne "nom" par la présence d'un mot tout en majuscules
    (le nom de famille), qu'il soit en première ou deuxième position.
    """
    resultat = {
        "attribution": None,
        "fonction": None,
        "nom_signataire": None,
        "prenom_signataire": None,
        "emploi": None,
        "grade": None,
    }

    lignes = [l.strip() for l in texte.split("\n") if l.strip()]

    idx_lieu = None
    for i, ligne in enumerate(lignes):
        if PATTERN_LIEU_DATE_SIGNATURE.match(ligne):
            idx_lieu = i
            break

    if idx_lieu is None:
        return resultat

    if idx_lieu + 1 < len(lignes):
        resultat["attribution"] = lignes[idx_lieu + 1]
    if idx_lieu + 2 < len(lignes):
        resultat["fonction"] = lignes[idx_lieu + 2]

    idx_nom = None
    for i in range(idx_lieu + 3, len(lignes)):
        mots = lignes[i].split()
        if 1 < len(mots) <= 4 and any(_est_tout_majuscule(m) for m in mots):
            idx_nom = i
            break

    if idx_nom is None:
        return resultat

    nom, prenom = split_nom_prenom(lignes[idx_nom])
    resultat["nom_signataire"] = nom
    resultat["prenom_signataire"] = prenom

    if idx_nom + 1 < len(lignes):
        resultat["emploi"] = lignes[idx_nom + 1]
    if idx_nom + 2 < len(lignes):
        resultat["grade"] = lignes[idx_nom + 2]

    return resultat


def extraire_ampliations(texte: str) -> list[str]:
    """
    Extrait la liste des destinataires d'ampliation (section "AMPLIATIONS"
    en bas de l'AM : Haut-Commissariat, DP/Culture, Gendarmerie, Police,
    Archives/Chrono...). Chaque ligne du bloc est un candidat de label,
    nettoyé des puces ("-", "*") -- mais PAS corrigé du bruit OCR, qui est
    géré séparément par la dédup approximative (voir validators.py,
    find_or_create_ampliation) au moment de la création en base.

    Retourne une liste de chaînes brutes (potentiellement bruitées),
    filtrées pour exclure les lignes trop courtes pour être un vrai label
    (artefacts OCR isolés du type ponctuation seule).
    """
    m_debut = PATTERN_DEBUT_AMPLIATIONS.search(texte)
    if not m_debut:
        return []

    bloc = texte[m_debut.end():]
    m_fin = PATTERN_FIN_AMPLIATIONS.search(bloc)
    if m_fin:
        bloc = bloc[:m_fin.start()]

    candidats = []
    for ligne in bloc.split("\n"):
        ligne = ligne.strip().lstrip("-*•").strip()
        lettres = re.sub(r"[^a-zA-ZÀ-ÿ]", "", ligne)
        if len(lettres) >= 3:
            candidats.append(ligne)

    return candidats
