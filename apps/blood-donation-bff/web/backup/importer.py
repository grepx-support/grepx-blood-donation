# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

import grepx_contracts as gc
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import DateTime, delete, func, insert, select, text, Integer
from models import metadata

class RestoreRefused(Exception): pass

class TableImporter:
    """Loads a backup into any database. Also the easy way to move SQLite -> PostgreSQL/MySQL."""
    def __init__(self, engine): self.engine = engine

    DATA_TABLES = (gc.people.PEOPLE, gc.event.EVENTS, gc.donation.DONATIONS, "interests", gc.task.TASKS)  # starter rows (roles, migrations) don't count

    def restore(self, folder, force=False):
        src = Path(folder) / "tables"
        if not src.is_dir(): raise RestoreRefused(f"No backup found in {src}")
        metadata.create_all(self.engine)
        with self.engine.begin() as conn:
            if not force and any(conn.execute(select(func.count()).select_from(metadata.tables[n])).scalar() for n in self.DATA_TABLES):
                raise RestoreRefused("The database already has data. Use --force to replace it.")
            for t in reversed(metadata.sorted_tables): conn.execute(delete(t))
            counts = {t.name: self._load(conn, t, src / f"{t.name}.json") for t in metadata.sorted_tables}
            self._reset_sequences(conn)
        if self.engine.dialect.name == "postgresql":  # fresh statistics so queries are fast right after a big restore
            with self.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as c: c.exec_driver_sql("ANALYZE")
        return counts

    def _load(self, conn, table, path):
        if not path.exists(): return 0
        rows = [self._typed(table, r) for r in json.loads(path.read_text(encoding="utf-8"))]
        for i in range(0, len(rows), 500): conn.execute(insert(table), rows[i:i + 500])
        return len(rows)

    @staticmethod
    def _typed(table, row):
        cols = {c.name: c for c in table.columns}
        out = {k: v for k, v in row.items() if k in cols}
        for k, v in out.items():
            if isinstance(cols[k].type, DateTime) and isinstance(v, str): out[k] = datetime.fromisoformat(v)
        return out

    def _reset_sequences(self, conn):
        if self.engine.dialect.name != "postgresql": return
        for t in metadata.sorted_tables:
            if "id" in t.c and isinstance(t.c.id.type, Integer) and t.c.id.autoincrement is not False and t.name != "drive_reports":
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{t.name}', 'id'), COALESCE((SELECT MAX(id) FROM {t.name}), 0) + 1, false)"))
