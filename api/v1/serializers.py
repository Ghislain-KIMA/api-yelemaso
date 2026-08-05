"""
Serializers consommés par le poste central (CRUD complet, dashboard,
classement des propositions "Autre").
"""
from rest_framework import serializers

from apps.culture.models import (
    DimensionAutre,
    GenreAutre,
    Manifestation,
    PeriodiciteAutre,
    TypeEspaceAutre,
    TypeManifestationAutre,
)
from apps.gestion.models import (
    Autorisation,
    Demande,
    Demandeur,
    Document,
    Habilitation,
    Personne,
    Signature,
    StatutDemandeurAutre,
)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ["texte_extrait", "statut_extraction", "datetime_upload"]


class DemandeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demandeur
        fields = "__all__"


class DemandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demande
        fields = "__all__"


class ManifestationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manifestation
        fields = "__all__"


class AutorisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autorisation
        fields = "__all__"


class PersonneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personne
        fields = "__all__"


class HabilitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habilitation
        fields = "__all__"


class SignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signature
        fields = "__all__"


class StatutDemandeurAutreSerializer(serializers.ModelSerializer):
    """
    Classement d'une proposition : le centre choisit/crée un StatutDemandeur,
    puis PATCH cette ressource avec `statut="classee"`. La mise à jour de
    Demandeur.statut_demandeur se fait séparément (côté vue), cette
    ressource ne fait que suivre le statut de la proposition elle-même.
    """
    class Meta:
        model = StatutDemandeurAutre
        fields = "__all__"


class GenreAutreSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenreAutre
        fields = "__all__"


class TypeManifestationAutreSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeManifestationAutre
        fields = "__all__"


class PeriodiciteAutreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodiciteAutre
        fields = "__all__"


class DimensionAutreSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimensionAutre
        fields = "__all__"


class TypeEspaceAutreSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeEspaceAutre
        fields = "__all__"
