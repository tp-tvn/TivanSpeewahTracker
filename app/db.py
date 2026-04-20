"""Database layer - SQLite setup and all CRUD operations."""
import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent / "drill_costs.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS rigs (
        id                   INTEGER PRIMARY KEY,
        name                 TEXT NOT NULL UNIQUE,   -- e.g. "Strike Rig 18"
        short_name           TEXT NOT NULL UNIQUE,   -- e.g. "STR RIG 18"
        rig_type             TEXT NOT NULL,          -- RC, DD, HYD
        contract             TEXT,
        rate_group           TEXT,                   -- e.g. "Strike RC", "DDH1 DD", "Hyd"
        default_interval_type TEXT                   -- RC, PQ3, HQ3, NQ3, HYD — overrides rig_type for target lookup
    );

    CREATE TABLE IF NOT EXISTS rates (
        id              INTEGER PRIMARY KEY,
        rig_id          INTEGER NOT NULL REFERENCES rigs(id),
        category        TEXT NOT NULL,   -- e.g. "drilling_0_50", "active_rig", "booster"
        label           TEXT NOT NULL,   -- human-readable label
        rate            REAL NOT NULL,
        unit            TEXT NOT NULL,   -- "$/m", "$/hr", "$/day", "$/person/day"
        effective_date  TEXT NOT NULL DEFAULT (date('now')),
        UNIQUE(rig_id, category, effective_date)
    );

    CREATE TABLE IF NOT EXISTS plods (
        id              INTEGER PRIMARY KEY,
        plod_ref        TEXT NOT NULL UNIQUE,   -- e.g. "6174-250624D"
        date            TEXT NOT NULL,
        rig_id          INTEGER NOT NULL REFERENCES rigs(id),
        shift           TEXT,
        coreplan_total  REAL,
        engine_h_start  REAL,
        engine_h_end    REAL,
        contract        TEXT,
        notes           TEXT,
        imported_at     TEXT NOT NULL DEFAULT (datetime('now')),
        source_file     TEXT
    );

    CREATE TABLE IF NOT EXISTS drilling_intervals (
        id              INTEGER PRIMARY KEY,
        plod_id         INTEGER NOT NULL REFERENCES plods(id),
        hole_name       TEXT,
        depth_from      REAL,
        depth_to        REAL,
        length_m        REAL,           -- depth_to - depth_from
        interval_type   TEXT,           -- RC, PQ3, HQ3, NQ etc.
        duration_h      REAL,
        cost_per_m_cp   REAL,           -- CorePlan's rate
        cost_cp         REAL,           -- CorePlan's calculated cost
        drill_bit       TEXT,
        end_of_hole     INTEGER         -- 0/1
    );

    CREATE TABLE IF NOT EXISTS time_breakdown (
        id              INTEGER PRIMARY KEY,
        plod_id         INTEGER NOT NULL REFERENCES plods(id),
        hole_name       TEXT,
        category        TEXT,
        duration_h      REAL,
        rate_cp         REAL,           -- CorePlan's $/hr
        cost_cp         REAL            -- CorePlan's cost
    );

    CREATE TABLE IF NOT EXISTS consumables (
        id              INTEGER PRIMARY KEY,
        plod_id         INTEGER NOT NULL REFERENCES plods(id),
        hole_name       TEXT,
        item_name       TEXT,
        quantity        REAL,
        unit            TEXT,
        cost_per_unit   REAL,
        cost_total      REAL
    );

    CREATE TABLE IF NOT EXISTS equipment (
        id              INTEGER PRIMARY KEY,
        plod_id         INTEGER NOT NULL REFERENCES plods(id),
        hole_name       TEXT,
        equipment_name  TEXT,
        duration_h      REAL,
        cost_cp         REAL,
        time_period     TEXT            -- "Per Hour", "Per Day Per Rig" etc.
    );

    CREATE TABLE IF NOT EXISTS people (
        id              INTEGER PRIMARY KEY,
        plod_id         INTEGER NOT NULL REFERENCES plods(id),
        person_name     TEXT,
        duration_h      REAL,
        is_supervisor   INTEGER,
        job_role        TEXT
    );

    CREATE TABLE IF NOT EXISTS cost_summary (
        id                  INTEGER PRIMARY KEY,
        plod_id             INTEGER NOT NULL UNIQUE REFERENCES plods(id),
        metres_drilled      REAL,
        our_drilling_cost   REAL,
        our_time_cost       REAL,
        our_equipment_cost  REAL,
        our_consumables     REAL,
        our_accommodation   REAL,
        our_total           REAL,
        coreplan_total      REAL,
        variance            REAL,       -- our_total - coreplan_total
        variance_pct        REAL
    );
    """)

    conn.commit()
    _migrate(conn)
    _seed_rigs_and_rates(conn)
    _dedup_rates(conn)
    conn.close()


def _migrate(conn):
    """Apply any schema migrations needed for existing databases."""
    cols = [r[1] for r in conn.execute("PRAGMA table_info(rigs)").fetchall()]
    if "rate_group" not in cols:
        conn.execute("ALTER TABLE rigs ADD COLUMN rate_group TEXT")
        conn.commit()
    # Rename legacy rig names to simplified "Rig XX" format
    _rig_renames = [
        ("STR RIG 18",  "RIG 18",       "Strike Rig 18", "Rig 18"),
        ("DDH1 RIG 41", "RIG 41",       "DDH1 Rig 41",   "Rig 41"),
        ("DDH1 RIG 38", "RIG 38",       "DDH1 Rig 38",   "Rig 38"),
        ("HYD RIG 16",  "RIG 16 (HYD)", "Hyd Rig 16",    "Rig 16 (HYD)"),
        ("HYD RIG 18",  "RIG 18 (HYD)", "Hyd Rig 18",    "Rig 18 (HYD)"),
    ]
    for old_short, new_short, old_name, new_name in _rig_renames:
        conn.execute(
            "UPDATE rigs SET short_name=?, name=? WHERE short_name=?",
            (new_short, new_name, old_short),
        )
    conn.commit()

    # Backfill rate_group from seeded defaults
    defaults = {
        "RIG 18":       "Strike RC",
        "RIG 41":       "DDH1 DD",
        "RIG 38":       "DDH1 DD",
        "RIG 16 (HYD)": "Hyd",
        "RIG 18 (HYD)": "Hyd",
    }
    for short_name, group in defaults.items():
        conn.execute(
            "UPDATE rigs SET rate_group=? WHERE short_name=? AND rate_group IS NULL",
            (group, short_name),
        )
    conn.commit()
    # Add default_interval_type to rigs if missing
    if "default_interval_type" not in cols:
        conn.execute("ALTER TABLE rigs ADD COLUMN default_interval_type TEXT")
        conn.commit()
    _default_interval_defaults = {
        "RIG 18":       "RC",
        "RIG 41":       "PQ3",
        "RIG 38":       "PQ3",
        "RIG 16 (HYD)": "HYD",
        "RIG 18 (HYD)": "HYD",
    }
    for short_name, itype in _default_interval_defaults.items():
        conn.execute(
            "UPDATE rigs SET default_interval_type=? WHERE short_name=? AND default_interval_type IS NULL",
            (itype, short_name),
        )
    conn.commit()
    plod_cols = [r[1] for r in conn.execute("PRAGMA table_info(plods)").fetchall()]
    if "drill_purpose" not in plod_cols:
        conn.execute("ALTER TABLE plods ADD COLUMN drill_purpose TEXT")
        conn.commit()
    cs_cols = [r[1] for r in conn.execute("PRAGMA table_info(cost_summary)").fetchall()]
    if "slow_drilling" not in cs_cols:
        conn.execute("ALTER TABLE cost_summary ADD COLUMN slow_drilling INTEGER DEFAULT 0")
        conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hole_purposes (
            hole_name TEXT PRIMARY KEY,
            purpose   TEXT,
            hole_type TEXT
        )
    """)

    # Migration: Add hole_type column if it doesn't exist
    hp_cols = [col[1] for col in conn.execute("PRAGMA table_info(hole_purposes)").fetchall()]
    if "hole_type" not in hp_cols:
        conn.execute("ALTER TABLE hole_purposes ADD COLUMN hole_type TEXT")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS planned_drilling (
            hole_name TEXT PRIMARY KEY,
            planned_metres REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budget_targets (
            drill_type   TEXT NOT NULL,
            hole_type    TEXT NOT NULL,
            budget_per_m REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (drill_type, hole_type)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ignored_rate_combinations (
            drill_type TEXT NOT NULL,
            hole_type  TEXT NOT NULL,
            reason     TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (drill_type, hole_type)
        )
    """)

    # Migration: Migrate from old (purpose, drill_type) schema to new (drill_type, hole_type) schema
    bt_cols = [r[1] for r in conn.execute("PRAGMA table_info(budget_targets)").fetchall()]
    if "purpose" in bt_cols:
        # Old schema exists - migrate it
        # Move old data to a backup, create new table, then convert data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_targets_old AS
            SELECT * FROM budget_targets
        """)
        conn.execute("DROP TABLE budget_targets")
        conn.execute("""
            CREATE TABLE budget_targets (
                drill_type   TEXT NOT NULL,
                hole_type    TEXT NOT NULL,
                budget_per_m REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (drill_type, hole_type)
            )
        """)
        # The old data had purpose as the hole type name, so we can map it
        # For now, we'll just create empty table and let user re-enter via UI
        conn.commit()
    elif "rate_group" in bt_cols:
        # Even older schema - just recreate
        conn.execute("DROP TABLE IF EXISTS budget_targets")
        conn.execute("""
            CREATE TABLE budget_targets (
                drill_type   TEXT NOT NULL,
                hole_type    TEXT NOT NULL,
                budget_per_m REAL NOT NULL DEFAULT 0,
                PRIMARY KEY (drill_type, hole_type)
            )
        """)
        conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metres_targets (
            drill_type      TEXT PRIMARY KEY,
            metres_per_shift REAL NOT NULL DEFAULT 0
        )
    """)
    mt_cols = [r[1] for r in conn.execute("PRAGMA table_info(metres_targets)").fetchall()]
    if "purpose" in mt_cols and "drill_type" not in mt_cols:
        conn.execute("ALTER TABLE metres_targets RENAME COLUMN purpose TO drill_type")
        conn.commit()
    mt_cols = [r[1] for r in conn.execute("PRAGMA table_info(metres_targets)").fetchall()]
    if "metres_per_day" in mt_cols and "metres_per_shift" not in mt_cols:
        conn.execute("ALTER TABLE metres_targets RENAME COLUMN metres_per_day TO metres_per_shift")
        conn.commit()
    mt_cols = [r[1] for r in conn.execute("PRAGMA table_info(metres_targets)").fetchall()]
    if "slow_threshold_m_per_hr" not in mt_cols:
        conn.execute("ALTER TABLE metres_targets ADD COLUMN slow_threshold_m_per_hr REAL NOT NULL DEFAULT 0")
        conn.commit()
    # NEW TABLE: One row per purpose with separate columns for each activity type
    conn.execute("""
        CREATE TABLE IF NOT EXISTS purpose_budgets (
            purpose                         TEXT NOT NULL PRIMARY KEY,

            drilling_work_group             TEXT DEFAULT '',
            drilling_budget                 REAL NOT NULL DEFAULT 0,
            drilling_start_date             TEXT,
            drilling_end_date               TEXT,

            earthworks_work_group           TEXT DEFAULT '',
            earthworks_budget               REAL NOT NULL DEFAULT 0,
            earthworks_start_date           TEXT,
            earthworks_end_date             TEXT,

            fuel_budget                     REAL NOT NULL DEFAULT 0,
            fuel_start_date                 TEXT,
            fuel_end_date                   TEXT,

            in_scope                        INTEGER NOT NULL DEFAULT 1,
            notes                           TEXT,
            currency                        TEXT NOT NULL DEFAULT 'AUD',
            created_at                      TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at                      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Migration: Migrate data from old table if it exists
    try:
        old_cols = [r[1] for r in conn.execute("PRAGMA table_info(purpose_budget_allocations)").fetchall()]
        if old_cols:  # Old table exists
            # Check if migration already done
            new_cols = [r[1] for r in conn.execute("PRAGMA table_info(purpose_budgets)").fetchall()]
            if len(new_cols) > 3:  # If new table has data
                # Get all purposes from new table
                existing = set(r[0] for r in conn.execute("SELECT purpose FROM purpose_budgets").fetchall())

                # Migrate from old table, only if not already migrated
                old_purposes = conn.execute("SELECT DISTINCT purpose FROM purpose_budget_allocations").fetchall()
                for (purpose,) in old_purposes:
                    if purpose not in existing:
                        old_data = conn.execute(
                            "SELECT * FROM purpose_budget_allocations WHERE purpose = ? LIMIT 1",
                            (purpose,)
                        ).fetchone()

                        if old_data:
                            conn.execute("""
                                INSERT OR REPLACE INTO purpose_budgets
                                (purpose, drilling_budget, earthworks_budget, fuel_budget, in_scope, notes, currency, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (purpose, old_data["drilling_budget"], old_data["earthworks_budget"],
                                  old_data["fuel_budget"], old_data["in_scope"], old_data["notes"],
                                  old_data["currency"], old_data["created_at"], old_data["updated_at"]))

                conn.commit()
    except:
        pass  # Old table doesn't exist, that's fine

    conn.commit()
    # Add raw_hole_name to child tables (stores original hole ID before normalisation)
    for table in ("drilling_intervals", "time_breakdown", "consumables", "equipment"):
        t_cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if "raw_hole_name" not in t_cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN raw_hole_name TEXT")
    conn.commit()
    # Feedback table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id            INTEGER PRIMARY KEY,
            submitted_at  TEXT NOT NULL DEFAULT (datetime('now')),
            name          TEXT,
            category      TEXT NOT NULL,
            message       TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'Open',
            auto_response TEXT,
            admin_response TEXT,
            responded_at  TEXT
        )
    """)
    conn.commit()
    # ── Earthworks tables ────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_contractors (
            id    INTEGER PRIMARY KEY,
            name  TEXT NOT NULL UNIQUE,
            notes TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_daily (
            id                  INTEGER PRIMARY KEY,
            date                TEXT NOT NULL,
            contractor_id       INTEGER NOT NULL REFERENCES ew_contractors(id),
            supervisor          TEXT,
            works_description   TEXT,
            location            TEXT,
            area                TEXT,
            start_time          TEXT,
            end_time            TEXT,
            additional_comments TEXT,
            principal_name      TEXT,
            source_filename     TEXT,
            is_historical       INTEGER NOT NULL DEFAULT 0,
            imported_at         TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(date, contractor_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_production (
            id          INTEGER PRIMARY KEY,
            daily_id    INTEGER NOT NULL REFERENCES ew_daily(id) ON DELETE CASCADE,
            roads_km    REAL NOT NULL DEFAULT 0,
            tracks_km   REAL NOT NULL DEFAULT 0,
            pads_count  INTEGER NOT NULL DEFAULT 0,
            sumps_pits  INTEGER NOT NULL DEFAULT 0,
            notes       TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_misc (
            id          INTEGER PRIMARY KEY,
            daily_id    INTEGER NOT NULL REFERENCES ew_daily(id) ON DELETE CASCADE,
            item_name   TEXT NOT NULL,
            quantity    TEXT,
            notes       TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_equipment_rates (
            id              INTEGER PRIMARY KEY,
            contractor_id   INTEGER NOT NULL REFERENCES ew_contractors(id),
            equipment_name  TEXT NOT NULL,
            plant_rate      REAL NOT NULL DEFAULT 0,
            operator_rate   REAL NOT NULL DEFAULT 0,
            standby_rate    REAL NOT NULL DEFAULT 0,
            mob_cost        REAL NOT NULL DEFAULT 0,
            demob_cost      REAL NOT NULL DEFAULT 0,
            UNIQUE(contractor_id, equipment_name)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_entries (
            id                INTEGER PRIMARY KEY,
            daily_id          INTEGER REFERENCES ew_daily(id) ON DELETE CASCADE,
            date              TEXT NOT NULL,
            contractor_id     INTEGER NOT NULL REFERENCES ew_contractors(id),
            equipment_name    TEXT NOT NULL,
            mobilised         INTEGER NOT NULL DEFAULT 0,
            demobilised       INTEGER NOT NULL DEFAULT 0,
            active_hours      REAL NOT NULL DEFAULT 0,
            standdown_hours   REAL NOT NULL DEFAULT 0,
            breakdown_hours   REAL NOT NULL DEFAULT 0,
            unavailable_hours REAL NOT NULL DEFAULT 0,
            total_hours       REAL NOT NULL DEFAULT 0,
            mob_cost          REAL NOT NULL DEFAULT 0,
            operating_cost    REAL NOT NULL DEFAULT 0,
            standdown_cost    REAL NOT NULL DEFAULT 0,
            accommodation     REAL NOT NULL DEFAULT 0,
            total_cost        REAL NOT NULL DEFAULT 0,
            hourmeter_start   REAL,
            hourmeter_end     REAL,
            notes             TEXT,
            is_historical     INTEGER NOT NULL DEFAULT 0,
            UNIQUE(date, contractor_id, equipment_name)
        )
    """)
    # Migrate ew_entries: add new columns if upgrading from older schema
    _ew_cols = [r[1] for r in conn.execute("PRAGMA table_info(ew_entries)").fetchall()]
    for _col, _def in [
        ("daily_id",        "INTEGER"),
        ("breakdown_hours", "REAL NOT NULL DEFAULT 0"),
        ("hourmeter_start", "REAL"),
        ("hourmeter_end",   "REAL"),
    ]:
        if _col not in _ew_cols:
            conn.execute(f"ALTER TABLE ew_entries ADD COLUMN {_col} {_def}")
    conn.commit()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_pads (
            id            INTEGER PRIMARY KEY,
            date          TEXT NOT NULL,
            contractor_id INTEGER REFERENCES ew_contractors(id),
            pad_id        TEXT NOT NULL,
            notes         TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ew_ocr_corrections (
            id               INTEGER PRIMARY KEY,
            created_at       TEXT NOT NULL DEFAULT (datetime('now')),
            field            TEXT NOT NULL,
            equipment_name   TEXT,
            extracted_value  TEXT,
            corrected_value  TEXT,
            source_filename  TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS weather_events (
            id              INTEGER PRIMARY KEY,
            date            TEXT NOT NULL,
            shift           TEXT,                  -- e.g. 'Morning', 'Afternoon', 'Night' or NULL for whole day
            event_type      TEXT NOT NULL,        -- 'rain', 'thunderstorm', 'sunny', etc.
            severity        TEXT,                 -- 'light', 'moderate', 'heavy' for rain; 'severe' for thunderstorm
            notes           TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    # Seed default earthworks contractors
    for cname in ("MDM", "NGCM"):
        conn.execute(
            "INSERT OR IGNORE INTO ew_contractors (name) VALUES (?)", (cname,)
        )
    conn.commit()
    # Seed 2026 MDM rates
    _mdm = conn.execute("SELECT id FROM ew_contractors WHERE name='MDM'").fetchone()
    if _mdm:
        _mdm_id = _mdm["id"]
        _mdm_rates = [
            # (equipment_name, plant_rate, operator_rate, standby_rate, mob_cost, demob_cost)
            ("336 Excavator", 90.2,  110.0, 100.0, 2660.0, 2660.0),
            ("D7 Dozer",      130.9, 110.0, 100.0, 2660.0, 2660.0),
            ("D8 Dozer",      154.0, 110.0, 100.0, 2660.0, 2660.0),
            ("D9 Dozer",      184.8, 110.0, 100.0, 3143.0, 3143.0),
            ("16H Grader",    123.2, 110.0, 100.0, 2660.0, 2660.0),
            ("Tip Truck",       0.0, 110.0, 100.0, 2660.0, 2660.0),
            ("Service Truck",   0.0, 110.0, 100.0, 2660.0, 2660.0),
            ("Survey Trailer",120.0,   0.0,   0.0,    0.0,    0.0),
            ("LV",            100.0,   0.0,   0.0,    0.0,    0.0),
            ("Base Station",  120.0,   0.0,   0.0,    0.0,    0.0),
            ("Fitter",          0.0, 176.0,   0.0,    0.0,    0.0),
            ("Rockbreaker",   220.0,   0.0,   0.0,    0.0,    0.0),
        ]
        for row in _mdm_rates:
            conn.execute(
                "INSERT OR IGNORE INTO ew_equipment_rates "
                "(contractor_id, equipment_name, plant_rate, operator_rate, standby_rate, mob_cost, demob_cost) "
                "VALUES (?,?,?,?,?,?,?)",
                (_mdm_id, *row)
            )
    conn.commit()
    # Seed default admin password ("admin") if not already set
    import hashlib as _hl
    if not conn.execute("SELECT 1 FROM settings WHERE key='admin_password'").fetchone():
        conn.execute(
            "INSERT INTO settings (key, value) VALUES ('admin_password', ?)",
            (_hl.sha256(b"admin").hexdigest(),)
        )
        conn.commit()
    # Seed default branding
    for key, val in [("app_title", "Tivan Dashboard"), ("app_subtitle", "Tivan Tracking Tool · Tivan Limited")]:
        if not conn.execute("SELECT 1 FROM settings WHERE key=?", (key,)).fetchone():
            conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, val))
    conn.commit()


def _seed_rigs_and_rates(conn):
    """Insert default rigs and rates extracted from the tracker. Only runs once."""
    c = conn.cursor()

    rigs = [
        ("Rig 18",       "RIG 18",       "RC",  "Speewah Mining Strike RC (start 1 June 2025)", "Strike RC", "RC"),
        ("Rig 41",       "RIG 41",       "DD",  "Speewah Mining DDH1 Rig 41",                   "DDH1 DD",   "PQ3"),
        ("Rig 38",       "RIG 38",       "DD",  "Speewah Mining DDH1 Rig 38",                   "DDH1 DD",   "PQ3"),
        ("Rig 16 (HYD)", "RIG 16 (HYD)", "HYD", "Speewah Mining Hyd Rig 16",                   "Hyd",       "HYD"),
        ("Rig 18 (HYD)", "RIG 18 (HYD)", "HYD", "Speewah Mining Hyd Rig 18",                   "Hyd",       "HYD"),
    ]
    for name, short, rtype, contract, rate_group, def_itype in rigs:
        c.execute(
            "INSERT OR IGNORE INTO rigs (name, short_name, rig_type, contract, rate_group, default_interval_type) VALUES (?,?,?,?,?,?)",
            (name, short, rtype, contract, rate_group, def_itype)
        )
    conn.commit()

    # Rates per rig type - keyed by short_name
    rate_data = {
        "STR RIG 18": [
            ("accommodation",   "Accommodation",            130.0,  "$/person/day"),
            ("drilling_0_50",   "Drilling 0–50 m",           40.0,  "$/m"),
            ("drilling_50_100", "Drilling 50–100 m",         45.0,  "$/m"),
            ("drilling_100_150","Drilling 100–150 m",        50.0,  "$/m"),
            ("drilling_150_200","Drilling 150–200 m",        55.0,  "$/m"),
            ("drilling_200_250","Drilling 200–250 m",        60.0,  "$/m"),
            ("drilling_250_300","Drilling 250–300 m",        65.0,  "$/m"),
            ("active_rig",      "Active Rig Rate",          575.0,  "$/hr"),
            ("inactive",        "Inactive / Supervisor",    360.0,  "$/hr"),
            ("standby",         "Standby",                  360.0,  "$/hr"),
            ("non_charged",     "Non-Charged",                0.0,  "$/hr"),
            ("booster",         "Auxiliary Booster",        110.0,  "$/hr"),
            ("aux_compressor",  "Auxiliary Compressor",     110.0,  "$/hr"),
            ("azi_aligner",     "Azi Aligner",              175.0,  "$/day"),
            ("gyro",            "Gyro Tool",                420.0,  "$/day"),
        ],
        "DDH1 RIG 41": [
            ("accommodation",   "Accommodation",            130.0,  "$/person/day"),
            ("drilling_pq3",    "Drilling PQ3",             175.0,  "$/m"),
            ("drilling_hq3",    "Drilling HQ3",             135.0,  "$/m"),
            ("active_rig",      "Active Rig Rate",          460.0,  "$/hr"),
            ("inactive",        "Inactive",                 360.0,  "$/hr"),
            ("standby",         "Standby",                  360.0,  "$/hr"),
            ("non_charged",     "Non-Charged",                0.0,  "$/hr"),
            ("pq_ori_tool",     "PQ Orientation Tool",      175.0,  "$/use"),
            ("hq_ori_tool",     "HQ Orientation Tool",      155.0,  "$/use"),
            ("gyro",            "Gyro Tool",                420.0,  "$/use"),
        ],
        "DDH1 RIG 38": [
            ("accommodation",   "Accommodation",            130.0,  "$/person/day"),
            ("drilling_pq3",    "Drilling PQ3",             175.0,  "$/m"),
            ("drilling_hq3",    "Drilling HQ3",             135.0,  "$/m"),
            ("active_rig",      "Active Rig Rate",          460.0,  "$/hr"),
            ("inactive",        "Inactive",                 360.0,  "$/hr"),
            ("standby",         "Standby",                  360.0,  "$/hr"),
            ("non_charged",     "Non-Charged",                0.0,  "$/hr"),
            ("pq_ori_tool",     "PQ Orientation Tool",      175.0,  "$/use"),
            ("hq_ori_tool",     "HQ Orientation Tool",      155.0,  "$/use"),
            ("gyro",            "Gyro Tool",                420.0,  "$/use"),
        ],
        "HYD RIG 16": [
            ("accommodation",       "Accommodation",                180.0,  "$/person/day"),
            ("drilling_381mm",      'Drilling 14.5" (381 mm)',      295.0,  "$/m"),
            ("drilling_312mm",      'Drilling 12.5" (312 mm)',      185.0,  "$/m"),
            ("drilling_230mm",      'Drilling 9.5" (230 mm)',       295.0,  "$/m"),
            ("drilling_150mm",      'Drilling 6" (150 mm)',         135.0,  "$/m"),
            ("active_rig",          "Active Rig Rate",              950.0,  "$/hr"),
            ("inactive",            "Inactive",                     360.0,  "$/hr"),
            ("standby",             "Standby",                      420.0,  "$/hr"),
            ("non_charged",         "Non-Charged",                    0.0,  "$/hr"),
            ("survey_camera",       "Survey Camera",                950.0,  "$/day"),
            ("pvc_100_plain",       "PVC 100 mm Plain Casing",       32.0,  "$/m"),
            ("pvc_100_slotted",     "PVC 100 mm Slotted Casing",     44.0,  "$/m"),
            ("end_cap_200mm",       "200 mm Top/End Cap",           187.0,  "$/unit"),
            ("steel_casing_350nb",  "Steel Casing 350 NB",          176.0,  "$/m"),
            ("well_cover",          "Steel Well Cover",             925.0,  "$/unit"),
            ("concrete_plinth",     "Concrete Plinth",              600.0,  "$/unit"),
            ("gravel_pack",         "Gravel Pack",                   28.5,  "$/bag"),
            ("casing_centraliser",  "Casing Centraliser",            78.0,  "$/unit"),
            ("drilling_fluids",     "Drilling Fluids",              650.0,  "$/drum"),
            ("bentonite",           "Bentonite Pallets",            187.0,  "$/pallet"),
        ],
        "HYD RIG 18": [
            ("accommodation",       "Accommodation",                180.0,  "$/person/day"),
            ("drilling_381mm",      'Drilling 14.5" (381 mm)',      295.0,  "$/m"),
            ("drilling_312mm",      'Drilling 12.5" (312 mm)',      185.0,  "$/m"),
            ("drilling_230mm",      'Drilling 9.5" (230 mm)',       295.0,  "$/m"),
            ("drilling_150mm",      'Drilling 6" (150 mm)',         135.0,  "$/m"),
            ("active_rig",          "Active Rig Rate",              950.0,  "$/hr"),
            ("inactive",            "Inactive",                     360.0,  "$/hr"),
            ("standby",             "Standby",                      420.0,  "$/hr"),
            ("non_charged",         "Non-Charged",                    0.0,  "$/hr"),
            ("survey_camera",       "Survey Camera",                950.0,  "$/day"),
            ("pvc_100_plain",       "PVC 100 mm Plain Casing",       32.0,  "$/m"),
            ("pvc_100_slotted",     "PVC 100 mm Slotted Casing",     44.0,  "$/m"),
            ("end_cap_200mm",       "200 mm Top/End Cap",           187.0,  "$/unit"),
            ("steel_casing_350nb",  "Steel Casing 350 NB",          176.0,  "$/m"),
            ("well_cover",          "Steel Well Cover",             925.0,  "$/unit"),
            ("concrete_plinth",     "Concrete Plinth",              600.0,  "$/unit"),
            ("gravel_pack",         "Gravel Pack",                   28.5,  "$/bag"),
            ("casing_centraliser",  "Casing Centraliser",            78.0,  "$/unit"),
            ("drilling_fluids",     "Drilling Fluids",              650.0,  "$/drum"),
            ("bentonite",           "Bentonite Pallets",            187.0,  "$/pallet"),
        ],
    }

    for short_name, rates in rate_data.items():
        row = c.execute("SELECT id FROM rigs WHERE short_name=?", (short_name,)).fetchone()
        if not row:
            continue
        rig_id = row["id"]
        # Only seed if this rig has no rates yet
        existing = c.execute("SELECT COUNT(*) FROM rates WHERE rig_id=?", (rig_id,)).fetchone()[0]
        if existing > 0:
            continue
        for cat, label, rate, unit in rates:
            c.execute(
                "INSERT INTO rates (rig_id, category, label, rate, unit) VALUES (?,?,?,?,?)",
                (rig_id, cat, label, rate, unit)
            )
    conn.commit()


def _dedup_rates(conn):
    """Remove duplicate rate rows, keeping the earliest (lowest id) per rig+category."""
    conn.execute("""
        DELETE FROM rates
        WHERE id NOT IN (
            SELECT MIN(id) FROM rates GROUP BY rig_id, category
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_rigs():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM rigs ORDER BY rig_type, name").fetchall()]


def save_rig_default_interval_types(mapping: dict):
    """Update default_interval_type for rigs. mapping: {rig_id: interval_type}"""
    with get_conn() as conn:
        for rig_id, itype in mapping.items():
            conn.execute(
                "UPDATE rigs SET default_interval_type=? WHERE id=?",
                (itype or None, int(rig_id)),
            )
        conn.commit()


def get_plod_date_bounds():
    """Return the earliest and latest PLOD dates in the database."""
    with get_conn() as conn:
        row = conn.execute("SELECT MIN(date) as min_d, MAX(date) as max_d FROM plods").fetchone()
    from datetime import date as _date
    min_d = _date.fromisoformat(row["min_d"]) if row["min_d"] else _date.today()
    max_d = _date.fromisoformat(row["max_d"]) if row["max_d"] else _date.today()
    return min_d, max_d


def get_rigs_with_plods(date_from=None, date_to=None):
    """Return only rigs that have at least one PLOD in the given date range."""
    where = []
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT r.* FROM rigs r "
            f"JOIN plods p ON p.rig_id = r.id "
            f"{where_sql} "
            f"ORDER BY r.rig_type, r.name",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def get_rig_types_with_plods(date_from=None, date_to=None):
    """Return distinct rig_type values that have at least one PLOD in the date range."""
    where = []
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT r.rig_type FROM rigs r "
            f"JOIN plods p ON p.rig_id = r.id "
            f"{where_sql} ORDER BY r.rig_type",
            params,
        ).fetchall()
    return [r["rig_type"] for r in rows]


def update_plod_purpose(plod_id: int, purpose):
    with get_conn() as conn:
        conn.execute("UPDATE plods SET drill_purpose=? WHERE id=?",
                     (purpose or None, plod_id))
        conn.commit()


def get_hole_purposes() -> dict:
    """Return {hole_name: purpose} for all holes with an assigned purpose."""
    with get_conn() as conn:
        rows = conn.execute("SELECT hole_name, purpose FROM hole_purposes").fetchall()
    return {r["hole_name"]: r["purpose"] for r in rows}


def get_planned_metres(hole_name: str) -> float:
    """Get planned metres for a hole."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT planned_metres FROM planned_drilling WHERE hole_name = ?",
            (hole_name,)
        ).fetchone()
    return row["planned_metres"] if row else 0.0


def set_planned_metres(mapping: dict):
    """Upsert {hole_name: planned_metres} mappings."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO planned_drilling (hole_name, planned_metres, updated_at) VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(hole_name) DO UPDATE SET planned_metres=excluded.planned_metres, updated_at=datetime('now')",
            [(k, float(v)) for k, v in mapping.items()],
        )
        conn.commit()


def get_hole_status(hole_name: str) -> str:
    """Determine if hole is 'In Progress' or 'Completed'.
    Completed if no drilling recorded in last 2 consecutive days."""
    with get_conn() as conn:
        # Get the last drilling date for this hole
        last_record = conn.execute(
            "SELECT MAX(p.date) as last_date FROM drilling_intervals di "
            "JOIN plods p ON di.plod_id = p.id "
            "WHERE di.hole_name = ?",
            (hole_name,)
        ).fetchone()

        if not last_record or not last_record["last_date"]:
            return "Not Started"

        last_date = last_record["last_date"]
        # Check if there's any drilling in the last 2 days (from yesterday back)
        two_days_ago = (
            __import__('datetime').datetime.fromisoformat(last_date) -
            __import__('datetime').timedelta(days=2)
        ).date()

        recent_drilling = conn.execute(
            "SELECT COUNT(*) as count FROM drilling_intervals di "
            "JOIN plods p ON di.plod_id = p.id "
            "WHERE di.hole_name = ? AND p.date >= ?",
            (hole_name, str(two_days_ago))
        ).fetchone()

        return "In Progress" if (recent_drilling and recent_drilling["count"] > 0) else "Completed"


def get_holes_without_purpose() -> list:
    """Return list of holes with drilling data but no assigned purpose.
    Includes planned vs actual metres, hole status, and auto-extracted hole_type.
    [{hole_name, actual_m, planned_m, variance_m, drill_hours, rig, interval_type, status, hole_type}]"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT
                DISTINCT di.hole_name,
                SUM(di.length_m) AS actual_m,
                SUM(di.duration_h) AS drill_hours,
                ri.short_name AS rig,
                di.interval_type,
                MIN(p.date) AS first_date,
                MAX(p.date) AS last_date
            FROM drilling_intervals di
            JOIN plods p ON di.plod_id = p.id
            JOIN rigs ri ON p.rig_id = ri.id
            LEFT JOIN hole_purposes hp ON hp.hole_name = di.hole_name
            WHERE hp.hole_name IS NULL
            AND di.hole_name IS NOT NULL AND di.hole_name != ''
            GROUP BY di.hole_name, ri.short_name, di.interval_type
            ORDER BY MAX(p.date) DESC, di.hole_name
        """).fetchall()

    result = []
    for row in rows:
        hole_name = row["hole_name"]
        planned_m = get_planned_metres(hole_name)
        actual_m = row["actual_m"] or 0.0
        variance_m = actual_m - planned_m
        status = get_hole_status(hole_name)
        # Extract hole_type from hole_name (e.g., "SF25_DDRD055" -> "DDRD")
        hole_type = hole_name[5:9] if len(hole_name) >= 9 else ""

        result.append({
            "hole_name": hole_name,
            "actual_m": actual_m,
            "planned_m": planned_m,
            "variance_m": variance_m,
            "drill_hours": row["drill_hours"],
            "rig": row["rig"],
            "interval_type": row["interval_type"],
            "status": status,
            "first_date": row["first_date"],
            "last_date": row["last_date"],
            "hole_type": hole_type,
        })

    return result


def set_hole_purposes(mapping: dict):
    """Upsert hole purposes and hole types.
    Accepts either:
    - {hole_name: purpose} (legacy format)
    - {hole_name: {purpose, hole_type}} (new format with optional hole_type)
    """
    with get_conn() as conn:
        rows = []
        for hole_name, value in mapping.items():
            if isinstance(value, dict):
                purpose = value.get("purpose")
                hole_type = value.get("hole_type")
            else:
                # Legacy format: just purpose string
                purpose = value
                hole_type = None
            rows.append((hole_name, purpose or None, hole_type or None))

        conn.executemany(
            "INSERT INTO hole_purposes (hole_name, purpose, hole_type) VALUES (?,?,?) "
            "ON CONFLICT(hole_name) DO UPDATE SET purpose=excluded.purpose, hole_type=excluded.hole_type",
            rows,
        )
        conn.commit()


def get_unique_holes(plod_ids: list | None = None) -> list:
    """Return sorted unique hole names from drilling_intervals and hole_purposes tables.
    Optionally scoped to specific PLOD IDs (only applies to drilling_intervals)."""
    with get_conn() as conn:
        if plod_ids:
            placeholders = ",".join("?" * len(plod_ids))
            rows = conn.execute(
                f"SELECT DISTINCT hole_name FROM drilling_intervals "
                f"WHERE plod_id IN ({placeholders}) "
                f"AND hole_name IS NOT NULL AND hole_name != '' "
                f"UNION "
                f"SELECT DISTINCT hole_name FROM hole_purposes "
                f"WHERE hole_name IS NOT NULL AND hole_name != '' "
                f"ORDER BY hole_name",
                plod_ids,
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT hole_name FROM drilling_intervals "
                "WHERE hole_name IS NOT NULL AND hole_name != '' "
                "UNION "
                "SELECT DISTINCT hole_name FROM hole_purposes "
                "WHERE hole_name IS NOT NULL AND hole_name != '' "
                "ORDER BY hole_name"
            ).fetchall()
    return [r["hole_name"] for r in rows]


def get_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        conn.commit()


def check_admin_password(password: str) -> bool:
    import hashlib
    h = hashlib.sha256(password.encode()).hexdigest()
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key='admin_password'").fetchone()
    return bool(row and row["value"] == h)


def set_admin_password(new_password: str):
    import hashlib
    h = hashlib.sha256(new_password.encode()).hexdigest()
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('admin_password', ?)", (h,)
        )
        conn.commit()


def get_rate_groups():
    """Return distinct rate groups with one representative rig per group."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT rate_group, rig_type, MIN(id) as rep_rig_id "
            "FROM rigs WHERE rate_group IS NOT NULL "
            "GROUP BY rate_group ORDER BY rig_type, rate_group"
        ).fetchall()
    return [dict(r) for r in rows]


def get_rates_for_group(rate_group: str):
    """Return rates from the representative (lowest-id) rig in the group."""
    with get_conn() as conn:
        rep = conn.execute(
            "SELECT MIN(id) as id FROM rigs WHERE rate_group=?", (rate_group,)
        ).fetchone()
        if not rep:
            return []
        rows = conn.execute(
            "SELECT r.id, r.category, r.label, r.rate, r.unit "
            "FROM rates r WHERE r.rig_id=? ORDER BY r.rowid",
            (rep["id"],)
        ).fetchall()
    return [dict(r) for r in rows]


def get_rates(rig_id=None):
    with get_conn() as conn:
        if rig_id:
            rows = conn.execute(
                "SELECT r.*, ri.name as rig_name, ri.short_name, ri.rig_type "
                "FROM rates r JOIN rigs ri ON r.rig_id=ri.id "
                "WHERE r.rig_id=? ORDER BY r.category",
                (rig_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT r.*, ri.name as rig_name, ri.short_name, ri.rig_type "
                "FROM rates r JOIN rigs ri ON r.rig_id=ri.id "
                "ORDER BY ri.rig_type, ri.name, r.category"
            ).fetchall()
        return [dict(r) for r in rows]


def update_rate(rate_id, new_rate):
    with get_conn() as conn:
        conn.execute("UPDATE rates SET rate=? WHERE id=?", (new_rate, rate_id))
        conn.commit()


def update_rates_for_group(rate_group: str, category_rates: dict):
    """Update rates for all rigs in a group. category_rates = {category: new_rate}."""
    with get_conn() as conn:
        rig_ids = [r[0] for r in conn.execute(
            "SELECT id FROM rigs WHERE rate_group=?", (rate_group,)
        ).fetchall()]
        for rig_id in rig_ids:
            for category, new_rate in category_rates.items():
                conn.execute(
                    "UPDATE rates SET rate=? WHERE rig_id=? AND category=?",
                    (new_rate, rig_id, category)
                )
        conn.commit()


def upsert_rate(rig_id, category, label, rate, unit):
    """Add a new rate category or update existing."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rates (rig_id, category, label, rate, unit) VALUES (?,?,?,?,?) "
            "ON CONFLICT(rig_id, category, effective_date) DO UPDATE SET rate=excluded.rate, label=excluded.label",
            (rig_id, category, label, rate, unit)
        )
        conn.commit()


def get_plod_exists(plod_ref):
    with get_conn() as conn:
        row = conn.execute("SELECT id FROM plods WHERE plod_ref=?", (plod_ref,)).fetchone()
        return row is not None


def get_rig_by_name(name_fragment):
    """Match CorePlan rig name to our rigs table."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM rigs").fetchall()
        name_lower = name_fragment.lower()
        for row in rows:
            if row["short_name"].lower() in name_lower or name_lower in row["name"].lower():
                return dict(row)
            # also try partial token match
            tokens = row["short_name"].lower().split()
            if all(t in name_lower for t in tokens):
                return dict(row)
        return None


def get_daily_summary(date_from=None, date_to=None, rig_id=None, purpose=None):
    where = []
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    if purpose:
        # Handle both single purpose (string) and multiple purposes (list)
        if isinstance(purpose, list):
            placeholders = ",".join(["?"] * len(purpose))
            where.append(
                f"p.id IN ("
                f"  SELECT DISTINCT di.plod_id FROM drilling_intervals di"
                f"  JOIN hole_purposes hp ON hp.hole_name = di.hole_name"
                f"  WHERE hp.purpose IN ({placeholders})"
                f")"
            )
            params.extend(purpose)
        else:
            where.append(
                "p.id IN ("
                "  SELECT DISTINCT di.plod_id FROM drilling_intervals di"
                "  JOIN hole_purposes hp ON hp.hole_name = di.hole_name"
                "  WHERE hp.purpose = ?"
                ")"
            )
            params.append(purpose)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
            p.date,
            ri.short_name        AS rig,
            ri.rig_type,
            cs.metres_drilled,
            cs.our_drilling_cost,
            cs.our_time_cost,
            cs.our_equipment_cost,
            cs.our_consumables,
            cs.our_accommodation,
            cs.our_total,
            cs.coreplan_total,
            cs.variance,
            cs.variance_pct,
            p.plod_ref,
            p.notes
        FROM plods p
        JOIN rigs ri ON p.rig_id = ri.id
        LEFT JOIN cost_summary cs ON cs.plod_id = p.id
        {where_sql}
        ORDER BY p.date, ri.short_name
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_hole_summary(date_from=None, date_to=None, rig_id=None):
    where = ["di.length_m > 0"]
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    where_sql = "WHERE " + " AND ".join(where)

    sql = f"""
        SELECT
            di.hole_name,
            ri.short_name        AS rig,
            ri.rig_type,
            MIN(p.date)          AS first_date,
            MAX(p.date)          AS last_date,
            MAX(di.depth_to)     AS total_m,
            SUM(di.duration_h)   AS drill_hours,
            SUM(di.cost_cp)      AS drill_cost,
            CASE
                WHEN ri.rig_type = 'DD' AND di.interval_type NOT IN ('PQ3','HQ3','NQ3')
                THEN COALESCE(ri.default_interval_type, di.interval_type)
                ELSE di.interval_type
            END                  AS interval_type,
            COUNT(DISTINCT p.id) AS plod_count
        FROM drilling_intervals di
        JOIN plods p ON di.plod_id = p.id
        JOIN rigs ri ON p.rig_id = ri.id
        {where_sql}
        GROUP BY di.hole_name, ri.short_name, ri.rig_type,
                 CASE
                     WHEN ri.rig_type = 'DD' AND di.interval_type NOT IN ('PQ3','HQ3','NQ3')
                     THEN COALESCE(ri.default_interval_type, di.interval_type)
                     ELSE di.interval_type
                 END
        ORDER BY first_date, di.hole_name
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def insert_plod(data: dict) -> int:
    """Insert a plod record and return its id."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO plods (plod_ref,date,rig_id,shift,coreplan_total,"
            "engine_h_start,engine_h_end,contract,notes,source_file) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (data["plod_ref"], data["date"], data["rig_id"], data.get("shift"),
             data.get("coreplan_total"), data.get("engine_h_start"),
             data.get("engine_h_end"), data.get("contract"),
             data.get("notes"), data.get("source_file"))
        )
        plod_id = c.lastrowid
        conn.commit()
        return plod_id


def insert_drilling_intervals(plod_id, rows):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO drilling_intervals "
            "(plod_id,hole_name,raw_hole_name,depth_from,depth_to,length_m,interval_type,"
            "duration_h,cost_per_m_cp,cost_cp,drill_bit,end_of_hole) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            [(plod_id, r["hole_name"], r.get("raw_hole_name"), r["depth_from"], r["depth_to"],
              r["length_m"], r["interval_type"], r["duration_h"],
              r["cost_per_m_cp"], r["cost_cp"], r["drill_bit"], r["end_of_hole"])
             for r in rows]
        )
        conn.commit()


def insert_time_breakdown(plod_id, rows):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO time_breakdown (plod_id,hole_name,raw_hole_name,category,duration_h,rate_cp,cost_cp) "
            "VALUES (?,?,?,?,?,?,?)",
            [(plod_id, r["hole_name"], r.get("raw_hole_name"), r["category"],
              r["duration_h"], r["rate_cp"], r["cost_cp"]) for r in rows]
        )
        conn.commit()


def insert_consumables(plod_id, rows):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO consumables (plod_id,hole_name,raw_hole_name,item_name,quantity,unit,cost_per_unit,cost_total) "
            "VALUES (?,?,?,?,?,?,?,?)",
            [(plod_id, r["hole_name"], r.get("raw_hole_name"), r["item_name"],
              r["quantity"], r["unit"], r["cost_per_unit"], r["cost_total"]) for r in rows]
        )
        conn.commit()


def insert_equipment(plod_id, rows):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO equipment (plod_id,hole_name,raw_hole_name,equipment_name,duration_h,cost_cp,time_period) "
            "VALUES (?,?,?,?,?,?,?)",
            [(plod_id, r["hole_name"], r.get("raw_hole_name"), r["equipment_name"],
              r["duration_h"], r["cost_cp"], r["time_period"]) for r in rows]
        )
        conn.commit()


def insert_people(plod_id, rows):
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO people (plod_id,person_name,duration_h,is_supervisor,job_role) "
            "VALUES (?,?,?,?,?)",
            [(plod_id, r["person_name"], r["duration_h"],
              r["is_supervisor"], r["job_role"]) for r in rows]
        )
        conn.commit()


def delete_plods(plod_ids: list):
    """Delete PLODs and all their child records."""
    if not plod_ids:
        return
    placeholders = ",".join("?" * len(plod_ids))
    with get_conn() as conn:
        for table in ("drilling_intervals", "time_breakdown", "consumables",
                      "equipment", "people", "cost_summary"):
            conn.execute(f"DELETE FROM {table} WHERE plod_id IN ({placeholders})", plod_ids)
        conn.execute(f"DELETE FROM plods WHERE id IN ({placeholders})", plod_ids)
        conn.commit()


def get_plods_list(date_from=None, date_to=None, rig_id=None):
    """Return a flat list of PLODs for display/selection purposes."""
    where, params = [], []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT p.id, p.plod_ref, p.date, p.shift, r.short_name AS rig, "
            f"cs.metres_drilled, cs.our_total, cs.coreplan_total "
            f"FROM plods p JOIN rigs r ON p.rig_id = r.id "
            f"LEFT JOIN cost_summary cs ON cs.plod_id = p.id "
            f"{where_sql} ORDER BY p.date DESC, r.short_name",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def insert_cost_summary(plod_id, summary: dict):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cost_summary "
            "(plod_id,metres_drilled,our_drilling_cost,our_time_cost,"
            "our_equipment_cost,our_consumables,our_accommodation,"
            "our_total,coreplan_total,variance,variance_pct,slow_drilling) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (plod_id, summary["metres_drilled"], summary["our_drilling_cost"],
             summary["our_time_cost"], summary["our_equipment_cost"],
             summary["our_consumables"], summary["our_accommodation"],
             summary["our_total"], summary["coreplan_total"],
             summary["variance"], summary["variance_pct"],
             1 if summary.get("slow_drilling") else 0)
        )
        conn.commit()


def recalculate_all_summaries():
    """Recompute cost_summary for every PLOD using current rates and rig defaults."""
    import calculate
    with get_conn() as conn:
        plods = conn.execute(
            "SELECT p.id, p.plod_ref, r.rig_type, r.default_interval_type "
            "FROM plods p JOIN rigs r ON r.id = p.rig_id"
        ).fetchall()

    updated = 0
    for p in plods:
        plod_id = p["id"]
        with get_conn() as conn:
            drilling    = [dict(r) for r in conn.execute("SELECT * FROM drilling_intervals WHERE plod_id=?", (plod_id,)).fetchall()]
            time_rows   = [dict(r) for r in conn.execute("SELECT * FROM time_breakdown    WHERE plod_id=?", (plod_id,)).fetchall()]
            consumables = [dict(r) for r in conn.execute("SELECT * FROM consumables       WHERE plod_id=?", (plod_id,)).fetchall()]
            equipment   = [dict(r) for r in conn.execute("SELECT * FROM equipment         WHERE plod_id=?", (plod_id,)).fetchall()]
            plod_row    = dict(conn.execute(
                "SELECT p.*, r.id AS rig_id_r, r.rig_type, r.default_interval_type "
                "FROM plods p JOIN rigs r ON r.id = p.rig_id WHERE p.id=?", (plod_id,)
            ).fetchone())

        rig = {
            "id":                   plod_row["rig_id"],
            "rig_type":             plod_row["rig_type"],
            "default_interval_type": plod_row.get("default_interval_type") or "",
        }
        parsed = {
            "drilling":       drilling,
            "time_rows":      time_rows,
            "consumables":    consumables,
            "equipment":      equipment,
            "rig":            rig,
            "coreplan_total": plod_row.get("coreplan_total") or 0.0,
        }
        summary = calculate.compute_summary(plod_id, parsed)
        insert_cost_summary(plod_id, summary)
        updated += 1

    return updated


def get_budget_targets() -> dict:
    """Return {drill_type: {hole_type: budget_per_m}}.
    Maps drilling interval types to hole type costs."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT drill_type, hole_type, budget_per_m FROM budget_targets"
        ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["drill_type"], {})[r["hole_type"]] = r["budget_per_m"]
    return result


def set_budget_targets(mapping: dict):
    """Upsert {drill_type: {hole_type: budget_per_m}} values.
    drill_type is the interval type (RC, HQ3, NQ3, PQ3, HQ, HYD).
    hole_type is the hole purpose/type (RCRD, DDGT, DMET, REXP, STER, RCAG, DDRD)."""
    rows = [
        (dt, ht, float(rate))
        for dt, hts in mapping.items()
        for ht, rate in hts.items()
        if rate  # Skip empty/zero rates to keep table clean
    ]
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO budget_targets (drill_type, hole_type, budget_per_m) VALUES (?, ?, ?) "
            "ON CONFLICT(drill_type, hole_type) DO UPDATE SET budget_per_m=excluded.budget_per_m",
            rows,
        )
        conn.commit()


def get_missing_budget_rates(date_from=None, date_to=None, rig_id=None) -> list:
    """Find (drill_type, hole_type) combinations that have actual drilling data but no budget rate configured.
    Excludes combinations marked as ignored.
    Returns [{drill_type, hole_type, metres}] sorted by metres DESC."""
    where = ["di.length_m > 0", "(bt.budget_per_m IS NULL OR bt.budget_per_m = 0)"]
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    where_sql = "WHERE " + " AND ".join(where) if where else ""

    sql = f"""
        SELECT
            di.interval_type AS drill_type,
            SUBSTR(di.hole_name, 6, 4) AS hole_type,
            SUM(di.length_m) AS metres
        FROM drilling_intervals di
        JOIN plods p ON di.plod_id = p.id
        LEFT JOIN budget_targets bt ON bt.drill_type = di.interval_type
                                    AND bt.hole_type = SUBSTR(di.hole_name, 6, 4)
        LEFT JOIN ignored_rate_combinations irc ON irc.drill_type = di.interval_type
                                                AND irc.hole_type = SUBSTR(di.hole_name, 6, 4)
        {where_sql}
        AND irc.drill_type IS NULL
        GROUP BY di.interval_type, SUBSTR(di.hole_name, 6, 4)
        ORDER BY metres DESC
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def ignore_rate_combination(drill_type: str, hole_type: str, reason: str = None):
    """Mark a drill_type + hole_type combination as ignored (not applicable)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO ignored_rate_combinations (drill_type, hole_type, reason) VALUES (?, ?, ?)",
            (drill_type, hole_type, reason)
        )
        conn.commit()


