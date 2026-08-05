"""
Commande de démonstration du pipeline d'extraction.

Usage :
    python manage.py extraire_document /chemin/vers/photo.jpg --mairie-id 6
    python manage.py extraire_document /chemin/vers/am.docx --type word --mairie-id 6 --valider

Sans --valider : le Document est créé, le texte est extrait et les champs
sont affichés pour inspection, mais aucune Autorisation n'est créée
(statut_extraction reste "en_validation").

Avec --valider : après affichage, une confirmation interactive est
demandée avant de créer Demandeur/CNIB/Demande/Manifestation/Personne/
Habilitation/Signature/Autorisation avec les valeurs extraites (l'agent
peut à ce moment corriger les champs mal reconnus, comme le ferait le
futur écran de validation web).
"""
import os
from datetime import datetime

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.administration.models import Mairie
from apps.culture.models import DemandeManifestation, Genre, Manifestation, ModeAcces, TypeManifestation
from apps.gestion.models import (
    CNIB,
    Autorisation,
    AutorisationAmpliation,
    Demande,
    Demandeur,
    Document,
    Habilitation,
    Personne,
    Signature,
)
from apps.gestion.services.extraction import deviner_type_document, extraire_texte
from apps.gestion.services.lexique import suggerer_classification
from apps.gestion.services.parsing import extraire_ampliations, parser_champs
from apps.gestion.validators import find_or_create_ampliation

CHAMPS_OBLIGATOIRES_VALIDATION = (
    "numero", "date_demande", "objet", "date_evenement", "espace",
    "nom_demandeur", "prenom_demandeur", "cnib_numero", "cnib_date",
    "telephone", "date_autorisation", "fonction",
    "nom_signataire", "prenom_signataire",
)


