-- ============================================================
-- eaiou Python CMS — Fresh Install (single-file)
-- Version: 1.0 (2026-04-10)
-- Platform: MariaDB 10.x / Python FastAPI CMS (no Joomla)
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742
--
-- This script creates the complete eaiou database from scratch
-- for the Python CMS. It does NOT require Joomla to be installed.
-- It incorporates all migrations (001, 002) inline.
--
-- Run: mariadb -u root -p eaiou < python_cms_install_fresh.sql
--
-- TEMPORAL BLINDNESS ENFORCEMENT:
-- submitted_at, acceptance_sealed_at, publication_sealed_at
-- carry NO INDEXES by design. Indexing sealed temporal fields
-- creates a timing side-channel that allows bias to infer
-- submission order. q_overall is the ONLY discovery sort key.
-- Do not add indexes to sealed fields. This is not an omission.
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

-- ============================================================
-- 1. eaiou_papers (Python CMS native — no Joomla baggage)
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_papers` (
  `id`                      INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_uuid`              CHAR(36)     NOT NULL UNIQUE COMMENT 'random UUID4, minted at submission',
  `cosmoid`                 CHAR(36)     DEFAULT NULL   COMMENT 'context fingerprint, minted at creation, NEVER removed',
  `title`                   VARCHAR(1000) DEFAULT NULL,
  `abstract`                LONGTEXT     DEFAULT NULL,
  `author_name`             VARCHAR(255) DEFAULT NULL,
  `orcid`                   VARCHAR(50)  DEFAULT NULL,
  `keywords`                TEXT         DEFAULT NULL,
  `ai_disclosure_level`     ENUM('none','editing','analysis','drafting','collaborative') DEFAULT NULL,
  `ai_disclosure_notes`     TEXT         DEFAULT NULL,
  `status`                  VARCHAR(50)  NOT NULL DEFAULT 'draft'
                            COMMENT 'draft → submitted → under_review → revision_requested → accepted/rejected → published/archived',
  `authorship_mode`         ENUM('human','ai','hybrid') NOT NULL DEFAULT 'human',
  -- SEALED TEMPORAL STATE SPACE — NO INDEXES (timing side-channel prevention)
  `submitted_at`            DATETIME     DEFAULT NULL COMMENT 'sealed at submission receipt — never shown during review',
  `acceptance_sealed_at`    DATETIME     DEFAULT NULL COMMENT 'sealed at acceptance — never displayed publicly',
  `publication_sealed_at`   DATETIME     DEFAULT NULL COMMENT 'sealed at publication — never displayed publicly',
  -- END SEALED FIELDS
  `submission_hash`         VARCHAR(64)  DEFAULT NULL COMMENT 'SHA256(paper_uuid+submitted_at+content_hash)',
  `submission_capstone`     VARCHAR(255) DEFAULT NULL COMMENT 'Zenodo DOI — public receipt without revealing timing',
  `q_overall`               DECIMAL(7,4) DEFAULT NULL COMMENT 'quality signal — the sole discovery sort key',
  -- Tombstone model (annotate, never purge)
  `tombstone_state`         ENUM('private','revivable','reusable','public_unspace') DEFAULT NULL
                            COMMENT 'NULL = active record. Set on tombstone transition.',
  `tombstone_reason`        TEXT         DEFAULT NULL,
  `tombstone_at`            DATETIME     DEFAULT NULL,
  -- Metadata
  `doi`                     VARCHAR(255) DEFAULT NULL,
  `created`                 DATETIME     NOT NULL,
  `modified`                DATETIME     DEFAULT NULL,
  INDEX `idx_status`        (`status`),
  INDEX `idx_q_overall`     (`q_overall`)   -- discovery sort key — the ONLY sort index
  -- NO INDEX on submitted_at, acceptance_sealed_at, publication_sealed_at
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 2. eaiou_versions
-- Per-paper file version lineage. AI-generated versions flagged.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_versions` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`        INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `label`           VARCHAR(100) NOT NULL,
  `file_path`       VARCHAR(500) DEFAULT NULL,
  `content_hash`    VARCHAR(64)  DEFAULT NULL,
  `ai_flag`         TINYINT      NOT NULL DEFAULT 0,
  `ai_model_name`   VARCHAR(255) DEFAULT NULL,
  `generated_at`    DATETIME     DEFAULT NULL,
  `notes`           TEXT         DEFAULT NULL,
  `state`           TINYINT      NOT NULL DEFAULT 1,
  `created`         DATETIME     NOT NULL,
  `modified`        DATETIME     DEFAULT NULL,
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_ai_flag`  (`ai_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 3. eaiou_ai_sessions
-- Per-paper AI usage logs. Answer Box fields are SAID primitives.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_ai_sessions` (
  `id`                         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`                   INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `session_label`              VARCHAR(255) DEFAULT NULL,
  `ai_model_name`              VARCHAR(255) NOT NULL,
  `start_time`                 DATETIME     DEFAULT NULL,
  `end_time`                   DATETIME     DEFAULT NULL,
  `tokens_in`                  INT          DEFAULT NULL,
  `tokens_out`                 INT          DEFAULT NULL,
  `redaction_status`           ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  `session_notes`              TEXT         DEFAULT NULL,
  `session_hash`               VARCHAR(64)  DEFAULT NULL,
  `answer_box_session_id`      VARCHAR(255) DEFAULT NULL COMMENT 'SAID: Answer Box session receipt ID',
  `answer_box_ledger_capstone` VARCHAR(255) DEFAULT NULL COMMENT 'SAID: ledger capstone for this session',
  `state`                      TINYINT      NOT NULL DEFAULT 1,
  `created`                    DATETIME     NOT NULL,
  `modified`                   DATETIME     DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_model`       (`ai_model_name`),
  INDEX `idx_redaction`   (`redaction_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 4. eaiou_didntmakeit
