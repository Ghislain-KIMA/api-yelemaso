"""
Logique de déduplication utilisée lors de la synchronisation ascendante
(un poste local peut créer un Agent ou une Habilitation hors ligne ; le
central doit éviter les doublons plutôt que de bloquer sur une contrainte
d'unicité brute).
"""
import difflib
import re

import phonenumbers

SEUIL_SIMILARITE_AMPLIATION = 0.80


def normaliser_telephone(numero: str, region: str = "BF") -> str | None:
    """
    Normalise un numéro de téléphone au format E.164 (ex: +22670123456),
    en s'appuyant sur phonenumbers (portage Python de libphonenumber,
    Google). Retourne None si le numéro est vide ou invalide.
    """
    if not numero or not numero.strip():
        return None
    try:
        parsed = phonenumbers.parse(numero, region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        return None


def find_or_none_by_telephone(model, telephone: str):
    """
    Recherche une correspondance existante par téléphone, après
    normalisation E.164 — évite qu'un même agent/signataire saisi avec un
    formatage différent (espaces, tirets, absence d'indicatif) soit traité
    comme une personne différente lors de la synchronisation.
    """
    normalized = normaliser_telephone(telephone)
    if normalized is None:
        return None
    return model.objects.filter(telephone=normalized).first()


def find_or_none_by_fields(model, **fields):
    """
    Recherche générique par égalité stricte sur plusieurs champs.
    Utilisée pour les modèles sans identifiant fiable de type téléphone
    (ex: Habilitation, dédupliquée sur fonction+attribution).
    Moins fiable qu'une dédup par téléphone (deux personnes peuvent
    partager le même nom), mais évite les doublons évidents.
    """
    return model.objects.filter(**fields).first()


def _normaliser_label(label: str) -> str:
    """
    Normalisation légère avant comparaison : espaces, casse, et un simple
    retrait du 's' final (gère le cas le plus courant de pluriel, sans
    prétendre gérer toutes les règles de pluriel du français).
    """
    label = re.sub(r"\s+", " ", label).strip().lower()
    return label.rstrip("s")


def find_or_create_ampliation(label_brut: str):
    """
    Recherche une Ampliation existante dont le label est une quasi-
    correspondance de label_brut (pluriel, casse différente, léger bruit
    OCR), plutôt qu'une égalité stricte -- utile car ces variations sont
    fréquentes ("Police"/"police", "Archives/Chrono"/"Archives/Chronos")
    et ne doivent pas produire des doublons distincts dans le catalogue.

    Le seuil (SEUIL_SIMILARITE_AMPLIATION = 0.80) a été choisi pour
    accepter les variations mineures (accents, pluriel, casse, une lettre
    OCR mal reconnue) tout en refusant les correspondances trop
    approximatives (une Ampliation gravement mal lue par l'OCR sera créée
    comme nouvelle entrée plutôt que fusionnée à tort avec une existante
    -- à corriger ensuite manuellement par le centre, comme pour les
    tables *_Autre).

    Retourne (ampliation, cree: bool).
    """
    from apps.gestion.models import Ampliation

    label_normalise = _normaliser_label(label_brut)

    meilleure = None
    meilleur_score = 0.0
    for ampliation in Ampliation.objects.all():
        score = difflib.SequenceMatcher(
            None, _normaliser_label(ampliation.label), label_normalise
        ).ratio()
        if score > meilleur_score:
            meilleur_score = score
            meilleure = ampliation

    if meilleure is not None and meilleur_score >= SEUIL_SIMILARITE_AMPLIATION:
        return meilleure, False

    nouvelle = Ampliation.objects.create(label=label_brut.strip())
    return nouvelle, True
