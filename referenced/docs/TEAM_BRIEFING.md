# Tivan Dashboard — Team Briefing
## Comprehensive Guide to the Drill Tracker Tool

---

## 📋 Executive Summary

**Tivan Dashboard** is a Streamlit-based activity tracking and cost management system for drilling projects. It integrates daily drilling operations (PLODs) with project budgets, timelines, and financial reporting to give real-time visibility into project health.

### At a Glance
- **Purpose**: Track drilling activities, manage budgets, forecast costs, and monitor schedule performance
- **Users**: Project managers, drilling supervisors, financial analysts, site coordinators
- **Key Data**: PLODs (daily drilling reports), budget allocations, hole purposes, cost rates
- **Main Outputs**: Budget vs Actual reports, Gantt timelines, activity summaries, cost forecasts

---

## 🎯 Core Capabilities

### 1. **PLOD Ingestion & Validation**
Import daily drilling reports (PLODs) from PDF or manual entry:
- Extracts hole names, depths, drilling intervals, equipment used
- Validates data against known holes and purposes
- Flags anomalies (unusual depths, unknown hole types)
- Calculates cost automatically based on configured rates
- Stores drilling intervals for historical analysis

### 2. **Budget Planning & Gantt Integration**
Connect your project schedule to drilling budgets:
- Import Gantt charts as CSV/Excel
- Map Gantt items to drilling purposes
- Set budget amounts, start/end dates for each period
- Support multiple phases per purpose (different contractors)
- Assign work groups (contractors, teams) to each budget period

### 3. **Budget vs Actual Reporting**
Compare planned vs actual spending in real time:
- Metres drilled vs planned metres
- Actual cost vs budgeted amount (calculated from PLOD data)
- Cost per metre trending
- Variance alerts (warning if overspending or ahead of schedule)
- Filter by purpose, rig, or date range

### 4. **Timeline Analysis (Gantt Charts)**
Visualize planned vs actual project timelines:
- Horizontal bar chart showing planned vs actual drilling dates
- Identify schedule delays and early finishes
- Track progress by purpose or work group
- See which phases overlap and dependencies
- Detailed summary table with start/end variance calculations

### 5. **Historical Analysis & Data Explorer**
Dive deep into drilling data:
- Search PLODs by hole name, purpose, date, or rig
- View drilling interval details (ROP, equipment, consumables)
- Compare performance across holes, rigs, and drilling types
- Identify patterns (which holes take longest, where costs spike)

### 6. **Financial Analytics**
Understand costs and forecasts:
- Cost per metre by drilling type and hole type
- Equipment and consumable expense tracking
- Labour and overhead allocation
- Cash flow forecasts (if budget amounts provided)
- Variance analysis (over/under budget by how much)

### 7. **Admin Features** (Password Protected)
Configure system for your project:
- Set drillhole purposes and planned metres
- Manage budget rates ($/metre for each drill type)
- Import/edit Gantt chart allocations
- Assign work groups to contractors/teams
- Configure rigs and equipment
- Set weather data for efficiency analysis
- Correct OCR errors from PDF imports

---

## 🚀 Quick Start Guide (QRG)

### **First Run: One-Time Setup**

#### Step 1: Define Your Drilling Purposes
**Location**: Admin Panel → 🎯 Drillhole Purposes

1. Click **"🔒 Admin"** in top right, enter admin password
2. Click **"🎯 Drillhole Purposes"** tab
3. **Option A** — Import CSV:
   - Prepare CSV with 2 columns: Hole Name, Purpose (e.g., "RC Resource Definition")
   - Click "Upload planned metres list" or "Upload drillhole purpose list"
   - Select your CSV file → Click Import
4. **Option B** — Manual Entry:
   - Scroll to bottom of page
   - Click on table cells to add/edit hole names and purposes

**Example**:
```
Hole Name    | Purpose
TIVAN-001    | 2026 RC Resource Definition
TIVAN-002    | 2026 RC Resource Definition
MDM-001      | 2026 Diamond Metallurgical
```

