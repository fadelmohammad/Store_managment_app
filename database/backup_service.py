# File: database/backup_service.py

import os
import logging
import sqlite3
from datetime import datetime

_BACKUP_DIR = "backups"
_DB_PATH    = "store.db"
_MAX_KEEP   = 30


class BackupService:
    def __init__(self, db_path: str = _DB_PATH, backup_dir: str = _BACKUP_DIR):
        self.db_path    = db_path
        self.backup_dir = backup_dir
        os.makedirs(self.backup_dir, exist_ok=True)

    # ── public API ────────────────────────────────────────────────────────────

    def create_backup(self, label: str = "") -> str:
        """
        Hot-copy the live database using SQLite's backup API (safe while app runs).
        Embeds the current schema version in the filename so you always know
        what version a backup was made on.
        Returns the path of the created backup file.
        """
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        schema_ver = self._read_schema_version(self.db_path)
        suffix     = f"_{label}" if label else ""
        filename   = f"store_{timestamp}_sv{schema_ver}{suffix}.db"
        dest       = os.path.join(self.backup_dir, filename)

        self._copy_db(self.db_path, dest)
        logging.info(f"Backup created: {dest}")
        self._prune_old_backups()
        return dest

    def restore_backup(self, backup_path: str) -> None:
        """
        Restore a backup file over the live database.
        - Creates a safety backup of the current DB first.
        - Validates the file is a real SQLite database.
        - After overwriting, runs run_migrations() so any schema changes
          introduced since the backup was made are applied automatically.
        """
        if not os.path.isfile(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        self._validate_sqlite(backup_path)

        # Safety snapshot before overwriting
        self.create_backup(label="pre_restore")

        self._copy_db(backup_path, self.db_path)
        logging.info(f"Restored from: {backup_path}")

        # Re-apply any migrations the restored (older) DB is missing
        self._run_migrations_on_restored()

    def list_backups(self) -> list[dict]:
        """
        Returns list of dicts sorted newest-first:
          { name, path, size_kb, created_at, schema_version }
        """
        files = []
        for fname in os.listdir(self.backup_dir):
            if not fname.endswith(".db"):
                continue
            fpath = os.path.join(self.backup_dir, fname)
            stat  = os.stat(fpath)
            files.append({
                "name":           fname,
                "path":           fpath,
                "size_kb":        round(stat.st_size / 1024, 1),
                "created_at":     datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "schema_version": self._parse_schema_version_from_name(fname),
            })
        return sorted(files, key=lambda f: f["created_at"], reverse=True)

    def delete_backup(self, backup_path: str) -> None:
        if not os.path.isfile(backup_path):
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        os.remove(backup_path)
        logging.info(f"Backup deleted: {backup_path}")

    def auto_backup(self) -> str | None:
        """
        Called on app startup. Creates one backup per day max.
        Returns the backup path if one was created, else None.
        """
        today = datetime.now().strftime("%Y%m%d")
        for f in self.list_backups():
            if today in f["name"] and "pre_restore" not in f["name"]:
                return None  # already backed up today
        return self.create_backup(label="auto")

    # ── private ───────────────────────────────────────────────────────────────

    def _copy_db(self, src_path: str, dest_path: str) -> None:
        src  = sqlite3.connect(src_path)
        dest = sqlite3.connect(dest_path)
        try:
            src.backup(dest)
        finally:
            dest.close()
            src.close()

    def _validate_sqlite(self, path: str) -> None:
        try:
            conn = sqlite3.connect(path)
            result = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            if result[0] != "ok":
                raise ValueError(f"Integrity check failed: {result[0]}")
        except Exception as e:
            raise ValueError(f"Invalid or corrupt backup file: {e}")

    def _read_schema_version(self, db_path: str) -> int:
        try:
            conn = sqlite3.connect(db_path)
            row  = conn.execute("SELECT value FROM settings WHERE key = 'schema_version'").fetchone()
            conn.close()
            return int(row[0]) if row else 0
        except Exception:
            return 0

    def _parse_schema_version_from_name(self, filename: str) -> str:
        """Extract sv<N> from filename, e.g. store_20250601_sv3_auto.db → 'v3'."""
        import re
        m = re.search(r"_sv(\d+)", filename)
        return f"v{m.group(1)}" if m else "?"

    def _run_migrations_on_restored(self) -> None:
        """After restore, apply any pending migrations to bring schema up to date."""
        try:
            from database.schema import run_migrations
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            try:
                run_migrations(conn)
                conn.commit()
            finally:
                conn.close()
            logging.info("Post-restore migrations applied.")
        except Exception as e:
            logging.error(f"Post-restore migration failed: {e}")
            raise

    def _prune_old_backups(self) -> None:
        backups = self.list_backups()
        for old in backups[_MAX_KEEP:]:
            try:
                os.remove(old["path"])
                logging.info(f"Pruned old backup: {old['name']}")
            except OSError:
                pass