def unignore_rate_combination(drill_type: str, hole_type: str):
    """Remove a drill_type + hole_type combination from the ignored list."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM ignored_rate_combinations WHERE drill_type = ? AND hole_type = ?",
            (drill_type, hole_type)
        )
        conn.commit()


def get_ignored_rate_combinations() -> list:
    """Return all ignored rate combinations."""
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT drill_type, hole_type, reason FROM ignored_rate_combinations ORDER BY drill_type, hole_type"
        ).fetchall()]


def get_daily_metres_by_purpose_type(date_from=None, date_to=None, rig_id=None) -> list:
    """Return [{date, hole_type, interval_type, total_m}] for computing budget lines by hole type.
    hole_type is extracted from characters 5-8 (0-indexed) of hole_name."""
    where = []
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT
            p.date,
            SUBSTR(di.hole_name, 6, 4) AS hole_type,
            CASE
                WHEN ri.rig_type = 'DD' AND di.interval_type NOT IN ('PQ3','HQ3','NQ3')
                THEN COALESCE(ri.default_interval_type, di.interval_type)
                ELSE di.interval_type
            END AS interval_type,
            SUM(di.length_m) AS total_m
        FROM drilling_intervals di
        JOIN plods p ON di.plod_id = p.id
        JOIN rigs ri ON p.rig_id = ri.id
        {where_sql}
        GROUP BY p.date, hole_type, interval_type
        ORDER BY p.date
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_metres_by_drill_type(date_from=None, date_to=None, rig_id=None, purpose=None) -> list:
    """Return [{interval_type, total_m, total_our_cost}] grouped by drill type using all-in cost."""
    where  = []
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    if purpose:
        # Handle both single purpose (string) and multiple purposes (list)
        if isinstance(purpose, list):
            placeholders = ",".join(["?"] * len(purpose))
            where.append(
                f"p.id IN ("
                f"  SELECT DISTINCT di2.plod_id FROM drilling_intervals di2"
                f"  JOIN hole_purposes hp ON hp.hole_name = di2.hole_name"
                f"  WHERE hp.purpose IN ({placeholders})"
                f")"
            )
            params.extend(purpose)
        else:
            where.append(
                "p.id IN ("
                "  SELECT DISTINCT di2.plod_id FROM drilling_intervals di2"
                "  JOIN hole_purposes hp ON hp.hole_name = di2.hole_name"
                "  WHERE hp.purpose = ?"
                ")"
            )
            params.append(purpose)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    # Aggregate metres per plod first to avoid multiplying cost_summary rows.
    # Use our_total (all cost categories) from cost_summary for a true all-in $/m.
    # Map DD rig intervals through default_interval_type for correct type grouping.
    sql = f"""
        SELECT
            COALESCE(r.default_interval_type, r.rig_type) AS interval_type,
            SUM(di_agg.total_m)  AS total_m,
            SUM(cs.our_total)    AS total_our_cost
        FROM cost_summary cs
        JOIN plods p ON p.id = cs.plod_id
        JOIN rigs r   ON r.id = p.rig_id
        JOIN (
            SELECT plod_id, SUM(length_m) AS total_m
            FROM drilling_intervals
            WHERE length_m > 0
            GROUP BY plod_id
        ) di_agg ON di_agg.plod_id = p.id
        {where_sql}
        GROUP BY 1
        ORDER BY 1
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_daily_drill_rate(date_from=None, date_to=None, rig_id=None) -> list:
    """Return [{date, rig, total_m, total_hours, m_per_hr}] grouped by date and rig."""
    where  = ["di.length_m > 0", "di.duration_h > 0"]
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    where_sql = "WHERE " + " AND ".join(where)
    sql = f"""
        SELECT p.date,
               r.short_name          AS rig,
               SUM(di.length_m)      AS total_m,
               SUM(di.duration_h)    AS total_hours,
               SUM(di.length_m) / SUM(di.duration_h) AS m_per_hr
        FROM drilling_intervals di
        JOIN plods p ON di.plod_id = p.id
        JOIN rigs r  ON p.rig_id   = r.id
        {where_sql}
        GROUP BY p.date, r.short_name
        ORDER BY p.date, r.short_name
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_metres_targets() -> dict:
    """Return {drill_type: metres_per_shift} for all configured targets."""
    with get_conn() as conn:
        rows = conn.execute("SELECT drill_type, metres_per_shift FROM metres_targets").fetchall()
    return {r["drill_type"]: r["metres_per_shift"] for r in rows}


def set_metres_targets(mapping: dict):
    """Upsert {drill_type: metres_per_shift} values."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO metres_targets (drill_type, metres_per_shift) VALUES (?, ?) "
            "ON CONFLICT(drill_type) DO UPDATE SET metres_per_shift=excluded.metres_per_shift",
            [(k, float(v)) for k, v in mapping.items()],
        )
        conn.commit()


