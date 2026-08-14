"""Tests for database.run_migrations() -- the Alembic-backed schema
provisioning path wired into api/main.py's real lifespan(). Previously the
live uvicorn entrypoint ran no schema setup at all (database.create_tables()
was only ever reachable from the separate, production-unused app.py/startup.py
CLI path); see migrations/ + database.py::run_migrations().
"""

import sqlite3

import database


def _table_names(db_path) -> set[str]:
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'alembic_version'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        con.close()


class TestRunMigrations:
    def test_upgrade_creates_all_orm_tables(self, tmp_path, monkeypatch):
        db_path = tmp_path / "migration_test.db"
        monkeypatch.setattr("config.DATABASE_URL", f"sqlite:///{db_path}")

        database.run_migrations()

        expected = set(database.Base.metadata.tables.keys())
        assert _table_names(db_path) == expected

    def test_upgrade_is_idempotent(self, tmp_path, monkeypatch):
        db_path = tmp_path / "migration_test_idempotent.db"
        monkeypatch.setattr("config.DATABASE_URL", f"sqlite:///{db_path}")

        database.run_migrations()
        database.run_migrations()  # second call must be a safe no-op

        expected = set(database.Base.metadata.tables.keys())
        assert _table_names(db_path) == expected
