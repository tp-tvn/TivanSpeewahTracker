# Application Launchers — Quick Start Guide

## Overview

Two convenient .bat files have been created to launch the Tivan Tracking Tool:
- **dashboard.bat** — Main user dashboard
- **admin.bat** — Pre-authenticated admin panel

## Using the Launchers

### Option 1: Double-Click the .bat File

1. **Open Windows Explorer**
2. **Navigate to**: `H:\My Drive\Claude Projects\Drill Tracker\`
3. **Find**: `dashboard.bat` or `admin.bat`
4. **Double-click** the file
5. Application launches in your default browser

### Option 2: From Command Prompt

```bash
cd "H:\My Drive\Claude Projects\Drill Tracker"
dashboard.bat
```

or

```bash
admin.bat
```

### Option 3: Create Shortcuts

For quick access, create desktop shortcuts:

1. **Right-click** on the .bat file
2. **Send to → Desktop (create shortcut)**
3. **Rename** the shortcut for clarity
4. **Double-click** anytime to launch

## What Each Launcher Does

### dashboard.bat
- **Purpose**: Launch the main user dashboard
- **Runs**: `streamlit run app.py`
- **Access**: Full dashboard with all features
- **Authentication**: Not required (public view)
- **URL**: http://localhost:8501

Features available:
- 📊 Tivan Dashboard
- 📋 Tivan Tracker
- 📅 Gantt Chart
- 📂 Import PLODs
- 🔍 Data Explorer
- 💧 Groundwater
- And more...

### admin.bat
- **Purpose**: Launch pre-authenticated admin panel
- **Runs**: `streamlit run admin.py`
- **Access**: Admin configuration tools
- **Authentication**: Pre-authenticated (no login needed)
- **URL**: http://localhost:8502

Features available:
- 🎯 Drillhole Purposes
- 💰 Rate Management
- 📊 Budget Allocations
- 📅 Gantt Chart Import
- ⚙️ Rig Configuration
- 🔧 System Settings
- And more...

## System Requirements

✓ **Python 3.8+** installed and in PATH
✓ **Streamlit** installed (`pip install streamlit`)
✓ **pandas** installed (`pip install pandas`)
✓ **plotly** installed (`pip install plotly`)
✓ **openpyxl** installed (`pip install openpyxl`)

### Verify Python Installation

Open Command Prompt and type:
```bash
python --version
```

Should show version 3.8 or higher.

## Typical Workflow

### Daily Use
1. **Double-click dashboard.bat**
2. Navigate to relevant tab
3. Import PLODs or view reports
4. Close browser when done
5. Command window closes automatically

### Administrative Tasks
1. **Double-click admin.bat**
2. Configure purposes, rates, budgets
3. Import Gantt charts
4. Manage system settings
5. Close browser when done

### Parallel Running
You can run both simultaneously:
1. **Launch dashboard.bat** (port 8501)
2. **Launch admin.bat** (port 8502)
3. Switch between browser tabs or windows
4. Both share the same database

## Troubleshooting

### "Python is not installed or not in PATH"

**Solution 1: Add Python to PATH**
1. Find Python installation folder
   - Usually: `C:\Users\YourName\AppData\Local\Programs\Python\Python312\`
   - Or: `C:\Program Files\Python312\`
2. Add to System PATH:
   - **Windows Settings** → Search "Environment Variables"
   - **Edit System Environment Variables**
   - **Environment Variables** button
   - Under "System variables", find **Path**
   - **Edit** → **New** → Paste Python folder
   - **OK**, restart computer

**Solution 2: Use Full Python Path**
Edit the .bat file and replace:
```batch
python -m streamlit run app.py
```

With full path:
```batch
C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe -m streamlit run app.py
```

### "admin.py not found" or "app.py not found"

**Solution**: Make sure you're in the correct directory
- The .bat files must be in the same folder as app.py, admin.py, and db.py
- Check: `H:\My Drive\Claude Projects\Drill Tracker\`

### Port Already in Use

**Symptom**: Error about port 8501 or 8502 already in use

**Solution**: 
- Streamlit automatically tries next port (8503, 8504, etc.)
- Or close the application using that port
- Or modify the .bat file to specify a port:

```batch
python -m streamlit run app.py --server.port 8505
```

### Browser Doesn't Open Automatically

**Symptom**: Command window shows "local URL: http://localhost:8501" but browser doesn't open

**Solution**: 
- Manually open browser
- Go to `http://localhost:8501` (or the URL shown)
- Bookmark for future reference

