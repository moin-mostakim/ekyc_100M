"""
Revert/truncate 100M data from bpsca_ekyc_100M tables.
Preserves schema and stub data (employee, organization, dbs_role).
"""

import sys

try:
    import pymysql
except ImportError:
    print("Install: pip install pymysql")
    sys.exit(1)

from config import DB_CONFIG


def main():
    cnxn = pymysql.connect(**DB_CONFIG)
    cur = cnxn.cursor()

    tables = ["contact_details", "user_info", "esignkyc"]

    try:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in tables:
            cur.execute(f"TRUNCATE TABLE `{t}`")
            print(f"Truncated {t}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        cnxn.commit()
        print("Revert complete.")
    except Exception as e:
        cnxn.rollback()
        print(f"Error: {e}")
    finally:
        cur.close()
        cnxn.close()


if __name__ == "__main__":
    main()
