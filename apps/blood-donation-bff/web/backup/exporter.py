# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

import json
from datetime import date, datetime
from pathlib import Path
from sqlalchemy import select
from models import metadata

class TableExporter:
    """Dumps every table to tables/<name>.json (UTF-8, stable order so git diffs stay small)."""
    def __init__(self, engine): self.engine = engine

    def export(self, folder):
        out = Path(folder) / "tables"; out.mkdir(parents=True, exist_ok=True)
        counts = {}
        with self.engine.connect() as conn:
            for table in metadata.sorted_tables:
                rows = [dict(r) for r in conn.execute(select(table).order_by(*table.primary_key.columns)).mappings()]
                (out / f"{table.name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=self._plain), encoding="utf-8")
                counts[table.name] = len(rows)
        manifest = {"created": datetime.now().isoformat(timespec="seconds"), "database": self.engine.dialect.name, "rows": counts}
        (Path(folder) / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        return manifest

    @staticmethod
    def _plain(v): return v.isoformat(sep=" ") if isinstance(v, datetime) else v.isoformat() if isinstance(v, date) else str(v)
