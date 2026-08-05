from django.contrib import admin

from .models import (
    Dimension,
    DimensionAutre,
    DemandeManifestation,
    Genre,
    GenreAutre,
    Manifestation,
    ModeAcces,
    Periodicite,
    PeriodiciteAutre,
    TypeEspace,
    TypeEspaceAutre,
    TypeManifestation,
    TypeManifestationAutre,
)

admin.site.register(ModeAcces)
admin.site.register(Genre)
admin.site.register(GenreAutre)
admin.site.register(Periodicite)
admin.site.register(PeriodiciteAutre)
admin.site.register(TypeManifestation)
admin.site.register(TypeManifestationAutre)
admin.site.register(Dimension)
admin.site.register(DimensionAutre)
admin.site.register(TypeEspace)
admin.site.register(TypeEspaceAutre)
admin.site.register(Manifestation)
admin.site.register(DemandeManifestation)
