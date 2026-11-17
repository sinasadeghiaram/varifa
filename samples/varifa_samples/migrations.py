"""Migration-first start-up.

Varifa installs on many independent machines, each with its own PostgreSQL
database. Instead of shipping upgrade scripts, the app applies any pending
schema migrations every time it starts, so an install that skipped several
versions still ends up with the full, current schema.

Rules this runner enforces:

* Files are named ``NNNN_short_description.sql`` and applied in order.
* Each migration runs in its own transaction and is recorded only on success.
* A migration that was already applied must never change afterwards; if its
  checksum differs, start-up stops instead of silently diverging.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

_FILENAME = re.compile(r"^(\d{4})_[a-z0-9_]+\.sql$")


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str

    @property
    def checksum(self) -> str:
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def discover(directory: Path) -> list[Migration]:
    """Read and order all migration files in ``directory``."""
    found: dict[int, Migration] = {}
    for path in sorted(Path(directory).glob("*.sql")):
        match = _FILENAME.match(path.name)
        if not match:
            raise MigrationError(f"Badly named migration file: {path.name}")
        version = int(match.group(1))
        if version in found:
            raise MigrationError(
                f"Duplicate migration version {version}: {found[version].name} and {path.name}"
            )
        found[version] = Migration(version, path.name, path.read_text(encoding="utf-8"))
    return [found[v] for v in sorted(found)]


def _default_run_sql(cursor, sql: str) -> None:
    cursor.execute(sql)  # psycopg2 accepts several statements in one call


def apply_pending(
    conn,
    directory: Path,
    *,
    placeholder: str = "%s",
    run_sql: Callable[[object, str], None] = _default_run_sql,
) -> list[str]:
    """Apply every migration not yet recorded; return the names applied.

    ``conn`` is any DB-API connection. ``placeholder`` is its parameter style
    (``%s`` for psycopg2, ``?`` for sqlite3).
    """
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        " version INTEGER PRIMARY KEY,"
        " name TEXT NOT NULL,"
        " checksum TEXT NOT NULL,"
        " applied_at TEXT NOT NULL)"
    )
    conn.commit()

    cur.execute("SELECT version, checksum FROM schema_migrations")
    applied = dict(cur.fetchall())

    newly_applied: list[str] = []
    for migration in discover(directory):
        recorded = applied.get(migration.version)
        if recorded is not None:
            if recorded != migration.checksum:
                raise MigrationError(
                    f"{migration.name} was changed after it was applied; "
                    "add a new migration instead of editing an old one"
                )
            continue

        try:
            run_sql(cur, migration.sql)
            cur.execute(
                "INSERT INTO schema_migrations (version, name, checksum, applied_at) "
                f"VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})",
                (
                    migration.version,
                    migration.name,
                    migration.checksum,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise MigrationError(f"{migration.name} failed: {exc}") from exc
        newly_applied.append(migration.name)

    return newly_applied
