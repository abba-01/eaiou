-- Migration 006: RS (Research State) tags for papers
-- Author-applied, bottom-up signals indexed for discovery.
-- Vocabulary defined in SSOT Section 7.

CREATE TABLE IF NOT EXISTS `#__eaiou_paper_tags` (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    paper_id     INT UNSIGNED NOT NULL,
    tag          VARCHAR(64)  NOT NULL,
    subtype      VARCHAR(64)  DEFAULT NULL,
    visibility   ENUM('public','reviewers','editorial','private') NOT NULL DEFAULT 'public',
    tag_resolved TINYINT(1)   NOT NULL DEFAULT 0,
    notes        TEXT         DEFAULT NULL,
    created_at   DATETIME     NOT NULL,
    created_by   INT UNSIGNED DEFAULT NULL,
    resolved_at  DATETIME     DEFAULT NULL,
    FOREIGN KEY (paper_id) REFERENCES `#__eaiou_papers`(id) ON DELETE CASCADE,
    INDEX idx_tag (tag),
    INDEX idx_paper_id (paper_id),
    INDEX idx_resolved (tag_resolved),
    INDEX idx_visibility (visibility)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
