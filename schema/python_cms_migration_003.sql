-- eaiou Python CMS — Migration 003
-- Purpose: Observation verification layer + machine-readable tombstone reason codes
-- Run after: python_cms_migration_002.sql
-- Date: 2026-04-11
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742

-- ─── Observation log: verification layer ─────────────────────────────────────
-- observer_hash: SHA-256 of ephemeral observer context (IP + agent + hourly bucket)
--   for anonymous callers. Not stored raw. Never linkable to a person.
--   For verified callers (Bearer token), this is derived from client_uuid instead.
-- verification_level:
--   anonymous  — no bearer token; observer_hash is IP-derived
--   verified   — bearer token resolved to a valid api_client
--   system     — internal system call (e.g. sealing pipeline)

ALTER TABLE `#__eaiou_observation_log`
  ADD COLUMN IF NOT EXISTS `observer_hash` VARCHAR(64) DEFAULT NULL
      COMMENT 'SHA-256 of anonymous observer context or client_uuid. Never raw PII.',
  ADD COLUMN IF NOT EXISTS `verification_level`
      ENUM('anonymous','verified','system') NOT NULL DEFAULT 'anonymous'
      COMMENT 'Provenance quality of this observation record.';

-- ─── Papers: machine-readable tombstone reason code ──────────────────────────
-- tombstone_reason (TEXT, existing) = human-readable notes
-- tombstone_reason_code (ENUM, new)  = machine-readable classification
--   author_deleted  — author voluntarily removed the work
--   policy          — removed by editorial policy (ToS, retraction, etc.)
--   merged          — superseded by a newer record; content merged into cosmoid
--   deprecated      — methodology or data no longer valid; preserved for record

ALTER TABLE `#__eaiou_papers`
  ADD COLUMN IF NOT EXISTS `tombstone_reason_code`
      ENUM('author_deleted','policy','merged','deprecated') DEFAULT NULL
      COMMENT 'Machine-readable tombstone classification. tombstone_reason TEXT = human notes.';
