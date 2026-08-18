"""Tests for database.run_migrations() -- the Alembic-backed schema
provisioning path wired into api/main.py's real lifespan(). Previously the
live uvicorn entrypoint ran no schema setup at all (database.create_tables()
was only ever reachable from the separate, production-unused app.py/startup.py
CLI path); see migrations/ + database.py::run_migrations().
"""

import logging
import sqlite3
from logging.handlers import RotatingFileHandler

import pytest

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


class TestRunMigrationsLoggingInteraction:
    """Regression coverage for api/main.py's lifespan() call order.

    migrations/env.py's fileConfig(disable_existing_loggers=False) still
    replaces the root logger's *handler list* with alembic.ini's
    [logger_root] handlers=console -- disable_existing_loggers only guards
    against loggers not named in the ini being silenced, not against root's
    existing handlers being swapped out. lifespan() must call
    database.run_migrations() BEFORE logging_config.setup_logging() so the
    app's real file handlers are installed last and survive.
    """

    @pytest.fixture(autouse=True)
    def _restore_root_handlers(self):
        root = logging.getLogger()
        original = list(root.handlers)
        yield
        root.handlers.clear()
        for h in original:
            root.addHandler(h)

    def _root_handler_types(self):
        return {type(h) for h in logging.getLogger().handlers}

    def test_run_migrations_replaces_root_handlers_with_console_only(
        self, tmp_path, monkeypatch
    ):
        from logging_config import setup_logging

        setup_logging(log_dir=str(tmp_path / "logs"))
        assert RotatingFileHandler in self._root_handler_types()

        db_path = tmp_path / "migration_logging_test.db"
        monkeypatch.setattr("config.DATABASE_URL", f"sqlite:///{db_path}")
        database.run_migrations()

        # Documents the underlying behavior: run_migrations() alone wipes
        # out any RotatingFileHandler the app had already installed.
        assert RotatingFileHandler not in self._root_handler_types()

    def test_setup_logging_after_migrations_keeps_file_handlers(
        self, tmp_path, monkeypatch
    ):
        from logging_config import setup_logging

        db_path = tmp_path / "migration_logging_test_2.db"
        monkeypatch.setattr("config.DATABASE_URL", f"sqlite:///{db_path}")
        database.run_migrations()

        setup_logging(log_dir=str(tmp_path / "logs"))

        assert RotatingFileHandler in self._root_handler_types()
