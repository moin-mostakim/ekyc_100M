"""Database configuration for bpsca_ekyc_100M project. Copy to config.py and set values."""

DB_CONFIG = {
    "host": "192.16.0.176",
    "port": 3306,
    "database": "bpsca_ekyc_100M",
    "user": "root",
    "password": "",  # Set your password
    "charset": "utf8mb4",
    "autocommit": False,
}

TOTAL_RECORDS = 100_000_000
BATCH_SIZE = 5_000
VALID_NID_LENGTHS = (10, 13, 17)
