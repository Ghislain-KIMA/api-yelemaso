"""
Génère la "Fiche de dépouillement des manifestations et des activités
culturelles autorisées par les communes", au même format que celle
remplie manuellement par les agents du MCCAT pour le compte de la DGESS
(cf. docs/database/conception -- exemple fourni).

Usage :
    python manage.py generer_fiche_depouillement --commune-id 6 --annee 2024
    python manage.py generer_fiche_depouillement --commune-id 6 --annee 2024 --sortie fiche.csv

Sans --sortie : affiche la fiche dans le terminal (colonnes séparées par
des tabulations). Avec --sortie : écrit un fichier CSV du même contenu.
"""
import csv
import sys

from django.core.management.base import BaseCommand, CommandError

from apps.administration.models import Commune
from apps.culture.models import DemandeManifestation, Manifestation

MOIS_LABEL = {
    1: "Janvier", 2: "Février", 3: "Mars", 4: "Avril", 5: "Mai", 6: "Juin",
    7: "Juillet", 8: "Août", 9: "Septembre", 10: "Octobre", 11: "Novembre",
    12: "Décembre",
}

ENTETES = [
    "N° Dossier", "Mois", "Statut du demandeur", "Genre", "Type",
    "Périodicité", "Dimension", "Lieu", "Durée (heures)", "Mode d'accès",
]


class Command(BaseCommand):
    help = (
        "Génère la Fiche de dépouillement des manifestations culturelles "
        "autorisées, au format utilisé par la DGESS (MCCAT)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--commune-id", type=int, required=True)
        parser.add_argument("--annee", type=int, required=True)
        parser.add_argument(
            "--sortie",
            type=str,
            default=None,
            help="Chemin du fichier CSV à écrire. Si omis, affiche dans le terminal.",
        )

    def handle(self, *args, **options):
        commune = Commune.objects.filter(id=options["commune_id"]).first()
        if commune is None:
            raise CommandError(f"Aucune Commune avec id={options['commune_id']}")

        annee = options["annee"]

        manifestations = (
            Manifestation.objects.filter(
                demandes_liees__demande__autorisations__mairie__commune=commune,
                datetime_debut__year=annee,
            )
            .select_related(
                "genre", "type_manifestation", "periodicite", "dimension",
                "type_espace", "mode_acces",
            )
            .prefetch_related("demandes_liees__demande__demandeur__statut_demandeur")
            .distinct()
            .order_by("datetime_debut")
        )

        if not manifestations.exists():
            self.stdout.write(self.style.WARNING(
                f"Aucune manifestation trouvée pour {commune.nom_commune} en {annee}."
            ))
            return

        lignes = []
        for index, manifestation in enumerate(manifestations, start=1):
            demande_liee = DemandeManifestation.objects.filter(
                manifestation=manifestation
            ).select_related("demande__demandeur__statut_demandeur").first()
            statut_demandeur = None
            if demande_liee:
                statut_demandeur = demande_liee.demande.demandeur.statut_demandeur

            lignes.append([
                f"{annee}-{index:02d}",
                MOIS_LABEL.get(manifestation.datetime_debut.month, ""),
                statut_demandeur.label if statut_demandeur else "",
                manifestation.genre.label if manifestation.genre else "",
                manifestation.type_manifestation.label
                if manifestation.type_manifestation else "",
                manifestation.periodicite.label if manifestation.periodicite else "",
                manifestation.dimension.label if manifestation.dimension else "",
                manifestation.type_espace.label if manifestation.type_espace else "",
                manifestation.duree if manifestation.duree is not None else "",
                manifestation.mode_acces.label if manifestation.mode_acces else "",
            ])

        entete_fiche = (
            f"Fiche de dépouillement des manifestations et des activités "
            f"culturelles autorisées par les communes\n"
            f"Région : {commune.province.region.nom_region} | "
            f"Province : {commune.province.nom_province} | "
            f"Commune : {commune.nom_commune} | Année : {annee}\n"
        )

        if options["sortie"]:
            with open(options["sortie"], "w", newline="", encoding="utf-8") as f:
                f.write(entete_fiche)
                writer = csv.writer(f)
                writer.writerow(ENTETES)
                writer.writerows(lignes)
            self.stdout.write(self.style.SUCCESS(f"Fiche écrite : {options['sortie']}"))
        else:
            self.stdout.write(entete_fiche)
            writer = csv.writer(sys.stdout, delimiter="\t")
            writer.writerow(ENTETES)
            writer.writerows(lignes)
