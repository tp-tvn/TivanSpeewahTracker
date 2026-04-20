# 🚀 Drill Tracker - Quick Start

## Open the Dashboard

### ⭐ **The Easiest Way**
Double-click this file to open the dashboard:
```
app/dashboard.bat
```

That's it! The dashboard will open in your browser.

---

## What You're Looking At

The **Drill Tracker Dashboard** shows:
- **Drill Costs**: Real-time cost tracking for active drill projects
- **Budget Monitoring**: Current spending vs. budget limits
- **Timeline Analysis**: Gantt charts showing project schedules
- **Activity Types**: Different types of drilling activities being tracked
- **Admin Panel**: For managing drill data and settings

---

## First Time Setup

### Step 1: Install Dependencies
Run this once:
```
app/install.bat
```

### Step 2: Start the Dashboard
```
app/dashboard.bat
```

The dashboard opens automatically in your default browser at `http://localhost:8501`

---

## File Organization

```
Drill Tracker/
├── 📖_OPEN_TEAM_BRIEFING.bat    ← Opens full documentation
├── QUICKSTART.md                 ← You are here
├── README.md                     ← Project overview
├── INDEX.md                      ← File navigation guide
│
├── app/                          ← Application source code
│   ├── dashboard.bat             ← ⭐ OPENS THE DASHBOARD
│   ├── admin.bat                 ← Opens admin panel
│   ├── app.py                    ← Main Streamlit app
│   └── [other Python files]
│
├── data/                         ← Databases & imported data
│   ├── drill_costs.db            ← Main database
│   ├── tivan.db                  ← Tivan database
│   ├── August/                   ← Historical drill sheets
│   └── tmp_import/               ← Temporary import folder
│
├── config/                       ← Configuration & assets
│   ├── logo.png
│   ├── .streamlit/config.toml
│   └── .claude/                  ← Claude Code settings
│
├── data_imports/                 ← Templates & examples
│   ├── earthworks_template.csv
│   └── example_gantt.csv
│
└── referenced/docs/              ← Full documentation
    ├── TEAM_BRIEFING.md
    ├── BRIEFING.html
    └── [many other guides]
```

---

## Common Tasks

### ✅ Check Drill Costs
1. Open: `app/dashboard.bat`
2. Go to "Drill Costs" tab
3. View current costs and budget status

### 📊 View Gantt Chart
1. Open: `app/dashboard.bat`
2. Go to "Timeline" tab
3. See project schedules

### 💾 Manage Data
1. Open: `app/admin.bat`
2. Use admin panel to add/edit drill data

### 📥 Import Drill Sheets
1. Place CSV files in `data/tmp_import/`
2. Open dashboard and use import feature
3. Files move to `data/August/` when processed

---

## Need Help?

- **Quick reference**: Open `OPEN_FULL_DOCUMENTATION.bat`
- **Full documentation**: See `referenced/docs/TEAM_BRIEFING.md`
- **Troubleshooting**: See `referenced/docs/` folder

---

## Tips

💡 **Bookmark the dashboard URL**: After opening, bookmark `http://localhost:8501` in your browser  
💡 **Keep the terminal open**: The terminal window stays open while the dashboard runs  
💡 **Database**: All data is stored in `data/drill_costs.db`  
💡 **Backups**: Automatic backups are in `data/` folder

---

**Ready?** Double-click `app/dashboard.bat` to get started! 🎯
