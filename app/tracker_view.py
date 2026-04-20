"""
Build Excel-style per-rig tracker DataFrames from the database.

One row per PLOD, columns matching the layout of the original Excel tracker:
  RC  → depth-band metres, time hours, equipment hours, consumable total
  DD  → per-hole PQ3/HQ3 intervals, time hours, tool uses
  HYD → diameter metres, time hours, itemised consumable columns
"""
import re
import pandas as pd
import db
import calculate

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ACCOM_KW = ("accommodation", "messing", "camp")

RC_DEPTH_BANDS = [
    ("0-50m",    0,   50),
    ("50-100m",  50,  100),
    ("100-150m", 100, 150),
    ("150-200m", 150, 200),
    ("200-250m", 200, 250),
    ("250-300m", 250, 300),
]

HYD_DIAMETERS = [
    ('14.5" (381mm)', "381"),
    ('12.5" (312mm)', "312"),
    ('9.5" (230mm)',  "230"),
    ('6" (150mm)',    "150"),
]

DD_TYPES = ["PQ3", "HQ3", "NQ3"]

# equipment_name (substring, lower) → display column
_EQUIP_MAP = {
    "booster":               "Booster (p/hr)",
    "auxiliary booster":     "Booster (p/hr)",
    "aux compressor":        "Aux Compressor (p/hr)",
    "auxiliary compressor":  "Aux Compressor (p/hr)",
    "azi aligner":           "Azi Aligner (p/day)",
    "azimuth aligner":       "Azi Aligner (p/day)",
    "gyro":                  "Gyro (p/day)",
    "survey camera":         "Gyro (p/day)",
    "pq orientation":        "PQ Ori Tool",
    "hq orientation":        "HQ Ori Tool",
}

# consumable item_name (substring, lower) → HYD display column
_HYD_CONS_MAP = {
    "pvc 100 mm plain":   "PVC 100mm Plain (m)",
    "pvc 100mm plain":    "PVC 100mm Plain (m)",
    "100mm pvc plain":    "PVC 100mm Plain (m)",
    "pvc 100 mm slotted": "PVC 100mm Slotted (m)",
    "pvc 100mm slotted":  "PVC 100mm Slotted (m)",
    "100mm pvc slotted":  "PVC 100mm Slotted (m)",
    "200mm top/end cap":  "200mm End Cap",
    "end cap 200":        "200mm End Cap",
    "steel casing 350":   "Steel Casing 350NB (m)",
    "steel well cover":   "Steel Well Cover",
    "concrete plinth":    "Concrete Plinth",
    "gravel pack":        "Gravel Pack (bags)",
    "casing centraliser": "Casing Centraliser",
    "drilling fluids":    "Drilling Fluids (drums)",
    "bentonite":          "Bentonite (pallets)",
    "cement":             "Cement (bags)",
}

