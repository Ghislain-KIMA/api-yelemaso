"""
Restrictions d'accès pour le rôle admin (poste central) :
device binding, restriction horaire, etc. — à appliquer côté
api/v1/admin/views.py une fois le mécanisme d'authentification en place.
"""
from datetime import time

from django.utils import timezone
from rest_framework.permissions import BasePermission

HEURES_OUVERTURE = time(8, 0)
HEURES_FERMETURE = time(18, 0)


class EstDansPlageHoraireAdmin(BasePermission):
    message = "Accès admin restreint aux heures de service."

    def has_permission(self, request, view):
        now = timezone.localtime().time()
        return HEURES_OUVERTURE <= now <= HEURES_FERMETURE
