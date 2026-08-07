# Backend — Yelemaso : plateforme de dépouillement et l'analyse des manifestations culturelles

Système centralisé qui extrait automatiquement les données des Autorisations
de Manifester (AM) à partir de documents existants (photo, scan, Word, PDF), et
propose un dashboard d'analyse des manifestations culturelles recensées et aussi un dépouillement des AM au cours d'une année.

## Installation

```bash
conda env create env-yelemaso python==3.14
conda activate env-yelemaso
pip install -r requirements/dev.txt
mv .env.example .env                # puis renseigner les vraies valeurs
```

### Dépendance système : Tesseract OCR

Le pipeline d'extraction utilise Tesseract pour l'OCR (scans/photos) — à
installer séparément de `pip` :

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-fra
```

## Base de données

1. Créer la base PostgreSQL et l'utilisateur applicatif (hors du périmètre
   de ce script — à faire selon votre installation PostgreSQL).
2. Créer les 4 schémas AVANT la première migration :
   ```bash
   psql -U <user> -h localhost -d <db> -f scripts/create_schemas.sql
   ```
3. Appliquer les migrations (déjà générées dans ce dépôt) :
   ```bash
   python manage.py migrate
   ```
4. Créer un superutilisateur pour l'admin Django :
   ```bash
   python manage.py createsuperuser
   ```
5. Peupler les tables de référence minimales pour pouvoir tester
   l'extraction (Region/Province/Commune/Mairie, Mode_Acces, Genre,
   Type_Manifestation...) — via l'admin Django (`/admin/`) ou un script
   de seed à écrire selon vos données réelles.

## Lancer le serveur de développement

```bash
python manage.py runserver
```

- Admin Django : http://127.0.0.1:8000/admin/
- API REST : http://127.0.0.1:8000/api/v1/
- Dashboard de visualisation : http://127.0.0.1:8000/dashboard/

## Démonstration en ligne de commande

### 1. Extraire une AM à partir d'un document

```bash
# Inspection seule (affiche le texte extrait + les champs détectés,
# sans rien créer en base)
python manage.py extraire_document /chemin/vers/photo.jpg --mairie-id 1

# Extraction + validation interactive + création des enregistrements
# (Demandeur, CNIB, Demande, Manifestation, Autorisation)
python manage.py extraire_document /chemin/vers/photo.jpg --mairie-id 1 --valider
```

Le type de document (`word`/`pdf`/`scanne`/`photo`) est deviné depuis
l'extension du fichier, ou précisé explicitement avec `--type`.

Testé de bout en bout sur une vraie photo d'AM (mairie de Nouna) : tous
les champs (numéro, dates, demandeur, CNIB, téléphone, signataire) sont
correctement extraits malgré le bruit OCR typique d'une photo prise au
téléphone.

### 2. Générer la fiche de dépouillement

```bash
# Affichage dans le terminal
python manage.py generer_fiche_depouillement --commune-id 1 --annee 2024

# Export CSV (même format que la fiche officielle du Ministère)
python manage.py generer_fiche_depouillement --commune-id 1 --annee 2024 --sortie fiche.csv
```

### 3. Dashboard

Ouvrir http://127.0.0.1:8000/dashboard/ après avoir lancé le serveur.
Filtrable par région/province/commune via le menu déroulant.

## Structure du projet

- `config/` — réglages Django (settings par environnement, urls racine)
- `core/` — utilitaires transversaux (qualification de schéma, pagination)
- `apps/` — un dossier = un schéma PostgreSQL (administration, gestion,
  securite, culture) — modèles et logique métier
  - `apps/gestion/services/` — pipeline d'extraction (OCR/parsing/lexique
    de classification)
  - `apps/gestion/management/commands/` — commandes CLI de démonstration
  - `apps/culture/views.py` + `templates/` — dashboard web
- `api/v1/` — API REST (CRUD sur toutes les entités, y compris les
  propositions "Autre" à classer)
- `docs/database/` — MCD/MLD/MPD (conception), DDL de référence (schema),
  et `archive/` (composants de l'ancienne architecture offline-first
  multi-postes, conservés comme référence historique — voir le mémoire,
  section limitations/évolutions)

## Ce qui a changé par rapport à l'architecture initiale

Le projet a été recentré (cf. échanges avec le superviseur de stage) sur
un système centralisé d'extraction de documents existants, plutôt qu'une
saisie distribuée multi-postes hors ligne. En conséquence :

- L'ancienne couche `api/v1/sync/` et `WritableUUIDIdModelSerializer`
  (idempotence de synchronisation) ont été retirées du code actif — elles
  répondaient à un problème (postes déconnectés produisant des données en
  parallèle) qui ne se pose plus avec un point d'entrée centralisé.
  Conservées dans `docs/database/archive/` à titre de référence.
- `Document` a été ajouté comme source obligatoire de toute `Autorisation`
  (`document` en FK unique non nulle) — cohérent avec le nouveau
  périmètre : pas d'autorisation sans preuve documentaire extraite.

## À faire ensuite

- [ ] Insertion des seeds.
  - [ ] Le scripte convertir_excel_vers_json.py est-elle universelle, est-ce que je peux l'utilser  par exemple pour culture,
  - [X] Question : pour ficher excel est-ce que garder les id dérange le script ?
  - [ ] Je veux que tu m'explique le srcript en détaille.
  - [X] Dans quelle dossier je doit mettre le script ?
  - [X] le nom de mes tables doivent-elle être au singulier ou au plurielle ?
- [X] Rendre Commune.type_commune nullable
- [ ] Commande d'extraction de plusieurs fichier.
- [ ] Authentification (JWT déjà en dépendance, à câbler sur les vues)
- [ ] Écran de validation web (actuellement seulement en CLI via
  `extraire_document --valider`)
- [ ] Écran de classement des propositions "Autre" (endpoints API déjà
  prêts : `/api/v1/genre-autre/`, etc., filtrables par `?statut=en_attente`)
- [ ] Tests automatisés (pytest-django) sur le pipeline d'extraction
- [ ] Peuplement systématique des tables de référence (script de seed)

> NOTE:
>
> Quand tu charges ce JSON avec `loaddata`, Django insère les lignes avec les `pk` exacts du fichier (1, 2, 3...) — mais la **séquence auto-incrémentée** de PostgreSQL (qui génère normalement les futurs ID) n'est pas automatiquement mise à jour pour "savoir" que ces numéros sont déjà pris. Résultat possible : si tu crées une nouvelle `Region` **après** le chargement, PostgreSQL pourrait essayer de lui donner un ID déjà utilisé, et ça plante.
>
> **La correction, à faire une fois juste après `loaddata`**
>
> bash
>
> ```bash
> python manage.py loaddata docs/database/seeds/geographie.json
> python manage.py sqlsequencereset administration | python manage.py dbshell
> ```
> python scripts/convertir_excel_vers_json.py docs/database/seeds/source/communes_burkina.xlsx docs/database/seeds/geographie.json
> python manage.py loaddata docs/database/seeds/geographie.json
