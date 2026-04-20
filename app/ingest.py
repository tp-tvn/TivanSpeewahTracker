"""Parse CorePlan PLOD CSV files and insert into the database."""
import csv
import io
import re
from datetime import datetime, date
from pathlib import Path

import db


# Canonical 12-char hole ID: SFXX_LLLLNNN
_HOLE_ID_RE = re.compile(r"^SF\w{2}_[A-Za-z]{4}\d{3}$")

# Reconstruct from variants: SF + 2chars + optional-sep + 4letters + optional-sep + 2–4 digits
# Handles: missing sep, hyphen sep, sep after letters, double sep, 2-digit suffix, 4-digit with leading 0
_HOLE_RECONSTRUCT_RE = re.compile(r"^SF(\w{2})[-_]?([A-Za-z]{4})[-_]?(\d{2,4})$")

# 13-char with 5-letter section: stray leading letter after separator (e.g. SF25_DDMET023 → SF25_DMET023)
_HOLE_5LETTER_RE = re.compile(r"^(SF\w{2}_)[A-Za-z]([A-Za-z]{4}\d{3})$")

# Missing SF prefix: letters (2–8) + 3 digits, not starting with SF
_HOLE_NO_PREFIX_RE = re.compile(r"^(?!SF)[A-Za-z]{2,8}\d{3}$")

# Extract SFXX_ prefix from any hole name that has one
_HOLE_PREFIX_RE = re.compile(r"^(SF\w{2}_)")


def _normalise_hole_id(name: str) -> str:
    """Normalise a hole ID to the canonical 12-character SFXX_LLLLNNN format.

    Handles: SP→SF typo, SF_XX→SFXX position error, hyphen separators,
    missing separators, separator after letters, double separators,
    2-digit suffixes (pad to 3), 4-digit suffixes with leading zero.
    Holes that are already valid or genuinely unrecognised pass through unchanged.
    """
    name = name.strip()
    if not name:
        return name
    if _HOLE_ID_RE.match(name):
        return name

    candidate = name

    # SP → SF prefix typo (e.g. SP25_DDGT006 → SF25_DDGT006)
    if candidate.startswith("SP"):
        candidate = "SF" + candidate[2:]
        if _HOLE_ID_RE.match(candidate):
            return candidate

    # Underscore after SF instead of after SFXX (e.g. SF_25RCRD060 → SF25RCRD060)
    if re.match(r"^SF_\w{2}", candidate):
        candidate = "SF" + candidate[3:]
        if _HOLE_ID_RE.match(candidate):
            return candidate

    # Reconstruct from all separator/digit-count variants
    m = _HOLE_RECONSTRUCT_RE.match(candidate)
    if m:
        prefix, letters, digits = m.group(1), m.group(2), m.group(3)
        if len(digits) == 4 and digits[0] == "0":
            digits = digits[1:]
        elif len(digits) == 2:
            digits = "0" + digits
        if len(digits) == 3:
            return f"SF{prefix}_{letters}{digits}"

    # 5-letter section: stray leading letter after separator (e.g. SF25_DDMET023 → SF25_DMET023)
    m = _HOLE_5LETTER_RE.match(candidate)
    if m:
        return m.group(1) + m.group(2)

    return name  # unrecognised — pass through unchanged


def _infer_prefix(name: str, siblings: list[str]) -> str:
    """Prepend an SFXX_ prefix to a hole ID that's missing one.

    Scans sibling hole IDs (same PLOD, or same rig nearby) to find a valid
    SFXX_ prefix.  Returns the name unchanged if no prefix can be determined.
    """
    if not name or not _HOLE_NO_PREFIX_RE.match(name):
        return name
    for sibling in siblings:
        m = _HOLE_PREFIX_RE.match(sibling)
        if m:
            return _normalise_hole_id(m.group(1) + name)
    return name


def _parse_money(val: str) -> float:
    if not val:
        return 0.0
    return float(str(val).replace("$", "").replace(",", "").strip() or 0)


def _parse_float(val) -> float:
    try:
        return float(val) if val not in (None, "", "None") else 0.0
    except (ValueError, TypeError):
        return 0.0


def _parse_bool(val) -> int:
    if isinstance(val, bool):
        return int(val)
    return 1 if str(val).lower() in ("true", "1", "yes") else 0


def _split_sections(text: str) -> dict[str, list[str]]:
    """Split the multi-section CorePlan CSV into a dict of {section_name: [lines]}."""
    sections = {}
    current_name = None
    current_lines = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        stripped = line.strip()
        is_blank = not stripped or not stripped.replace(",", "").strip()

        if is_blank:
            # blank line → save current section, reset
            if current_name and current_lines:
                sections[current_name] = current_lines
            current_name = None
            current_lines = []
        elif current_name is None:
            # first non-blank after a gap → section header (strip trailing commas/whitespace)
            current_name = stripped.rstrip(",")
        else:
            current_lines.append(line)

    # catch last section if file doesn't end with blank line
    if current_name and current_lines:
        sections[current_name] = current_lines

    return sections


