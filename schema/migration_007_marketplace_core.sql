-- migration_007_marketplace_core.sql
-- eaiou / checksubmit — marketplace core schema
-- Phase 0 of the Manusights-competitor build (see manusights_competitor_mvp_plan.md §0.4)
-- Author: Eric D. Martin | ORCID 0009-0006-5944-1742
-- Date: 2026-05-01
--
-- This migration adds five tables for the checksubmit storefront:
--   1. eaiou_products            — product catalog (8 SKUs, prices, handler refs)
--   2. eaiou_subscriptions       — Stripe subscription tracking
--   3. eaiou_subscription_credits — per-SKU credit balance per subscription
--   4. eaiou_orders              — every order placed (by user OR partner)
--   5. eaiou_partner_keys        — B2B partner-API auth + rate limit + wholesale flag
--   6. eaiou_marketplace_log     — append-only event log (ToS compliance audit trail)
--
-- All statements are idempotent (CREATE TABLE IF NOT EXISTS).
-- Run with: mariadb -u eaiou -p eaiou < schema/migration_007_marketplace_core.sql
--
-- Conventions:
-- * `#__` prefix substituted at install time (see migration_005 / 006).
-- * CHAR(36) for UUIDs, INT for timestamps where high-volume (Stripe meter events).
-- * idempotency_key UNIQUE per partner_key_id OR user_id to support replay-safe writes.

SET FOREIGN_KEY_CHECKS = 0;
SET NAMES utf8mb4;

