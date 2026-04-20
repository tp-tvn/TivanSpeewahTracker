"""
Compute cost summary from parsed PLOD data.

Our total = charged drilling + equipment + activity time + consumables + accommodation + on-charges + flights + freight.
Variance = our_total - CorePlan total.
"""

import db

_ACCOM_KEYWORDS  = ("accommodation", "messing", "camp")
_EQUIP_KEYWORDS  = ("booster", "compressor", "azi aligner", "azimuth aligner", "gyro", "survey camera")
_FLIGHT_KEYWORDS   = ("flight",)
_FREIGHT_KEYWORDS  = ("freight",)
_ONCHARGE_KEYWORDS = ("on-charg",)


# Depth-band → rate category mapping for RC
_RC_BAND_RATES = [
    (0,   50,  "drilling_0_50"),
    (50,  100, "drilling_50_100"),
    (100, 150, "drilling_100_150"),
    (150, 200, "drilling_150_200"),
    (200, 250, "drilling_200_250"),
    (250, 300, "drilling_250_300"),
]

# Interval-type prefix → rate category for DD
_DD_TYPE_RATES = {"PQ": "drilling_pq3", "HQ": "drilling_hq3", "NQ": "drilling_nq3"}

# Diameter substring → rate category for HYD
_HYD_DIAM_RATES = {
    "381": "drilling_381mm",
    "312": "drilling_312mm",
    "230": "drilling_230mm",
    "150": "drilling_150mm",
}


def drilling_cost_from_rates(drilling: list[dict], rig_id: int, rig_type: str,
                             default_interval_type: str = "") -> float:
    """Compute drilling cost from our rate table (metres × rate per bracket/type)."""
    rates   = db.get_rates(rig_id=rig_id)
    by_cat  = {r["category"]: float(r["rate"] or 0.0) for r in rates}
    total   = 0.0

    if rig_type == "RC":
        for d in drilling:
            d_from = d.get("depth_from") or 0.0
            d_to   = d.get("depth_to")   or 0.0
            for lo, hi, cat in _RC_BAND_RATES:
                overlap = min(d_to, hi) - max(d_from, lo)
                if overlap > 0:
                    total += overlap * by_cat.get(cat, 0.0)

    elif rig_type == "DD":
        for d in drilling:
            # Use stored interval_type; fall back to rig's default if CorePlan left it blank
            itype  = (d.get("interval_type") or default_interval_type or "").upper()
            metres = d.get("length_m") or 0.0
            for prefix, cat in _DD_TYPE_RATES.items():
                if prefix in itype:
                    total += metres * by_cat.get(cat, 0.0)
                    break

    elif rig_type == "HYD":
        for d in drilling:
            itype  = d.get("interval_type") or ""
            metres = d.get("length_m") or 0.0
            for diam, cat in _HYD_DIAM_RATES.items():
                if diam in itype:
                    total += metres * by_cat.get(cat, 0.0)
                    break

    return total


def _item_is(name: str, keywords: tuple) -> bool:
    n = name.lower()
    return any(kw in n for kw in keywords)


def _get_active_rate(rig_id: int) -> float:
    """Return the active rig rate ($/hr) for the given rig, or 0 if not found."""
    rates = db.get_rates(rig_id=rig_id)
    for r in rates:
        if r.get("category") == "active_rig":
            return float(r.get("rate") or 0.0)
    return 0.0


def compute_summary(plod_id: int, parsed: dict) -> dict:
    drilling    = parsed.get("drilling",    [])
    time_rows   = parsed.get("time_rows",   [])
    consumables = parsed.get("consumables", [])
    equipment   = parsed.get("equipment",   [])
    rig         = parsed.get("rig",         {})

    # ── Drilling ────────────────────────────────────────────────────────────
    metres_drilled   = sum(r.get("length_m")   or 0.0 for r in drilling)
    drill_time_hrs   = sum(r.get("duration_h") or 0.0 for r in drilling)
    drilling_cost_rated = drilling_cost_from_rates(
        drilling, rig.get("id", 0), rig.get("rig_type", ""),
        rig.get("default_interval_type", "")
    )

    active_rate       = _get_active_rate(rig.get("id", 0))
    time_based_cost   = drill_time_hrs * active_rate
    our_drilling_cost = max(drilling_cost_rated, time_based_cost)
    slow_drilling     = time_based_cost > drilling_cost_rated

    # ── Activity time ────────────────────────────────────────────────────────
    our_time_cost = sum(r.get("cost_cp") or 0.0 for r in time_rows)

    # ── Equipment ────────────────────────────────────────────────────────────
    # Equipment table costs + any equipment items that CorePlan lists under consumables
    equip_from_table = sum(r.get("cost_cp")    or 0.0 for r in equipment)
    equip_from_cons  = sum(
        r.get("cost_total") or 0.0 for r in consumables
        if _item_is(r.get("item_name") or "", _EQUIP_KEYWORDS)
    )
    our_equipment_cost = equip_from_table + equip_from_cons

    # ── Accommodation (tracked separately, not in our_total) ─────────────────
    our_accommodation = sum(
        r.get("cost_total") or 0.0 for r in consumables
        if _item_is(r.get("item_name") or "", _ACCOM_KEYWORDS)
    )

    # ── Flights & freight (included in our_total, shown as own columns) ──────
    flights = sum(
        r.get("cost_total") or 0.0 for r in consumables
        if _item_is(r.get("item_name") or "", _FLIGHT_KEYWORDS)
    )
    freight = sum(
        r.get("cost_total") or 0.0 for r in consumables
        if _item_is(r.get("item_name") or "", _FREIGHT_KEYWORDS)
    )
    oncharges = sum(
        r.get("cost_total") or 0.0 for r in consumables
        if _item_is(r.get("item_name") or "", _ONCHARGE_KEYWORDS)
    )

    # ── Consumables (everything else — excl. accom, equipment, flights, freight, on-charges)
    our_consumables = sum(
        r.get("cost_total") or 0.0 for r in consumables
        if not _item_is(r.get("item_name") or "", _ACCOM_KEYWORDS)
        and not _item_is(r.get("item_name") or "", _EQUIP_KEYWORDS)
        and not _item_is(r.get("item_name") or "", _FLIGHT_KEYWORDS)
        and not _item_is(r.get("item_name") or "", _FREIGHT_KEYWORDS)
        and not _item_is(r.get("item_name") or "", _ONCHARGE_KEYWORDS)
    )

    # ── Totals & variance ────────────────────────────────────────────────────
    cp_total  = parsed.get("coreplan_total") or 0.0
    our_total = (
        our_drilling_cost
        + our_equipment_cost
        + our_time_cost
        + our_consumables
        + our_accommodation
        + oncharges
        + flights
        + freight
    )

    variance     = our_total - cp_total
    variance_pct = (variance / cp_total * 100) if cp_total else 0.0

    return {
        "metres_drilled":      metres_drilled,
        "our_drilling_cost":   our_drilling_cost,
        "our_time_cost":       our_time_cost,
        "our_equipment_cost":  our_equipment_cost,
        "our_consumables":     our_consumables,
        "our_accommodation":   our_accommodation,
        "our_total":           our_total,
        "coreplan_total":      cp_total,
        "variance":            variance,
        "variance_pct":        variance_pct,
        "slow_drilling":       slow_drilling,
    }
