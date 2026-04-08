-- eaiou Canonical Install Schema
-- Version: 2.0 (2026-04-07)
-- Derived from: SSOT.md v2.0
-- Platform: Joomla 5.3 / MariaDB 10.x
--
-- TEMPORAL BLINDNESS ENFORCEMENT:
-- submission_sealed_at, acceptance_sealed_at, publication_sealed_at
-- carry NO INDEXES by design. Indexing sealed temporal fields creates
-- a timing side-channel that allows bias to infer submission order.
-- q_signal is the ONLY discovery sort key in this system.
-- Do not add indexes to sealed fields. This is not an omission.
--
-- HASH CHAIN:
-- eaiou_api_logs.prior_hash chains each entry to the previous.
-- Breaking the chain is detectable. Append-only by policy.

SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

-- ============================================================
-- 1. eaiou_papers
-- Bridge table: maps Joomla article to archival record.
-- Holds sealed temporal state space.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_papers` (
  `id`                      INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `article_id`              INT NOT NULL COMMENT 'joomla #__content.id',
  `paper_uuid`              CHAR(36) NOT NULL UNIQUE COMMENT 'matches paper_id custom field on article',
  `authorship_mode`         ENUM('human','ai','hybrid') NOT NULL DEFAULT 'human',
  `status`                  VARCHAR(50) NOT NULL DEFAULT 'draft',
  `submission_version`      INT NOT NULL DEFAULT 1,
  `doi`                     VARCHAR(255) DEFAULT NULL,
  `authors_json`            JSON DEFAULT NULL,
  -- SEALED TEMPORAL STATE SPACE — NO INDEXES (timing side-channel prevention)
  `submission_sealed_at`    DATETIME DEFAULT NULL COMMENT 'sealed at submission — never displayed publicly',
  `sealed_by`               INT DEFAULT NULL COMMENT 'user_id who triggered sealing',
  `submission_hash`         VARCHAR(64) DEFAULT NULL COMMENT 'SHA256(paper_uuid+submission_sealed_at+content_hash)',
  `submission_capstone`     VARCHAR(255) DEFAULT NULL COMMENT 'Zenodo DOI — public receipt without revealing timing',
  `acceptance_sealed_at`    DATETIME DEFAULT NULL COMMENT 'sealed at acceptance — never displayed publicly',
  `publication_sealed_at`   DATETIME DEFAULT NULL COMMENT 'sealed at publication — never displayed publicly',
  -- END SEALED FIELDS
  `bundle_path`             VARCHAR(500) DEFAULT NULL,
  `q_signal`                DECIMAL(7,4) DEFAULT NULL COMMENT 'denormalized from eaiou_quality_signals — discovery sort key',
  `state`                   TINYINT NOT NULL DEFAULT 1,
  `access`                  INT NOT NULL DEFAULT 1,
  `ordering`                INT NOT NULL DEFAULT 0,
  `created`                 DATETIME NOT NULL,
  `created_by`              INT NOT NULL,
  `modified`                DATETIME DEFAULT NULL,
  `modified_by`             INT DEFAULT NULL,
  `checked_out`             INT DEFAULT NULL,
  `checked_out_time`        DATETIME DEFAULT NULL,
  INDEX `idx_article_id`    (`article_id`),
  INDEX `idx_status`        (`status`),
  INDEX `idx_q_signal`      (`q_signal`),        -- discovery sort key
  INDEX `idx_authorship`    (`authorship_mode`)
  -- NO INDEX on submission_sealed_at, acceptance_sealed_at, publication_sealed_at
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. eaiou_versions
-- Version lineage per paper. AI-generated versions flagged.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_versions` (
  `id`                      INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`                INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `label`                   VARCHAR(100) NOT NULL,
  `file_path`               VARCHAR(500) DEFAULT NULL,
  `content_hash`            VARCHAR(64) DEFAULT NULL,
  `ai_flag`                 TINYINT NOT NULL DEFAULT 0,
  `ai_model_name`           VARCHAR(255) DEFAULT NULL,
  `generated_at`            DATETIME DEFAULT NULL,
  `notes`                   TEXT DEFAULT NULL,
  `state`                   TINYINT NOT NULL DEFAULT 1,
  `access`                  INT NOT NULL DEFAULT 1,
  `ordering`                INT NOT NULL DEFAULT 0,
  `created`                 DATETIME NOT NULL,
  `created_by`              INT NOT NULL,
  `modified`                DATETIME DEFAULT NULL,
  `modified_by`             INT DEFAULT NULL,
  `checked_out`             INT DEFAULT NULL,
  `checked_out_time`        DATETIME DEFAULT NULL,
  INDEX `idx_paper_id`      (`paper_id`),
  INDEX `idx_ai_flag`       (`ai_flag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. eaiou_ai_sessions
-- Per-paper AI usage logs. Session-level traceability.
-- answer_box fields link AI decision receipts to paper records (SAID primitive).
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_ai_sessions` (
  `id`                          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`                    INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `session_label`               VARCHAR(255) DEFAULT NULL,
  `ai_model_name`               VARCHAR(255) NOT NULL,
  `start_time`                  DATETIME DEFAULT NULL,
  `end_time`                    DATETIME DEFAULT NULL,
  `tokens_in`                   INT DEFAULT NULL,
  `tokens_out`                  INT DEFAULT NULL,
  `redaction_status`            ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  `session_notes`               TEXT DEFAULT NULL,
  `session_hash`                VARCHAR(64) DEFAULT NULL,
  `answer_box_session_id`       VARCHAR(255) DEFAULT NULL COMMENT 'SAID: Answer Box session receipt ID',
  `answer_box_ledger_capstone`  VARCHAR(255) DEFAULT NULL COMMENT 'SAID: ledger capstone for this session',
  `state`                       TINYINT NOT NULL DEFAULT 1,
  `access`                      INT NOT NULL DEFAULT 1,
  `ordering`                    INT NOT NULL DEFAULT 0,
  `created`                     DATETIME NOT NULL,
  `created_by`                  INT NOT NULL,
  `modified`                    DATETIME DEFAULT NULL,
  `modified_by`                 INT DEFAULT NULL,
  `checked_out`                 INT DEFAULT NULL,
  `checked_out_time`            DATETIME DEFAULT NULL,
  INDEX `idx_paper_id`          (`paper_id`),
  INDEX `idx_model`             (`ai_model_name`),
  INDEX `idx_redaction`         (`redaction_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. eaiou_didntmakeit
-- Excluded AI outputs. Never hard-deleted. Preserved for archival.
-- "What didn't make it" is part of the research record.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_didntmakeit` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id`        INT NOT NULL COMMENT 'fk eaiou_ai_sessions.id',
  `prompt_text`       LONGTEXT DEFAULT NULL,
  `response_text`     LONGTEXT DEFAULT NULL,
  `exclusion_reason`  TEXT DEFAULT NULL,
  `redacted`          TINYINT NOT NULL DEFAULT 0,
  `redaction_hash`    VARCHAR(64) DEFAULT NULL,
  `state`             TINYINT NOT NULL DEFAULT 1,
  `access`            INT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT NOT NULL,
  `modified`          DATETIME DEFAULT NULL,
  `modified_by`       INT DEFAULT NULL,
  `checked_out`       INT DEFAULT NULL,
  `checked_out_time`  DATETIME DEFAULT NULL,
  INDEX `idx_session_id` (`session_id`),
  INDEX `idx_redacted`   (`redacted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. eaiou_remsearch
-- Literature triage. Used AND unused sources preserved.
-- What was considered but not used is part of the research record.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_remsearch` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `citation_title`    VARCHAR(500) DEFAULT NULL,
  `citation_source`   VARCHAR(255) DEFAULT NULL,
  `citation_link`     VARCHAR(1000) DEFAULT NULL,
  `source_type`       ENUM('journal','preprint','book','dataset','code','other') DEFAULT 'journal',
  `used`              TINYINT NOT NULL DEFAULT 0,
  `reason_unused`     TEXT DEFAULT NULL,
  `fulltext_notes`    TEXT DEFAULT NULL,
  `state`             TINYINT NOT NULL DEFAULT 1,
  `access`            INT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT NOT NULL,
  `modified`          DATETIME DEFAULT NULL,
  `modified_by`       INT DEFAULT NULL,
  `checked_out`       INT DEFAULT NULL,
  `checked_out_time`  DATETIME DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_used`        (`used`),
  INDEX `idx_source_type` (`source_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. eaiou_review_logs
-- Rubric-based peer review records. Six dimensions.
-- Feeds eaiou_quality_signals for q_signal computation.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_review_logs` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`              INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `reviewer_id`           INT NOT NULL COMMENT 'joomla user_id',
  `version_reviewed`      VARCHAR(100) DEFAULT NULL,
  `review_date`           DATETIME DEFAULT NULL,
  `rubric_overall`        TINYINT DEFAULT NULL CHECK (`rubric_overall` BETWEEN 0 AND 10),
  `rubric_originality`    TINYINT DEFAULT NULL CHECK (`rubric_originality` BETWEEN 0 AND 10),
  `rubric_methodology`    TINYINT DEFAULT NULL CHECK (`rubric_methodology` BETWEEN 0 AND 10),
  `rubric_transparency`   TINYINT DEFAULT NULL CHECK (`rubric_transparency` BETWEEN 0 AND 10),
  `rubric_ai_disclosure`  TINYINT DEFAULT NULL CHECK (`rubric_ai_disclosure` BETWEEN 0 AND 10),
  `rubric_crossdomain`    TINYINT DEFAULT NULL CHECK (`rubric_crossdomain` BETWEEN 0 AND 10),
  `recommendation`        ENUM('accept','minor','major','reject','abstain') DEFAULT NULL,
  `review_notes`          LONGTEXT DEFAULT NULL,
  `labels_json`           JSON DEFAULT NULL,
  `unsci_flagged`         TINYINT NOT NULL DEFAULT 0,
  `open_consent`          TINYINT NOT NULL DEFAULT 0,
  `state`                 TINYINT NOT NULL DEFAULT 1,
  `access`                INT NOT NULL DEFAULT 1,
  `ordering`              INT NOT NULL DEFAULT 0,
  `created`               DATETIME NOT NULL,
  `created_by`            INT NOT NULL,
  `modified`              DATETIME DEFAULT NULL,
  `modified_by`           INT DEFAULT NULL,
  `checked_out`           INT DEFAULT NULL,
  `checked_out_time`      DATETIME DEFAULT NULL,
  INDEX `idx_paper_id`      (`paper_id`),
  INDEX `idx_reviewer_id`   (`reviewer_id`),
  INDEX `idx_recommendation` (`recommendation`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. eaiou_attribution_log
-- Contribution history. Human and AI contributors named.
-- Principle: treat things that can talk like humanity.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_attribution_log` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `contributor_name`  VARCHAR(255) NOT NULL,
  `orcid`             VARCHAR(50) DEFAULT NULL,
  `role_description`  VARCHAR(500) DEFAULT NULL,
  `contribution_type` VARCHAR(100) DEFAULT NULL,
  `is_human`          TINYINT NOT NULL DEFAULT 1,
  `is_ai`             TINYINT NOT NULL DEFAULT 0,
  `ai_tool_used`      VARCHAR(255) DEFAULT NULL,
  `version_id`        INT DEFAULT NULL COMMENT 'fk eaiou_versions.id (optional)',
  `state`             TINYINT NOT NULL DEFAULT 1,
  `access`            INT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT NOT NULL,
  `modified`          DATETIME DEFAULT NULL,
  `modified_by`       INT DEFAULT NULL,
  `checked_out`       INT DEFAULT NULL,
  `checked_out_time`  DATETIME DEFAULT NULL,
  INDEX `idx_paper_id`      (`paper_id`),
  INDEX `idx_contributor`   (`contributor_name`),
  INDEX `idx_is_ai`         (`is_ai`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 8. eaiou_plugins_used
-- Tool and plugin execution audit per paper.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_plugins_used` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`            INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `plugin_name`         VARCHAR(255) NOT NULL,
  `plugin_type`         VARCHAR(100) DEFAULT NULL,
  `execution_context`   VARCHAR(255) DEFAULT NULL,
  `exec_log_path`       VARCHAR(500) DEFAULT NULL,
  `exec_timestamp`      DATETIME DEFAULT NULL,
  `state`               TINYINT NOT NULL DEFAULT 1,
  `access`              INT NOT NULL DEFAULT 1,
  `ordering`            INT NOT NULL DEFAULT 0,
  `created`             DATETIME NOT NULL,
  `created_by`          INT NOT NULL,
  `modified`            DATETIME DEFAULT NULL,
  `modified_by`         INT DEFAULT NULL,
  `checked_out`         INT DEFAULT NULL,
  `checked_out_time`    DATETIME DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_plugin_name` (`plugin_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 9. eaiou_api_keys
-- API access registry. Keys scoped by access_level.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_api_keys` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`       INT NOT NULL COMMENT 'joomla user_id',
  `api_key`       VARCHAR(255) NOT NULL UNIQUE,
  `description`   VARCHAR(500) DEFAULT NULL,
  `access_level`  ENUM('read','submit','review','admin') NOT NULL DEFAULT 'read',
  `status`        ENUM('active','revoked','suspended') NOT NULL DEFAULT 'active',
  `last_used`     DATETIME DEFAULT NULL,
  `state`         TINYINT NOT NULL DEFAULT 1,
  `access`        INT NOT NULL DEFAULT 1,
  `ordering`      INT NOT NULL DEFAULT 0,
  `created`       DATETIME NOT NULL,
  `created_by`    INT NOT NULL,
  `modified`      DATETIME DEFAULT NULL,
  `modified_by`   INT DEFAULT NULL,
  `checked_out`   INT DEFAULT NULL,
  `checked_out_time` DATETIME DEFAULT NULL,
  INDEX `idx_user_id`      (`user_id`),
  INDEX `idx_status`       (`status`),
  INDEX `idx_access_level` (`access_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 10. eaiou_api_logs
-- Append-only API call audit with hash chain.
-- log_hash = SHA256 of this record's content.
-- prior_hash = log_hash of the previous entry.
-- Breaking the chain is detectable.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_api_logs` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `api_key_id`      INT NOT NULL COMMENT 'fk eaiou_api_keys.id',
  `endpoint`        VARCHAR(500) NOT NULL,
  `method`          VARCHAR(10) DEFAULT NULL,
  `request_data`    JSON DEFAULT NULL,
  `response_code`   SMALLINT DEFAULT NULL,
  `log_hash`        VARCHAR(64) DEFAULT NULL COMMENT 'SHA256 of this record — tamper detection',
  `prior_hash`      VARCHAR(64) DEFAULT NULL COMMENT 'SHA256 of previous log entry — chain integrity',
  `log_timestamp`   DATETIME NOT NULL,
  `state`           TINYINT NOT NULL DEFAULT 1,
  `access`          INT NOT NULL DEFAULT 1,
  `ordering`        INT NOT NULL DEFAULT 0,
  `created`         DATETIME NOT NULL,
  `created_by`      INT NOT NULL,
  `modified`        DATETIME DEFAULT NULL,
  `modified_by`     INT DEFAULT NULL,
  `checked_out`     INT DEFAULT NULL,
  `checked_out_time` DATETIME DEFAULT NULL,
  INDEX `idx_api_key_id`  (`api_key_id`),
  INDEX `idx_endpoint`    (`endpoint`(100)),
  INDEX `idx_timestamp`   (`log_timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 11. eaiou_quality_signals
-- One record per review event. Source of q_signal computation.
-- q_transparency weighted 1.5x: AI disclosure quality is privileged.
-- q_signal is indexed — it is the sole discovery sort key.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_quality_signals` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT NOT NULL COMMENT 'fk eaiou_papers.id',
  `review_log_id`     INT DEFAULT NULL COMMENT 'fk eaiou_review_logs.id',
  `q_overall`         DECIMAL(5,3) DEFAULT NULL,
  `q_originality`     DECIMAL(5,3) DEFAULT NULL,
  `q_methodology`     DECIMAL(5,3) DEFAULT NULL,
  `q_transparency`    DECIMAL(5,3) DEFAULT NULL COMMENT 'weighted 1.5x in q_signal — AI disclosure quality is privileged',
  `q_ai_disclosure`   DECIMAL(5,3) DEFAULT NULL,
  `q_crossdomain`     DECIMAL(5,3) DEFAULT NULL,
  `q_signal`          DECIMAL(7,4) DEFAULT NULL COMMENT 'computed composite — the discovery sort key',
  `weight_override`   JSON DEFAULT NULL COMMENT 'per-computation weight overrides if any',
  `computed_at`       DATETIME DEFAULT NULL,
  `state`             TINYINT NOT NULL DEFAULT 1,
  `access`            INT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT NOT NULL,
  `modified`          DATETIME DEFAULT NULL,
  `modified_by`       INT DEFAULT NULL,
  `checked_out`       INT DEFAULT NULL,
  `checked_out_time`  DATETIME DEFAULT NULL,
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_q_signal` (`q_signal`)  -- discovery sort key
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- End of canonical schema — eaiou v2.0
-- Temporal Blindness enforced. q_signal is the river.
