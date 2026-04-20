# Gantt Chart Tab — Planned vs Actual Timeline

## Overview

The new **"📅 Gantt Chart"** tab provides a visual comparison of planned vs actual drilling timelines for all purposes.

**Location**: Top navigation → "📅 Gantt Chart"

## What It Shows

### Main Gantt Chart Visualization
A horizontal bar chart displaying:
- **Y-axis**: Drilling purposes
- **X-axis**: Timeline (dates)
- **Planned bars** (blue): Budget allocation periods from Gantt imports
- **Actual bars** (green): Actual drilling dates from PLOD data

Each bar shows:
- Purpose name
- Type (Planned or Actual)
- Start and end dates
- Resource details (PLODs count, metres drilled)

### Timeline Summary Table
Detailed comparison for each purpose:
| Column | Meaning |
|--------|---------|
| Purpose | Drilling purpose name |
| Planned Start | Budgeted start date from Gantt chart |
| Actual Start | When drilling actually started |
| Start Variance | Days early (negative) or late (positive) |
| Planned End | Budgeted end date |
| Actual End | When drilling actually ended |
| Planned Duration | Days in planned timeline |
| Actual Duration | Days in actual drilling timeline |

### Insights Section
Quick statistics showing:
- **Total Purposes**: Number of purposes tracked
- **Started**: How many purposes have actual drilling data
- **Not Yet Started**: Purposes with budgets but no drilling yet
- **Early/Late Starts**: Purposes that started before/after schedule

Color-coded insights:
- 🟢 Green: Purposes that started early
- 🟡 Yellow: Purposes that started late
- 🔵 Blue: Purposes not yet started

## How to Read the Gantt Chart

### Example: Single Purpose
```
Purpose: "MDM Earthworks"

Planned:  [==============================]
          2026-03-01          2026-05-31
          
Actual:        [==============]
               2026-03-15  2026-05-15

Start Variance: +14 days (started late)
Duration: Planned 92 days, Actual 62 days (finished early)
```

### Example: Multiple Periods (One Purpose)
```
Purpose: "Tivan Presence"

Planned:  [===========][===========]
          Phase 1     Phase 2
          
Actual:       [=====][======]
              Phase 1 overlapped
              
Shows two contractor phases with different budgets
```

## Data Sources

### Planned Timeline
Comes from: **Admin → Budget → Import from Gantt Chart**
- Dates: `start_date` and `end_date` from budget allocations
- Only shows purposes with `in_scope = 1` (active)

### Actual Timeline
Comes from: **PLOD data**
- Calculated from: `MIN(PLOD date)` to `MAX(PLOD date)` per purpose
- Shows: How long purposes actually took in reality
- Includes: Number of PLODs and total metres drilled

## Features

### Interactive Hover
Hover over any bar to see:
- Purpose name
- Type (Planned/Actual)
- Start and end dates
- Resource information
- Duration in days

### Responsive Design
- Height automatically adjusts based on number of purposes
- Scales to fill the screen width
- Left margin expands for long purpose names

### Sorting
- Purposes listed alphabetically in the chart
- Can be reordered by clicking the summary table headers

## Use Cases

### 1. Schedule Compliance
Compare planned vs actual start dates to identify delays:
```
Started on time?     → Green (Planned Start = Actual Start)
Started early?       → Early start notification  
Started late?        → Late start warning
Not started?         → Blue (future work)
```

### 2. Duration Analysis
See if work took longer or shorter than expected:
```
Planned: 90 days
Actual: 62 days
Result: Finished 28 days early
```

### 3. Multi-Phase Work
Track multiple periods of the same purpose:
```
"Tivan Presence - Contractor A" (Jan-Mar)
"Tivan Presence - Contractor B" (Apr-Jun)
"Tivan Presence - Follow-up"    (Jul-Sep)
```

### 4. Portfolio View
See overall project timeline at a glance:
- Which purposes overlap
- Which phases are sequential
- Total project duration
- Risk areas (purposes not yet started)

## Interpretation Tips

### ✓ Good Signals
- Planned and actual timelines overlap well
- Actual starts match planned starts closely
- Projects finishing on or ahead of schedule

### ⚠️ Warning Signs
- Actual start significantly later than planned (late variance > 14 days)
- Actual duration much longer than planned
- Many purposes marked as "Not Yet Started" but should have started

### ℹ️ Notes
- If no actual bars show for a purpose, it hasn't been drilled yet
- Default planned dates (2020-01-01 to 2099-12-31) mean the purpose exists but wasn't in your Gantt import
- To get accurate planned dates, use the Gantt Import feature in Admin → Budget

## Actions You Can Take

### Update Planned Dates
If actual drilling is significantly different from plan:
1. Go to **Admin → Budget**
2. Edit the budget allocation start/end dates
3. Re-import from updated Gantt chart if available

### Mark Out of Scope
If a purpose no longer applies:
1. Go to **Admin → Budget**
2. Uncheck "In Scope" for that purpose
3. It will disappear from the Gantt chart

### Investigate Delays
If a purpose started late:
1. Check the Data Explorer for more details
2. Review the associated PLODs
3. Determine the cause (weather, equipment, staffing, etc.)

### Plan Next Phases
Use the visual timeline to:
- Identify when phases end so you can sequence work
- See overlapping purposes that might compete for equipment
- Plan mobilizations and crew deployments

## Technical Details

### Database Query
The function `db.get_gantt_timeline_data()` returns:
```python
{
    "Purpose": "2026 RC Resource Definition",
    "Start": "2026-01-15",
    "End": "2026-05-31",
    "Type": "Planned" or "Actual",
    "Duration": 136,  # in days
    "Resource": "Budget" or "Drilling (5 PLODs, 1250m)"
}
```

### Visualization
Built with Plotly's horizontal bar chart:
- Grouped bars for Planned vs Actual
- Custom hover information
- Responsive sizing
- White theme for clarity

### Performance
- Renders instantly for up to 50+ purposes
- No pagination needed (all data visible with scroll)
- Cached during dashboard session

## Limitations & Future Work

### Current Limitations
- Shows timeline only, not cost or metres progress
- Cannot edit directly from Gantt chart (edit in Admin → Budget)
- Early/Late classification uses simple date comparison (no variance tolerance)

### Planned Enhancements
- Add cost overlay (budgeted vs actual spending)
- Add metres progress bars
- Variance thresholds (e.g., > 7 days = "late")
- Milestone markers for key events
- Filter by purpose, status, or rig
- Export as PNG/PDF for reporting
- Schedule comparison by contractor or rig

## Keyboard Shortcuts

When viewing the Gantt chart:
- **Hover**: See detailed information
- **Click legend**: Toggle Planned/Actual visibility
- **Zoom**: Click and drag on chart to zoom into date range
- **Pan**: Shift + drag to move around chart

## Example Insights from Real Data

Looking at the example data:
- **24 Planned timelines** imported from Gantt chart
- **4 Active purposes** with actual drilling data
- Most purposes not yet started (future work)
- Some early data showing drilling is beginning

As more PLODs are imported:
- Green actual bars will grow
- Variances will be calculated
- Risks (late starts, delays) will be highlighted
