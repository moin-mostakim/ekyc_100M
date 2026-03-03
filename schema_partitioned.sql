-- Partitioned schema for bpsca_ekyc_100M - 100M records
-- Partition key (id) included in unique keys for MySQL compliance
-- Run with: mysql -h 192.16.0.176 -P 3306 -u root -p < schema_partitioned.sql

SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS `bpsca_ekyc_100M` DEFAULT CHARACTER SET utf8mb4;
USE `bpsca_ekyc_100M`;

-- Stub tables (referenced by user_info)
CREATE TABLE IF NOT EXISTS `employee` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS `organization` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- dbs_role (referenced by user_role)
CREATE TABLE IF NOT EXISTS `dbs_role` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `parent_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- esignkyc - partitioned by KEY(id_type, id_no)
-- id_type: 1=NID, 2=Passport, 3=Driving licence, 4=Birth certificate
-- email, phone_no are NULL - fetched from contact_details
DROP TABLE IF EXISTS `esign_photos`;
DROP TABLE IF EXISTS `esignkyc`;
CREATE TABLE `esignkyc` (
  `id` bigint(20) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `id_type` bigint(20) NOT NULL DEFAULT 1 COMMENT '1=NID, 2=Passport, 3=Driving licence, 4=Birth certificate',
  `id_no` varchar(100) NOT NULL,
  `creation_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `is_delete` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_esignkyc_idtype_idno` (`id_type`, `id_no`),
  KEY `idx_esignkyc_idtype_idno` (`id_type`, `id_no`)
) ENGINE=InnoDB
PARTITION BY KEY (`id_type`, `id_no`) PARTITIONS 20;

-- user_info - partitioned
DROP TABLE IF EXISTS `contact_details`;
DROP TABLE IF EXISTS `user_role`;
DROP TABLE IF EXISTS `user_info`;
-- email, contact_number (phone) are NULL - fetched from contact_details
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
  CONSTRAINT `fk_user_esign` FOREIGN KEY (`esign_id`) REFERENCES `esignkyc` (`id`),
  CONSTRAINT `fk_user_emp` FOREIGN KEY (`emp_id`) REFERENCES `employee` (`id`),
  CONSTRAINT `fk_user_org` FOREIGN KEY (`org_id`) REFERENCES `organization` (`id`)
) ENGINE=InnoDB
PARTITION BY RANGE (`id`) (
  PARTITION p0 VALUES LESS THAN (5000001),
  PARTITION p1 VALUES LESS THAN (10000001),
  PARTITION p2 VALUES LESS THAN (15000001),
  PARTITION p3 VALUES LESS THAN (20000001),
  PARTITION p4 VALUES LESS THAN (25000001),
  PARTITION p5 VALUES LESS THAN (30000001),
  PARTITION p6 VALUES LESS THAN (35000001),
  PARTITION p7 VALUES LESS THAN (40000001),
  PARTITION p8 VALUES LESS THAN (45000001),
  PARTITION p9 VALUES LESS THAN (50000001),
  PARTITION p10 VALUES LESS THAN (55000001),
  PARTITION p11 VALUES LESS THAN (60000001),
  PARTITION p12 VALUES LESS THAN (65000001),
  PARTITION p13 VALUES LESS THAN (70000001),
  PARTITION p14 VALUES LESS THAN (75000001),
  PARTITION p15 VALUES LESS THAN (80000001),
  PARTITION p16 VALUES LESS THAN (85000001),
  PARTITION p17 VALUES LESS THAN (90000001),
  PARTITION p18 VALUES LESS THAN (95000001),
  PARTITION p19 VALUES LESS THAN (100000001),
  PARTITION p20 VALUES LESS THAN MAXVALUE
);

-- contact_details - partitioned, searchable by info (email/phone)
CREATE TABLE `contact_details` (
  `id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `contact_type` int(11) DEFAULT NULL,
  `info` varchar(255) NOT NULL,
  `creation_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_contact_info` (`id`, `info`),
  KEY `idx_contact_info` (`info`),
  KEY `idx_contact_user` (`user_id`),
  CONSTRAINT `fk_contact_user` FOREIGN KEY (`user_id`) REFERENCES `user_info` (`id`)
) ENGINE=InnoDB
PARTITION BY RANGE (`id`) (
  PARTITION p0 VALUES LESS THAN (5000001),
  PARTITION p1 VALUES LESS THAN (10000001),
  PARTITION p2 VALUES LESS THAN (15000001),
  PARTITION p3 VALUES LESS THAN (20000001),
  PARTITION p4 VALUES LESS THAN (25000001),
  PARTITION p5 VALUES LESS THAN (30000001),
  PARTITION p6 VALUES LESS THAN (35000001),
  PARTITION p7 VALUES LESS THAN (40000001),
  PARTITION p8 VALUES LESS THAN (45000001),
  PARTITION p9 VALUES LESS THAN (50000001),
  PARTITION p10 VALUES LESS THAN (55000001),
  PARTITION p11 VALUES LESS THAN (60000001),
  PARTITION p12 VALUES LESS THAN (65000001),
  PARTITION p13 VALUES LESS THAN (70000001),
  PARTITION p14 VALUES LESS THAN (75000001),
  PARTITION p15 VALUES LESS THAN (80000001),
  PARTITION p16 VALUES LESS THAN (85000001),
  PARTITION p17 VALUES LESS THAN (90000001),
  PARTITION p18 VALUES LESS THAN (95000001),
  PARTITION p19 VALUES LESS THAN (100000001),
  PARTITION p20 VALUES LESS THAN MAXVALUE
);

-- Seed required FK rows
INSERT IGNORE INTO `employee` (`id`) VALUES (1);
INSERT IGNORE INTO `organization` (`id`) VALUES (1);
INSERT IGNORE INTO `dbs_role` (`id`, `name`) VALUES (1, 'user');

SET FOREIGN_KEY_CHECKS = 1;
