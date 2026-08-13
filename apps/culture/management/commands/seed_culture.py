"""
Peuple Mode_Acces, Genre, Type_Manifestation, Periodicite, Dimension,
Type_Espace depuis les fichiers .xlsx placés dans
docs/database/seeds/culture/source/.

Usage :
    python manage.py seed_culture

Idempotent : peut être relancée sans jamais créer de doublon.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.culture.models import Dimension, Genre, ModeAcces, Periodicite, TypeEspace, TypeManifestation
from core.seed_utils import ouvrir_classeurs, seed_labels, trouver_fichiers_source

DOSSIER_SOURCE = Path(settings.BASE_DIR) / "docs" / "database" / "seeds" / "culture" / "source"

# (nom_feuille_excel, modele)
TABLES = [
    ("Mode_Acces", ModeAcces),
    ("Genre", Genre),
    ("Type_Manifestation", TypeManifestation),
    ("Periodicite", Periodicite),
    ("Dimension", Dimension),
    ("Type_Espace", TypeEspace),
]


class Command(BaseCommand):
    help = "Peuple les tables de référence culture depuis les .xlsx."

    def handle(self, *args, **options):
        chemins = trouver_fichiers_source(str(DOSSIER_SOURCE))
        if not chemins:
            self.stderr.write(self.style.ERROR(
                f"Aucun fichier .xlsx dans {DOSSIER_SOURCE} -- rien à faire."
            ))
            return

        self.stdout.write(f"Fichiers source : {chemins}")
        classeurs = ouvrir_classeurs(chemins)

        for nom_feuille, model in TABLES:
            self.stdout.write(f"{model.__name__}...")
            n = seed_labels(model, classeurs, nom_feuille, stdout=self.stdout)
            self.stdout.write(self.style.SUCCESS(f"  {n} créé(s)"))
