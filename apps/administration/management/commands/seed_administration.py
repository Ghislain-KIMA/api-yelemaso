"""
Peuple Region, Province, Commune, Type_Commune, Type_Mairie depuis les fichiers .xlsx placés dans 
docs/database/seeds/administration/source/.

Usage :
    python manage.py seed_administration

Idempotent : peut être relancée sans jamais créer de doublon.
"""



from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.administration.models import Commune, Province, Region, TypeCommune, TypeMairie
from core.seed_utils import lire_lignes, ouvrir_classeurs, trouver_feuille, trouver_fichiers_source



DOSSIER_SOURCE = Path(settings.BASE_DIR) / "docs" / "database" / "seeds" / "administration" / "source"



class Command(BaseCommand):
    help = "Peuple Region, Province, Commune, Type_Commune, Type_Mairie depuis les .xlsx."

    def handle(self, *args, **options):
        chemins = trouver_fichiers_source(str(DOSSIER_SOURCE))
        if not chemins:
            self.stderr.write(self.style.ERROR(
                f"Aucun fichier .xlsx dans {DOSSIER_SOURCE} -- rien à faire."
            ))
            return

        self.stdout.write(f"Fichiers source : {chemins}")
        classeurs = ouvrir_classeurs(chemins)

        self.stdout.write("Type_Commune...")
        n = self._seed_type_commune(classeurs)
        self.stdout.write(self.style.SUCCESS(f"  {n} créé(s)"))

        self.stdout.write("Type_Mairie...")
        n = self._seed_type_mairie(classeurs)
        self.stdout.write(self.style.SUCCESS(f"  {n} créé(s)"))

        self.stdout.write("Region...")
        n = self._seed_regions(classeurs)
        self.stdout.write(self.style.SUCCESS(f"  {n} créée(s)"))

        self.stdout.write("Province...")
        n = self._seed_provinces(classeurs)
        self.stdout.write(self.style.SUCCESS(f"  {n} créée(s)"))

        self.stdout.write("Commune...")
        n = self._seed_communes(classeurs)
        self.stdout.write(self.style.SUCCESS(f"  {n} créée(s)"))

    # Type_Commune et Type_Mairie sont des vocabulaires fixes (3 et 2
    # valeurs, définies dans le MCD) -- on les crée directement plutôt
    # que via seed_labels générique, pour rester explicite sur la liste
    # attendue et détecter une valeur inattendue dans le fichier source.
    def _seed_type_commune(self, classeurs) -> int:
        attendues = ["rurale", "urbaine", "statut particulier"]
        return self._seed_vocabulaire_fixe(classeurs, "Type_Commune", TypeCommune, attendues)

    def _seed_type_mairie(self, classeurs) -> int:
        attendues = ["Centrale", "Arrondissement"]
        return self._seed_vocabulaire_fixe(classeurs, "Type_Mairie", TypeMairie, attendues)

    def _seed_vocabulaire_fixe(self, classeurs, nom_feuille, model, attendues) -> int:
        chemin, feuille = trouver_feuille(classeurs, nom_feuille, stdout=self.stdout)
        if feuille is None:
            self.stdout.write(f"  ! Feuille '{nom_feuille}' absente -- ignorée.")
            return 0
        lignes = lire_lignes(feuille, {"label": "label"})
        nb_crees = 0
        for ligne in lignes:
            label = ligne["label"]
            if not label:
                continue
            label = str(label).strip()
            correspondances = [v for v in attendues if v.lower() == label.lower()]
            if not correspondances:
                self.stderr.write(
                    f"  ! '{label}' ne correspond à aucune valeur attendue "
                    f"({attendues}) -- ignoré."
                )
                continue
            _, cree = model.objects.get_or_create(label=correspondances[0])
            if cree:
                nb_crees += 1
                self.stdout.write(f"  + {model.__name__} créé : {correspondances[0]}")
        return nb_crees

    def _seed_regions(self, classeurs) -> int:
        chemin, feuille = trouver_feuille(classeurs, "Region", stdout=self.stdout)
        if feuille is None:
            self.stderr.write("  ! Feuille 'Region' introuvable.")
            return 0
        nb_crees = 0
        for ligne in lire_lignes(feuille, {"nom": "nom_region"}):
            nom = ligne["nom"]
            if not nom:
                continue
            _, cree = Region.objects.get_or_create(nom_region=str(nom).strip())
            if cree:
                nb_crees += 1
                self.stdout.write(f"  + Region créée : {nom}")
        return nb_crees

    def _seed_provinces(self, classeurs) -> int:
        chemin, feuille = trouver_feuille(classeurs, "Province", stdout=self.stdout)
        if feuille is None:
            self.stderr.write("  ! Feuille 'Province' introuvable.")
            return 0
        nb_crees = 0
        for ligne in lire_lignes(feuille, {"nom": "nom_province", "region": "nom_region"}):
            nom_province = ligne["nom"]
            nom_region = ligne["region"]
            if not nom_province:
                continue
            try:
                region = Region.objects.get(nom_region=str(nom_region).strip())
            except Region.DoesNotExist:
                self.stderr.write(
                    f"  ! Region introuvable pour '{nom_province}' : "
                    f"'{nom_region}' -- ligne ignorée."
                )
                continue
            _, cree = Province.objects.get_or_create(
                nom_province=str(nom_province).strip(), region=region
            )
            if cree:
                nb_crees += 1
                self.stdout.write(f"  + Province créée : {nom_province}")
        return nb_crees

    def _seed_communes(self, classeurs) -> int:
        chemin, feuille = trouver_feuille(classeurs, "Commune", stdout=self.stdout)
        if feuille is None:
            self.stderr.write("  ! Feuille 'Commune' introuvable.")
            return 0
        nb_crees = 0
        colonnes = {"nom": "nom_commune", "province": "nom_province", "type_commune": "type_commune"}
        for ligne in lire_lignes(feuille, colonnes):
            nom_commune = ligne["nom"]
            nom_province = ligne["province"]
            label_type_commune = ligne.get("type_commune")
            if not nom_commune:
                continue

            try:
                province = Province.objects.get(nom_province=str(nom_province).strip())
            except Province.DoesNotExist:
                self.stderr.write(
                    f"  ! Province introuvable pour '{nom_commune}' : "
                    f"'{nom_province}' -- ligne ignorée."
                )
                continue

            type_commune = None
            if label_type_commune:
                type_commune = TypeCommune.objects.filter(
                    label__iexact=str(label_type_commune).strip()
                ).first()
                if type_commune is None:
                    self.stderr.write(
                        f"  ! Type_Commune '{label_type_commune}' inconnu pour "
                        f"'{nom_commune}' -- laissé vide."
                    )

            _, cree = Commune.objects.get_or_create(
                nom_commune=str(nom_commune).strip(),
                province=province,
                defaults={"type_commune": type_commune},
            )
            if cree:
                nb_crees += 1
                self.stdout.write(f"  + Commune créée : {nom_commune}")
        return nb_crees
