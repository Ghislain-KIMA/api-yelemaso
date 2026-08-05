from rest_framework import viewsets

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

from .serializers import (
    AutorisationSerializer,
    DemandeSerializer,
    DemandeurSerializer,
    DimensionAutreSerializer,
    DocumentSerializer,
    GenreAutreSerializer,
    HabilitationSerializer,
    ManifestationSerializer,
    PeriodiciteAutreSerializer,
    PersonneSerializer,
    SignatureSerializer,
    StatutDemandeurAutreSerializer,
    TypeEspaceAutreSerializer,
    TypeManifestationAutreSerializer,
)


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filterset_fields = ["statut_extraction", "type_document"]


class DemandeurViewSet(viewsets.ModelViewSet):
    queryset = Demandeur.objects.all()
    serializer_class = DemandeurSerializer


class DemandeViewSet(viewsets.ModelViewSet):
    queryset = Demande.objects.all()
    serializer_class = DemandeSerializer


class ManifestationViewSet(viewsets.ModelViewSet):
    queryset = Manifestation.objects.all()
    serializer_class = ManifestationSerializer


class AutorisationViewSet(viewsets.ModelViewSet):
    queryset = Autorisation.objects.all()
    serializer_class = AutorisationSerializer


class PersonneViewSet(viewsets.ModelViewSet):
    queryset = Personne.objects.all()
    serializer_class = PersonneSerializer


class HabilitationViewSet(viewsets.ModelViewSet):
    queryset = Habilitation.objects.all()
    serializer_class = HabilitationSerializer


class SignatureViewSet(viewsets.ModelViewSet):
    queryset = Signature.objects.all()
    serializer_class = SignatureSerializer


class StatutDemandeurAutreViewSet(viewsets.ModelViewSet):
    """
    Écran de classement (poste central) : lister les propositions
    en_attente, puis PATCH avec statut="classee" une fois qu'un
    StatutDemandeur a été choisi/créé et appliqué sur Demandeur
    (mise à jour à faire séparément, cette ressource ne suit que la
    proposition elle-même).
    """
    queryset = StatutDemandeurAutre.objects.all()
    serializer_class = StatutDemandeurAutreSerializer
    filterset_fields = ["statut"]


class GenreAutreViewSet(viewsets.ModelViewSet):
    queryset = GenreAutre.objects.all()
    serializer_class = GenreAutreSerializer
    filterset_fields = ["statut"]


class TypeManifestationAutreViewSet(viewsets.ModelViewSet):
    queryset = TypeManifestationAutre.objects.all()
    serializer_class = TypeManifestationAutreSerializer
    filterset_fields = ["statut"]


class PeriodiciteAutreViewSet(viewsets.ModelViewSet):
    queryset = PeriodiciteAutre.objects.all()
    serializer_class = PeriodiciteAutreSerializer
    filterset_fields = ["statut"]


class DimensionAutreViewSet(viewsets.ModelViewSet):
    queryset = DimensionAutre.objects.all()
    serializer_class = DimensionAutreSerializer
    filterset_fields = ["statut"]


class TypeEspaceAutreViewSet(viewsets.ModelViewSet):
    queryset = TypeEspaceAutre.objects.all()
    serializer_class = TypeEspaceAutreSerializer
    filterset_fields = ["statut"]