def get_slow_thresholds() -> dict:
    """Return {drill_type: slow_threshold_m_per_hr}."""
    with get_conn() as conn:
        rows = conn.execute("SELECT drill_type, slow_threshold_m_per_hr FROM metres_targets").fetchall()
    return {r["drill_type"]: r["slow_threshold_m_per_hr"] for r in rows}


def set_slow_thresholds(mapping: dict):
    """Upsert {drill_type: slow_threshold_m_per_hr} values."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO metres_targets (drill_type, metres_per_shift, slow_threshold_m_per_hr) VALUES (?, 0, ?) "
            "ON CONFLICT(drill_type) DO UPDATE SET slow_threshold_m_per_hr=excluded.slow_threshold_m_per_hr",
            [(k, float(v)) for k, v in mapping.items()],
        )
        conn.commit()


def get_plod_metres_by_type(date_from=None, date_to=None, rig_id=None, purpose=None) -> list:
    """
    Return [{plod_id, date, interval_type, metres}] ordered by date then plod_id.
    One row per PLOD × drill type — used to build a per-shift cumulative target.
    """
    where  = ["di.length_m > 0"]
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    if rig_id:
        where.append("p.rig_id = ?"); params.append(rig_id)
    if purpose:
        # Handle both single purpose (string) and multiple purposes (list)
        if isinstance(purpose, list):
            placeholders = ",".join(["?"] * len(purpose))
            where.append(
                f"p.id IN ("
                f"  SELECT DISTINCT di2.plod_id FROM drilling_intervals di2"
                f"  JOIN hole_purposes hp ON hp.hole_name = di2.hole_name"
                f"  WHERE hp.purpose IN ({placeholders})"
                f")"
            )
            params.extend(purpose)
        else:
            where.append(
                "p.id IN ("
                "  SELECT DISTINCT di2.plod_id FROM drilling_intervals di2"
                "  JOIN hole_purposes hp ON hp.hole_name = di2.hole_name"
                "  WHERE hp.purpose = ?"
                ")"
            )
            params.append(purpose)
    where_sql = "WHERE " + " AND ".join(where)
    sql = f"""
        SELECT p.id AS plod_id, p.date, r.short_name AS rig,
               r.rig_type,
               CASE
                   WHEN r.rig_type = 'DD' AND di.interval_type NOT IN ('PQ3','HQ3','NQ3')
                   THEN COALESCE(r.default_interval_type, di.interval_type)
                   ELSE di.interval_type
               END AS interval_type,
               SUM(di.length_m) AS metres
        FROM drilling_intervals di
        JOIN plods p ON di.plod_id = p.id
        JOIN rigs r ON p.rig_id = r.id
        {where_sql}
        GROUP BY p.id, p.date, r.short_name, r.rig_type,
                 CASE
                     WHEN r.rig_type = 'DD' AND di.interval_type NOT IN ('PQ3','HQ3','NQ3')
                     THEN COALESCE(r.default_interval_type, di.interval_type)
                     ELSE di.interval_type
                 END
        ORDER BY p.date, r.short_name, p.id
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

