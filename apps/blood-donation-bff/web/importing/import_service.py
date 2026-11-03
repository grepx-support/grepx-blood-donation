# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

import uuid
from .excel_reader import HeaderError

class ImportService:
    """Stage → review/fix → commit. Collaborators are injected (Dependency Inversion)."""
    def __init__(self, reader, validator, rows, donors):
        self.reader, self.validator, self.rows, self.donors = reader, validator, rows, donors

    def stage(self, stream):
        batch, n = uuid.uuid4().hex[:10], 0
        for no, data in self.reader.read(stream):
            errors = self.validator.validate(data)
            self.rows.add(batch, no, data, errors, "error" if errors else "valid"); n += 1
        if not n: raise HeaderError("No data rows found in the file.")
        return batch

    def stage_rows(self, rows):
        """Same as an Excel upload, but from rows typed or pasted into the on-screen grid."""
        from .excel_reader import KEYS
        batch, n = uuid.uuid4().hex[:10], 0
        for no, raw in enumerate(rows, start=1):
            data = {k: str(raw.get(k, "") or "").strip() for k in KEYS}
            if not any(data.values()): continue
            errors = self.validator.validate(data)
            self.rows.add(batch, no, data, errors, "error" if errors else "valid"); n += 1
        if not n: raise HeaderError("Nothing to add — the grid is empty.")
        return batch

    def revalidate(self, row_id, data):
        errors = self.validator.validate(data)
        self.rows.update(row_id, data, errors, "error" if errors else "valid")

    def ignore(self, row_id): self.rows.set_status(row_id, "ignored")

    def commit(self, batch):
        done = skipped = 0
        for r in self.rows.parsed(batch):
            if r["status"] != "valid": continue
            if self.donors.by_email(r["data"]["email"]):
                self.rows.set_status(r["id"], "skipped"); skipped += 1; continue
            self._create(self.validator.clean(r["data"]))
            self.rows.set_status(r["id"], "imported"); done += 1
        return done, skipped

    def _create(self, d):
        self.donors.create(d.name, d.email, d.phone, "",
                           d.blood_group, d.sex, d.weight, d.dob.isoformat() if d.dob else None)
