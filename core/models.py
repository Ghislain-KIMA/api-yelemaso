"""
Classes de base abstraites, une par schéma, pour éviter de répéter la
logique de qualification du nom de table sur chaque modèle.
"""
import uuid

from django.db import models


class UUIDModel(models.Model):
    """
    Base pour les entités identifiées par UUID (données produites par les
    postes locaux, potentiellement hors ligne : Demandeur, Autorisation,
    Manifestation, Agent, Poste, Personne, Habilitation, Ampliation, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        abstract = True


class ReferenceModel(models.Model):
    """
    Base pour les tables de référence (listes fixes gérées côté central :
    Genre, Mode_Acces, Region, Province, etc.) — clé technique SMALLINT.
    """
    id = models.SmallAutoField(primary_key=True)

    class Meta:
        abstract = True
