"""
Full search on contact_details by email or phone number.
"""

import sys
import time

try:
    import pymysql
except ImportError:
    print("Install: pip install pymysql")
    sys.exit(1)

from config import DB_CONFIG


def search(cnxn, query: str, value: str) -> list:
    cur = cnxn.cursor(pymysql.cursors.DictCursor)
    cur.execute(query, (value,))
    rows = cur.fetchall()
    cur.close()
    return rows


def main():
    if len(sys.argv) < 2:
        print("Usage: python search_contact.py <email|phone> [value]")
        print("  email: search by info (email)")
        print("  phone: search by info (phone)")
        print("  If value omitted, runs sample search.")
        sys.exit(1)

    search_type = sys.argv[1].lower()
    value = sys.argv[2] if len(sys.argv) > 2 else None

    cnxn = pymysql.connect(**DB_CONFIG)

    if search_type == "email":
        q = "SELECT id, user_id, contact_type, info, creation_date FROM contact_details WHERE info = %s"
        if not value:
            cur = cnxn.cursor()
            cur.execute("SELECT info FROM contact_details WHERE contact_type = 1 LIMIT 1")
            row = cur.fetchone()
            cur.close()
            value = row[0] if row else "user1@ekyc1.bd"
        print(f"Searching email: {value}")
    elif search_type == "phone":
        q = "SELECT id, user_id, contact_type, info, creation_date FROM contact_details WHERE info = %s"
        if not value:
            cur = cnxn.cursor()
            cur.execute("SELECT info FROM contact_details WHERE contact_type = 2 LIMIT 1")
            row = cur.fetchone()
            cur.close()
            value = row[0] if row else None
        if not value:
            print("No phone in DB. Use: python search_contact.py phone 01512345678")
            cnxn.close()
            sys.exit(1)
        print(f"Searching phone: {value}")
    else:
        print("Use 'email' or 'phone'")
        cnxn.close()
        sys.exit(1)

    t0 = time.perf_counter()
    rows = search(cnxn, q, value)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    print(f"Found {len(rows)} row(s) in {elapsed_ms:.2f} ms")
    for r in rows:
        print(r)

    cnxn.close()


if __name__ == "__main__":
    main()
