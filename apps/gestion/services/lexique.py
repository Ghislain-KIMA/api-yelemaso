"""
Suggestion de classification (Genre, Type_Manifestation) à partir du
texte libre décrivant l'événement (le champ "objet" extrait de l'AM).

Ce n'est PAS une extraction (l'info n'est jamais écrite littéralement
dans le document) : c'est une interprétation par mots-clés, toujours
proposée comme suggestion à valider/corriger par un humain -- jamais
appliquée automatiquement sans confirmation.

Les mots-clés sont volontairement en minuscules, la recherche se fait sur
le texte normalisé (accents conservés, casse ignorée).
"""
import unicodedata

# mot-clé -> (label Genre ou None, label Type_Manifestation ou None)
LEXIQUE: dict[str, tuple[str | None, str | None]] = {
    "tournoi": ("Sportif", "Tournoi"),
    "maracana": ("Sportif", "Tournoi"),
    "match": ("Sportif", "Compétition sportive"),
    "competition sportive": ("Sportif", "Compétition sportive"),
    "concert": ("Musique", "Concert"),
    "festival": ("Multi genre", "Festival"),
    "foire": (None, "Foire"),
    "exposition": ("Peinture", "Exposition"),
    "conte": ("Conte", "Représentation"),
    "theatre": ("Théâtre", "Représentation"),
    "marionnette": ("Marionnette", "Représentation"),
    "projection": ("Audiovisuel", "Projection"),
    "cinema": ("Cinéma", "Projection"),
    "danse": ("Danse", "Animation"),
    "assemblee generale": ("Communautaire/Associatif", "Assemblée générale / Réunion associative"),
    "reunion associative": ("Communautaire/Associatif", "Assemblée générale / Réunion associative"),
    "ceremonie religieuse": ("Religieux/Cultuel", "Cérémonie religieuse"),
    "culte": ("Religieux/Cultuel", "Cérémonie religieuse"),
    "funerailles": (None, "Funérailles traditionnelles"),
    "journee des communautes": (None, "Journée des communautés"),
    "gastronomie": ("Gastronomie / Art Culinaire", None),
    "defile de mode": ("Mode/Défilé de mode", None),
    "artisanat": ("Artisanat", None),
    "sculpture": ("Sculpture", None),
    "photographie": ("Photographie", None),
    "poesie": ("Littérature / Poésie / Slam", None),
    "slam": ("Littérature / Poésie / Slam", None),
}


def _normaliser(texte: str) -> str:
    """Minuscule, sans accents -- pour une recherche de mot-clé robuste."""
    texte = texte.lower()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return texte


# Le lexique est indexé avec accents retirés pour matcher _normaliser()
_LEXIQUE_NORMALISE = {_normaliser(cle): valeur for cle, valeur in LEXIQUE.items()}


def suggerer_classification(objet_texte: str) -> dict:
    """
    Cherche le premier mot-clé du lexique présent dans le texte, et
    retourne la suggestion correspondante. Retourne {"genre": None,
    "type_manifestation": None} si rien ne correspond -- l'utilisateur
    devra choisir manuellement, sans suggestion trompeuse.
    """
    resultat = {"genre": None, "type_manifestation": None}
    if not objet_texte:
        return resultat

    texte_normalise = _normaliser(objet_texte)
    for mot_cle, (genre, type_manif) in _LEXIQUE_NORMALISE.items():
        if mot_cle in texte_normalise:
            resultat["genre"] = genre
            resultat["type_manifestation"] = type_manif
            break

    return resultat