-- ============================================================
-- 1. eaiou_products
-- Product catalog. Each row is one purchasable review service.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_products` (
  `sku`                       VARCHAR(64)  NOT NULL PRIMARY KEY,
  `display_name`              VARCHAR(255) NOT NULL,
  `description`               TEXT         DEFAULT NULL,
  `retail_price_cents`        INT UNSIGNED NOT NULL COMMENT 'cents, e.g. 1000 = $10.00',
  `wholesale_price_cents`     INT UNSIGNED NOT NULL COMMENT 'partner pricing (cents)',
  `latency_target_seconds`    INT UNSIGNED NOT NULL DEFAULT 30,
  `handler_module`            VARCHAR(255) NOT NULL COMMENT 'dotted path, e.g. app.services.review_handlers.scope_check',
  `active`                    TINYINT(1)   NOT NULL DEFAULT 1,
  `created_at`                TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`                TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_active (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 2. eaiou_subscriptions
-- Stripe-tier subscription rows. One per active customer plan.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_subscriptions` (
  `subscription_id`         CHAR(36)     NOT NULL PRIMARY KEY COMMENT 'eaiou-side UUID',
  `user_id`                 CHAR(36)     NOT NULL,
  `tier`                    VARCHAR(32)  NOT NULL COMMENT 'free | starter | pro | enterprise',
  `stripe_subscription_id`  VARCHAR(128) DEFAULT NULL,
  `stripe_customer_id`      VARCHAR(128) DEFAULT NULL,
  `status`                  VARCHAR(32)  NOT NULL DEFAULT 'pending' COMMENT 'pending | active | past_due | canceled',
  `current_period_start`    TIMESTAMP    NULL DEFAULT NULL,
  `current_period_end`      TIMESTAMP    NULL DEFAULT NULL,
  `created_at`              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`              TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user (`user_id`),
  INDEX idx_status (`status`),
  INDEX idx_stripe_sub (`stripe_subscription_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 3. eaiou_subscription_credits
-- Per-period credit balance for à-la-carte SKUs included in a tier.
-- e.g. "starter tier ships 5 scope_checks/month" = one row, remaining_count=5.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_subscription_credits` (
  `credit_id`        CHAR(36)     NOT NULL PRIMARY KEY,
  `subscription_id`  CHAR(36)     NOT NULL,
  `sku`              VARCHAR(64)  NOT NULL,
  `remaining_count`  INT          NOT NULL DEFAULT 0,
  `period_start`     TIMESTAMP    NOT NULL,
  `period_end`       TIMESTAMP    NOT NULL,
  `created_at`       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `updated_at`       TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_subscription (`subscription_id`),
  INDEX idx_sku (`sku`),
  INDEX idx_period (`period_end`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 4. eaiou_partner_keys
-- B2B partner integration keys. Wholesale-priced, per-key rate limit.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_partner_keys` (
  `partner_key_id`        CHAR(36)     NOT NULL PRIMARY KEY,
  `display_name`          VARCHAR(128) NOT NULL,
  `key_hash`              CHAR(64)     NOT NULL UNIQUE COMMENT 'sha256 of full secret',
  `prefix`                VARCHAR(16)  NOT NULL COMMENT 'e.g. eaiou_pk_a8f3 — visible to partner for rotation UI',
  `active`                TINYINT(1)   NOT NULL DEFAULT 1,
  `rate_limit_per_minute` INT UNSIGNED DEFAULT NULL,
  `wholesale_pricing`     TINYINT(1)   NOT NULL DEFAULT 0,
  `created_at`            TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `last_used_at`          TIMESTAMP    NULL DEFAULT NULL,
  `revoked_at`            TIMESTAMP    NULL DEFAULT NULL,
  INDEX idx_active (`active`),
  INDEX idx_prefix (`prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- 5. eaiou_orders
-- Every review order. Author OR partner-key initiated.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_orders` (
  `order_id`               CHAR(36)     NOT NULL PRIMARY KEY,
  `user_id`                CHAR(36)     DEFAULT NULL COMMENT 'set when author-initiated',
  `partner_key_id`         CHAR(36)     DEFAULT NULL COMMENT 'set when partner-initiated; mutex with user_id',
  `sku`                    VARCHAR(64)  NOT NULL,
  `manuscript_id`          CHAR(36)     DEFAULT NULL,
  `inputs_json`            LONGTEXT     NOT NULL,
  `result_json`            LONGTEXT     DEFAULT NULL,
  `status`                 VARCHAR(32)  NOT NULL DEFAULT 'pending' COMMENT 'pending | running | completed | failed | refunded',
  `iid_id`                 CHAR(36)     DEFAULT NULL COMMENT 'fk to tblintellids if/when wired',
  `amount_cents`           INT          NOT NULL,
  `via`                    VARCHAR(32)  NOT NULL COMMENT 'subscription_credit | stripe_meter | partner_key | free_trial',
  `stripe_meter_event_id`  VARCHAR(128) DEFAULT NULL,
  `idempotency_key`        VARCHAR(128) DEFAULT NULL,
  `source`                 VARCHAR(64)  DEFAULT NULL COMMENT 'manuscript_editor | api_v1 | partner_api',
  `session_id`             VARCHAR(128) DEFAULT NULL,
  `created_at`             TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  `completed_at`           TIMESTAMP    NULL DEFAULT NULL,
  `refunded_at`            TIMESTAMP    NULL DEFAULT NULL,
  INDEX idx_user (`user_id`),
  INDEX idx_partner (`partner_key_id`),
  INDEX idx_status (`status`),
  INDEX idx_sku (`sku`),
  INDEX idx_idempotency (`idempotency_key`),
  INDEX idx_created (`created_at`),
  CONSTRAINT fk_orders_sku FOREIGN KEY (`sku`) REFERENCES `#__eaiou_products`(`sku`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Idempotency replay-safety: same partner+key OR same user+key returns the existing order.
-- One unique index per actor type (user vs partner) to allow nulls cleanly in MariaDB.
CREATE UNIQUE INDEX IF NOT EXISTS `unq_orders_user_idem`
  ON `#__eaiou_orders` (`user_id`, `idempotency_key`);
CREATE UNIQUE INDEX IF NOT EXISTS `unq_orders_partner_idem`
  ON `#__eaiou_orders` (`partner_key_id`, `idempotency_key`);

-- ============================================================
-- 6. eaiou_marketplace_log
-- Append-only event log for ToS-compliance audits.
-- Records: subscription create/cancel, partner-key mint/revoke,
--          unusual order patterns, refunds, webhook receipts.
-- ============================================================
CREATE TABLE IF NOT EXISTS `#__eaiou_marketplace_log` (
  `log_id`        CHAR(36)     NOT NULL PRIMARY KEY,
  `event_type`    VARCHAR(64)  NOT NULL COMMENT 'e.g. order.created, subscription.canceled, partner_key.revoked',
  `actor_type`    VARCHAR(32)  NOT NULL COMMENT 'user | partner | admin | system | stripe_webhook',
  `actor_id`      VARCHAR(128) DEFAULT NULL,
  `entity_type`   VARCHAR(64)  DEFAULT NULL COMMENT 'order | subscription | partner_key | product',
  `entity_id`     VARCHAR(128) DEFAULT NULL,
  `payload_json`  LONGTEXT     DEFAULT NULL,
  `created_at`    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_event (`event_type`),
  INDEX idx_actor (`actor_type`, `actor_id`),
  INDEX idx_entity (`entity_type`, `entity_id`),
  INDEX idx_created (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- Verification:
-- Run after applying:
--   SHOW TABLES LIKE '#__eaiou_%' (substitute prefix as needed);
-- Expected new tables:
--   eaiou_products, eaiou_subscriptions, eaiou_subscription_credits,
--   eaiou_partner_keys, eaiou_orders, eaiou_marketplace_log
-- ============================================================
