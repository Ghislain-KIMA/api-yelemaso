"""
Peuple Statut_Demandeur et Ampliation depuis les fichiers .xlsx placés
dans docs/database/seeds/gestion/source/.

Usage :
    python manage.py seed_gestion

Idempotent : peut être relancée sans jamais créer de doublon.

Note sur Ampliation : contrairement à Statut_Demandeur, Ampliation peut
aussi être créée/enrichie automatiquement pendant l'extraction de
documents (voir find_or_create_ampliation dans validators.py, avec
déduplication approximative). Ce seed sert juste à préremplir les
valeurs déjà connues (Haut-Commissariat, Police, Gendarmerie...) avant
le premier document traité.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.gestion.models import Ampliation, StatutDemandeur
from core.seed_utils import ouvrir_classeurs, seed_labels, trouver_fichiers_source

DOSSIER_SOURCE = Path(settings.BASE_DIR) / "docs" / "database" / "seeds" / "gestion" / "source"

TABLES = [
    ("Statut_Demandeur", StatutDemandeur),
    ("Ampliation", Ampliation),
]


class Command(BaseCommand):
    help = "Peuple Statut_Demandeur et Ampliation depuis les .xlsx."

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