HYD_CONS_COLS = [
    "PVC 100mm Plain (m)", "PVC 100mm Slotted (m)", "200mm End Cap",
    "Steel Casing 350NB (m)", "Steel Well Cover", "Concrete Plinth",
    "Gravel Pack (bags)", "Casing Centraliser", "Drilling Fluids (drums)",
    "Bentonite (pallets)", "Cement (bags)", "Other Consumables",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _equip_col(name: str) -> str | None:
    n = name.lower()
    for key, col in _EQUIP_MAP.items():
        if key in n:
            return col
    return None


def _hyd_cons_col(name: str) -> str:
    n = name.lower()
    for key, col in _HYD_CONS_MAP.items():
        if key in n:
            return col
    return "Other Consumables"


def _is_accom(name: str) -> bool:
    return any(k in name.lower() for k in _ACCOM_KW)

def _parse_groundwater_pairs(notes: str) -> list:
    """
    Scan PLOD notes for 12-character hole IDs starting with SF.
    For each hole, collect all depth values (numbers followed by m/M) up to
    the next hole ID and return the maximum non-zero depth.
    Returns a list of (hole_id, depth_m) tuples in order of appearance.
    """
    if not notes:
        return []

    _HOLE  = re.compile(r'(SF[A-Z0-9_\-]{10})(?!\w)', re.IGNORECASE)
    _DEPTH = re.compile(r'\b(\d+)\s*[Mm]\b')

    def _normalise(raw: str) -> str:
        raw = raw.upper().replace('-', '_')
        return raw[:2] + raw[2:].replace('O', '0')

    hole_matches = list(_HOLE.finditer(notes))
    if not hole_matches:
        return []

    pairs = []
    seen: set = set()

    for i, hm in enumerate(hole_matches):
        hole = _normalise(hm.group(1))
        if hole in seen:
            continue
        seen.add(hole)

        seg_start = hm.end()
        seg_end   = hole_matches[i + 1].start() if i + 1 < len(hole_matches) else len(notes)
        segment   = notes[seg_start:seg_end]

        depths = [int(m.group(1)) for m in _DEPTH.finditer(segment) if int(m.group(1)) > 0]
        if depths:
            pairs.append((hole, max(depths)))

    return pairs


def _parse_groundwater(notes: str) -> str:
    """String summary of groundwater pairs, e.g. 'SFGW001_001A: 18m | SFHB0001_001: 45m'."""
    return " | ".join(f"{h}: {d}m" for h, d in _parse_groundwater_pairs(notes))


def _is_flight(name: str) -> bool:
    return "flight" in name.lower()

def _is_freight(name: str) -> bool:
    return "freight" in name.lower()

def _is_oncharge(name: str) -> bool:
    return "on-charg" in name.lower()

def _flights_freight_oncharge(consumables: list[dict]) -> tuple[float | None, float | None, float | None]:
    """Return (flights, freight, oncharges) totals — None if not present."""
    flights   = sum(c.get("cost_total") or 0.0 for c in consumables if _is_flight(c.get("item_name") or ""))
    freight   = sum(c.get("cost_total") or 0.0 for c in consumables if _is_freight(c.get("item_name") or ""))
    oncharges = sum(c.get("cost_total") or 0.0 for c in consumables if _is_oncharge(c.get("item_name") or ""))
    return (flights or None, freight or None, oncharges or None)


def _cons_tooltip(consumables: list[dict]) -> str:
    """Build a hover tooltip string showing the itemised consumable breakdown."""
    if not consumables:
        return ""
    lines = []
    for c in consumables:
        name  = c.get("item_name") or "Unknown"
        qty   = c.get("quantity") or 0
        unit  = c.get("unit") or ""
        total = c.get("cost_total") or 0.0
        lines.append(f"{name} ({qty} {unit}): ${total:,.2f}")
    grand = sum(c.get("cost_total") or 0.0 for c in consumables)
    lines.append("─" * 28)
    lines.append(f"Total: ${grand:,.2f}")
    return "\n".join(lines)


def _fetch_plods(rig_ids: list[int], date_from: str, date_to: str) -> list[dict]:
    if not rig_ids:
        return []
    placeholders = ",".join("?" * len(rig_ids))
    with db.get_conn() as conn:
        rows = conn.execute(
            f"SELECT p.*, r.rig_type, r.short_name, r.default_interval_type "
            f"FROM plods p JOIN rigs r ON p.rig_id = r.id "
            f"WHERE p.rig_id IN ({placeholders}) AND p.date BETWEEN ? AND ? "
            f"ORDER BY p.date, r.short_name, p.shift",
            [*rig_ids, date_from, date_to],
        ).fetchall()
    return [dict(r) for r in rows]


def _fetch_sub(plod_id: int) -> dict:
    with db.get_conn() as conn:
        summary_row = conn.execute(
            "SELECT * FROM cost_summary WHERE plod_id=?", (plod_id,)
        ).fetchone()
        return {
            "drilling":    [dict(r) for r in conn.execute("SELECT * FROM drilling_intervals WHERE plod_id=?", (plod_id,)).fetchall()],
            "time":        [dict(r) for r in conn.execute("SELECT * FROM time_breakdown WHERE plod_id=?", (plod_id,)).fetchall()],
            "consumables": [dict(r) for r in conn.execute("SELECT * FROM consumables WHERE plod_id=?", (plod_id,)).fetchall()],
            "equipment":   [dict(r) for r in conn.execute("SELECT * FROM equipment WHERE plod_id=?", (plod_id,)).fetchall()],
            "people":      [dict(r) for r in conn.execute("SELECT * FROM people WHERE plod_id=?", (plod_id,)).fetchall()],
            "summary":     dict(summary_row) if summary_row else {},
        }


def _unique_holes(drilling: list[dict], max_holes: int) -> list[str | None]:
    seen: list[str] = []
    for d in drilling:
        h = d.get("hole_name") or ""
        if h and h not in seen:
            seen.append(h)
    holes = seen[:max_holes]
    holes += [None] * (max_holes - len(holes))
    return holes


def _time_breakdown(time_rows: list[dict]) -> dict:
    cats = {
        "Active Hours":      0.0,
        "Inactive Hours":    0.0,
        "Standby Hours":     0.0,
        "Non-charged Hours": 0.0,
        "Maintenance Hours": 0.0,
    }
    for t in time_rows:
        cat = (t.get("category") or "").lower().strip()
        h = t.get("duration_h") or 0.0
        if "maintenance" in cat:
            cats["Maintenance Hours"] += h
        elif "non" in cat and "charg" in cat:
            cats["Non-charged Hours"] += h
        elif "standby" in cat:
            cats["Standby Hours"] += h
        elif "inactive" in cat or "pulling" in cat:
            cats["Inactive Hours"] += h
        else:
            cats["Active Hours"] += h
    return cats


def _equipment_hours(equipment: list[dict]) -> dict:
    """Return {display_col: total_hours/uses}."""
    out: dict[str, float] = {}
    for e in equipment:
        col = _equip_col(e.get("equipment_name") or "")
        if col:
            out[col] = out.get(col, 0.0) + (e.get("duration_h") or 0.0)
    return out


_AUX_COLS = {"Booster (p/hr)", "Aux Compressor (p/hr)"}
_SURVEY_COLS = {"Azi Aligner (p/day)", "Gyro (p/day)", "Survey Camera (p/day)"}


def _equipment_costs(equipment: list[dict]) -> dict:
    """Return cost totals keyed by display column, plus combined Aux Equipment Cost."""
    out: dict[str, float] = {}
    for e in equipment:
        col = _equip_col(e.get("equipment_name") or "")
        if col:
            out[col] = out.get(col, 0.0) + (e.get("cost_cp") or 0.0)
    aux_total = sum(out.get(c, 0.0) for c in _AUX_COLS)
    return out, aux_total or None


def _driller(people: list[dict]) -> str | None:
    for p in people:
        if not p.get("is_supervisor"):
            return p.get("person_name")
    return people[0]["person_name"] if people else None


# ---------------------------------------------------------------------------
# RC tracker
# ---------------------------------------------------------------------------


def build_rc_tracker(rig_ids: list[int], date_from: str, date_to: str) -> pd.DataFrame:
    """One row per PLOD — RC depth-band layout."""
    plods = _fetch_plods(rig_ids, date_from, date_to)
    if not plods:
        return pd.DataFrame()

    hp   = db.get_hole_purposes()
    rows = []

    for p in plods:
        sub = _fetch_sub(p["id"])
        s   = sub["summary"]
        drilling = sub["drilling"]

        # Hole IDs (up to 4)
        holes = _unique_holes(drilling, 4)

        # Metres by depth band (total) + per-hole breakdown
        band_m: dict[str, float] = {name: 0.0 for name, *_ in RC_DEPTH_BANDS}
        hole_band_m: dict[str, dict[str, float]] = {}
        hole_drill_time: dict[str, float] = {}
        drill_time    = 0.0
        for d in drilling:
            h      = d.get("hole_name") or ""
            d_from = d.get("depth_from") or 0.0
            d_to   = d.get("depth_to")   or 0.0
            dt     = d.get("duration_h") or 0.0
            drill_time += dt
            if h not in hole_band_m:
                hole_band_m[h]    = {name: 0.0 for name, *_ in RC_DEPTH_BANDS}
                hole_drill_time[h] = 0.0
            hole_drill_time[h] += dt
            for name, lo, hi in RC_DEPTH_BANDS:
                ov = min(d_to, hi) - max(d_from, lo)
                if ov > 0:
                    band_m[name]          += ov
                    hole_band_m[h][name]  += ov

        total_metres  = sum(band_m.values())
        cp_drill_cost = calculate.drilling_cost_from_rates(drilling, p["rig_id"], p["rig_type"])

        equip, aux_cost = _equipment_costs(sub["equipment"])
        tbreak = _time_breakdown(sub["time"])
        total_hours = sum(tbreak.values()) + drill_time

        our_total  = s.get("our_total") or 0.0
        flights_cost, freight_cost, oncharge_cost = _flights_freight_oncharge(sub["consumables"])

        row = {
            "PLOD ID":                    p["id"],
            "Rig":                        p["short_name"],
            "Date":                       p["date"],
            "Shift":                      p.get("shift"),
            "Hole 1":                     holes[0],
            "Hole 2":                     holes[1],
            "Hole 3":                     holes[2],
            "Hole 4":                     holes[3],
            "Driller":                    _driller(sub["people"]),
            "Personnel":                  len(sub["people"]),
            "Accom Cost":                 s.get("our_accommodation"),
            **band_m,
            "Total Daily Metres":         total_metres,
            "Drilling Cost (CP)":         cp_drill_cost,
            "Drill Time (hrs)":           drill_time,
            "Charged Drilling Cost":      s.get("our_drilling_cost"),
            "Slow Drilling":              "🚩" if s.get("slow_drilling") else "",
            "Aux Equipment Cost":          aux_cost,
            "Azi Aligner Cost":           equip.get("Azi Aligner (p/day)") or None,
            "Gyro Cost":                  equip.get("Gyro (p/day)") or None,
            **tbreak,
            "Total Hours":                total_hours,
            "Total Activity Hours Cost":  s.get("our_time_cost"),
            "Total Equipment Cost":       s.get("our_equipment_cost"),
            "Total Consumables":          s.get("our_consumables"),
            "Consumables On-Charges":     oncharge_cost,
            "Flights":                    flights_cost,
            "Freight":                    freight_cost,
            "_cons_tooltip": _cons_tooltip(sub["consumables"]),
            "Total Costs":                our_total,
            "Variance ($)":               s.get("variance"),
            "Variance (%)":               s.get("variance_pct"),
            "Operational Cost Per Metre":  (
                                              (s.get("our_drilling_cost") or 0)
                                              + (s.get("our_equipment_cost") or 0)
                                              + (s.get("our_time_cost") or 0)
                                          ) / total_metres if total_metres else None,
            "PLOD Link":                  p.get("plod_ref"),
            "Notes":                      p.get("notes"),
        }

        # Per-hole detail columns (far right)
        for i, hole_name in enumerate(holes, 1):
            hbm = hole_band_m.get(hole_name or "", {})
            row[f"H{i} Name"]            = hole_name
            row[f"H{i} Purpose"]         = hp.get(hole_name or "", "") if hole_name else ""
            for bname, *_ in RC_DEPTH_BANDS:
                row[f"H{i} {bname}"]     = hbm.get(bname) if hole_name else None
            row[f"H{i} Total m"]         = sum(hbm.values()) if hole_name else None
            row[f"H{i} Drill Time (hrs)"] = hole_drill_time.get(hole_name or "") if hole_name else None

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# DD tracker
# ---------------------------------------------------------------------------

def build_dd_tracker(rig_ids: list[int], date_from: str, date_to: str) -> pd.DataFrame:
    """One row per PLOD — DD per-hole PQ3/HQ3 interval layout."""
    plods = _fetch_plods(rig_ids, date_from, date_to)
    if not plods:
        return pd.DataFrame()

    hp = db.get_hole_purposes()

    # Determine max holes across all PLODs for this rig/period
    all_hole_counts = []
    sub_cache = {}
    for p in plods:
        sub = _fetch_sub(p["id"])
        sub_cache[p["id"]] = sub
        holes = [d.get("hole_name") or "" for d in sub["drilling"]]
        unique = list(dict.fromkeys(h for h in holes if h))
        all_hole_counts.append(len(unique))
    max_holes = max(all_hole_counts, default=2)
    max_holes = max(max_holes, 2)  # always show at least 2 hole columns

    rows = []

    for p in plods:
        sub      = sub_cache[p["id"]]
        s        = sub["summary"]
        drilling = sub["drilling"]

        holes = _unique_holes(drilling, max_holes)

        # Per-hole, per-type: aggregate depth range + total length
        intervals: dict[tuple, dict] = {}  # (hole, type_key) → {from, to, length}
        drill_time = 0.0

        default_itype = (p.get("default_interval_type") or "").upper()
        for d in drilling:
            h     = d.get("hole_name") or ""
            itype = (d.get("interval_type") or "").upper()
            if "PQ" in itype:
                tkey = "PQ3"
            elif "HQ" in itype:
                tkey = "HQ3"
            elif "NQ" in itype:
                tkey = "NQ3"
            elif default_itype in ("PQ3", "HQ3", "NQ3"):
                tkey = default_itype  # CorePlan didn't populate type — use rig default
            else:
                tkey = itype or "Other"
            key   = (h, tkey)
            m     = d.get("length_m") or 0.0
            drill_time += d.get("duration_h") or 0.0

            if key not in intervals:
                intervals[key] = {
                    "from":   d.get("depth_from") or 0.0,
                    "to":     d.get("depth_to")   or 0.0,
                    "length": m,
                }
            else:
                intervals[key]["from"]   = min(intervals[key]["from"],  d.get("depth_from") or 0.0)
                intervals[key]["to"]     = max(intervals[key]["to"],    d.get("depth_to")   or 0.0)
                intervals[key]["length"] += m

        total_metres  = sum(v["length"] for v in intervals.values())
        cp_drill_cost = calculate.drilling_cost_from_rates(
            drilling, p["rig_id"], p["rig_type"], p.get("default_interval_type", "")
        )

        equip, aux_cost = _equipment_costs(sub["equipment"])
        tbreak          = _time_breakdown(sub["time"])
        total_hours  = sum(tbreak.values()) + drill_time

        our_total  = s.get("our_total") or 0.0
        flights_cost, freight_cost, oncharge_cost = _flights_freight_oncharge(sub["consumables"])

        row: dict = {
            "PLOD ID": p["id"],
            "Rig":     p["short_name"],
            "Date":    p["date"],
            "Shift":   p.get("shift"),
        }

        for i, hole in enumerate(holes, 1):
            row[f"Hole {i}"] = hole
            for dtype in DD_TYPES:
                key = (hole or "", dtype)
                iv  = intervals.get(key)
                row[f"H{i} {dtype} From"]   = iv["from"]   if iv else None
                row[f"H{i} {dtype} To"]     = iv["to"]     if iv else None
                row[f"H{i} {dtype} Length"] = iv["length"] if iv else None

        row.update({
            "Driller":                    _driller(sub["people"]),
            "Personnel":                  len(sub["people"]),
            "Accom Cost":                 s.get("our_accommodation"),
            "Total Length (m)":           total_metres,
            "Drilling Cost (CP)":         cp_drill_cost,
            "Charged Drilling Cost":      s.get("our_drilling_cost"),
            "Slow Drilling":              "🚩" if s.get("slow_drilling") else "",
            "PQ Ori Tool":                equip.get("PQ Ori Tool"),
            "HQ Ori Tool":                equip.get("HQ Ori Tool"),
            "Gyro Cost":                  equip.get("Gyro (p/day)") or None,
            "Aux Equipment Cost":          aux_cost,
            "Total Equipment Cost":       s.get("our_equipment_cost"),
            "Drill Time (hrs)":           drill_time,
            **tbreak,
            "Total Hours":                total_hours,
            "Total Activity Hours Cost":  s.get("our_time_cost"),
            "Total Consumables":          s.get("our_consumables"),
            "Consumables On-Charges":     oncharge_cost,
            "Flights":                    flights_cost,
            "Freight":                    freight_cost,
            "_cons_tooltip": _cons_tooltip(sub["consumables"]),
            "Total Costs":                our_total,
            "Variance ($)":               s.get("variance"),
            "Variance (%)":               s.get("variance_pct"),
            "Operational Cost Per Metre":  (
                                              (s.get("our_drilling_cost") or 0)
                                              + (s.get("our_equipment_cost") or 0)
                                              + (s.get("our_time_cost") or 0)
                                          ) / total_metres if total_metres else None,
            "PLOD Link":                  p.get("plod_ref"),
            "Notes":                      p.get("notes"),
        })

        # Per-hole purpose columns (far right — interval data already in middle columns)
        for i, hole_name in enumerate(holes, 1):
            row[f"H{i} Purpose"] = hp.get(hole_name or "", "") if hole_name else ""

        rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# HYD tracker
# ---------------------------------------------------------------------------

def build_hyd_tracker(rig_ids: list[int], date_from: str, date_to: str) -> pd.DataFrame:
    """One row per PLOD — HYD diameter + itemised consumable layout."""
    plods = _fetch_plods(rig_ids, date_from, date_to)
    if not plods:
        return pd.DataFrame()

    hp = db.get_hole_purposes()

    rows = []

    for p in plods:
        sub = _fetch_sub(p["id"])
        s   = sub["summary"]
        drilling = sub["drilling"]

        holes = _unique_holes(drilling, 4)

        # Metres by diameter (total) + per-hole breakdown
        diam_m: dict[str, float] = {col: 0.0 for col, _ in HYD_DIAMETERS}
        hole_diam_m: dict[str, dict[str, float]] = {}
        drill_time = 0.0
        for d in drilling:
            h      = d.get("hole_name") or ""
            itype  = d.get("interval_type") or ""
            metres = d.get("length_m") or 0.0
            drill_time += d.get("duration_h") or 0.0
            if h not in hole_diam_m:
                hole_diam_m[h] = {col: 0.0 for col, _ in HYD_DIAMETERS}
            matched = False
            for col, diam in HYD_DIAMETERS:
                if diam in itype:
                    diam_m[col]          += metres
                    hole_diam_m[h][col]  += metres
                    matched = True
                    break
            if not matched and metres:
                diam_m[HYD_DIAMETERS[0][0]]         += metres
                hole_diam_m[h][HYD_DIAMETERS[0][0]] += metres

        total_metres  = sum(diam_m.values())
        cp_drill_cost = calculate.drilling_cost_from_rates(drilling, p["rig_id"], p["rig_type"])

        equip, aux_cost = _equipment_costs(sub["equipment"])
        tbreak  = _time_breakdown(sub["time"])
        total_hours = sum(tbreak.values()) + drill_time

        # Itemised consumables (exclude accom, equipment items, flights, freight)
        _HYD_EQUIP_KW = ("booster", "compressor", "azi aligner", "azimuth aligner", "gyro", "survey camera")
        cons_by_col = {c: 0.0 for c in HYD_CONS_COLS}
        for c in sub["consumables"]:
            name = c.get("item_name") or ""
            if (_is_accom(name) or _is_flight(name) or _is_freight(name) or _is_oncharge(name)
                    or any(kw in name.lower() for kw in _HYD_EQUIP_KW)):
                continue
            col = _hyd_cons_col(name)
            cons_by_col[col] = cons_by_col.get(col, 0.0) + (c.get("cost_total") or 0.0)

        our_total  = s.get("our_total") or 0.0
        flights_cost, freight_cost, oncharge_cost = _flights_freight_oncharge(sub["consumables"])

        row = {
            "PLOD ID":                    p["id"],
            "Rig":                        p["short_name"],
            "Date":                       p["date"],
            "Hole 1":                     holes[0],
            "Hole 2":                     holes[1],
            "Hole 3":                     holes[2],
            "Hole 4":                     holes[3],
            "Driller":                    _driller(sub["people"]),
            "Personnel":                  len(sub["people"]),
            "Accom Cost":                 s.get("our_accommodation"),
            **diam_m,
            "Total Daily Metres":         total_metres,
            "Drilling Cost (CP)":         cp_drill_cost,
            "Drill Time (hrs)":           drill_time,
            "Charged Drilling Cost":      s.get("our_drilling_cost"),
            "Slow Drilling":              "🚩" if s.get("slow_drilling") else "",
            "Aux Equipment Cost":          aux_cost,
            "Azi Aligner Cost":           equip.get("Azi Aligner (p/day)") or None,
            "Gyro Cost":                  equip.get("Gyro (p/day)") or None,
            **tbreak,
            "Total Hours":                total_hours,
            "Total Activity Hours Cost":  s.get("our_time_cost"),
            **cons_by_col,
            "Total Equipment Cost":       s.get("our_equipment_cost"),
            "Total Consumables":          s.get("our_consumables"),
            "Consumables On-Charges":     oncharge_cost,
            "Flights":                    flights_cost,
            "Freight":                    freight_cost,
            "_cons_tooltip": _cons_tooltip(sub["consumables"]),
            "Total Costs":                our_total,
            "Variance ($)":               s.get("variance"),
            "Variance (%)":               s.get("variance_pct"),
            "Operational Cost Per Metre":  (
                                              (s.get("our_drilling_cost") or 0)
                                              + (s.get("our_equipment_cost") or 0)
                                              + (s.get("our_time_cost") or 0)
                                          ) / total_metres if total_metres else None,
            "PLOD Link":                  p.get("plod_ref"),
            "Notes":                      p.get("notes"),
        }

        # Per-hole detail columns (far right)
        for i, hole_name in enumerate(holes, 1):
            hdm = hole_diam_m.get(hole_name or "", {})
            row[f"H{i} Name"]    = hole_name
            row[f"H{i} Purpose"] = hp.get(hole_name or "", "") if hole_name else ""
            for col, _ in HYD_DIAMETERS:
                row[f"H{i} {col}"] = hdm.get(col) if hole_name else None
            row[f"H{i} Total m"] = sum(hdm.values()) if hole_name else None

        rows.append(row)

    return pd.DataFrame(rows)
