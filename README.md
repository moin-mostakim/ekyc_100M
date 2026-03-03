# bpsca_ekyc_100M - 100M Insert & Search Benchmark

Insert 100M records into partitioned MySQL tables with contact search by email/phone.

## Setup

1. Edit `config.py`: set `user`, `password` for MySQL.
2. Create schema:

```bash
mysql -h 192.16.0.176 -P 3306 -u root -p < schema_partitioned.sql
```

3. Install deps:

```bash
pip install -r requirements.txt
```

## Scripts

| Script | Description |
|--------|-------------|
| `insert_100m.py` | Insert up to 100M records. Usage: `python insert_100m.py [limit]` (default 100M) |
| `revert_100m.py` | Truncate contact_details, user_info, esignkyc |
| `search_contact.py` | Search by email/phone: `python search_contact.py email` or `python search_contact.py phone [value]` |
| `benchmark_timing.py` | Insert 1M→5M→10M→25M→50M→100M, measure search time at each step |

## NID Rules

NID is 10, 13, or 17 digits only.

## Partitioning

`schema_partitioned.sql` uses RANGE partitioning on `id` for esignkyc, user_info, contact_details (20 partitions of 5M rows each). Search uses `idx_contact_info` on `info`. To compare with non-partitioned tables, run `schema.sql` (original) and measure search time separately.