class Command(BaseCommand):
    help = "Extrait les données d'une AM à partir d'un fichier (photo/scan/pdf/word)."

    def add_arguments(self, parser):
        parser.add_argument("chemin_fichier", type=str)
        parser.add_argument(
            "--type",
            dest="type_document",
            choices=["word", "pdf", "scanne", "photo"],
            default=None,
            help="Type de document. Deviné depuis l'extension si omis.",
        )
        parser.add_argument(
            "--mairie-id",
            dest="mairie_id",
            type=int,
            required=True,
            help="ID de la Mairie à l'origine de cette AM.",
        )
        parser.add_argument(
            "--valider",
            action="store_true",
            help="Crée les enregistrements après confirmation, plutôt que de "
            "seulement afficher l'extraction.",
        )

    def handle(self, *args, **options):
        chemin_fichier = options["chemin_fichier"]
        if not os.path.exists(chemin_fichier):
            raise CommandError(f"Fichier introuvable : {chemin_fichier}")

        mairie = Mairie.objects.filter(id=options["mairie_id"]).first()
        if mairie is None:
            raise CommandError(f"Aucune Mairie avec id={options['mairie_id']}")

        type_document = options["type_document"] or deviner_type_document(chemin_fichier)
        self.stdout.write(f"Type de document : {type_document}")

        # --- 1. Créer le Document et y attacher le fichier ---
        document = Document(type_document=type_document, statut_extraction="brute")
        with open(chemin_fichier, "rb") as f:
            document.fichier.save(os.path.basename(chemin_fichier), File(f), save=False)
        document.save()
        self.stdout.write(self.style.SUCCESS(f"Document créé : {document.id}"))

        # --- 2. Extraction du texte brut (OCR ou lecture directe) ---
        try:
            texte = extraire_texte(chemin_fichier, type_document)
        except Exception as exc:
            document.statut_extraction = "rejetee"
            document.save(update_fields=["statut_extraction"])
            raise CommandError(f"Échec de l'extraction : {exc}")

        document.texte_extrait = texte
        document.statut_extraction = "en_validation"
        document.save(update_fields=["texte_extrait", "statut_extraction"])

        self.stdout.write("\n--- Texte brut extrait ---")
        self.stdout.write(texte)

        # --- 3. Parsing des champs structurés ---
        champs = parser_champs(texte)
        suggestion = suggerer_classification(champs["objet"] or "")
        ampliations_brutes = extraire_ampliations(texte)

        self.stdout.write("\n--- Champs détectés ---")
        for cle, valeur in champs.items():
            self.stdout.write(f"  {cle:20s} : {valeur}")
        self.stdout.write(f"  {'genre (suggéré)':20s} : {suggestion['genre']}")
        self.stdout.write(f"  {'type (suggéré)':20s} : {suggestion['type_manifestation']}")
        self.stdout.write(f"  {'ampliations':20s} : {ampliations_brutes}")

        if not options["valider"]:
            self.stdout.write(self.style.WARNING(
                "\nDocument en attente de validation (--valider non fourni). "
                "Aucune Autorisation créée."
            ))
            return

        # --- 4. Validation interactive avant création ---
        self.stdout.write(self.style.WARNING(
            "\n--valider fourni : confirmez ou corrigez chaque champ "
            "(Entrée pour garder la valeur détectée)."
        ))
        champs = self._confirmer_champs(champs)

        champs_manquants = [
            c for c in CHAMPS_OBLIGATOIRES_VALIDATION if not champs.get(c)
        ]
        if champs_manquants:
            raise CommandError(
                f"Impossible de valider : champs manquants {champs_manquants}. "
                "Relancez sans --valider pour inspecter, ou corrigez le document source."
            )

        with transaction.atomic():
            # --- Demandeur + CNIB ---
            cnib = CNIB.objects.create(
                numero=champs["cnib_numero"],
                date_cnib=champs["cnib_date"],
                structure=mairie.nom_mairie,
            )
            demandeur = Demandeur.objects.create(
                nom=champs["nom_demandeur"],
                prenom=champs["prenom_demandeur"],
                telephone=champs["telephone"],
                profession="Non renseigné",
                residence=mairie.nom_mairie,
                cnib=cnib,
            )
            demande = Demande.objects.create(
                date_demande=champs["date_demande"] or champs["date_autorisation"],
                objet=champs["objet"],
                demandeur=demandeur,
            )

            # --- Manifestation ---
            genre = None
            if suggestion["genre"]:
                genre = Genre.objects.filter(label=suggestion["genre"]).first()
            type_manif = None
            if suggestion["type_manifestation"]:
                type_manif = TypeManifestation.objects.filter(
                    label=suggestion["type_manifestation"]
                ).first()
            mode_acces = ModeAcces.objects.first()
            if mode_acces is None:
                raise CommandError(
                    "Aucun Mode_Acces en base -- peuplez cette table de "
                    "référence avant de valider une extraction."
                )

            datetime_debut = timezone.make_aware(
                datetime.combine(champs["date_evenement"], datetime.min.time())
            )
            manifestation = Manifestation.objects.create(
                espace=champs["espace"],
                datetime_debut=datetime_debut,
                mode_acces=mode_acces,
                genre=genre,
                type_manifestation=type_manif,
            )
            DemandeManifestation.objects.create(
                demande=demande, manifestation=manifestation
            )

            # --- Signataire : Personne (identité) + Habilitation
            # (catalogue fonction/attribution, dédupliqué) + Signature
            # (association ternaire Autorisation/Personne/Habilitation) ---
            personne, _ = Personne.objects.get_or_create(
                nom=champs["nom_signataire"],
                prenom=champs["prenom_signataire"],
                defaults={
                    "profession": champs.get("emploi") or None,
                    "grade": champs.get("grade") or None,
                },
            )
            habilitation, _ = Habilitation.objects.get_or_create(
                fonction=champs["fonction"],
                attribution=champs.get("attribution"),
            )

            # --- Autorisation ---
            autorisation = Autorisation.objects.create(
                numero=champs["numero"],
                date_autorisation=champs["date_autorisation"],
                mairie=mairie,
                demande=demande,
                document=document,
            )
            Signature.objects.create(
                autorisation=autorisation,
                personne=personne,
                habilitation=habilitation,
            )

            # --- Ampliations : trouve/crée chaque destinataire avec
            # tolérance aux variantes proches (casse, pluriel, bruit OCR
            # léger) plutôt qu'une égalité stricte -- voir
            # find_or_create_ampliation() dans validators.py.
            for label_brut in ampliations_brutes:
                ampliation, _ = find_or_create_ampliation(label_brut)
                AutorisationAmpliation.objects.get_or_create(
                    autorisation=autorisation,
                    ampliation=ampliation,
                    defaults={"structure": label_brut},
                )

            document.statut_extraction = "validee"
            document.save(update_fields=["statut_extraction"])

        self.stdout.write(self.style.SUCCESS(
            f"\nAutorisation créée : {autorisation.numero} (id={autorisation.id})"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Signée par : {personne.prenom} {personne.nom} ({habilitation.fonction})"
        ))
        if ampliations_brutes:
            noms_ampliations = ", ".join(
                a.ampliation.label for a in autorisation.ampliations.all()
            )
            self.stdout.write(self.style.SUCCESS(f"Ampliations : {noms_ampliations}"))

    def _confirmer_champs(self, champs: dict) -> dict:
        confirmes = {}
        for cle, valeur in champs.items():
            saisie = input(f"{cle} [{valeur}] : ").strip()
            confirmes[cle] = saisie if saisie else valeur
        return confirmes
