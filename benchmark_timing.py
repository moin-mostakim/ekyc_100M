"""
Benchmark: Insert data gradually (1M, 5M, 10M, ... 100M) and measure search time.
Outputs a comparison table of query timing vs data size.
"""

import sys
import time
from datetime import datetime

try:
    import pymysql
except ImportError:
    print("Install: pip install pymysql")
    sys.exit(1)

from config import DB_CONFIG, BATCH_SIZE, VALID_NID_LENGTHS

# Milestones for gradual insert
MILESTONES = [1_000_000, 5_000_000, 10_000_000, 25_000_000, 50_000_000, 100_000_000]


def gen_nid(eid: int) -> str:
    """Unique NID per eid, 10/13/17 digits for id_type=1."""
    length = VALID_NID_LENGTHS[eid % 3]
    base = 10 ** (length - 1)
    return str(base + (eid % (10**length - base)))


def gen_phone(eid: int) -> str:
    return f"01{5 + (eid % 5)}{eid % 100000000:08d}"


def gen_email(eid: int) -> str:
    return f"user{eid}@ekyc{(eid % 10000)}.bd"


def insert_batch(cnxn, cur, start_id: int, count: int):
    ids = list(range(start_id, start_id + count))
    esignkyc_rows = []
    user_info_rows = []
    contact_rows = []

    for i, eid in enumerate(ids):
        nid = gen_nid(eid)
        phone = gen_phone(eid)
        email = gen_email(eid)
        esignkyc_rows.append((eid, f"User {eid}", 1, nid))
        user_info_rows.append((eid, eid, 1, 1, nid, f"user_{eid}"))
        contact_rows.append((eid * 2 - 1, eid, 1, email))
        contact_rows.append((eid * 2, eid, 2, phone))

    cur.executemany(
        "INSERT IGNORE INTO esignkyc (id, name, id_type, id_no) VALUES (%s,%s,%s,%s)",
        esignkyc_rows,
    )
    cur.executemany(
        "INSERT IGNORE INTO user_info (id, esign_id, emp_id, org_id, nid, user_name) VALUES (%s,%s,%s,%s,%s,%s)",
        user_info_rows,
    )
    cur.executemany(
        "INSERT IGNORE INTO contact_details (id, user_id, contact_type, info) VALUES (%s,%s,%s,%s)",
        contact_rows,
    )
    cnxn.commit()


def get_search_target(cnxn) -> str:
    cur = cnxn.cursor()
    cur.execute("SELECT info FROM contact_details WHERE contact_type = 1 ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    return row[0] if row else "user1@ekyc1.bd"


def measure_search_ms(cnxn, value: str) -> float:
    cur = cnxn.cursor()
    q = "SELECT id, user_id, info FROM contact_details WHERE info = %s"
    t0 = time.perf_counter()
    cur.execute(q, (value,))
    cur.fetchall()
    return (time.perf_counter() - t0) * 1000


def run_benchmark(revert_first: bool = True):
    cnxn = pymysql.connect(**DB_CONFIG)
    cur = cnxn.cursor()

    if revert_first:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for t in ["contact_details", "user_info", "esignkyc"]:
            cur.execute(f"TRUNCATE TABLE `{t}`")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
        cnxn.commit()
        print("Reverted existing data.\n")

    results = []
    next_id = 1

    for target in MILESTONES:
        to_insert = target - (next_id - 1)
        if to_insert <= 0:
            search_val = get_search_target(cnxn)
            ms = measure_search_ms(cnxn, search_val)
            results.append((target, ms))
            print(f"  {target:>12,} rows -> search {ms:.2f} ms")
            continue

        print(f"Inserting up to {target:,}...", end=" ")
        t0 = datetime.now()
        while next_id <= target:
            batch = min(BATCH_SIZE, target - next_id + 1)
            insert_batch(cnxn, cur, next_id, batch)
            next_id += batch
        elapsed = (datetime.now() - t0).total_seconds()
        print(f"{elapsed:.1f}s")

        search_val = get_search_target(cnxn)
        ms = measure_search_ms(cnxn, search_val)
        results.append((target, ms))
        print(f"  Search time: {ms:.2f} ms\n")

    cur.close()
    cnxn.close()

    # Print comparison table
    print("\n" + "=" * 55)
    print("TIMING COMPARISON: Search by Email/Phone (contact_details)")
    print("=" * 55)
    print(f"{'Rows':>15} | {'Search (ms)':>12} | {'vs 1M':>10}")
    print("-" * 55)
    base_ms = results[0][1] if results else 1
    for rows, ms in results:
        ratio = f"{ms / base_ms:.2f}x" if base_ms else "-"
        print(f"{rows:>15,} | {ms:>12.2f} | {ratio:>10}")
    print("=" * 55)

    return results


if __name__ == "__main__":
    revert = "--no-revert" not in sys.argv
    run_benchmark(revert_first=revert)
