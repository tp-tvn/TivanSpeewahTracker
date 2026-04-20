# 📑 Drill Tracker - File Navigation Guide

Use this guide to find files and understand the project structure.

---

## 🎯 I Want To...

### ▶️ Open the Dashboard
→ Double-click: `app/dashboard.bat`

### ▶️ Open the Admin Panel
→ Double-click: `app/admin.bat`

### ▶️ Read Full Documentation
→ Double-click: `OPEN_FULL_DOCUMENTATION.bat`

### ▶️ Get Quick Start Instructions
→ Open: `QUICKSTART.md`

### ▶️ Understand the Project
→ Open: `README.md`

### ▶️ Find Installation Instructions
→ See: `QUICKSTART.md` → Step 1

### ▶️ Import Drill Data
1. See: `QUICKSTART.md` → "Import Drill Sheets"
2. Place CSV files in: `data/tmp_import/`
3. Use dashboard admin panel to import

### ▶️ Backup My Data
1. Copy: `data/drill_costs.db`
2. Save to safe location
3. See: `referenced/docs/TEAM_BRIEFING.md` for details

### ▶️ View Historical Drill Sheets
→ Folder: `data/August/` (31 daily CSV files)

### ▶️ See Project Templates
→ Folder: `data_imports/` (templates and examples)

---

## 📁 Complete File Structure

### Root Files (Read These First)
```
Drill Tracker/
├── QUICKSTART.md              ← Quick start guide (5 min read)
├── README.md                  ← Project overview (10 min read)
├── INDEX.md                   ← This file - navigation guide
└── OPEN_FULL_DOCUMENTATION.bat  ← Opens full documentation
```

### 🚀 Application Folder: `app/`
**What it contains**: Source code and application launchers  
**What you'll use**: The `.bat` files to run the dashboard

```
app/
├── 📌 dashboard.bat           ← RUN THIS to open the dashboard
├── admin.bat                  ← Opens admin panel
├── install.bat                ← Install dependencies (first time only)
│
├── app.py                     ← Main Streamlit application
├── tracker_view.py            ← Dashboard views and displays
├── ingest.py                  ← Data import and processing
├── calculate.py               ← Cost calculations
├── db.py                      ← Database operations
├── admin.py                   ← Admin panel functionality
├── ew_ocr.py                  ← OCR utilities
└── requirements.txt           ← Python dependencies list
```

### 💾 Data Folder: `data/`
**What it contains**: Databases and imported drill data  
**What you might access**: Historical drill sheets, backups

```
data/
├── 📌 drill_costs.db          ← Main database (contains all your data)
├── tivan.db                   ← Secondary database
├── Drill Cost Tracker Updated.xlsx
│
├── 📁 August/                 ← Historical drill sheets (daily)
│   ├── 250801DS.csv
│   ├── 250802DS.csv
│   └── ... (29 more daily files)
│
├── 📁 tmp_import/             ← Staging folder for new imports
│   └── [place CSV files here before importing]
│
└── 📁 Backups/
    ├── drill_costs.db.backup_20260401_104843
    ├── drill_costs.db.backup_20260401_111359
    └── ... (more backups)
```

### ⚙️ Configuration Folder: `config/`
**What it contains**: System configuration and settings  
**What you might change**: Logo, Streamlit settings

```
config/
├── logo.png                   ← Dashboard logo/branding
│
├── 📁 .streamlit/
│   └── config.toml            ← Streamlit framework settings
│
└── 📁 .claude/
    ├── launch.json            ← Claude Code launch config
    └── settings.local.json    ← Local settings
```

### 📥 Data Imports Folder: `data_imports/`
**What it contains**: Templates and example files  
**What you'll use**: As templates for importing your own data

```
data_imports/
├── earthworks_template.csv    ← Template for drill sheet imports
└── example_gantt.csv          ← Example Gantt chart data
```

### 📚 Documentation Folder: `referenced/docs/`
**What it contains**: Complete project documentation  
**When to read**: For detailed information on specific features

```
referenced/docs/
│
├── 📖 TEAM_BRIEFING.md        ← Complete user guide (read in editor)
├── 📖 BRIEFING.html           ← HTML version (open in browser)
├── 📖 START_HERE.txt          ← Getting started text file
├── 📖 QUICK_REFERENCE_CARD.txt ← One-page reference (printable)
│
├── 📋 LAUNCHER_GUIDE.md       ← How to launch the dashboard
├── 📋 BUDGET_WORKFLOW.md      ← Budget tracking guide
│
├── 📊 GANTT_CHART_IMPLEMENTATION.md
├── 📊 GANTT_AUTO_MATCH.md
├── 📊 GANTT_IMPORT_GUIDE.md
├── 📊 GANTT_IMPORT_WORKFLOW.md
├── 📊 GANTT_CHART_TAB.md
├── 📊 QUICK_START_GANTT.md
│
├── 🔧 ACTIVITY_TYPE_IMPLEMENTATION.md
├── 🔧 ACTIVITY_TYPE_QUICK_REF.md
├── 🔧 ACTIVITY_TYPE_ROUTING.md
├── 🔧 WORK_GROUP_FEATURE.md
│
└── 📝 [Other documentation files]
    ├── SESSION_SUMMARY.md
    ├── ENHANCEMENTS_SUMMARY.md
    ├── IMPLEMENTATION_VERIFICATION.md
    ├── TIMELINE_FIX.md
    └── ...more
```

