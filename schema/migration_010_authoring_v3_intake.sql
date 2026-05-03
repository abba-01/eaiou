-- migration_010_authoring_v3_intake.sql
-- eaiou — authoring v3 intake schema (journal-rail lock + SLA + intake sessions)
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742
-- Date: 2026-05-02
--
-- Implements the v3 authoring architecture committed at
-- docs/AUTHORING_DESIGN_v3_FINAL.md. Lays the data layer for:
--   - the live-reactive journal & scope finder
--   - rails import + desktop lock at journal selection
--   - the 10-principle gate sequence (intake → validity → journal → rails → workspace)
--   - SLA status tracking with append-only override audit trail
--   - intake-session persistence so authors can abandon and resume per gate
--
-- Tables created:
--   1. eaiou_journals                — catalog of target journals + their rail constraints
--   2. eaiou_intake_sessions         — per-author intake state (Q1–Q5 + validity + journal)
--   3. eaiou_manuscript_journals     — m2m: manuscript ↔ candidate journals (primary | candidate)
--   4. eaiou_intake_session_log      — append-only event log per intake session
--
-- Tables altered:
--   eaiou_manuscripts — add journal_rails_json, journal_rails_locked_at,
--                       sla_status, sla_overrides_json, sla_status_changed_at,
--                       intake_session_id, current_gate
--
-- Idempotent: CREATE ... IF NOT EXISTS on tables, conditional ALTER for columns.
-- Run with: mariadb -u eaiou_db -p eaiou < schema/migration_010_authoring_v3_intake.sql

SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