def insert_feedback(name: str, category: str, message: str, auto_response: str = None) -> int:
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO feedback (name, category, message, auto_response) VALUES (?,?,?,?)",
            (name or None, category, message, auto_response or None),
        )
        conn.commit()
        return c.lastrowid


def get_feedback(status: str = None) -> list:
    where = "WHERE status=?" if status else ""
    params = (status,) if status else ()
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM feedback {where} ORDER BY submitted_at DESC", params
        ).fetchall()
    return [dict(r) for r in rows]


def update_feedback(feedback_id: int, status: str, admin_response: str):
    with get_conn() as conn:
        conn.execute(
            "UPDATE feedback SET status=?, admin_response=?, responded_at=datetime('now') WHERE id=?",
            (status, admin_response or None, feedback_id),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Earthworks
# ---------------------------------------------------------------------------

def get_ew_contractors() -> list:
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT id, name, notes FROM ew_contractors ORDER BY name"
        ).fetchall()]


def get_ew_equipment_rates(contractor_id: int = None) -> list:
    where = "WHERE contractor_id=?" if contractor_id else ""
    params = (contractor_id,) if contractor_id else ()
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            f"""SELECT er.id, c.name AS contractor, er.contractor_id,
                       er.equipment_name, er.plant_rate, er.operator_rate,
                       er.standby_rate, er.mob_cost, er.demob_cost
                FROM ew_equipment_rates er
                JOIN ew_contractors c ON c.id = er.contractor_id
                {where}
                ORDER BY c.name, er.equipment_name""",
            params,
        ).fetchall()]


