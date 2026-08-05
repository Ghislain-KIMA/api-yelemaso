from django.core.exceptions import ValidationError
from django.db import models

from apps.administration.models import Mairie
from core.db_utils import schema_table
from core.models import ReferenceModel, UUIDModel

SCHEMA = "gestion"

STATUT_PROPOSITION_CHOICES = [
    ("en_attente", "En attente de classement"),
    ("classee", "Classée"),
    ("rejetee", "Rejetée (doublon d'une valeur existante)"),
]


class StatutDemandeur(ReferenceModel):
    label = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "statut_demandeur")
        verbose_name = "Statut du demandeur"

    def __str__(self):
        return self.label


class CNIB(UUIDModel):
    numero = models.CharField(max_length=50, unique=True)
    date_cnib = models.DateField()
    structure = models.CharField(max_length=50)

    class Meta:
        db_table = schema_table(SCHEMA, "cnib")
        verbose_name = "CNIB"
        verbose_name_plural = "CNIB"

    def __str__(self):
        return self.numero


class Demandeur(UUIDModel):
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    profession = models.CharField(max_length=255)
    residence = models.CharField(max_length=100)
    cnib = models.OneToOneField(
        CNIB, on_delete=models.PROTECT, related_name="demandeur"
    )
    # Nullable : en attente de classement si "Autre" a été choisi
    # (voir StatutDemandeurAutre)
    statut_demandeur = models.ForeignKey(
        StatutDemandeur, on_delete=models.PROTECT, related_name="demandeurs",
        blank=True, null=True,
    )

    class Meta:
        db_table = schema_table(SCHEMA, "demandeur")
        verbose_name = "Demandeur"

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class StatutDemandeurAutre(UUIDModel):
    """
    Proposition d'un nouveau statut, saisie par un poste local lorsqu'aucune
    valeur de StatutDemandeur ne correspond. Le centre classe la proposition
    et met à jour directement Demandeur.statut_demandeur, sans lien retour
    depuis cette table (même principe que Genre_Autre côté Manifestation).
    """
    label = models.CharField(max_length=100)
    datetime_proposition = models.DateTimeField()
    statut = models.CharField(
        max_length=50, choices=STATUT_PROPOSITION_CHOICES, default="en_attente"
    )
    demandeur = models.ForeignKey(
        Demandeur, on_delete=models.CASCADE, related_name="statut_autre_propositions"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "statut_demandeur_autre")
        verbose_name = "Statut demandeur (proposition Autre)"

    def __str__(self):
        return self.label


class Demande(UUIDModel):
    date_demande = models.DateField()
    objet = models.CharField(max_length=255)
    demandeur = models.ForeignKey(
        Demandeur, on_delete=models.PROTECT, related_name="demandes"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "demande")
        verbose_name = "Demande"

    def __str__(self):
        return f"Demande {self.id} — {self.objet}"


class Personne(UUIDModel):
    """
    Identité stable d'un individu pouvant signer une Autorisation, à travers
    différentes fonctions/attributions au fil du temps (voir Signature).
    Peut être créée par un poste local (hors ligne) : cf. sync ascendante.
    """
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=100)
    profession = models.CharField(max_length=255, blank=True, null=True)
    grade = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = schema_table(SCHEMA, "personne")
        verbose_name = "Personne"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(profession__isnull=False)
                | models.Q(grade__isnull=False),
                name="chk_personne_profession_ou_grade",
            )
        ]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def clean(self):
        if not self.profession and not self.grade:
            raise ValidationError(
                "Au moins l'un des deux champs profession ou grade doit "
                "être renseigné."
            )


class Habilitation(UUIDModel):
    """
    Catalogue dédupliqué des combinaisons (fonction, attribution) dans
    lesquelles une Personne peut signer une Autorisation. Ex : fonction
    "Agent", attribution "Pour le Directeur/DP". Réutilisable par
    plusieurs Personne à différents moments (voir Signature).
    Peut être créée par un poste local (hors ligne) : cf. sync ascendante.
    """
    fonction = models.CharField(max_length=255)
    attribution = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = schema_table(SCHEMA, "habilitation")
        verbose_name = "Habilitation"

    def __str__(self):
        if self.attribution:
            return f"{self.fonction} — {self.attribution}"
        return self.fonction


