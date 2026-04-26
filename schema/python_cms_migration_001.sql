-- eaiou Python CMS — Migration 001
-- Purpose: Extend #__eaiou_papers for standalone Python CMS operation
--          (no Joomla #__content dependency)
-- Run after: eaiou_install_canonical.sql

-- Make Joomla-legacy fields nullable (no Joomla in Python CMS)
ALTER TABLE `#__eaiou_papers`
  MODIFY `article_id`   INT NULL COMMENT 'joomla #__content.id — NULL in Python CMS',
  MODIFY `created_by`   INT NULL;

-- Add Python CMS paper content columns
ALTER TABLE `#__eaiou_papers`
  ADD COLUMN IF NOT EXISTS `title`                VARCHAR(1000) DEFAULT NULL AFTER `article_id`,
  ADD COLUMN IF NOT EXISTS `abstract`             LONGTEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `author_name`          VARCHAR(255) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `orcid`                VARCHAR(50) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `keywords`             TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `ai_disclosure_level`  ENUM('none','editing','analysis','drafting','collaborative') DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `ai_disclosure_notes`  TEXT DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `submitted_at`         DATETIME DEFAULT NULL COMMENT 'alias for submission_sealed_at in Python CMS',
  ADD COLUMN IF NOT EXISTS `q_overall`            DECIMAL(7,4) DEFAULT NULL COMMENT 'alias for q_signal in Python CMS';
