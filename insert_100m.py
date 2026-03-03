"""
Insert 100M records into bpsca_ekyc_100M tables (partitioned).
NID: 10, 13, or 17 digits only.
"""

import sys
from datetime import datetime

try:
    import pymysql
except ImportError:
    print("Install: pip install pymysql")
    sys.exit(1)

from config import DB_CONFIG, TOTAL_RECORDS, BATCH_SIZE, VALID_NID_LENGTHS


def gen_nid(eid: int) -> str:
    """Generate unique NID per eid, 10/13/17 digits. id_type=1 (NID) requires unique id_no."""
    length = VALID_NID_LENGTHS[eid % 3]
    base = 10 ** (length - 1)
    return str(base + (eid % (10**length - base)))


def gen_phone(eid: int) -> str:
    return f"01{5 + (eid % 5)}{eid % 100000000:08d}"


def gen_email(eid: int) -> str:
    return f"user{eid}@ekyc{(eid % 10000)}.bd"


def run(cnxn, cur, limit: int = TOTAL_RECORDS):
    start = datetime.now()
    print(f"Inserting {limit:,} records (batch={BATCH_SIZE:,})...")

    for batch_start in range(1, limit + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, limit + 1)
        ids = list(range(batch_start, batch_end))

        esignkyc_rows = []
        user_info_rows = []
        contact_rows = []

        for i, eid in enumerate(ids):
            nid = gen_nid(eid)
            phone = gen_phone(eid)
            email = gen_email(eid)
            contact_type_1, contact_type_2 = 1, 2
            contact_rows.append((eid * 2 - 1, eid, contact_type_1, email))
            contact_rows.append((eid * 2, eid, contact_type_2, phone))

            esignkyc_rows.append((eid, f"User {eid}", 1, nid))
            user_info_rows.append((eid, eid, 1, 1, nid, f"user_{eid}"))

        esign_sql = "INSERT IGNORE INTO esignkyc (id, name, id_type, id_no) VALUES (%s,%s,%s,%s)"
        user_sql = "INSERT IGNORE INTO user_info (id, esign_id, emp_id, org_id, nid, user_name) VALUES (%s,%s,%s,%s,%s,%s)"
        contact_sql = "INSERT IGNORE INTO contact_details (id, user_id, contact_type, info) VALUES (%s,%s,%s,%s)"

        cur.executemany(esign_sql, esignkyc_rows)
        cur.executemany(user_sql, user_info_rows)
        cur.executemany(contact_sql, contact_rows)
        cnxn.commit()

        if batch_end % 100_000 == 0 or batch_end > limit:
            print(f"  {batch_end - 1:,} rows in {datetime.now() - start}")

    elapsed = datetime.now() - start
    print(f"Done. Total: {elapsed}")


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else TOTAL_RECORDS
    cnxn = pymysql.connect(**DB_CONFIG)
    cur = cnxn.cursor()
    try:
        run(cnxn, cur, limit)
    finally:
        cur.close()
        cnxn.close()


if __name__ == "__main__":
    main()
