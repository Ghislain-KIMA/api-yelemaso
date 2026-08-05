from django.contrib import admin

from .models import Agent, Enregistrement, Poste

admin.site.register(Poste)
admin.site.register(Agent)
admin.site.register(Enregistrement)
