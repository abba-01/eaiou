-- migration_009_api_key_bcrypt.sql
-- M-6 fix (CWO audit 2026-05-02): switch API key hashing from SHA-256 to bcrypt
--
-- Backward-compatible: existing rows stay SHA-256 (key_hash_algo='sha256');
-- new rows write bcrypt hashes (key_hash_algo='bcrypt'). The auth path
-- inspects key_hash_algo per row and dispatches to the matching verifier.
--
-- Why: SHA-256 is a fast hash (GPU-friendly); a leaked api_keys table can be
-- offline-cracked in seconds for short keys. bcrypt with cost factor 12 is
-- ~250ms per verification — slow enough to make offline brute-force
-- impractical, fast enough that the per-request latency is invisible.
--
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742
-- Date: 2026-05-02
-- Companion code change: app/routers/api_keys.py (post-migration patch).
--
-- DO NOT APPLY without code patch in same deploy — the column write must land
-- before any code reads it. Order:
--   1. apply migration_009 (DB column added, all existing rows = sha256)
--   2. deploy api_keys.py patch (verifies via algo column)
--   3. operationally rotate any api keys in active use over the next 90 days
--      so existing sha256-hashed keys age out

SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `#__eaiou_api_keys`
  ADD COLUMN IF NOT EXISTS `key_hash_algo` VARCHAR(16) NOT NULL DEFAULT 'sha256'
    COMMENT 'sha256 (legacy) | bcrypt (post-2026-05-02). Auth dispatches per-row.'
    AFTER `api_key`;

-- Mark all existing rows as sha256 explicitly (they default to that, but be
-- explicit for forensic clarity).
UPDATE `#__eaiou_api_keys` SET `key_hash_algo` = 'sha256'
  WHERE `key_hash_algo` IS NULL OR `key_hash_algo` = '';

-- Optional: add an index so auth can short-circuit when stratifying old vs
-- new rows during the cutover period.
CREATE INDEX IF NOT EXISTS `idx_key_hash_algo` ON `#__eaiou_api_keys` (`key_hash_algo`);

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================================
-- Verification:
--   SHOW COLUMNS FROM `#__eaiou_api_keys` LIKE 'key_hash_algo';
--   SELECT key_hash_algo, COUNT(*) FROM `#__eaiou_api_keys` GROUP BY key_hash_algo;
-- Expected (post-migration, pre-code-rollout):
--   sha256: <existing row count>; bcrypt: 0
-- Expected (after first new-key creation post-rollout):
--   sha256: <legacy>; bcrypt: 1+
-- ============================================================================

-- ============================================================================
-- Code patch overview (applied separately):
--
--   app/routers/api_keys.py:
--     - import: from passlib.hash import bcrypt
--     - create_api_key: replace
--           key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
--       with:
--           key_hash = bcrypt.using(rounds=12).hash(raw_key)
--           # store key_hash_algo='bcrypt' on insert
--     - any verify path (where the lookup compares incoming raw key to
--       stored hash): branch on row['key_hash_algo']:
--         if algo == 'sha256': sha256(raw).hexdigest() == row['api_key']
--         if algo == 'bcrypt': bcrypt.verify(raw, row['api_key'])
--     - new keys MUST insert key_hash_algo='bcrypt' explicitly
-- ============================================================================
