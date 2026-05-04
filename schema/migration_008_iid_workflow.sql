-- migration_008_iid_workflow.sql
-- eaiou — IID workflow schema for the authoring surface
-- Phase B + C prerequisite (manuscript blocks + IID providers/actions/snapshots)
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742
-- Date: 2026-05-02
--
-- Companion to migration_007_marketplace_core. Where 007 covers the
-- checksubmit storefront, 008 covers the manuscript-editor + IID-dispatch
-- workflow inside eaiou itself.
--
-- Tables created:
--   1. eaiou_manuscripts       — author manuscripts
--   2. eaiou_manuscript_blocks — block-structured editor content
--   3. eaiou_manuscript_snapshots — version timeline (point-in-time copies)
--   4. eaiou_iid_providers     — author-configured IID providers (Mae, OpenAI, Gemini, etc.)
--   5. eaiou_iid_actions       — every IID invocation (audit trail; ToS Compliance Doctrine §3)
--   6. eaiou_iid_action_inputs — input payloads per action (kept separate so they don't bloat the actions row)
--
-- All statements idempotent (CREATE TABLE IF NOT EXISTS). Run with:
--   mariadb -u eaiou_db -p eaiou < schema/migration_008_iid_workflow.sql
--
-- Convention: `#__eaiou_*` prefix matches migrations 005-007 and the existing
-- production schema. App code in app/services/iid_dispatcher.py and
-- app/routers/api_iid.py uses this prefix consistently.

SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

-- ============================================================
-- 1. eaiou_manuscripts
-- One row per manuscript draft. Owned by an author (user).
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_manuscripts` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`           INT UNSIGNED NOT NULL COMMENT 'fk #__eaiou_users.id (author)',
  `title`             VARCHAR(512) NOT NULL DEFAULT 'Untitled',
  `target_venue`      VARCHAR(255) DEFAULT NULL,
  `discipline`        VARCHAR(128) DEFAULT NULL COMMENT 'computational | experimental | review | ...',
  `status`            VARCHAR(32)  NOT NULL DEFAULT 'draft' COMMENT 'draft | submitted | revised | accepted | rejected',
  `word_count`        INT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'cached; recomputed on autosave',
  `cosmoid`           CHAR(36)     DEFAULT NULL COMMENT 'CosmoID once minted; never overwritten',
  `created_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user (`user_id`),
  INDEX idx_status (`status`),
  INDEX idx_cosmoid (`cosmoid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 2. eaiou_manuscript_blocks
-- Block-structured editor content. Order via sort_index.
-- Block types: heading_2, heading_3, paragraph, code, blockquote, list_item,
--              math_block, table, figure_caption.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_manuscript_blocks` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `manuscript_id`   INT UNSIGNED NOT NULL,
  `sort_index`      INT          NOT NULL DEFAULT 0,
  `type`            VARCHAR(32)  NOT NULL DEFAULT 'paragraph',
  `text`            MEDIUMTEXT   DEFAULT NULL COMMENT 'plain-text content (for headings/paragraphs)',
  `html`            MEDIUMTEXT   DEFAULT NULL COMMENT 'rendered html (for paragraph blocks with inline marks)',
  `anchor`          VARCHAR(128) DEFAULT NULL COMMENT 'slug for in-page navigation',
  `metadata_json`   LONGTEXT     DEFAULT NULL COMMENT 'block-type-specific extras (e.g. code language, table headers)',
  `created_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_manuscript_sort (`manuscript_id`, `sort_index`),
  INDEX idx_type (`type`),
  INDEX idx_anchor (`anchor`),
  CONSTRAINT fk_blocks_manuscript
    FOREIGN KEY (`manuscript_id`) REFERENCES `#__eaiou_manuscripts`(`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 3. eaiou_manuscript_snapshots
-- Point-in-time copies (version timeline). Created on every autosave commit
-- AND on every IID action that modifies the manuscript text.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_manuscript_snapshots` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `manuscript_id`   INT UNSIGNED NOT NULL,
  `label`           VARCHAR(128) DEFAULT NULL COMMENT 'auto-generated (rN) or author-given',
  `triggered_by`    VARCHAR(64)  NOT NULL DEFAULT 'autosave' COMMENT 'autosave | manual | iid_action | submission',
  `iid_action_id`   INT UNSIGNED DEFAULT NULL COMMENT 'fk eaiou_iid_actions.id if triggered_by=iid_action',
  `blocks_json`     LONGTEXT     NOT NULL COMMENT 'full snapshot of manuscript_blocks as JSON array',
  `word_count`      INT UNSIGNED NOT NULL DEFAULT 0,
  `content_hash`    CHAR(64)     DEFAULT NULL COMMENT 'sha256 of blocks_json',
  `created_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_manuscript_created (`manuscript_id`, `created_at`),
  INDEX idx_iid_action (`iid_action_id`),
  CONSTRAINT fk_snapshots_manuscript
    FOREIGN KEY (`manuscript_id`) REFERENCES `#__eaiou_manuscripts`(`id`)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 4. eaiou_iid_providers
-- Per-user IID provider configuration. Mae (Anthropic), OpenAI, Gemini, etc.
-- API keys encrypted at rest (AES-GCM), key from secret store NOT in DB.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_iid_providers` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `user_id`           INT UNSIGNED NOT NULL,
  `name`              VARCHAR(64)  NOT NULL COMMENT 'mae | openai | gemini | llama | custom',
  `display_name`      VARCHAR(128) NOT NULL,
  `provider_legal`    VARCHAR(128) NOT NULL COMMENT 'Anthropic | OpenAI | Google | Meta | Custom',
  `default_model`     VARCHAR(128) NOT NULL COMMENT 'e.g. claude-opus-4-7 | gpt-5 | gemini-2.5',
  `api_key_encrypted` VARBINARY(2048) DEFAULT NULL COMMENT 'AES-GCM ciphertext; never logged',
  `api_endpoint_url`  VARCHAR(512) DEFAULT NULL COMMENT 'override only for custom providers',
  `enabled_actions`   LONGTEXT     DEFAULT NULL COMMENT 'JSON array of action names this provider exposes',
  `active`            TINYINT(1)   NOT NULL DEFAULT 1,
  `disabled_at`       TIMESTAMP    NULL DEFAULT NULL COMMENT 'soft-disable when key revoked or auth failed',
  `cost_cap_cents`    INT UNSIGNED DEFAULT NULL COMMENT 'monthly spend cap, NULL=unlimited',
  `created_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unq_user_provider (`user_id`, `name`),
  INDEX idx_active (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 5. eaiou_iid_actions
-- Every IID action invocation. Append-only; never UPDATE except for status
-- transitions and result attachment. ToS Compliance Doctrine §3 audit trail.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_iid_actions` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `intellid`          CHAR(36)     NOT NULL COMMENT 'UUID per action; primary identity',
  `user_id`           INT UNSIGNED NOT NULL,
  `provider_id`       INT UNSIGNED NOT NULL COMMENT 'fk eaiou_iid_providers.id',
  `manuscript_id`     INT UNSIGNED DEFAULT NULL,
  `action_name`       VARCHAR(64)  NOT NULL COMMENT 'scope_check | clarity_check | methods_check | ...',
  `model_family`      VARCHAR(128) NOT NULL COMMENT 'snapshot of provider.default_model at call time',
  `instance_hash`     CHAR(16)     NOT NULL COMMENT 'short hash for disclosure block (16 hex chars)',
  `status`            VARCHAR(32)  NOT NULL DEFAULT 'pending' COMMENT 'pending | running | completed | failed | cancelled',
  `superseded_by`     INT UNSIGNED DEFAULT NULL COMMENT 'fk to a re-run action; ONLY allowed cross-action link (no chaining)',
  `input_tokens`      INT UNSIGNED DEFAULT NULL,
  `output_tokens`     INT UNSIGNED DEFAULT NULL,
  `cost_cents`        INT          DEFAULT NULL,
  `result_text`       LONGTEXT     DEFAULT NULL COMMENT 'human-readable result body',
  `result_structured` LONGTEXT     DEFAULT NULL COMMENT 'JSON-structured result fields per-action',
  `error_text`        TEXT         DEFAULT NULL,
  `created_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `completed_at`      TIMESTAMP    NULL DEFAULT NULL,
  UNIQUE KEY unq_intellid (`intellid`),
  INDEX idx_user (`user_id`),
  INDEX idx_provider (`provider_id`),
  INDEX idx_manuscript (`manuscript_id`),
  INDEX idx_action (`action_name`),
  INDEX idx_status (`status`),
  INDEX idx_created (`created_at`),
  INDEX idx_superseded (`superseded_by`),
  CONSTRAINT fk_actions_provider
    FOREIGN KEY (`provider_id`) REFERENCES `#__eaiou_iid_providers`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 6. eaiou_iid_action_inputs
-- Input payloads kept in their own table so eaiou_iid_actions stays narrow.
-- One-to-one with actions.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_iid_action_inputs` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `action_id`       INT UNSIGNED NOT NULL,
  `selected_text`   LONGTEXT     DEFAULT NULL COMMENT 'verbatim text the action was invoked on',
  `inputs_json`     LONGTEXT     DEFAULT NULL COMMENT 'all other input fields per-action',
  `manuscript_snapshot_id` INT UNSIGNED DEFAULT NULL COMMENT 'pinned manuscript version at invocation',
  `created_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY unq_action (`action_id`),
  INDEX idx_snapshot (`manuscript_snapshot_id`),
  CONSTRAINT fk_inputs_action
    FOREIGN KEY (`action_id`) REFERENCES `#__eaiou_iid_actions`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- Verification:
-- SHOW TABLES LIKE '#__eaiou_manuscript%';
-- SHOW TABLES LIKE '#__eaiou_iid_%';
-- Expected new tables:
--   #__eaiou_manuscripts, #__eaiou_manuscript_blocks, #__eaiou_manuscript_snapshots,
--   #__eaiou_iid_providers, #__eaiou_iid_actions, #__eaiou_iid_action_inputs
-- ============================================================
