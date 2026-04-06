-- eaiou_papers — Central hub table
-- Temporal Blindness Doctrine: submission_sealed_at is NEVER exposed publicly
-- Access model: governance layer only (editors + audit system)
-- Author: Eric D. Martin — ORCID: 0009-0006-5944-1742

CREATE TABLE IF NOT EXISTS `#__eaiou_papers` (
  `id`                    INT UNSIGNED NOT NULL AUTO_INCREMENT,

  -- === JOOMLA STANDARD COLUMNS ===
  `state`                 TINYINT NOT NULL DEFAULT 0,
  `access`                INT UNSIGNED NOT NULL DEFAULT 1,
  `ordering`              INT NOT NULL DEFAULT 0,
  `created`               DATETIME NOT NULL,
  `created_by`            INT UNSIGNED NOT NULL DEFAULT 0,
  `modified`              DATETIME NOT NULL,
  `modified_by`           INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out`           INT UNSIGNED NOT NULL DEFAULT 0,
  `checked_out_time`      DATETIME NULL DEFAULT NULL,

  -- === PAPER IDENTITY ===
  `title`                 VARCHAR(512) NOT NULL DEFAULT '',
  `slug`                  VARCHAR(512) NOT NULL DEFAULT '',
  `abstract`              MEDIUMTEXT,
  `keywords`              TEXT,
  `doi`                   VARCHAR(256) DEFAULT NULL,
  `authorship_mode`       ENUM('human','ai','hybrid') NOT NULL DEFAULT 'human',
  `authors_json`          JSON DEFAULT NULL,

  -- === WORKFLOW STATUS ===
  -- Public-facing status label. Does NOT imply temporal ordering.
  `status`                ENUM(
                            'draft',
                            'submitted',
                            'under_review',
                            'revisions',
                            'accepted',
                            'published',
                            'retired'
                          ) NOT NULL DEFAULT 'draft',

  -- === TEMPORAL BLINDNESS — SEALED STATE SPACE ===
  -- These fields are NEVER exposed in public queries, API responses,
  -- discovery views, or reviewer interfaces.
  -- Access: governance layer only (editors + audit system).
  -- Once written, never updated. Sealed at submission.

  `submission_sealed_at`  DATETIME NULL DEFAULT NULL
                          COMMENT 'SEALED: governance layer only. Never public.',

  `submission_hash`       CHAR(64) NULL DEFAULT NULL
                          COMMENT 'SHA256(paper_id + submission_sealed_at + content_hash). Immutable.',

  `submission_capstone`   VARCHAR(256) NULL DEFAULT NULL
                          COMMENT 'Zenodo DOI anchoring submission_hash externally. Perpetual.',

  `submission_version`    SMALLINT UNSIGNED NOT NULL DEFAULT 1,

  -- acceptance and publication dates: governance only
  -- exposed only when paper reaches published state, at editor discretion
  `acceptance_sealed_at`  DATETIME NULL DEFAULT NULL
                          COMMENT 'SEALED: governance layer only.',

  `acceptance_hash`       CHAR(64) NULL DEFAULT NULL,

  `publication_sealed_at` DATETIME NULL DEFAULT NULL
                          COMMENT 'SEALED: governance layer only.',

  -- === CONTENT ===
  `bundle_path`           VARCHAR(512) DEFAULT NULL,
  `thumbnail`             VARCHAR(512) DEFAULT NULL,

  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_slug` (`slug`(191)),
  KEY `idx_status` (`status`),
  KEY `idx_created_by` (`created_by`),
  KEY `idx_state_access` (`state`, `access`)

  -- NOTE: No index on submission_sealed_at by design.
  -- Indexing a sealed field creates a timing side-channel.
  -- Governance queries use the audit layer, not direct index scans.

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
