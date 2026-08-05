from django.db import models

from apps.gestion.models import STATUT_PROPOSITION_CHOICES, Demande
from core.db_utils import schema_table
from core.models import ReferenceModel, UUIDModel

SCHEMA = "culture"


class ModeAcces(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "mode_acces")
        verbose_name = "Mode d'accès"

    def __str__(self):
        return self.label


class Genre(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "genre")
        verbose_name = "Genre"

    def __str__(self):
        return self.label


class Periodicite(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "periodicite")
        verbose_name = "Périodicité"
        verbose_name_plural = "Périodicités"

    def __str__(self):
        return self.label


class TypeManifestation(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "type_manifestation")
        verbose_name = "Type de manifestation"

    def __str__(self):
        return self.label


class Dimension(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "dimension")
        verbose_name = "Dimension"

    def __str__(self):
        return self.label


class TypeEspace(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "type_espace")
        verbose_name = "Type d'espace"

    def __str__(self):
        return self.label


class Manifestation(UUIDModel):
    espace = models.CharField(max_length=256)
    duree = models.IntegerField(
        blank=True, null=True,
        help_text="Durée en heures d'activité effective — indépendante de "
                   "l'intervalle datetime_debut/datetime_fin, qui peut "
                   "couvrir plusieurs jours calendaires avec activité "
                   "partielle.",
    )
    datetime_debut = models.DateTimeField()
    datetime_fin = models.DateTimeField(blank=True, null=True)
    # mode_acces reste obligatoire : pas de mécanisme "Autre" pour ce
    # référentiel (liste fermée à 3 valeurs, jugée suffisante).
    mode_acces = models.ForeignKey(
        ModeAcces, on_delete=models.PROTECT, related_name="manifestations"
    )
    # Les 5 FK suivantes sont nullables : en attente de classement si
    # l'agent a signalé "aucune valeur ne correspond" (voir les tables
    # *Autre ci-dessous, qui remontent la proposition au centre).
    genre = models.ForeignKey(
        Genre, on_delete=models.PROTECT, related_name="manifestations",
        blank=True, null=True,
    )
    periodicite = models.ForeignKey(
        Periodicite, on_delete=models.PROTECT, related_name="manifestations",
        blank=True, null=True,
    )
    type_manifestation = models.ForeignKey(
        TypeManifestation, on_delete=models.PROTECT, related_name="manifestations",
        blank=True, null=True,
    )
    dimension = models.ForeignKey(
        Dimension, on_delete=models.PROTECT, related_name="manifestations",
        blank=True, null=True,
    )
    type_espace = models.ForeignKey(
        TypeEspace, on_delete=models.PROTECT, related_name="manifestations",
        blank=True, null=True,
    )

    class Meta:
        db_table = schema_table(SCHEMA, "manifestation")
        verbose_name = "Manifestation"

    def __str__(self):
        return f"Manifestation {self.id} — {self.espace}"


class DemandeManifestation(models.Model):
    """Une demande peut concerner plusieurs manifestations (cf. note MPD)."""
    demande = models.ForeignKey(
        Demande, on_delete=models.CASCADE, related_name="manifestations_liees"
    )
    manifestation = models.ForeignKey(
        Manifestation, on_delete=models.CASCADE, related_name="demandes_liees"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "demande_manifestation")
        verbose_name = "Manifestation d'une demande"
        constraints = [
            models.UniqueConstraint(
                fields=["demande", "manifestation"],
                name="uq_demande_manifestation",
            )
        ]


class PropositionAutreBase(UUIDModel):
    """
    Base commune aux 5 tables "_Autre" liées à Manifestation. Chacune
    capture la précision texte saisie par l'agent quand aucune valeur du
    référentiel correspondant ne convient. Le centre classe la proposition
    et met à jour directement la FK sur Manifestation — pas de lien retour
    depuis cette table vers le référentiel officiel.
    """
    label = models.CharField(max_length=100)
    datetime_proposition = models.DateTimeField()
    statut = models.CharField(
        max_length=50, choices=STATUT_PROPOSITION_CHOICES, default="en_attente"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class GenreAutre(PropositionAutreBase):
    manifestation = models.ForeignKey(
        Manifestation, on_delete=models.CASCADE, related_name="genre_autre_propositions"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "genre_autre")
        verbose_name = "Genre (proposition Autre)"


class TypeManifestationAutre(PropositionAutreBase):
    manifestation = models.ForeignKey(
        Manifestation, on_delete=models.CASCADE,
        related_name="type_manifestation_autre_propositions",
    )

    class Meta:
        db_table = schema_table(SCHEMA, "type_manifestation_autre")
        verbose_name = "Type de manifestation (proposition Autre)"


class PeriodiciteAutre(PropositionAutreBase):
    manifestation = models.ForeignKey(
        Manifestation, on_delete=models.CASCADE,
        related_name="periodicite_autre_propositions",
    )

    class Meta:
        db_table = schema_table(SCHEMA, "periodicite_autre")
        verbose_name = "Périodicité (proposition Autre)"


class DimensionAutre(PropositionAutreBase):
    manifestation = models.ForeignKey(
        Manifestation, on_delete=models.CASCADE,
        related_name="dimension_autre_propositions",
    )

    class Meta:
        db_table = schema_table(SCHEMA, "dimension_autre")
        verbose_name = "Dimension (proposition Autre)"


class TypeEspaceAutre(PropositionAutreBase):
    manifestation = models.ForeignKey(
        Manifestation, on_delete=models.CASCADE,
        related_name="type_espace_autre_propositions",
    )

    class Meta:
        db_table = schema_table(SCHEMA, "type_espace_autre")
        verbose_name = "Type d'espace (proposition Autre)"
