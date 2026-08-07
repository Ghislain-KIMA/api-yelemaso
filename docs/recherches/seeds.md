
Bien, on part de zéro chez toi. Je découpe en 6 étapes, chacune avec son propre commit suggéré — comme ça ton historique Git reste propre et compréhensible.

## Étape 1 — L'utilitaire partagé

Crée le fichier `core/seed_utils.py` :

```python
"""
Utilitaire de seed pour les tables de référence simples (une seule colonne
"label", ex: Genre, Type_Manifestation, Statut_Demandeur, Ampliation...).

Toujours idempotent (get_or_create) : relancer une commande de seed
plusieurs fois ne crée jamais de doublon.
"""
import csv
from pathlib import Path


def seed_labels(model, chemin_csv: Path, colonne: str = "label", stdout=None) -> int:
    """
    Lit un CSV à une colonne (par défaut 'label') et crée les objets du
    modèle donné qui n'existent pas encore (matching par cette colonne).
    Retourne le nombre d'objets réellement créés.
    """
    if not chemin_csv.exists():
        raise FileNotFoundError(
            f"Fichier de seed introuvable : {chemin_csv}. "
            f"Placez-y le CSV exporté depuis Excel (encodage UTF-8)."
        )

    nb_crees = 0
    with open(chemin_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            valeur = row[colonne].strip()
            if not valeur:
                continue
            _, cree = model.objects.get_or_create(**{colonne: valeur})
            if cree:
                nb_crees += 1
                if stdout:
                    stdout.write(f"  + {model.__name__} créé : {valeur}")
    return nb_crees
```

**Commit** :

```bash
git add core/seed_utils.py
git commit -m "feat(core): ajouter seed_labels, utilitaire partagé pour peupler les tables de référence"
```

---

## Étape 2 — Commande `seed_administration`

Crée les dossiers et fichiers vides nécessaires :

```bash
mkdir -p apps/administration/management/commands
mkdir -p apps/administration/seed_data
touch apps/administration/management/__init__.py
touch apps/administration/management/commands/__init__.py
```

Puis crée `apps/administration/management/commands/seed_administration.py` :

```python
"""
Peuple les tables de référence administratives à partir de fichiers CSV
(exportés depuis Excel en "CSV UTF-8", placés dans apps/administration/seed_data/).

Usage :
    python manage.py seed_administration

Idempotent : peut être relancée sans jamais créer de doublon.
"""
import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.administration.models import Commune, Province, Region, TypeCommune, TypeMairie
from core.seed_utils import seed_labels

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed_data"


class Command(BaseCommand):
    help = "Peuple Region, Province, Commune, Type_Commune, Type_Mairie depuis les CSV."

    def handle(self, *args, **options):
        self.stdout.write("Type_Commune...")
        n = seed_labels(TypeCommune, SEED_DIR / "type_commune.csv", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(f"  {n} créé(s)"))

        self.stdout.write("Type_Mairie...")
        n = seed_labels(TypeMairie, SEED_DIR / "type_mairie.csv", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(f"  {n} créé(s)"))

        self.stdout.write("Region...")
        n = seed_labels(Region, SEED_DIR / "regions.csv", colonne="nom_region", stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(f"  {n} créé(s)"))

        self.stdout.write("Province...")
        n = self._seed_provinces()
        self.stdout.write(self.style.SUCCESS(f"  {n} créée(s)"))

        self.stdout.write("Commune...")
        n = self._seed_communes()
        self.stdout.write(self.style.SUCCESS(f"  {n} créée(s)"))

    def _seed_provinces(self) -> int:
        chemin = SEED_DIR / "provinces.csv"
        if not chemin.exists():
            raise FileNotFoundError(f"Fichier introuvable : {chemin}")

        nb_crees = 0
        with open(chemin, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                nom_province = row["nom_province"].strip()
                nom_region = row["nom_region"].strip()
                try:
                    region = Region.objects.get(nom_region=nom_region)
                except Region.DoesNotExist:
                    self.stderr.write(
                        f"  ! Region introuvable pour '{nom_province}' : "
                        f"'{nom_region}' -- ligne ignorée. Vérifiez l'orthographe "
                        f"exacte (doit correspondre à regions.csv)."
                    )
                    continue
                _, cree = Province.objects.get_or_create(
                    nom_province=nom_province, region=region
                )
                if cree:
                    nb_crees += 1
                    self.stdout.write(f"  + Province créée : {nom_province}")
        return nb_crees

    def _seed_communes(self) -> int:
        chemin = SEED_DIR / "communes.csv"
        if not chemin.exists():
            raise FileNotFoundError(f"Fichier introuvable : {chemin}")

        nb_crees = 0
        with open(chemin, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                nom_commune = row["nom_commune"].strip()
                nom_province = row["nom_province"].strip()
                label_type_commune = row["type_commune"].strip()

                try:
                    province = Province.objects.get(nom_province=nom_province)
                except Province.DoesNotExist:
                    self.stderr.write(
                        f"  ! Province introuvable pour '{nom_commune}' : "
                        f"'{nom_province}' -- ligne ignorée."
                    )
                    continue
                try:
                    type_commune = TypeCommune.objects.get(label=label_type_commune)
                except TypeCommune.DoesNotExist:
                    self.stderr.write(
                        f"  ! Type_Commune introuvable pour '{nom_commune}' : "
                        f"'{label_type_commune}' -- ligne ignorée. Valeurs "
                        f"attendues : rurale / urbaine / statut particulier."
                    )
                    continue

                _, cree = Commune.objects.get_or_create(
                    nom_commune=nom_commune,
                    province=province,
                    defaults={"type_commune": type_commune},
                )
                if cree:
                    nb_crees += 1
                    self.stdout.write(f"  + Commune créée : {nom_commune}")
        return nb_crees
```

Crée aussi les 5 CSV dans `apps/administration/seed_data/` (remplace par tes vraies données ensuite) :

`type_commune.csv` :

```csv
label
rurale
urbaine
statut particulier
```

`type_mairie.csv` :

```csv
label
Centrale
Arrondissement
```

`regions.csv`, `provinces.csv`, `communes.csv` — utilise directement tes propres données Excel exportées, avec les colonnes vues précédemment (`nom_region` / `nom_province,nom_region` / `nom_commune,nom_province,type_commune`).

**Commit** :

```bash
git add apps/administration/management/ apps/administration/seed_data/
git commit -m "feat(administration): ajouter la commande seed_administration"
```

---

Dis-moi quand tu as fini ces deux étapes et testé (`python manage.py seed_administration`), et je te donne les étapes 3 à 6 (`seed_culture`, `seed_gestion`, et la mise à jour du README) — je préfère avancer par petits blocs vérifiables plutôt que de tout déverser d'un coup.
