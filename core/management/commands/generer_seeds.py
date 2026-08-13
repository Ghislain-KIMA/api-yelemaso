"""
Commande principale unique qui lance seed_administration, seed_culture et
seed_gestion à la suite -- équivalent de "python manage.py collectstatic" pour
toutes les tables de référence du projet.

Usage :
    python manage.py generer_seeds

(securite n'a actuellement aucune table de référence à peupler -- Poste et
Agent sont produits par l'extraction de  documents, pas seedés.)
"""



from django.core.management import call_command
from django.core.management.base import BaseCommand



class Command(BaseCommand):
    help = "Lance seed_administration, seed_culture et seed_gestion à la suite."

    def handle(self, *args, **options):
        for nom_commande in ["seed_administration", "seed_culture", "seed_gestion"]:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n=== {nom_commande} ==="))
            call_command(nom_commande)

        self.stdout.write(self.style.SUCCESS("\nTerminé."))
