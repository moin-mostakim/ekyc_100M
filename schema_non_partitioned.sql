-- Non-partitioned schema for A/B comparison (search timing)
-- Same structure as partitioned but without PARTITION BY
-- Use this to compare query performance: partitioned vs non-partitioned

SET FOREIGN_KEY_CHECKS = 0;
CREATE DATABASE IF NOT EXISTS `bpsca_ekyc_100M` DEFAULT CHARACTER SET utf8mb4;
USE `bpsca_ekyc_100M`;

CREATE TABLE IF NOT EXISTS `employee` (`id` bigint(20) NOT NULL AUTO_INCREMENT, PRIMARY KEY (`id`)) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS `organization` (`id` bigint(20) NOT NULL AUTO_INCREMENT, PRIMARY KEY (`id`)) ENGINE=InnoDB;
INSERT IGNORE INTO `employee` (`id`) VALUES (1);
INSERT IGNORE INTO `organization` (`id`) VALUES (1);

DROP TABLE IF EXISTS `contact_details`;
DROP TABLE IF EXISTS `user_info`;
DROP TABLE IF EXISTS `esignkyc`;

-- esignkyc: email, phone_no omitted - fetched from contact_details
CREATE TABLE `esignkyc` (
  `id` bigint(20) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `id_type` bigint(20) NOT NULL DEFAULT 1 COMMENT '1=NID, 2=Passport, 3=Driving licence, 4=Birth certificate',
  `id_no` varchar(100) NOT NULL,
  `creation_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_idtype_idno` (`id_type`, `id_no`),
  KEY `idx_idtype_idno` (`id_type`, `id_no`)
) ENGINE=InnoDB;

-- user_info: email, contact_number omitted - fetched from contact_details
CREATE TABLE `user_info` (
  `id` bigint(20) NOT NULL,
  `esign_id` bigint(20) NOT NULL,
  `emp_id` bigint(20) DEFAULT 1,
  `org_id` bigint(20) DEFAULT 1,
  `nid` varchar(17) DEFAULT NULL,
  `user_name` varchar(100) DEFAULT NULL,
  `created_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_esign` (`esign_id`),
  KEY `idx_user_nid` (`nid`),
  FOREIGN KEY (`esign_id`) REFERENCES `esignkyc` (`id`),
  FOREIGN KEY (`emp_id`) REFERENCES `employee` (`id`),
  FOREIGN KEY (`org_id`) REFERENCES `organization` (`id`)
) ENGINE=InnoDB;

-- contact_details: single source for email/phone search
CREATE TABLE `contact_details` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `contact_type` int(11) DEFAULT NULL COMMENT '1=email, 2=phone',
  `info` varchar(255) NOT NULL,
  `creation_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_info` (`info`),
  KEY `idx_contact_info` (`info`),
  KEY `idx_contact_user` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;