-- ============================================================
-- 1. eaiou_journals
-- Catalog of target journals, each with its locked rail payload.
-- The rail JSON columns drive desktop lock at journal-selection time.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_journals` (
  `id`                          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `name`                        VARCHAR(255) NOT NULL,
  `publisher`                   VARCHAR(255) NOT NULL,
  `issn`                        VARCHAR(32)  NOT NULL DEFAULT '',
  `eissn`                       VARCHAR(32)  NOT NULL DEFAULT '',
  `homepage_url`                VARCHAR(512) NOT NULL DEFAULT '',
  `submission_url`              VARCHAR(512) NOT NULL DEFAULT '',
  `scope_keywords`              TEXT         NOT NULL COMMENT 'comma-separated topical scope (drives candidate filter)',
  `validity_routes_accepted`    TEXT         NOT NULL COMMENT 'JSON array — empirical, mathematical, theoretical, review, case_study, framework, position',
  `paper_types_accepted`        TEXT         NOT NULL COMMENT 'JSON array — research, letter, brief_communication, review, methods, data_note, registered_report',
  `audience_tier`               VARCHAR(32)  NOT NULL DEFAULT '' COMMENT 'peers | practitioners | policy | public | mixed',
  `word_limits_json`            TEXT         NOT NULL COMMENT 'JSON {abstract, main, methods, supplementary} per paper-type',
  `section_template_json`       TEXT         NOT NULL COMMENT 'JSON ordered list of required sections',
  `required_statements_json`    TEXT         NOT NULL COMMENT 'JSON array — data_availability, code_availability, competing_interests, etc.',
  `citation_style`              VARCHAR(64)  NOT NULL DEFAULT '' COMMENT 'e.g. nature, ieee, plos, cell, apa',
  `figure_limit`                INT          NOT NULL DEFAULT 0,
  `table_limit`                 INT          NOT NULL DEFAULT 0,
  `supplementary_allowed`       TINYINT(1)   NOT NULL DEFAULT 0,
  `preregistration_recognized`  TINYINT(1)   NOT NULL DEFAULT 0,
  `open_access_required`        TINYINT(1)   NOT NULL DEFAULT 0,
  `registered_report_track`     TINYINT(1)   NOT NULL DEFAULT 0,
  `ethics_required_for_json`    TEXT         NOT NULL COMMENT 'JSON array — human_subjects, animal_subjects, clinical_trial, etc.',
  `fees_json`                   TEXT         NOT NULL COMMENT 'JSON {apc, page_charge, color_charge, currency}',
  `acceptance_rate_pct`         DECIMAL(5,2) NULL DEFAULT NULL,
  `time_to_decision_days`       INT          NULL DEFAULT NULL,
  `scope_score_components_json` TEXT         NOT NULL COMMENT 'JSON tuning weights for journal.candidates_filter scoring',
  `data_source`                 VARCHAR(64)  NOT NULL DEFAULT 'manual' COMMENT 'manual | crossref | publisher_partner | imported',
  `last_refreshed_at`           DATETIME     NULL DEFAULT NULL,
  `state`                       TINYINT      NOT NULL DEFAULT 1 COMMENT '1=published, 0=hidden, -1=archived',
  `created_at`                  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`                  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_publisher` (`publisher`),
  KEY `idx_issn` (`issn`),
  KEY `idx_audience_tier` (`audience_tier`),
  KEY `idx_state` (`state`),
  KEY `idx_data_source` (`data_source`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Journal catalog with rail constraints — drives candidate filter and desktop lock';

-- ============================================================
-- 2. eaiou_intake_sessions
-- Per-author intake state. Holds Q1-Q5 answers, validity route,
-- candidate journal pool, current gate. Persisted across sessions
-- so authors can abandon mid-flow and resume from the same gate.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_intake_sessions` (
  `id`                       INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`                  INT UNSIGNED NOT NULL COMMENT 'fk #__eaiou_users.id (author)',
  `manuscript_id`            INT UNSIGNED NULL DEFAULT NULL COMMENT 'fk #__eaiou_manuscripts.id (linked at journal-selection gate)',
  `parent_session_id`        INT UNSIGNED NULL DEFAULT NULL COMMENT 'fk to a prior intake session (RESTRUCTURED chains to original)',
  `path`                     VARCHAR(16)  NOT NULL DEFAULT 'fresh' COMMENT 'fresh | restructured',
  `current_gate`             VARCHAR(64)  NOT NULL DEFAULT 'q1_question' COMMENT 'q1_question | q1_discovery | q1_confirm | q2_claim | q3_audience | q4_provenance | q5_falsifiability | validity_route | journal_family | journal_select | rails_import | scope_axis | workspace',
  `consent_status`           VARCHAR(32)  NOT NULL DEFAULT 'pending' COMMENT 'pending | accepted_fresh | accepted_restructured | declined_by_author | revoked',
  `consent_decision_at`      DATETIME     NULL DEFAULT NULL,
  `q1_question_raw`          TEXT         NOT NULL COMMENT 'author-typed question, pre-extraction',
  `q1_question_normalized`   TEXT         NOT NULL COMMENT 'analyzer-normalized form',
  `q1_confirmed_at`          DATETIME     NULL DEFAULT NULL,
  `q2_claim_type`            VARCHAR(64)  NOT NULL DEFAULT '' COMMENT 'measure | test | build | synthesize | argue',
  `q3_audience`              VARCHAR(64)  NOT NULL DEFAULT '' COMMENT 'peers | practitioners | policy | public',
  `q4_provenance`            TEXT         NOT NULL,
  `q5_falsifiability`        TEXT         NOT NULL,
  `validity_route`           VARCHAR(32)  NOT NULL DEFAULT '' COMMENT 'empirical | mathematical | theoretical | review | case_study | framework | position',
  `validity_standard`        VARCHAR(64)  NOT NULL DEFAULT '' COMMENT 'falsifiability | provability | boundary_conditions | reproducible_search | evidentiary_traceability | classification_utility | argumentative_coherence',
  `candidate_journals_json`  MEDIUMTEXT   NOT NULL COMMENT 'JSON array of journal_ids ranked, with per-candidate evidence_set + score',
  `selected_journal_ids_json` TEXT        NOT NULL COMMENT 'JSON array of selected journal_ids (single = [n], array = [n, m, k])',
  `primary_journal_id`       INT UNSIGNED NULL DEFAULT NULL,
  `commitment_ledger_json`   TEXT         NOT NULL COMMENT 'JSON snapshot at intent.commitment_seal',
  `commitment_sealed_at`     DATETIME     NULL DEFAULT NULL,
  `dismantle_buckets_json`   MEDIUMTEXT   NOT NULL COMMENT 'RESTRUCTURED only — three-bucket output of manuscript.dismantle',
  `created_at`               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`               DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY `idx_user` (`user_id`),
  KEY `idx_manuscript` (`manuscript_id`),
  KEY `idx_parent_session` (`parent_session_id`),
  KEY `idx_current_gate` (`current_gate`),
  KEY `idx_consent_status` (`consent_status`),
  KEY `idx_path` (`path`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Per-author intake state — persisted, resumable, gate-aware';

-- ============================================================
-- 3. eaiou_manuscript_journals
-- m2m: each manuscript can have one primary journal + array of candidates.
-- Switching primary within array is logged in switched_at_history_json.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_manuscript_journals` (
  `id`                          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `manuscript_id`               INT UNSIGNED NOT NULL COMMENT 'fk #__eaiou_manuscripts.id',
  `journal_id`                  INT UNSIGNED NOT NULL COMMENT 'fk #__eaiou_journals.id',
  `position`                    VARCHAR(16)  NOT NULL DEFAULT 'candidate' COMMENT 'primary | candidate',
  `selected_at`                 DATETIME     NULL DEFAULT NULL,
  `switched_at_history_json`    TEXT         NOT NULL COMMENT 'append-only JSON array of {timestamp, from_position, to_position, actor}',
  `removed_at`                  DATETIME     NULL DEFAULT NULL,
  `created_at`                  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_manuscript` (`manuscript_id`),
  KEY `idx_journal` (`journal_id`),
  KEY `idx_position` (`position`),
  UNIQUE KEY `uniq_manuscript_journal_active` (`manuscript_id`, `journal_id`, `removed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='m2m manuscript ↔ journals (single primary, ≥0 additional candidates)';

-- ============================================================
-- 4. eaiou_intake_session_log
-- Append-only event log per intake session. Captures every gate
-- transition, every override, every consent decision. Used for
-- audit trail and the SLA out-of-bounds reasoning.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_intake_session_log` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `intake_session_id`   INT UNSIGNED NOT NULL COMMENT 'fk #__eaiou_intake_sessions.id',
  `event_type`          VARCHAR(64)  NOT NULL COMMENT 'gate_advanced | gate_reverted | answer_recorded | journal_selected | journal_switched | restructure_initiated | consent_accepted | consent_declined | sla_override | sla_returned',
  `from_state`          VARCHAR(128) NOT NULL DEFAULT '',
  `to_state`            VARCHAR(128) NOT NULL DEFAULT '',
  `payload_json`        MEDIUMTEXT   NOT NULL COMMENT 'event-specific data (e.g. evidence cited, override rationale)',
  `actor`               VARCHAR(32)  NOT NULL DEFAULT 'author' COMMENT 'author | system | analyzer',
  `created_at`          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `idx_intake_session` (`intake_session_id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Append-only intake session event log — never edited, only appended';

-- ============================================================
-- 5. ALTER eaiou_manuscripts — add v3 fields
-- ============================================================

-- Helper: idempotent ADD COLUMN via stored procedure
DROP PROCEDURE IF EXISTS `eaiou_add_column_if_missing`;
DELIMITER //
CREATE PROCEDURE `eaiou_add_column_if_missing`(
  IN tbl VARCHAR(64),
  IN col VARCHAR(64),
  IN ddl TEXT
)
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = DATABASE()
      AND table_name = tbl
      AND column_name = col
  ) THEN
    SET @sql = CONCAT('ALTER TABLE `', tbl, '` ADD COLUMN ', ddl);
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
  END IF;
END //
DELIMITER ;

CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'intake_session_id',
  '`intake_session_id` INT UNSIGNED NULL DEFAULT NULL COMMENT ''fk #__eaiou_intake_sessions.id'' AFTER `id`'
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'current_gate',
  '`current_gate` VARCHAR(64) NOT NULL DEFAULT ''q1_question'' COMMENT ''gate sequencing for resume-from-gate''  AFTER `status`'
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'journal_rails_json',
  '`journal_rails_json` MEDIUMTEXT NOT NULL COMMENT ''pinned superset rails — drives desktop lock''  AFTER `target_venue`'
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'journal_rails_locked_at',
  '`journal_rails_locked_at` DATETIME NULL DEFAULT NULL  AFTER `journal_rails_json`'
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'sla_status',
  '`sla_status` VARCHAR(32) NOT NULL DEFAULT ''in_sla'' COMMENT ''in_sla | out_of_sla'''
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'sla_overrides_json',
  '`sla_overrides_json` MEDIUMTEXT NOT NULL COMMENT ''append-only JSON array of override events''  AFTER `sla_status`'
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'sla_status_changed_at',
  '`sla_status_changed_at` DATETIME NULL DEFAULT NULL  AFTER `sla_overrides_json`'
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'corresponding_author_id',
  '`corresponding_author_id` INT UNSIGNED NULL DEFAULT NULL COMMENT ''fk #__eaiou_users.id — single corresponding author owns gates'''
);
CALL eaiou_add_column_if_missing(
  'jos_eaiou_manuscripts', 'co_authors_json',
  '`co_authors_json` TEXT NOT NULL COMMENT ''JSON array of co-author user_ids with attributed sections'''
);

DROP PROCEDURE IF EXISTS `eaiou_add_column_if_missing`;

-- Ensure idx
ALTER TABLE `jos_eaiou_manuscripts`
  ADD INDEX IF NOT EXISTS `idx_intake_session` (`intake_session_id`),
  ADD INDEX IF NOT EXISTS `idx_current_gate`   (`current_gate`),
  ADD INDEX IF NOT EXISTS `idx_sla_status`     (`sla_status`),
  ADD INDEX IF NOT EXISTS `idx_corresponding`  (`corresponding_author_id`);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- Migration 010 complete.
-- Next: seed eaiou_journals with ~50 high-volume journals via
--       schema/seed_journals_v1.sql (separate file).
-- ============================================================