def set_ew_equipment_rates(contractor_id: int, rows: list):
    """Upsert list of dicts with keys: equipment_name, plant_rate, operator_rate,
    standby_rate, mob_cost, demob_cost."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO ew_equipment_rates "
            "(contractor_id, equipment_name, plant_rate, operator_rate, standby_rate, mob_cost, demob_cost) "
            "VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(contractor_id, equipment_name) DO UPDATE SET "
            "plant_rate=excluded.plant_rate, operator_rate=excluded.operator_rate, "
            "standby_rate=excluded.standby_rate, mob_cost=excluded.mob_cost, "
            "demob_cost=excluded.demob_cost",
            [
                (contractor_id, r["equipment_name"], float(r["plant_rate"]),
                 float(r["operator_rate"]), float(r["standby_rate"]),
                 float(r["mob_cost"]), float(r["demob_cost"]))
                for r in rows
            ],
        )
        conn.commit()


def insert_ew_entries(entries: list, replace: bool = False) -> int:
    """Insert list of ew_entry dicts. Returns count inserted/replaced."""
    conflict = "REPLACE" if replace else "IGNORE"
    sql = (
        f"INSERT OR {conflict} INTO ew_entries "
        "(date, contractor_id, equipment_name, mobilised, demobilised, "
        "active_hours, standdown_hours, unavailable_hours, total_hours, "
        "mob_cost, operating_cost, standdown_cost, accommodation, total_cost, "
        "notes, is_historical) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    rows = [
        (
            e["date"], e["contractor_id"], e["equipment_name"],
            int(e.get("mobilised", 0)), int(e.get("demobilised", 0)),
            float(e.get("active_hours", 0)), float(e.get("standdown_hours", 0)),
            float(e.get("unavailable_hours", 0)), float(e.get("total_hours", 0)),
            float(e.get("mob_cost", 0)), float(e.get("operating_cost", 0)),
            float(e.get("standdown_cost", 0)), float(e.get("accommodation", 0)),
            float(e.get("total_cost", 0)),
            e.get("notes"), int(e.get("is_historical", 0)),
        )
        for e in entries
    ]
    with get_conn() as conn:
        conn.executemany(sql, rows)
        conn.commit()
    return len(rows)


def get_ew_entries(date_from=None, date_to=None, contractor_id=None,
                   include_historical=True) -> list:
    where = []
    params = []
    if date_from:
        where.append("e.date >= ?"); params.append(date_from)
    if date_to:
        where.append("e.date <= ?"); params.append(date_to)
    if contractor_id:
        where.append("e.contractor_id = ?"); params.append(contractor_id)
    if not include_historical:
        where.append("e.is_historical = 0")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT e.*, c.name AS contractor
        FROM ew_entries e
        JOIN ew_contractors c ON c.id = e.contractor_id
        {where_sql}
        ORDER BY e.date, c.name, e.equipment_name
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_ew_daily_summary(date_from=None, date_to=None, contractor_id=None,
                         include_historical=True) -> list:
    """Return one row per date with totals across all equipment."""
    where = []
    params = []
    if date_from:
        where.append("e.date >= ?"); params.append(date_from)
    if date_to:
        where.append("e.date <= ?"); params.append(date_to)
    if contractor_id:
        where.append("e.contractor_id = ?"); params.append(contractor_id)
    if not include_historical:
        where.append("e.is_historical = 0")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT
            e.date,
            SUM(e.active_hours)    AS active_hours,
            SUM(e.standdown_hours) AS standdown_hours,
            SUM(e.total_cost)      AS total_cost,
            SUM(e.mob_cost)        AS mob_cost,
            COUNT(DISTINCT e.equipment_name) AS equipment_count,
            (SELECT COUNT(*) FROM ew_pads p WHERE p.date = e.date) AS pads_completed
        FROM ew_entries e
        {where_sql}
        GROUP BY e.date
        ORDER BY e.date
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def insert_ew_pads(pads: list):
    """Insert list of dicts with keys: date, contractor_id, pad_id, notes."""
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO ew_pads (date, contractor_id, pad_id, notes) VALUES (?,?,?,?)",
            [(p["date"], p.get("contractor_id"), p["pad_id"], p.get("notes")) for p in pads],
        )
        conn.commit()


def get_ew_pads(date_from=None, date_to=None) -> list:
    where = []
    params = []
    if date_from:
        where.append("p.date >= ?"); params.append(date_from)
    if date_to:
        where.append("p.date <= ?"); params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT p.*, c.name AS contractor
        FROM ew_pads p
        LEFT JOIN ew_contractors c ON c.id = p.contractor_id
        {where_sql}
        ORDER BY p.date, p.pad_id
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_ew_setting(key: str, default: str = "") -> str:
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_ew_setting(key: str, value: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


def insert_ew_daily(record: dict) -> int:
    """Insert or replace a daily PLOD header. Returns the row id."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO ew_daily "
            "(date, contractor_id, supervisor, works_description, location, area, "
            "start_time, end_time, additional_comments, principal_name, "
            "source_filename, is_historical) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(date, contractor_id) DO UPDATE SET "
            "supervisor=excluded.supervisor, works_description=excluded.works_description, "
            "location=excluded.location, area=excluded.area, "
            "start_time=excluded.start_time, end_time=excluded.end_time, "
            "additional_comments=excluded.additional_comments, "
            "principal_name=excluded.principal_name, "
            "source_filename=excluded.source_filename, "
            "is_historical=excluded.is_historical",
            (
                record["date"], record["contractor_id"],
                record.get("supervisor"), record.get("works_description"),
                record.get("location"), record.get("area"),
                record.get("start_time"), record.get("end_time"),
                record.get("additional_comments"), record.get("principal_name"),
                record.get("source_filename"), int(record.get("is_historical", 0)),
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM ew_daily WHERE date=? AND contractor_id=?",
            (record["date"], record["contractor_id"]),
        ).fetchone()
        return row["id"]


