from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("documents", views.DocumentViewSet, basename="document")
router.register("demandeurs", views.DemandeurViewSet, basename="demandeur")
router.register("demandes", views.DemandeViewSet, basename="demande")
router.register("manifestations", views.ManifestationViewSet, basename="manifestation")
router.register("autorisations", views.AutorisationViewSet, basename="autorisation")
router.register("personnes", views.PersonneViewSet, basename="personne")
router.register("habilitations", views.HabilitationViewSet, basename="habilitation")
router.register("signatures", views.SignatureViewSet, basename="signature")
router.register(
    "statut-demandeur-autre",
    views.StatutDemandeurAutreViewSet,
    basename="statut-demandeur-autre",
)
router.register("genre-autre", views.GenreAutreViewSet, basename="genre-autre")
router.register(
    "type-manifestation-autre",
    views.TypeManifestationAutreViewSet,
    basename="type-manifestation-autre",
)
router.register(
    "periodicite-autre", views.PeriodiciteAutreViewSet, basename="periodicite-autre"
)
router.register("dimension-autre", views.DimensionAutreViewSet, basename="dimension-autre")
router.register(
    "type-espace-autre", views.TypeEspaceAutreViewSet, basename="type-espace-autre"
)

urlpatterns = router.urls