def _csv_rows(lines: list[str]) -> list[dict]:
    """Parse a list of lines (header + data) as CSV dicts."""
    if len(lines) < 2:
        return []
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    return list(reader)


def parse_plod_file(filepath: str | Path, rig_id: int | None = None) -> dict:
    """
    Parse a CorePlan PLOD CSV and return a structured dict ready for DB insertion.
    If rig_id is provided it is used directly, bypassing auto-detection.
    Returns None if the file cannot be parsed.
    """
    filepath = Path(filepath)
    text = filepath.read_text(encoding="utf-8-sig", errors="replace")
    sections = _split_sections(text)

    # ---- Details ----
    detail_rows = _csv_rows(sections.get("Details", []))
    if not detail_rows:
        return None
    d = detail_rows[0]

    plod_ref  = d.get("plod", "").strip()
    date_str  = d.get("date", "").strip()          # "2025-06-24"
    rig_name  = d.get("rig", "").strip()
    shift     = d.get("workshift", "").strip()
    contract  = d.get("contract", "").strip()
    cp_total  = _parse_money(d.get("total_cost", ""))
    eng_start = _parse_float(d.get("rig_engine_hours_start"))
    eng_end   = _parse_float(d.get("rig_engine_hours_end"))
    notes     = d.get("notes", "").strip()

    if rig_id is not None:
        with db.get_conn() as conn:
            row = conn.execute("SELECT * FROM rigs WHERE id=?", (rig_id,)).fetchone()
        rig = dict(row) if row else None
        if not rig:
            raise ValueError(f"Rig ID {rig_id} not found in database.")
    else:
        rig = db.get_rig_by_name(rig_name)
        if not rig:
            rig_guess = _guess_rig(rig_name, filepath.name)
            rig = db.get_rig_by_name(rig_guess) if rig_guess else None
        if not rig:
            raise ValueError(f"Cannot match rig '{rig_name}' to known rigs. Check rig names in the database.")

    # ---- Drilling Intervals ----
    drilling = []
    for r in _csv_rows(sections.get("Drilling Intervals", [])):
        depth_from = _parse_float(r.get("depth_from"))
        depth_to   = _parse_float(r.get("depth_to"))
        length_m   = depth_to - depth_from
        _raw_type  = r.get("type", "").strip()
        # DD rigs must have a diameter subtype (PQ3/HQ3/NQ3); fall back only
        # for RC and HYD where the rig_type IS the interval type.
        itype    = _raw_type or rig["rig_type"]
        raw_name = r.get("hole_name", "").strip()
        drilling.append({
            "hole_name":    _normalise_hole_id(raw_name),
            "raw_hole_name": raw_name,
            "depth_from":   depth_from,
            "depth_to":     depth_to,
            "length_m":     length_m,
            "interval_type":itype,
            "duration_h":   _parse_float(r.get("duration_hours")),
            "cost_per_m_cp":_parse_money(r.get("cost_per_m")),
            "cost_cp":      _parse_money(r.get("cost")),
            "drill_bit":    r.get("drill_bit", "").strip(),
            "end_of_hole":  _parse_bool(r.get("end_of_hole", "False")),
        })

    # ---- Time Breakdown ----
    time_rows = []
    for r in _csv_rows(sections.get("Time Breakdown", [])):
        raw_name = r.get("hole_name", "").strip()
        time_rows.append({
            "hole_name":    _normalise_hole_id(raw_name),
            "raw_hole_name": raw_name,
            "category":     r.get("category", "").strip(),
            "duration_h":   _parse_float(r.get("duration_hours")),
            "rate_cp":      _parse_money(r.get("cost_per_hour")),
            "cost_cp":      _parse_money(r.get("cost")),
        })

    # ---- Down Hole Activities ----
    # These are active-rate hours that CorePlan tracks separately from Time Breakdown.
    # Fold them in as active-rate time rows using the cost_per_h and cost from the section.
    for r in _csv_rows(sections.get("Down Hole Activities", [])):
        duration_h = _parse_float(r.get("duration_hours"))
        if not duration_h:
            continue
        raw_name = r.get("hole_name", "").strip()
        rate_cp  = _parse_money(r.get("cost_per_h"))
        cost_cp  = _parse_money(r.get("cost")) or (duration_h * rate_cp)
        time_rows.append({
            "hole_name":    _normalise_hole_id(raw_name),
            "raw_hole_name": raw_name,
            "category":     "Downhole Activities",
            "duration_h":   duration_h,
            "rate_cp":      rate_cp,
            "cost_cp":      cost_cp,
        })

    # ---- Consumables ----
    consumables = []
    for r in _csv_rows(sections.get("Consumables", [])):
        raw_name = r.get("hole_name", "").strip()
        consumables.append({
            "hole_name":    _normalise_hole_id(raw_name),
            "raw_hole_name": raw_name,
            "item_name":    r.get("item_name", "").strip(),
            "quantity":     _parse_float(r.get("quantity")),
            "unit":         r.get("unit", "").strip(),
            "cost_per_unit":_parse_money(r.get("cost_per_unit")),
            "cost_total":   _parse_money(r.get("cost")),
        })

    # ---- Equipment ----
    equipment = []
    for r in _csv_rows(sections.get("Equipment", [])):
        raw_name = r.get("hole_name", "").strip()
        equipment.append({
            "hole_name":     _normalise_hole_id(raw_name),
            "raw_hole_name": raw_name,
            "equipment_name":r.get("equipment_item_name", "").strip(),
            "duration_h":    _parse_float(r.get("duration_hours")),
            "cost_cp":       _parse_money(r.get("cost")),
            "time_period":   r.get("time_period", "").strip(),
        })

    # ---- People ----
    people = []
    for r in _csv_rows(sections.get("People", [])):
        people.append({
            "person_name":  r.get("person_name", "").strip(),
            "duration_h":   _parse_float(r.get("duration_hours")),
            "is_supervisor":_parse_bool(r.get("is_supervisor", "False")),
            "job_role":     r.get("job_role", "").strip(),
        })

    # Second pass: fix holes missing the SFXX_ prefix by inferring it from siblings.
    # Collect all normalised names across every section as context.
    _sections = (drilling, time_rows, consumables, equipment)
    _all_names = [row["hole_name"] for s in _sections for row in s if row.get("hole_name")]
    for section in _sections:
        for row in section:
            row["hole_name"] = _infer_prefix(row["hole_name"], _all_names)

    # Collect any hole IDs that were changed by normalisation (for import reporting)
    hole_renames = sorted({
        (row["raw_hole_name"], row["hole_name"])
        for section in _sections
        for row in section
        if row.get("raw_hole_name") and row["raw_hole_name"] != row["hole_name"]
    })

    return {
        "plod_ref":    plod_ref,
        "date":        date_str,
        "rig":         rig,
        "shift":       shift,
        "contract":    contract,
        "coreplan_total": cp_total,
        "engine_h_start": eng_start,
        "engine_h_end":   eng_end,
        "notes":       notes,
        "source_file": str(filepath),
        "drilling":     drilling,
        "time_rows":    time_rows,
        "consumables":  consumables,
        "equipment":    equipment,
        "people":       people,
        "hole_renames": hole_renames,
    }