def insert_ew_production(daily_id: int, prod: dict):
    with get_conn() as conn:
        conn.execute("DELETE FROM ew_production WHERE daily_id=?", (daily_id,))
        conn.execute(
            "INSERT INTO ew_production (daily_id, roads_km, tracks_km, pads_count, sumps_pits, notes) "
            "VALUES (?,?,?,?,?,?)",
            (daily_id, float(prod.get("roads_km") or 0),
             float(prod.get("tracks_km") or 0),
             int(prod.get("pads_count") or 0),
             int(prod.get("sumps_pits") or 0),
             prod.get("notes")),
        )
        conn.commit()


def insert_ew_misc_items(daily_id: int, items: list):
    with get_conn() as conn:
        conn.execute("DELETE FROM ew_misc WHERE daily_id=?", (daily_id,))
        conn.executemany(
            "INSERT INTO ew_misc (daily_id, item_name, quantity, notes) VALUES (?,?,?,?)",
            [(daily_id, i["item_name"], str(i.get("quantity") or ""), i.get("notes")) for i in items],
        )
        conn.commit()


def get_ew_daily_plods(date_from=None, date_to=None, contractor_id=None,
                       include_historical=True) -> list:
    where = []
    params = []
    if date_from:
        where.append("d.date >= ?"); params.append(date_from)
    if date_to:
        where.append("d.date <= ?"); params.append(date_to)
    if contractor_id:
        where.append("d.contractor_id = ?"); params.append(contractor_id)
    if not include_historical:
        where.append("d.is_historical = 0")
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT d.*, c.name AS contractor,
               COALESCE(p.roads_km,   0) AS roads_km,
               COALESCE(p.tracks_km,  0) AS tracks_km,
               COALESCE(p.pads_count, 0) AS pads_count,
               COALESCE(p.sumps_pits, 0) AS sumps_pits,
               p.notes                   AS production_notes
        FROM ew_daily d
        JOIN ew_contractors c ON c.id = d.contractor_id
        LEFT JOIN ew_production p ON p.daily_id = d.id
        {where_sql}
        ORDER BY d.date DESC
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def delete_ew_historical():
    """Remove all entries flagged as historical. Used to clear demo data."""
    with get_conn() as conn:
        conn.execute("DELETE FROM ew_daily WHERE is_historical = 1")
        conn.execute("DELETE FROM ew_entries WHERE is_historical = 1")
        conn.commit()


# ---------------------------------------------------------------------------
# OCR Correction memory
# ---------------------------------------------------------------------------

def insert_ew_corrections(corrections: list):
    """Store a list of field-level corrections made during PLOD review."""
    if not corrections:
        return
    with get_conn() as conn:
        conn.executemany(
            "INSERT INTO ew_ocr_corrections "
            "(field, equipment_name, extracted_value, corrected_value, source_filename) "
            "VALUES (?,?,?,?,?)",
            [
                (c["field"], c.get("equipment_name"),
                 c.get("extracted_value"), c.get("corrected_value"),
                 c.get("source_filename"))
                for c in corrections
            ],
        )
        conn.commit()


