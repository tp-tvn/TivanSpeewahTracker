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
</style>
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
        "Holes & Purposes",
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

    # ── Holes & Purposes ────────────────────────────────────────
    with adm_purposes:
        st.markdown("**Import Hole Purposes**")
        st.caption("Upload a CSV with columns: hole_name, purpose, hole_type")
        up_file = st.file_uploader("Choose CSV file", type="csv", key="adm_purpose_upload")
        if up_file:
            try:
                df = pd.read_csv(up_file)
                st.dataframe(df, use_container_width=True)
                if st.button("Import Hole Purposes", key="adm_do_import_purposes"):
                    mapping = {}
                    for _, row in df.iterrows():
                        hole_name = row.get("hole_name")
                        purpose = row.get("purpose")
                        hole_type = row.get("hole_type")
                        if hole_name:
                            mapping[hole_name] = {
                                "purpose": purpose,
                                "hole_type": hole_type
                            }
                    if mapping:
                        db.set_hole_purposes(mapping)
                        st.success(f"✅ Imported {len(mapping)} hole purposes")
                        st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

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
            st.success("✅ Budget targets saved")
            st.rerun()
    with adm_rigs:
        st.info("Rigs management (not included in admin panel)")
    with adm_branding:
        st.info("Branding settings (not included in admin panel)")
    with adm_settings:
        st.info("Settings (not included in admin panel)")
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