#### Step 2: Set Budget Rates
**Location**: Admin → 💰 Rate Management

1. Click **"💰 Rate Management"** tab
2. Look for "Budget Targets" section
3. Set cost rates for each drill type + hole type combo
   - Example: RC drilling × RCRD holes = $150/metre
   - Example: HQ3 drilling × DDGT holes = $250/metre
4. Mark "N/A" for combinations you don't use
5. Save

#### Step 3: Configure Your Rigs
**Location**: Admin → 🔩 Rigs

1. Add rig names (e.g., "RC-001", "Diamond Rig A")
2. Set default drill type for each rig
3. Add hourly rates if tracking equipment costs

#### Step 4: Import Your Gantt Chart (Budget Planning)
**Location**: Admin → 📊 Budget Targets

1. Export your project Gantt chart as CSV or Excel
2. Scroll to "📊 Import from Gantt Chart"
3. Upload your file
4. **Map Gantt items to purposes**:
   - System shows each unique item name
   - You select the corresponding drilling purpose
   - Example: "Tivan Phase 1" → "2026 RC Resource Definition"
5. Assign **Work Groups** (contractors):
   - Click the "Work Group" column to edit
   - Enter contractor/team name (e.g., "Contractor A")
6. Review dates and budgeted amounts
7. Click **"Import Gantt Chart Allocations"** → Saved!

---

### **Daily Operations: Importing PLODs**

#### Import a PLOD
**Location**: Main Dashboard → "Import PLOD"

**Method 1: Upload PDF**
1. Click **"Import PLOD"** button (top of dashboard)
2. Select a PDF file from your drill site
3. System extracts hole names, depths, drilling intervals
4. Review the extracted data
5. Click **"Save PLOD"**

**Method 2: Manual Entry**
1. Click **"Import PLOD"** → **"Manual Entry"**
2. Fill in form:
   - Date of drilling
   - Rig name
   - Hole name (must match a configured hole)
   - Drilling intervals (depth, type, metres)
   - Equipment used, consumables, costs
3. Click **"Save PLOD"**

**What Happens Next**:
- System matches hole name to a purpose (from hole_purposes table)
- Calculates cost: metres × rate for that drill type
- Allocates cost to the correct budget period (by date)
- Updates Budget vs Actual report automatically

---

### **Daily Monitoring: Budget vs Actual**

#### View Your Current Status
**Location**: Main Dashboard → "📊 Budget vs Actual"

This is your **one-page health check**:

| Column | What It Means | Action |
|--------|---------------|--------|
| **Purpose** | Which drilling project | - |
| **Status** | 🟢 On Track / 🟡 Warning / 🔴 Risk | Monitor if at warning/risk |
| **Actual Metres** | Total metres drilled so far | Compare to Planned |
| **Planned Metres** | Target metres for this phase | Set during setup |
| **Actual Cost** | Money spent so far | Compare to Budget |
| **Budget** | Money allocated for this phase | Review if approaching |
| **Variance** | Difference from plan ($, %) | < 0% = under budget ✓ |
| **Cost/Metre** | Actual cost per metre drilled | Track efficiency |

**Interpreting Status**:
- 🟢 **Green** (On Track): Spending and metres match budget, within 10%
- 🟡 **Yellow** (Warning): Approaching budget limit or running ahead/behind metres
- 🔴 **Red** (Risk): Over budget or significantly behind schedule

**If You See Red**:
1. Click the purpose to view details
2. Check recent PLODs for that purpose
3. Review actual costs vs assumed rates (Admin → 💰 Rate Management)
4. Escalate if overspend is expected

---

### **Schedule Tracking: Gantt Chart Tab**

#### View Timeline vs Reality
**Location**: Main Dashboard → "📅 Gantt Chart"

This shows a visual comparison:
- **Blue bars** = Planned timeline (from your Gantt import)
- **Green bars** = Actual drilling (from PLOD data)

**What to Look For**:
- ✓ Green starts near blue = On schedule
- ⚠️ Green starts after blue = Running late
- ⚠️ Green much shorter than blue = Finished early
- ? No green bar = Not yet started

