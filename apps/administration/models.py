from django.core.exceptions import ValidationError
from django.db import models

from core.db_utils import schema_table
from core.models import ReferenceModel

SCHEMA = "administration"


class Region(ReferenceModel):
    nom_region = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "region")
        verbose_name = "Région"

    def __str__(self):
        return self.nom_region


class Province(ReferenceModel):
    nom_province = models.CharField(max_length=50, unique=True)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="provinces"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "province")
        verbose_name = "Province"

    def __str__(self):
        return self.nom_province


class TypeCommune(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "type_commune")
        verbose_name = "Type de commune"

    def __str__(self):
        return self.label


class Commune(ReferenceModel):
    nom_commune = models.CharField(max_length=50)
    type_commune = models.ForeignKey(
        TypeCommune, on_delete=models.PROTECT, related_name="communes"
    )
    province = models.ForeignKey(
        Province, on_delete=models.PROTECT, related_name="communes"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "commune")
        verbose_name = "Commune"
        constraints = [
            models.UniqueConstraint(
                fields=["nom_commune", "province"],
                name="uq_commune_nom_province",
            )
        ]

    def __str__(self):
        return self.nom_commune


class TypeMairie(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "type_mairie")
        verbose_name = "Type de mairie"

    def __str__(self):
        return self.label


class Mairie(ReferenceModel):
    nom_mairie = models.CharField(max_length=50)
    type_mairie = models.ForeignKey(
        TypeMairie, on_delete=models.PROTECT, related_name="mairies"
    )
    commune = models.ForeignKey(
        Commune, on_delete=models.PROTECT, related_name="mairies"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "mairie")
        verbose_name = "Mairie"
        constraints = [
            models.UniqueConstraint(
                fields=["nom_mairie", "commune"],
                name="uq_mairie_nom_commune",
            )
        ]

    def __str__(self):
        return self.nom_mairie

    def clean(self):
        """
        Règle métier : une commune rurale/urbaine ne peut avoir qu'une
        seule mairie ("mairie centrale"). Les communes à statut particulier
        peuvent en avoir plusieurs (mairies d'arrondissement).
        Doublée par un trigger PostgreSQL côté base
        (voir docs/database/schema/schema_postgresql.sql) pour garantir
        l'intégrité même hors de l'API.
        """
        label = self.commune.type_commune.label.lower()
        if label in ("rurale", "urbaine"):
            qs = Mairie.objects.filter(commune=self.commune).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(
                    "Cette commune (rurale/urbaine) ne peut avoir qu'une "
                    "seule mairie."
                )