def _guess_rig(rig_name: str, filename: str) -> str:
    """Fallback: try to guess rig from common patterns."""
    combined = (rig_name + " " + filename).lower()
    if "rig 41" in combined or "r41" in combined:
        return "Rig 41"
    if "rig 38" in combined or "r38" in combined:
        return "Rig 38"
    if "rig 16" in combined or "r16" in combined:
        return "Rig 16 (HYD)"
    if "hyd" in combined and ("rig 18" in combined or "r18" in combined):
        return "Rig 18 (HYD)"
    if "rig 18" in combined or "r18" in combined:
        return "Rig 18"
    return ""


def _peek_rig_name(filepath: Path) -> str:
    """Read just the Details section of a PLOD CSV and return the rig name field."""
    try:
        text = filepath.read_text(encoding="utf-8-sig", errors="replace")
        sections = _split_sections(text)
        rows = _csv_rows(sections.get("Details", []))
        return rows[0].get("rig", "").strip() if rows else ""
    except Exception:
        return ""


def peek_plod_ref(filepath: str | Path) -> str:
    """Read just the Details section of a PLOD CSV and return the plod_ref field."""
    try:
        text = Path(filepath).read_text(encoding="utf-8-sig", errors="replace")
        sections = _split_sections(text)
        rows = _csv_rows(sections.get("Details", []))
        return rows[0].get("plod", "").strip() if rows else ""
    except Exception:
        return ""


