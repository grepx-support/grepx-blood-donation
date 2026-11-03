# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of LifeFlow Blood Camp and is proprietary and confidential.
# Unauthorised copying, modification or distribution is strictly prohibited.

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from repos import DonorRepo, ImportRepo
from importing.excel_reader import ExcelReader, HeaderError, KEYS, HEADERS
from importing.excel_template import ExcelTemplate
from importing.row_validator import RowValidator
from importing.import_service import ImportService
from security import permission_required

bp = Blueprint("imports", __name__, url_prefix="/admin/import")
guard = permission_required("bulk_import")

def svc():
    donors = DonorRepo()
    return ImportService(ExcelReader(), RowValidator(donors), ImportRepo(), donors)

@bp.route("/")
@guard
def index(): return render_template("admin/import.html", headers=HEADERS)

@bp.route("/template.xlsx")
@guard
def template(): return send_file(ExcelTemplate().build(), as_attachment=True, download_name="donor_template.xlsx")

@bp.post("/upload")
@guard
def upload():
    try: batch = svc().stage(request.files["file"].stream)
    except HeaderError as e: flash(str(e), "error"); return redirect(url_for("imports.index"))
    except Exception: flash("That doesn't look like a valid .xlsx file.", "error"); return redirect(url_for("imports.index"))
    return redirect(url_for("imports.review", batch=batch))

@bp.route("/<batch>")
@guard
def review(batch):
    rows = ImportRepo().parsed(batch)
    count = lambda s: sum(r["status"] == s for r in rows)
    return render_template("admin/import_review.html", rows=rows, batch=batch, keys=KEYS, headers=dict(zip(KEYS, HEADERS)),
                           valid=count("valid"), bad=count("error"), ignored=count("ignored"))

@bp.post("/<batch>/fix/<rid>")
@guard
def fix(batch, rid):
    svc().revalidate(rid, {k: request.form.get(k, "").strip() for k in KEYS})
    return redirect(url_for("imports.review", batch=batch))

@bp.post("/<batch>/ignore/<rid>")
@guard
def ignore(batch, rid):
    svc().ignore(rid); return redirect(url_for("imports.review", batch=batch))

@bp.post("/<batch>/commit")
@guard
def commit(batch):
    done, skipped = svc().commit(batch)
    flash(f"Imported {done} donors{f', skipped {skipped} duplicates' if skipped else ''}. 🎉", "celebrate")
    return redirect(url_for("donors.index"))