**The Summary Table** shows:
- Purpose name
- Planned start date vs Actual start date
- Start variance (days early/late)
- Planned duration vs Actual duration
- Work group (contractor name)

**Actions to Take**:
- **Late start detected?** → Check with site supervisor
- **Early finish?** → Great! Document why for future planning
- **Not started yet?** → Confirm mobilization date is correct

---

## ❓ Frequently Asked Questions

### **Setup & Configuration**

**Q: How do I know if my Gantt import worked?**
A: Go to Admin → 📊 Budget Targets → scroll down to "Purpose Budget Allocations" table. You should see new rows with dates, budgets, and work groups. Each row is one Gantt item you imported.

**Q: What happens if I upload the same Gantt chart twice?**
A: The system does NOT de-duplicate. You'll get duplicate budget allocations. Solution: Delete old ones in Admin → Budget first, or use the "Delete PLODs" tab to clean up.

**Q: Can I have multiple budget periods for the same purpose?**
A: Yes! Example: "2026 RC" from Jan-Mar (Contractor A), then Apr-Jun (Contractor B), then Jul-Sep (Follow-up). Each period is a separate row in the budget allocations table.

**Q: How do I change a work group after importing?**
A: Go to Admin → 📊 Budget → scroll to "Purpose Budget Allocations" table. Click the Work Group cell and edit directly. Click Save when done.

---

### **PLOD Import & Data**

**Q: What file formats does PDF import support?**
A: Currently PDF only. Manual entry available for other formats (Excel, CSV, handwritten notes). If you have a different format, contact your admin.

**Q: The PDF import missed some drilling data. What went wrong?**
A: PDF extraction uses OCR, which can struggle with:
- Faint text, handwritten entries
- Non-standard table layouts
- Poor image quality
Fix: Use Manual Entry for the missing data, or go to Admin → 🧠 OCR Corrections to train the system.

**Q: Can I edit a PLOD after importing it?**
A: Yes. In Admin → 🗑️ Delete PLODs, find your PLOD and delete it. Then re-import with corrected data. (You cannot edit in place yet.)

**Q: What if a hole doesn't have an assigned purpose?**
A: The PLOD will still import, but won't be allocated to any budget period. Go to Admin → 🎯 Drillhole Purposes and add it to the hole_purposes table.

**Q: Can I import future-dated PLODs?**
A: Yes, but they won't affect budget tracking until that date arrives. Useful for pre-staging planned drilling.

---

### **Budget & Cost Reporting**

**Q: Why does my "Actual Cost" show $0 even though I imported PLODs?**
A: Missing budget rate. Solution:
1. Go to Admin → 💰 Rate Management → Budget Targets
2. Check if the drill_type + hole_type combination has a rate
3. If blank or "N/A", add a rate (e.g., $150/m)
4. Costs recalculate automatically

**Q: How is the actual cost calculated?**
A: `Actual Cost = Sum of (metres drilled × rate for that drill type)`
The system finds the rate in Budget Targets based on the drilling interval type (RC, HQ3, PQ3, etc.) and the hole type (RCRD, DDGT, DMET, etc.).

**Q: Can I override the calculated cost?**
A: Not directly in the dashboard. If you need to adjust, contact admin to manually edit the cost_summary table in the database.

**Q: What if budget runs out before the period ends?**
A: The system will flag as 🔴 Risk. You have options:
1. Increase the budget (edit in Admin → Budget → edit the "drilling_budget" field)
2. Reduce planned metres (contact site supervisor)
3. End the budget period early and create a new one
4. Move work to a different phase/contractor

**Q: When should I start worrying about overspend?**
A: - **80% of budget**: Start monitoring closely
- **90% of budget**: Escalate to project manager
- **100% of budget**: Stop work until approved adjustment

---

### **Timeline & Gantt Chart**

**Q: Why doesn't my Gantt chart show any actual drilling data?**
A: No PLODs have been imported yet, or they're for different purposes. Solution:
1. Check "Budget vs Actual" tab to see if PLODs imported for that purpose
2. Confirm hole names in PLODs match hole_purposes table
3. Confirm purpose names match Gantt import exactly (case-sensitive)