---

## 🎓 Reading Paths by Role

### 👤 Executive / Manager
1. Read: `QUICKSTART.md` (5 min)
2. Open dashboard: `app/dashboard.bat` (to see it in action)
3. Deep dive: `referenced/docs/BUDGET_WORKFLOW.md`

### 💻 Administrator
1. Read: `README.md` (10 min)
2. Read: `QUICKSTART.md` (5 min)
3. Setup: Run `app/install.bat` (first time)
4. Operate: Open `app/admin.bat`
5. Deep dive: `referenced/docs/LAUNCHER_GUIDE.md`

### 📊 Data Analyst
1. Read: `QUICKSTART.md` (5 min)
2. Open dashboard: `app/dashboard.bat`
3. Deep dive: `referenced/docs/GANTT_*.md` docs
4. Reference: `referenced/docs/BUDGET_WORKFLOW.md`

### 🔧 Developer
1. Read: `README.md` (10 min)
2. Review structure: This file
3. Read: `app/requirements.txt`
4. Code review: `app/*.py` files
5. Config: `config/` folder
6. Docs: `referenced/docs/IMPLEMENTATION_*.md`

### 📚 New User
1. Start: `QUICKSTART.md` (5-10 min)
2. Launch: Double-click `app/dashboard.bat`
3. Explore: Click through dashboard tabs
4. Deep dive: Open `OPEN_FULL_DOCUMENTATION.bat` when ready

---

## 📖 Documentation Files

### Quick Reference (Start Here)
| File | Type | Time | Purpose |
|------|------|------|---------|
| QUICKSTART.md | Markdown | 5 min | Quick setup & overview |
| START_HERE.txt | Text | 5 min | Getting started guide |
| QUICK_REFERENCE_CARD.txt | Text | 3 min | One-page reference |

### Guides (In-Depth Learning)
| File | Type | Time | Topic |
|------|------|------|-------|
| README.md | Markdown | 10 min | Project overview |
| TEAM_BRIEFING.md | Markdown | 45 min | Complete guide |
| BRIEFING.html | HTML | 45 min | Formatted web version |

### Feature Guides
| File | Topic | Best For |
|------|-------|----------|
| LAUNCHER_GUIDE.md | Running the dashboard | Setup & operations |
| BUDGET_WORKFLOW.md | Cost tracking | Budget management |
| GANTT_*.md (6 files) | Timeline/scheduling | Project timelines |
| ACTIVITY_TYPE_*.md (3 files) | Activity types | Activity configuration |
| WORK_GROUP_FEATURE.md | Work groups | Team organization |

### Technical Documentation
| File | Purpose |
|------|---------|
| IMPLEMENTATION_VERIFICATION.md | Technical verification |
| SESSION_SUMMARY.md | Development sessions |
| ENHANCEMENTS_SUMMARY.md | Feature enhancements |
| TIMELINE_FIX.md | Timeline fixes |

---

## 🔍 Search Tips

**Looking for something specific?**

In any markdown or text file, use `Ctrl+F` to search:
- "budget" → Budget-related content
- "import" → Import instructions
- "Gantt" → Timeline/scheduling
- "activity" → Activity types
- "admin" → Admin operations
- "error" or "troubleshoot" → Problem solving

In the HTML file (`BRIEFING.html`):
- Open in browser and use browser search (`Ctrl+F`)
- Use navigation menu to jump to sections

---

## ⚡ Quick Reference

### Most Used Files
1. `app/dashboard.bat` - Open dashboard
2. `app/admin.bat` - Open admin panel
3. `QUICKSTART.md` - Quick help
4. `data/drill_costs.db` - Your data

### File Extensions Explained
- `.bat` - Windows batch files (launchers)
- `.py` - Python source code
- `.md` - Markdown documentation (open in editor or browser)
- `.html` - Web pages (open in browser)
- `.txt` - Text files (open in any editor)
- `.csv` - Data files (can open in Excel or text editor)
- `.db` - SQLite database (stores your data)
- `.toml` - Configuration files
- `.json` - Configuration/settings files

---

## 🆘 Can't Find What You Need?

1. **Getting started?** → `QUICKSTART.md`
2. **Need help?** → `referenced/docs/START_HERE.txt`
3. **Full documentation?** → Open `OPEN_FULL_DOCUMENTATION.bat`
4. **Specific feature?** → Check folders in `referenced/docs/`
5. **Troubleshooting?** → See FAQ in `TEAM_BRIEFING.md`

---

**Last Updated**: April 14, 2026  
**Structure Version**: 2.0 (Organized)  
**Status**: Ready to Use
