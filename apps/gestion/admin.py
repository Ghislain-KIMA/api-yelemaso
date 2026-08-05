from django.contrib import admin

from .models import (
    CNIB,
    Ampliation,
    Autorisation,
    AutorisationAmpliation,
    Demande,
    Demandeur,
    Document,
    Habilitation,
    Personne,
    Signature,
    StatutDemandeur,
    StatutDemandeurAutre,
)

admin.site.register(StatutDemandeur)
admin.site.register(CNIB)
admin.site.register(Demandeur)
admin.site.register(StatutDemandeurAutre)
admin.site.register(Demande)
admin.site.register(Personne)
admin.site.register(Habilitation)
admin.site.register(Document)
admin.site.register(Autorisation)
admin.site.register(Signature)
admin.site.register(Ampliation)
admin.site.register(AutorisationAmpliation)