**Q: Can I filter the Gantt chart by contractor?**
A: Not yet in the UI, but you can:
- Look at the summary table and sort by Work Group
- Use Gantt chart zoom to focus on a date range
- Future enhancement: filterable by work group

**Q: What if I have the same purpose with two different contractors?**
A: Show them as separate rows on the Gantt chart:
- "Contractor A - RC Definition" (Jan-Mar)
- "Contractor B - RC Definition" (Apr-Jun)
They appear stacked in the chart and the summary table shows the Work Group column.

**Q: Can I edit dates directly in the Gantt chart?**
A: No. Edit in Admin → 📊 Budget → edit the start_date and end_date columns in the budget allocations table.

**Q: What do the colors mean?**
A: 
- **Blue bars** = Planned (from Gantt import)
- **Green bars** = Actual (from PLOD data)
- **🟢 Green in Insights** = Started early
- **🟡 Yellow in Insights** = Started late
- **🔵 Blue in Insights** = Not yet started

---

### **Admin & Access Control**

**Q: How do I become an admin?**
A: Ask your project manager for the admin password. Click 🔒 Admin in top right, enter password.

**Q: Can there be multiple admins with different passwords?**
A: Currently one password for all admins. Future enhancement: user-level access control.

**Q: What if I forget the admin password?**
A: Contact your IT admin. The password is stored in the database (hashed). No reset link available yet.

**Q: Can I see who made what changes?**
A: Not in the dashboard. For audit trail, check the database directly (database logs not shown in UI). Future feature: change history.

---

### **Data & Performance**

**Q: How much data can the dashboard handle?**
A: Tested with:
- 500+ PLODs (daily reports)
- 50+ purposes
- 1000+ drilling intervals
Loads instantly. Larger datasets may be slower—contact admin if you exceed 1000 PLODs.

**Q: How often does data update?**
A: Real-time. As soon as you click "Save PLOD" or "Import Gantt", the dashboard refreshes.

**Q: Can I export reports?**
A: Download table data as CSV:
1. Click the "⬇️ Download" icon on any table
2. Opens CSV in Excel
Manual copy-paste available for all charts.
Full PDF export coming soon.

**Q: Is my data backed up?**
A: Database is stored locally. Backup frequency depends on your IT setup. Ask your admin about backup schedule. **Recommendation**: Manual backups before major Gantt imports.

---

### **Troubleshooting**

**Q: Dashboard is slow or won't load.**
A: 
1. Refresh the page (Ctrl+R or Cmd+R)
2. Clear browser cache
3. If still slow, check if a large PLOD import is running
4. Contact admin if persists

**Q: "Admin mode" won't activate.**
A: 
1. Double-check password spelling
2. Clear browser cookies
3. Try incognito/private browsing mode
4. Contact admin to verify password is correct

**Q: I see "Database locked" error.**
A: Another user is editing data. Wait 30 seconds and refresh. If persists, contact admin.

**Q: A figure/chart is blank or says "No data".**
A: 
1. Confirm you've imported at least one PLOD
2. Confirm Gantt import was successful (check Admin → Budget table)
3. Check that purpose names match exactly (including capitalization)
4. Refresh the page

**Q: PLOD PDF import failed with "Unable to extract".**
A: PDF might be image-only (no text layer). Solutions:
1. Try manual entry instead
2. Run PDF through OCR software first
3. Contact admin to troubleshoot specific PDF layout

---

## 🔗 Key Tabs & Navigation

### **Main Dashboard** (No Login Required)
- **Overview**: Summary of active purposes, cost alerts
- **📊 Budget vs Actual**: Spending tracker (your main go-to)
- **📅 Gantt Chart**: Timeline visualization
- **🔍 Data Explorer**: Search and filter historical PLODs
- **Import PLOD**: Upload daily reports

