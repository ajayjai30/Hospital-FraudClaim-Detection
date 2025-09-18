CREATE DATABASE IF NOT EXISTS claim_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE claim_db;

CREATE TABLE IF NOT EXISTS claims (
  id INT AUTO_INCREMENT PRIMARY KEY,
  claim_amount DECIMAL(12,2) NOT NULL,
  policy_coverage DECIMAL(12,2),
  policy_start DATE,
  claim_date DATE,
  incident_date DATE,
  incident_location VARCHAR(255),
  previous_claims INT DEFAULT 0,
  provider_id VARCHAR(128),
  risk_score INT DEFAULT NULL,
  risk_label VARCHAR(32) DEFAULT NULL,
  model_output JSON DEFAULT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
