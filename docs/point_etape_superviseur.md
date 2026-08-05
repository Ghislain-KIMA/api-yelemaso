# Point d'étape — Cadrage du projet et question ouverte

## 1. Rappel du cadrage validé

Suite à nos échanges, le projet a été recentré sur un périmètre réaliste pour la durée du stage :

**Le système prend en entrée un document d'Autorisation de Manifester (AM) existant** — photo, scan ou fichier Word — **et en extrait automatiquement les informations** pour les structurer dans une base de données. Un écran de validation permet à l'utilisateur de corriger les champs mal extraits avant enregistrement définitif. Les données ainsi collectées alimentent un **dashboard d'analyse** (nombre de manifestations, répartition par genre/type, niveaux communal → national).

Ce recentrage remplace l'architecture initialement envisagée (application de saisie distribuée sur plusieurs postes, fonctionnement hors ligne) — jugée trop ambitieuse pour le délai du stage. Le travail de modélisation des données déjà réalisé (structure des autorisations, classification des manifestations, découpage géographique) reste directement réutilisable : seule la **méthode de collecte** change, pas la structure de la base.

## 2. Complexité identifiée : la classification des manifestations

Un document AM décrit un événement en langage libre (ex. *"lancement du tournoi dénommé Maracana de l'espoir"*), sans indiquer explicitement sa catégorie officielle (Genre, Type de manifestation, Périodicité...). Cette classification est une interprétation, pas une donnée extractible telle quelle.

**Solution retenue pour la soutenance** : un système de mots-clés (ex. "tournoi" → Genre "Sportif") pour pré-remplir une suggestion, toujours validée/corrigée par l'utilisateur. Une automatisation plus poussée (classification par apprentissage supervisé, une fois un corpus de documents validés accumulé) est identifiée comme perspective, non implémentée dans le cadre du stage.

## 3. Risque identifié : dépendance à la source de données

La conception actuelle repose entièrement sur l'hypothèse suivante : **l'accès à de vraies AM délivrées par une mairie**. Or cet accès n'est pas encore garanti (collaboration à négocier, éventuelles restrictions de confidentialité côté administration).

### Deux scénarios de repli envisagés

**Option A — Changer la source, garder le public cible administratif**
Utiliser les archives déjà centralisées (Haut-Commissariat, Préfecture, ou Ministère), qui reçoivent déjà une copie de chaque AM via les ampliations réglementaires — plutôt que négocier un accès mairie par mairie. Cette option ne change rien à l'architecture ni au schéma de données déjà conçus.

**Option B — Pivoter vers les promoteurs d'événements et la mesure d'impact**
Si aucun accès administratif n'est possible, recentrer l'outil sur les organisateurs de manifestations (nombre de participants, retombées, comparaison géographique de l'accueil réservé à un type d'événement). Cette option change la nature même de la donnée collectée (déclarative, post-événement) et une partie du schéma (le bloc administratif — Autorisation, Agent, Poste, Signature — devient sans objet), tout en conservant le noyau commun (Manifestation, classification, géographie).

## 4. Décision proposée pour la soutenance

**Conserver le cap actuel** : source = documents AM, public cible = administration (agents communaux et DGESS/MCCAT). C'est l'option la plus avancée et la plus cohérente avec le travail déjà réalisé.

L'option B (promoteurs/impact) sera mentionnée dans le mémoire comme **perspective d'extension**, sans être implémentée — elle illustre une réflexion sur la valorisation future de l'outil sans complexifier le périmètre du stage.

## 5. Question à trancher avec vous

**Si la collaboration directe avec une mairie ne se concrétise pas à temps, un accès aux archives déjà centralisées (Haut-Commissariat, Préfecture, ou Ministère) est-il une piste envisageable et plus réaliste ?**

Si non, faut-il prévoir, en complément d'un nombre limité de documents réels, des **documents fictifs construits sur le même gabarit** pour démontrer le fonctionnement du pipeline lors de la soutenance ?
