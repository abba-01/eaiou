-- eaiou — Remaining Schema Tables
-- Temporal Blindness Doctrine: ALL temporal fields are governance-only.
-- Discovery surface is ordered by scientific quality signals, NOT timestamps.
-- Author: Eric D. Martin — ORCID: 0009-0006-5944-1742
-- Date: 2026-04-06
--
-- Tables in this file:
--   eaiou_versions
--   eaiou_ai_sessions        (Answer Box wired: session_id + ledger_capstone)
--   eaiou_didntmakeit
--   eaiou_remsearch
--   eaiou_review_logs        (quality signals → discovery ranking, not review_date)
--   eaiou_attribution_log
--   eaiou_plugins_used
--   eaiou_api_keys
--   eaiou_api_logs


-- ============================================================
-- eaiou_versions
-- Version lineage per paper.
-- Reviewers and public see: label, ai_flag, notes.
-- Temporal fields (generated_at, sealed_at): governance only.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_versions` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`           TINYINT NOT NULL DEFAULT 1,
  `ordering`        INT NOT NULL DEFAULT 0,
  `created`         DATETIME NOT NULL,
  `created_by`      INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`        DATETIME NOT NULL,
  `modified_by`     INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`     INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time` DATETIME NULL DEFAULT NULL,

  -- === RELATIONSHIPS ===
  `paper_id`        INT UNSIGNED NOT NULL,

  -- === VERSION IDENTITY ===
  `label`           VARCHAR(128) NOT NULL DEFAULT '',
  `file_path`       VARCHAR(512) DEFAULT NULL,
  `content_hash`    CHAR(64) DEFAULT NULL
                    COMMENT 'SHA256 of the version file at time of upload.',
  `ai_flag`         TINYINT(1) NOT NULL DEFAULT 0,
  `ai_model_name`   VARCHAR(128) DEFAULT NULL,
  `notes`           TEXT,

  -- === TEMPORAL — SEALED STATE SPACE ===
  -- Never exposed publicly. Governance layer only.
  `generated_at`    DATETIME NULL DEFAULT NULL
                    COMMENT 'SEALED: governance only. When this version was created.',
  `sealed_at`       DATETIME NULL DEFAULT NULL
                    COMMENT 'SEALED: governance only. Immutable after upload.',
  `sealed_hash`     CHAR(64) NULL DEFAULT NULL
                    COMMENT 'SHA256(version_id + file_path + content_hash + sealed_at).',

  PRIMARY KEY (`id`),
  KEY `idx_paper_id` (`paper_id`),
  KEY `idx_state_paper` (`state`, `paper_id`)

  -- No index on sealed_at — timing side-channel prevention.

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_ai_sessions
-- Per-paper AI usage audit. Immutable after close.
--
-- Answer Box integration:
--   answer_box_session_id  → UUID from AnswerBox.__init__(), sealed before ledger opens
--   answer_box_ledger_capstone → Zenodo DOI of the Answer Box ledger block
--   This wire makes every AI session auditable via the external capstone.
--
-- Discovery surface: sessions are hidden. Only ai_flag on the paper is public.
-- Temporal fields: governance only.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_ai_sessions` (
  `id`                        INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`                     TINYINT NOT NULL DEFAULT 1,
  `ordering`                  INT NOT NULL DEFAULT 0,
  `created`                   DATETIME NOT NULL,
  `created_by`                INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`                  DATETIME NOT NULL,
  `modified_by`               INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`               INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time`          DATETIME NULL DEFAULT NULL,

  -- === RELATIONSHIPS ===
  `paper_id`                  INT UNSIGNED NOT NULL,

  -- === SESSION IDENTITY ===
  `session_label`             VARCHAR(256) NOT NULL DEFAULT '',
  `ai_model_name`             VARCHAR(128) NOT NULL DEFAULT '',
  `ai_model_version`          VARCHAR(64) DEFAULT NULL,

  -- === ANSWER BOX WIRE ===
  -- answer_box_session_id is sealed before the ledger opens.
  -- It is the escape-proof identifier: if trajectory shifts mid-session,
  -- the gap is visible in the ledger chain.
  `answer_box_session_id`     CHAR(36) NULL DEFAULT NULL
                              COMMENT 'UUID from AnswerBox init. Sealed before ledger opens. Immutable.',
  `answer_box_ledger_capstone` VARCHAR(256) NULL DEFAULT NULL
                              COMMENT 'Zenodo DOI anchoring the Answer Box ledger block for this session.',

  -- === USAGE METRICS ===
  `tokens_in`                 INT UNSIGNED NOT NULL DEFAULT 0,
  `tokens_out`                INT UNSIGNED NOT NULL DEFAULT 0,
  `session_notes`             TEXT,

  -- === REDACTION ===
  `redaction_status`          ENUM('none','partial','full') NOT NULL DEFAULT 'none',
  `redaction_reason`          TEXT,

  -- === AUDIT ===
  `session_hash`              CHAR(64) NULL DEFAULT NULL
                              COMMENT 'SHA256(session_id + paper_id + model + tokens + end_time). Immutable after close.',

  -- === TEMPORAL — SEALED STATE SPACE ===
  -- Start and end times are immutable after session close.
  -- Never exposed publicly.
  `start_sealed_at`           DATETIME NULL DEFAULT NULL
                              COMMENT 'SEALED: governance only. Session open time.',
  `end_sealed_at`             DATETIME NULL DEFAULT NULL
                              COMMENT 'SEALED: governance only. Session close time. Null = still open.',

  PRIMARY KEY (`id`),
  KEY `idx_paper_id` (`paper_id`),
  KEY `idx_model_state` (`ai_model_name`(64), `state`),
  KEY `idx_answer_box_session` (`answer_box_session_id`)

  -- No index on start_sealed_at or end_sealed_at — timing side-channel prevention.

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_didntmakeit
-- Excluded AI interactions archived for full-context preservation.
-- "What didn't make it" stays discoverable.
-- Prompts hashed by default; raw text stored only if redaction_status = 'none'.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_didntmakeit` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`             TINYINT NOT NULL DEFAULT 1,
  `ordering`          INT NOT NULL DEFAULT 0,
  `created`           DATETIME NOT NULL,
  `created_by`        INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`          DATETIME NOT NULL,
  `modified_by`       INT UNSIGNED NOT NULL DEFAULT 0,

  -- === RELATIONSHIPS ===
  `session_id`        INT UNSIGNED NOT NULL,
  `paper_id`          INT UNSIGNED NOT NULL,

  -- === CONTENT ===
  `prompt_hash`       CHAR(64) NOT NULL
                      COMMENT 'SHA256 of the prompt. Always stored.',
  `prompt_text`       MEDIUMTEXT
                      COMMENT 'Raw prompt. May be NULL if redaction_status = partial or full.',
  `response_hash`     CHAR(64) NULL DEFAULT NULL,
  `response_text`     MEDIUMTEXT
                      COMMENT 'Raw response. May be NULL if redacted.',
  `exclusion_reason`  TEXT
                      COMMENT 'Why this output was not used.',

  -- === REDACTION ===
  `redacted`          TINYINT(1) NOT NULL DEFAULT 0,
  `redaction_hash`    CHAR(64) NULL DEFAULT NULL
                      COMMENT 'Hash of the redacted content for integrity proof.',
  `redaction_status`  ENUM('none','partial','full') NOT NULL DEFAULT 'none',

  -- === TEMPORAL — SEALED ===
  `interaction_sealed_at` DATETIME NULL DEFAULT NULL
                          COMMENT 'SEALED: governance only. When interaction occurred.',

  PRIMARY KEY (`id`),
  KEY `idx_session_id` (`session_id`),
  KEY `idx_paper_id` (`paper_id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_remsearch
-- Literature triage — sources considered, used or excluded.
-- Used sources are provenance. Excluded sources are context.
-- Both are valuable. Neither is deleted.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_remsearch` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`           TINYINT NOT NULL DEFAULT 1,
  `ordering`        INT NOT NULL DEFAULT 0,
  `created`         DATETIME NOT NULL,
  `created_by`      INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`        DATETIME NOT NULL,
  `modified_by`     INT UNSIGNED NOT NULL DEFAULT 0,

  -- === RELATIONSHIPS ===
  `paper_id`        INT UNSIGNED NOT NULL,

  -- === CITATION ===
  `citation_title`  VARCHAR(512) NOT NULL DEFAULT '',
  `citation_source` VARCHAR(256) DEFAULT NULL,
  `citation_doi`    VARCHAR(256) DEFAULT NULL,
  `citation_link`   VARCHAR(512) DEFAULT NULL,
  `source_type`     ENUM(
                      'journal',
                      'preprint',
                      'dataset',
                      'code',
                      'book',
                      'conference',
                      'patent',
                      'other'
                    ) NOT NULL DEFAULT 'journal',

  -- === TRIAGE DECISION ===
  `used`            TINYINT(1) NOT NULL DEFAULT 0,
  `reason_unused`   TEXT
                    COMMENT 'Exclusion reason. Required when used=0 and state=published.',
  `cross_domain_flag` TINYINT(1) NOT NULL DEFAULT 0
                    COMMENT 'Flagged as potentially relevant in another domain.',

  -- === TEMPORAL — SEALED ===
  `triaged_at`      DATETIME NULL DEFAULT NULL
                    COMMENT 'SEALED: governance only. When triage decision was made.',

  PRIMARY KEY (`id`),
  KEY `idx_paper_id` (`paper_id`),
  KEY `idx_used` (`used`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_review_logs
-- Peer review lineage. Review is archival, not editorial housekeeping.
--
-- CRITICAL DESIGN NOTE — Scientific Flow:
-- Papers are NOT ranked by review_date.
-- Review scores (rubric_*) feed into the discovery quality signal.
-- The public surface shows: who reviewed, what scores, what recommendation.
-- It does NOT show: when the review was submitted.
--
-- review_sealed_at: governance only. Never indexed. Never public.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_review_logs` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`                 TINYINT NOT NULL DEFAULT 1,
  `ordering`              INT NOT NULL DEFAULT 0,
  `created`               DATETIME NOT NULL,
  `created_by`            INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`              DATETIME NOT NULL,
  `modified_by`           INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`           INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time`      DATETIME NULL DEFAULT NULL,

  -- === RELATIONSHIPS ===
  `paper_id`              INT UNSIGNED NOT NULL,
  `reviewer_user_id`      INT UNSIGNED NOT NULL DEFAULT 0,
  `version_reviewed`      VARCHAR(128) DEFAULT NULL,

  -- === IDENTITY DISPLAY ===
  `reviewer_displayname`  VARCHAR(256) DEFAULT NULL
                          COMMENT 'Display name for open review rendering. NULL = anonymized.',
  `identity_mode`         ENUM('open','anonymous') NOT NULL DEFAULT 'anonymous',
  `consent_display`       TINYINT(1) NOT NULL DEFAULT 0,

  -- === RUBRIC SCORES ===
  -- These are the discovery quality signals.
  -- Papers accumulate signal from rubric scores across reviews.
  -- Higher signal = higher discovery rank. Not indexed by time.
  `rubric_overall`        TINYINT UNSIGNED NOT NULL DEFAULT 0
                          COMMENT '0-10. Feeds paper quality_signal.',
  `rubric_originality`    TINYINT UNSIGNED NOT NULL DEFAULT 0
                          COMMENT '0-10.',
  `rubric_methodology`    TINYINT UNSIGNED NOT NULL DEFAULT 0
                          COMMENT '0-10.',
  `rubric_transparency`   TINYINT UNSIGNED NOT NULL DEFAULT 0
                          COMMENT '0-10. Weighted higher for eaiou doctrine.',
  `rubric_ai_disclosure`  TINYINT UNSIGNED NOT NULL DEFAULT 0
                          COMMENT '0-10. Required when ai_flag=1 on paper.',
  `rubric_cross_domain`   TINYINT UNSIGNED NOT NULL DEFAULT 0
                          COMMENT '0-10. Signal for cross-domain applicability.',

  -- === DECISION ===
  `recommendation`        ENUM(
                            'accept',
                            'minor_revisions',
                            'major_revisions',
                            'reject',
                            'refer'
                          ) NULL DEFAULT NULL,

  -- === CONTENT ===
  `labels_json`           JSON DEFAULT NULL
                          COMMENT 'Structured review labels/chips.',
  `review_notes`          MEDIUMTEXT,
  `attachments_json`      JSON DEFAULT NULL,
  `author_response`       MEDIUMTEXT
                          COMMENT 'Author response to this review, if recorded.',

  -- === TEMPORAL — SEALED STATE SPACE ===
  -- Review date is governance only. Science is evaluated on rubric, not recency.
  `review_sealed_at`      DATETIME NULL DEFAULT NULL
                          COMMENT 'SEALED: governance only. When review was submitted. Never public.',
  `review_hash`           CHAR(64) NULL DEFAULT NULL
                          COMMENT 'SHA256(review_id + paper_id + reviewer_id + rubrics + review_sealed_at).',

  PRIMARY KEY (`id`),
  KEY `idx_paper_id` (`paper_id`),
  KEY `idx_reviewer` (`reviewer_user_id`),
  KEY `idx_state_paper` (`state`, `paper_id`)

  -- No index on review_sealed_at — timing side-channel.
  -- Discovery sort uses rubric_overall, not review_sealed_at.

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_attribution_log
-- Who did what. Human and AI contribution roles distinguished.
-- Immutable after creation. Annotate, never delete.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_attribution_log` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`               TINYINT NOT NULL DEFAULT 1,
  `ordering`            INT NOT NULL DEFAULT 0,
  `created`             DATETIME NOT NULL,
  `created_by`          INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`            DATETIME NOT NULL,
  `modified_by`         INT UNSIGNED NOT NULL DEFAULT 0,

  -- === RELATIONSHIPS ===
  `paper_id`            INT UNSIGNED NOT NULL,

  -- === CONTRIBUTOR ===
  `contributor_name`    VARCHAR(256) NOT NULL DEFAULT '',
  `contributor_orcid`   VARCHAR(64) DEFAULT NULL,
  `contributor_type`    ENUM('human','ai','hybrid') NOT NULL DEFAULT 'human',
  `role_description`    VARCHAR(512) NOT NULL DEFAULT '',
  `contribution_type`   ENUM(
                          'conceptualization',
                          'methodology',
                          'software',
                          'validation',
                          'formal_analysis',
                          'investigation',
                          'data_curation',
                          'writing_original',
                          'writing_review',
                          'visualization',
                          'supervision',
                          'project_admin',
                          'funding',
                          'ai_assistance',
                          'other'
                        ) NOT NULL DEFAULT 'other',
  `ai_tool_used`        VARCHAR(128) DEFAULT NULL
                        COMMENT 'AI tool name if contributor_type = ai or hybrid.',
  `scope_notes`         TEXT,

  -- === TEMPORAL — SEALED ===
  `contribution_sealed_at` DATETIME NULL DEFAULT NULL
                           COMMENT 'SEALED: governance only.',

  PRIMARY KEY (`id`),
  KEY `idx_paper_id` (`paper_id`),
  KEY `idx_contributor_type` (`contributor_type`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_plugins_used
-- Tool/plugin execution audit per paper.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_plugins_used` (
  `id`                  INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`               TINYINT NOT NULL DEFAULT 1,
  `ordering`            INT NOT NULL DEFAULT 0,
  `created`             DATETIME NOT NULL,
  `created_by`          INT UNSIGNED NOT NULL DEFAULT 0,

  -- === RELATIONSHIPS ===
  `paper_id`            INT UNSIGNED NOT NULL,

  -- === PLUGIN IDENTITY ===
  `plugin_name`         VARCHAR(256) NOT NULL DEFAULT '',
  `plugin_type`         ENUM(
                          'analysis',
                          'visualization',
                          'transformation',
                          'validation',
                          'ai_bridge',
                          'export',
                          'other'
                        ) NOT NULL DEFAULT 'other',
  `plugin_version`      VARCHAR(64) DEFAULT NULL,
  `execution_context`   VARCHAR(256) DEFAULT NULL,
  `exec_log_path`       VARCHAR(512) DEFAULT NULL,
  `result_hash`         CHAR(64) DEFAULT NULL
                        COMMENT 'Hash of execution output for reproducibility.',

  -- === TEMPORAL — SEALED ===
  `executed_at`         DATETIME NULL DEFAULT NULL
                        COMMENT 'SEALED: governance only.',

  PRIMARY KEY (`id`),
  KEY `idx_paper_id` (`paper_id`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_api_keys
-- API access registry. Keys stored hashed only.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_api_keys` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD ===
  `state`           TINYINT NOT NULL DEFAULT 1,
  `ordering`        INT NOT NULL DEFAULT 0,
  `created`         DATETIME NOT NULL,
  `created_by`      INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`        DATETIME NOT NULL,
  `modified_by`     INT UNSIGNED NOT NULL DEFAULT 0,

  -- === RELATIONSHIPS ===
  `user_id`         INT UNSIGNED NOT NULL DEFAULT 0,

  -- === KEY ===
  `api_key_hash`    CHAR(64) NOT NULL
                    COMMENT 'SHA256 of the raw API key. Raw key never stored.',
  `description`     VARCHAR(256) DEFAULT NULL,
  `access_level`    ENUM(
                      'read',
                      'submit',
                      'review',
                      'admin'
                    ) NOT NULL DEFAULT 'read',

  -- === TEMPORAL — GOVERNANCE ===
  `issued_at`       DATETIME NULL DEFAULT NULL
                    COMMENT 'SEALED: governance only.',
  `expires_at`      DATETIME NULL DEFAULT NULL
                    COMMENT 'Governance only. Null = no expiry.',
  `last_used_at`    DATETIME NULL DEFAULT NULL
                    COMMENT 'Updated on use. Governance only.',
  `revoked_at`      DATETIME NULL DEFAULT NULL
                    COMMENT 'Set when key is revoked. Immutable once set.',
  `revocation_reason` TEXT,

  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_api_key_hash` (`api_key_hash`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_state` (`state`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_api_logs
-- Immutable API call audit. Append-only by policy.
-- No UPDATE or DELETE on this table in application code.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_api_logs` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === RELATIONSHIPS ===
  `api_key_id`      INT UNSIGNED NULL DEFAULT NULL,
  `user_id`         INT UNSIGNED NULL DEFAULT NULL,

  -- === REQUEST ===
  `endpoint`        VARCHAR(512) NOT NULL DEFAULT '',
  `method`          ENUM('GET','POST','PUT','PATCH','DELETE') NOT NULL DEFAULT 'GET',
  `request_hash`    CHAR(64) NULL DEFAULT NULL
                    COMMENT 'SHA256 of request payload. Full payload not stored by default.',
  `response_code`   SMALLINT UNSIGNED NOT NULL DEFAULT 200,
  `response_summary` VARCHAR(512) DEFAULT NULL,

  -- === TEMPORAL — ALL GOVERNANCE ===
  -- API logs are purely governance / audit layer.
  -- No temporal field from this table is ever public.
  `request_at`      DATETIME NOT NULL
                    COMMENT 'Immutable. Set once on insert.',

  -- === INTEGRITY ===
  `log_hash`        CHAR(64) NULL DEFAULT NULL
                    COMMENT 'SHA256(log_id + api_key_id + endpoint + request_at). Chain anchor.',
  `prior_hash`      CHAR(64) NULL DEFAULT NULL
                    COMMENT 'Hash of previous log row. Hash chain for tamper detection.',

  PRIMARY KEY (`id`),
  KEY `idx_api_key_id` (`api_key_id`),
  KEY `idx_user_id` (`user_id`)

  -- NOTE: No index on request_at by design.
  -- API logs are scanned by governance queries only.
  -- Indexing request_at exposes a timing side-channel.

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- eaiou_quality_signals
-- Computed quality signal per paper.
-- Updated by governance layer when reviews complete.
-- This is the NON-temporal discovery ranking surface.
-- Public queries ORDER BY q_signal DESC — never by any date.
-- ============================================================

CREATE TABLE IF NOT EXISTS `#__eaiou_quality_signals` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === RELATIONSHIP ===
  `paper_id`              INT UNSIGNED NOT NULL,

  -- === SIGNAL COMPONENTS ===
  -- Each component is computed from review rubrics and content analysis.
  -- None of these are timestamps. All are quality measures.
  `q_overall`             DECIMAL(5,3) NOT NULL DEFAULT 0.000
                          COMMENT 'Weighted average of rubric_overall across all accepted reviews.',
  `q_originality`         DECIMAL(5,3) NOT NULL DEFAULT 0.000,
  `q_methodology`         DECIMAL(5,3) NOT NULL DEFAULT 0.000,
  `q_transparency`        DECIMAL(5,3) NOT NULL DEFAULT 0.000
                          COMMENT 'Weighted 1.5x in eaiou doctrine. Transparency is a first-class value.',
  `q_cross_domain`        DECIMAL(5,3) NOT NULL DEFAULT 0.000
                          COMMENT 'Cross-domain applicability signal. Boosts serendipitous discovery.',
  `q_ai_disclosure`       DECIMAL(5,3) NOT NULL DEFAULT 0.000,

  -- === COMPOSITE SIGNAL ===
  `q_signal`              DECIMAL(7,4) NOT NULL DEFAULT 0.0000
                          COMMENT 'Composite discovery signal. Order by this, never by date.',
  `review_count`          SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `signal_version`        SMALLINT UNSIGNED NOT NULL DEFAULT 1
                          COMMENT 'Incremented each time signal is recomputed.',

  -- === GOVERNANCE TEMPORAL ===
  `last_computed_at`      DATETIME NULL DEFAULT NULL
                          COMMENT 'SEALED: governance only. When signal was last recomputed.',

  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_paper_id` (`paper_id`),
  KEY `idx_q_signal` (`q_signal`)

  -- q_signal IS indexed — it is the discovery sort key.
  -- Dates are not indexed. Quality is the surface.

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
