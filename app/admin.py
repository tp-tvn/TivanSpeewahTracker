"""Tivan Admin Panel — Streamlit admin interface (pre-authenticated)."""
import streamlit as st
import pandas as pd
from pathlib import Path

import db
import ingest

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Tivan Admin",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide sidebar toggle + remove default left padding so header sits at the edge
st.markdown("""
<style>
[data-testid="stSidebar"]        { display: none; }
[data-testid="collapsedControl"] { display: none; }
.block-container {
    padding-left:  1.5rem !important;
    padding-right: 1.5rem !important;
    padding-top:   1rem   !important;
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

import os
is_staging = "developer" in os.environ.get("STREAMLIT_SERVER_HEADLESS", "") or \
             "developer" in os.getcwd().lower() or \
             "tivanspeewahtracker-developer" in os.getcwd().lower()
try:
    import subprocess
    current_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                           cwd='app', stderr=subprocess.DEVNULL).decode().strip()
except:
    current_branch = "develop" if is_staging else "main"

if current_branch == "develop":
    st.markdown("""
    <div class="staging-banner">
        🚀 STAGING/DEVELOPER ENVIRONMENT - Changes test here before production
    </div>
    """, unsafe_allow_html=True)

db.init_db()

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
/* ── Number input container ──────────────────────────– */
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

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
logo_path   = Path(__file__).parent / "logo.png"
app_title   = db.get_setting("app_title",    "Tivan Dashboard")

hdr_brand, hdr_theme = st.columns([8, 1])
with hdr_brand:
    if logo_path.exists():
        import base64
        _logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;padding:4px 0">
  <img src="data:image/png;base64,{_logo_b64}" style="height:60px;width:auto"/>
  <div>
    <div style="font-size:1.6rem;font-weight:700;line-height:1.2">⚙️ {app_title} Admin</div>
    <div style="font-size:0.85rem;opacity:0.6">Admin Panel (Pre-Authenticated)</div>
  </div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"## ⚙️ {app_title} Admin")
        st.caption("Admin Panel (Pre-Authenticated)")
with hdr_theme:
    st.write("")
    st.session_state.dark_mode = st.toggle(
        "🌙" if st.session_state.dark_mode else "☀️",
        value=st.session_state.dark_mode,
        help="Toggle dark / light mode",
    )

st.divider()

# ---------------------------------------------------------------------------
# Admin content (always shown, no authentication needed)
# ---------------------------------------------------------------------------
with st.container(border=True):
    st.markdown("#### ⚙️ Admin Panel")
    adm_purposes, adm_rates, adm_budget, adm_rigs, adm_branding, adm_settings, adm_delete, adm_ew_rates, adm_corrections, adm_feedback, adm_weather = st.tabs([
        "Drillhole Information",
        "Rates",
        "Budget",
        "Rigs",
        "Branding",
        "Settings",
        "Delete",
        "Earthworks",
        "Corrections",
        "Feedback",
        "Weather"
    ])

    # ── Drillhole Information ──────────────────────────────────────
    with adm_purposes:
        st.markdown("#### 🔍 Drillhole Information")
        st.caption("Import comprehensive drillhole data from CSV")

        st.markdown("**Import Drillhole Data**")
        st.caption("Upload CSV with columns: Hole number, Hole ID (actual), Hole status, Azimuth (TN), Dip, Target depth, Actual depth, Purpose, Drill Type, Coordinates.Easting, Coordinates.Northing, etc.")

        uploaded_file = st.file_uploader("Choose drillhole CSV file", type="csv", key="adm_drillhole_upload")
        if uploaded_file:
            try:
                df_preview = pd.read_csv(uploaded_file)
                st.dataframe(df_preview, use_container_width=True)
                st.info(f"Preview: {len(df_preview)} drillholes found")

                if st.button("Import Drillhole Data", key="adm_import_drillholes"):
                    uploaded_file.seek(0)
                    imported = db.import_drillholes_csv(uploaded_file)
                    st.success(f"✅ Imported {imported} drillhole records")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

        st.divider()
        st.markdown("**Current Drillhole Records**")

        drillholes = db.get_drillholes()
        if drillholes:
            dh_df = pd.DataFrame(drillholes)
            display_cols = ['hole_number', 'hole_id_actual', 'hole_status', 'azimuth_tn', 'dip',
                          'target_depth', 'actual_depth', 'purpose', 'drill_type', 'prospect', 'pad_id_link']
            available_cols = [c for c in display_cols if c in dh_df.columns]
            st.dataframe(dh_df[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No drillhole records imported yet. Upload a CSV to get started.")

    # Rates Management
    with adm_rates:
        st.markdown("#### 💰 Rate Management")
        st.caption("View and manage rates for all rigs")

        rigs = db.get_rigs()
        if not rigs:
            st.info("No rigs found in database")
        else:
            selected_rig = st.selectbox(
                "Select Rig",
                options=rigs,
                format_func=lambda r: r['name'],
                key="adm_select_rig_for_rates"
            )

            if selected_rig:
                rig_id = selected_rig['id']
                rates = db.get_rates(rig_id=rig_id)

                if rates:
                    rates_df = pd.DataFrame(rates)
                    rates_df = rates_df[['label', 'category', 'rate', 'unit', 'effective_date']]

                    st.subheader(f"Rates for {selected_rig['name']}")
                    st.dataframe(rates_df, use_container_width=True, hide_index=True)

                    st.divider()
                    st.markdown("**Update Rate**")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        rate_label = st.selectbox(
                            "Rate Name",
                            options=[r['label'] for r in rates],
                            key="adm_rate_label_select"
                        )
                    with col2:
                        current_rate = next((r['rate'] for r in rates if r['label'] == rate_label), 0)
                        new_rate = st.number_input(
                            "New Rate",
                            value=float(current_rate),
                            step=0.01,
                            key="adm_new_rate_input"
                        )
                    with col3:
                        st.write("")
                        st.write("")
                        if st.button("Update Rate", key="adm_update_rate_btn"):
                            rate_id = next((r['id'] for r in rates if r['label'] == rate_label), None)
                            if rate_id:
                                db.update_rate(rate_id, new_rate)
                                db.export_rates_csv()
                                st.success(f"✅ Updated {rate_label} to {new_rate}")
                                st.rerun()
                else:
                    st.info(f"No rates found for {selected_rig['name']}")
    with adm_budget:
        st.markdown("#### 📊 Budget Targets")
        st.caption("Set a budget cost per metre by drill type")

        budget_targets = db.get_budget_targets()

        drill_types = ["RC", "HQ3", "PQ3", "NQ3", "HYD"]
        budget_data = []

        for drill_type in drill_types:
            budget_data.append({
                "Drill Type": drill_type,
                "Budget ($/m)": budget_targets.get(drill_type, {}).get(drill_type, 0) if isinstance(budget_targets.get(drill_type), dict) else budget_targets.get(drill_type, 0)
            })

        budget_df = pd.DataFrame(budget_data)
        edited_budget = st.data_editor(
            budget_df,
            column_config={
                "Drill Type": st.column_config.TextColumn("Drill Type", disabled=True),
                "Budget ($/m)": st.column_config.NumberColumn("Budget ($/m)", min_value=0, step=1),
            },
            hide_index=True,
            use_container_width=True,
            key="adm_budget_editor",
        )

        if st.button("Save Budget Targets", key="adm_save_budget"):
            budget_mapping = {}
            for _, row in edited_budget.iterrows():
                drill_type = row["Drill Type"]
                budget_mapping[drill_type] = row["Budget ($/m)"]

            db.set_budget_targets(budget_mapping)
            db.export_budget_targets_csv()
            st.success("✅ Budget targets saved")
            st.rerun()
    with adm_rigs:
        st.info("Rigs management (not included in admin panel)")
    with adm_branding:
        st.info("Branding settings (not included in admin panel)")
    with adm_settings:
        st.markdown("#### ⚙️ Settings & Deployment")

        if current_branch == "develop":
            st.divider()
            st.markdown("**🚀 Deploy to Production**")
            st.caption("Merge changes from staging (develop) to production (main)")

            try:
                git_status = subprocess.check_output(['git', 'status', '--porcelain'],
                                                     cwd='app', stderr=subprocess.DEVNULL).decode().strip()
                git_log = subprocess.check_output(['git', 'log', '--oneline', 'develop..main', '-n', '5'],
                                                 cwd='app', stderr=subprocess.DEVNULL).decode().strip()

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Current Status")
                    if git_status:
                        st.warning(f"⚠️ **{len(git_status.splitlines())} uncommitted changes**")
                        with st.expander("View changes"):
                            st.code(git_status)
                    else:
                        st.success("✅ All changes committed")

                with col2:
                    st.subheader("Commits Ahead")
                    if git_log:
                        commit_count = len(git_log.splitlines())
                        st.info(f"🔄 **{commit_count} commit(s)** ready to push")
                        with st.expander("View commits"):
                            st.code(git_log)
                    else:
                        st.info("📦 No new commits (in sync with production)")

                st.divider()
                st.markdown("**One-click deployment:**")
                col_deploy, col_status = st.columns([2, 1])
                with col_deploy:
                    if st.button("🚀 DEPLOY TO PRODUCTION", use_container_width=True, type="primary"):
                        try:
                            # Stage all changes
                            subprocess.run(['git', 'add', '-A'], cwd='app', check=True, capture_output=True)
                            # Commit if there are changes
                            git_status_check = subprocess.check_output(['git', 'status', '--porcelain'],
                                                                      cwd='app').decode().strip()
                            if git_status_check:
                                subprocess.run(['git', 'commit', '-m', 'Staging deployment - auto-commit'],
                                             cwd='app', check=True, capture_output=True)
                            # Push develop to main
                            subprocess.run(['git', 'push', 'origin', 'develop:main'],
                                         cwd='app', check=True, capture_output=True)
                            st.success("✅ Deployed! Production will update in 30-60 seconds.")
                            st.balloons()
                        except subprocess.CalledProcessError as e:
                            st.error(f"❌ Deployment failed: {e}")

            except subprocess.CalledProcessError:
                st.warning("⚠️ Could not read git status. Ensure you're in a git repository.")
        else:
            st.success("✅ You're on PRODUCTION (main branch) - all changes are live")
    with adm_delete:
        st.info("Delete functions (not included in admin panel)")
    with adm_ew_rates:
        st.info("Earthworks rates (not included in admin panel)")
    with adm_corrections:
        st.info("Corrections (not included in admin panel)")
    with adm_feedback:
        st.info("Feedback (not included in admin panel)")
    with adm_weather:
        st.info("Weather settings (not included in admin panel)")
