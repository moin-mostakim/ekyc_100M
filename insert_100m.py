"""
Insert 100M records into bpsca_ekyc_100M tables (partitioned).
Parallel workers, resume from last stop. NID: 10, 13, or 17 digits only.
Logs to insert_log.txt and stdout.
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

LOG_FILE = "insert_log.txt"


def log(msg: str):
    """Print and append to log file with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass

try:
    import pymysql
except ImportError:
    print("Install: pip install pymysql")
    sys.exit(1)

from config import (
    DB_CONFIG,
    TOTAL_RECORDS,
    BATCH_SIZE,
    NUM_WORKERS,
    VALID_NID_LENGTHS,
)


def gen_nid(eid: int) -> str:
    """Generate unique NID per eid, 10/13/17 digits. id_type=1 (NID) requires unique id_no."""
    length = VALID_NID_LENGTHS[eid % 3]
    base = 10 ** (length - 1)
    return str(base + (eid % (10**length - base)))


def gen_phone(eid: int) -> str:
    return f"01{5 + (eid % 5)}{eid % 100000000:08d}"


def gen_email(eid: int) -> str:
    return f"user{eid}@ekyc{(eid % 10000)}.bd"


def _worker_insert(args):
    """Worker: insert range [start_id, end_id). Returns (worker_id, rows, elapsed_sec)."""
    start_id, end_id, worker_id, db_config, batch_size = args
    start_time = datetime.now()
    rows_done = 0

    cnxn = pymysql.connect(**db_config)
    cur = cnxn.cursor()

    try:
        for batch_start in range(start_id, end_id, batch_size):
            batch_end = min(batch_start + batch_size, end_id)
            ids = list(range(batch_start, batch_end))

            esignkyc_rows = []
            user_info_rows = []
            contact_rows = []

            for eid in ids:
                nid = gen_nid(eid)
                phone = gen_phone(eid)
                email = gen_email(eid)
                contact_rows.append((eid * 2 - 1, eid, 1, email))
                contact_rows.append((eid * 2, eid, 2, phone))
                esignkyc_rows.append((eid, f"User {eid}", 1, nid))
                user_info_rows.append((eid, eid, 1, 1, nid, f"user_{eid}"))

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
            rows_done += len(ids)

    finally:
        cur.close()
        cnxn.close()

    elapsed = (datetime.now() - start_time).total_seconds()
    return (worker_id, rows_done, elapsed)


def get_resume_start_id(cnxn) -> int:
    """Return next id to insert. 1 if empty."""
    cur = cnxn.cursor()
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM esignkyc")
    m1 = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM user_info")
    m2 = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(MAX(id), 0) FROM contact_details")
    m3 = cur.fetchone()[0]
    cur.close()
    last_user_contact = (m3 + 1) // 2
    last_complete = min(m1, m2, last_user_contact)
    return last_complete + 1


def run_parallel(start_id: int, end_id: int, limit: int):
    """Run parallel insert from start_id to min(end_id, limit)."""
    end_id = min(end_id, limit + 1)
    total = end_id - start_id
    if total <= 0:
        log("Nothing to insert (already complete).")
        return

    chunk = max(1, (end_id - start_id) // NUM_WORKERS)
    chunks = []
    s = start_id
    for i in range(NUM_WORKERS):
        e = min(s + chunk, end_id)
        if s < e:
            chunks.append((s, e, i, DB_CONFIG, BATCH_SIZE))
        s = e

    if not chunks:
        log("Nothing to insert.")
        return

    log(f"Starting {len(chunks)} workers for {total:,} rows")

    start_time = datetime.now()
    done = 0

    with ThreadPoolExecutor(max_workers=len(chunks)) as ex:
        futures = {ex.submit(_worker_insert, c): c[2] for c in chunks}
        for fut in as_completed(futures):
            wid, rows, elapsed = fut.result()
            done += rows
            pct = 100 * done / total if total else 0
            log(f"  Worker {wid} done: {rows:,} rows ({elapsed:.1f}s) | Total: {done:,} / {total:,} ({pct:.1f}%)")

    elapsed = datetime.now() - start_time
    rate = done / elapsed.total_seconds() if elapsed.total_seconds() else 0
    log(f"Done. Inserted {done:,} in {elapsed} ({rate:,.0f} rows/s)")


def run_single(cnxn, cur, start_id: int, limit: int):
    """Single-thread insert from start_id to limit."""
    start_time = datetime.now()
    for batch_start in range(start_id, limit + 1, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, limit + 1)
        ids = list(range(batch_start, batch_end))

        esignkyc_rows = []
        user_info_rows = []
        contact_rows = []

        for eid in ids:
            nid = gen_nid(eid)
            phone = gen_phone(eid)
            email = gen_email(eid)
            contact_rows.append((eid * 2 - 1, eid, 1, email))
            contact_rows.append((eid * 2, eid, 2, phone))
            esignkyc_rows.append((eid, f"User {eid}", 1, nid))
            user_info_rows.append((eid, eid, 1, 1, nid, f"user_{eid}"))

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

        if batch_end % 100_000 == 0 or batch_end > limit:
            log(f"  {batch_end - 1:,} rows in {datetime.now() - start_time}")

    log(f"Done. Total: {datetime.now() - start_time}")


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else TOTAL_RECORDS
    use_parallel = "--sequential" not in sys.argv and NUM_WORKERS > 1

    cnxn = pymysql.connect(**DB_CONFIG)
    start_id = get_resume_start_id(cnxn)
    cnxn.close()

    if start_id > limit:
        log(f"Already complete. esignkyc max id >= {limit}. Nothing to insert.")
        return

    remaining = limit - start_id + 1
    log(f"Inserting from id {start_id:,} to {limit:,} ({remaining:,} records) | Workers: {NUM_WORKERS} | Batch: {BATCH_SIZE:,}")
    if start_id > 1:
        log("(Resuming from previous run)")

    if use_parallel:
        run_parallel(start_id, limit + 1, limit)
    else:
        log("Running in sequential mode")
        cnxn = pymysql.connect(**DB_CONFIG)
        cur = cnxn.cursor()
        try:
            run_single(cnxn, cur, start_id, limit)
        finally:
            cur.close()
            cnxn.close()


if __name__ == "__main__":
    main()