### **Admin Panel** (Login Required)
- **🎯 Drillhole Purposes**: Define holes and purposes
- **💰 Rate Management**: Set $/metre rates
- **📊 Budget Targets**: Gantt import, budget allocations
- **🔩 Rigs**: Configure equipment
- **🎨 Branding**: Customize app title/logo
- **🔧 Settings**: App configuration
- **🗑️ Delete PLODs**: Remove incorrect imports
- **🚜 EW Rates**: Equipment/weather settings
- **🧠 OCR Corrections**: Train PDF extraction
- **💬 Feedback**: Send feature requests
- **🌦️ Weather**: Add weather data for analysis

---

## 🎓 Training Scenarios

### **Scenario 1: First Day of a New Project**
1. ✅ Receive hole list from geology team
2. ✅ Define purposes in Admin → 🎯 Drillhole Purposes (upload CSV)
3. ✅ Set budget rates in Admin → 💰 Rate Management
4. ✅ Export project Gantt chart from PMO
5. ✅ Import Gantt in Admin → 📊 Budget Targets
6. ✅ Assign work groups to contractors
7. ✅ First PLOD arrives → Import via "Import PLOD"
8. ✅ Check Budget vs Actual → Should show some spending

### **Scenario 2: Monthly Budget Review**
1. ✅ Open 📊 Budget vs Actual tab
2. ✅ Look at Variance column for each purpose
3. ✅ Any variances > 10%? Investigate
4. ✅ Check Gantt Chart tab for schedule delays
5. ✅ If on track: Archive this report (manual screenshot/export)
6. ✅ If at risk: Escalate and plan mitigation

### **Scenario 3: Late Delivery on Phase 1**
1. ✅ Notice in Gantt Chart that Phase 1 "Actual Start" is after "Planned Start"
2. ✅ Open Data Explorer, filter for Phase 1 purposes
3. ✅ Review individual PLODs to understand delay (weather, equipment, crew)
4. ✅ Calculate impact: how much delay affects Phase 2?
5. ✅ Adjust Phase 2 budget dates in Admin → Budget (edit start_date, end_date)
6. ✅ Re-check Gantt Chart to confirm new timeline
7. ✅ Report to stakeholders

### **Scenario 4: Cost Overrun Alert**
1. ✅ See 🔴 Red status in Budget vs Actual for "RC Definition"
2. ✅ Check Actual Cost vs Budget
3. ✅ Investigate: Is it fewer metres at higher rate, or more metres?
4. ✅ Review actual rates paid (check recent PLODs)
5. ✅ Compare to configured rates in Admin → 💰 Rate Management
6. ✅ If rates changed, update budget rates
7. ✅ If volume changed, contact site supervisor
8. ✅ Decision: Increase budget, reduce scope, or re-baseline

---

## 💡 Pro Tips

1. **Use work groups for accountability**: Assign each contractor to their phases. Easy to track who's responsible for variance.

2. **Import Gantt chart early**: Even rough dates are better than defaults. Gantt becomes your schedule baseline.

3. **Set realistic budget rates**: Consult with procurement/finance on $/metre before drilling starts. Rates locked in = better cost predictions.

4. **Check dashboard weekly**: Budget vs Actual should be reviewed at least weekly. Catch variances early.

5. **Keep hole names consistent**: If PLOD says "TIVAN-001" but hole_purposes has "Tivan-001", it won't match. Use exact spelling.

6. **Document any manual edits**: If you override a budget amount or delete a PLOD, note it somewhere. Audit trail is limited.

7. **Use Data Explorer for detailed dives**: Budget vs Actual gives you a summary. Data Explorer shows the details (individual holes, depths, dates).

8. **Export monthly snapshots**: Download tables as CSV at end of month for historical record. Dashboard doesn't have version history (yet).

---

## 📞 Support & Contact

- **General questions**: Contact your project manager or drill site supervisor
- **Admin issues** (password, user access): Contact your IT admin
- **Feature requests or bugs**: Use Admin → 💬 Feedback tab
- **Database issues or recovery**: Contact system administrator

---

**Last Updated**: April 2026  
**Version**: 1.0 (Full Feature Set)
