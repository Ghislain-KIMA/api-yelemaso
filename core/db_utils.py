"""
Utilitaire pour qualifier le nom de table Django avec un schéma PostgreSQL.

Django place par défaut toutes les tables dans le schéma "public". Cette
astuce (db_table contenant un guillemet + point) permet de cibler un autre
schéma sans rien changer côté migrations : Django entoure db_table de
guillemets doubles tel quel, donc schema_table('gestion', 'demande')
produit la table "gestion"."demande".

Les 4 schémas utilisés dans ce projet : administration, gestion,
securite, culture — voir docs/database/schema/schema_postgresql.sql

SQLite (utilisé pour des tests locaux rapides sans serveur PostgreSQL)
ne supporte pas cette syntaxe de schéma -- DB_USE_SCHEMAS=False dans les
settings (voir config/settings/test_local.py) fait retomber sur un nom de
table simple, préfixé par le schéma pour éviter les collisions
(ex: 'gestion_demande' plutôt que '"gestion"."demande"').
"""
from django.conf import settings


def schema_table(schema: str, name: str) -> str:
    if getattr(settings, "DB_USE_SCHEMAS", True):
        return f'{schema}"."{name}'
    return f"{schema}_{name}"
