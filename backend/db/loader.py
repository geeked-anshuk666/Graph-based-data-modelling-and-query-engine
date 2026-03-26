"""Load SAP O2C JSONL files into SQLite.

Handles multi-part files (globs *.jsonl per entity folder).
Converts camelCase JSONL keys to snake_case column names.
"""
import json
import logging
import re
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# camelCase → snake_case
_camel_re = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _to_snake(name: str) -> str:
    return _camel_re.sub("_", name).lower()


def _read_jsonl(folder: Path) -> list[dict]:
    """Read all .jsonl part files in a folder, concat the rows."""
    rows = []
    for f in sorted(folder.glob("*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    return rows


# map from folder name → table name
# most are 1:1 except these two which have longer folder names
TABLE_MAP = {
    "journal_entry_items_accounts_receivable": "journal_entry_items",
    "payments_accounts_receivable": "payments",
}


def _table_name(folder_name: str) -> str:
    return TABLE_MAP.get(folder_name, folder_name)


def _flatten_val(v):
    """SQLite can't bind dicts or lists — serialize them."""
    if isinstance(v, (dict, list)):
        return json.dumps(v)
    return v


def _insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict]):
    if not rows:
        return 0

    # get actual table columns from SQLite schema
    cursor = conn.execute(f"PRAGMA table_info({table})")
    table_cols = {row[1] for row in cursor.fetchall()}

    # convert keys to snake_case, flatten nested values
    converted = [
        {_to_snake(k): _flatten_val(v) for k, v in row.items()}
        for row in rows
    ]

    # only insert columns that exist in the table — silently drop extras
    # (the JSONL may have fields we deliberately excluded from the schema)
    cols = [c for c in converted[0].keys() if c in table_cols]
    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(cols)
    sql = f"INSERT OR IGNORE INTO {table} ({col_names}) VALUES ({placeholders})"

    conn.executemany(sql, [tuple(r.get(c) for c in cols) for r in converted])
    return len(converted)


def load_all(data_dir: Path, db_path: Path):
    """Main entry point: create schema, load all entities from JSONL."""
    if db_path.exists():
        # if file exists, check if it actually has data (schema tables)
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales_order_headers'")
            found = cursor.fetchone()
            conn.close()
            if found:
                logger.info("database with data already exists at %s, skipping load", db_path)
                return
        except Exception:
            pass

    schema_path = Path(__file__).parent / "schema.sql"
    conn = sqlite3.connect(str(db_path))

    logger.info("creating schema...")
    conn.executescript(schema_path.read_text())

    entity_dirs = sorted(
        d for d in data_dir.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    )

    total = 0
    for entity_dir in entity_dirs:
        table = _table_name(entity_dir.name)
        rows = _read_jsonl(entity_dir)
        count = _insert_rows(conn, table, rows)
        total += count
        logger.info("loaded %d rows into %s", count, table)

    conn.commit()
    conn.close()
    logger.info("done — %d total rows loaded into %s", total, db_path)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    # allow running with custom paths: python loader.py [data_dir] [db_path]
    from config import settings
    data = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(settings.data_dir)
    db = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(settings.db_path)
    load_all(data, db)
