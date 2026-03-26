import sqlite3
import pathlib

print("Scanning for all o2c.db files:")
for path in pathlib.Path('.').rglob('o2c.db'):
    conn = sqlite3.connect(str(path))
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    print(f"File: {path}")
    print(f"Tables: {tables}")
    if 'sales_order_headers' in tables:
        count = conn.execute("SELECT COUNT(*) FROM sales_order_headers").fetchone()[0]
        print(f"  sales_order_headers rows: {count}")
    print("---")
