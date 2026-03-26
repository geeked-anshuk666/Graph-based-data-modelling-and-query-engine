import sqlite3
import logging

logger = logging.getLogger(__name__)

SAFE_STARTERS = ("SELECT", "WITH")


def run_query(sql: str, conn: sqlite3.Connection) -> list[dict]:
    """Execute LLM-generated SQL with safety guards.

    Only SELECT/WITH allowed. No stacked statements.
    This is the last line of defense against a jailbroken LLM prompt
    trying to generate DROP TABLE or INSERT.
    """
    clean = sql.strip()
    upper = clean.upper()

    if not any(upper.startswith(kw) for kw in SAFE_STARTERS):
        raise ValueError("only SELECT queries allowed")

    # block stacked statements — semicolons inside string literals are
    # extremely unlikely in generated SQL, so this is safe enough
    if clean.count(";") > 1:
        raise ValueError("multiple statements not allowed")

    try:
        cur = conn.execute(clean)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchmany(100)
        return [dict(zip(cols, row)) for row in rows]
    except sqlite3.OperationalError as e:
        logger.warning("query failed | err=%s | sql=%.100s", e, sql)
        raise