def get_ew_corrections(limit: int = 50) -> list:
    """Return recent corrections ordered by most frequent pattern first."""
    sql = """
        SELECT field, equipment_name, extracted_value, corrected_value,
               COUNT(*) AS times_seen,
               MAX(created_at) AS last_seen
        FROM ew_ocr_corrections
        GROUP BY field, extracted_value, corrected_value
        ORDER BY times_seen DESC, last_seen DESC
        LIMIT ?
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(sql, (limit,)).fetchall()]


def get_all_ew_corrections_raw() -> list:
    """Return every individual correction row for admin review."""
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM ew_ocr_corrections ORDER BY created_at DESC"
        ).fetchall()]


def delete_ew_correction_pattern(field: str, extracted_value: str, corrected_value: str):
    """Delete all correction records matching a specific pattern."""
    with get_conn() as conn:
        conn.execute(
            "DELETE FROM ew_ocr_corrections "
            "WHERE field=? AND extracted_value=? AND corrected_value=?",
            (field, extracted_value, corrected_value),
        )
        conn.commit()


# ─────────────────────────────────────────────────────────────────────────────
# ACTIVITY CATEGORIZATION
# ─────────────────────────────────────────────────────────────────────────────

def categorize_activity(category: str, rig_id: int = None) -> str:
    """
    Map detailed time_breakdown categories to broad activity types.
    Uses rate table to determine if something is 'active' or 'inactive'.

    Returns: 'Active Rate', 'Inactive Rate', 'Standby', 'Weather Standby', 'Breakdown'
    """
    if not category:
        return "Active Rate"

    cat_lower = category.lower().strip()

    # Check for weather-related standby first
    if any(kw in cat_lower for kw in ("standby", "stand by", "idle")):
        if any(kw in cat_lower for kw in ("weather", "rain", "cloud", "storm", "wet", "delay")):
            return "Weather Standby"
        return "Standby"

    if any(kw in cat_lower for kw in ("breakdown", "break down", "maintenance", "repair", "fault")):
        return "Breakdown"

    # Check if it's an active rate category using rates table
    if rig_id:
        rates = get_rates(rig_id=rig_id)
        for r in rates:
            if r.get("category") == "active_rig" and category.lower() == r.get("label", "").lower():
                return "Active Rate"

    # Default: treat as Active if it doesn't match other patterns
    return "Active Rate"


def get_activity_breakdown_by_date(date_from: str = None, date_to: str = None, rig_id: int = None) -> list:
    """
    Get detailed activity breakdown by date for a date range.
    Calculates: Drill Time, Active, Inactive, Standby, Breakdown per PLOD (shift).
    Each shift = 12 hours. Inactive = 12 - (Drill + Active + Standby + Breakdown)

    Returns list of dicts with: date, rig, broad_category, hours, detailed_breakdown
    Aggregates multiple PLODs per date/rig by summing across shifts.
    """
    with get_conn() as conn:
        # Use subqueries to SUM hours per PLOD before joining
        sql = """
            SELECT
                p.id AS plod_id,
                p.date,
                p.rig_id,
                ri.short_name AS rig,
                COALESCE(di_sum.drill_hours, 0) AS drill_hours,
                tb_sum.tb_detail
            FROM plods p
            JOIN rigs ri ON p.rig_id = ri.id
            LEFT JOIN (
                SELECT plod_id, SUM(duration_h) AS drill_hours
                FROM drilling_intervals
                WHERE duration_h > 0
                GROUP BY plod_id
            ) di_sum ON p.id = di_sum.plod_id
            LEFT JOIN (
                SELECT plod_id, GROUP_CONCAT(category || ':' || duration_h, '|') AS tb_detail
                FROM time_breakdown
                WHERE duration_h > 0
                GROUP BY plod_id
            ) tb_sum ON p.id = tb_sum.plod_id
            WHERE 1=1
        """
        params = []
        if date_from:
            sql += " AND p.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND p.date <= ?"
            params.append(date_to)
        if rig_id:
            sql += " AND p.rig_id = ?"
            params.append(rig_id)

        sql += " ORDER BY p.date, ri.short_name, p.id"

        plod_rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

        # Process each PLOD and categorize its hours
        plod_data = {}  # date/rig → category data

        for row in plod_rows:
            date = row["date"]
            rig = row["rig"]
            key = (date, rig)

            drill_hours = row.get("drill_hours") or 0.0

            # Parse time_breakdown detail for this PLOD
            active_hours = 0.0
            standby_hours = 0.0
            weather_standby_hours = 0.0
            breakdown_hours = 0.0
            tb_detail_map = {}

            if row.get("tb_detail"):
                for item in row["tb_detail"].split("|"):
                    if ":" in item:
                        cat, hrs_str = item.rsplit(":", 1)
                        try:
                            hrs = float(hrs_str) if hrs_str else 0.0
                        except ValueError:
                            hrs = 0.0

                        if hrs > 0:
                            broad = categorize_activity(cat, row["rig_id"])
                            if broad not in tb_detail_map:
                                tb_detail_map[broad] = []
                            tb_detail_map[broad].append((cat, hrs))

                            if broad == "Active Rate":
                                active_hours += hrs
                            elif broad == "Standby":
                                standby_hours += hrs
                            elif broad == "Weather Standby":
                                weather_standby_hours += hrs
                            elif broad == "Breakdown":
                                breakdown_hours += hrs

            # Calculate inactive for this PLOD (each shift = 12 hours)
            accounted = drill_hours + active_hours + standby_hours + weather_standby_hours + breakdown_hours
            inactive_hours = max(0, 12.0 - accounted)

            # Initialize key if needed
            if key not in plod_data:
                plod_data[key] = {
                    "Drilling": {"hours": 0, "details": []},
                    "Active Rate": {"hours": 0, "details": []},
                    "Inactive Rate": {"hours": 0, "details": []},
                    "Standby": {"hours": 0, "details": []},
                    "Weather Standby": {"hours": 0, "details": []},
                    "Breakdown": {"hours": 0, "details": []}
                }

            # Add this PLOD's hours to the aggregate
            plod_data[key]["Drilling"]["hours"] += drill_hours
            plod_data[key]["Active Rate"]["hours"] += active_hours
            plod_data[key]["Active Rate"]["details"].extend(tb_detail_map.get("Active Rate", []))
            plod_data[key]["Inactive Rate"]["hours"] += inactive_hours
            plod_data[key]["Standby"]["hours"] += standby_hours
            plod_data[key]["Standby"]["details"].extend(tb_detail_map.get("Standby", []))
            plod_data[key]["Weather Standby"]["hours"] += weather_standby_hours
            plod_data[key]["Weather Standby"]["details"].extend(tb_detail_map.get("Weather Standby", []))
            plod_data[key]["Breakdown"]["hours"] += breakdown_hours
            plod_data[key]["Breakdown"]["details"].extend(tb_detail_map.get("Breakdown", []))

        # Build result with aggregated data per date/rig
        result = []
        for (date, rig), categories in plod_data.items():
            for cat_name, data in categories.items():
                hours = data["hours"]
                if hours > 0 or cat_name == "Inactive Rate":  # Always show inactive
                    detail_list = data["details"]
                    # Use line breaks for vertical display in hover tooltip
                    detail_str = "<br>".join([f"{c}: {h:.2f}h" for c, h in detail_list]) if detail_list else ""

                    result.append({
                        "date": date,
                        "rig": rig,
                        "broad_category": cat_name,
                        "hours": hours,
                        "detailed_breakdown": detail_str
                    })

        return result


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER JSON CACHE
# ─────────────────────────────────────────────────────────────────────────────

def _get_weather_cache_path() -> Path:
    """Get the path to the weather cache JSON file."""
    cache_dir = Path(__file__).parent / ".weather_cache"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "weather_data.json"


def load_weather_from_cache(date_from: str = None, date_to: str = None) -> dict:
    """
    Load weather data from local JSON cache.
    Returns dict mapping date_str → {event_type, severity}
    """
    import json

    cache_path = _get_weather_cache_path()
    if not cache_path.exists():
        return {}

    try:
        with open(cache_path, 'r') as f:
            all_weather = json.load(f)

        # Filter by date range if specified
        if date_from or date_to:
            filtered = {}
            for date_str, data in all_weather.items():
                if date_from and date_str < date_from:
                    continue
                if date_to and date_str > date_to:
                    continue
                filtered[date_str] = data
            return filtered

        return all_weather
    except Exception as e:
        print(f"Error loading weather cache: {e}")
        return {}


def save_weather_to_cache(weather_data: dict):
    """
    Save weather data to local JSON cache.
    Merges with existing cache to preserve historical data.
    """
    import json

    cache_path = _get_weather_cache_path()

    # Load existing cache
    existing = load_weather_from_cache()

    # Merge new data (overwrites if date exists)
    existing.update(weather_data)

    # Save merged data
    try:
        with open(cache_path, 'w') as f:
            json.dump(existing, f, indent=2, sort_keys=True)
    except Exception as e:
        print(f"Error saving weather cache: {e}")


def get_missing_dates_for_weather(date_from: str, date_to: str) -> list:
    """
    Get list of dates between date_from and date_to that are NOT in the cache.
    Returns list of date strings in YYYY-MM-DD format.
    """
    from datetime import datetime, timedelta

    cached = load_weather_from_cache(date_from, date_to)

    current = datetime.strptime(date_from, "%Y-%m-%d").date()
    end = datetime.strptime(date_to, "%Y-%m-%d").date()

    missing = []
    while current <= end:
        date_str = str(current)
        if date_str not in cached:
            missing.append(date_str)
        current += timedelta(days=1)

    return missing


# ─────────────────────────────────────────────────────────────────────────────
# WEATHER
# ─────────────────────────────────────────────────────────────────────────────

def get_weather_events(date_from: str = None, date_to: str = None) -> list:
    """Get weather events for a date range, prioritizing rain/thunderstorm over sunny."""
    with get_conn() as conn:
        sql = "SELECT * FROM weather_events WHERE 1=1"
        params = []
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        sql += " ORDER BY date, CASE WHEN event_type IN ('thunderstorm', 'rain') THEN 0 ELSE 1 END, created_at"
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def insert_weather_event(date: str, event_type: str, shift: str = None, severity: str = None, notes: str = None) -> int:
    """Insert a weather event. Returns the row ID."""
    with get_conn() as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO weather_events (date, event_type, shift, severity, notes) VALUES (?, ?, ?, ?, ?)",
            (date, event_type, shift, severity, notes),
        )
        conn.commit()
        return c.lastrowid


def delete_weather_event(event_id: int):
    """Delete a weather event by ID."""
    with get_conn() as conn:
        conn.execute("DELETE FROM weather_events WHERE id=?", (event_id,))
        conn.commit()


def get_weather_summary_by_date(date_from: str = None, date_to: str = None) -> dict:
    """
    Return a dict mapping date → representative weather event.
    Prioritizes rain/thunderstorm over sunny weather.
    """
    events = get_weather_events(date_from, date_to)
    result = {}
    for event in events:
        d = event["date"]
        if d not in result:  # First (prioritized) event for each date wins
            result[d] = event
    return result


def parse_dms_coordinate(dms_str: str) -> float:
    """
    Parse DMS (degrees, minutes, seconds) coordinate to decimal.
    Accepts formats like: 16°23'51.8"S, 127°58'50.1"E, -16.3977, etc.
    """
    import re

    dms_str = dms_str.strip()

    # Try to parse as DMS format: 16°23'51.8"S
    # Matches: digits°digits'digits.digits"[NSEW]
    dms_pattern = r"(\d+)°(\d+)['\u2019]?([\d.]+)?[\"″]?\s*([NSEWnsew])"
    match = re.search(dms_pattern, dms_str)

    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2))
        seconds = float(match.group(3)) if match.group(3) else 0.0
        direction = match.group(4).upper()

        decimal = degrees + minutes / 60.0 + seconds / 3600.0

        # South and West are negative
        if direction in ("S", "W"):
            decimal = -decimal

        return decimal

    # Try to parse as decimal
    try:
        return float(dms_str)
    except ValueError:
        raise ValueError(f"Could not parse coordinate: {dms_str}. Use format: 16°23'51.8\"S or -16.3977")


def save_location_for_weather(location: str, latitude_str: str = None, longitude_str: str = None):
    """
    Save the location for weather data retrieval.
    Accepts latitude/longitude as DMS (e.g., 16°23'51.8"S) or decimal.
    """
    latitude = None
    longitude = None

    if latitude_str:
        latitude = parse_dms_coordinate(latitude_str)
    if longitude_str:
        longitude = parse_dms_coordinate(longitude_str)

    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("weather_location", location)
        )
        if latitude is not None:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("weather_latitude", str(latitude))
            )
        if longitude is not None:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("weather_longitude", str(longitude))
            )
        conn.commit()


def get_location_for_weather() -> dict:
    """Get the saved location for weather data."""
    with get_conn() as conn:
        location = get_setting("weather_location", "")
        latitude_str = get_setting("weather_latitude", "")
        longitude_str = get_setting("weather_longitude", "")
        radius_str = get_setting("weather_radius_km", "50")

        latitude = None
        longitude = None
        radius_km = 50

        try:
            latitude = float(latitude_str) if latitude_str else None
            longitude = float(longitude_str) if longitude_str else None
            radius_km = float(radius_str) if radius_str else 50
        except (ValueError, TypeError):
            pass

        return {
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km
        }


def get_coordinates_within_radius(center_lat: float, center_lon: float, radius_km: float = 50) -> list:
    """
    Calculate boundary coordinates for a circular buffer around a center point.
    Returns: list of (lat, lon) tuples representing the buffer boundary (8 points).

    This helps visualize the coverage area of weather data.
    Uses simple approximation (good for distances up to ~100km).
    """
    import math

    # Earth's radius in km
    R = 6371

    # Convert to radians
    lat_rad = math.radians(center_lat)
    lon_rad = math.radians(center_lon)

    # Angular distance in radians
    angular_distance = radius_km / R

    # Generate 8 points around the circle
    points = []
    for i in range(8):
        bearing = math.radians(i * 45)  # 0°, 45°, 90°, etc.

        lat = math.asin(math.sin(lat_rad) * math.cos(angular_distance) +
                       math.cos(lat_rad) * math.sin(angular_distance) * math.cos(bearing))

        lon = lon_rad + math.atan2(math.sin(bearing) * math.sin(angular_distance) * math.cos(lat_rad),
                                   math.cos(angular_distance) - math.sin(lat_rad) * math.sin(lat))

        points.append((math.degrees(lat), math.degrees(lon)))

    return points


def fetch_weather_from_api_range(latitude: float, longitude: float, date_from: str, date_to: str) -> dict:
    """
    Fetch historical weather from Open-Meteo API for a date range (single request).
    MUCH faster than fetching one day at a time.

    Returns dict mapping date_str → {event_type, severity}
    """
    try:
        import requests

        # Open-Meteo historical weather API
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": date_from,
            "end_date": date_to,
            "daily": "weather_code,precipitation_sum"
        }

        print(f"[Weather API] Fetching {date_from} to {date_to} for ({latitude}, {longitude})")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        print(f"[Weather API] Response status: {response.status_code}")

        if "daily" not in data or not data["daily"]["time"]:
            print(f"[Weather API] No daily data in response. Keys: {data.keys()}")
            return {}

        daily = data["daily"]
        dates = daily.get("time", [])
        weather_codes = daily.get("weather_code", [])
        precipitations = daily.get("precipitation_sum", [])

        print(f"[Weather API] Processing {len(dates)} dates")

        result = {}
        for i, date_str in enumerate(dates):
            weather_code = weather_codes[i] if i < len(weather_codes) else None
            precipitation = precipitations[i] if i < len(precipitations) else 0

            # Determine event type based on WMO weather codes and precipitation
            # WMO codes 80-82 indicate thunderstorms
            if weather_code in [80, 81, 82]:
                event_type = "thunderstorm"
                severity = "severe"
            elif precipitation > 0.1:
                if precipitation > 10:
                    severity = "heavy"
                elif precipitation > 2:
                    severity = "moderate"
                else:
                    severity = "light"
                event_type = "rain"
            else:
                event_type = "sunny" if weather_code in [0, 1] else "cloudy"
                severity = None

            result[date_str] = {"event_type": event_type, "severity": severity}

        print(f"[Weather API] Successfully processed {len(result)} dates")
        return result

    except Exception as e:
        print(f"[Weather API] Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {}


def fetch_weather_from_api(latitude: float, longitude: float, date_str: str) -> dict:
    """
    Fetch historical weather from Open-Meteo API for a single day.
    Deprecated: use fetch_weather_from_api_range() for better performance.

    Returns dict with event_type and severity.
    """
    result = fetch_weather_from_api_range(latitude, longitude, date_str, date_str)
    return result.get(date_str) if result else None


# ── Purpose Budget Allocations ──────────────────────────────────────────────

def get_all_purposes() -> list:
    """Get all distinct purposes from hole_purposes table."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT DISTINCT purpose FROM hole_purposes WHERE purpose IS NOT NULL ORDER BY purpose")
    purposes = [row["purpose"] for row in c.fetchall()]
    conn.close()
    return purposes


def get_hole_type_purpose_mapping() -> dict:
    """Get mapping of hole_type -> [list of purposes it appears under].
    Returns dict like: {
        'DDRD': ['2026 RC Infill A Vein', 'Resource Definition'],
        'RCRD': ['2026 RC Infill A Vein'],
        'ROP': ['2026 sterilisation drilling'],
        ...
    }
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT hole_type, purpose FROM hole_purposes "
            "WHERE hole_type IS NOT NULL AND purpose IS NOT NULL "
            "ORDER BY hole_type, purpose"
        ).fetchall()

    mapping = {}
    for row in rows:
        ht = row["hole_type"]
        purpose = row["purpose"]
        if ht not in mapping:
            mapping[ht] = []
        if purpose not in mapping[ht]:
            mapping[ht].append(purpose)

    return mapping


def get_all_purpose_budgets() -> list:
    """
    Get all purpose budgets with new simplified structure.
    Returns list of dicts: {purpose, drilling_work_group, drilling_budget, drilling_start_date, drilling_end_date, ...}
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM purpose_budgets ORDER BY purpose")
    result = [dict(row) for row in c.fetchall()]
    conn.close()
    return result


def get_purpose_budget(purpose: str) -> dict:
    """Get a single purpose budget."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM purpose_budgets WHERE purpose = ?", (purpose,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def save_purpose_budget(purpose: str, drilling_work_group: str = "", drilling_budget: float = 0,
                       drilling_start_date: str = "", drilling_end_date: str = "",
                       earthworks_work_group: str = "", earthworks_budget: float = 0,
                       earthworks_start_date: str = "", earthworks_end_date: str = "",
                       fuel_budget: float = 0, in_scope: bool = True, notes: str = "",
                       currency: str = "AUD") -> bool:
    """Save or update a purpose budget. Calculates fuel dates as MIN/MAX of drilling/earthworks dates."""
    conn = get_conn()
    c = conn.cursor()

    try:
        # Calculate fuel dates: min of starts, max of ends
        from datetime import datetime
        fuel_start = fuel_end = None

        dates = []
        if drilling_start_date:
            dates.append(drilling_start_date)
        if earthworks_start_date:
            dates.append(earthworks_start_date)
        if dates:
            fuel_start = min(dates)

        dates = []
        if drilling_end_date:
            dates.append(drilling_end_date)
        if earthworks_end_date:
            dates.append(earthworks_end_date)
        if dates:
            fuel_end = max(dates)

        in_scope_int = 1 if in_scope else 0

        c.execute("""
            INSERT OR REPLACE INTO purpose_budgets
            (purpose, drilling_work_group, drilling_budget, drilling_start_date, drilling_end_date,
             earthworks_work_group, earthworks_budget, earthworks_start_date, earthworks_end_date,
             fuel_budget, fuel_start_date, fuel_end_date, in_scope, notes, currency, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (purpose, drilling_work_group, drilling_budget, drilling_start_date, drilling_end_date,
              earthworks_work_group, earthworks_budget, earthworks_start_date, earthworks_end_date,
              fuel_budget, fuel_start, fuel_end, in_scope_int, notes, currency))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving purpose budget: {e}")
        conn.close()
        return False


