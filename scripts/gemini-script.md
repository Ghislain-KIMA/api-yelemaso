C'est un excellent cas d'usage pour une commande personnalisée (*Custom Management Command*) Django !

Voici la démarche complète et le code pour mettre en place cette commande (par exemple `python manage.py convert_seeds` ou `generate_fixtures`).

---

### 1. Prérequis : Dépendance Excel

Assurez-vous que la bibliothèque `openpyxl` est installée dans votre environnement virtuel :

```bash
pip install openpyxl
```

---

### 2. Emplacement du fichier de commande

Créez l'arborescence suivante dans l'une de vos applications Django principales (ou une application globale `core` / `common`) :

```text
api-yelemaso/
└── apps/
    └── core/ (ou n'importe quelle app installée)
        ├── management/
        │   ├── __init__.py
        │   └── commands/
        │       ├── __init__.py
        │       └── convert_seeds.py  <-- Votre commande
```

---

### 3. Code de la commande (`convert_seeds.py`)

Voici le code complet. Il gère deux formats au choix :

1. **JSON brut / clé-valeur** (simple tableau d'objets)
2. **Format Fixture Django native** (avec `model`, `pk`, et `fields`) — *activable avec l'option `--django-format*`.

```python
import json
from pathlib import Path
import openpyxl

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Transforme les fichiers Excel (.xlsx) contenus dans "
        "docs/database/seeds/<app-name>/source/ en fichiers JSON "
        "placés dans apps/<app-name>/fixtures/."
    )

    def add_arguments(self, parser):
        # Option pour cibler une application spécifique
        parser.add_argument(
            '--app',
            type=str,
            help="Nom d'une application spécifique à traiter (ex: --app users)"
        )
        # Option pour formater sous forme de Fixture Django native
        parser.add_argument(
            '--django-format',
            action='store_true',
            help="Génère du JSON au format fixture Django native (model, pk, fields)."
        )

    def handle(self, *args, **options):
        target_app = options.get('app')
        use_django_format = options.get('django_format')

        # Racine du projet (BASE_DIR)
        base_dir = Path(settings.BASE_DIR)
        seeds_base_dir = base_dir / 'docs' / 'database' / 'seeds'

        if not seeds_base_dir.exists():
            raise CommandError(f"Le dossier source des seeds n'existe pas : {seeds_base_dir}")

        # Liste des dossiers d'applications sous docs/database/seeds/
        app_folders = [d for d in seeds_base_dir.iterdir() if d.is_dir()]

        if target_app:
            app_folders = [d for d in app_folders if d.name == target_app]
            if not app_folders:
                raise CommandError(f"Aucun dossier de seed trouvé pour l'app : {target_app}")

        total_files_processed = 0

        for app_folder in app_folders:
            app_name = app_folder.name
            source_dir = app_folder / 'source'

            if not source_dir.exists():
                self.stdout.write(self.style.WARNING(f"[-] Pas de dossier 'source' trouvé pour l'app '{app_name}'."))
                continue

            # Dossier destination : api-yelemaso/apps/<app-name>/fixtures/
            fixtures_dir = base_dir / 'apps' / app_name / 'fixtures'
            fixtures_dir.mkdir(parents=True, exist_ok=True)

            excel_files = list(source_dir.glob('*.xlsx'))
            if not excel_files:
                self.stdout.write(self.style.WARNING(f"[-] Aucun fichier .xlsx trouvé dans {source_dir}"))
                continue

            for excel_file in excel_files:
                self.stdout.write(f" Traitement de {excel_file.relative_to(base_dir)}...")
                self.convert_excel_to_json(
                    excel_path=excel_file,
                    output_dir=fixtures_dir,
                    app_name=app_name,
                    use_django_format=use_django_format
                )
                total_files_processed += 1

        self.stdout.write(self.style.SUCCESS(f"\n Conversion terminée ! {total_files_processed} fichier(s) traité(s)."))

    def convert_excel_to_json(self, excel_path: Path, output_dir: Path, app_name: str, use_django_format: bool):
        """
        Lit toutes les feuilles d'un fichier Excel et crée un fichier .json par feuille
        (ou un seul fichier portant le nom de l'Excel si une seule feuille existe).
        """
        # openpyxl : data_only=True permet de lire les valeurs calculées et non les formules
        wb = openpyxl.load_workbook(excel_path, data_only=True)

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            rows = list(sheet.iter_rows(values_only=True))

            # Fichier/Feuille vide ou juste une ligne d'en-tête
            if not rows or len(rows) < 2:
                continue

            # Ligne 1 : Noms des colonnes / champs
            headers = [str(cell).strip() if cell is not None else f"column_{i}" for i, cell in enumerate(rows[0])]

            records = []
            for row_idx, row in enumerate(rows[1:], start=2):
                # Ignorer les lignes totalement vides
                if not any(cell is not None for cell in row):
                    continue

                row_dict = {}
                pk_val = None

                for col_idx, col_name in enumerate(headers):
                    val = row[col_idx] if col_idx < len(row) else None
                
                    if col_name.lower() in ('id', 'pk'):
                        pk_val = val
                    else:
                        row_dict[col_name] = val

                if use_django_format:
                    # Hypothèse : Nom de la feuille = nom du modèle (ex: User, Product)
                    model_name = sheet_name.lower()
                    record = {
                        "model": f"{app_name}.{model_name}",
                        "pk": pk_val if pk_val is not None else row_idx - 1,
                        "fields": row_dict
                    }
                else:
                    # Inclure la PK directement dans l'objet si format JSON simple
                    if pk_val is not None:
                        row_dict['id'] = pk_val
                    record = row_dict

                records.append(record)

            # Nom du fichier JSON généré
            json_filename = f"{sheet_name.lower().replace(' ', '_')}.json"
            output_file = output_dir / json_filename

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2, default=str)

            self.stdout.write(self.style.SUCCESS(f"   --> Fixture créée : {output_file.relative_to(settings.BASE_DIR)}"))
```

---

### 4. Utilisation de la commande

1. **Convertir toutes les applications :**

```bash
python manage.py convert_seeds
```

2. **Convertir une application spécifique :**

```bash
python manage.py convert_seeds --app users
```

3. **Générer au format Fixture Django native (`loaddata`) :**

```bash
python manage.py convert_seeds --django-format
```

---

### 5. Format des fichiers Excel attendu

Chaque feuille Excel (Worksheet) représente une table/modèle.

* **Exemple de feuille nommée `User` dans `docs/database/seeds/users/source/users.xlsx` :**

| id | username | email              | is_active |
| -- | -------- | ------------------ | --------- |
| 1  | admin    | admin@yelemaso.com | True      |
| 2  | john_doe | john@yelemaso.com  | True      |

* **Résultat généré dans `apps/users/fixtures/user.json` (Format standard) :**

```json
[
  {
    "username": "admin",
    "email": "admin@yelemaso.com",
    "is_active": "True",
    "id": 1
  },
  {
    "username": "john_doe",
    "email": "john@yelemaso.com",
    "is_active": "True",
    "id": 2
  }
]
```

Si vous utilisez ensuite `python manage.py loaddata <fixture_name>`, vous pouvez exécuter la commande avec le drapeau `--django-format`.
