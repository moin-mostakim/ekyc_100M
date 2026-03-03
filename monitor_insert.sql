-- Monitor 100M insert progress
-- Run: mysql -h 192.16.0.176 -P 3306 -u root -p bpsca_ekyc_100M < monitor_insert.sql
-- Or execute in HeidiSQL / MySQL Workbench

USE bpsca_ekyc_100M;

-- Row counts per table (target: esignkyc 100M, user_info 100M, contact_details 200M)
SELECT
  (SELECT COUNT(*) FROM esignkyc)   AS esignkyc_rows,
  (SELECT COUNT(*) FROM user_info)  AS user_info_rows,
  (SELECT COUNT(*) FROM contact_details) AS contact_details_rows,
  ROUND((SELECT COUNT(*) FROM esignkyc) / 1000000, 2) AS esignkyc_pct_of_100M;

-- Last inserted IDs (shows progress)
SELECT
  COALESCE((SELECT MAX(id) FROM esignkyc), 0)     AS last_esignkyc_id,
  COALESCE((SELECT MAX(id) FROM user_info), 0)    AS last_user_info_id,
  COALESCE((SELECT MAX(id) FROM contact_details), 0) AS last_contact_details_id;
