-- À exécuter une seule fois, avant la toute première migration Django
-- (ou via une migration RunSQL dans apps/administration/migrations/0001_initial.py)
CREATE SCHEMA IF NOT EXISTS administration;
CREATE SCHEMA IF NOT EXISTS gestion;
CREATE SCHEMA IF NOT EXISTS securite;
CREATE SCHEMA IF NOT EXISTS culture;
