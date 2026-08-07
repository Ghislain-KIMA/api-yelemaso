-- ============================================================================
-- SCHEMA POSTGRESQL - Systeme de gestion des autorisations de manifestations
-- Serveur central -- version alignee sur le MPD final (34 tables)
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- CREATION DES SCHEMAS
-- ============================================================================
CREATE SCHEMA IF NOT EXISTS administration;
CREATE SCHEMA IF NOT EXISTS gestion;
CREATE SCHEMA IF NOT EXISTS securite;
CREATE SCHEMA IF NOT EXISTS culture;

-- ============================================================================
-- SCHEMA: administration
-- ============================================================================

CREATE TABLE administration.region (
    id          SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_region  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE administration.province (
    id            SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_province  VARCHAR(50) NOT NULL UNIQUE,
    region_id     SMALLINT NOT NULL REFERENCES administration.region(id)
);

CREATE TABLE administration.type_commune (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE administration.commune (
    id                SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_commune       VARCHAR(50) NOT NULL,
    type_commune_id   SMALLINT REFERENCES administration.type_commune(id),
    province_id       SMALLINT NOT NULL REFERENCES administration.province(id),
    CONSTRAINT uq_commune_nom_province UNIQUE (nom_commune, province_id)
);

CREATE TABLE administration.type_mairie (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE administration.mairie (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom_mairie      VARCHAR(50) NOT NULL,
    type_mairie_id  SMALLINT NOT NULL REFERENCES administration.type_mairie(id),
    commune_id      SMALLINT NOT NULL REFERENCES administration.commune(id),
    CONSTRAINT uq_mairie_nom_commune UNIQUE (nom_mairie, commune_id)
);

CREATE OR REPLACE FUNCTION administration.check_unicite_mairie()
RETURNS TRIGGER AS $$
DECLARE
    v_label_type_commune VARCHAR(50);
    v_nb_mairies INTEGER;
BEGIN
    SELECT tc.label INTO v_label_type_commune
    FROM administration.commune c
    LEFT JOIN administration.type_commune tc ON tc.id = c.type_commune_id
    WHERE c.id = NEW.commune_id;

    -- Si le type de la commune n'est pas encore renseigné (import en
    -- cours, classification pas encore faite), on ne peut pas appliquer
    -- la règle "une seule mairie" -- elle sera revérifiée dès que le
    -- type sera connu (au prochain INSERT/UPDATE d'une Mairie).
    IF v_label_type_commune IS NULL THEN
        RETURN NEW;
    END IF;

    IF lower(v_label_type_commune) IN ('rurale', 'urbaine') THEN
        SELECT count(*) INTO v_nb_mairies
        FROM administration.mairie
        WHERE commune_id = NEW.commune_id
          AND id <> COALESCE(NEW.id, -1);

        IF v_nb_mairies >= 1 THEN
            RAISE EXCEPTION
                'La commune % (type %) ne peut avoir qu''une seule mairie',
                NEW.commune_id, v_label_type_commune;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_unicite_mairie
    BEFORE INSERT OR UPDATE ON administration.mairie
    FOR EACH ROW EXECUTE FUNCTION administration.check_unicite_mairie();

-- ============================================================================
-- SCHEMA: gestion
-- ============================================================================

CREATE TABLE gestion.statut_demandeur (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE gestion.cnib (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero     VARCHAR(50) NOT NULL UNIQUE,
    date_cnib  DATE NOT NULL,
    structure  VARCHAR(50) NOT NULL
);

CREATE TABLE gestion.demandeur (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom                   VARCHAR(50) NOT NULL,
    prenom                VARCHAR(100) NOT NULL,
    telephone             VARCHAR(20) NOT NULL UNIQUE,
    email                 VARCHAR(100) UNIQUE,
    profession            VARCHAR(255) NOT NULL,
    residence             VARCHAR(100) NOT NULL,
    cnib_id               UUID NOT NULL UNIQUE REFERENCES gestion.cnib(id),
    statut_demandeur_id   SMALLINT REFERENCES gestion.statut_demandeur(id)
);

CREATE TABLE gestion.statut_demandeur_autre (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label                 VARCHAR(100) NOT NULL,
    datetime_proposition  TIMESTAMP NOT NULL,
    statut                VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    demandeur_id          UUID NOT NULL REFERENCES gestion.demandeur(id)
);

CREATE TABLE gestion.demande (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_demande   DATE NOT NULL,
    objet          VARCHAR(255) NOT NULL,
    demandeur_id   UUID NOT NULL REFERENCES gestion.demandeur(id)
);

CREATE TABLE gestion.personne (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom         VARCHAR(50) NOT NULL,
    prenom      VARCHAR(100) NOT NULL,
    profession  VARCHAR(255),
    grade       VARCHAR(255),
    CONSTRAINT chk_personne_profession_ou_grade
        CHECK (profession IS NOT NULL OR grade IS NOT NULL)
);

CREATE TABLE gestion.habilitation (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fonction     VARCHAR(255) NOT NULL,
    attribution  VARCHAR(255)
);

CREATE TABLE gestion.document (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fichier             VARCHAR(500) NOT NULL,
    type_document       VARCHAR(20) NOT NULL
        CHECK (type_document IN ('word', 'pdf', 'scanne', 'photo')),
    texte_extrait       TEXT,
    datetime_upload     TIMESTAMP NOT NULL DEFAULT now(),
    statut_extraction   VARCHAR(50) NOT NULL DEFAULT 'brute'
        CHECK (statut_extraction IN ('brute', 'en_validation', 'validee', 'rejetee'))
);

CREATE TABLE gestion.autorisation (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    numero              VARCHAR(100) NOT NULL UNIQUE,
    date_autorisation   DATE NOT NULL,
    mairie_id           SMALLINT NOT NULL REFERENCES administration.mairie(id),
    demande_id          UUID NOT NULL REFERENCES gestion.demande(id),
    -- Une autorisation ne peut exister que si elle decoule d'un document
    -- source (photo/scan/Word) valide -- coherent avec le perimetre du
    -- projet limite a l'extraction de documents existants (pas de saisie
    -- directe pour l'instant).
    document_id         UUID NOT NULL UNIQUE REFERENCES gestion.document(id)
);

CREATE TABLE gestion.signature (
    autorisation_id   UUID PRIMARY KEY REFERENCES gestion.autorisation(id),
    personne_id       UUID NOT NULL REFERENCES gestion.personne(id),
    habilitation_id   UUID NOT NULL REFERENCES gestion.habilitation(id)
);

CREATE TABLE gestion.ampliation (
    id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label  VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE gestion.autorisation_ampliation (
    autorisation_id   UUID NOT NULL REFERENCES gestion.autorisation(id),
    ampliation_id     UUID NOT NULL REFERENCES gestion.ampliation(id),
    structure         VARCHAR(255) NOT NULL,
    PRIMARY KEY (autorisation_id, ampliation_id)
);

-- ============================================================================
-- SCHEMA: securite
-- ============================================================================

CREATE TABLE securite.poste (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    structure   VARCHAR(256) NOT NULL,
    telephone   VARCHAR(20) UNIQUE,
    email       VARCHAR(100) UNIQUE,
    login_at    TIMESTAMP,
    created_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_at  TIMESTAMP,
    deleted_at  TIMESTAMP,
    mairie_id   SMALLINT NOT NULL REFERENCES administration.mairie(id)
);

CREATE TABLE securite.agent (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nom            VARCHAR(50) NOT NULL,
    prenom         VARCHAR(100) NOT NULL,
    telephone      VARCHAR(20) NOT NULL UNIQUE,
    statut_agent   VARCHAR(100) NOT NULL
);

CREATE TABLE securite.enregistrement (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    datetime_enregistrement   TIMESTAMP NOT NULL,
    autorisation_id           UUID NOT NULL UNIQUE REFERENCES gestion.autorisation(id),
    agent_id                  UUID NOT NULL REFERENCES securite.agent(id),
    poste_id                  UUID NOT NULL REFERENCES securite.poste(id)
);

-- ============================================================================
-- SCHEMA: culture
-- ============================================================================

CREATE TABLE culture.mode_acces (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE culture.genre (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE culture.periodicite (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE culture.type_manifestation (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE culture.dimension (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE culture.type_espace (
    id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label  VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE culture.manifestation (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    espace                  VARCHAR(256) NOT NULL,
    duree                   INTEGER,
    datetime_debut          TIMESTAMP NOT NULL,
    datetime_fin            TIMESTAMP,
    mode_acces_id           SMALLINT NOT NULL REFERENCES culture.mode_acces(id),
    genre_id                SMALLINT REFERENCES culture.genre(id),
    periodicite_id          SMALLINT REFERENCES culture.periodicite(id),
    type_manifestation_id   SMALLINT REFERENCES culture.type_manifestation(id),
    dimension_id            SMALLINT REFERENCES culture.dimension(id),
    type_espace_id          SMALLINT REFERENCES culture.type_espace(id)
);

CREATE TABLE culture.demande_manifestation (
    demande_id        UUID NOT NULL REFERENCES gestion.demande(id),
    manifestation_id  UUID NOT NULL REFERENCES culture.manifestation(id),
    PRIMARY KEY (demande_id, manifestation_id)
);

CREATE TABLE culture.genre_autre (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label                 VARCHAR(100) NOT NULL,
    datetime_proposition  TIMESTAMP NOT NULL,
    statut                VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    manifestation_id      UUID NOT NULL REFERENCES culture.manifestation(id)
);

CREATE TABLE culture.type_manifestation_autre (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label                 VARCHAR(100) NOT NULL,
    datetime_proposition  TIMESTAMP NOT NULL,
    statut                VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    manifestation_id      UUID NOT NULL REFERENCES culture.manifestation(id)
);

CREATE TABLE culture.periodicite_autre (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label                 VARCHAR(100) NOT NULL,
    datetime_proposition  TIMESTAMP NOT NULL,
    statut                VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    manifestation_id      UUID NOT NULL REFERENCES culture.manifestation(id)
);

CREATE TABLE culture.dimension_autre (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label                 VARCHAR(100) NOT NULL,
    datetime_proposition  TIMESTAMP NOT NULL,
    statut                VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    manifestation_id      UUID NOT NULL REFERENCES culture.manifestation(id)
);

CREATE TABLE culture.type_espace_autre (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label                 VARCHAR(100) NOT NULL,
    datetime_proposition  TIMESTAMP NOT NULL,
    statut                VARCHAR(50) NOT NULL DEFAULT 'en_attente',
    manifestation_id      UUID NOT NULL REFERENCES culture.manifestation(id)
);

-- ============================================================================
-- INDEX complementaires
-- ============================================================================

CREATE INDEX idx_province_region ON administration.province(region_id);
CREATE INDEX idx_commune_province ON administration.commune(province_id);
CREATE INDEX idx_commune_type ON administration.commune(type_commune_id);
CREATE INDEX idx_mairie_commune ON administration.mairie(commune_id);
CREATE INDEX idx_mairie_type ON administration.mairie(type_mairie_id);

CREATE INDEX idx_demandeur_statut ON gestion.demandeur(statut_demandeur_id);
CREATE INDEX idx_statut_demandeur_autre_demandeur ON gestion.statut_demandeur_autre(demandeur_id);
CREATE INDEX idx_statut_demandeur_autre_statut ON gestion.statut_demandeur_autre(statut);
CREATE INDEX idx_demande_demandeur ON gestion.demande(demandeur_id);
CREATE INDEX idx_autorisation_mairie ON gestion.autorisation(mairie_id);
CREATE INDEX idx_autorisation_demande ON gestion.autorisation(demande_id);
CREATE INDEX idx_document_statut_extraction ON gestion.document(statut_extraction);
CREATE INDEX idx_signature_personne ON gestion.signature(personne_id);
CREATE INDEX idx_signature_habilitation ON gestion.signature(habilitation_id);
CREATE INDEX idx_autorisation_ampliation_ampliation ON gestion.autorisation_ampliation(ampliation_id);

CREATE INDEX idx_poste_mairie ON securite.poste(mairie_id);
CREATE INDEX idx_enregistrement_agent ON securite.enregistrement(agent_id);
CREATE INDEX idx_enregistrement_poste ON securite.enregistrement(poste_id);

CREATE INDEX idx_manifestation_mode_acces ON culture.manifestation(mode_acces_id);
CREATE INDEX idx_manifestation_genre ON culture.manifestation(genre_id);
CREATE INDEX idx_manifestation_periodicite ON culture.manifestation(periodicite_id);
CREATE INDEX idx_manifestation_type ON culture.manifestation(type_manifestation_id);
CREATE INDEX idx_manifestation_dimension ON culture.manifestation(dimension_id);
CREATE INDEX idx_manifestation_espace ON culture.manifestation(type_espace_id);
CREATE INDEX idx_demande_manifestation_manif ON culture.demande_manifestation(manifestation_id);

CREATE INDEX idx_genre_autre_manifestation ON culture.genre_autre(manifestation_id);
CREATE INDEX idx_genre_autre_statut ON culture.genre_autre(statut);
CREATE INDEX idx_type_manifestation_autre_manifestation ON culture.type_manifestation_autre(manifestation_id);
CREATE INDEX idx_type_manifestation_autre_statut ON culture.type_manifestation_autre(statut);
CREATE INDEX idx_periodicite_autre_manifestation ON culture.periodicite_autre(manifestation_id);
CREATE INDEX idx_periodicite_autre_statut ON culture.periodicite_autre(statut);
CREATE INDEX idx_dimension_autre_manifestation ON culture.dimension_autre(manifestation_id);
CREATE INDEX idx_dimension_autre_statut ON culture.dimension_autre(statut);
CREATE INDEX idx_type_espace_autre_manifestation ON culture.type_espace_autre(manifestation_id);
CREATE INDEX idx_type_espace_autre_statut ON culture.type_espace_autre(statut);

-- ============================================================================
-- search_path recommande pour la connexion applicative (Django) :
--   ALTER ROLE django_app SET search_path TO gestion, securite, culture,
--                                            administration, public;
-- ============================================================================
