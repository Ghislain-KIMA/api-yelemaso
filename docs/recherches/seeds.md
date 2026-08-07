Bonne nouvelle, l'export CSV va bien plus simplifier les choses. Deux points avant le code : le format d'export, puis la structure de fichiers attendue par app.

**Export depuis Excel — un point à ne pas rater**

Utilise **"CSV UTF-8 (délimité par des virgules)"** dans Excel (`Fichier > Enregistrer sous`), pas le simple "CSV" — sinon les accents français (`é`, `è`, `à`...) risquent d'être mal encodés à la lecture en Python.

**Structure de fichiers attendue, par app**

| App                | Fichier                    | Colonnes                                            |
| ------------------ | -------------------------- | --------------------------------------------------- |
| `administration` | `regions.csv`            | `nom_region`                                      |
| `administration` | `provinces.csv`          | `nom_province`, `nom_region`                    |
| `administration` | `communes.csv`           | `nom_commune`, `nom_province`, `type_commune` |
| `administration` | `type_commune.csv`       | `label`                                           |
| `administration` | `type_mairie.csv`        | `label`                                           |
| `culture`        | `genre.csv`              | `label`                                           |
| `culture`        | `type_manifestation.csv` | `label`                                           |
| `culture`        | `periodicite.csv`        | `label`                                           |
| `culture`        | `dimension.csv`          | `label`                                           |
| `culture`        | `type_espace.csv`        | `label`                                           |
| `culture`        | `mode_acces.csv`         | `label`                                           |
| `gestion`        | `statut_demandeur.csv`   | `label`                                           |
| `gestion`        | `ampliation.csv`         | `label`                                           |

Je crée un utilitaire partagé (`core/seed_utils.py`) pour éviter de répéter la même logique "lire un CSV à une colonne `label`, `get_or_create`" dans 8 tables différentes :Le container a été réinitialisé, mais le zip est toujours là — je le restaure avant d'ajouter les scripts de seed :Restauré. Je crée l'utilitaire partagé et les trois commandes de seed :Créons des fichiers CSV d'exemple (avec des données réalistes, style Ampliation/Statut_Demandeur qu'on avait déjà définies dans le MCD) pour que tu voies le format exact et que le tout se teste réellement :Testons réellement les trois commandes sur une base SQLite temporaire :Django n'est plus installé (container réinitialisé). Je le réinstalle pour terminer le test :Migré. Maintenant testons les trois commandes de seed :Parfait, la hiérarchie complète (Région → Province → Commune) se crée correctement, avec matching réussi sur les clés naturelles. Testons `culture` et `gestion`, puis l'idempotence :Tout se peuple correctement. Testons maintenant l'**idempotence** — relancer une deuxième fois doit créer zéro doublon :**Idempotence confirmée** : zéro doublon au deuxième passage, les comptes restent stables. Nettoyage et livraison :Ajout d'une note dans le README pour documenter ces commandes :## Résumé — testé de bout en bout

**3 commandes créées** : `seed_administration` (Region/Province/Commune/Type_Commune/Type_Mairie, avec matching en cascade sur les clés naturelles), `seed_culture` (les 6 référentiels culturels), `seed_gestion` (Statut_Demandeur/Ampliation) — toutes construites sur un utilitaire partagé `core/seed_utils.py`.

**Réellement testé** : les 3 commandes exécutées sur une vraie base SQLite, avec des CSV d'exemple (contenant les valeurs qu'on avait déjà définies ensemble dans le MCD). **Idempotence vérifiée** : relancées une deuxième fois, elles affichent bien `0 créé(s)` partout, comptes stables.

**Ce que tu dois faire maintenant**

1. **Exporte tes fichiers Excel en "CSV UTF-8"** (important pour les accents) — un fichier par table, dans `apps/<app>/seed_data/`, selon le tableau de colonnes attendu que je t'ai donné plus haut.
2. Remplace mes CSV d'exemple (4 régions, 4 communes... juste pour tester) par tes vraies données complètes.
3. Lance les 3 commandes dans l'ordre : `seed_administration`, `seed_culture`, `seed_gestion`.

**Un point d'attention pour `communes.csv`** : la commande **ignore silencieusement** (avec message d'erreur affiché, pas de crash) toute ligne où `nom_province` ou `type_commune` ne correspond pas exactement à une valeur déjà en base — vérifie bien l'orthographe exacte (accents compris) entre tes fichiers `provinces.csv` et `communes.csv`.

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
