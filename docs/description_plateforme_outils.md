# Description de la plateforme et des outils utilisés

## 1. Description de la plateforme

**Yelemaso** est une plateforme de dépouillement et d'analyse des manifestations culturelles locales, développée dans le cadre d'un stage de fin de cycle licence à l'Université Virtuelle du Burkina Faso, pour le compte de la Direction Générale des Études et des Statistiques Sectorielles (DGESS) du Ministère de la Communication, de la Culture, des Arts et du Tourisme (MCCAT).

### Problème traité

Aujourd'hui, chaque manifestation publique organisée sur le territoire communal nécessite une **Autorisation de Manifester (AM)**, délivrée par la mairie sous forme de document papier. Le suivi statistique de ces autorisations repose sur une **fiche de dépouillement** que les agents du MCCAT remplissent manuellement, commune par commune, pour compilation ultérieure par la DGESS. Ce processus est entièrement manuel, chronophage, et source d'erreurs de saisie.

### Principe de fonctionnement

Yelemaso automatise cette chaîne en trois étapes :

1. **Extraction** — l'agent importe le document source d'une AM (photo, scan, ou fichier Word) ; la plateforme en extrait automatiquement le texte (par reconnaissance optique de caractères ou lecture directe selon le format), puis identifie les champs structurés (numéro d'autorisation, dates, identité du demandeur, objet de la manifestation, signataire, destinataires des ampliations...).
2. **Validation** — les champs extraits sont présentés à l'agent pour confirmation ou correction avant tout enregistrement définitif, garantissant qu'aucune donnée erronée n'est intégrée silencieusement à la base.
3. **Restitution** — les données validées alimentent une base structurée, à partir de laquelle sont générés automatiquement la fiche de dépouillement (au format utilisé par la DGESS) et un tableau de bord de visualisation des manifestations recensées (par genre, type, période, mode d'accès, localisation).

### Périmètre actuel

Le développement est actuellement centré sur une seule commune pilote (Nouna, province de la Kossi, région de la Boucle du Mouhoun), avec une architecture conçue pour permettre, dans un second temps, une extension à l'ensemble des communes du pays, à d'autres types de fiches de collecte, et potentiellement à d'autres départements ministériels gérant des autorisations administratives comparables.

## 2. Outils et technologies utilisées

### 2.1 Backend et base de données

| Outil | Rôle |
|---|---|
| **Python** | Langage principal du backend |
| **Django** | Framework web, ORM, administration technique intégrée |
| **Django REST Framework** | Exposition de l'API REST (consultation et gestion des données) |
| **PostgreSQL** | Système de gestion de base de données, organisé en 4 schémas fonctionnels (administration géographique, gestion des demandes/autorisations, sécurité/traçabilité, culture) |
| **django-filter** | Filtrage des ressources de l'API (ex. propositions de classification en attente) |

Le choix de Django s'explique par la maturité de son ORM pour modéliser un schéma relationnel riche (35 tables), ainsi que par son système de migrations qui a permis de faire évoluer le schéma de données de façon itérative tout au long de la conception (modèle conceptuel → logique → physique).

### 2.2 Pipeline d'extraction de documents

| Outil | Rôle |
|---|---|
| **Tesseract OCR** | Moteur de reconnaissance optique de caractères, open source, utilisé pour les documents scannés et les photos |
| **pytesseract** | Interface Python vers Tesseract |
| **Pillow (PIL)** | Prétraitement des images avant OCR (conversion en niveaux de gris, ajustement du contraste) |
| **pdfplumber** | Extraction du texte natif des fichiers PDF, avec bascule vers l'OCR si le PDF est un scan sans couche de texte |
| **python-docx** | Lecture directe du texte des documents Word (`.docx`) |

Le choix de Tesseract, plutôt qu'un service d'OCR propriétaire en ligne, répond à une double contrainte : la gratuité (aucun coût récurrent par document traité) et l'indépendance vis-à-vis d'une connexion internet stable, un facteur important dans le contexte burkinabè.

### 2.3 Interprétation des champs extraits

L'extraction du texte brut ne suffit pas à elle seule : les champs structurés (numéro, dates, identité, objet, signataire, destinataires d'ampliation) sont ensuite identifiés par un module de **règles d'extraction fondées sur des expressions régulières**, calibrées sur le gabarit réel des AM observées. Ce choix, plutôt qu'une approche par apprentissage automatique, se justifie par la stabilité du format administratif et par la nécessité de pouvoir expliquer et vérifier chaque règle d'extraction — une exigence importante pour un usage administratif.

Deux mécanismes complémentaires accompagnent cette extraction :
- Un **lexique de mots-clés** propose une classification indicative du genre et du type de manifestation à partir du texte libre décrivant l'événement, toujours soumise à validation humaine.
- Un mécanisme de **déduplication approximative** (bibliothèque `difflib` de la bibliothèque standard Python) évite la création de doublons lorsque les destinataires d'ampliation sont désignés de façon légèrement différente d'un document à l'autre (variation de casse, pluriel, légère différence orthographique).

### 2.4 Restitution et visualisation

| Outil | Rôle |
|---|---|
| **Commandes Django (interface en ligne de commande)** | Démonstration du pipeline d'extraction et génération de la fiche de dépouillement |
| **Chart.js** | Bibliothèque de graphiques utilisée par le tableau de bord intégré au backend |
| **HTML / CSS / SVG natif** | Maquette de démonstration statique du tableau de bord, avec données fictives, sans dépendance à une connexion réseau |

### 2.5 Méthodologie et outillage de conception

| Outil | Rôle |
|---|---|
| **Merise (MCD / MLD / MPD)** | Méthodologie de modélisation des données, en trois niveaux successifs |
| **draw.io** | Réalisation des diagrammes de modélisation |
| **Git** | Gestion de versions du code source |

### 2.6 Environnement de développement

Le développement a été mené sous **Termux**, un environnement Linux pour Android, permettant de travailler directement depuis un terminal mobile — un choix cohérent avec l'attention portée, tout au long du projet, aux contraintes matérielles et de connectivité propres au contexte local.