### Application Crashes or Won't Start

**Solution 1**: Check for error message in command window
- Note the error
- Verify database file exists: `drill_costs.db`

**Solution 2**: Reinstall dependencies
```bash
pip install --upgrade streamlit pandas plotly openpyxl
```

**Solution 3**: Check database
- Delete `drill_costs.db` to reset (loses data!)
- Or run `python db.py` to reinitialize

## Advanced Usage

### Custom Port

Edit the .bat file and add `--server.port`:

```batch
python -m streamlit run app.py --server.port 9001
```

### Disable Browser Auto-Open

Add `--logger.level=error`:

```batch
python -m streamlit run app.py --server.headless true
```

### Run Headless (No Browser)

```batch
python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
```

### Access from Other Computers

By default, Streamlit only listens on localhost. To access from another machine:

Edit the .bat file:
```batch
python -m streamlit run app.py --server.address=0.0.0.0
```

Then access from another computer:
```
http://YOUR_COMPUTER_IP:8501
```

## Common Tasks

### View Dashboard
```batch
dashboard.bat
```
Then click "📊 Tivan Dashboard" tab

### Import PLODs
```batch
dashboard.bat
```
Then click "📂 Import PLODs" tab

### Configure Budgets
```batch
admin.bat
```
Then click "💰 Budget" tab

### View Gantt Chart
```batch
dashboard.bat
```
Then click "📅 Gantt Chart" tab

### Manage Purposes
```batch
admin.bat
```
Then click "🎯 Drillhole Purposes" tab

## Performance Tips

### Tip 1: One Instance at a Time
If you only need the dashboard, use:
```batch
dashboard.bat
```
Don't need admin? Use dashboard only.

### Tip 2: Keep Browser Window Open
Minimize instead of closing to avoid restart overhead.

### Tip 3: Browser Caching
First load is slower (caching). Subsequent loads are faster.

### Tip 4: Database Maintenance
Periodically check database size:
- Monitor `drill_costs.db` file size
- Large databases may slow down queries
- Consider archiving old data

## Security Notes

⚠️ **Important**: These launchers run on localhost (your machine only)

- Dashboard URL is `http://localhost:8501`
- Not accessible from other computers (by default)
- No authentication required on dashboard
- Admin panel also doesn't require password (pre-authenticated)

### If You Need Remote Access

**Do NOT expose directly to internet**

Use instead:
- VPN into your corporate network
- SSH tunneling
- Cloud deployment (with proper security)

## Shortcut Creation (Windows)

For fastest access, create desktop shortcuts:

### Method 1: Direct Shortcut
1. **Right-click** dashboard.bat
2. **Send to** → **Desktop (create shortcut)**
3. Rename to "Tivan Dashboard"
4. Double-click to launch

### Method 2: Custom Shortcut
1. **Right-click** desktop
2. **New** → **Shortcut**
3. **Location**: 
   ```
   cmd /k "H:\My Drive\Claude Projects\Drill Tracker\dashboard.bat"
   ```
4. **Name**: "Tivan Dashboard"
5. **Finish**

### Method 3: Task Scheduler
Schedule automatic startup:
1. **Windows Task Scheduler**
2. **Create Basic Task**
3. **Trigger**: At startup
4. **Action**: Run dashboard.bat

## Stopping the Application

### Method 1: Close Browser Tab
- Application continues running

### Method 2: Close Command Window
- Click **X** on command window
- Or type **Ctrl + C**
- Application stops

### Method 3: Task Manager
- **Ctrl + Shift + Esc** (Task Manager)
- Find **streamlit**
- **End Task**

## Summary

✓ **Quick launch**: Double-click dashboard.bat
✓ **Administration**: Double-click admin.bat
✓ **Both can run simultaneously**
✓ **No authentication needed**
✓ **Accessible on localhost only**
✓ **Create shortcuts for frequent use**

The launchers are production-ready and handle all setup automatically!