def import_plod(filepath: str | Path, rig_id: int | None = None, force: bool = False) -> dict:
    """
    Full pipeline: parse CSV → calculate costs → insert to DB.
    If rig_id is provided it overrides the rig detected in the CSV.
    Returns a result dict with status and summary.
    """
    filepath = Path(filepath)

    # Validate rig before importing — check the PLOD's own rig field matches the selection
    if rig_id is not None:
        plod_rig_name = _peek_rig_name(filepath)
        if plod_rig_name:
            plod_rig = db.get_rig_by_name(plod_rig_name)
            if plod_rig and plod_rig["id"] != rig_id:
                with db.get_conn() as conn:
                    sel_row = conn.execute("SELECT short_name FROM rigs WHERE id=?", (rig_id,)).fetchone()
                sel_name = sel_row["short_name"] if sel_row else f"ID {rig_id}"
                return {
                    "status":  "skipped",
                    "message": (
                        f"Rig mismatch — PLOD belongs to '{plod_rig['short_name']}' "
                        f"but selected rig is '{sel_name}'. File not imported."
                    ),
                    "file": str(filepath),
                }

    try:
        parsed = parse_plod_file(filepath, rig_id=rig_id)
    except ValueError as e:
        return {"status": "error", "message": str(e), "file": str(filepath)}

    if not parsed:
        return {"status": "error", "message": "Failed to parse file", "file": str(filepath)}

    plod_ref = parsed["plod_ref"]
    if db.get_plod_exists(plod_ref):
        if not force:
            return {"status": "skipped", "message": f"{plod_ref} already imported", "file": str(filepath)}
        # Force replace: delete existing record and all child data before re-importing
        with db.get_conn() as conn:
            existing = conn.execute("SELECT id FROM plods WHERE plod_ref=?", (plod_ref,)).fetchone()
        if existing:
            db.delete_plods([existing["id"]])

    # Insert plod header
    plod_data = {
        "plod_ref":      plod_ref,
        "date":          parsed["date"],
        "rig_id":        parsed["rig"]["id"],
        "shift":         parsed["shift"],
        "coreplan_total":parsed["coreplan_total"],
        "engine_h_start":parsed["engine_h_start"],
        "engine_h_end":  parsed["engine_h_end"],
        "contract":      parsed["contract"],
        "notes":         parsed["notes"],
        "source_file":   parsed["source_file"],
    }
    plod_id = db.insert_plod(plod_data)

    # Insert sub-tables
    if parsed["drilling"]:
        db.insert_drilling_intervals(plod_id, parsed["drilling"])
    if parsed["time_rows"]:
        db.insert_time_breakdown(plod_id, parsed["time_rows"])
    if parsed["consumables"]:
        db.insert_consumables(plod_id, parsed["consumables"])
    if parsed["equipment"]:
        db.insert_equipment(plod_id, parsed["equipment"])
    if parsed["people"]:
        db.insert_people(plod_id, parsed["people"])

    # Calculate our costs and insert summary
    import calculate
    summary = calculate.compute_summary(plod_id, parsed)
    db.insert_cost_summary(plod_id, summary)

    return {
        "status":       "replaced" if force else "ok",
        "plod_ref":     plod_ref,
        "date":         parsed["date"],
        "rig":          parsed["rig"]["short_name"],
        "our_total":    summary["our_total"],
        "cp_total":     summary["coreplan_total"],
        "variance":     summary["variance"],
        "variance_pct": summary["variance_pct"],
        "metres":       summary["metres_drilled"],
        "hole_renames": parsed.get("hole_renames", []),
    }


def normalise_existing_hole_ids() -> list[tuple]:
    """
    Re-apply hole ID normalisation to all existing records in the DB.
    Uses the global pool of all hole names as sibling context so prefix
    inference works even for PLODs where only one hole was drilled.
    Preserves the original value in raw_hole_name if not already set.
    Returns a sorted, deduplicated list of (old_name, new_name) pairs changed.
    """
    _TABLES = ("drilling_intervals", "time_breakdown", "consumables", "equipment")

    # Build global sibling pool from every hole name already in the DB
    all_names: list[str] = []
    with db.get_conn() as conn:
        for table in _TABLES:
            rows = conn.execute(
                f"SELECT DISTINCT hole_name FROM {table} WHERE hole_name IS NOT NULL AND hole_name != ''"
            ).fetchall()
            all_names.extend(r["hole_name"] for r in rows)

    changes: list[tuple] = []
    with db.get_conn() as conn:
        for table in _TABLES:
            rows = conn.execute(
                f"SELECT id, hole_name, raw_hole_name FROM {table}"
            ).fetchall()
            for row in rows:
                old = row["hole_name"] or ""
                if not old:
                    continue
                new = _normalise_hole_id(old)
                new = _infer_prefix(new, all_names)
                if new != old:
                    raw = row["raw_hole_name"] or old   # keep original if not already stored
                    conn.execute(
                        f"UPDATE {table} SET hole_name=?, raw_hole_name=? WHERE id=?",
                        (new, raw, row["id"]),
                    )
                    changes.append((old, new))
        conn.commit()

    return sorted(set(changes))


def import_folder(folder: str | Path, rig_id: int | None = None) -> list[dict]:
    """Import all CSV files in a folder."""
    folder = Path(folder)
    results = []
    for f in sorted(folder.glob("*.csv")):
        results.append(import_plod(f, rig_id=rig_id))
    return results
