-- eaiou Python CMS — Migration 004
-- Purpose: Gateway-dependent tables + API clients
-- Run after: python_cms_migration_003.sql
-- Date: 2026-04-11
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742

SET FOREIGN_KEY_CHECKS = 0;

-- ─── Paper sections ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_paper_sections` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`         INT UNSIGNED NOT NULL,
  `section_name`     VARCHAR(255) NOT NULL,
  `section_content`  LONGTEXT DEFAULT NULL,
  `section_notes`    LONGTEXT DEFAULT NULL,
  `section_order`    INT NOT NULL DEFAULT 0,
  `seeded_from`      VARCHAR(64) DEFAULT NULL COMMENT 'interrogation, template, manual',
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_order`    (`paper_id`, `section_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Intelligence modules (per-paper AI agents) ───────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_intelligence_modules` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`      INT UNSIGNED NOT NULL,
  `display_label` VARCHAR(255) DEFAULT NULL,
  `role`          ENUM('defender','red_team') NOT NULL,
  `provider`      VARCHAR(64) NOT NULL DEFAULT 'anthropic',
  `model_id`      VARCHAR(128) NOT NULL,
  `status`        ENUM('not_loaded','active') NOT NULL DEFAULT 'not_loaded',
  `created`       DATETIME NOT NULL,
  `last_event_at` DATETIME DEFAULT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Module events (read / red_team / defend outputs) ────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_module_events` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `module_id`     INT UNSIGNED NOT NULL,
  `paper_id`      INT UNSIGNED NOT NULL,
  `event_type`    ENUM('read','red_team','defend') NOT NULL,
  `focus_text`    TEXT DEFAULT NULL,
  `response_text` LONGTEXT DEFAULT NULL,
  `tokens_in`     INT DEFAULT NULL,
  `tokens_out`    INT DEFAULT NULL,
  `occurred_at`   DATETIME NOT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_event` (`paper_id`, `event_type`),
  INDEX `idx_module_id`   (`module_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Interrogation log (expert Q&A exchanges) ────────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_interrogation_log` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`      INT UNSIGNED NOT NULL,
  `question`      TEXT NOT NULL,
  `response`      LONGTEXT NOT NULL,
  `expert_domain` VARCHAR(128) DEFAULT NULL,
  `expert_title`  VARCHAR(255) DEFAULT NULL,
  `asked_at`      DATETIME NOT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Volley log (cross-intelligence audit rounds) ────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_volley_log` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`          INT UNSIGNED NOT NULL,
  `round_number`      INT NOT NULL DEFAULT 1,
  `auditor_model`     VARCHAR(128) NOT NULL,
  `document_snapshot` LONGTEXT DEFAULT NULL,
  `findings_json`     LONGTEXT DEFAULT NULL,
  `finding_count`     INT NOT NULL DEFAULT 0,
  `is_clean`          TINYINT(1) NOT NULL DEFAULT 0,
  `audited_at`        DATETIME NOT NULL,
  `author_response`   TEXT DEFAULT NULL,
  `responded_at`      DATETIME DEFAULT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id`    (`paper_id`),
  INDEX `idx_unresponded` (`paper_id`, `is_clean`, `author_response`(1))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Paper snapshots (gate milestone checkpoints) ────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_paper_snapshots` (
  `id`                   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`             INT UNSIGNED NOT NULL,
  `gate_code`            VARCHAR(64) NOT NULL,
  `content_hash`         VARCHAR(64) NOT NULL,
  `word_vector_json`     LONGTEXT DEFAULT NULL,
  `section_json`         LONGTEXT DEFAULT NULL,
  `section_count`        INT NOT NULL DEFAULT 0,
  `divergence_from_prior` FLOAT DEFAULT NULL,
  `change_class`         ENUM('DRIFT','BRANCH','REWRITE') DEFAULT NULL,
  `created_at`           DATETIME NOT NULL,
  UNIQUE KEY `uq_paper_gate` (`paper_id`, `gate_code`),
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Integrity seals (submission seal records) ───────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_integrity_seals` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`              INT UNSIGNED NOT NULL,
  `cosmoid`               CHAR(36) DEFAULT NULL,
  `seal_hash`             VARCHAR(64) NOT NULL,
  `gate_valid`            TINYINT(1) NOT NULL DEFAULT 0,
  `audit_status`          VARCHAR(32) NOT NULL DEFAULT 'PENDING',
  `leakage_count`         INT NOT NULL DEFAULT 0,
  `contamination_score`   FLOAT DEFAULT NULL,
  `mbs`                   FLOAT DEFAULT NULL,
  `integrity_payload_json` LONGTEXT DEFAULT NULL,
  `sealed_at`             DATETIME NOT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`),
  INDEX `idx_sealed_at` (`paper_id`, `sealed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Leakage flags (per-section leakage detection results) ───────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_leakage_flags` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`         INT UNSIGNED NOT NULL,
  `snapshot_id`      INT UNSIGNED DEFAULT NULL,
  `section_name`     VARCHAR(255) DEFAULT NULL,
  `module_event_id`  INT UNSIGNED DEFAULT NULL,
  `similarity_score` FLOAT DEFAULT NULL,
  `status`           VARCHAR(32) NOT NULL DEFAULT 'flagged',
  `reason`           TEXT DEFAULT NULL,
  `detected_at`      DATETIME NOT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Trajectories (fork tree nodes) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_trajectories` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `paper_id`    INT UNSIGNED NOT NULL,
  `parent_id`   INT UNSIGNED DEFAULT NULL,
  `agent`       VARCHAR(128) DEFAULT NULL,
  `method_class` VARCHAR(64) DEFAULT NULL,
  `active`      TINYINT(1) NOT NULL DEFAULT 1,
  `fork_reason` TEXT DEFAULT NULL,
  `created_at`  DATETIME NOT NULL,
  FOREIGN KEY (`paper_id`) REFERENCES `#__eaiou_papers`(`id`),
  INDEX `idx_paper_id` (`paper_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Author profiles (ORCID-derived vocab, never asked) ──────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_author_profiles` (
  `id`               INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `orcid`            VARCHAR(50) NOT NULL UNIQUE,
  `profile_vocab_json` LONGTEXT DEFAULT NULL,
  `vocab_updated_at` DATETIME DEFAULT NULL,
  `intake_json`      LONGTEXT DEFAULT NULL,
  `updated_at`       DATETIME DEFAULT NULL,
  INDEX `idx_orcid` (`orcid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Gap matches (gitgap gap → author profile matching) ──────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_gap_matches` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `author_profile_id` INT UNSIGNED NOT NULL,
  `gap_id`            INT NOT NULL,
  `gap_declaration`   LONGTEXT DEFAULT NULL,
  `gap_title`         VARCHAR(500) DEFAULT NULL,
  `gap_journal`       VARCHAR(255) DEFAULT NULL,
  `gap_term`          VARCHAR(128) DEFAULT NULL,
  `match_score`       FLOAT DEFAULT NULL,
  `matched_at`        DATETIME NOT NULL,
  `dismissed`         TINYINT(1) NOT NULL DEFAULT 0,
  `accepted`          TINYINT(1) NOT NULL DEFAULT 0,
  FOREIGN KEY (`author_profile_id`) REFERENCES `#__eaiou_author_profiles`(`id`),
  INDEX `idx_profile_id` (`author_profile_id`),
  INDEX `idx_gap_id`     (`gap_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── API clients (intelligence author API registrations) ─────────────────────
CREATE TABLE IF NOT EXISTS `#__eaiou_api_clients` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `client_uuid`       CHAR(36) NOT NULL UNIQUE,
  `system_name`       VARCHAR(255) NOT NULL,
  `intelligence_name` VARCHAR(255) NOT NULL,
  `intellid_ref`      CHAR(36) DEFAULT NULL,
  `responsible_human` VARCHAR(255) DEFAULT NULL,
  `api_token`         VARCHAR(64) NOT NULL UNIQUE,
  `origin_type`       ENUM('non_humint') NOT NULL DEFAULT 'non_humint',
  `active`            TINYINT(1) NOT NULL DEFAULT 1,
  `created_at`        DATETIME NOT NULL,
  `last_used_at`      DATETIME DEFAULT NULL,
  INDEX `idx_api_token` (`api_token`),
  INDEX `idx_active`    (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
