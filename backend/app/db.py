"""Postgres connection management.

Raw SQL by design - no ORM. You are designing the schema yourself, and an ORM
would hide the joins you need to be able to explain in an interview.

Usage:
    from app.db import connection, query

    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")

    rows = query("SELECT * FROM buildings WHERE name = %s", ("Siebel Center for Comp Sci",))
"""

from contextlib import contextmanager
from typing import Any, Iterator, Sequence

import psycopg
from psycopg.rows import dict_row

from app.config import require_database_url


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    """Open a connection, commit on clean exit, roll back on exception."""
    conn = psycopg.connect(require_database_url(), row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query(sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
    """Run a SELECT and return all rows as dicts."""
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def execute(sql: str, params: Sequence[Any] = ()) -> int:
    """Run a write. Returns affected row count."""
    with connection() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def execute_many(sql: str, rows: Sequence[Sequence[Any]]) -> None:
    """Bulk write - one transaction for all rows."""
    with connection() as conn, conn.cursor() as cur:
        cur.executemany(sql, rows)


def apply_migrations() -> None:
    """Run every .sql file in backend/migrations/ in filename order.

    Deliberately dumb: no migration-state tracking. Your migrations should be
    idempotent (CREATE TABLE IF NOT EXISTS ...) so re-running is harmless.
    Swap this for Alembic later if the schema starts churning.
    """
    from pathlib import Path

    migrations_dir = Path(__file__).resolve().parents[1] / "migrations"
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        print("no migration files found")
        return

    with connection() as conn, conn.cursor() as cur:
        for path in files:
            sql = path.read_text(encoding="utf-8").strip()
            if not sql:
                print(f"  skip {path.name} (empty)")
                continue
            print(f"  apply {path.name}")
            cur.execute(sql)
    print("migrations applied")
