-- migration_005_canonical_tables.sql
-- eaiou — 10 canonical archival tables + Temporal Blindness sealed fields on papers
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742
-- Date: 2026-04-12
--
-- TEMPORAL BLINDNESS ENFORCEMENT:
-- submission_sealed_at, acceptance_sealed_at, publication_sealed_at,
-- log_hash, prior_hash (api_logs), submitted_at (review_logs)
-- carry NO INDEXES by design. Indexing these fields creates a timing
-- side-channel that allows bias to infer submission/review order.
-- q_signal is the ONLY discovery sort key in this system.
-- This is not an omission. This is doctrine.
--
-- All statements are idempotent (CREATE TABLE IF NOT EXISTS,
-- ADD COLUMN IF NOT EXISTS). Safe to run on every start.

SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

-- ============================================================
-- 1. eaiou_versions
-- Version lineage per paper. AI-generated versions flagged.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_versions` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `label`             VARCHAR(128) NOT NULL DEFAULT '',
  `file_path`         VARCHAR(512) DEFAULT NULL,
  `content_hash`      CHAR(64) DEFAULT NULL COMMENT 'SHA256 of version file at upload.',
  `ai_flag`           TINYINT(1) NOT NULL DEFAULT 0,
  `ai_model_name`     VARCHAR(128) DEFAULT NULL,
  `generated_at`      DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `notes`             TEXT,
  `state`             TINYINT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`       INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`       INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time`  DATETIME NULL DEFAULT NULL,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_ai_flag`     (`ai_flag`),
  INDEX `idx_state_paper` (`state`, `paper_id`)
  -- No index on generated_at — timing side-channel prevention.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. eaiou_ai_sessions
-- Per-paper AI usage audit. Session-level traceability.
-- answer_box fields link AI decision receipts (SAID primitive).
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_ai_sessions` (
  `id`                          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`                    INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `session_label`               VARCHAR(256) NOT NULL DEFAULT '',
  `ai_model_name`               VARCHAR(128) NOT NULL DEFAULT '',
  `ai_model_version`            VARCHAR(64) DEFAULT NULL,
  `answer_box_session_id`       CHAR(36) NULL DEFAULT NULL COMMENT 'UUID from AnswerBox init. Sealed before ledger opens. Immutable.',
  `answer_box_ledger_capstone`  VARCHAR(256) NULL DEFAULT NULL COMMENT 'Zenodo DOI anchoring the Answer Box ledger block.',
  `tokens_in`                   INT UNSIGNED NOT NULL DEFAULT 0,
  `tokens_out`                  INT UNSIGNED NOT NULL DEFAULT 0,
  `redaction_status`            ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  `redaction_reason`            TEXT,
  `session_notes`               TEXT,
  `session_hash`                CHAR(64) NULL DEFAULT NULL COMMENT 'SHA256(session_id+paper_id+model+tokens+end_time). Immutable after close.',
  `start_sealed_at`             DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `end_sealed_at`               DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only. Null = still open.',
  `state`                       TINYINT NOT NULL DEFAULT 1,
  `ordering`                    INT NOT NULL DEFAULT 0,
  `created`                     DATETIME NOT NULL,
  `created_by`                  INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`                    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`                 INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`                 INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time`            DATETIME NULL DEFAULT NULL,
  INDEX `idx_paper_id`          (`paper_id`),
  INDEX `idx_model_state`       (`ai_model_name`(64), `state`),
  INDEX `idx_redaction`         (`redaction_status`),
  INDEX `idx_answer_box_session`(`answer_box_session_id`)
  -- No index on start_sealed_at or end_sealed_at — timing side-channel prevention.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. eaiou_didntmakeit
-- Excluded AI outputs. Never hard-deleted. Preserved for archival.
-- "What didn't make it" is part of the research record.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_didntmakeit` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `session_id`            INT UNSIGNED NOT NULL COMMENT 'fk eaiou_ai_sessions.id',
  `paper_id`              INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `prompt_hash`           CHAR(64) NOT NULL COMMENT 'SHA256 of the prompt. Always stored.',
  `prompt_text`           MEDIUMTEXT COMMENT 'Raw prompt. May be NULL if redacted.',
  `response_hash`         CHAR(64) NULL DEFAULT NULL,
  `response_text`         MEDIUMTEXT COMMENT 'Raw response. May be NULL if redacted.',
  `exclusion_reason`      TEXT COMMENT 'Why this output was not used.',
  `redacted`              TINYINT(1) NOT NULL DEFAULT 0,
  `redaction_hash`        CHAR(64) NULL DEFAULT NULL COMMENT 'Hash of redacted content for integrity proof.',
  `redaction_status`      ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  `interaction_sealed_at` DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `state`                 TINYINT NOT NULL DEFAULT 1,
  `ordering`              INT NOT NULL DEFAULT 0,
  `created`               DATETIME NOT NULL,
  `created_by`            INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`           INT UNSIGNED NOT NULL DEFAULT 0,
  INDEX `idx_session_id` (`session_id`),
  INDEX `idx_paper_id`   (`paper_id`),
  INDEX `idx_redacted`   (`redacted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. eaiou_remsearch
-- Literature triage. Used AND unused sources preserved.
-- What was considered but not used is part of the research record.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_remsearch` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `citation_title`    VARCHAR(512) NOT NULL DEFAULT '',
  `citation_source`   VARCHAR(256) DEFAULT NULL,
  `citation_doi`      VARCHAR(256) DEFAULT NULL,
  `citation_link`     VARCHAR(512) DEFAULT NULL,
  `source_type`       ENUM('journal','preprint','dataset','code','book','conference','patent','other') NOT NULL DEFAULT 'journal',
  `used`              TINYINT(1) NOT NULL DEFAULT 0,
  `reason_unused`     TEXT COMMENT 'Required when used=0 and state=published.',
  `cross_domain_flag` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Flagged as potentially relevant in another domain.',
  `fulltext_notes`    TEXT,
  `triaged_at`        DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `state`             TINYINT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`       INT UNSIGNED NOT NULL DEFAULT 0,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_used`        (`used`),
  INDEX `idx_source_type` (`source_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. eaiou_review_logs
-- Rubric-based peer review records. Six quality dimensions.
-- Feeds eaiou_quality_signals for q_signal computation.
-- CRITICAL: submitted_at / review_sealed_at carry NO INDEX.
-- Discovery sort uses rubric scores, not review timing.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_review_logs` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`              INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `reviewer_user_id`      INT UNSIGNED NOT NULL DEFAULT 0,
  `version_reviewed`      VARCHAR(128) DEFAULT NULL,
  `reviewer_displayname`  VARCHAR(256) DEFAULT NULL COMMENT 'NULL = anonymized.',
  `identity_mode`         ENUM('open','anonymous') NOT NULL DEFAULT 'anonymous',
  `consent_display`       TINYINT(1) NOT NULL DEFAULT 0,
  `rubric_overall`        TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0-10.',
  `rubric_originality`    TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0-10.',
  `rubric_methodology`    TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0-10.',
  `rubric_transparency`   TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0-10. Weighted 1.5x for eaiou doctrine.',
  `rubric_ai_disclosure`  TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0-10. Required when ai_flag=1.',
  `rubric_cross_domain`   TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '0-10.',
  `recommendation`        ENUM('accept','minor_revisions','major_revisions','reject','refer') NULL DEFAULT NULL,
  `labels_json`           JSON DEFAULT NULL,
  `review_notes`          MEDIUMTEXT,
  `attachments_json`      JSON DEFAULT NULL,
  `author_response`       MEDIUMTEXT,
  `review_sealed_at`      DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only. Never public.',
  `review_hash`           CHAR(64) NULL DEFAULT NULL COMMENT 'SHA256(review_id+paper_id+reviewer_id+rubrics+review_sealed_at).',
  `state`                 TINYINT NOT NULL DEFAULT 1,
  `ordering`              INT NOT NULL DEFAULT 0,
  `created`               DATETIME NOT NULL,
  `created_by`            INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`              DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`           INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`           INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time`      DATETIME NULL DEFAULT NULL,
  INDEX `idx_paper_id`      (`paper_id`),
  INDEX `idx_reviewer`      (`reviewer_user_id`),
  INDEX `idx_state_paper`   (`state`, `paper_id`)
  -- NO INDEX on review_sealed_at or submitted_at — timing side-channel prevention.
  -- Discovery sort uses rubric_overall, not any temporal field.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. eaiou_attribution_log
-- Contributor history. Human and AI contributors named.
-- Principle: treat things that can talk like humanity.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_attribution_log` (
  `id`                     INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`               INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `contributor_name`       VARCHAR(256) NOT NULL DEFAULT '',
  `contributor_orcid`      VARCHAR(64) DEFAULT NULL,
  `contributor_type`       ENUM('human','ai','hybrid') NOT NULL DEFAULT 'human',
  `role_description`       VARCHAR(512) NOT NULL DEFAULT '',
  `contribution_type`      ENUM(
                             'conceptualization','methodology','software','validation',
                             'formal_analysis','investigation','data_curation',
                             'writing_original','writing_review','visualization',
                             'supervision','project_admin','funding','ai_assistance','other'
                           ) NOT NULL DEFAULT 'other',
  `ai_tool_used`           VARCHAR(128) DEFAULT NULL COMMENT 'AI tool name if contributor_type = ai or hybrid.',
  `scope_notes`            TEXT,
  `contribution_sealed_at` DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `state`                  TINYINT NOT NULL DEFAULT 1,
  `ordering`               INT NOT NULL DEFAULT 0,
  `created`                DATETIME NOT NULL,
  `created_by`             INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`               DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`            INT UNSIGNED NOT NULL DEFAULT 0,
  INDEX `idx_paper_id`         (`paper_id`),
  INDEX `idx_contributor_type` (`contributor_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. eaiou_plugins_used
-- Plugin/tool execution audit per paper.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_plugins_used` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `plugin_name`       VARCHAR(256) NOT NULL DEFAULT '',
  `plugin_type`       ENUM('analysis','visualization','transformation','validation','ai_bridge','export','other') NOT NULL DEFAULT 'other',
  `plugin_version`    VARCHAR(64) DEFAULT NULL,
  `execution_context` VARCHAR(256) DEFAULT NULL,
  `exec_log_path`     VARCHAR(512) DEFAULT NULL,
  `result_hash`       CHAR(64) DEFAULT NULL COMMENT 'Hash of execution output for reproducibility.',
  `executed_at`       DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `state`             TINYINT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT UNSIGNED NOT NULL DEFAULT 0,
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_plugin_name` (`plugin_name`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 8. eaiou_api_keys
-- API access registry. Keys stored hashed only. Raw key never stored.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_api_keys` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`           INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'fk eaiou_users.id',
  `api_key_hash`      CHAR(64) NOT NULL COMMENT 'SHA256 of the raw API key.',
  `description`       VARCHAR(256) DEFAULT NULL,
  `access_level`      ENUM('read','submit','review','admin') NOT NULL DEFAULT 'read',
  `issued_at`         DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  `expires_at`        DATETIME NULL DEFAULT NULL COMMENT 'Governance only. Null = no expiry.',
  `last_used_at`      DATETIME NULL DEFAULT NULL COMMENT 'Updated on use. Governance only.',
  `revoked_at`        DATETIME NULL DEFAULT NULL COMMENT 'Set when key is revoked. Immutable once set.',
  `revocation_reason` TEXT,
  `state`             TINYINT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `modified_by`       INT UNSIGNED NOT NULL DEFAULT 0,
  UNIQUE KEY `uq_api_key_hash` (`api_key_hash`),
  INDEX `idx_user_id`    (`user_id`),
  INDEX `idx_state`      (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 9. eaiou_api_logs
-- Append-only API call audit with hash chain.
-- log_hash = SHA256 of this record's content.
-- prior_hash = log_hash of the previous entry.
-- Breaking the chain is detectable. Append-only by policy.
-- CRITICAL: log_hash and prior_hash carry NO INDEX.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_api_logs` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `api_key_id`       INT UNSIGNED NULL DEFAULT NULL COMMENT 'fk eaiou_api_keys.id',
  `user_id`          INT UNSIGNED NULL DEFAULT NULL,
  `endpoint`         VARCHAR(512) NOT NULL DEFAULT '',
  `method`           ENUM('GET','POST','PUT','PATCH','DELETE') NOT NULL DEFAULT 'GET',
  `request_hash`     CHAR(64) NULL DEFAULT NULL COMMENT 'SHA256 of request payload. Full payload not stored by default.',
  `response_code`    SMALLINT UNSIGNED NOT NULL DEFAULT 200,
  `response_summary` VARCHAR(512) DEFAULT NULL,
  `request_at`       DATETIME NOT NULL COMMENT 'Immutable. Set once on insert.',
  `log_hash`         CHAR(64) NULL DEFAULT NULL COMMENT 'SHA256(log_id+api_key_id+endpoint+request_at). Chain anchor.',
  `prior_hash`       CHAR(64) NULL DEFAULT NULL COMMENT 'Hash of previous log row — tamper detection chain.',
  INDEX `idx_api_key_id` (`api_key_id`),
  INDEX `idx_user_id`    (`user_id`)
  -- NO INDEX on log_hash, prior_hash, or request_at — timing side-channel prevention.
  -- API logs are scanned by governance queries only.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 10. eaiou_quality_signals
-- Computed quality signal per paper.
-- This is the NON-temporal discovery ranking surface.
-- Public queries ORDER BY q_signal DESC — never by any date.
-- q_signal IS indexed — it is the sole discovery sort key.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_quality_signals` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT UNSIGNED NOT NULL COMMENT 'fk eaiou_papers.id',
  `q_overall`         DECIMAL(5,3) NOT NULL DEFAULT 0.000 COMMENT 'Weighted average of rubric_overall across all accepted reviews.',
  `q_originality`     DECIMAL(5,3) NOT NULL DEFAULT 0.000,
  `q_methodology`     DECIMAL(5,3) NOT NULL DEFAULT 0.000,
  `q_transparency`    DECIMAL(5,3) NOT NULL DEFAULT 0.000 COMMENT 'Weighted 1.5x in eaiou doctrine. Transparency is a first-class value.',
  `q_cross_domain`    DECIMAL(5,3) NOT NULL DEFAULT 0.000 COMMENT 'Cross-domain applicability signal.',
  `q_ai_disclosure`   DECIMAL(5,3) NOT NULL DEFAULT 0.000,
  `q_signal`          DECIMAL(7,4) NOT NULL DEFAULT 0.0000 COMMENT 'Composite discovery signal. Order by this, never by date.',
  `review_count`      SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `signal_version`    SMALLINT UNSIGNED NOT NULL DEFAULT 1 COMMENT 'Incremented each time signal is recomputed.',
  `last_computed_at`  DATETIME NULL DEFAULT NULL COMMENT 'SEALED: governance only.',
  UNIQUE KEY `uq_paper_id` (`paper_id`),
  INDEX `idx_q_signal` (`q_signal`)
  -- q_signal IS indexed — it is the discovery sort key.
  -- Dates are not indexed. Quality is the surface.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- ALTER #__eaiou_papers: add 5 Temporal Blindness sealed fields
-- All ADD COLUMN IF NOT EXISTS — fully idempotent.
-- CRITICAL: NO INDEX on any of these columns.
-- ============================================================
ALTER TABLE `#__eaiou_papers`
  ADD COLUMN IF NOT EXISTS `submission_sealed_at`  DATETIME DEFAULT NULL COMMENT 'NEVER indexed — TB doctrine',
  ADD COLUMN IF NOT EXISTS `acceptance_sealed_at`  DATETIME DEFAULT NULL COMMENT 'NEVER indexed — TB doctrine',
  ADD COLUMN IF NOT EXISTS `publication_sealed_at` DATETIME DEFAULT NULL COMMENT 'NEVER indexed — TB doctrine',
  ADD COLUMN IF NOT EXISTS `sealed_by`             INT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `submission_hash`       VARCHAR(64) DEFAULT NULL;

SET FOREIGN_KEY_CHECKS = 1;

-- End of migration_005 — eaiou canonical archival tables
-- Temporal Blindness enforced. q_signal is the river.
