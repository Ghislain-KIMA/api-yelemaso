"""
Dashboard de visualisation des manifestations culturelles, agrégées par
niveau géographique (commune / province / région / national) -- voir
apps/gestion/management/commands/generer_fiche_depouillement.py pour
l'équivalent "fiche officielle" en sortie CSV.

Volontairement simple (pas de framework JS, un peu de Chart.js via CDN)
pour rester démontrable rapidement en soutenance sans étape de build.
"""
import json

from django.db.models import Count
from django.shortcuts import render

from apps.administration.models import Commune, Province, Region
from apps.culture.models import Manifestation


def dashboard(request):
    """
    Filtres optionnels en query string :
        ?niveau=region|province|commune&id=<id>
    Sans filtre : statistiques nationales (toutes les manifestations).
    """
    niveau = request.GET.get("niveau")
    filtre_id = request.GET.get("id")

    queryset = Manifestation.objects.all()
    titre_zone = "National"

    if niveau == "region" and filtre_id:
        region = Region.objects.filter(id=filtre_id).first()
        if region:
            queryset = queryset.filter(
                demandes_liees__demande__autorisations__mairie__commune__province__region=region
            )
            titre_zone = f"Région : {region.nom_region}"
    elif niveau == "province" and filtre_id:
        province = Province.objects.filter(id=filtre_id).first()
        if province:
            queryset = queryset.filter(
                demandes_liees__demande__autorisations__mairie__commune__province=province
            )
            titre_zone = f"Province : {province.nom_province}"
    elif niveau == "commune" and filtre_id:
        commune = Commune.objects.filter(id=filtre_id).first()
        if commune:
            queryset = queryset.filter(
                demandes_liees__demande__autorisations__mairie__commune=commune
            )
            titre_zone = f"Commune : {commune.nom_commune}"

    queryset = queryset.distinct()

    total = queryset.count()

    par_genre = list(
        queryset.exclude(genre__isnull=True)
        .values("genre__label")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    par_type = list(
        queryset.exclude(type_manifestation__isnull=True)
        .values("type_manifestation__label")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    par_mode_acces = list(
        queryset.values("mode_acces__label").annotate(total=Count("id")).order_by("-total")
    )
    par_mois = list(
        queryset.values("datetime_debut__month")
        .annotate(total=Count("id"))
        .order_by("datetime_debut__month")
    )

    contexte = {
        "titre_zone": titre_zone,
        "total": total,
        "regions": Region.objects.all(),
        "provinces": Province.objects.all(),
        "communes": Commune.objects.all(),
        "data_genre_json": json.dumps(
            {"labels": [d["genre__label"] for d in par_genre],
             "valeurs": [d["total"] for d in par_genre]}
        ),
        "data_type_json": json.dumps(
            {"labels": [d["type_manifestation__label"] for d in par_type],
             "valeurs": [d["total"] for d in par_type]}
        ),
        "data_mode_acces_json": json.dumps(
            {"labels": [d["mode_acces__label"] for d in par_mode_acces],
             "valeurs": [d["total"] for d in par_mode_acces]}
        ),
        "data_mois_json": json.dumps(
            {"labels": [str(d["datetime_debut__month"]) for d in par_mois],
             "valeurs": [d["total"] for d in par_mois]}
        ),
    }
    return render(request, "culture/dashboard.html", contexte)