-- Excluded AI outputs. Never hard-deleted. Part of the record.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_didntmakeit` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id`       INT NOT NULL COMMENT 'fk eaiou_ai_sessions.id',
  `prompt_text`      LONGTEXT     DEFAULT NULL,
  `response_text`    LONGTEXT     DEFAULT NULL,
  `exclusion_reason` TEXT         DEFAULT NULL,
  `redacted`         TINYINT      NOT NULL DEFAULT 0,
  `redaction_hash`   VARCHAR(64)  DEFAULT NULL,
  `state`            TINYINT      NOT NULL DEFAULT 1,
  `created`          DATETIME     NOT NULL,
  `modified`         DATETIME     DEFAULT NULL,
  INDEX `idx_session_id` (`session_id`),
  INDEX `idx_redacted`   (`redacted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 5. eaiou_remsearch
-- Literature triage. Used AND unused sources preserved.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_remsearch` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`         INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `citation_title`   VARCHAR(500) DEFAULT NULL,
  `citation_source`  VARCHAR(255) DEFAULT NULL,
  `citation_link`    VARCHAR(1000) DEFAULT NULL,
  `source_type`      ENUM('journal','preprint','book','dataset','code','other') DEFAULT 'journal',
  `used`             TINYINT      NOT NULL DEFAULT 0,
  `reason_unused`    TEXT         DEFAULT NULL,
  `fulltext_notes`   TEXT         DEFAULT NULL,
  `state`            TINYINT      NOT NULL DEFAULT 1,
  `created`          DATETIME     NOT NULL,
  `modified`         DATETIME     DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_used`        (`used`),
  INDEX `idx_source_type` (`source_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 6. eaiou_review_logs
-- Rubric-based peer review. Six dimensions (0–10 each).
-- q_transparency weighted 1.5x — AI disclosure quality is privileged.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_review_logs` (
  `id`                   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`             INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `reviewer_intellid`    CHAR(36)     DEFAULT NULL COMMENT 'fk intellid_registry.intellid',
  `version_reviewed`     VARCHAR(100) DEFAULT NULL,
  `review_date`          DATETIME     DEFAULT NULL,
  `rubric_overall`       TINYINT      DEFAULT NULL CHECK (`rubric_overall` BETWEEN 0 AND 10),
  `rubric_originality`   TINYINT      DEFAULT NULL CHECK (`rubric_originality` BETWEEN 0 AND 10),
  `rubric_methodology`   TINYINT      DEFAULT NULL CHECK (`rubric_methodology` BETWEEN 0 AND 10),
  `rubric_transparency`  TINYINT      DEFAULT NULL CHECK (`rubric_transparency` BETWEEN 0 AND 10),
  `rubric_ai_disclosure` TINYINT      DEFAULT NULL CHECK (`rubric_ai_disclosure` BETWEEN 0 AND 10),
  `rubric_crossdomain`   TINYINT      DEFAULT NULL CHECK (`rubric_crossdomain` BETWEEN 0 AND 10),
  `recommendation`       ENUM('accept','minor','major','reject','abstain') DEFAULT NULL,
  `review_notes`         LONGTEXT     DEFAULT NULL,
  `labels_json`          JSON         DEFAULT NULL,
  `unsci_flagged`        TINYINT      NOT NULL DEFAULT 0,
  `open_consent`         TINYINT      NOT NULL DEFAULT 0,
  `state`                TINYINT      NOT NULL DEFAULT 1,
  `created`              DATETIME     NOT NULL,
  `modified`             DATETIME     DEFAULT NULL,
  INDEX `idx_paper_id`       (`paper_id`),
  INDEX `idx_reviewer`       (`reviewer_intellid`),
  INDEX `idx_recommendation` (`recommendation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 7. eaiou_quality_signals
-- Computed Q scores per review event.
-- q_signal is the sole discovery sort key.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_quality_signals` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`        INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `review_log_id`   INT          DEFAULT NULL COMMENT 'fk eaiou_review_logs.id',
  `q_overall`       DECIMAL(5,3) DEFAULT NULL,
  `q_originality`   DECIMAL(5,3) DEFAULT NULL,
  `q_methodology`   DECIMAL(5,3) DEFAULT NULL,
  `q_transparency`  DECIMAL(5,3) DEFAULT NULL COMMENT 'weighted 1.5x in q_signal',
  `q_ai_disclosure` DECIMAL(5,3) DEFAULT NULL,
  `q_crossdomain`   DECIMAL(5,3) DEFAULT NULL,
  `q_signal`        DECIMAL(7,4) DEFAULT NULL COMMENT 'composite discovery sort key',
  `weight_override` JSON         DEFAULT NULL,
  `computed_at`     DATETIME     DEFAULT NULL,
  `state`           TINYINT      NOT NULL DEFAULT 1,
  `created`         DATETIME     NOT NULL,
  `modified`        DATETIME     DEFAULT NULL,
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_q_signal` (`q_signal`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 8. eaiou_intellid_registry  (Migration 002)
-- One row per contributing intelligence instance.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_intellid_registry` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `intellid`        CHAR(36)     NOT NULL UNIQUE COMMENT 'eaiou-minted UUID, opaque',
  `type`            ENUM('human','ai','hybrid','institutional','system') NOT NULL,
  `origin`          ENUM('orcid','model','mcp','api','manual','unknown') NOT NULL DEFAULT 'unknown',
  `model_family`    VARCHAR(255) DEFAULT NULL COMMENT 'claude, gpt-4, etc. Disclosed, not provider-specific.',
  `instance_hash`   VARCHAR(64)  DEFAULT NULL COMMENT 'SHA256 of session-specific context. Sealed.',
  `connector`       ENUM('mcp','api','direct','manual','system') DEFAULT NULL,
  `cosmoid_context` CHAR(36)     DEFAULT NULL COMMENT 'CosmoID of the paper this IntelliD was active in',
  `scope_paper_id`  INT          DEFAULT NULL COMMENT 'NULL = cross-paper identity',
  `public_type`     TINYINT      NOT NULL DEFAULT 1 COMMENT '1=type disclosed, 0=sealed',
  `state`           TINYINT      NOT NULL DEFAULT 1,
  `created`         DATETIME     NOT NULL,
  INDEX `idx_intellid`  (`intellid`),
  INDEX `idx_type`      (`type`),
  INDEX `idx_scope`     (`scope_paper_id`),
  INDEX `idx_cosmoid`   (`cosmoid_context`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 9. eaiou_intellid_contributions  (Migration 002)
-- Attribution graph: (intellid, artifact, relation) edges.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_intellid_contributions` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `intellid`      CHAR(36)     NOT NULL COMMENT 'fk intellid_registry.intellid',
  `artifact_type` ENUM('paper','version','ai_session','remsearch','review','dataset','claim') NOT NULL,
  `artifact_id`   INT          DEFAULT NULL,
  `artifact_uuid` CHAR(36)     DEFAULT NULL,
  `cosmoid`       CHAR(36)     DEFAULT NULL,
  `relation`      ENUM('generated','edited','validated','rejected','reviewed','cited','derived','proposed','refuted') NOT NULL,
  `weight`        DECIMAL(5,3) DEFAULT NULL,
  `confidence`    DECIMAL(5,3) DEFAULT NULL,
  `notes`         TEXT         DEFAULT NULL,
  `state`         TINYINT      NOT NULL DEFAULT 1,
  `created`       DATETIME     NOT NULL,
  INDEX `idx_intellid`  (`intellid`),
  INDEX `idx_artifact`  (`artifact_type`, `artifact_id`),
  INDEX `idx_cosmoid`   (`cosmoid`),
  INDEX `idx_relation`  (`relation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 10. eaiou_observation_log  (Migration 002)
-- UHA layer — only populated if an observation event is recorded.
-- NO INDEX on observation_at — Temporal Blindness applies to
-- observation timing too.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_observation_log` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `observed_cosmoid`  CHAR(36)     NOT NULL COMMENT 'CosmoID of the artifact observed',
  `observer_intellid` CHAR(36)     DEFAULT NULL COMMENT 'IntelliD of the observer, if known',
  `observation_type`  ENUM('read','cite','fork','contact','validate','replicate') NOT NULL DEFAULT 'read',
  `uha_address`       VARCHAR(500) DEFAULT NULL COMMENT 'UHA-encoded observation address',
  `uha_cosmoid`       CHAR(36)     DEFAULT NULL COMMENT 'CosmoID under which UHA was computed',
  `observation_at`    DATETIME     NOT NULL,
  -- NO INDEX on observation_at — timing side-channel prevention
  INDEX `idx_observed_cosmoid`  (`observed_cosmoid`),
  INDEX `idx_observer_intellid` (`observer_intellid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 11. eaiou_attribution_log
-- Human and AI contributor history per paper.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_attribution_log` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT NOT NULL,
  `contributor_name`  VARCHAR(255) NOT NULL,
  `orcid`             VARCHAR(50)  DEFAULT NULL,
  `role_description`  VARCHAR(500) DEFAULT NULL,
  `contribution_type` VARCHAR(100) DEFAULT NULL,
  `is_human`          TINYINT      NOT NULL DEFAULT 1,
  `is_ai`             TINYINT      NOT NULL DEFAULT 0,
  `ai_tool_used`      VARCHAR(255) DEFAULT NULL,
  `version_id`        INT          DEFAULT NULL,
  `state`             TINYINT      NOT NULL DEFAULT 1,
  `created`           DATETIME     NOT NULL,
  `modified`          DATETIME     DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_contributor` (`contributor_name`),
  INDEX `idx_is_ai`       (`is_ai`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 12. eaiou_api_keys
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_api_keys` (
  `id`           INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`      INT NOT NULL,
  `api_key`      VARCHAR(255) NOT NULL UNIQUE,
  `description`  VARCHAR(500) DEFAULT NULL,
  `access_level` ENUM('read','submit','review','admin') NOT NULL DEFAULT 'read',
  `status`       ENUM('active','revoked','suspended') NOT NULL DEFAULT 'active',
  `last_used`    DATETIME     DEFAULT NULL,
  `state`        TINYINT      NOT NULL DEFAULT 1,
  `created`      DATETIME     NOT NULL,
  `modified`     DATETIME     DEFAULT NULL,
  INDEX `idx_user_id`      (`user_id`),
  INDEX `idx_status`       (`status`),
  INDEX `idx_access_level` (`access_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 13. eaiou_api_logs (append-only, hash chain)
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_api_logs` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `api_key_id`     INT NOT NULL,
  `endpoint`       VARCHAR(500) NOT NULL,
  `method`         VARCHAR(10)  DEFAULT NULL,
  `request_data`   JSON         DEFAULT NULL,
  `response_code`  SMALLINT     DEFAULT NULL,
  `log_hash`       VARCHAR(64)  DEFAULT NULL COMMENT 'SHA256 of this record',
  `prior_hash`     VARCHAR(64)  DEFAULT NULL COMMENT 'SHA256 of previous log entry — chain integrity',
  `log_timestamp`  DATETIME     NOT NULL,
  `state`          TINYINT      NOT NULL DEFAULT 1,
  `created`        DATETIME     NOT NULL,
  `modified`       DATETIME     DEFAULT NULL,
  INDEX `idx_api_key_id` (`api_key_id`),
  INDEX `idx_endpoint`   (`endpoint`(100)),
  INDEX `idx_timestamp`  (`log_timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- End of eaiou Python CMS fresh install
-- Temporal Blindness enforced. q_overall is the river.
-- ============================================================