class Document(UUIDModel):
    """
    Fichier source (photo, scan, ou Word) d'une Autorisation de Manifester,
    dont les données ont été (ou vont être) extraites automatiquement.
    Cycle de vie : brute -> en_validation -> validee / rejetee.
    Une Autorisation ne peut exister que si son Document est validee
    (cf. contrainte document, not null + unique, sur Autorisation).
    """
    TYPE_CHOICES = [
        ("word", "Document Word"),
        ("pdf", "PDF"),
        ("scanne", "Scan"),
        ("photo", "Photo"),
    ]
    STATUT_CHOICES = [
        ("brute", "Uploadé, pas encore traité"),
        ("en_validation", "Extraction faite, en attente de validation humaine"),
        ("validee", "Validé — Autorisation créée"),
        ("rejetee", "Rejeté (illisible, doublon...)"),
    ]

    fichier = models.FileField(upload_to="documents_sources/%Y/%m/")
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    texte_extrait = models.TextField(blank=True, null=True)
    datetime_upload = models.DateTimeField(auto_now_add=True)
    statut_extraction = models.CharField(
        max_length=50, choices=STATUT_CHOICES, default="brute"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "document")
        verbose_name = "Document"

    def __str__(self):
        return f"Document {self.id} ({self.type_document}, {self.statut_extraction})"


class Autorisation(UUIDModel):
    numero = models.CharField(max_length=100, unique=True)
    date_autorisation = models.DateField()
    mairie = models.ForeignKey(
        Mairie, on_delete=models.PROTECT, related_name="autorisations"
    )
    demande = models.ForeignKey(
        Demande, on_delete=models.PROTECT, related_name="autorisations"
    )
    # Une Autorisation ne peut exister que si elle découle d'un document
    # source validé (photo/scan/Word) — cohérent avec le périmètre du
    # projet, limité à l'extraction de documents existants.
    document = models.OneToOneField(
        Document, on_delete=models.PROTECT, related_name="autorisation"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "autorisation")
        verbose_name = "Autorisation"

    def __str__(self):
        return self.numero


class Signature(models.Model):
    """
    Association ternaire Autorisation / Personne / Habilitation : capture
    l'acte de signature précis, immuable une fois créé. autorisation sert
    de clé primaire (pas d'id UUID séparé), ce qui garantit qu'une
    Autorisation n'a qu'un seul acte de signature.
    """
    autorisation = models.OneToOneField(
        Autorisation, on_delete=models.PROTECT, primary_key=True,
        related_name="signature",
    )
    personne = models.ForeignKey(
        Personne, on_delete=models.PROTECT, related_name="signatures"
    )
    habilitation = models.ForeignKey(
        Habilitation, on_delete=models.PROTECT, related_name="signatures"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "signature")
        verbose_name = "Signature"

    def __str__(self):
        return f"Signature {self.autorisation.numero}"


class Ampliation(UUIDModel):
    """Peut être créée par un poste local (hors ligne) : cf. sync ascendante."""
    label = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = schema_table(SCHEMA, "ampliation")
        verbose_name = "Ampliation"

    def __str__(self):
        return self.label


class AutorisationAmpliation(models.Model):
    """
    Association Autorisation <-> Ampliation.
    NB : le DDL SQL brut définit une clé primaire composite
    (autorisation_id, ampliation_id). Django (hors 5.2+ CompositePrimaryKey,
    non utilisé ici pour rester compatible large) gère plus simplement une
    clé technique BigAutoField + une contrainte d'unicité qui reproduit la
    même garantie fonctionnelle.
    """
    autorisation = models.ForeignKey(
        Autorisation, on_delete=models.CASCADE, related_name="ampliations"
    )
    ampliation = models.ForeignKey(
        Ampliation, on_delete=models.PROTECT, related_name="autorisations"
    )
    structure = models.CharField(
        max_length=255,
        help_text="Structure exacte destinataire (ex: commissariat précis)",
    )

    class Meta:
        db_table = schema_table(SCHEMA, "autorisation_ampliation")
        verbose_name = "Ampliation d'autorisation"
        constraints = [
            models.UniqueConstraint(
                fields=["autorisation", "ampliation"],
                name="uq_autorisation_ampliation",
            )
        ]

    def __str__(self):
        return f"{self.autorisation.numero} -> {self.ampliation.label}"
