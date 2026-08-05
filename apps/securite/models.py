from django.db import models

from apps.administration.models import Mairie
from apps.gestion.models import Autorisation
from core.db_utils import schema_table
from core.models import UUIDModel

SCHEMA = "securite"


class Poste(UUIDModel):
    """
    Un poste local s'auto-enregistre au premier lancement de l'application
    (voir bootstrap offline : données de référence préchargées, puis
    remontée de cet enregistrement dès que la connexion est disponible).
    """
    structure = models.CharField(max_length=256)
    telephone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    email = models.EmailField(max_length=100, unique=True, blank=True, null=True)
    login_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    mairie = models.ForeignKey(
        Mairie, on_delete=models.PROTECT, related_name="postes"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "poste")
        verbose_name = "Poste"

    def __str__(self):
        return self.structure


class Agent(UUIDModel):
    """Peut être créé par un poste local (hors ligne) : cf. sync ascendante."""
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, unique=True)
    statut_agent = models.CharField(max_length=100)

    class Meta:
        db_table = schema_table(SCHEMA, "agent")
        verbose_name = "Agent"

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Enregistrement(UUIDModel):
    """
    Trace qui (Agent) a enregistré quelle Autorisation, depuis quel Poste.
    Une autorisation ne peut être enregistrée qu'une seule fois
    (OneToOneField ci-dessous).
    """
    datetime_enregistrement = models.DateTimeField()
    autorisation = models.OneToOneField(
        Autorisation, on_delete=models.PROTECT, related_name="enregistrement"
    )
    agent = models.ForeignKey(
        Agent, on_delete=models.PROTECT, related_name="enregistrements"
    )
    poste = models.ForeignKey(
        Poste, on_delete=models.PROTECT, related_name="enregistrements"
    )

    class Meta:
        db_table = schema_table(SCHEMA, "enregistrement")
        verbose_name = "Enregistrement"

    def __str__(self):
        return f"Enregistrement {self.autorisation.numero}"
