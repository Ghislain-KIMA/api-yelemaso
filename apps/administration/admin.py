from django.contrib import admin

from .models import Commune, Mairie, Province, Region, TypeCommune, TypeMairie

admin.site.register(Region)
admin.site.register(Province)
admin.site.register(TypeCommune)
admin.site.register(Commune)
admin.site.register(TypeMairie)
admin.site.register(Mairie)