def get_purpose_budget_allocations(date_str: str = None) -> dict:
    """
    Get purpose budget allocations, optionally filtered by effective date.
    Returns dict: {purpose: {start_date, end_date, in_scope, drilling_budget, earthworks_budget, fuel_budget, currency, notes, work_group}}
    If date_str provided, returns only allocations that are effective on that date.
    """
    conn = get_conn()
    c = conn.cursor()

    if date_str:
        # Get allocations effective on the given date
        c.execute("""
            SELECT purpose, start_date, end_date, in_scope, drilling_budget, earthworks_budget, fuel_budget, currency, notes, work_group
            FROM purpose_budget_allocations
            WHERE start_date <= ? AND end_date >= ?
            ORDER BY purpose, start_date
        """, (date_str, date_str))
    else:
        # Get all allocations
        c.execute("""
            SELECT purpose, start_date, end_date, in_scope, drilling_budget, earthworks_budget, fuel_budget, currency, notes, work_group
            FROM purpose_budget_allocations
            ORDER BY purpose, start_date
        """)

    result = {}
    for row in c.fetchall():
        key = f"{row['purpose']} ({row['start_date']} to {row['end_date']})"
        result[key] = {
            "purpose": row["purpose"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "in_scope": bool(row["in_scope"]),
            "drilling_budget": row["drilling_budget"],
            "earthworks_budget": row["earthworks_budget"],
            "fuel_budget": row["fuel_budget"],
            "currency": row["currency"],
            "notes": row["notes"],
            "work_group": row["work_group"] or "",
        }
    conn.close()
    return result


def save_purpose_budget_allocation(purpose: str, start_date: str, end_date: str, in_scope: bool = True, drilling_budget: float = 0, earthworks_budget: float = 0, fuel_budget: float = 0, currency: str = "AUD", notes: str = "", work_group: str = "") -> bool:
    """
    Save or update purpose budget allocation with date range.
    Date format: YYYY-MM-DD
    Returns True on success.
    """
    conn = get_conn()
    c = conn.cursor()
    try:
        in_scope_int = 1 if in_scope else 0
        c.execute("""
            INSERT INTO purpose_budget_allocations
            (purpose, start_date, end_date, in_scope, drilling_budget, earthworks_budget, fuel_budget, currency, notes, work_group, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(purpose, start_date, end_date) DO UPDATE SET
                in_scope = ?,
                drilling_budget = ?,
                earthworks_budget = ?,
                fuel_budget = ?,
                currency = ?,
                notes = ?,
                work_group = ?,
                updated_at = datetime('now')
        """, (purpose, start_date, end_date, in_scope_int, drilling_budget, earthworks_budget, fuel_budget, currency, notes, work_group,
              in_scope_int, drilling_budget, earthworks_budget, fuel_budget, currency, notes, work_group))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving purpose budget allocation: {e}")
        conn.close()
        return False


def get_purpose_budget_total(purpose: str) -> dict:
    """
    Get total budget and breakdown for a specific purpose.
    Returns dict: {total, drilling, earthworks, fuel, currency}
    """
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT drilling_budget, earthworks_budget, fuel_budget, currency
        FROM purpose_budget_allocations
        WHERE purpose = ?
    """, (purpose,))
    row = c.fetchone()
    conn.close()

    if row:
        drilling = row["drilling_budget"]
        earthworks = row["earthworks_budget"]
        fuel = row["fuel_budget"]
        return {
            "total": drilling + earthworks + fuel,
            "drilling": drilling,
            "earthworks": earthworks,
            "fuel": fuel,
            "currency": row["currency"],
        }
    return {"total": 0, "drilling": 0, "earthworks": 0, "fuel": 0, "currency": "AUD"}


def delete_stale_migration_records():
    """
    Remove old migration records that have default dates (2020-01-01 to 2099-12-31).
    These are the old default dates from database migration before Gantt import.
    Only delete if there are other records with real dates for the same purpose.
    Returns count of deleted records.
    """
    conn = get_conn()
    c = conn.cursor()

    deleted_count = 0

    # Find all purposes that have BOTH migration records AND real records
    c.execute("""
        SELECT purpose FROM purpose_budget_allocations
        WHERE start_date = '2020-01-01' AND end_date = '2099-12-31'
        GROUP BY purpose
    """)

    migration_purposes = [row["purpose"] for row in c.fetchall()]

    for purpose in migration_purposes:
        # Check if this purpose has real (non-migration) dates
        c.execute("""
            SELECT COUNT(*) as cnt FROM purpose_budget_allocations
            WHERE purpose = ? AND NOT (start_date = '2020-01-01' AND end_date = '2099-12-31')
        """, (purpose,))

        real_count = c.fetchone()["cnt"]

        # If there are real records, delete the migration record
        if real_count > 0:
            c.execute("""
                DELETE FROM purpose_budget_allocations
                WHERE purpose = ? AND start_date = '2020-01-01' AND end_date = '2099-12-31'
            """, (purpose,))
            deleted_count += 1

    conn.commit()
    conn.close()
    return deleted_count


def get_stale_migration_records() -> list:
    """
    Get list of purposes with stale migration records (2020-01-01 to 2099-12-31).
    Returns list of dicts with purpose name and whether it has real records too.
    Checks both old purpose_budget_allocations and new purpose_budgets tables.
    """
    conn = get_conn()
    c = conn.cursor()

    stale_records = []

    # Check old table for stale records
    c.execute("""
        SELECT DISTINCT purpose FROM purpose_budget_allocations
        WHERE start_date = '2020-01-01' AND end_date = '2099-12-31'
        ORDER BY purpose
    """)

    for row in c.fetchall():
        purpose = row["purpose"]

        # Check if this purpose has real records
        c.execute("""
            SELECT COUNT(*) as cnt FROM purpose_budget_allocations
            WHERE purpose = ? AND NOT (start_date = '2020-01-01' AND end_date = '2099-12-31')
        """, (purpose,))

        real_count = c.fetchone()["cnt"]

        stale_records.append({
            "purpose": purpose,
            "has_real_records": real_count > 0,
            "real_record_count": real_count
        })

    conn.close()
    return stale_records


def normalize_dates_to_iso_format():
    """
    Normalize all dates in purpose_budgets table to YYYY-MM-DD format.
    Converts DD/MM/YYYY format dates to YYYY-MM-DD.
    """
    from datetime import datetime
    conn = get_conn()
    c = conn.cursor()

    date_columns = [
        "drilling_start_date", "drilling_end_date",
        "earthworks_start_date", "earthworks_end_date",
        "fuel_start_date", "fuel_end_date"
    ]

    normalized_count = 0

    try:
        for col in date_columns:
            # Find all dates that are NOT in YYYY-MM-DD format
            c.execute(f"""
                SELECT purpose, {col}
                FROM purpose_budgets
                WHERE {col} IS NOT NULL
                AND {col} NOT LIKE '____-__-__'
            """)

            rows = c.fetchall()

            for row in rows:
                purpose = row["purpose"]
                date_str = row[col]

                try:
                    # Try to parse as DD/MM/YYYY
                    dt = datetime.strptime(date_str, "%d/%m/%Y")
                    normalized_date = dt.strftime("%Y-%m-%d")

                    # Update the record
                    c.execute(
                        f"UPDATE purpose_budgets SET {col} = ? WHERE purpose = ?",
                        (normalized_date, purpose)
                    )
                    normalized_count += 1
                except ValueError:
                    # If we can't parse it, leave it as-is
                    pass

        conn.commit()
        return normalized_count

    except Exception as e:
        print(f"Error normalizing dates: {e}")
        return 0
    finally:
        conn.close()


def get_gantt_timeline_data() -> list:
    """
    Get planned vs actual timeline data for Gantt chart.
    Returns list of dicts showing drilling, earthworks, and fuel activities.
    {
        "Purpose": purpose name,
        "Activity": "Drilling", "Earthworks", or "Fuel",
        "WorkGroup": who performs it,
        "Start": date string,
        "End": date string,
        "Type": "Planned" or "Actual",
        "Duration": number of days,
        "Resource": "Budget" or "Drilling"
    }
    """
    conn = get_conn()
    c = conn.cursor()

    rows = []

    # Get planned timelines from purpose_budgets (new simplified structure)
    from datetime import datetime

    c.execute("""
        SELECT purpose,
               drilling_work_group, drilling_start_date, drilling_end_date,
               earthworks_work_group, earthworks_start_date, earthworks_end_date,
               fuel_start_date, fuel_end_date
        FROM purpose_budgets
        WHERE in_scope = 1
        ORDER BY purpose
    """)

    def calc_duration(start_str, end_str):
        try:
            if start_str and end_str:
                # Try multiple date formats (YYYY-MM-DD and DD/MM/YYYY)
                start_dt = None
                end_dt = None

                # Try YYYY-MM-DD format first
                try:
                    start_dt = datetime.strptime(str(start_str), "%Y-%m-%d")
                except ValueError:
                    pass

                # If that failed, try DD/MM/YYYY format
                if start_dt is None:
                    try:
                        start_dt = datetime.strptime(str(start_str), "%d/%m/%Y")
                    except ValueError:
                        pass

                # Same for end date
                try:
                    end_dt = datetime.strptime(str(end_str), "%Y-%m-%d")
                except ValueError:
                    pass

                if end_dt is None:
                    try:
                        end_dt = datetime.strptime(str(end_str), "%d/%m/%Y")
                    except ValueError:
                        pass

                if start_dt and end_dt:
                    return (end_dt - start_dt).days
        except:
            pass
        return 0

    # Add planned activities: Drilling, Earthworks, Fuel
    for row in c.fetchall():
        purpose = row["purpose"]

        # Drilling activity
        if row["drilling_start_date"] and row["drilling_end_date"]:
            rows.append({
                "Purpose": purpose,
                "Activity": "Drilling",
                "WorkGroup": row["drilling_work_group"] or "Unassigned",
                "Start": row["drilling_start_date"],
                "End": row["drilling_end_date"],
                "Type": "Planned",
                "Duration": calc_duration(row["drilling_start_date"], row["drilling_end_date"]),
                "Resource": "Budget"
            })

        # Earthworks activity
        if row["earthworks_start_date"] and row["earthworks_end_date"]:
            rows.append({
                "Purpose": purpose,
                "Activity": "Earthworks",
                "WorkGroup": row["earthworks_work_group"] or "Unassigned",
                "Start": row["earthworks_start_date"],
                "End": row["earthworks_end_date"],
                "Type": "Planned",
                "Duration": calc_duration(row["earthworks_start_date"], row["earthworks_end_date"]),
                "Resource": "Budget"
            })

        # Fuel activity (combined fuel period)
        if row["fuel_start_date"] and row["fuel_end_date"]:
            rows.append({
                "Purpose": purpose,
                "Activity": "Fuel",
                "WorkGroup": "(Combined)",
                "Start": row["fuel_start_date"],
                "End": row["fuel_end_date"],
                "Type": "Planned",
                "Duration": calc_duration(row["fuel_start_date"], row["fuel_end_date"]),
                "Resource": "Budget"
            })

    # Get actual drilling timelines from PLODs (grouped by purpose)
    c.execute("""
        SELECT DISTINCT
            hp.purpose,
            MIN(p.date) as start_date,
            MAX(p.date) as end_date,
            COUNT(DISTINCT p.id) as plod_count,
            SUM(di.length_m) as total_metres
        FROM drilling_intervals di
        JOIN plods p ON di.plod_id = p.id
        JOIN hole_purposes hp ON di.hole_name = hp.hole_name
        WHERE hp.purpose IS NOT NULL AND hp.purpose != ''
        GROUP BY hp.purpose
        ORDER BY hp.purpose
    """)

    for actual_row in c.fetchall():
        purpose = actual_row["purpose"]

        # Add actual drilling activity
        rows.append({
            "Purpose": purpose,
            "Activity": "Drilling",
            "WorkGroup": "(From PLODs)",
            "Start": actual_row["start_date"],
            "End": actual_row["end_date"],
            "Type": "Actual",
            "Duration": calc_duration(actual_row["start_date"], actual_row["end_date"]),
            "Resource": f"Drilling ({actual_row['plod_count']} PLODs, {actual_row['total_metres']:.0f}m)"
        })

    conn.close()
    return rows
