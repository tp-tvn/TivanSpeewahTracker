"""Tivan Dashboard — Streamlit activity tracking dashboard."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import date, timedelta

import db
import ingest
import tracker_view

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Tivan Dashboard",
    page_icon="⛏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide sidebar toggle + remove default left padding so header sits at the edge
st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none; }
[data-testid="collapsedControl"] { display: none; }
[data-testid="stToolbar"]        { display: none; }
.block-container {
    padding-left:  1.5rem !important;
    padding-right: 1.5rem !important;
    padding-top:   3.5rem !important;
    max-width:     100%   !important;
}
.staging-banner {
    background: linear-gradient(90deg, #ff6b35 0%, #f7931e 100%);
    color: white;
    padding: 12px 20px;
    border-radius: 4px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 20px;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

import subprocess
try:
    current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                           cwd='app', stderr=subprocess.DEVNULL).decode().strip()
except:
    current_branch = "unknown"

if current_branch == "develop":
    st.markdown("""
    <div class="staging-banner">
        🚀 STAGING/DEVELOPER ENVIRONMENT - Changes test here before production
    </div>
    """, unsafe_allow_html=True)

db.init_db()

rigs      = db.get_rigs()
rig_opts  = {"All rigs": None} | {r["short_name"]: r["id"] for r in rigs}

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = (current_branch == "develop")
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# ---------------------------------------------------------------------------
# Dark mode CSS injection (applied every rerun when enabled)
# ---------------------------------------------------------------------------
_DARK_CSS = """
<style>
/* ── Main backgrounds ────────────────────────────────── */
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stAppViewContainer"] > section > div:first-child {
    background-color: #0e1117 !important;
    color: #e0e0e0 !important;
}
[data-testid="stHeader"] {
    background-color: #0e1117 !important;
    border-bottom: 1px solid #2d2d3a !important;
}
/* ── Secondary surfaces ──────────────────────────────── */
.stTabs [data-baseweb="tab-list"],
[data-testid="stExpander"] > details,
[data-testid="stForm"],
[data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
    background-color: #1e2130 !important;
}
[data-testid="stExpander"] summary {
    color: #e0e0e0 !important;
}
/* ── Text ────────────────────────────────────────────── */
p, li, span, label, caption,
h1, h2, h3, h4, h5, h6,
[data-testid="stMarkdownContainer"],
[data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] {
    color: #e0e0e0 !important;
}
/* ── Tabs ────────────────────────────────────────────── */
.stTabs [data-baseweb="tab"] { color: #9ca3af !important; }
.stTabs [aria-selected="true"] { color: #e0e0e0 !important; }
/* ── Inputs ──────────────────────────────────────────── */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div,
[data-baseweb="textarea"] > div {
    background-color: #1e2130 !important;
    color: #e0e0e0 !important;
}
[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
    background-color: #1e2130 !important;
    color: #e0e0e0 !important;
    caret-color: #4F8BF9 !important;
}
/* ── Input / widget labels ───────────────────────────── */
[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #c0c0d0 !important;
}
/* ── Number input container ──────────────────────────── */
[data-testid="stNumberInput"] > div {
    background-color: #1e2130 !important;
    border-color: #3d3d4a !important;
}
/* ── Data editor ─────────────────────────────────────── */
[data-testid="stDataEditor"] th,
[data-testid="stDataEditor"] [role="columnheader"] {
    background-color: #2d2d3a !important;
    color: #e0e0e0 !important;
}
[data-testid="stDataEditor"] td,
[data-testid="stDataEditor"] [role="gridcell"] {
    background-color: #1e2130 !important;
    color: #e0e0e0 !important;
}
/* ── Containers with border ──────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] > div,
[data-testid="stVerticalBlockBorderWrapper"] > div > div {
    background-color: #1e2130 !important;
}
/* ── Buttons ─────────────────────────────────────────── */
.stButton > button {
    background-color: #1e2130 !important;
    color: #e0e0e0 !important;
    border-color: #3d3d4a !important;
}
.stButton > button:hover {
    border-color: #4F8BF9 !important;
    color: #4F8BF9 !important;
}
/* ── Columns ─────────────────────────────────────────── */
[data-testid="stColumn"] {
    background-color: transparent !important;
}
/* ── Popover trigger button ──────────────────────────── */
[data-testid="stPopover"] button {
    background-color: #1e2130 !important;
    color: #e0e0e0 !important;
    border-color: #3d3d4a !important;
}
[data-testid="stPopover"] button:hover {
    border-color: #4F8BF9 !important;
    color: #4F8BF9 !important;
}
/* ── Popover / modal ─────────────────────────────────── */
[data-testid="stPopover"] > div,
[data-testid="stPopoverBody"],
[data-testid="stPopoverBody"] > div,
[data-testid="stPopoverBody"] > div > div {
    background-color: #1e2130 !important;
    color: #e0e0e0 !important;
}
/* Popover inner elements need explicit overrides (portal renders outside app tree) */
[data-testid="stPopoverBody"] [data-baseweb="input"],
[data-testid="stPopoverBody"] [data-baseweb="input"] > div {
    background-color: #2a2d3e !important;
    border-color: #3d3d4a !important;
}
[data-testid="stPopoverBody"] [data-baseweb="input"] input {
    background-color: #2a2d3e !important;
    color: #e0e0e0 !important;
    caret-color: #4F8BF9 !important;
}
[data-testid="stPopoverBody"] .stButton > button {
    background-color: #2a2d3e !important;
    color: #e0e0e0 !important;
    border-color: #3d3d4a !important;
}
[data-testid="stPopoverBody"] p,
[data-testid="stPopoverBody"] span,
[data-testid="stPopoverBody"] label,
[data-testid="stPopoverBody"] [data-testid="stCaptionContainer"] {
    color: #9ca3af !important;
    background-color: transparent !important;
}
/* ── Tooltips ────────────────────────────────────────── */
[data-baseweb="tooltip"],
[data-baseweb="tooltip"] > div,
[role="tooltip"],
[role="tooltip"] > div {
    background-color: #2a2d3e !important;
    color: #e0e0e0 !important;
    border: 1px solid #3d3d4a !important;
    border-radius: 4px !important;
}
/* ── Toggle ──────────────────────────────────────────── */
[data-testid="stToggle"],
[data-testid="stToggle"] > label,
[data-testid="stToggle"] > div {
    background-color: transparent !important;
    color: #e0e0e0 !important;
}
/* ── Slider ──────────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] {
    background-color: transparent !important;
}
/* ── File uploader ───────────────────────────────────── */
[data-testid="stFileUploader"] section {
    background-color: #1e2130 !important;
    border-color: #3d3d4a !important;
}
/* ── Containers / dividers ───────────────────────────── */
hr { border-color: #2d2d3a !important; }
[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: #2d2d3a !important;
    background-color: #1e2130 !important;
}
</style>
"""

if st.session_state.dark_mode:
    st.markdown(_DARK_CSS, unsafe_allow_html=True)


def _recalculate_all(rig_id):
    """Re-run cost calculations for all PLODs for a given rig."""
    import calculate
    with db.get_conn() as conn:
        plod_rows = conn.execute(
            "SELECT id FROM plods WHERE rig_id=?", (rig_id,)
        ).fetchall()
    for pr in plod_rows:
        plod_id = pr["id"]
        with db.get_conn() as conn:
            p   = dict(conn.execute("SELECT * FROM plods WHERE id=?", (plod_id,)).fetchone())
            rig = dict(conn.execute("SELECT * FROM rigs WHERE id=?", (p["rig_id"],)).fetchone())
            drilling    = [dict(r) for r in conn.execute("SELECT * FROM drilling_intervals WHERE plod_id=?", (plod_id,)).fetchall()]
            time_rows   = [dict(r) for r in conn.execute("SELECT * FROM time_breakdown WHERE plod_id=?",    (plod_id,)).fetchall()]
            consumables = [dict(r) for r in conn.execute("SELECT * FROM consumables WHERE plod_id=?",       (plod_id,)).fetchall()]
            equipment   = [dict(r) for r in conn.execute("SELECT * FROM equipment WHERE plod_id=?",         (plod_id,)).fetchall()]
            people      = [dict(r) for r in conn.execute("SELECT * FROM people WHERE plod_id=?",            (plod_id,)).fetchall()]
        parsed = {
            "rig": rig, "coreplan_total": p["coreplan_total"],
            "drilling": drilling, "time_rows": time_rows,
            "consumables": consumables, "equipment": equipment, "people": people,
        }
        summary = calculate.compute_summary(plod_id, parsed)
        db.insert_cost_summary(plod_id, summary)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
logo_path   = Path(__file__).parent / "logo.png"
app_title   = db.get_setting("app_title",    "Tivan Dashboard")
app_subtitle = db.get_setting("app_subtitle", "Tivan Tracking Tool · Tivan Limited")

hdr_brand, hdr_theme, hdr_right = st.columns([8, 1, 1])
with hdr_brand:
    if logo_path.exists():
        import base64
        _logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:4px 0">
  <img src="data:image/png;base64,{_logo_b64}" style="height:60px;width:auto"/>
  <div>
    <div style="font-size:1.6rem;font-weight:700;line-height:1.2">{app_title}</div>
    <div style="font-size:0.85rem;opacity:0.6">{app_subtitle}</div>
  </div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"## {app_title}")
        st.caption(app_subtitle)
with hdr_theme:
    st.write("")
    st.session_state.dark_mode = st.toggle(
        "🌙" if st.session_state.dark_mode else "☀️",
        value=st.session_state.dark_mode,
        help="Toggle dark / light mode",
    )
with hdr_right:
    st.write("")
    if st.session_state.admin_authenticated:
        with st.popover("🔓 Admin", use_container_width=True):
            if current_branch == "develop":
                st.caption("Admin mode (auto-enabled in staging)")
            else:
                st.caption("Admin mode is active.")
            if st.button("Lock", key="admin_lock", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.rerun()
    else:
        with st.popover("🔒 Admin", use_container_width=True):
            st.caption("Enter admin password")
            pw = st.text_input("Password", type="password", key="admin_pw_input",
                               label_visibility="collapsed")
            if st.button("Login", key="admin_login_btn", use_container_width=True):
                if db.check_admin_password(pw):
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")

st.divider()

# ---------------------------------------------------------------------------
# Admin panel (visible only when authenticated)
# ---------------------------------------------------------------------------
if st.session_state.admin_authenticated:
    with st.container(border=True):
        st.markdown("#### ⚙️ Admin Panel")
        adm_purposes, adm_rates, adm_budget, adm_rigs, adm_branding, adm_settings, adm_delete, adm_ew_rates, adm_corrections, adm_feedback, adm_weather = st.tabs([
            "🎯 Drillhole Purposes",
            "💰 Rate Management",
            "📊 Budget Targets",
            "🔩 Rigs",
            "🎨 Branding",
            "🔧 Settings",
            "🗑️ Delete PLODs",
            "🚜 EW Rates",
            "🧠 OCR Corrections",
            "💬 Feedback",
            "🌦️ Weather",
        ])

        # ── Drillhole Purposes ──────────────────────────────────────────────
        with adm_purposes:
            st.markdown("Assign a drill purpose to each hole and set planned metres. Upload CSVs or edit the table below.")

            # ── Planned Metres Import ────────────────────────────────────────
            st.subheader("📋 Upload Planned Metres")
            st.caption("CSV format: two columns — one for hole name, one for planned metres (any header names work).")

            uploaded_planned = st.file_uploader(
                "Upload planned metres list (CSV)", type="csv", key="adm_planned_upload"
            )
            if uploaded_planned:
                try:
                    pp_df = pd.read_csv(uploaded_planned)
                    pp_df.columns = pp_df.columns.str.strip().str.lower().str.replace(r"[\s_]+", "_", regex=True)
                    _HOLE_KW_P = ("hole_name", "hole", "holeid", "hole_id", "drillhole")
                    _METRES_KW = ("planned_metres", "planned", "metres", "meters", "target", "target_metres")
                    hole_col_p = next((c for c in pp_df.columns if c in _HOLE_KW_P), None)
                    metres_col = next((c for c in pp_df.columns if c in _METRES_KW), None)
                    if not hole_col_p:
                        st.error(f"No hole name column found. Got columns: {list(pp_df.columns)}")
                    elif not metres_col:
                        st.error(f"No metres column found. Got columns: {list(pp_df.columns)}")
                    else:
                        preview_p = pp_df[[hole_col_p, metres_col]].rename(
                            columns={hole_col_p: "Hole", metres_col: "Planned Metres"}
                        ).dropna(subset=["Hole"])
                        preview_p["Hole"] = preview_p["Hole"].astype(str).str.strip()
                        preview_p["Planned Metres"] = pd.to_numeric(preview_p["Planned Metres"], errors="coerce")
                        st.dataframe(preview_p, use_container_width=True, height=200)
                        st.caption(f"{len(preview_p)} holes found in file.")
                        if st.button("Import planned metres to database", key="adm_import_planned"):
                            db.set_planned_metres(dict(zip(preview_p["Hole"], preview_p["Planned Metres"])))
                            st.success(f"Imported planned metres for {len(preview_p)} holes.")
                            st.rerun()
                except Exception as e:
                    st.error(f"Could not read CSV: {e}")

            st.divider()
            st.markdown("Assign a drill purpose to each hole. Upload a CSV or edit the table below.")
            st.caption("CSV format: two columns — one for hole name, one for purpose (any header names work).")

            uploaded_purposes = st.file_uploader(
                "Upload drillhole purpose list (CSV)", type="csv", key="adm_purpose_upload"
            )
            if uploaded_purposes:
                try:
                    pu_df = pd.read_csv(uploaded_purposes)
                    pu_df.columns = pu_df.columns.str.strip().str.lower().str.replace(r"[\s_]+", "_", regex=True)
                    _HOLE_KW    = ("hole_name", "hole", "holeid", "hole_id", "drillhole")
                    _PURPOSE_KW = ("purpose", "drill_purpose", "type", "program", "program_purpose")
                    hole_col = next((c for c in pu_df.columns if c in _HOLE_KW), None)
                    purp_col = next((c for c in pu_df.columns if c in _PURPOSE_KW), None)
                    if not hole_col:
                        st.error(f"No hole name column found. Got columns: {list(pu_df.columns)}")
                    elif not purp_col:
                        st.error(f"No purpose column found. Got columns: {list(pu_df.columns)}")
                    else:
                        preview = pu_df[[hole_col, purp_col]].rename(
                            columns={hole_col: "Hole", purp_col: "Purpose"}
                        ).dropna(subset=["Hole"])
                        preview["Hole"]    = preview["Hole"].astype(str).str.strip()
                        preview["Purpose"] = preview["Purpose"].fillna("").astype(str).str.strip()
                        st.dataframe(preview, use_container_width=True, height=200)
                        st.caption(f"{len(preview)} holes found in file.")
                        if st.button("Import to database", key="adm_import_purposes"):
                            db.set_hole_purposes(dict(zip(preview["Hole"], preview["Purpose"])))
                            st.success(f"Imported {len(preview)} hole purposes.")
                            st.rerun()
                except Exception as e:
                    st.error(f"Could not read CSV: {e}")

            st.divider()
            st.markdown("**⚠️ Audit: Holes Without Assigned Purpose**")
            st.caption("These holes have been drilled but don't have a purpose assigned. Assign purposes to account for all drilling in your budget.")

            unassigned_holes = db.get_holes_without_purpose()
            if unassigned_holes:
                ua_df = pd.DataFrame(unassigned_holes)
                st.warning(f"🔴 **{len(ua_df)} holes without purpose assignment**")

                # Display unassigned holes with quick assignment
                st.subheader("Quick Assign Purposes & Variance Commentary")
                _PURPOSES_LIST = ["", "Geotech", "Resource Definition", "Program"]
                _VARIANCE_REASONS = [
                    "",
                    "Hole ended due to safety reasons",
                    "Hole was extended",
                    "Geological conditions encountered",
                    "Reached target depth early",
                    "Hit water/aquifer",
                    "Equipment failure/downtime",
                    "Ore contact found",
                    "Structural issue encountered",
                    "Sample collection completed",
                    "Different hole type required",
                    "Hole abandoned",
                    "Geotechnical testing required extension",
                    "Other",
                ]

                ua_edit_df = ua_df[["hole_name", "status", "planned_m", "actual_m", "variance_m", "drill_hours", "rig", "interval_type", "hole_type"]].copy()
                ua_edit_df["Purpose"] = ""
                ua_edit_df["Variance Reason"] = ""
                ua_edit_df = ua_edit_df[["hole_name", "hole_type", "status", "planned_m", "actual_m", "variance_m", "Purpose", "Variance Reason", "drill_hours", "rig", "interval_type"]]

                ua_edited = st.data_editor(
                    ua_edit_df,
                    column_config={
                        "hole_name":      st.column_config.TextColumn("Hole", disabled=True),
                        "hole_type":      st.column_config.TextColumn("Hole Type", help="Auto-extracted from hole name. Edit if incorrect (e.g., DDRD, RCRD, ROP, etc)"),
                        "status":         st.column_config.TextColumn("Status", disabled=True, help="In Progress = drilling in last 2 days, Completed = no drilling for 2+ days"),
                        "planned_m":      st.column_config.NumberColumn("Planned (m)", disabled=True, format="%.1f"),
                        "actual_m":       st.column_config.NumberColumn("Actual (m)", disabled=True, format="%.1f"),
                        "variance_m":     st.column_config.NumberColumn("Variance (m)", disabled=True, format="%.1f"),
                        "Purpose":        st.column_config.SelectboxColumn("Purpose", options=_PURPOSES_LIST, required=True),
                        "Variance Reason": st.column_config.SelectboxColumn("Variance Reason", options=_VARIANCE_REASONS, required=False),
                        "drill_hours":    st.column_config.NumberColumn("Hours", disabled=True, format="%.1f"),
                        "rig":            st.column_config.TextColumn("Rig", disabled=True),
                        "interval_type":  st.column_config.TextColumn("Type", disabled=True),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="adm_unassigned_holes_editor",
                    height=max(400, len(ua_edit_df) * 35 + 50),
                )

                if st.button("Assign Purposes to Unassigned Holes", key="adm_assign_unassigned"):
                    new_purposes = {}
                    for _, row in ua_edited.iterrows():
                        if row["Purpose"]:  # Only save if purpose is assigned
                            new_purposes[row["hole_name"]] = {
                                "purpose": row["Purpose"],
                                "hole_type": row["hole_type"] if row["hole_type"] else None
                            }

                    if new_purposes:
                        db.set_hole_purposes(new_purposes)
                        st.success(f"✅ Assigned purposes and hole types to {len(new_purposes)} holes. Audit cleared!")
                        st.rerun()
                    else:
                        st.warning("Please assign at least one purpose before saving.")
            else:
                st.success("✅ All drilled holes have purposes assigned!")

            st.divider()
            st.markdown("**Current assignments** — edit inline or via CSV import.")

            # Export/Import section
            exp_imp_col1, exp_imp_col2 = st.columns(2)

            with exp_imp_col1:
                st.subheader("📥 Export to CSV")
                all_holes = db.get_unique_holes()
                if not all_holes:
                    st.info("No holes found in the database yet. Import PLODs first.")
                else:
                    hp_all = db.get_hole_purposes()

                    # Get hole_type from the hole_purposes table
                    conn = db.get_conn()
                    hole_type_map = {}
                    for row in conn.execute("SELECT hole_name, hole_type FROM hole_purposes WHERE hole_type IS NOT NULL").fetchall():
                        hole_type_map[row["hole_name"]] = row["hole_type"]
                    conn.close()

                    export_df = pd.DataFrame({
                        "Hole": all_holes,
                        "Purpose": [hp_all.get(h) or "" for h in all_holes],
                        "Hole Type": [hole_type_map.get(h) or "" for h in all_holes],
                    })

                    csv_data = export_df.to_csv(index=False)
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv_data,
                        file_name="hole_assignments.csv",
                        mime="text/csv",
                        key="export_assignments_csv"
                    )

            with exp_imp_col2:
                st.subheader("📤 Import from CSV")
                uploaded_csv = st.file_uploader(
                    "Upload hole assignments CSV (Hole, Purpose, Hole Type columns)",
                    type="csv",
                    key="import_assignments_csv"
                )

                if uploaded_csv:
                    try:
                        import_df = pd.read_csv(uploaded_csv)

                        # Validate required columns
                        required_cols = {"Hole", "Purpose"}
                        if not required_cols.issubset(set(import_df.columns)):
                            st.error(f"❌ CSV must contain 'Hole' and 'Purpose' columns. Found: {list(import_df.columns)}")
                        else:
                            st.success(f"✅ Valid CSV - {len(import_df)} holes found")
                            st.dataframe(import_df, use_container_width=True, hide_index=True)

                            if st.button("Apply Imported Assignments", key="apply_import_assignments"):
                                import_mapping = {}
                                for _, row in import_df.iterrows():
                                    hole = row.get("Hole")
                                    purpose = row.get("Purpose") or None
                                    hole_type = row.get("Hole Type") or None

                                    if hole:
                                        import_mapping[hole] = {
                                            "purpose": purpose,
                                            "hole_type": hole_type
                                        }

                                if import_mapping:
                                    db.set_hole_purposes(import_mapping)
                                    st.success(f"✅ Imported and saved {len(import_mapping)} hole assignments!")
                                    st.rerun()
                                else:
                                    st.warning("No valid holes to import.")

                    except Exception as e:
                        st.error(f"❌ Could not read CSV: {e}")

            st.divider()
            st.markdown("**Or edit inline and save:**")
            all_holes = db.get_unique_holes()
            if not all_holes:
                st.info("No holes found in the database yet. Import PLODs first.")
            else:
                _PURPOSES_LIST = ["", "Geotech", "Resource Definition", "Program"]
                hp_all = db.get_hole_purposes()
                all_holes_df = pd.DataFrame({
                    "Hole":    all_holes,
                    "Purpose": [hp_all.get(h) or "" for h in all_holes],
                })
                edited_all = st.data_editor(
                    all_holes_df,
                    column_config={
                        "Hole":    st.column_config.TextColumn("Hole", disabled=True),
                        "Purpose": st.column_config.SelectboxColumn(
                                       "Purpose", options=_PURPOSES_LIST, required=False
                                   ),
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="adm_all_holes_editor",
                )
                if st.button("Save", key="adm_save_all_holes"):
                    db.set_hole_purposes(dict(zip(edited_all["Hole"], edited_all["Purpose"])))
                    st.success("Hole purposes saved.")
                    st.rerun()

            st.divider()
            st.markdown("**Hole Type → Purpose Validation**")
            st.caption("Review which hole types appear under each purpose. Flag inconsistencies (e.g., RCRD shouldn't appear under 'Sterilisation').")

            ht_purpose_map = db.get_hole_type_purpose_mapping()
            if ht_purpose_map:
                # Create a dataframe for better visualization
                validation_data = []
                for hole_type in sorted(ht_purpose_map.keys()):
                    purposes = ht_purpose_map[hole_type]
                    validation_data.append({
                        "Hole Type": hole_type,
                        "Purposes": ", ".join(purposes),
                        "Count": len(purposes),
                    })

                val_df = pd.DataFrame(validation_data)
                st.dataframe(val_df, use_container_width=True, hide_index=True)

                # Optional: show warnings for hole types appearing under multiple purposes
                multi_purpose_types = {ht: purposes for ht, purposes in ht_purpose_map.items() if len(purposes) > 1}
                if multi_purpose_types:
                    st.warning("⚠️ These hole types appear under multiple purposes (may indicate data entry errors):")
                    for ht, purposes in sorted(multi_purpose_types.items()):
                        st.write(f"**{ht}**: {', '.join(purposes)}")
            else:
                st.info("No hole type assignments yet. Assign purposes in the audit section above.")

        # ── Rate Management ─────────────────────────────────────────────────
        with adm_rates:
            st.markdown("""
            Edit rates below. Changes take effect immediately for any **new** PLODs imported after saving.
            Use **Save & Recalculate** to refresh costs on already-imported PLODs.
            """)
            rate_groups = db.get_rate_groups()
            if not rate_groups:
                st.info("No rate groups found. Add a rig first.")
            else:
                group_tabs = st.tabs([g["rate_group"] for g in rate_groups])
                for _tab, group in zip(group_tabs, rate_groups):
                    with _tab:
                        group_name = group["rate_group"]
                        rates = db.get_rates_for_group(group_name)
                        if not rates:
                            st.info("No rates defined for this group.")
                            continue
                        df_rates = pd.DataFrame(rates)[["category", "label", "rate", "unit"]]
                        df_rates = df_rates.rename(columns={"label": "Description", "rate": "Rate", "unit": "Unit"})
                        edited = st.data_editor(
                            df_rates[["category", "Description", "Rate", "Unit"]],
                            column_config={
                                "category":    st.column_config.TextColumn("Category",    disabled=True),
                                "Description": st.column_config.TextColumn("Description", disabled=True),
                                "Rate":        st.column_config.NumberColumn("Rate ($)", min_value=0.0, format="%.2f"),
                                "Unit":        st.column_config.TextColumn("Unit",        disabled=True),
                            },
                            use_container_width=True,
                            hide_index=True,
                            key=f"adm_rates_{group_name}",
                        )
                        col_save, col_recalc, _ = st.columns([1, 2, 4])
                        with col_save:
                            if st.button("Save Rates", key=f"adm_save_{group_name}"):
                                cat_rates = dict(zip(edited["category"], edited["Rate"].astype(float)))
                                db.update_rates_for_group(group_name, cat_rates)
                                st.success("Rates saved.")
                                st.rerun()
                        with col_recalc:
                            if st.button("Save & Recalculate All PLODs", key=f"adm_recalc_{group_name}"):
                                cat_rates = dict(zip(edited["category"], edited["Rate"].astype(float)))
                                db.update_rates_for_group(group_name, cat_rates)
                                with db.get_conn() as conn:
                                    rig_ids = [r[0] for r in conn.execute(
                                        "SELECT id FROM rigs WHERE rate_group=?", (group_name,)
                                    ).fetchall()]
                                for rid in rig_ids:
                                    _recalculate_all(rid)
                                st.success("Rates saved and all PLODs recalculated.")
                                st.rerun()

            st.divider()
            st.subheader("Add a New Rig")
            with st.expander("Add Rig"):
                c1, c2, c3, c4, c5, c6 = st.columns(6)
                new_name     = c1.text_input("Full name",   placeholder="Strike Rig 99")
                new_short    = c2.text_input("Short name",  placeholder="STR RIG 99")
                new_type     = c3.selectbox("Type", ["RC", "DD", "HYD"])
                new_def_itype= c4.selectbox("Default Interval", ["RC", "PQ3", "HQ3", "NQ3", "HYD", "DD"])
                new_group    = c5.text_input("Rate group",  placeholder="Strike RC")
                new_contract = c6.text_input("Contract (optional)")
                if st.button("Add Rig"):
                    if new_name and new_short:
                        with db.get_conn() as conn:
                            conn.execute(
                                "INSERT OR IGNORE INTO rigs (name, short_name, rig_type, contract, rate_group, default_interval_type) VALUES (?,?,?,?,?,?)",
                                (new_name, new_short, new_type, new_contract, new_group or None, new_def_itype),
                            )
                            conn.commit()
                        st.success(f"Added {new_short}. Reload to see it in the rate tabs.")
                        st.rerun()

        # ── Budget Targets ───────────────────────────────────────────────────
        with adm_budget:
            st.markdown(
                "Set a **budget cost per metre** by drill type and hole type. "
                "**Rows** = drilling interval types (RC, HQ3, etc.). "
                "**Columns** = hole types (RCRD, DDGT, etc.). "
                "Leave blank if that combination doesn't apply."
            )

            # Drill types (rows) and hole types (columns)
            # _DRILL_TYPES sourced from actual interval_type values in drilling_intervals table
            _DRILL_TYPES = ["RC", "HQ3", "PQ3"]
            _HOLE_TYPES = ["RCRD", "DDGT", "DMET", "REXP", "STER", "RCAG", "DDRD"]

            budget_targets = db.get_budget_targets()  # {drill_type: {hole_type: rate}}

            # Build a flat DataFrame with one row per drill type, columns = hole types
            budget_rows = []
            for dt in _DRILL_TYPES:
                row = {"Drill Type": dt}
                for ht in _HOLE_TYPES:
                    row[ht] = budget_targets.get(dt, {}).get(ht, None)
                budget_rows.append(row)
            budget_df = pd.DataFrame(budget_rows)

            edited_budget = st.data_editor(
                budget_df,
                column_config={
                    "Drill Type": st.column_config.TextColumn("Drill Type", disabled=True),
                    **{
                        ht: st.column_config.NumberColumn(ht, min_value=0.0, format="$%.2f")
                        for ht in _HOLE_TYPES
                    },
                },
                use_container_width=True,
                hide_index=True,
                key="adm_budget_editor",
            )
            if st.button("Save Budget Targets", key="adm_save_budget"):
                new_mapping = {}
                for _, row in edited_budget.iterrows():
                    dt = row["Drill Type"]
                    new_mapping[dt] = {}
                    for ht in _HOLE_TYPES:
                        val = row[ht]
                        if pd.notna(val) and val > 0:  # Only save non-null, positive values
                            new_mapping[dt][ht] = float(val)
                db.set_budget_targets(new_mapping)
                st.success("✅ Budget targets saved!")
                st.rerun()

            st.divider()
            st.markdown("**⚠️ Audit: Drill Types with Missing Budget Rates**")
            st.caption("These drill type + hole type combinations have actual drilling data but no budget rate configured. Either add a rate above or click 'Ignore' if this combination doesn't apply.")

            missing_rates = db.get_missing_budget_rates()
            if missing_rates:
                st.error(f"🔴 **{len(missing_rates)} missing rate configurations**")

                # Display each missing rate with an ignore button
                for idx, rate in enumerate(missing_rates):
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1.5])
                    with col1:
                        st.write(f"**{rate['drill_type']}**")
                    with col2:
                        st.write(f"**{rate['hole_type']}**")
                    with col3:
                        st.write(f"{rate['metres']:.1f} m")
                    with col4:
                        if st.button("Ignore", key=f"ignore_{idx}_{rate['drill_type']}_{rate['hole_type']}"):
                            db.ignore_rate_combination(rate['drill_type'], rate['hole_type'])
                            st.success(f"Ignored {rate['drill_type']} + {rate['hole_type']}")
                            st.rerun()

                st.info("📋 Add missing rates to the budget table above, then click Save. Or click 'Ignore' if this combination doesn't apply.")
            else:
                st.success("✓ All drill type + hole type combinations have budget rates configured or ignored!")

            # Show ignored combinations
            ignored = db.get_ignored_rate_combinations()
            if ignored:
                st.divider()
                st.markdown("**Ignored Rate Combinations**")
                st.caption("These combinations are marked as 'not applicable' and won't appear in the audit.")

                ignored_df = pd.DataFrame(ignored)
                for idx, row in ignored_df.iterrows():
                    col1, col2, col3, col4 = st.columns([2, 2, 3, 1.5])
                    with col1:
                        st.write(f"{row['drill_type']}")
                    with col2:
                        st.write(f"{row['hole_type']}")
                    with col3:
                        st.write(f"_{row['reason'] or '(no reason given)'}_")
                    with col4:
                        if st.button("Un-ignore", key=f"unignore_{idx}_{row['drill_type']}_{row['hole_type']}"):
                            db.unignore_rate_combination(row['drill_type'], row['hole_type'])
                            st.success(f"Un-ignored {row['drill_type']} + {row['hole_type']}")
                            st.rerun()

            st.divider()
            st.markdown("**Metres per shift & Slow Drilling Threshold** — used for the metres-tracking chart and slow hole flagging on the dashboard.")
            metres_targets = db.get_metres_targets()
            slow_thresholds_adm = db.get_slow_thresholds()
            metres_df = pd.DataFrame([
                {
                    "Drill Type":            dt,
                    "Target (m/shift)":      metres_targets.get(dt, 0.0),
                    "Slow Threshold (m/hr)": slow_thresholds_adm.get(dt, 0.0),
                }
                for dt in _DRILL_TYPES
            ])
            edited_metres = st.data_editor(
                metres_df,
                column_config={
                    "Drill Type":            st.column_config.TextColumn("Drill Type", disabled=True),
                    "Target (m/shift)":      st.column_config.NumberColumn(
                        "Target (m/shift)", min_value=0.0, format="%.1f m"
                    ),
                    "Slow Threshold (m/hr)": st.column_config.NumberColumn(
                        "Slow Threshold (m/hr)", min_value=0.0, format="%.1f m/hr",
                        help="Holes drilled below this rate will be flagged red on the dashboard.",
                    ),
                },
                use_container_width=True,
                hide_index=True,
                key="adm_metres_editor",
            )
            if st.button("Save Metres Targets", key="adm_save_metres"):
                db.set_metres_targets(
                    dict(zip(edited_metres["Drill Type"], edited_metres["Target (m/shift)"]))
                )
                db.set_slow_thresholds(
                    dict(zip(edited_metres["Drill Type"], edited_metres["Slow Threshold (m/hr)"]))
                )
                st.success("Metres targets saved.")

            st.divider()
            st.markdown("**Purpose Budget Allocations** — set total budget per purpose for drilling, earthworks, and fuel. Toggle **In Scope** to flag out-of-scope activities.")

            # Define the required order of purposes
            _PURPOSE_ORDER = [
                "General (Site Access, general freight, umpire samples)",
                "2026 RC Infill A Vein",
                "2026 P1 RC Infill G Vein",
                "2026 P2 RC Infill G Vein",
                "2026 DD A Vein HG Infill Deferred 2025",
                "2026 P1 Infill Deferred 2025 Drilling",
                "2026 Infill Deferred 2025 Drilling",
                "2026 Dingo Vein Extensional Drilling",
                "2026 Southern Extensional Drilling",
                "2026 WSP Work - Phase 2 Access Road Drilling",
                "2026 WD Sterilisation Drilling",
                "2026 H Vein 80m",
                "2026 H Vein 40m",
                "2026 WSP Work - Process Plant Geotechnical",
                "2026 District 9 Extensional Drilling",
                "2026 P1 MET Drilling",
                "2026 P2 MET Drilling",
                "2026 DD Drilling Contigency",
                "2026 RC Drilling Contigency",
                "2026 RC Additional Mob/Demob",
                "MDM Mobilisation / Demobilisation of D9 Equipment",
                "MDM Mobilisation of all other equipment",
                "NGCM Mobilisation",
                "Re-establishing access to site",
                "2026 MDM Metallurgy Costeaning",
                "2026 MDM Rehabilitation",
                "2026 NGCM Rehabilitation",
                "WSP Work - Phase 2 Access Road Test Pits (incl. Rehab)",
                "WSP Work - Phase 2 Access Costeans",
                "WG Work - Phase 2 Access Track",
                "WSP Field Work - Access road / GNH Tie in Test Pits",
                "WSP Field Work - Processing Plant Geophysics",
            ]

            all_purposes = db.get_all_purposes()
            if not all_purposes:
                st.info("No purposes found. Import PLODs with purpose assignments first.")
            else:
                # Normalize any mixed date formats (DD/MM/YYYY → YYYY-MM-DD)
                # This ensures timeline and duration calculations work correctly
                db.normalize_dates_to_iso_format()

                # Get all purposes with new simplified structure
                purpose_budgets = db.get_all_purpose_budgets()
                budget_dict = {pb["purpose"]: pb for pb in purpose_budgets}

                # Build rows with three column groups: Drilling, Earthworks, Fuel
                budget_rows = []
                for purpose in sorted(all_purposes):
                    pb = budget_dict.get(purpose, {})
                    budget_rows.append({
                        "In Scope": pb.get("in_scope", 1) == 1,
                        "Purpose": purpose,
                        # DRILLING GROUP
                        "Drill_WorkGroup": pb.get("drilling_work_group", ""),
                        "Drill_Budget": pb.get("drilling_budget", 0.0),
                        "Drill_Start": pb.get("drilling_start_date", ""),
                        "Drill_End": pb.get("drilling_end_date", ""),
                        # EARTHWORKS GROUP
                        "EW_WorkGroup": pb.get("earthworks_work_group", ""),
                        "EW_Budget": pb.get("earthworks_budget", 0.0),
                        "EW_Start": pb.get("earthworks_start_date", ""),
                        "EW_End": pb.get("earthworks_end_date", ""),
                        # FUEL GROUP
                        "Fuel_Budget": pb.get("fuel_budget", 0.0),
                        # METADATA
                        "Notes": pb.get("notes", ""),
                    })

                budget_df = pd.DataFrame(budget_rows)

                # Display with three column groups for clarity
                st.subheader("📋 Purpose Budgets — Three Activity Groups")
                st.caption(
                    "**In Scope** | **Purpose** | "
                    "[DRILLING: WorkGroup, Budget, Start, End] | "
                    "[EARTHWORKS: WorkGroup, Budget, Start, End] | "
                    "[FUEL: Budget] | Notes"
                )

                edited_budget = st.data_editor(
                    budget_df,
                    column_config={
                        "In Scope": st.column_config.CheckboxColumn("✓", width=40),
                        "Purpose": st.column_config.TextColumn("Purpose", width=180, disabled=True),
                        # DRILLING COLUMNS
                        "Drill_WorkGroup": st.column_config.TextColumn("Drill WG", width=100),
                        "Drill_Budget": st.column_config.NumberColumn("Drill $", width=80, min_value=0.0, format="$%.0f"),
                        "Drill_Start": st.column_config.TextColumn("Drill Start", width=90, help="YYYY-MM-DD"),
                        "Drill_End": st.column_config.TextColumn("Drill End", width=90, help="YYYY-MM-DD"),
                        # EARTHWORKS COLUMNS
                        "EW_WorkGroup": st.column_config.TextColumn("EW WG", width=100),
                        "EW_Budget": st.column_config.NumberColumn("EW $", width=80, min_value=0.0, format="$%.0f"),
                        "EW_Start": st.column_config.TextColumn("EW Start", width=90, help="YYYY-MM-DD"),
                        "EW_End": st.column_config.TextColumn("EW End", width=90, help="YYYY-MM-DD"),
                        # FUEL COLUMN
                        "Fuel_Budget": st.column_config.NumberColumn("Fuel $", width=80, min_value=0.0, format="$%.0f"),
                        # NOTES
                        "Notes": st.column_config.TextColumn("Notes", width=150),
                    },
                    use_container_width=True,
                    hide_index=True,
                    key="adm_purpose_budgets_editor",
                    height=max(500, len(budget_df) * 36 + 50),
                )

                if st.button("💾 Save All Budgets", key="adm_save_budgets"):
                    saved_count = 0
                    for _, row in edited_budget.iterrows():
                        try:
                            if db.save_purpose_budget(
                                purpose=row["Purpose"],
                                drilling_work_group=row.get("Drill_WorkGroup", ""),
                                drilling_budget=float(row.get("Drill_Budget", 0)),
                                drilling_start_date=row.get("Drill_Start", ""),
                                drilling_end_date=row.get("Drill_End", ""),
                                earthworks_work_group=row.get("EW_WorkGroup", ""),
                                earthworks_budget=float(row.get("EW_Budget", 0)),
                                earthworks_start_date=row.get("EW_Start", ""),
                                earthworks_end_date=row.get("EW_End", ""),
                                fuel_budget=float(row.get("Fuel_Budget", 0)),
                                in_scope=bool(row.get("In Scope", True)),
                                notes=row.get("Notes", "")
                            ):
                                saved_count += 1
                        except Exception as e:
                            st.error(f"Error saving {row['Purpose']}: {e}")

                    st.success(f"✅ Saved {saved_count} purpose budgets!")

                # ── Data Cleanup ────────────────────────────────────────────────
                st.divider()
                st.subheader("🧹 Data Cleanup")
                st.caption("Remove duplicate migration data")

                stale_records = db.get_stale_migration_records()
                stale_with_real = [r for r in stale_records if r["has_real_records"]]
                stale_only = [r for r in stale_records if not r["has_real_records"]]

                if stale_with_real:
                    st.warning(
                        f"⚠️ Found {len(stale_with_real)} **DUPLICATE** budget records.\n\n"
                        f"These purposes have both:\n"
                        f"- Old stale dates (2020-01-01 to 2099-12-31) from migration\n"
                        f"- Real imported dates from Gantt chart\n\n"
                        f"Click below to delete the duplicates (keeps the real dates)."
                    )

                    # Show which purposes have duplicates
                    with st.expander(f"Show {len(stale_with_real)} duplicates to remove", expanded=False):
                        stale_df = pd.DataFrame([
                            {
                                "Purpose": r["purpose"],
                                "Real Records": r["real_record_count"]
                            }
                            for r in stale_with_real
                        ])
                        st.dataframe(stale_df, use_container_width=True, hide_index=True)

                    if st.button("🧹 Remove Duplicates", key="adm_cleanup_stale"):
                        deleted = db.delete_stale_migration_records()
                        st.success(f"✅ Deleted {deleted} duplicate records.")
                        st.rerun()

                if stale_only:
                    st.info(
                        f"ℹ️ **{len(stale_only)} orphan records found** (no imported dates)\n\n"
                        f"These purposes exist only with stale dates (2020-01-01 to 2099-12-31). "
                        f"They were never imported from Gantt. These are **automatically hidden** "
                        f"from the Gantt chart timeline, so no action needed."
                    )

                if not stale_with_real and not stale_only:
                    st.success("✅ No stale records found. Your data is clean!")

                # ── Gantt Chart Import ──────────────────────────────────────────
                st.divider()
                st.subheader("📊 Import from Gantt Chart")
                st.caption(
                    "Upload a Gantt chart CSV with columns: Item Name, Start Date (YYYY-MM-DD), End Date (YYYY-MM-DD), "
                    "and optionally Budget. The system will map items to purposes using fuzzy matching or manual assignment."
                )

                gantt_upload = st.file_uploader(
                    "Upload Gantt chart (CSV)",
                    type=["csv", "xlsx"],
                    key="adm_gantt_upload"
                )

                if gantt_upload:
                    try:
                        # Read the file
                        if gantt_upload.name.endswith('.xlsx'):
                            gantt_df = pd.read_excel(gantt_upload)
                        else:
                            gantt_df = pd.read_csv(gantt_upload)

                        # Normalize column names
                        gantt_df.columns = gantt_df.columns.str.strip().str.lower().str.replace(r"[\s_]+", "_", regex=True)

                        # Find key columns by common patterns
                        name_col = next((c for c in gantt_df.columns if any(kw in c for kw in ["item", "name", "title"])), None)
                        start_col = next((c for c in gantt_df.columns if any(kw in c for kw in ["start", "start_date", "begin"])), None)
                        end_col = next((c for c in gantt_df.columns if any(kw in c for kw in ["end", "end_date", "finish"])), None)
                        budget_col = next((c for c in gantt_df.columns if any(kw in c for kw in ["budget", "amount", "cost"])), None)
                        workgroup_col = next((c for c in gantt_df.columns if any(kw in c for kw in ["work", "group", "contractor", "team", "crew"])), None)
                        activity_col = next((c for c in gantt_df.columns if any(kw in c for kw in ["activity", "type", "work_type", "activity_type"])), None)

                        if not name_col or not start_col or not end_col:
                            st.error(f"Could not identify required columns. Found: {list(gantt_df.columns)}")
                            st.info("Expected columns containing: 'item/name', 'start/start_date', 'end/end_date'")
                        else:
                            # Prepare the mapping dataframe
                            gantt_import_rows = []
                            for _, row in gantt_df.iterrows():
                                item_name = str(row[name_col]).strip()
                                start_date = str(row[start_col]).strip() if start_col else ""
                                end_date = str(row[end_col]).strip() if end_col else ""
                                budget = float(row[budget_col]) if budget_col and pd.notna(row[budget_col]) else 0.0
                                work_group = str(row[workgroup_col]).strip() if workgroup_col and pd.notna(row[workgroup_col]) else ""
                                activity_type = str(row[activity_col]).strip().lower() if activity_col and pd.notna(row[activity_col]) else "drilling"

                                # Normalize activity type
                                if activity_type not in ["drilling", "earthworks"]:
                                    # Try to detect from name or work group
                                    item_lower = item_name.lower()
                                    if any(kw in item_lower for kw in ["earthwork", "ew", "excavat", "blast", "grade"]):
                                        activity_type = "earthworks"
                                    elif any(kw in item_lower for kw in ["drill", "bore", "core"]):
                                        activity_type = "drilling"
                                    else:
                                        activity_type = "drilling"  # Default

                                # Clean up dates if they're in Excel format
                                try:
                                    if isinstance(row[start_col], str):
                                        from datetime import datetime
                                        start_date = datetime.strptime(start_date.split()[0], "%Y-%m-%d").strftime("%Y-%m-%d")
                                    else:
                                        start_date = pd.to_datetime(row[start_col]).strftime("%Y-%m-%d")
                                except:
                                    pass

                                try:
                                    if isinstance(row[end_col], str):
                                        from datetime import datetime
                                        end_date = datetime.strptime(end_date.split()[0], "%Y-%m-%d").strftime("%Y-%m-%d")
                                    else:
                                        end_date = pd.to_datetime(row[end_col]).strftime("%Y-%m-%d")
                                except:
                                    pass

                                gantt_import_rows.append({
                                    "Gantt Item": item_name,
                                    "Start Date": start_date,
                                    "End Date": end_date,
                                    "Budget": budget,
                                    "Work Group": work_group,
                                    "Activity Type": activity_type,
                                    "Map to Purpose": ""
                                })

                            gantt_import_df = pd.DataFrame(gantt_import_rows)

                            st.subheader("📋 Auto-Match Gantt Items to Purposes")
                            st.caption(
                                "System auto-matches items to purposes by name similarity. "
                                "✅ = Auto-matched (you can override). ❓ = Needs your input. "
                                "Leave blank to skip (timeline placeholders)."
                            )

                            # Auto-match Gantt items to purposes using fuzzy matching
                            from difflib import SequenceMatcher

                            def get_match_score(gantt_name: str, purpose_name: str) -> float:
                                """Calculate similarity score between two strings (0-1)"""
                                # Normalize to lowercase for comparison
                                g = gantt_name.lower()
                                p = purpose_name.lower()
                                return SequenceMatcher(None, g, p).ratio()

                            def find_best_match(gantt_item: str, purposes: list, threshold: float = 0.6) -> str:
                                """Find best matching purpose or empty string if no good match"""
                                if not purposes:
                                    return ""

                                scores = [(p, get_match_score(gantt_item, p)) for p in purposes]
                                best_match, best_score = max(scores, key=lambda x: x[1])

                                # Return match only if score exceeds threshold
                                return best_match if best_score >= threshold else ""

                            # Apply auto-matching
                            purpose_list = list(all_purposes) if all_purposes else []
                            gantt_import_df["Map to Purpose"] = gantt_import_df["Gantt Item"].apply(
                                lambda x: find_best_match(x, purpose_list, threshold=0.6)
                            )

                            # Add a helper column to show match status (for display only)
                            gantt_import_df["Match Status"] = gantt_import_df["Map to Purpose"].apply(
                                lambda x: "✅ Auto-matched" if x else "❓ Needs input"
                            )

                            # Create mapping editor
                            purpose_options = [""] + list(all_purposes) if all_purposes else [""]

                            edited_gantt_import = st.data_editor(
                                gantt_import_df,
                                column_config={
                                    "Gantt Item": st.column_config.TextColumn("Gantt Item", disabled=True),
                                    "Start Date": st.column_config.TextColumn("Start Date", disabled=True),
                                    "End Date": st.column_config.TextColumn("End Date", disabled=True),
                                    "Budget": st.column_config.NumberColumn("Budget ($)", disabled=True),
                                    "Work Group": st.column_config.TextColumn("Work Group", help="Edit if needed (auto-detected from Gantt)"),
                                    "Activity Type": st.column_config.SelectboxColumn(
                                        "Activity Type",
                                        options=["drilling", "earthworks"],
                                        help="Determines which contractor field this work group is assigned to"
                                    ),
                                    "Match Status": st.column_config.TextColumn("Status", disabled=True, help="Auto-matched or needs input"),
                                    "Map to Purpose": st.column_config.SelectboxColumn(
                                        "Map to Purpose",
                                        options=purpose_options,
                                        help="Override auto-match or assign manually. Leave blank to skip (placeholder)"
                                    )
                                },
                                use_container_width=True,
                                hide_index=True,
                                key="adm_gantt_mapping_editor",
                                height=max(400, len(gantt_import_df) * 35 + 50),
                            )

                            # Show summary of matches
                            auto_matched = len(edited_gantt_import[edited_gantt_import["Match Status"] == "✅ Auto-matched"])
                            needs_input = len(edited_gantt_import[edited_gantt_import["Match Status"] == "❓ Needs input"])

                            col_summary1, col_summary2, col_summary3 = st.columns(3)
                            with col_summary1:
                                st.metric("Auto-Matched", auto_matched, help="Items matched by name similarity")
                            with col_summary2:
                                st.metric("Needs Input", needs_input, help="Items with no good match")
                            with col_summary3:
                                will_import = len(edited_gantt_import[edited_gantt_import["Map to Purpose"] != ""])
                                st.metric("Will Import", will_import, help="Items with an assigned purpose")

                            # Show items that will be skipped (placeholders)
                            skipped_rows = edited_gantt_import[edited_gantt_import["Map to Purpose"] == ""]
                            create_timeline_only = False
                            if len(skipped_rows) > 0:
                                with st.expander("ℹ️ Unmatched Items (Can Create Timeline-Only Entries)", expanded=False):
                                    st.caption(
                                        f"{len(skipped_rows)} items have no purpose assigned. "
                                        "Create **timeline-only** entries to show them on Gantt (no budget tracking). "
                                        "Useful for contractors like WSP with scheduled activities but external cost management."
                                    )
                                    skipped_display = skipped_rows[["Gantt Item", "Start Date", "End Date", "Work Group", "Budget"]].copy()
                                    st.dataframe(skipped_display, use_container_width=True, hide_index=True)

                                    create_timeline_only = st.checkbox(
                                        "Create timeline-only purposes for these items",
                                        value=False,
                                        key="create_timeline_only_checkbox",
                                        help="Items will appear on Gantt chart but have no budget allocations"
                                    )

                            # Show preview of what will be created
                            mapped_rows = edited_gantt_import[edited_gantt_import["Map to Purpose"] != ""]

                            if len(mapped_rows) > 0:
                                st.subheader(f"📊 Preview: How Gantt Items Will Be Aggregated")
                                st.caption("Items are separated by Activity Type (Drilling vs Earthworks) and assigned to correct contractor columns")

                                # Group by purpose and activity type to show aggregation
                                preview_rows = []
                                for purpose in mapped_rows["Map to Purpose"].unique():
                                    purpose_items = mapped_rows[mapped_rows["Map to Purpose"] == purpose]

                                    # Separate by activity type
                                    drilling_items = purpose_items[purpose_items["Activity Type"] == "drilling"]
                                    ew_items = purpose_items[purpose_items["Activity Type"] == "earthworks"]

                                    # Process drilling items
                                    if len(drilling_items) > 0:
                                        drill_start = [row["Start Date"] for _, row in drilling_items.iterrows() if isinstance(row["Start Date"], str)]
                                        drill_end = [row["End Date"] for _, row in drilling_items.iterrows() if isinstance(row["End Date"], str)]
                                        drill_budget = drilling_items["Budget"].sum()
                                        drill_wg = drilling_items.iloc[0].get("Work Group", "")

                                        preview_rows.append({
                                            "Purpose": purpose,
                                            "Activity": "Drilling",
                                            "Items": len(drilling_items),
                                            "Contractor": drill_wg,
                                            "Budget": f"${drill_budget:,.0f}" if drill_budget > 0 else "$0",
                                            "Start": min(drill_start) if drill_start else "—",
                                            "End": max(drill_end) if drill_end else "—"
                                        })

                                    # Process earthworks items
                                    if len(ew_items) > 0:
                                        ew_start = [row["Start Date"] for _, row in ew_items.iterrows() if isinstance(row["Start Date"], str)]
                                        ew_end = [row["End Date"] for _, row in ew_items.iterrows() if isinstance(row["End Date"], str)]
                                        ew_budget = ew_items["Budget"].sum()
                                        ew_wg = ew_items.iloc[0].get("Work Group", "")

                                        preview_rows.append({
                                            "Purpose": purpose,
                                            "Activity": "Earthworks",
                                            "Items": len(ew_items),
                                            "Contractor": ew_wg,
                                            "Budget": f"${ew_budget:,.0f}" if ew_budget > 0 else "$0",
                                            "Start": min(ew_start) if ew_start else "—",
                                            "End": max(ew_end) if ew_end else "—"
                                        })

                                preview_df = pd.DataFrame(preview_rows)
                                st.dataframe(
                                    preview_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        "Activity": st.column_config.TextColumn("Activity", help="Drilling or Earthworks"),
                                        "Items": st.column_config.NumberColumn("Items", help="Count of Gantt items"),
                                        "Contractor": st.column_config.TextColumn("Contractor/Work Group", help="Assigned to this contractor field"),
                                        "Budget": st.column_config.TextColumn("Budget (Summed)"),
                                        "Start": st.column_config.TextColumn("Start Date"),
                                        "End": st.column_config.TextColumn("End Date"),
                                    }
                                )

                                # Show detailed breakdown
                                with st.expander("📋 Detailed Item Breakdown by Activity Type", expanded=False):
                                    detail_rows = []
                                    for purpose in mapped_rows["Map to Purpose"].unique():
                                        purpose_items = mapped_rows[mapped_rows["Map to Purpose"] == purpose]
                                        for _, item in purpose_items.iterrows():
                                            detail_rows.append({
                                                "Purpose": purpose,
                                                "Activity": item.get("Activity Type", "drilling").capitalize(),
                                                "Gantt Item": item["Gantt Item"],
                                                "Contractor": item.get("Work Group", ""),
                                                "Start Date": item["Start Date"],
                                                "End Date": item["End Date"],
                                                "Budget": f"${item['Budget']:,.0f}" if item['Budget'] > 0 else "$0"
                                            })

                                    detail_df = pd.DataFrame(detail_rows)
                                    st.dataframe(detail_df, use_container_width=True, hide_index=True)

                                col_import1, col_import2 = st.columns([2, 1])
                                with col_import1:
                                    if st.button("✅ Import Gantt Chart Allocations", key="adm_import_gantt", use_container_width=True):
                                        import_count = 0
                                        timeline_only_count = 0

                                        # Import budget-tracked purposes
                                        purpose_groups = mapped_rows.groupby("Map to Purpose")

                                        for purpose, group_rows in purpose_groups:
                                            # For each purpose, calculate aggregate date range and budget
                                            start_dates = [row["Start Date"] for _, row in group_rows.iterrows() if isinstance(row["Start Date"], str)]
                                            end_dates = [row["End Date"] for _, row in group_rows.iterrows() if isinstance(row["End Date"], str)]
                                            total_budget = group_rows["Budget"].sum()

                                            min_date = min(start_dates) if start_dates else None
                                            max_date = max(end_dates) if end_dates else None

                                            # Separate by activity type
                                            drilling_rows = group_rows[group_rows["Activity Type"] == "drilling"]
                                            earthworks_rows = group_rows[group_rows["Activity Type"] == "earthworks"]

                                            # Get work groups and budgets for each activity type
                                            drill_wg = drilling_rows.iloc[0].get("Work Group", "") if len(drilling_rows) > 0 else ""
                                            drill_budget = drilling_rows["Budget"].sum() if len(drilling_rows) > 0 else 0

                                            ew_wg = earthworks_rows.iloc[0].get("Work Group", "") if len(earthworks_rows) > 0 else ""
                                            ew_budget = earthworks_rows["Budget"].sum() if len(earthworks_rows) > 0 else 0

                                            # Calculate date ranges per activity type
                                            drill_start_dates = [row["Start Date"] for _, row in drilling_rows.iterrows() if isinstance(row["Start Date"], str)]
                                            drill_end_dates = [row["End Date"] for _, row in drilling_rows.iterrows() if isinstance(row["End Date"], str)]
                                            drill_start = min(drill_start_dates) if drill_start_dates else None
                                            drill_end = max(drill_end_dates) if drill_end_dates else None

                                            ew_start_dates = [row["Start Date"] for _, row in earthworks_rows.iterrows() if isinstance(row["Start Date"], str)]
                                            ew_end_dates = [row["End Date"] for _, row in earthworks_rows.iterrows() if isinstance(row["End Date"], str)]
                                            ew_start = min(ew_start_dates) if ew_start_dates else None
                                            ew_end = max(ew_end_dates) if ew_end_dates else None

                                            # Import with correct activity type routing
                                            success = db.save_purpose_budget(
                                                purpose=purpose,
                                                drilling_work_group=drill_wg,
                                                drilling_budget=drill_budget,
                                                drilling_start_date=drill_start,
                                                drilling_end_date=drill_end,
                                                earthworks_work_group=ew_wg,
                                                earthworks_budget=ew_budget,
                                                earthworks_start_date=ew_start,
                                                earthworks_end_date=ew_end,
                                                notes=f"Imported from Gantt ({len(group_rows)} item{'s' if len(group_rows) > 1 else ''})"
                                            )
                                            if success:
                                                import_count += 1

                                        # Import timeline-only purposes (if option selected)
                                        if create_timeline_only and len(skipped_rows) > 0:
                                            for purpose in skipped_rows["Gantt Item"].unique():
                                                # Get all rows for this purpose
                                                purpose_rows = skipped_rows[skipped_rows["Gantt Item"] == purpose]

                                                # Get activity type from first row
                                                activity_type = purpose_rows.iloc[0].get("Activity Type", "drilling") if len(purpose_rows) > 0 else "drilling"

                                                start_dates = [row["Start Date"] for _, row in purpose_rows.iterrows() if isinstance(row["Start Date"], str)]
                                                end_dates = [row["End Date"] for _, row in purpose_rows.iterrows() if isinstance(row["End Date"], str)]
                                                work_group = purpose_rows.iloc[0].get("Work Group", "") if len(purpose_rows) > 0 else ""

                                                min_date = min(start_dates) if start_dates else None
                                                max_date = max(end_dates) if end_dates else None

                                                # Create timeline-only entry with correct activity type routing
                                                if activity_type == "earthworks":
                                                    success = db.save_purpose_budget(
                                                        purpose=purpose,
                                                        earthworks_work_group=work_group,
                                                        earthworks_start_date=min_date,
                                                        earthworks_end_date=max_date,
                                                        notes="Timeline-only (no budget tracking)"
                                                    )
                                                else:  # drilling
                                                    success = db.save_purpose_budget(
                                                        purpose=purpose,
                                                        drilling_work_group=work_group,
                                                        drilling_start_date=min_date,
                                                        drilling_end_date=max_date,
                                                        notes="Timeline-only (no budget tracking)"
                                                    )
                                                if success:
                                                    timeline_only_count += 1

                                        msg = f"✅ Imported {import_count} purpose budgets"
                                        if timeline_only_count > 0:
                                            msg += f" + {timeline_only_count} timeline-only purposes"
                                        st.success(msg + " from Gantt chart.")

                                        if not create_timeline_only and len(skipped_rows) > 0:
                                            st.info(f"ℹ️ {len(skipped_rows)} unmatched items were not imported.")

                                        st.info("Refresh the budget table above to see the new allocations.")
                                        st.rerun()
                            else:
                                st.warning("⚠️ No items have been assigned to purposes. Assign at least one Gantt item to a purpose to import.")
                    except Exception as e:
                        st.error(f"Could not read Gantt file: {e}")

        # ── Rigs ─────────────────────────────────────────────────────────────
        with adm_rigs:
            st.markdown(
                "Configure the **default interval type** for each rig. "
                "This is used in the metres-performance projection so DD rigs "
                "(which drill PQ3/HQ3/NQ3) look up the correct target rather than "
                "the ambiguous 'DD' category."
            )
            _INTERVAL_TYPES = ["RC", "PQ3", "HQ3", "NQ3", "HYD", "DD"]
            rigs_list = db.get_rigs()
            rigs_df = pd.DataFrame([
                {
                    "ID":                   r["id"],
                    "Rig":                  r["short_name"],
                    "Type":                 r["rig_type"],
                    "Default Interval":     r.get("default_interval_type") or "",
                }
                for r in rigs_list
            ])
            edited_rigs = st.data_editor(
                rigs_df,
                column_config={
                    "ID":               st.column_config.NumberColumn("ID", disabled=True),
                    "Rig":              st.column_config.TextColumn("Rig", disabled=True),
                    "Type":             st.column_config.TextColumn("Type", disabled=True),
                    "Default Interval": st.column_config.SelectboxColumn(
                        "Default Interval Type",
                        options=_INTERVAL_TYPES,
                        help="The interval type used for projection target lookup (e.g. PQ3 for a DD rig).",
                    ),
                },
                use_container_width=True,
                hide_index=True,
                key="adm_rigs_editor",
            )
            if st.button("Save Rig Defaults", key="adm_save_rigs"):
                db.save_rig_default_interval_types(
                    dict(zip(edited_rigs["ID"], edited_rigs["Default Interval"]))
                )
                st.success("Rig default interval types saved.")

        # ── Branding ─────────────────────────────────────────────────────────
        with adm_branding:
            st.subheader("App Branding")

            # Logo upload
            st.markdown("**Logo**")
            if logo_path.exists():
                st.image(str(logo_path), width=120)
            logo_file = st.file_uploader("Upload logo (PNG)", type=["png"], key="logo_upload")
            if logo_file:
                logo_path.write_bytes(logo_file.read())
                st.success("Logo saved.")
                st.rerun()
            if logo_path.exists():
                if st.button("Remove logo", key="remove_logo"):
                    logo_path.unlink()
                    st.rerun()

            st.divider()

            # Title / subtitle
            with st.form("branding_form"):
                new_title    = st.text_input("App title",          value=app_title)
                new_subtitle = st.text_input("Subtitle / caption", value=app_subtitle)
                if st.form_submit_button("Save", use_container_width=True):
                    db.set_setting("app_title",    new_title.strip() or "Drill Dashboard")
                    db.set_setting("app_subtitle", new_subtitle.strip())
                    st.success("Branding updated — changes appear on next page reload.")

        # ── Delete PLODs ─────────────────────────────────────────────────────
        with adm_delete:
            st.markdown("Select PLODs to permanently delete. All related data (drilling intervals, time, consumables, equipment, people, cost summary) will be removed.")

            del_rigs    = db.get_rigs()
            del_rig_opts = {"All rigs": None} | {r["short_name"]: r["id"] for r in del_rigs}
            dc1, dc2, dc3 = st.columns(3)
            del_rig_sel  = dc1.selectbox("Filter by rig",  list(del_rig_opts.keys()), key="del_rig_filter")
            del_date_min, del_date_max = db.get_plod_date_bounds()
            del_from = dc2.date_input("From", value=del_date_min, key="del_date_from")
            del_to   = dc3.date_input("To",   value=del_date_max, key="del_date_to")

            plod_list = db.get_plods_list(
                date_from=str(del_from),
                date_to=str(del_to),
                rig_id=del_rig_opts[del_rig_sel],
            )

            if not plod_list:
                st.info("No PLODs found for the selected filters.")
            else:
                del_df = pd.DataFrame(plod_list)
                del_df["label"] = (
                    del_df["plod_ref"].fillna("") + "  |  "
                    + del_df["date"] + "  |  "
                    + del_df["rig"]
                )
                label_to_id = dict(zip(del_df["label"], del_df["id"]))

                selected_labels = st.multiselect(
                    f"Select PLODs to delete ({len(plod_list)} available)",
                    options=del_df["label"].tolist(),
                    key="del_plod_select",
                )

                if selected_labels:
                    preview_ids = [label_to_id[l] for l in selected_labels]
                    preview_df  = del_df[del_df["id"].isin(preview_ids)][
                        ["plod_ref", "date", "rig", "shift", "metres_drilled", "our_total", "coreplan_total"]
                    ].rename(columns={
                        "plod_ref": "PLOD Ref", "date": "Date", "rig": "Rig",
                        "shift": "Shift", "metres_drilled": "Metres",
                        "our_total": "Our Total ($)", "coreplan_total": "CP Total ($)",
                    })
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)
                    st.warning(f"⚠️ This will permanently delete **{len(preview_ids)} PLOD(s)** and all their data.")
                    if st.button("🗑️ Confirm Delete", type="primary", key="del_confirm_btn"):
                        db.delete_plods(preview_ids)
                        st.success(f"Deleted {len(preview_ids)} PLOD(s).")
                        st.rerun()

        # ── Earthworks Equipment Rates ───────────────────────────────────────
        with adm_ew_rates:
            st.markdown(
                "Set **plant rate**, **operator rate**, and **standby rate** (all $/hr) "
                "plus mob/demob costs for each contractor's equipment. "
                "These rates are used to compute costs when importing earthworks CSVs."
            )
            _adm_ew_contractors = db.get_ew_contractors()
            _adm_ew_cont_tabs   = st.tabs([c["name"] for c in _adm_ew_contractors])
            for _adm_ct, _adm_cont in zip(_adm_ew_cont_tabs, _adm_ew_contractors):
                with _adm_ct:
                    _adm_rates = db.get_ew_equipment_rates(_adm_cont["id"])
                    _adm_rate_df = pd.DataFrame(_adm_rates) if _adm_rates else pd.DataFrame(
                        columns=["equipment_name", "plant_rate", "operator_rate",
                                 "standby_rate", "mob_cost", "demob_cost"]
                    )
                    _adm_rate_df_show = _adm_rate_df[
                        ["equipment_name", "plant_rate", "operator_rate",
                         "standby_rate", "mob_cost", "demob_cost"]
                    ] if not _adm_rate_df.empty else _adm_rate_df

                    _edited_ew_rates = st.data_editor(
                        _adm_rate_df_show,
                        column_config={
                            "equipment_name": st.column_config.TextColumn("Equipment"),
                            "plant_rate":     st.column_config.NumberColumn("Plant ($/hr)",    format="$%.2f"),
                            "operator_rate":  st.column_config.NumberColumn("Operator ($/hr)", format="$%.2f"),
                            "standby_rate":   st.column_config.NumberColumn("Standby ($/hr)",  format="$%.2f"),
                            "mob_cost":       st.column_config.NumberColumn("Mob ($)",         format="$%.2f"),
                            "demob_cost":     st.column_config.NumberColumn("Demob ($)",       format="$%.2f"),
                        },
                        use_container_width=True,
                        hide_index=True,
                        num_rows="dynamic",
                        key=f"adm_ew_rates_{_adm_cont['id']}",
                    )
                    if st.button(f"Save {_adm_cont['name']} Rates", key=f"adm_ew_save_{_adm_cont['id']}"):
                        db.set_ew_equipment_rates(
                            _adm_cont["id"],
                            _edited_ew_rates.to_dict("records"),
                        )
                        st.success(f"{_adm_cont['name']} rates saved.")

        # ── OCR Corrections Memory ───────────────────────────────────────────
        with adm_corrections:
            st.markdown(
                "Corrections recorded when reviewers change OCR-extracted values during PLOD import. "
                "These are injected as few-shot examples on future extractions to improve accuracy."
            )
            _corr_rows = db.get_ew_corrections()
            _all_corr  = db.get_all_ew_corrections_raw()
            if not _corr_rows:
                st.info("No corrections recorded yet. Edit OCR values during PLOD import review and save to start building correction memory.")
            else:
                st.caption(f"{len(_all_corr)} total correction(s) across {len(_corr_rows)} unique pattern(s)")
                _corr_df = pd.DataFrame([
                    {
                        "Field":             c["field"],
                        "Equipment":         c.get("equipment_name") or "—",
                        "Extracted (wrong)": c["extracted_value"],
                        "Corrected (right)": c["corrected_value"],
                        "Times seen":        c["times_seen"],
                    }
                    for c in _corr_rows
                ])
                st.dataframe(_corr_df, use_container_width=True, hide_index=True)

                st.divider()
                st.markdown("**Delete a correction pattern**")
                st.caption("Removing a pattern stops it being injected into future extractions. Historical corrections are deleted too.")
                _del_opts = [
                    f"{c['field']} | {c.get('equipment_name') or '—'} | '{c['extracted_value']}' → '{c['corrected_value']}'"
                    for c in _corr_rows
                ]
                _del_sel = st.selectbox("Select pattern to delete", _del_opts, key="adm_corr_del_sel")
                if st.button("Delete pattern", key="adm_corr_del_btn", type="secondary"):
                    _di = _del_opts.index(_del_sel)
                    _dc = _corr_rows[_di]
                    db.delete_ew_correction_pattern(
                        _dc["field"],
                        _dc["extracted_value"],
                        _dc["corrected_value"],
                    )
                    st.success("Pattern deleted.")
                    st.rerun()

        # ── Admin Feedback ───────────────────────────────────────────────────
        with adm_feedback:
            _STATUS_OPTS = ["Open", "In Progress", "Resolved", "Won't Fix"]
            _status_filter = st.selectbox("Filter by status", ["All"] + _STATUS_OPTS, key="adm_fb_filter")
            all_fb = db.get_feedback(None if _status_filter == "All" else _status_filter)
            if not all_fb:
                st.info("No feedback yet.")
            else:
                st.caption(f"{len(all_fb)} submission(s)")
                for fb in all_fb:
                    _badge = {"Open": "🔴", "In Progress": "🟡", "Resolved": "🟢", "Won't Fix": "⚫"}.get(fb["status"], "⚪")
                    with st.expander(
                        f"{_badge} [{fb['category']}] {fb['message'][:60]}{'…' if len(fb['message']) > 60 else ''}"
                        f"  —  {fb['submitted_at'][:16]}  {('— ' + fb['name']) if fb['name'] else ''}",
                        expanded=False,
                    ):
                        st.markdown(f"**Message:** {fb['message']}")
                        if fb.get("auto_response"):
                            st.info(f"**Auto-response:** {fb['auto_response']}")
                        with st.form(f"adm_fb_form_{fb['id']}"):
                            new_status = st.selectbox("Status", _STATUS_OPTS,
                                index=_STATUS_OPTS.index(fb["status"]) if fb["status"] in _STATUS_OPTS else 0,
                                key=f"adm_fb_status_{fb['id']}")
                            admin_resp = st.text_area("Response to user", value=fb.get("admin_response") or "",
                                key=f"adm_fb_resp_{fb['id']}")
                            if st.form_submit_button("Save"):
                                db.update_feedback(fb["id"], new_status, admin_resp)
                                st.success("Saved.")
                                st.rerun()

        # ── Weather Data ────────────────────────────────────────────────────
        with adm_weather:
            st.markdown("**Set up automatic weather data retrieval**")
            current_loc = db.get_location_for_weather()

            location_name = st.text_input(
                "Location/Site Name",
                value=current_loc.get("location", ""),
                placeholder="e.g., Speewah Fluorite Project",
                key="adm_weather_location_name"
            )

            st.markdown("**GPS Coordinates**")
            st.caption("Accept formats: 16°23'51.8\"S (DMS) or -16.3977 (decimal)")

            coord_col1, coord_col2 = st.columns(2)
            with coord_col1:
                latitude_input = st.text_input(
                    "Latitude",
                    value=f"{current_loc.get('latitude', -20.0):.4f}" if current_loc.get("latitude") else "",
                    placeholder="16°23'51.8\"S or -16.3977",
                    key="adm_weather_lat_input"
                )

            with coord_col2:
                longitude_input = st.text_input(
                    "Longitude",
                    value=f"{current_loc.get('longitude', 135.0):.4f}" if current_loc.get("longitude") else "",
                    placeholder="127°58'50.1\"E or 127.9806",
                    key="adm_weather_lon_input"
                )

            st.markdown("**Coverage Buffer**")
            st.info("📍 Weather data applies within 50km radius of the coordinates above")

            if st.button("📌 Save Location", key="adm_save_location"):
                try:
                    db.save_location_for_weather(location_name, latitude_input, longitude_input)
                    # Also save the 50km radius
                    db.set_setting("weather_radius_km", "50")
                    st.success(f"✓ Location saved: {location_name} (50km coverage buffer)")
                except ValueError as e:
                    st.error(f"Invalid coordinates: {e}")

            # Show coverage info if location is set
            if current_loc.get("latitude") and current_loc.get("longitude"):
                st.divider()
                st.markdown("**Current Coverage Area**")
                current_radius = current_loc.get("radius_km", 50)
                st.caption(f"Center: {current_loc['latitude']:.4f}°, {current_loc['longitude']:.4f}° | Radius: {current_radius}km")

                # Calculate and display buffer boundaries
                boundary_points = db.get_coordinates_within_radius(
                    current_loc["latitude"],
                    current_loc["longitude"],
                    current_radius
                )

                # Show as grid of coordinates
                st.text("Buffer boundary (8 cardinal points):")
                boundary_col1, boundary_col2, boundary_col3, boundary_col4 = st.columns(4)

                directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                for idx, (lat, lon) in enumerate(boundary_points):
                    col_idx = idx % 4
                    col = [boundary_col1, boundary_col2, boundary_col3, boundary_col4][col_idx]
                    with col:
                        st.caption(f"{directions[idx]}: {lat:.4f}°, {lon:.4f}°")

            st.divider()
            st.markdown("**Auto-fetch weather data for date range**")
            st.info("Uses Open-Meteo API (free, no authentication needed)")

            fetch_col1, fetch_col2 = st.columns(2)
            with fetch_col1:
                fetch_from = st.date_input("From date", value=date.today() - timedelta(days=30), key="adm_fetch_from_date")
            with fetch_col2:
                fetch_to = st.date_input("To date", value=date.today(), key="adm_fetch_to_date")

            if st.button("⛅ Fetch Weather Data", key="adm_fetch_weather"):
                if not current_loc.get("latitude") or not current_loc.get("longitude"):
                    st.error("Please set location with coordinates first")
                else:
                    try:
                        lat = current_loc["latitude"]
                        lon = current_loc["longitude"]

                        # Check which dates are missing from cache
                        missing_dates = db.get_missing_dates_for_weather(str(fetch_from), str(fetch_to))

                        if not missing_dates:
                            st.info("✓ All dates already cached! No API call needed.")
                        else:
                            with st.spinner(f"Fetching {len(missing_dates)} missing dates from API..."):
                                # Only fetch missing dates (from first missing to last missing)
                                first_missing = min(missing_dates)
                                last_missing = max(missing_dates)

                                st.write(f"🔄 Fetching weather from {first_missing} to {last_missing}")
                                st.write(f"📍 Coordinates: {lat:.4f}°, {lon:.4f}°")

                                # Fetch from API
                                weather_data_range = db.fetch_weather_from_api_range(lat, lon, first_missing, last_missing)

                                if not weather_data_range:
                                    st.error("❌ API returned no data. Please check:")
                                    st.write("- Are the coordinates correct?")
                                    st.write("- Are the dates valid?")
                                    st.write("- Check browser console for any errors")
                                    st.stop()

                                st.write(f"✓ Got {len(weather_data_range)} dates from API")

                                # Save to cache
                                db.save_weather_to_cache(weather_data_range)
                                st.write(f"✓ Saved to cache ({len(weather_data_range)} dates)")

                                # Save to database
                                success_count = 0
                                skipped_count = 0

                                for date_str, weather_data in weather_data_range.items():
                                    existing = db.get_weather_events(date_str, date_str)
                                    if existing:
                                        skipped_count += 1
                                    else:
                                        db.insert_weather_event(
                                            date=date_str,
                                            event_type=weather_data["event_type"],
                                            severity=weather_data.get("severity"),
                                            notes=f"Auto-fetched for {current_loc.get('location', 'site')}"
                                        )
                                        success_count += 1

                                msg = f"✓ Fetched {success_count} new dates (cached for future use)"
                                if skipped_count > 0:
                                    msg += f" ({skipped_count} dates already in database)"
                                st.success(msg)

                        st.rerun()
                    except Exception as e:
                        st.error(f"Error fetching weather: {e}")

        # ── Admin Settings ───────────────────────────────────────────────────
        with adm_settings:
            st.subheader("Anthropic API Key")
            st.markdown(
                "Required for earthworks PLOD scanning. "
                "Generate a key at [console.anthropic.com](https://console.anthropic.com). "
                "Stored securely in the local database."
            )
            with st.form("anthropic_key_form"):
                _cur_key = db.get_ew_setting("anthropic_api_key", "")
                _new_key = st.text_input(
                    "API Key", value=_cur_key,
                    type="password",
                    placeholder="sk-ant-api03-…",
                )
                if st.form_submit_button("Save API Key"):
                    db.set_ew_setting("anthropic_api_key", _new_key.strip())
                    st.success("API key saved.")

            st.divider()
            st.subheader("CorePlan PLOD URL")
            st.markdown("Set the base URL used to build PLOD links in the tracker. The PLOD reference will be appended to this URL.")
            st.caption("Example: `https://app.coreplan.com.au/plods/` — links will become `https://app.coreplan.com.au/plods/6174-250624D`")
            with st.form("plod_url_form"):
                current_url = db.get_setting("plod_base_url", "")
                new_plod_url = st.text_input("PLOD base URL", value=current_url, placeholder="https://app.coreplan.com.au/plods/")
                if st.form_submit_button("Save URL"):
                    db.set_setting("plod_base_url", new_plod_url.strip())
                    st.success("PLOD base URL saved.")

            st.divider()
            st.subheader("Normalise Hole IDs")
            st.markdown(
                "Re-applies the hole ID normalisation rules to every existing record in the database. "
                "Useful for PLODs imported before normalisation was in place. "
                "The original (raw) ID is preserved for reference."
            )
            if st.button("Normalise All Hole IDs", key="normalise_hole_ids"):
                with st.spinner("Scanning and updating…"):
                    changes = ingest.normalise_existing_hole_ids()
                if changes:
                    st.success(f"Updated {len(changes)} unique hole ID(s).")
                    with st.expander("View changes"):
                        for old, new in changes:
                            st.write(f"- `{old}` → `{new}`")
                else:
                    st.info("All hole IDs are already normalised — nothing to update.")

            st.divider()
            st.subheader("Recalculate Cost Summaries")
            st.markdown(
                "Recomputes every PLOD's cost summary using the current rates and rig defaults. "
                "Run this after updating rates or rig interval type mappings."
            )
            if st.button("Recalculate All Summaries", key="recalc_summaries"):
                with st.spinner("Recalculating..."):
                    n = db.recalculate_all_summaries()
                st.success(f"Recalculated {n} PLOD summaries.")

            st.divider()
            st.subheader("Change Admin Password")
            with st.form("change_pw_form"):
                cur_pw  = st.text_input("Current password", type="password")
                new_pw  = st.text_input("New password",     type="password")
                new_pw2 = st.text_input("Confirm new password", type="password")
                if st.form_submit_button("Update Password"):
                    if not db.check_admin_password(cur_pw):
                        st.error("Current password is incorrect.")
                    elif len(new_pw) < 6:
                        st.error("New password must be at least 6 characters.")
                    elif new_pw != new_pw2:
                        st.error("Passwords do not match.")
                    else:
                        db.set_admin_password(new_pw)
                        st.success("Password updated. You will need to log in again.")
                        st.session_state.admin_authenticated = False
                        st.rerun()


    st.divider()

# ---------------------------------------------------------------------------
# Utility formatters
# ---------------------------------------------------------------------------

def fmt_money(val):
    if val is None:
        return "-"
    return f"${val:,.2f}"


def fmt_pct(val):
    if val is None:
        return "-"
    return f"{val:+.1f}%"


def style_variance(val):
    if val is None:
        return ""
    if abs(val) < 2:
        return "color: green"
    return "color: red; font-weight: bold"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _timeline_filter(key: str, show_rig: bool = True):
    """
    Renders a rig selector (optional) + preset buttons + date-range slider.
    Returns (date_from, date_to, rig_id).
    """
    today     = date.today()
    min_date, max_date = db.get_plod_date_bounds()
    # Expand max_date to today so the slider always reaches today
    max_date = max(max_date, today)

    slider_key = f"{key}_slider"
    if slider_key not in st.session_state:
        # Default: from the first PLOD ever imported through to today
        st.session_state[slider_key] = (min_date, today)

    rig_id = None
    if show_rig:
        rig_sel = st.selectbox("Rig", list(rig_opts.keys()), key=f"{key}_rig")
        rig_id  = rig_opts[rig_sel]

    _wtd_start = today - timedelta(days=today.weekday())  # Monday of current week
    presets = {
        "7D":  (today - timedelta(days=7),       today),
        "30D": (today - timedelta(days=30),      today),
        "WTD": (_wtd_start,                      today),
        "MTD": (today.replace(day=1),            today),
        "90D": (today - timedelta(days=90),      today),
        "YTD": (today.replace(month=1, day=1),   today),
        "All": (min_date,                        max_date),
    }
    btn_cols = st.columns(len(presets))
    for col, (label, (pfrom, pto)) in zip(btn_cols, presets.items()):
        if col.button(label, key=f"{key}_preset_{label}", use_container_width=True):
            st.session_state[slider_key] = (
                max(pfrom, min_date),
                min(pto,   max_date),
            )
            st.rerun()

    # Guard against min == max (only one day of data)
    if min_date == max_date:
        st.session_state[slider_key] = (min_date, max_date)
        date_from = date_to = min_date
    else:
        date_from, date_to = st.slider(
            "Date range",
            min_value=min_date,
            max_value=max_date,
            format="DD MMM YYYY",
            key=slider_key,
            label_visibility="collapsed",
        )

    st.caption(f"**{date_from.strftime('%d %b %Y')}** → **{date_to.strftime('%d %b %Y')}**")
    return date_from, date_to, rig_id


def _show_import_results(results):
    ok       = [r for r in results if r.get("status") == "ok"]
    replaced = [r for r in results if r.get("status") == "replaced"]
    skipped  = [r for r in results if r.get("status") == "skipped"]
    errors   = [r for r in results if r.get("status") == "error"]

    if ok or replaced:
        all_imported = ok + replaced
        msg = []
        if ok:
            msg.append(f"{len(ok)} new")
        if replaced:
            msg.append(f"{len(replaced)} replaced")
        st.success(f"Imported {', '.join(msg)} PLOD(s)")
        df = pd.DataFrame(all_imported)[["plod_ref", "date", "rig", "metres",
                                         "our_total", "cp_total", "variance", "variance_pct"]]
        df["our_total"]    = df["our_total"].apply(fmt_money)
        df["cp_total"]     = df["cp_total"].apply(fmt_money)
        df["variance"]     = df["variance"].apply(fmt_money)
        df["variance_pct"] = df["variance_pct"].apply(fmt_pct)
        df["metres"]       = df["metres"].apply(lambda v: f"{v:.1f} m")
        st.dataframe(df, use_container_width=True)

        # Check for missing budget rates in the newly imported data
        st.divider()
        st.markdown("**⚠️ Check: Missing Budget Rates**")
        missing_rates = db.get_missing_budget_rates()
        if missing_rates:
            missing_df = pd.DataFrame(missing_rates)
            st.warning(
                f"🔴 **{len(missing_df)} drill type + hole type combination(s) have no budget rate configured**\n\n"
                f"Budget tracking will not work for these combinations. "
                f"Go to **Admin → Budget** to add the missing rates."
            )
            st.dataframe(
                missing_df,
                column_config={
                    "drill_type": st.column_config.TextColumn("Drill Type", width="medium"),
                    "hole_type": st.column_config.TextColumn("Hole Type", width="medium"),
                    "metres": st.column_config.NumberColumn("Metres Drilled", format="%.1f m"),
                },
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("✓ All drill type + hole type combinations have budget rates configured!")

    # Hole ID renames across all successful imports
    all_renames = [
        (r["plod_ref"], old, new)
        for r in (ok + replaced)
        for old, new in (r.get("hole_renames") or [])
    ]
    if all_renames:
        with st.expander(f"🔁 {len(all_renames)} hole ID(s) normalised"):
            for plod_ref, old, new in all_renames:
                st.write(f"- **{plod_ref}**: `{old}` → `{new}`")

    if skipped:
        with st.expander(f"{len(skipped)} already imported (skipped)"):
            for r in skipped:
                st.write(f"- {r['message']}")

    if errors:
        st.error(f"{len(errors)} file(s) failed")
        for r in errors:
            st.write(f"- {Path(r['file']).name}: {r['message']}")


# ---------------------------------------------------------------------------
# Top-level navigation tabs
# ---------------------------------------------------------------------------
tab_dash, tab_tracker, tab_gantt, tab_import, tab_explorer, tab_gw, tab_ew_dash, tab_ew_tracker, tab_ew_import, tab_fuel, tab_feedback = st.tabs([
    "📊 Tivan Dashboard",
    "📋 Tivan Tracker",
    "📅 Gantt Chart",
    "📂 Import PLODs",
    "🔍 Data Explorer",
    "💧 Groundwater",
    "🚜 EW Dashboard",
    "🚜 EW Tracker",
    "📂 EW Import",
    "⛽ Fuel Tracker",
    "💬 Feedback",
])


# ===========================================================================
# DASHBOARD
# ===========================================================================
with tab_dash:
    st.subheader("Tivan Dashboard")
    date_from, date_to, rig_id = _timeline_filter("dash", show_rig=True)

    # Independent filters for Purpose, Hole Type, and Drill Type
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    # Get available values from database
    all_purposes = sorted(db.get_all_purposes()) if db.get_all_purposes() else []
    _HOLE_TYPES_FILTER = ["RCRD", "DDGT", "DMET", "REXP", "STER", "RCAG", "DDRD"]
    _DRILL_TYPES_FILTER = ["RC", "HQ3", "PQ3"]

    with filter_col1:
        selected_purposes = st.multiselect(
            "Filter by Purpose",
            ["All"] + all_purposes,
            default="All",
            key="dash_purpose_filter"
        )
    with filter_col2:
        selected_hole_types = st.multiselect(
            "Filter by Hole Type",
            ["All"] + _HOLE_TYPES_FILTER,
            default="All",
            key="dash_hole_type_filter"
        )
    with filter_col3:
        selected_drill_types = st.multiselect(
            "Filter by Drill Type",
            ["All"] + _DRILL_TYPES_FILTER,
            default="All",
            key="dash_drill_type_filter"
        )

    st.divider()

    # Build budget lookup (needed by multiple sections below)
    _budget_targets = db.get_budget_targets()

    def _budget_rate(drill_type, hole_type):
        """Look up budget rate by drill type and hole type."""
        return _budget_targets.get(drill_type, {}).get(hole_type, 0.0)

    # Get data with all filters applied
    purpose_arg = None if "All" in selected_purposes else selected_purposes
    rows = db.get_daily_summary(str(date_from), str(date_to), rig_id, purpose=purpose_arg)

    if not rows:
        st.info("No data for the selected filters. Import some PLODs first.")
    else:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])

        # Add hole_type and drill_type for filtering (extracted from hole_name and interval_type)
        # Note: interval_type is already in the data, need to extract hole_type from hole_name if available
        if "hole_name" in df.columns:
            df["hole_type"] = df["hole_name"].str[5:9]  # Extract characters 5-8 (0-indexed)
        else:
            df["hole_type"] = ""

        if "interval_type" in df.columns:
            df["drill_type"] = df["interval_type"]
        else:
            df["drill_type"] = ""

        # Apply Hole Type filter
        if "All" not in selected_hole_types and selected_hole_types:
            df = df[df["hole_type"].isin(selected_hole_types)]

        # Apply Drill Type filter
        if "All" not in selected_drill_types and selected_drill_types:
            df = df[df["drill_type"].isin(selected_drill_types)]

            if df.empty:
                st.info("No data matches the selected filters.")
            else:
                total_our   = df["our_total"].sum()
                total_cp    = df["coreplan_total"].sum()
                total_m     = df["metres_drilled"].sum()
                total_var   = total_our - total_cp
                total_var_p = (total_var / total_cp * 100) if total_cp else 0
                cost_per_m  = (total_our / total_m) if total_m else 0

                k1, k2, k3, k4, k5 = st.columns(5)
                k1.metric("Our Total Cost",  fmt_money(total_our))
                k2.metric("CorePlan Total",  fmt_money(total_cp))
                k3.metric("Variance",        fmt_money(total_var), delta=fmt_pct(total_var_p))
                k4.metric("Metres Drilled",  f"{total_m:,.1f} m")
                k5.metric("Cost / Metre",    fmt_money(cost_per_m))

                st.divider()

                # Get daily metres broken down by hole type + drill type for accurate budget line
                _daily_pt = db.get_daily_metres_by_purpose_type(str(date_from), str(date_to), rig_id)
                _daily_budget_map: dict = {}
                for _r in _daily_pt:
                    _d = _r["date"]
                    # Look up budget rate using hole_type and interval_type (drill_type)
                    rate = _budget_rate(_r["interval_type"], _r["hole_type"])
                    _daily_budget_map[_d] = _daily_budget_map.get(_d, 0.0) + (
                        (_r["total_m"] or 0.0) * rate
                    )

                # Aggregate actual per day, then join with purpose-aware budget
                df_cum = (
                    df.groupby("date", as_index=False)
                    .agg(daily_actual=("our_total", "sum"))
                    .sort_values("date")
                )
                df_cum["date_str"] = df_cum["date"].dt.strftime("%Y-%m-%d")
                df_cum["daily_budget"] = df_cum["date_str"].map(
                    lambda d: _daily_budget_map.get(d, 0.0)
                )
                df_cum["cum_actual"] = df_cum["daily_actual"].cumsum()
                df_cum["cum_budget"] = df_cum["daily_budget"].cumsum()

                fig_cum = go.Figure()
                fig_cum.add_trace(go.Scatter(
                    x=df_cum["date"], y=df_cum["cum_actual"],
                    name="Actual", mode="lines+markers",
                    line=dict(width=2),
                ))
                fig_cum.add_trace(go.Scatter(
                    x=df_cum["date"], y=df_cum["cum_budget"],
                    name="Budget", mode="lines",
                    line=dict(width=2, dash="dash"),
                ))
                fig_cum.update_layout(
                    title="Cumulative Cost Over Time",
                    xaxis_title="Date", yaxis_title="Cumulative Cost ($)",
                    yaxis_tickformat="$,.0f", height=380,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                    margin=dict(b=80, r=150),
                )
                st.plotly_chart(fig_cum, use_container_width=True)

                cost_cols   = ["our_drilling_cost", "our_time_cost", "our_equipment_cost",
                               "our_consumables", "our_accommodation"]
                cost_labels = {
                    "our_drilling_cost":  "Drilling",
                    "our_time_cost":      "Time Activities",
                    "our_equipment_cost": "Equipment",
                    "our_consumables":    "Consumables",
                    "our_accommodation":  "Accommodation",
                }
                df_melt = df.melt(id_vars=["date", "rig"], value_vars=cost_cols,
                                  var_name="cost_type", value_name="cost")
                df_melt["cost_type"] = df_melt["cost_type"].map(cost_labels)

                for rig_name in sorted(df_melt["rig"].unique()):
                    rig_melt = df_melt[df_melt["rig"] == rig_name]
                    fig_bar = px.bar(
                        rig_melt, x="date", y="cost", color="cost_type",
                        title=f"Cost per Shift by Category — {rig_name}",
                        labels={"cost": "Cost ($)", "date": "Date", "cost_type": "Category"},
                    )
                    fig_bar.update_layout(
                        yaxis_tickformat="$,.0f", height=350,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                        margin=dict(b=80, r=150),
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

        # ── Activity Hours per Shift with Weather Events ──────────────────────
        st.divider()
        st.markdown("**Activity Hours per Shift & Weather Events**")
        st.caption("Hover over bar segments to see detailed activity breakdown")

        # Get detailed activity breakdown
        activity_detail = db.get_activity_breakdown_by_date(str(date_from), str(date_to), rig_id)

        if activity_detail:
            # Get weather events for the date range
            weather_map = db.get_weather_summary_by_date(str(date_from), str(date_to))

            activity_df = pd.DataFrame(activity_detail)
            activity_df["date"] = pd.to_datetime(activity_df["date"])
            activity_df["date_str"] = activity_df["date"].dt.strftime("%Y-%m-%d")

            # Define color scheme for broad categories
            category_colors = {
                "Drilling": "#1f77b4",
                "Active Rate": "#2E86AB",
                "Inactive Rate": "#A23B72",
                "Standby": "#F18F01",
                "Weather Standby": "#D72E08",
                "Breakdown": "#C73E1D"
            }

            # Build rig order, preserving sorted unique rigs
            rig_order = sorted(activity_df["rig"].unique())

            if rig_order:
                activity_tabs = st.tabs(rig_order)

                for tab, rig_name in zip(activity_tabs, rig_order):
                    with tab:
                        rig_activity = activity_df[activity_df["rig"] == rig_name].copy()

                        # Create stacked bar chart with hover text showing details
                        fig_activity = px.bar(
                            rig_activity, x="date", y="hours", color="broad_category",
                            title=f"Activity Hours per Shift — {rig_name}",
                            labels={"hours": "Hours", "date": "Date", "broad_category": "Activity Type"},
                            barmode="stack",
                            color_discrete_map=category_colors,
                            custom_data=["detailed_breakdown", "broad_category"]
                        )

                        # Update hover text to show detailed breakdown vertically
                        fig_activity.update_traces(
                            hovertemplate="<b>%{customdata[1]}</b><br>" +
                                         "%{y:.2f} hours<br>" +
                                         "%{customdata[0]}" +
                                         "<extra></extra>"
                        )

                        # Add weather event annotations directly above each bar
                        for date_val in rig_activity["date"].unique():
                            date_str = pd.Timestamp(date_val).strftime("%Y-%m-%d")
                            weather = weather_map.get(date_str)
                            if weather:
                                event_type = weather.get("event_type", "")

                                # Determine symbol for weather events
                                if event_type == "thunderstorm":
                                    symbol = "⚡"
                                elif event_type == "rain":
                                    symbol = "🌧️"
                                elif event_type == "cloudy":
                                    symbol = "☁️"
                                else:
                                    symbol = "☀️"

                                fig_activity.add_annotation(
                                    x=date_val, y=1.08,
                                    yref="paper",
                                    text=symbol, showarrow=False,
                                    font=dict(size=18),
                                    xanchor="center",
                                    yanchor="bottom"
                                )

                        fig_activity.update_layout(
                            yaxis_title="Activity Hours", height=450,
                            margin=dict(b=80, t=120, r=150),
                            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                            hovermode="closest"
                        )
                        st.plotly_chart(fig_activity, use_container_width=True)

        # ── Metres vs Target ─────────────────────────────────────────────────
        metres_targets = db.get_metres_targets()
        plod_type_rows = db.get_plod_metres_by_type(
            str(date_from), str(date_to), rig_id, purpose_arg
        )
        # Build a lookup: short_name → default_interval_type for projection
        _rig_default_itype = {
            r["short_name"]: (r.get("default_interval_type") or r["rig_type"])
            for r in db.get_rigs()
        }

        from collections import defaultdict
        from datetime import date as _date

        # Bucket rows by rig, preserving order of first appearance
        rig_type_rows = defaultdict(list)
        rig_order     = []
        for row in plod_type_rows:
            rig = row["rig"]
            if rig not in rig_order:
                rig_order.append(rig)
            rig_type_rows[rig].append(row)

        if rig_order:
            st.divider()
            st.markdown("**Metres Performance**")
            rig_tabs = st.tabs(rig_order)

            for tab, rig in zip(rig_tabs, rig_order):
                rows_rig = rig_type_rows[rig]
                with tab:
                    # Per-type, per-date aggregation
                    type_actual = defaultdict(lambda: defaultdict(float))
                    type_target = defaultdict(lambda: defaultdict(float))
                    plod_type_m = defaultdict(lambda: defaultdict(float))
                    for row in rows_rig:
                        dt  = row["interval_type"]
                        d   = row["date"]
                        pid = row["plod_id"]
                        type_actual[dt][d]   += row["metres"]
                        type_target[dt][d]   += metres_targets.get(dt, 0.0)
                        plod_type_m[pid][dt] += row["metres"]

                    all_dates_rig = sorted({row["date"] for row in rows_rig})

                    # Projection date range anchored to first/last PLOD for this rig
                    proj_start = _date.fromisoformat(all_dates_rig[0])
                    proj_end   = _date.fromisoformat(all_dates_rig[-1])
                    n_cal_days = (proj_end - proj_start).days + 1
                    proj_dates = [proj_start + timedelta(days=i) for i in range(n_cal_days)]

                    # Cumulative actual
                    cum_vals, running = [], 0.0
                    for d in all_dates_rig:
                        running += sum(type_actual[dt].get(d, 0.0) for dt in type_actual)
                        cum_vals.append(running)

                    # Projection: Calculate weighted average target based on actual drill type mix
                    # For each date, calculate proportion of each drill type and apply weighted target
                    daily_proj_targets = []
                    total_proj_m = 0.0

                    for d in all_dates_rig:
                        # Get metres for each type on this date
                        day_type_metres = {dt: type_actual[dt].get(d, 0.0) for dt in type_actual}
                        total_metres_day = sum(day_type_metres.values())

                        if total_metres_day > 0:
                            # Calculate weighted target: sum(proportion × target) for each type
                            weighted_target = sum(
                                (day_type_metres[dt] / total_metres_day) * metres_targets.get(dt, 0.0)
                                for dt in day_type_metres
                            )
                            daily_proj_targets.append(weighted_target)
                            total_proj_m += weighted_target
                        else:
                            daily_proj_targets.append(0.0)

                    n_shifts = len(plod_type_m)
                    avg_daily_proj = total_proj_m / len(all_dates_rig) if all_dates_rig else 0.0
                    proj_label = (
                        f"Weighted Target ({avg_daily_proj:.1f} m/shift avg)"
                        if avg_daily_proj > 0 else ""
                    )

                    # ── Cumulative chart ──────────────────────────────────────
                    # Build cumulative projection based on daily weighted targets
                    cum_proj = []
                    running_proj = 0.0
                    for proj_val in daily_proj_targets:
                        running_proj += proj_val
                        cum_proj.append(running_proj)

                    fig_cum = go.Figure()
                    fig_cum.add_trace(go.Scatter(
                        x=all_dates_rig, y=cum_vals,
                        name="Actual", mode="lines+markers", line=dict(width=2),
                    ))
                    if cum_proj and proj_label:
                        fig_cum.add_trace(go.Scatter(
                            x=all_dates_rig,
                            y=cum_proj,
                            name=proj_label,
                            mode="lines",
                            line=dict(width=2, color="orange"),
                        ))
                    fig_cum.update_layout(
                        title=f"{rig} — Cumulative Metres vs Shift Projection",
                        xaxis_title="Date", yaxis_title="Metres",
                        yaxis_tickformat=",.0f", height=350,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
            margin=dict(b=80, r=150),
                    )
                    st.plotly_chart(fig_cum, use_container_width=True)

                    # ── Daily chart ───────────────────────────────────────────
                    fig_daily = go.Figure()
                    # Show actual metres stacked by drill type
                    for dt in sorted(type_actual.keys()):
                        act_vals = [type_actual[dt].get(d, 0.0) for d in all_dates_rig]
                        fig_daily.add_trace(go.Bar(
                            x=all_dates_rig, y=act_vals, name=dt,
                        ))

                    # Add single weighted target line
                    fig_daily.add_trace(go.Scatter(
                        x=all_dates_rig, y=daily_proj_targets,
                        name="Weighted Target",
                        mode="lines",
                        line=dict(width=3, color="orange"),
                        yaxis="y"
                    ))

                    fig_daily.update_layout(
                        title=f"{rig} — Metres per Shift vs Weighted Target",
                        xaxis_title="Date", yaxis_title="Metres",
                        barmode="stack",
                        yaxis_tickformat=",.0f", height=350,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
            margin=dict(b=80, r=150),
                    )
                    st.plotly_chart(fig_daily, use_container_width=True)

        # ── Budget vs Actual by Purpose + Drill Type (Tabbed Layout) ──────────
        st.divider()
        st.markdown("**Budget vs Actual — By Hole Type**")

        # Get all drilling data grouped by hole_type and interval_type
        daily_pt = db.get_daily_metres_by_purpose_type(str(date_from), str(date_to), rig_id)

        # Aggregate metres by hole_type + drill_type
        hole_type_actuals: dict = {}  # {hole_type: {drill_type: {metres, cost}}}
        for _r in daily_pt:
            ht = _r["hole_type"]
            dt = _r["interval_type"]

            if ht not in hole_type_actuals:
                hole_type_actuals[ht] = {}
            if dt not in hole_type_actuals[ht]:
                hole_type_actuals[ht][dt] = {"metres": 0.0, "cost": 0.0}

            hole_type_actuals[ht][dt]["metres"] += _r["total_m"] or 0.0

        # Get cost data from cost_summary table and merge by rig + drill_type
        # Note: cost_summary is aggregated at PLOD level, so we get total costs by rig/date
        with db.get_conn() as conn:
            cost_rows = conn.execute(f"""
                SELECT
                    COALESCE(r.default_interval_type, r.rig_type) AS drill_type,
                    SUM(cs.our_total) AS total_cost
                FROM cost_summary cs
                JOIN plods p ON p.id = cs.plod_id
                JOIN rigs r ON r.id = p.rig_id
                WHERE p.date BETWEEN ? AND ?
                {f"AND p.rig_id = ?" if rig_id else ""}
                GROUP BY COALESCE(r.default_interval_type, r.rig_type)
            """,
            (str(date_from), str(date_to), rig_id) if rig_id else (str(date_from), str(date_to))
            ).fetchall()

        # Build cost lookup by drill_type
        cost_by_dt = {row["drill_type"]: row["total_cost"] for row in cost_rows}

        # Distribute costs proportionally to hole types based on their metre share
        for ht in hole_type_actuals:
            for dt in hole_type_actuals[ht]:
                if dt in cost_by_dt:
                    # Get total metres for this drill_type across all hole types
                    total_dt_metres = sum(
                        hole_type_actuals[_ht][dt]["metres"]
                        for _ht in hole_type_actuals
                        if dt in hole_type_actuals[_ht]
                    )
                    # Allocate cost proportionally
                    if total_dt_metres > 0:
                        hole_type_metres = hole_type_actuals[ht][dt]["metres"]
                        hole_type_actuals[ht][dt]["cost"] = (hole_type_metres / total_dt_metres) * cost_by_dt[dt]

        if hole_type_actuals:
            # Mapping of hole type abbreviations to full names
            _HOLE_TYPE_NAMES = {
                "DDRD": "Diamond Drilling Resource Definition",
                "RCRD": "RC Resource Definition",
                "DDGT": "Diamond Drilling Geotech",
                "DMET": "Diamond Drilling Metallurgical",
                "REXP": "RC Exploration",
                "STER": "Sterilisation",
                "RCAG": "RC District 9 Extensional Drilling",
            }

            # Create tabs for each hole type
            hole_type_order = sorted(hole_type_actuals.keys())
            hole_type_tabs = st.tabs(hole_type_order)

            for tab, hole_type in zip(hole_type_tabs, hole_type_order):
                with tab:
                    hole_type_label = _HOLE_TYPE_NAMES.get(hole_type, hole_type)
                    st.subheader(hole_type_label)

                    dt_data = hole_type_actuals[hole_type]
                    drill_types = sorted(dt_data.keys())

                    if drill_types:
                        # Create a clean table layout with compartmentalized cards
                        for dt in drill_types:
                            # Look up budget rate for this (drill_type, hole_type) combination
                            bud_per_m = _budget_rate(dt, hole_type)
                            if bud_per_m == 0:
                                continue

                            act_m = dt_data[dt].get("metres", 0.0)
                            act_cost = dt_data[dt].get("cost", 0.0)
                            # Skip drill types with no metres OR no cost data (incomplete records)
                            if act_m == 0 or act_cost == 0:
                                continue

                            bud_cost = act_m * bud_per_m
                            act_per_m = (act_cost / act_m) if act_m else 0.0
                            variance = act_cost - bud_cost
                            variance_pct = (variance / bud_cost * 100) if bud_cost > 0 else 0

                            # Compartmentalized container for each drill type
                            with st.container(border=True):
                                st.markdown(f"### **Drill Type: {dt}**")

                                col1, col2, col3, col4 = st.columns(4)

                                col1.metric("Metres Drilled", f"{act_m:,.1f} m")
                                col2.metric(
                                    "Budget $/m",
                                    fmt_money(bud_per_m),
                                    delta=f"{act_per_m - bud_per_m:+.2f}" if act_per_m else "No cost data"
                                )
                                col3.metric(
                                    "Actual $/m",
                                    fmt_money(act_per_m) if act_m > 0 else "$0.00"
                                )
                                col4.metric(
                                    "Cost Variance",
                                    fmt_money(variance),
                                    delta=f"{variance_pct:.1f}%" if variance != 0 else "On budget",
                                    delta_color="inverse"
                                )

                                col1_b, col2_b, col3_b = st.columns(3)
                                col1_b.metric("Total Budget", fmt_money(bud_cost))
                                col2_b.metric("Total Actual", fmt_money(act_cost))
                                col3_b.metric(
                                    "Total Variance",
                                    fmt_money(variance),
                                    delta=f"{variance_pct:.1f}%" if variance != 0 else "On budget",
                                    delta_color="inverse"
                                )
                    else:
                        st.info("No drilling data for this category")

        # ── Per-hole charts ───────────────────────────────────────────────────
        slow_thresholds = db.get_slow_thresholds()
        hole_rows = db.get_hole_summary(str(date_from), str(date_to), rig_id)
        if hole_rows:
            st.divider()

            # Calculate actual cost per metre by drill type (from real data)
            actual_cost_per_metre = {}
            drill_type_metres = {}
            drill_type_costs = {}
            for row in hole_rows:
                dt = row.get("interval_type", "")
                if dt:
                    if dt not in drill_type_metres:
                        drill_type_metres[dt] = 0.0
                        drill_type_costs[dt] = 0.0
                    drill_type_metres[dt] += row.get("total_m", 0.0)
                    drill_type_costs[dt] += row.get("drill_cost", 0.0)

            for dt in drill_type_metres:
                if drill_type_metres[dt] > 0:
                    actual_cost_per_metre[dt] = drill_type_costs[dt] / drill_type_metres[dt]

            # Get rig types for each hole
            rig_types = []
            for r in hole_rows:
                # Get rig_type from rigs table based on rig short_name
                rig_type = "Unknown"
                for rig in db.get_rigs():
                    if rig["short_name"] == r["rig"]:
                        rig_type = rig["rig_type"]
                        break
                rig_types.append(rig_type)

            # Separate rows by rig type
            rig_type_groups = {}
            for i, (row, rtype) in enumerate(zip(hole_rows, rig_types)):
                if rtype not in rig_type_groups:
                    rig_type_groups[rtype] = []
                rig_type_groups[rtype].append((i, row))

            # Single selector for drill type (controls both cost and time charts)
            if rig_type_groups:
                st.markdown("**Filter by Rig Type:**")
                selected_rig_type = st.radio(
                    "Rig Type",
                    options=sorted(rig_type_groups.keys()),
                    horizontal=True,
                    label_visibility="collapsed",
                    key="rig_type_selector"
                )

                # Get data for selected rig type
                if selected_rig_type in rig_type_groups:
                    rows_this_type = rig_type_groups[selected_rig_type]

                    # Extract data for selected rig type
                    holes_type = [hole_rows[i]["hole_name"] for i, _ in rows_this_type]
                    costs_type = [hole_rows[i]["drill_cost"] or 0.0 for i, _ in rows_this_type]
                    hours_type = [hole_rows[i]["drill_hours"] or 0.0 for i, _ in rows_this_type]
                    rigs_type = [hole_rows[i]["rig"] for i, _ in rows_this_type]
                    metres_type = [hole_rows[i]["total_m"] or 0.0 for i, _ in rows_this_type]

                    # Calculate cost per metre for each hole
                    cost_per_m_type = []
                    for i, _ in rows_this_type:
                        r = hole_rows[i]
                        metres = r.get("total_m", 0.0)
                        cost = r.get("drill_cost", 0.0)
                        cost_per_m = (cost / metres) if metres > 0 else 0.0
                        cost_per_m_type.append(cost_per_m)

                    # Flag slow holes
                    hole_m_per_hr_type = [
                        (hole_rows[i]["total_m"] / hole_rows[i]["drill_hours"]) if hole_rows[i]["drill_hours"] else 0.0
                        for i, _ in rows_this_type
                    ]
                    slow_flags_type = [
                        threshold > 0 and mhr > 0 and mhr < threshold
                        for mhr, i in zip(hole_m_per_hr_type, [idx for idx, _ in rows_this_type])
                        for threshold in [slow_thresholds.get(hole_rows[i]["interval_type"] or "", 0.0)]
                    ]

                    # ── COST CHART ──
                    st.markdown(f"### Drilling Cost per Hole — {selected_rig_type}")
                    fig_hcost = go.Figure()
                    for rig_name in sorted(set(rigs_type)):
                        idx = [j for j, r in enumerate(rigs_type) if r == rig_name]
                        fig_hcost.add_trace(go.Bar(
                            x=[holes_type[j] for j in idx],
                            y=[costs_type[j] for j in idx],
                            name=rig_name,
                        ))

                    # Add cost per metre labels at top of each bar
                    for hole, cost_per_m in zip(holes_type, cost_per_m_type):
                        if cost_per_m > 0:
                            fig_hcost.add_annotation(
                                x=hole, y=max(costs_type),
                                text=f"${cost_per_m:.0f}/m",
                                showarrow=False,
                                yshift=10,
                                font=dict(size=10, color="darkgreen")
                            )

                    fig_hcost.update_layout(
                        title="",
                        xaxis_title="Hole", yaxis_title="Drill Cost ($)",
                        yaxis_tickformat="$,.0f", barmode="stack", height=350,
                        xaxis_tickangle=-45,
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                        margin=dict(b=80, r=150),
                    )
                    st.plotly_chart(fig_hcost, use_container_width=True)

                    # ── TIME & DEPTH CHART (uses same selected_rig_type) ──
                    st.markdown(f"### Drilling Time & Metres per Hole — {selected_rig_type}")

                    # Calculate m/hr for each hole
                    m_per_hr_type = [
                        (hole_rows[i]["total_m"] / hole_rows[i]["drill_hours"]) if hole_rows[i]["drill_hours"] else 0.0
                        for i, _ in rows_this_type
                    ]

                    # Build time chart
                    fig_htime = go.Figure()
                    for rig_name in sorted(set(rigs_type)):
                        idx = [j for j, r in enumerate(rigs_type) if r == rig_name]
                        fig_htime.add_trace(go.Bar(
                            x=[holes_type[j] for j in idx],
                            y=[hours_type[j] for j in idx],
                            name=rig_name,
                            yaxis="y1",
                        ))

                    # Add m/hr labels at top of each bar
                    for hole, mhr in zip(holes_type, m_per_hr_type):
                        if mhr > 0:
                            fig_htime.add_annotation(
                                x=hole, y=max(hours_type),
                                text=f"{mhr:.1f}m/hr",
                                showarrow=False,
                                yshift=10,
                                font=dict(size=10, color="darkblue")
                            )

                    # Red x-axis labels for slow holes
                    for hole, is_slow in zip(holes_type, slow_flags_type):
                        fig_htime.add_annotation(
                            x=hole, y=0,
                            xref="x", yref="paper",
                            text=hole,
                            showarrow=False,
                            font=dict(color="red" if is_slow else "#444444", size=10),
                            textangle=-45,
                            xanchor="right",
                            yanchor="top",
                            yshift=-6,
                        )

                    fig_htime.update_layout(
                        title="",
                        xaxis=dict(showticklabels=False, title=""),
                        yaxis=dict(title="Drill Hours (h)"),
                        yaxis2=dict(title="Max Depth (m)", overlaying="y", side="right", showgrid=False),
                        barmode="stack", height=380,
                        margin=dict(b=120, r=150),
                        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                    )
                    st.plotly_chart(fig_htime, use_container_width=True)


# ===========================================================================
# TRACKER VIEW
# ===========================================================================
with tab_tracker:
    st.subheader("Tracker View")
    st.caption("One row per PLOD — same column layout as the Excel tracker.")
    st.markdown("""
    <style>
    [data-testid="stDataFrame"] [role="columnheader"] > div {
        white-space: normal !important;
        overflow: visible !important;
        line-height: 1.3;
        word-break: break-word;
    }
    </style>
    """, unsafe_allow_html=True)
    tv_from, tv_to, _ = _timeline_filter("tv", show_rig=False)
    st.divider()

    _TIME_KW  = ("Hours", "(hrs)", "(p/hr)", "(p/day)", " Ori Tool")
    _COUNT_COLS = {"Personnel", "Slow Drilling"}
    _PURPOSES = ["Geotech", "Resource Definition", "Program"]

    def _is_metre_col(col):
        # last "word" ends with m and contains a digit → e.g. "0-50m", "H1 0-50m"
        last = col.split()[-1] if col else ""
        if last == "m" or (last.endswith("m") and any(c.isdigit() for c in last)):
            return True
        if "mm)" in col:
            return True
        return any(kw in col for kw in ("Metres", " From", " To", " Length"))

    def _fmt_hours(val):
        if val is None:
            return "-"
        try:
            return f"{float(val):.2f}"
        except (TypeError, ValueError):
            return "-"

    def _fmt_metres(val):
        if val is None:
            return "-"
        try:
            return str(int(round(float(val))))
        except (TypeError, ValueError):
            return "-"

    def _render_tracker_tab(df: pd.DataFrame, type_label: str):
        if df.empty:
            st.info("No PLODs imported for the selected filters.")
            return

        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        # exclude PLOD ID from formatting
        numeric_cols = [c for c in numeric_cols if c != "PLOD ID"]
        metre_cols = [c for c in numeric_cols if _is_metre_col(c)]
        time_cols  = [c for c in numeric_cols if any(kw in c for kw in _TIME_KW)
                      and c not in metre_cols
                      and "Cost" not in c]
        money_cols = [c for c in numeric_cols
                      if c not in metre_cols and c not in time_cols
                      and c not in _COUNT_COLS]
        fmt_dict   = {c: _fmt_metres for c in metre_cols}
        fmt_dict  |= {c: _fmt_hours  for c in time_cols}
        fmt_dict  |= {c: fmt_money   for c in money_cols}
        if "Variance (%)" in df.columns:
            fmt_dict["Variance (%)"] = fmt_pct

        # Main read-only table (hide PLOD ID + per-hole detail columns)
        # Per-hole detail cols match "H{n} ..." but we keep DD interval cols (PQ/HQ/NQ/BQ)
        import re as _re
        _detail_re  = _re.compile(r"^H\d+ ")
        _keep_re    = _re.compile(r"^H\d+ (PQ|HQ|NQ|BQ)\d* Length$")
        detail_cols = [c for c in df.columns
                       if _detail_re.match(c) and not _keep_re.match(c)]
        # Extract per-row data before dropping columns
        cons_tooltips = df["_cons_tooltip"].tolist() if "_cons_tooltip" in df.columns else []
        plod_refs = df["PLOD Link"].tolist() if "PLOD Link" in df.columns else []
        _SUMMARY_COST_COLS = [
            ("Drilling",     "Charged Drilling Cost"),
            ("Time",         "Total Activity Hours Cost"),
            ("Equipment",    "Total Equipment Cost"),
            ("Consumables",  "Total Consumables"),
            ("Accom",        "Accom Cost"),
            ("Total",        "Total Costs"),
            ("Variance ($)", "Variance ($)"),
            ("Variance (%)", "Variance (%)"),
        ]
        cost_summaries = [
            {
                label: (row[col] if col in df.columns and pd.notna(row[col]) else None)
                for label, col in _SUMMARY_COST_COLS
            }
            for _, row in df.iterrows()
        ]

        display_df = df.drop(columns=["PLOD ID", "_cons_tooltip"] + detail_cols, errors="ignore")

        # Put Date first, then Rig
        _pin_cols = [c for c in ["Date", "Rig"] if c in display_df.columns]
        _rest_cols = [c for c in display_df.columns if c not in _pin_cols]
        display_df = display_df[_pin_cols + _rest_cols]

        # fmt_dict keys must exist in display_df after column drops
        fmt_dict = {k: v for k, v in fmt_dict.items() if k in display_df.columns}
        styled = display_df.style.format(fmt_dict, na_rep="-")
        if "Variance (%)" in display_df.columns:
            styled = styled.map(style_variance, subset=["Variance (%)"])

        # Bold all columns that feed into Total Costs
        _TOTAL_COST_COLS = [
            "Charged Drilling Cost",
            "Total Equipment Cost",
            "Aux Equipment Cost",
            "Azi Aligner Cost",
            "Gyro Cost",
            "Total Activity Hours Cost",
            "Accom Cost",
            "Total Consumables",
            "Consumables On-Charges",
            "Flights",
            "Freight",
            "Total Costs",
            "Operational Cost Per Metre",
        ]
        bold_cols = [c for c in _TOTAL_COST_COLS if c in display_df.columns]
        if bold_cols:
            styled = styled.set_properties(subset=bold_cols, **{"font-weight": "bold"})

        # PLOD Link column — hyperlink if base URL is configured
        plod_base_url = db.get_setting("plod_base_url", "")
        if plod_base_url and "PLOD Link" in display_df.columns:
            display_df["PLOD Link"] = display_df["PLOD Link"].apply(
                lambda ref: f"{plod_base_url.rstrip('/')}/{ref}" if pd.notna(ref) and ref else None
            )

        # Auto-size each column to fit its widest content; freeze Date + Rig
        col_config = {}
        for col in display_df.columns:
            max_data_len = (
                display_df[col].fillna("").astype(str).str.len().max()
                if not display_df.empty else 0
            )
            max_len = max(len(str(col)), max_data_len)
            if max_len <= 8:
                width = "small"
            elif max_len <= 22:
                width = "medium"
            else:
                width = "large"
            pinned = col in ("Date", "Rig")
            col_config[col] = st.column_config.Column(width=width, pinned=pinned)

        if "PLOD Link" in display_df.columns and plod_base_url:
            col_config["PLOD Link"] = st.column_config.LinkColumn(
                "PLOD Link",
                display_text=r"[^/]+$",  # show only the PLOD ref, not the full URL
                width="small",
            )

        selection = st.dataframe(
            styled,
            use_container_width=True,
            height=480,
            column_config=col_config,
            on_select="rerun",
            selection_mode="single-row",
            key=f"tracker_df_{type_label}",
        )

        csv_bytes = display_df.to_csv(index=False).encode()
        st.download_button(
            f"⬇ Download {type_label} CSV",
            csv_bytes,
            f"{type_label.replace(' ', '_')}_tracker.csv",
            "text/csv",
            key=f"dl_tv_{type_label}",
        )

        # PLOD detail panel — shown when a row is selected
        selected_rows = selection.selection.rows if selection else []
        clicked_idx = selected_rows[0] if selected_rows else None

        if clicked_idx is not None and clicked_idx < len(display_df):
            st.divider()
            row_costs = cost_summaries[clicked_idx] if clicked_idx < len(cost_summaries) else {}
            raw_ref   = plod_refs[clicked_idx] if clicked_idx < len(plod_refs) else None

            # Cost summary strip + View PLOD button
            btn_col, c1, c2, c3, c4, c5, c6, c7 = st.columns([1.2, 1, 1, 1, 1, 1, 1.2, 1])
            with btn_col:
                if plod_base_url and raw_ref:
                    st.link_button(
                        "📋 View PLOD",
                        f"{plod_base_url.rstrip('/')}/{raw_ref}",
                        use_container_width=True,
                    )
                elif raw_ref:
                    st.caption(f"PLOD: {raw_ref}")
            _metric_pairs = [
                (c1, "Drilling",    row_costs.get("Drilling")),
                (c2, "Time",        row_costs.get("Time")),
                (c3, "Equipment",   row_costs.get("Equipment")),
                (c4, "Consumables", row_costs.get("Consumables")),
                (c5, "Accom",       row_costs.get("Accom")),
                (c6, "Total",       row_costs.get("Total")),
            ]
            for col, label, val in _metric_pairs:
                with col:
                    st.metric(label, f"${val:,.0f}" if val is not None else "—")
            with c7:
                var_val = row_costs.get("Variance ($)")
                var_pct = row_costs.get("Variance (%)")
                delta_str = f"{var_pct:+.1f}%" if var_pct is not None else None
                st.metric(
                    "Variance",
                    f"${var_val:,.0f}" if var_val is not None else "—",
                    delta=delta_str,
                    delta_color="inverse",
                )

            # Consumables breakdown
            breakdown = cons_tooltips[clicked_idx] if clicked_idx < len(cons_tooltips) else ""
            with st.expander("🧾 Consumables Breakdown", expanded=bool(breakdown)):
                if breakdown:
                    st.code(breakdown, language=None)
                else:
                    st.info("No consumables recorded for this PLOD.")


    # --- Tabs per rig type ---
    active_types = db.get_rig_types_with_plods(str(tv_from), str(tv_to))
    active_rigs_tv = db.get_rigs_with_plods(str(tv_from), str(tv_to))

    if not active_types:
        st.info("No PLODs imported for the selected period.")
    else:
        type_tabs = st.tabs(active_types)
        for tab, rig_type in zip(type_tabs, active_types):
            with tab:
                type_rigs = [r for r in active_rigs_tv if r["rig_type"] == rig_type]

                fc1, fc2 = st.columns(2)
                rig_opts_tv   = ["All Rigs"] + [r["short_name"] for r in type_rigs]
                purp_opts_tv  = ["All"] + _PURPOSES + ["Not Set"]
                rig_filter    = fc1.selectbox("Filter by Rig",     rig_opts_tv,  key=f"tv_rig_{rig_type}")
                purpose_filter= fc2.selectbox("Filter by Purpose", purp_opts_tv, key=f"tv_purp_{rig_type}")

                show_ids = (
                    [r["id"] for r in type_rigs] if rig_filter == "All Rigs"
                    else [r["id"] for r in type_rigs if r["short_name"] == rig_filter]
                )

                if rig_type == "RC":
                    df = tracker_view.build_rc_tracker(show_ids, str(tv_from), str(tv_to))
                elif rig_type == "DD":
                    df = tracker_view.build_dd_tracker(show_ids, str(tv_from), str(tv_to))
                elif rig_type == "HYD":
                    df = tracker_view.build_hyd_tracker(show_ids, str(tv_from), str(tv_to))
                else:
                    df = pd.DataFrame()

                if not df.empty and purpose_filter != "All":
                    if purpose_filter == "Not Set":
                        df = df[df["Purpose"].isna() | (df["Purpose"] == "")]
                    else:
                        df = df[df["Purpose"].str.contains(purpose_filter, na=False)]

                _render_tracker_tab(df, rig_type)


# ===========================================================================
# GANTT CHART - PLANNED vs ACTUAL
# ===========================================================================
with tab_gantt:
    st.subheader("📅 Planned vs Actual Timeline")

    gantt_data = db.get_gantt_timeline_data()

    if not gantt_data:
        st.info("No timeline data available. Import budget allocations and PLODs to see the Gantt chart.")
    else:
        gantt_df = pd.DataFrame(gantt_data)

        # Create hierarchical labels (Work Group - Purpose - Activity)
        gantt_df["Task"] = (gantt_df["WorkGroup"] + " - " +
                           gantt_df["Purpose"] + " [" + gantt_df["Activity"] + "]")

        # Prepare data for Gantt chart
        gantt_rows = []
        for _, row in gantt_df.iterrows():
            gantt_rows.append({
                "Task": row["Task"],
                "Start": row["Start"],
                "Finish": row["End"],
                "Resource": row["Type"],
                "Duration": row["Duration"],
                "WorkGroup": row["WorkGroup"]
            })

        gantt_prep_df = pd.DataFrame(gantt_rows)

        # Color scheme for Planned vs Actual
        colors_dict = {"Planned": "#4472C4", "Actual": "#70AD47"}

        # Create Gantt chart using plotly figure_factory
        from plotly.figure_factory import create_gantt

        fig = create_gantt(
            gantt_prep_df,
            colors=colors_dict,
            index_col="Resource",
            title="Planned vs Actual Timeline by Work Group & Activity",
        )

        # Update layout for better display
        fig.update_layout(
            hovermode="closest",
            margin=dict(l=350, r=50, t=100, b=50),
            xaxis_title="Date",
            yaxis_title="Work Group - Purpose [Activity Type]",
            height=max(600, len(gantt_prep_df) * 30),
            font=dict(size=10),
            showlegend=True,
        )

        st.plotly_chart(fig, use_container_width=True)

        # Add summary table
        st.divider()
        st.subheader("Timeline Summary")

        summary_rows = []
        for _, row in gantt_df[gantt_df["Type"] == "Planned"].iterrows():
            purpose = row["Purpose"]
            work_group = row["WorkGroup"]
            purpose_data = gantt_df[gantt_df["Purpose"] == purpose]

            planned = purpose_data[purpose_data["Type"] == "Planned"]
            actual = purpose_data[purpose_data["Type"] == "Actual"]

            planned_start = planned["Start"].values[0] if len(planned) > 0 else "—"
            planned_end = planned["End"].values[0] if len(planned) > 0 else "—"
            planned_duration = planned["Duration"].values[0] if len(planned) > 0 else 0

            actual_start = actual["Start"].values[0] if len(actual) > 0 else "—"
            actual_end = actual["End"].values[0] if len(actual) > 0 else "—"
            actual_duration = actual["Duration"].values[0] if len(actual) > 0 else 0

            # Calculate variance
            if isinstance(planned_start, str) and isinstance(actual_start, str):
                try:
                    from datetime import datetime
                    ps = datetime.strptime(planned_start, "%Y-%m-%d")
                    ap = datetime.strptime(actual_start, "%Y-%m-%d")
                    start_variance = (ap - ps).days
                except:
                    start_variance = None
            else:
                start_variance = None

            summary_rows.append({
                "Work Group": work_group,
                "Purpose": purpose,
                "Planned Start": planned_start,
                "Actual Start": actual_start,
                "Start Variance": f"{start_variance:+d} days" if start_variance is not None else "—",
                "Planned End": planned_end,
                "Actual End": actual_end,
                "Planned Duration (days)": int(planned_duration) if planned_duration > 0 else "—",
                "Actual Duration (days)": int(actual_duration) if actual_duration > 0 else "—",
            })

        # Remove duplicates (in case there are multiple work group assignments)
        summary_df_list = []
        seen = set()
        for row in summary_rows:
            key = (row["Work Group"], row["Purpose"])
            if key not in seen:
                summary_df_list.append(row)
                seen.add(key)

        summary_df = pd.DataFrame(summary_df_list)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Add insights
        st.divider()
        st.subheader("📊 Insights")

        # Calculate some statistics
        early_starts = []
        late_starts = []
        completed = []
        not_started = []

        for purpose in gantt_df["Purpose"].unique():
            purpose_data = gantt_df[gantt_df["Purpose"] == purpose]
            planned = purpose_data[purpose_data["Type"] == "Planned"]
            actual = purpose_data[purpose_data["Type"] == "Actual"]

            if len(planned) > 0 and len(actual) > 0:
                try:
                    from datetime import datetime
                    ps = datetime.strptime(planned["Start"].values[0], "%Y-%m-%d")
                    ap = datetime.strptime(actual["Start"].values[0], "%Y-%m-%d")
                    variance = (ap - ps).days

                    if variance < 0:
                        early_starts.append((purpose, abs(variance)))
                    elif variance > 0:
                        late_starts.append((purpose, variance))

                    completed.append(purpose)
                except:
                    pass
            elif len(planned) > 0 and len(actual) == 0:
                not_started.append(purpose)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Purposes", len(gantt_df["Purpose"].unique()))

        with col2:
            st.metric("Started", len(completed))

        with col3:
            st.metric("Not Yet Started", len(not_started))

        with col4:
            st.metric("Early/Late Starts", len(early_starts) + len(late_starts))

        if early_starts:
            st.success(f"**Started Early:** {', '.join([f'{p} ({d} days)' for p, d in early_starts[:3]])}")
            if len(early_starts) > 3:
                st.caption(f"... and {len(early_starts) - 3} more")

        if late_starts:
            st.warning(f"**Started Late:** {', '.join([f'{p} ({d} days)' for p, d in late_starts[:3]])}")
            if len(late_starts) > 3:
                st.caption(f"... and {len(late_starts) - 3} more")

        if not_started:
            st.info(f"**Not Yet Started:** {', '.join(not_started[:5])}")
            if len(not_started) > 5:
                st.caption(f"... and {len(not_started) - 5} more")


# ===========================================================================
# IMPORT PLODs
# ===========================================================================
with tab_import:
    st.subheader("Import PLOD Files")

    # --- Rig selector (required before importing) ---
    all_rigs = db.get_rigs()
    rig_types = sorted({r["rig_type"] for r in all_rigs})

    imp_c1, imp_c2 = st.columns(2)
    with imp_c1:
        imp_rig_type = st.selectbox("Drill type", rig_types, key="imp_rig_type")
    with imp_c2:
        type_rigs = [r for r in all_rigs if r["rig_type"] == imp_rig_type]
        imp_rig_sel = st.selectbox(
            "Rig / Contract",
            type_rigs,
            format_func=lambda r: f"{r['short_name']}  —  {r['contract'] or r['name']}",
            key="imp_rig_sel",
        )

    selected_rig_id = imp_rig_sel["id"] if imp_rig_sel else None
    st.caption(f"PLODs will be imported against **{imp_rig_sel['short_name']}** and its rate sheet.")
    st.divider()

    # Session state for the conflict-confirmation flow
    if "imp_pending_paths" not in st.session_state:
        st.session_state.imp_pending_paths    = []   # list of Path strings awaiting import
        st.session_state.imp_conflicts        = []   # list of (filename, plod_ref) conflicts
        st.session_state.imp_pending_rig_id   = None
        st.session_state.imp_cleanup          = False  # True = tmp copies (upload tab), False = folder
        st.session_state.imp_results          = None # results to display after import

    def _run_import(paths: list[Path], rig_id, force_refs: set, cleanup: bool = False):
        """Import a list of paths; force-replace refs in force_refs.
        Set cleanup=True only for tmp copies (upload tab) — never for folder imports."""
        results  = []
        progress = st.progress(0)
        for i, p in enumerate(paths):
            ref   = ingest.peek_plod_ref(p)
            force = ref in force_refs
            results.append(ingest.import_plod(p, rig_id=rig_id, force=force))
            if cleanup:
                p.unlink(missing_ok=True)
            progress.progress((i + 1) / len(paths))
        st.session_state.imp_pending_paths  = []
        st.session_state.imp_conflicts      = []
        st.session_state.imp_pending_rig_id = None
        st.session_state.imp_cleanup        = False
        st.session_state.imp_results        = results

    # ── Conflict dialog ──────────────────────────────────────────────────────
    if st.session_state.imp_conflicts:
        conflicts = st.session_state.imp_conflicts
        pending   = [Path(p) for p in st.session_state.imp_pending_paths]
        rig_id    = st.session_state.imp_pending_rig_id
        cleanup   = st.session_state.imp_cleanup

        st.warning(
            f"**{len(conflicts)} file(s) already exist in the database.**\n\n"
            "The following PLODs are already imported:\n" +
            "".join(f"\n- **{ref}** — `{fname}`" for fname, ref in conflicts)
        )
        st.markdown("Do you want to replace the existing records?")
        col_skip, col_replace, col_cancel, _ = st.columns([1.4, 1.4, 1, 4])
        with col_skip:
            if st.button("Skip Existing", type="secondary", use_container_width=True):
                _run_import(pending, rig_id, force_refs=set(), cleanup=cleanup)
                st.rerun()
        with col_replace:
            if st.button("Replace All", type="primary", use_container_width=True):
                _run_import(pending, rig_id, force_refs={ref for _, ref in conflicts}, cleanup=cleanup)
                st.rerun()
        with col_cancel:
            if st.button("Cancel", type="secondary", use_container_width=True):
                if cleanup:
                    for p in pending:
                        p.unlink(missing_ok=True)
                st.session_state.imp_pending_paths  = []
                st.session_state.imp_conflicts      = []
                st.session_state.imp_pending_rig_id = None
                st.session_state.imp_cleanup        = False
                st.rerun()
        st.stop()

    # ── Show results from last import ────────────────────────────────────────
    if st.session_state.imp_results is not None:
        _show_import_results(st.session_state.imp_results)
        st.session_state.imp_results = None

    imp_tab1, imp_tab2 = st.tabs(["Upload Files", "Import Folder"])

    with imp_tab1:
        uploaded = st.file_uploader(
            "Select PLOD CSV files", type="csv", accept_multiple_files=True
        )
        if uploaded and st.button("Import Selected Files"):
            tmp_dir = Path(__file__).parent / "tmp_import"
            tmp_dir.mkdir(exist_ok=True)
            # Save files to tmp and scan for conflicts
            paths, conflicts = [], []
            for uf in uploaded:
                tmp = tmp_dir / uf.name
                tmp.write_bytes(uf.read())
                ref = ingest.peek_plod_ref(tmp)
                paths.append(str(tmp))
                if ref and db.get_plod_exists(ref):
                    conflicts.append((uf.name, ref))
            if conflicts:
                st.session_state.imp_pending_paths  = paths
                st.session_state.imp_conflicts      = conflicts
                st.session_state.imp_pending_rig_id = selected_rig_id
                st.session_state.imp_cleanup        = True
                st.rerun()
            else:
                _run_import([Path(p) for p in paths], selected_rig_id, force_refs=set(), cleanup=True)
                st.rerun()

    with imp_tab2:
        folder_path = st.text_input(
            "Folder path (paste the path to your PLOD folder)",
            placeholder=r"H:\My Drive\drill-tracker\August",
        )
        if folder_path and st.button("Import All CSVs in Folder"):
            folder = Path(folder_path)
            if not folder.exists():
                st.error(f"Folder not found: {folder_path}")
            else:
                csv_files = sorted(folder.glob("*.csv"))
                if not csv_files:
                    st.warning("No CSV files found in that folder.")
                else:
                    # Scan for conflicts (files stay in-place, no tmp copy needed)
                    conflicts = []
                    for f in csv_files:
                        ref = ingest.peek_plod_ref(f)
                        if ref and db.get_plod_exists(ref):
                            conflicts.append((f.name, ref))
                    if conflicts:
                        st.session_state.imp_pending_paths  = [str(f) for f in csv_files]
                        st.session_state.imp_conflicts      = conflicts
                        st.session_state.imp_pending_rig_id = selected_rig_id
                        st.rerun()
                    else:
                        _run_import(csv_files, selected_rig_id, force_refs=set())
                        st.rerun()


# ===========================================================================
# DATA EXPLORER
# ===========================================================================
with tab_explorer:
    st.subheader("Data Explorer")
    de_from, de_to, de_rig_id = _timeline_filter("de", show_rig=True)
    st.divider()

    exp_tab, hole_tab, time_tab, cons_tab = st.tabs([
        "Holes by Day", "Hole Summary", "Time Breakdown", "Consumables"
    ])

    with exp_tab:
        rows = db.get_daily_summary(str(de_from), str(de_to), de_rig_id)
        if rows:
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            df_valid = df[df["metres_drilled"] > 0].copy()
            if not df_valid.empty:
                df_valid["cost_per_m"] = df_valid["our_total"] / df_valid["metres_drilled"]
                fig = px.line(df_valid, x="date", y="cost_per_m", color="rig",
                              title="Cost per Metre Trend", markers=True,
                              labels={"cost_per_m": "$/m", "date": "Date"})
                fig.update_layout(yaxis_tickformat="$,.0f")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No data for selected filters.")

    with hole_tab:
        hole_rows = db.get_hole_summary(str(de_from), str(de_to), de_rig_id)
        if hole_rows:
            df_h = pd.DataFrame(hole_rows)
            st.dataframe(df_h, use_container_width=True)
            fig_h = px.bar(df_h, x="hole_name", y="total_m", color="rig",
                           title="Metres per Hole", labels={"total_m": "Metres", "hole_name": "Hole"})
            st.plotly_chart(fig_h, use_container_width=True)
        else:
            st.info("No drilling interval data for selected filters.")

    with time_tab:
        where_parts = ["p.date BETWEEN ? AND ?"]
        params = [str(de_from), str(de_to)]
        if de_rig_id:
            where_parts.append("p.rig_id = ?")
            params.append(de_rig_id)
        where_sql = " AND ".join(where_parts)

        with db.get_conn() as conn:
            t_rows = conn.execute(
                f"SELECT tb.category, tb.duration_h, tb.rate_cp, tb.cost_cp, "
                f"p.date, ri.short_name as rig "
                f"FROM time_breakdown tb "
                f"JOIN plods p ON tb.plod_id=p.id "
                f"JOIN rigs ri ON p.rig_id=ri.id "
                f"WHERE {where_sql} ORDER BY p.date",
                params,
            ).fetchall()

        if t_rows:
            df_t = pd.DataFrame([dict(r) for r in t_rows])
            agg = (df_t.groupby("category")
                   .agg(total_hours=("duration_h", "sum"), total_cost=("cost_cp", "sum"))
                   .reset_index().sort_values("total_cost", ascending=False))
            agg["total_cost"]  = agg["total_cost"].apply(fmt_money)
            agg["total_hours"] = agg["total_hours"].apply(lambda v: f"{v:.2f} h")
            st.dataframe(agg, use_container_width=True)
            fig_t = px.pie(df_t, values="duration_h", names="category",
                           title="Time Distribution by Category (hours)")
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.info("No time breakdown data for selected filters.")

    with cons_tab:
        where_parts = ["p.date BETWEEN ? AND ?"]
        params = [str(de_from), str(de_to)]
        if de_rig_id:
            where_parts.append("p.rig_id = ?")
            params.append(de_rig_id)
        where_sql = " AND ".join(where_parts)

        with db.get_conn() as conn:
            c_rows = conn.execute(
                f"SELECT c.item_name, c.quantity, c.unit, c.cost_total, "
                f"p.date, ri.short_name as rig "
                f"FROM consumables c "
                f"JOIN plods p ON c.plod_id=p.id "
                f"JOIN rigs ri ON p.rig_id=ri.id "
                f"WHERE {where_sql} ORDER BY p.date",
                params,
            ).fetchall()

        if c_rows:
            df_c = pd.DataFrame([dict(r) for r in c_rows])
            agg_c = (df_c.groupby(["item_name", "unit"])
                     .agg(total_qty=("quantity", "sum"), total_cost=("cost_total", "sum"))
                     .reset_index().sort_values("total_cost", ascending=False))
            agg_c["total_cost"] = agg_c["total_cost"].apply(fmt_money)
            st.dataframe(agg_c, use_container_width=True)
        else:
            st.info("No consumables data for selected filters.")

# ===========================================================================
# GROUNDWATER EXPORT
# ===========================================================================
with tab_gw:
    st.subheader("Groundwater Intersections")
    st.caption("Parsed from PLOD notes. Filter, preview, and download as CSV.")

    gw_min, gw_max = db.get_plod_date_bounds()
    gc1, gc2, gc3 = st.columns(3)
    gw_from = gc1.date_input("From", value=gw_min, key="gw_from")
    gw_to   = gc2.date_input("To",   value=gw_max, key="gw_to")
    gw_rigs = db.get_rigs()
    gw_rig_opts = {"All rigs": None} | {r["short_name"]: r["id"] for r in gw_rigs}
    gw_rig_sel  = gc3.selectbox("Rig", list(gw_rig_opts.keys()), key="gw_rig")

    with db.get_conn() as conn:
        gw_rows = conn.execute(
            "SELECT p.date, r.short_name as rig, p.plod_ref, p.notes "
            "FROM plods p JOIN rigs r ON p.rig_id = r.id "
            "WHERE p.date BETWEEN ? AND ? "
            + ("AND p.rig_id = ? " if gw_rig_opts[gw_rig_sel] else "")
            + "AND p.notes IS NOT NULL AND p.notes != '' "
            "ORDER BY p.date, r.short_name",
            ([str(gw_from), str(gw_to)] + ([gw_rig_opts[gw_rig_sel]] if gw_rig_opts[gw_rig_sel] else [])),
        ).fetchall()

    if not gw_rows:
        st.info("No PLOD notes found for the selected filters.")
    else:
        gw_records = []
        for row in gw_rows:
            pairs = tracker_view._parse_groundwater_pairs(row["notes"] or "")
            for hole, depth in pairs:
                gw_records.append({
                    "Date":     row["date"],
                    "Rig":      row["rig"],
                    "PLOD Ref": row["plod_ref"],
                    "Hole ID":  hole,
                    "GW (m)":   depth,
                })

        if not gw_records:
            st.info("No groundwater intersections found in notes for the selected period.")
        else:
            gw_df = pd.DataFrame(gw_records)
            st.dataframe(gw_df, use_container_width=True, hide_index=True)
            st.caption(f"{len(gw_df)} groundwater intersections across {gw_df['PLOD Ref'].nunique()} PLODs.")
            st.download_button(
                "⬇ Download Groundwater CSV",
                gw_df.to_csv(index=False).encode(),
                f"groundwater_{gw_from}_{gw_to}.csv",
                "text/csv",
                key="gw_download",
            )

# ===========================================================================
# FUEL TRACKER (placeholder)
# ===========================================================================
with tab_fuel:
    st.subheader("⛽ Fuel Tracker")
    st.info("Coming soon — fuel usage tracking across all plant and equipment.")

# ===========================================================================
# FEEDBACK
# ===========================================================================
with tab_feedback:
    st.subheader("Feedback")
    st.markdown("Found a bug, want a new feature, or have a question? Let us know below.")

    with st.form("feedback_form", clear_on_submit=True):
        fb_name     = st.text_input("Your name (optional)")
        fb_category = st.selectbox("Category", ["Bug", "Feature Request", "Question", "Other"])
        fb_message  = st.text_area("Message", height=120)
        submitted   = st.form_submit_button("Submit Feedback", type="primary")

    if submitted:
        if not fb_message.strip():
            st.warning("Please enter a message before submitting.")
        else:
            db.insert_feedback(fb_name.strip(), fb_category, fb_message.strip())
            st.success("Thanks — your feedback has been logged and the team will review it.")

    st.divider()
    st.markdown("##### Previous submissions")
    _all_fb = db.get_feedback()
    if not _all_fb:
        st.caption("No feedback submitted yet.")
    else:
        for _fb in _all_fb:
            _badge = {"Open": "🔴", "In Progress": "🟡", "Resolved": "🟢", "Won't Fix": "⚫"}.get(_fb["status"], "⚪")
            with st.expander(
                f"{_badge} [{_fb['category']}] {_fb['message'][:70]}{'…' if len(_fb['message']) > 70 else ''}"
                f"  —  {_fb['submitted_at'][:16]}  {('— ' + _fb['name']) if _fb['name'] else ''}",
                expanded=False,
            ):
                st.markdown(f"**Message:** {_fb['message']}")
                if _fb.get("admin_response"):
                    st.success(f"**Team response:** {_fb['admin_response']}")


# ===========================================================================
# EARTHWORKS DASHBOARD
# ===========================================================================
with tab_ew_dash:
    st.subheader("Earthworks Dashboard")

    _ew_contractors   = db.get_ew_contractors()
    _ew_cont_opts     = {"All contractors": None} | {c["name"]: c["id"] for c in _ew_contractors}
    _ew_show_hist     = st.checkbox("Include historical data (2025)", value=True, key="ew_dash_hist")

    ew_c1, ew_c2, ew_c3 = st.columns(3)
    with ew_c1:
        ew_date_from = st.date_input("From", value=date(2025, 5, 1), key="ew_dash_from")
    with ew_c2:
        ew_date_to   = st.date_input("To",   value=date.today(),    key="ew_dash_to")
    with ew_c3:
        ew_cont_sel  = st.selectbox("Contractor", list(_ew_cont_opts.keys()), key="ew_dash_cont")
    ew_cont_id = _ew_cont_opts[ew_cont_sel]

    ew_daily  = db.get_ew_daily_summary(str(ew_date_from), str(ew_date_to),
                                        ew_cont_id, include_historical=_ew_show_hist)
    ew_entries = db.get_ew_entries(str(ew_date_from), str(ew_date_to),
                                   ew_cont_id, include_historical=_ew_show_hist)
    ew_pads   = db.get_ew_pads(str(ew_date_from), str(ew_date_to))

    if not ew_daily:
        st.info("No earthworks data for the selected period. Import data in the EW Import tab.")
    else:
        ew_df  = pd.DataFrame(ew_daily)
        ew_df["date"] = pd.to_datetime(ew_df["date"])

        total_ew_cost   = ew_df["total_cost"].sum()
        total_ew_active = ew_df["active_hours"].sum()
        total_ew_sdown  = ew_df["standdown_hours"].sum()
        total_ew_pads   = ew_df["pads_completed"].sum()
        utilisation_pct = (
            total_ew_active / (total_ew_active + total_ew_sdown) * 100
            if (total_ew_active + total_ew_sdown) > 0 else 0
        )

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Cost",      fmt_money(total_ew_cost))
        k2.metric("Active Hours",    f"{total_ew_active:,.1f} h")
        k3.metric("Standdown Hours", f"{total_ew_sdown:,.1f} h")
        k4.metric("Utilisation",     f"{utilisation_pct:.1f}%")
        k5.metric("Pads Completed",  int(total_ew_pads))

        st.divider()

        # Cumulative cost
        ew_df_cum = ew_df.sort_values("date").copy()
        ew_df_cum["cum_cost"] = ew_df_cum["total_cost"].cumsum()
        fig_ew_cum = go.Figure()
        fig_ew_cum.add_trace(go.Scatter(
            x=ew_df_cum["date"], y=ew_df_cum["cum_cost"],
            name="Cumulative Cost", mode="lines+markers", line=dict(width=2),
        ))
        fig_ew_cum.update_layout(
            title="Cumulative Earthworks Cost",
            xaxis_title="Date", yaxis_title="Cost ($)",
            yaxis_tickformat="$,.0f", height=360,
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
            margin=dict(b=80, r=150),
        )
        st.plotly_chart(fig_ew_cum, use_container_width=True)

        # Daily cost by equipment (stacked bar)
        if ew_entries:
            ew_eq_df = pd.DataFrame(ew_entries)
            ew_eq_df["date"] = pd.to_datetime(ew_eq_df["date"])
            fig_ew_eq = px.bar(
                ew_eq_df, x="date", y="total_cost", color="equipment_name",
                title="Daily Cost per Shift by Equipment",
                labels={"total_cost": "Cost ($)", "date": "Date", "equipment_name": "Equipment"},
                barmode="stack",
            )
            fig_ew_eq.update_layout(
                yaxis_tickformat="$,.0f", height=360,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                margin=dict(b=80, r=150),
            )
            st.plotly_chart(fig_ew_eq, use_container_width=True)

            # Active vs standdown hours stacked bar
            ew_hrs_df = (
                ew_eq_df.groupby("date", as_index=False)
                .agg(active=("active_hours", "sum"), standdown=("standdown_hours", "sum"))
            )
            ew_hrs_melt = ew_hrs_df.melt(
                id_vars="date", value_vars=["active", "standdown"],
                var_name="type", value_name="hours"
            )
            ew_hrs_melt["type"] = ew_hrs_melt["type"].map(
                {"active": "Active", "standdown": "Standdown"}
            )
            fig_ew_hrs = px.bar(
                ew_hrs_melt, x="date", y="hours", color="type",
                title="Daily Hours per Shift — Active vs Standdown",
                labels={"hours": "Hours", "date": "Date", "type": ""},
                barmode="stack",
                color_discrete_map={"Active": "#2ecc71", "Standdown": "#e74c3c"},
            )
            fig_ew_hrs.update_layout(
                height=320,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                margin=dict(b=80, r=150),
            )
            st.plotly_chart(fig_ew_hrs, use_container_width=True)

        # Pads per day
        if total_ew_pads > 0:
            fig_pads = px.bar(
                ew_df[ew_df["pads_completed"] > 0], x="date", y="pads_completed",
                title="Pads Completed per Shift",
                labels={"pads_completed": "Pads", "date": "Date"},
            )
            fig_pads.update_layout(
                height=300,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                margin=dict(b=80, r=150),
            )
            st.plotly_chart(fig_pads, use_container_width=True)


# ===========================================================================
# EARTHWORKS TRACKER
# ===========================================================================
with tab_ew_tracker:
    st.subheader("Earthworks Tracker")

    _ew_tr_contractors = db.get_ew_contractors()
    _ew_tr_cont_opts   = {"All contractors": None} | {c["name"]: c["id"] for c in _ew_tr_contractors}
    _ew_tr_show_hist   = st.checkbox("Include historical data (2025)", value=True, key="ew_tr_hist")

    tr_c1, tr_c2, tr_c3 = st.columns(3)
    with tr_c1:
        ew_tr_from = st.date_input("From", value=date(2025, 5, 1), key="ew_tr_from")
    with tr_c2:
        ew_tr_to   = st.date_input("To",   value=date.today(),    key="ew_tr_to")
    with tr_c3:
        ew_tr_cont = st.selectbox("Contractor", list(_ew_tr_cont_opts.keys()), key="ew_tr_cont")
    ew_tr_cont_id = _ew_tr_cont_opts[ew_tr_cont]

    ew_tr_entries = db.get_ew_entries(str(ew_tr_from), str(ew_tr_to),
                                      ew_tr_cont_id, include_historical=_ew_tr_show_hist)
    ew_tr_pads    = db.get_ew_pads(str(ew_tr_from), str(ew_tr_to))

    if not ew_tr_entries:
        st.info("No data for the selected filters.")
    else:
        # Daily summary table (left side)
        ew_tr_df = pd.DataFrame(ew_tr_entries)
        ew_tr_pads_df = pd.DataFrame(ew_tr_pads) if ew_tr_pads else pd.DataFrame()

        # Group pad IDs per date
        pads_by_date: dict = {}
        if not ew_tr_pads_df.empty:
            for _, pr in ew_tr_pads_df.iterrows():
                pads_by_date.setdefault(pr["date"], []).append(pr["pad_id"])

        left_col, right_col = st.columns([2, 1])

        with left_col:
            st.markdown("**Daily Equipment Log**")
            display_cols = ["date", "contractor", "equipment_name", "active_hours",
                            "standdown_hours", "mob_cost", "total_cost", "notes"]
            col_labels   = {
                "date":             "Date",
                "contractor":       "Contractor",
                "equipment_name":   "Equipment",
                "active_hours":     "Active (h)",
                "standdown_hours":  "Standdown (h)",
                "mob_cost":         "Mob/Demob ($)",
                "total_cost":       "Total Cost ($)",
                "notes":            "Notes",
            }
            ew_show_df = ew_tr_df[display_cols].rename(columns=col_labels).copy()
            ew_show_df["Date"] = pd.to_datetime(ew_show_df["Date"]).dt.strftime("%d/%m/%Y")
            ew_show_df["Total Cost ($)"]    = ew_show_df["Total Cost ($)"].map(lambda v: f"${v:,.2f}")
            ew_show_df["Mob/Demob ($)"]     = ew_show_df["Mob/Demob ($)"].map(lambda v: f"${v:,.2f}" if v else "")
            st.dataframe(ew_show_df, use_container_width=True, hide_index=True)

        with right_col:
            st.markdown("**Pads Tracker**")
            if ew_tr_pads_df.empty:
                st.caption("No pads logged for this period.")
            else:
                pad_summary = []
                for d, ids in sorted(pads_by_date.items()):
                    pad_summary.append({
                        "Date":  pd.to_datetime(d).strftime("%d/%m/%Y"),
                        "Count": len(ids),
                        "Pad IDs": ", ".join(ids),
                    })
                st.dataframe(pd.DataFrame(pad_summary), use_container_width=True, hide_index=True)
                st.metric("Total Pads", sum(len(v) for v in pads_by_date.values()))


# ===========================================================================
# EARTHWORKS IMPORT
# ===========================================================================
with tab_ew_import:
    st.subheader("Import Earthworks Data")

    import ew_ocr

    _ew_imp_contractors = db.get_ew_contractors()
    _ew_imp_cont_map    = {c["name"]: c["id"] for c in _ew_imp_contractors}

    # ── OCR PLOD Import ──────────────────────────────────────────────────────
    st.markdown("### Scan / PDF Import")
    st.markdown(
        "Upload one or more handwritten PLOD PDFs or images. "
        "Claude will extract the data and flag anything unclear for your review before saving."
    )

    _api_key = db.get_ew_setting("anthropic_api_key", "")
    if not _api_key:
        st.warning(
            "No Anthropic API key configured. "
            "Go to **Admin → Settings** and enter your key under 'Anthropic API Key'."
        )

    _ocr_files = st.file_uploader(
        "Upload PLOD PDFs or images",
        type=["pdf", "jpg", "jpeg", "png"],
        accept_multiple_files=True,
        key="ew_ocr_upload",
    )
    _ocr_is_hist = st.checkbox(
        "Mark as historical data (can be cleared separately)",
        value=False, key="ew_ocr_hist"
    )
    _ocr_contractor = st.selectbox(
        "Contractor (if not readable from form)",
        list(_ew_imp_cont_map.keys()),
        key="ew_ocr_contractor",
    )

    # Session state keys for OCR review flow
    for _sk, _default in [
        ("ew_ocr_results",    None),
        ("ew_ocr_originals",  None),
        ("ew_ocr_review_idx", 0),
        ("ew_ocr_file_bytes", {}),
    ]:
        if _sk not in st.session_state:
            st.session_state[_sk] = _default

    if _ocr_files and _api_key:
        if st.button("Extract from PLODs", type="primary", key="ew_ocr_run"):
            import tempfile
            _tmp_dir = Path(tempfile.mkdtemp())
            _paths = []
            for _uf in _ocr_files:
                _p = _tmp_dir / _uf.name
                _p.write_bytes(_uf.read())
                _paths.append(_p)

            _prog = st.progress(0, text="Extracting…")

            def _cb(i, total, name):
                _prog.progress((i + 1) / total, text=f"Processing {name} ({i+1}/{total})")

            _stored_corrections = db.get_ew_corrections()
            _correction_str     = ew_ocr.build_correction_examples(_stored_corrections)
            _results, _file_bytes = ew_ocr.batch_extract(
                _paths, _api_key,
                progress_callback=_cb,
                correction_examples=_correction_str,
            )
            _prog.empty()

            # Attach contractor fallback
            for _r in _results:
                if not _r.get("contractor"):
                    _r["contractor"] = _ocr_contractor
                _r["_is_historical"] = int(_ocr_is_hist)

            import copy
            st.session_state["ew_ocr_results"]    = _results
            st.session_state["ew_ocr_originals"]  = copy.deepcopy(_results)
            st.session_state["ew_ocr_file_bytes"] = _file_bytes
            st.session_state["ew_ocr_review_idx"] = 0
            st.rerun()

    # ── Review form ──────────────────────────────────────────────────────────
    if st.session_state.get("ew_ocr_results"):
        _results    = st.session_state["ew_ocr_results"]
        _rev_idx    = st.session_state["ew_ocr_review_idx"]
        _total      = len(_results)

        st.divider()
        st.markdown(f"### Review Extracted PLODs — {_rev_idx + 1} of {_total}")

        _nav_c1, _nav_c2, _nav_c3 = st.columns([1, 4, 1])
        if _nav_c1.button("← Previous", disabled=_rev_idx == 0, key="ocr_prev"):
            st.session_state["ew_ocr_review_idx"] -= 1
            st.rerun()
        if _nav_c3.button("Next →", disabled=_rev_idx >= _total - 1, key="ocr_next"):
            st.session_state["ew_ocr_review_idx"] += 1
            st.rerun()

        _r = _results[_rev_idx]

        if _r.get("error"):
            st.error(f"Extraction failed for **{_r.get('_source_file', '')}**: {_r['error']}")
            if _r.get("raw_response"):
                with st.expander("Raw response"):
                    st.text(_r["raw_response"])
        else:
            _flags      = {f["field"]: f for f in _r.get("flags", [])}
            _src_file   = _r.get("_source_file", "")
            _src_bytes  = st.session_state["ew_ocr_file_bytes"].get(_src_file, b"")

            def _show_flag(flag: dict):
                """Render flag caption + inline snippet if bbox available."""
                st.caption(
                    f"⚠️ {flag['issue']}  (confidence: {flag.get('confidence', 0):.0%})"
                )
                _snip, _snip_err = ew_ocr.get_flag_snippet(_src_bytes, _src_file, flag)
                if _snip:
                    st.image(_snip, width=320)
                elif _snip_err:
                    st.caption(f"📷 Snippet unavailable: {_snip_err}")

            def _flag_note(field):
                f = _flags.get(field)
                if f:
                    _show_flag(f)

            st.caption(f"Source: **{_src_file}**")

            # ── Header ───────────────────────────────────────────────────────
            with st.container(border=True):
                st.markdown("**Header**")
                hc1, hc2, hc3 = st.columns(3)
                _r["date"] = hc1.text_input(
                    "Date (YYYY-MM-DD)", value=_r.get("date") or "", key=f"ocr_date_{_rev_idx}"
                )
                _flag_note("date")
                _r["supervisor"] = hc2.text_input(
                    "Supervisor", value=_r.get("supervisor") or "", key=f"ocr_sup_{_rev_idx}"
                )
                _r["contractor"] = hc3.selectbox(
                    "Contractor",
                    list(_ew_imp_cont_map.keys()),
                    index=list(_ew_imp_cont_map.keys()).index(_r.get("contractor", _ocr_contractor))
                    if _r.get("contractor") in _ew_imp_cont_map else 0,
                    key=f"ocr_cont_{_rev_idx}",
                )
                hc4, hc5 = st.columns(2)
                _r["start_time"] = hc4.text_input(
                    "Start Time", value=_r.get("start_time") or "", key=f"ocr_st_{_rev_idx}"
                )
                _r["end_time"] = hc5.text_input(
                    "End Time", value=_r.get("end_time") or "", key=f"ocr_et_{_rev_idx}"
                )
                _r["works_description"] = st.text_input(
                    "Works Description", value=_r.get("works_description") or "",
                    key=f"ocr_wd_{_rev_idx}"
                )
                hc6, hc7 = st.columns(2)
                _r["location"] = hc6.text_input(
                    "Location", value=_r.get("location") or "", key=f"ocr_loc_{_rev_idx}"
                )
                _r["area"] = hc7.text_input(
                    "Area", value=_r.get("area") or "", key=f"ocr_area_{_rev_idx}"
                )

            # ── Equipment Hours ───────────────────────────────────────────────
            with st.container(border=True):
                st.markdown("**Equipment Hours & Machine Hours**")
                _equip = _r.get("equipment", [])
                for _ei, _eq in enumerate(_equip):
                    _eq_name = _eq.get("name", f"Equipment {_ei+1}")
                    _has_flag = any(
                        f["field"].startswith(f"equipment.{_eq_name}") or
                        f["field"].startswith(f"equipment[{_ei}]")
                        for f in _r.get("flags", [])
                    )
                    _label = f"⚠️ {_eq_name}" if _has_flag else _eq_name
                    with st.expander(_label, expanded=_has_flag):
                        ec1, ec2, ec3, ec4 = st.columns(4)
                        _eq["active_hours"] = ec1.number_input(
                            "Active (h)", value=float(_eq.get("active_hours") or 0),
                            min_value=0.0, step=0.25, key=f"ocr_act_{_rev_idx}_{_ei}"
                        )
                        _eq["standdown_hours"] = ec2.number_input(
                            "Standdown (h)", value=float(_eq.get("standdown_hours") or 0),
                            min_value=0.0, step=0.25, key=f"ocr_std_{_rev_idx}_{_ei}"
                        )
                        _eq["breakdown_hours"] = ec3.number_input(
                            "Breakdown (h)", value=float(_eq.get("breakdown_hours") or 0),
                            min_value=0.0, step=0.25, key=f"ocr_brk_{_rev_idx}_{_ei}"
                        )
                        _eq["total_hours"] = ec4.number_input(
                            "Total (h)", value=float(_eq.get("total_hours") or 0),
                            min_value=0.0, step=0.25, key=f"ocr_tot_{_rev_idx}_{_ei}"
                        )
                        mc1, mc2 = st.columns(2)
                        _eq["hourmeter_start"] = mc1.number_input(
                            "Hourmeter Start", value=float(_eq.get("hourmeter_start") or 0),
                            min_value=0.0, step=0.1, key=f"ocr_hms_{_rev_idx}_{_ei}"
                        )
                        _eq["hourmeter_end"] = mc2.number_input(
                            "Hourmeter End", value=float(_eq.get("hourmeter_end") or 0),
                            min_value=0.0, step=0.1, key=f"ocr_hme_{_rev_idx}_{_ei}"
                        )
                        _eq["notes"] = st.text_input(
                            "Notes", value=_eq.get("notes") or "",
                            key=f"ocr_enotes_{_rev_idx}_{_ei}"
                        )
                        if _has_flag:
                            for _f in _r.get("flags", []):
                                if (f"equipment.{_eq_name}" in _f["field"] or
                                        f"equipment[{_ei}]" in _f["field"]):
                                    _show_flag(_f)

            # ── Production ───────────────────────────────────────────────────
            with st.container(border=True):
                st.markdown("**Production**")
                _prod = _r.get("production") or {}
                pc1, pc2, pc3, pc4 = st.columns(4)
                _prod["roads_km"]   = pc1.number_input(
                    "Roads (km)", value=float(_prod.get("roads_km") or 0),
                    min_value=0.0, step=0.1, key=f"ocr_rd_{_rev_idx}"
                )
                _prod["tracks_km"]  = pc2.number_input(
                    "Tracks (km)", value=float(_prod.get("tracks_km") or 0),
                    min_value=0.0, step=0.1, key=f"ocr_tr_{_rev_idx}"
                )
                _prod["pads_count"] = pc3.number_input(
                    "Pads (#)", value=int(_prod.get("pads_count") or 0),
                    min_value=0, step=1, key=f"ocr_pd_{_rev_idx}"
                )
                _prod["sumps_pits"] = pc4.number_input(
                    "Sumps/Pits (#)", value=int(_prod.get("sumps_pits") or 0),
                    min_value=0, step=1, key=f"ocr_sp_{_rev_idx}"
                )
                _prod["notes"] = st.text_input(
                    "Production notes", value=_prod.get("notes") or "",
                    key=f"ocr_pnotes_{_rev_idx}"
                )
                _r["production"] = _prod
                _flag_note("production.pads_count")

            # ── Miscellaneous ─────────────────────────────────────────────────
            with st.expander("Miscellaneous items"):
                _misc = _r.get("misc", [])
                for _mi, _m in enumerate(_misc):
                    mc1, mc2, mc3 = st.columns([3, 2, 3])
                    _m["item_name"] = mc1.text_input(
                        "Item", value=_m.get("item_name") or "",
                        key=f"ocr_mitem_{_rev_idx}_{_mi}"
                    )
                    _m["quantity"] = mc2.text_input(
                        "Qty", value=str(_m.get("quantity") or ""),
                        key=f"ocr_mqty_{_rev_idx}_{_mi}"
                    )
                    _m["notes"] = mc3.text_input(
                        "Notes", value=_m.get("notes") or "",
                        key=f"ocr_mnotes_{_rev_idx}_{_mi}"
                    )

            # ── Additional comments ───────────────────────────────────────────
            _r["additional_comments"] = st.text_area(
                "Additional Comments",
                value=_r.get("additional_comments") or "",
                key=f"ocr_ac_{_rev_idx}",
                height=80,
            )

            # ── All flags summary ─────────────────────────────────────────────
            if _r.get("flags"):
                with st.expander(f"⚠️ {len(_r['flags'])} flag(s) from extraction"):
                    for _f in _r["flags"]:
                        st.markdown(
                            f"**{_f['field']}** — {_f['issue']} "
                            f"*(confidence: {_f.get('confidence', 0):.0%})*"
                        )
                        _snip, _snip_err = ew_ocr.get_flag_snippet(_src_bytes, _src_file, _f)
                        if _snip:
                            st.image(_snip, width=400)
                        elif _snip_err:
                            st.caption(f"📷 Snippet unavailable: {_snip_err}")
                        st.divider()

            # ── Save this PLOD ────────────────────────────────────────────────
            if st.button(
                "Save this PLOD to database",
                type="primary",
                key=f"ocr_save_{_rev_idx}",
                disabled=not _r.get("date"),
            ):
                try:
                    # ── Diff: record corrections made during review ───────────
                    _orig = (st.session_state.get("ew_ocr_originals") or [{}])[_rev_idx]
                    _corrections = []
                    _fname = _r.get("_source_file", "")

                    # Header fields
                    for _fld in ["date", "supervisor", "start_time", "end_time",
                                 "works_description", "location", "area"]:
                        _ov, _sv = str(_orig.get(_fld)), str(_r.get(_fld))
                        if _ov != _sv:
                            _corrections.append({
                                "field": _fld,
                                "equipment_name": None,
                                "extracted_value": _orig.get(_fld),
                                "corrected_value": _r.get(_fld),
                                "source_filename": _fname,
                            })

                    # Equipment fields
                    _orig_eq = {e["name"]: e for e in _orig.get("equipment", [])}
                    for _eq in _r.get("equipment", []):
                        _en = _eq["name"]
                        _oeq = _orig_eq.get(_en, {})
                        for _fld in ["active_hours", "standdown_hours", "breakdown_hours",
                                     "total_hours", "hourmeter_start", "hourmeter_end"]:
                            _ov, _sv = str(_oeq.get(_fld)), str(_eq.get(_fld))
                            if _ov != _sv:
                                _corrections.append({
                                    "field": f"equipment.{_en}.{_fld}",
                                    "equipment_name": _en,
                                    "extracted_value": _oeq.get(_fld),
                                    "corrected_value": _eq.get(_fld),
                                    "source_filename": _fname,
                                })

                    # Production fields
                    _op = _orig.get("production") or {}
                    _sp = _r.get("production") or {}
                    for _fld in ["roads_km", "tracks_km", "pads_count", "sumps_pits"]:
                        _ov, _sv = str(_op.get(_fld)), str(_sp.get(_fld))
                        if _ov != _sv:
                            _corrections.append({
                                "field": f"production.{_fld}",
                                "equipment_name": None,
                                "extracted_value": _op.get(_fld),
                                "corrected_value": _sp.get(_fld),
                                "source_filename": _fname,
                            })

                    if _corrections:
                        db.insert_ew_corrections(_corrections)

                    _cont_id = _ew_imp_cont_map.get(_r["contractor"],
                                                    _ew_imp_cont_map.get(_ocr_contractor))
                    _all_rates = db.get_ew_equipment_rates()
                    _rate_map  = {(rr["contractor"], rr["equipment_name"]): rr
                                  for rr in _all_rates}

                    # Save daily header
                    _daily_id = db.insert_ew_daily({
                        "date":               _r["date"],
                        "contractor_id":      _cont_id,
                        "supervisor":         _r.get("supervisor"),
                        "works_description":  _r.get("works_description"),
                        "location":           _r.get("location"),
                        "area":               _r.get("area"),
                        "start_time":         _r.get("start_time"),
                        "end_time":           _r.get("end_time"),
                        "additional_comments": _r.get("additional_comments"),
                        "principal_name":     _r.get("principal_name"),
                        "source_filename":    _r.get("_source_file"),
                        "is_historical":      _r.get("_is_historical", 0),
                    })

                    # Save equipment entries (compute costs from rates)
                    _entries = []
                    for _eq in _r.get("equipment", []):
                        _rate  = _rate_map.get((_r["contractor"], _eq["name"]), {})
                        _act   = float(_eq.get("active_hours") or 0)
                        _std   = float(_eq.get("standdown_hours") or 0)
                        _brk   = float(_eq.get("breakdown_hours") or 0)
                        _tot   = float(_eq.get("total_hours") or (_act + _std + _brk))
                        _pr    = float(_rate.get("plant_rate",    0))
                        _or    = float(_rate.get("operator_rate", 0))
                        _sr    = float(_rate.get("standby_rate",  0))
                        _op_c  = _act * (_pr + _or)
                        _sd_c  = _std * _sr
                        # Check mobilisation
                        _is_mob   = any(
                            m["equipment"].lower() in _eq["name"].lower()
                            for m in _r.get("mobilisations", [])
                        )
                        _is_demob = any(
                            m["equipment"].lower() in _eq["name"].lower()
                            for m in _r.get("demobilisations", [])
                        )
                        _mc = (float(_rate.get("mob_cost",   0)) if _is_mob   else 0) + \
                              (float(_rate.get("demob_cost", 0)) if _is_demob else 0)
                        _entries.append({
                            "daily_id":        _daily_id,
                            "date":            _r["date"],
                            "contractor_id":   _cont_id,
                            "equipment_name":  _eq["name"],
                            "mobilised":       int(_is_mob),
                            "demobilised":     int(_is_demob),
                            "active_hours":    _act,
                            "standdown_hours": _std,
                            "breakdown_hours": _brk,
                            "unavailable_hours": 0,
                            "total_hours":     _tot,
                            "mob_cost":        _mc,
                            "operating_cost":  _op_c,
                            "standdown_cost":  _sd_c,
                            "accommodation":   0,
                            "total_cost":      _op_c + _sd_c + _mc,
                            "hourmeter_start": _eq.get("hourmeter_start") or None,
                            "hourmeter_end":   _eq.get("hourmeter_end") or None,
                            "notes":           _eq.get("notes") or None,
                            "is_historical":   _r.get("_is_historical", 0),
                        })
                    if _entries:
                        db.insert_ew_entries(_entries, replace=True)

                    # Save production
                    db.insert_ew_production(_daily_id, _r.get("production") or {})

                    # Save misc
                    if _r.get("misc"):
                        db.insert_ew_misc_items(_daily_id, _r["misc"])

                    # Save pads
                    _prod = _r.get("production") or {}
                    _pad_count = int(_prod.get("pads_count") or 0)
                    if _pad_count > 0:
                        db.insert_ew_pads([{
                            "date": _r["date"],
                            "contractor_id": _cont_id,
                            "pad_id": f"PAD-TBD-{_r['date']}-{_pi+1}",
                            "notes": None,
                        } for _pi in range(_pad_count)])

                    # Mark as saved in results
                    _r["_saved"] = True
                    st.session_state["ew_ocr_results"][_rev_idx] = _r
                    st.success(f"Saved PLOD for {_r['date']}.")
                    if _rev_idx < _total - 1:
                        st.session_state["ew_ocr_review_idx"] += 1
                    st.rerun()

                except Exception as _save_ex:
                    st.error(f"Save failed: {_save_ex}")

            if _r.get("_saved"):
                st.success("Already saved.")

        # Progress summary
        _saved_count = sum(1 for _x in _results if _x.get("_saved"))
        st.caption(f"{_saved_count}/{_total} PLODs saved to database.")
        if _saved_count == _total:
            if st.button("Clear review queue", key="ocr_clear"):
                st.session_state["ew_ocr_results"] = None
                st.session_state["ew_ocr_review_idx"] = 0
                st.rerun()

    st.divider()
    st.markdown("### CSV Import")
    st.markdown(
        "Alternatively, upload a CSV matching the earthworks template. "
        "Costs are computed automatically from the equipment rates configured in Admin."
    )

    # Download template
    _tmpl_path = Path(__file__).parent / "earthworks_template.csv"
    if _tmpl_path.exists():
        with open(_tmpl_path, "rb") as _tf:
            st.download_button(
                "Download CSV Template",
                data=_tf.read(),
                file_name="earthworks_template.csv",
                mime="text/csv",
            )

    uploaded_ew = st.file_uploader("Upload earthworks CSV", type="csv", key="ew_upload")

    _ew_imp_is_hist = st.checkbox(
        "Mark as historical data (can be cleared separately)",
        value=False, key="ew_imp_hist"
    )
    _ew_imp_replace = st.checkbox(
        "Replace existing entries for same date/contractor/equipment",
        value=False, key="ew_imp_replace"
    )

    if uploaded_ew:
        try:
            ew_raw = pd.read_csv(uploaded_ew)
            ew_raw.columns = [c.strip().lower().replace(" ", "_") for c in ew_raw.columns]

            # Validate required columns
            _req = {"date", "contractor", "equipment", "active_hours"}
            _missing = _req - set(ew_raw.columns)
            if _missing:
                st.error(f"Missing columns: {_missing}")
            else:
                # Load rates for cost calculation
                _all_rates = db.get_ew_equipment_rates()
                _rate_map = {
                    (r["contractor"], r["equipment_name"]): r for r in _all_rates
                }

                entries = []
                pads    = []
                errors  = []

                for i, row in ew_raw.iterrows():
                    contractor = str(row.get("contractor", "")).strip()
                    equipment  = str(row.get("equipment",  "")).strip()
                    if not contractor or not equipment:
                        continue
                    if contractor not in _ew_imp_cont_map:
                        errors.append(f"Row {i+2}: Unknown contractor '{contractor}'")
                        continue

                    cont_id      = _ew_imp_cont_map[contractor]
                    active_h     = float(row.get("active_hours",    0) or 0)
                    standdown_h  = float(row.get("standdown_hours", 0) or 0)
                    unavail_h    = float(row.get("unavailable_hours", 0) or 0)
                    total_h      = active_h + standdown_h + unavail_h
                    mob          = int(bool(row.get("mobilised",   0)))
                    demob        = int(bool(row.get("demobilised", 0)))
                    accommodation = float(row.get("accommodation", 0) or 0)
                    notes        = str(row.get("notes", "") or "").strip() or None

                    # Calculate cost from rates
                    rate = _rate_map.get((contractor, equipment), {})
                    plant_rate    = float(rate.get("plant_rate",    0))
                    op_rate       = float(rate.get("operator_rate", 0))
                    standby_rate  = float(rate.get("standby_rate",  0))
                    mob_cost_unit = float(rate.get("mob_cost",      0))
                    demob_cost_u  = float(rate.get("demob_cost",    0))

                    op_cost       = active_h * (plant_rate + op_rate)
                    sdown_cost    = standdown_h * standby_rate
                    mob_cost_val  = (mob_cost_unit if mob else 0) + (demob_cost_u if demob else 0)
                    total_cost    = op_cost + sdown_cost + mob_cost_val + accommodation

                    try:
                        entry_date = pd.to_datetime(row["date"]).strftime("%Y-%m-%d")
                    except Exception:
                        errors.append(f"Row {i+2}: Invalid date '{row['date']}'")
                        continue

                    entries.append({
                        "date":             entry_date,
                        "contractor_id":    cont_id,
                        "equipment_name":   equipment,
                        "mobilised":        mob,
                        "demobilised":      demob,
                        "active_hours":     active_h,
                        "standdown_hours":  standdown_h,
                        "unavailable_hours": unavail_h,
                        "total_hours":      total_h,
                        "mob_cost":         mob_cost_val,
                        "operating_cost":   op_cost,
                        "standdown_cost":   sdown_cost,
                        "accommodation":    accommodation,
                        "total_cost":       total_cost,
                        "notes":            notes,
                        "is_historical":    int(_ew_imp_is_hist),
                    })

                    # Pads
                    pads_count = int(row.get("pads_completed", 0) or 0)
                    pad_ids_raw = str(row.get("pad_ids", "") or "").strip()
                    pad_id_list = [p.strip() for p in pad_ids_raw.split("|") if p.strip()]
                    if not pad_id_list and pads_count > 0:
                        pad_id_list = [f"PAD-TBD-{entry_date}-{j+1}" for j in range(pads_count)]
                    for pid in pad_id_list:
                        pads.append({
                            "date":         entry_date,
                            "contractor_id": cont_id,
                            "pad_id":       pid,
                            "notes":        None,
                        })

                if errors:
                    for e in errors:
                        st.warning(e)

                if entries:
                    st.markdown(f"**Preview — {len(entries)} equipment entries, {len(pads)} pad records**")
                    prev_df = pd.DataFrame(entries)[
                        ["date", "contractor_id", "equipment_name",
                         "active_hours", "standdown_hours", "total_cost"]
                    ].copy()
                    prev_df["contractor_id"] = prev_df["contractor_id"].map(
                        {v: k for k, v in _ew_imp_cont_map.items()}
                    )
                    prev_df["total_cost"] = prev_df["total_cost"].map(lambda v: f"${v:,.2f}")
                    st.dataframe(prev_df, use_container_width=True, hide_index=True)

                    if st.button("Import Earthworks Data", type="primary", key="ew_do_import"):
                        n = db.insert_ew_entries(entries, replace=_ew_imp_replace)
                        if pads:
                            db.insert_ew_pads(pads)
                        st.success(f"Imported {n} equipment entries and {len(pads)} pad records.")
                        st.rerun()

        except Exception as _ew_ex:
            st.error(f"Error reading file: {_ew_ex}")

    st.divider()
    st.markdown("**Import Historical Data (2025)**")
    st.caption(
        "Upload the 2025 earthworks operations log CSV to populate historical data. "
        "The format is the original spreadsheet export."
    )
    uploaded_hist = st.file_uploader(
        "Upload 2025 operations log CSV", type="csv", key="ew_hist_upload"
    )
    if uploaded_hist:
        try:
            hist_raw = pd.read_csv(uploaded_hist, header=1)
            hist_raw.columns = [str(c).strip() for c in hist_raw.columns]
            # Expected columns from the 2025 spreadsheet
            hist_entries = []
            _mdm_id = _ew_imp_cont_map.get("MDM")

            for i, row in hist_raw.iterrows():
                try:
                    entry_date = pd.to_datetime(row.iloc[0]).strftime("%Y-%m-%d")
                except Exception:
                    continue
                equipment = str(row.iloc[1] if len(row) > 1 else "").strip()
                if not equipment or equipment.lower() in ("nan", ""):
                    continue

                def _safe_float(val):
                    try:
                        return float(str(val).replace("$", "").replace(",", "").strip())
                    except Exception:
                        return 0.0

                mob       = int(bool(str(row.iloc[2]).strip() not in ("", "nan", "0")))
                demob     = int(bool(str(row.iloc[3]).strip() not in ("", "nan", "0")))
                active_h  = _safe_float(row.iloc[4])
                sdown_h   = _safe_float(row.iloc[5])
                total_h   = _safe_float(row.iloc[7])
                mob_cost  = _safe_float(row.iloc[8])
                op_cost   = _safe_float(row.iloc[10])
                sdown_cost= _safe_float(row.iloc[11])
                total_cost= _safe_float(row.iloc[12])
                notes_val = str(row.iloc[14]).strip() if len(row) > 14 else ""
                notes_val = None if notes_val.lower() in ("", "nan") else notes_val
                accomm    = _safe_float(row.iloc[15]) if len(row) > 15 else 0.0

                hist_entries.append({
                    "date":             entry_date,
                    "contractor_id":    _mdm_id,
                    "equipment_name":   equipment,
                    "mobilised":        mob,
                    "demobilised":      demob,
                    "active_hours":     active_h,
                    "standdown_hours":  sdown_h,
                    "unavailable_hours": max(0.0, total_h - active_h - sdown_h),
                    "total_hours":      total_h,
                    "mob_cost":         mob_cost,
                    "operating_cost":   op_cost,
                    "standdown_cost":   sdown_cost,
                    "accommodation":    accomm,
                    "total_cost":       total_cost,
                    "notes":            notes_val,
                    "is_historical":    1,
                })

            if hist_entries:
                st.markdown(f"**{len(hist_entries)} historical entries parsed.**")
                if st.button("Import Historical Data", type="primary", key="ew_hist_do_import"):
                    n = db.insert_ew_entries(hist_entries, replace=True)
                    st.success(f"Imported {n} historical entries.")
                    st.rerun()
            else:
                st.warning("No valid rows found in the file.")
        except Exception as _hex:
            st.error(f"Error reading historical file: {_hex}")

    st.divider()
    if st.session_state.get("admin_authenticated"):
        st.markdown("**Clear Historical Data**")
        st.caption("Removes all entries flagged as historical (2025 demo data).")
        if st.button("Clear Historical Earthworks Data", type="secondary", key="ew_clear_hist"):
            db.delete_ew_historical()
            st.success("Historical earthworks data cleared.")

st.divider()
from datetime import datetime
now = datetime.now()
try:
    tz_name = now.astimezone().tzname()
except:
    tz_name = "Local"
st.markdown(f"""
<div style="text-align: center; padding: 1rem 0; color: #666; font-size: 0.85rem;">
  <strong>Tivan Speewah Tracker</strong> | Last deployed: {now.strftime('%Y-%m-%d %H:%M:%S')} {tz_name}
</div>
""", unsafe_allow_html=True)
