-- eaiou Python CMS — Migration 002
-- Purpose: IntelliD registry, contribution graph, CosmoID, tombstone model
-- Run after: python_cms_migration_001.sql
-- Date: 2026-04-10
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742

-- ─── CosmoID on papers ────────────────────────────────────────────────────────
-- Every record gets a CosmoID at creation. Permanent. Never null after creation.
-- CosmoID persists through tombstone — it represents the existence of a state,
-- not the visibility of a record.

ALTER TABLE `#__eaiou_papers`
  ADD COLUMN IF NOT EXISTS `cosmoid`         CHAR(36) DEFAULT NULL UNIQUE
      COMMENT 'State fingerprint. Minted at record creation. Never removed.',
  ADD COLUMN IF NOT EXISTS `tombstone_state` ENUM('private','revivable','reusable','public_unspace') DEFAULT NULL
      COMMENT 'NULL = active record. Set on tombstone transition.',
  ADD COLUMN IF NOT EXISTS `tombstone_reason` TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `tombstone_at`    DATETIME DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `tombstone_by`    INT DEFAULT NULL COMMENT 'intellid or user_id';

-- ─── IntelliD Registry ────────────────────────────────────────────────────────
-- One row per contributing intelligence instance.
-- IntelliD is eaiou-minted, opaque, routable.
-- provider mapping is sealed (model_family is disclosed; session mapping is not).

CREATE TABLE IF NOT EXISTS `#__eaiou_intellid_registry` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `intellid`        CHAR(36) NOT NULL UNIQUE         COMMENT 'eaiou-minted UUID. Opaque.',
  `type`            ENUM('human','ai','hybrid','institutional','system') NOT NULL,
  `origin`          ENUM('orcid','model','mcp','api','manual','unknown') NOT NULL DEFAULT 'unknown',
  `model_family`    VARCHAR(255) DEFAULT NULL         COMMENT 'claude, gpt-4, etc. Disclosed. Not provider-specific.',
  `instance_hash`   VARCHAR(64)  DEFAULT NULL         COMMENT 'SHA256 of session-specific context. Sealed.',
  `connector`       ENUM('mcp','api','direct','manual','system') DEFAULT NULL,
  `cosmoid_context` CHAR(36)     DEFAULT NULL         COMMENT 'CosmoID of the paper/context this IntelliD was active in.',
  `scope_paper_id`  INT          DEFAULT NULL         COMMENT 'Paper this IntelliD was issued for. NULL = cross-paper identity.',
  `public_type`     TINYINT      NOT NULL DEFAULT 1   COMMENT '1=type publicly disclosed (human/ai/etc). 0=sealed.',
  `state`           TINYINT      NOT NULL DEFAULT 1,
  `created`         DATETIME     NOT NULL,
  INDEX `idx_intellid`  (`intellid`),
  INDEX `idx_type`      (`type`),
  INDEX `idx_scope`     (`scope_paper_id`),
  INDEX `idx_cosmoid`   (`cosmoid_context`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── IntelliD Contributions (the graph) ──────────────────────────────────────
-- One row per (intellid, artifact, relation) edge.
-- This replaces string-based attribution_log as the authoritative attribution layer.
-- Not a timeline. A graph.

CREATE TABLE IF NOT EXISTS `#__eaiou_intellid_contributions` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `intellid`        CHAR(36)     NOT NULL              COMMENT 'Contributing intelligence (FK to intellid_registry)',
  `artifact_type`   ENUM('paper','version','ai_session','remsearch','review','dataset','claim') NOT NULL,
  `artifact_id`     INT          DEFAULT NULL           COMMENT 'Integer PK of the artifact, if applicable.',
  `artifact_uuid`   CHAR(36)     DEFAULT NULL           COMMENT 'UUID of the artifact, if applicable.',
  `cosmoid`         CHAR(36)     DEFAULT NULL           COMMENT 'CosmoID of the artifact at contribution time.',
  `relation`        ENUM('generated','edited','validated','rejected','reviewed','cited','derived','proposed','refuted') NOT NULL,
  `weight`          DECIMAL(5,3) DEFAULT NULL           COMMENT 'Contribution weight 0.000–1.000.',
  `confidence`      DECIMAL(5,3) DEFAULT NULL           COMMENT 'Attribution confidence 0.000–1.000.',
  `notes`           TEXT         DEFAULT NULL,
  `state`           TINYINT      NOT NULL DEFAULT 1,
  `created`         DATETIME     NOT NULL,
  INDEX `idx_intellid`   (`intellid`),
  INDEX `idx_artifact`   (`artifact_type`, `artifact_id`),
  INDEX `idx_cosmoid`    (`cosmoid`),
  INDEX `idx_relation`   (`relation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Observation log (UHA layer — optional, only populated on read events) ───
-- UHA is the observation/address layer. Only populated if you choose to record
-- that an observation happened. Most reads will not produce a record here.
-- When populated: encodes the observation event in a self-decoding, frame-agnostic way.

CREATE TABLE IF NOT EXISTS `#__eaiou_observation_log` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `observed_cosmoid` CHAR(36)    NOT NULL               COMMENT 'CosmoID of the artifact that was observed.',
  `observer_intellid` CHAR(36)   DEFAULT NULL            COMMENT 'IntelliD of the observing intelligence, if known.',
  `observation_type` ENUM('read','cite','fork','contact','validate','replicate') NOT NULL DEFAULT 'read',
  `uha_address`     VARCHAR(500) DEFAULT NULL            COMMENT 'UHA-encoded observation address, if encoded.',
  `uha_cosmoid`     CHAR(36)     DEFAULT NULL            COMMENT 'CosmoID under which UHA was computed.',
  `observation_at`  DATETIME     NOT NULL,
  -- No index on observation_at — Temporal Blindness applies to observation timing too
  INDEX `idx_observed_cosmoid`  (`observed_cosmoid`),
  INDEX `idx_observer_intellid` (`observer_intellid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
