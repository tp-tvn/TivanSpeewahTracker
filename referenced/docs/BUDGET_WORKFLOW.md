# Complete Budget Workflow with Gantt Import

## Overview
The drill tracker now supports a complete budget management workflow that connects your project Gantt chart to cost tracking and spending analysis.

## Workflow Steps

### Step 1: Set Up Drillhole Purposes (One-time)
**Location**: Admin → Drillhole Purposes

1. Import your drilling purposes via CSV
2. Optionally set planned metres for each hole
3. Or edit the quick-assign table directly

Example purposes:
- 2026 RC Resource Definition
- 2026 Diamond Metallurgical Drilling
- 2026 Geotech Drilling
- Sterilisation Drilling

### Step 2: Set Up Budget Rates (One-time)
**Location**: Admin → Budget → Budget Targets (scroll down)

1. Define cost rates for each drill_type + hole_type combination
2. Used to calculate actual costs from PLODs
3. Example: RC drilling with RCRD holes costs $150/m
4. Mark combinations as "not applicable" if they don't apply

### Step 3: Import Gantt Chart Dates (Project Planning)
**Location**: Admin → Budget → "📊 Import from Gantt Chart"

1. Export your project Gantt chart as CSV/Excel
2. Upload in the Gantt Import section
3. Map each Gantt item to a drilling purpose
4. Support multiple time periods per purpose (different contractors, phases)
5. Click Import to create budget allocations with date ranges

Result: Budget periods are created with start dates, end dates, and budgeted amounts

Example:
```
Gantt Item: "MDM Earthworks - Phase 1"
  → Maps to Purpose: "MDM Earthworks"
  → Creates: Budget allocation from 2026-03-01 to 2026-05-31, $300,000

Gantt Item: "MDM Earthworks - Phase 2"
  → Maps to Purpose: "MDM Earthworks"
  → Creates: Budget allocation from 2026-06-01 to 2026-08-31, $250,000
```

### Step 4: Import PLODs (Daily Operations)
**Location**: Main Dashboard → Import PLOD

1. Import daily activity PLODs as usual
2. Each PLOD contains drilling intervals with:
   - Hole name (matched to hole_purposes)
   - Depth, length in metres
   - Interval type (RC, HQ3, PQ3, etc.)
3. System automatically calculates costs using budget rates

### Step 5: Track Budget vs Actual (Ongoing)
**Location**: Main Dashboard → "Budget vs Actual"

The system now:
1. Groups actual costs by hole purpose
2. Compares against budgeted amount for the active date range
3. Shows metres progress, cost per metre
4. Warns if approaching or exceeding budget

Data points tracked:
- **Actual Metres**: Total metres drilled in this period
- **Actual Cost**: Calculated from PLOD data × budget rates
- **Planned Metres**: Imported when you set them up
- **Budget**: From Gantt chart import
- **Cost per Metre**: Actual ÷ Metres
- **Budget per Metre**: Budget ÷ Planned Metres

### Step 6: Audit & Adjust (As Needed)
**Location**: Admin → Budget → Various sections

1. **Audit missing budget rates**: Shows drill_type + hole_type combinations without rates
2. **Edit budget allocations**: Manually adjust dates, amounts, scope
3. **Mark as out-of-scope**: Flag specific purposes as not in this budget period
4. **Re-import Gantt**: Update from revised schedule

## Data Flow Diagram

```
Gantt Chart (Project Schedule)
    ↓
Gantt Chart Import (Admin)
    ↓
purpose_budget_allocations table
    ├─ Purpose name
    ├─ Start date (when active)
    ├─ End date (when active)
    └─ Budget amounts
    ↓
Daily PLOD Import
    ↓
Drilling intervals with:
    ├─ Hole name → hole_purposes → purpose
    ├─ Metres drilled
    └─ Interval type
    ↓
Cost Calculation
    ├─ Find budget rate for interval_type + hole_type
    ├─ Calculate cost = metres × rate
    └─ Allocate to correct budget period (by date)
    ↓
Budget vs Actual Report
    ├─ Actual metres vs planned
    ├─ Actual cost vs budgeted
    ├─ Cost per metre tracking
    └─ Variance analysis
    ↓
Audit & Decision
    ├─ Forecast spending
    ├─ Flag overspend risks
    ├─ Adjust budget if needed
    └─ Modify scope
```

## Multiple Budget Periods Per Purpose

The system supports different contractors, phases, or work periods for the same purpose:

```
Purpose: "2026 RC Resource Definition"

Period 1: Contractor A
  Start: 2026-01-15
  End: 2026-03-31
  Budget: $200,000
  Status: In Progress

Period 2: Contractor B
  Start: 2026-04-01
  End: 2026-06-30
  Budget: $150,000
  Status: Scheduled

Period 3: Follow-up Drilling
  Start: 2026-07-01
  End: 2026-09-30
  Budget: $100,000
  Status: Planned
```

When you import a PLOD dated 2026-05-15:
- System finds it's drilling with purpose "2026 RC Resource Definition"
- Searches budget allocations where start_date ≤ 2026-05-15 ≤ end_date
- Matches to Period 2 (Contractor B)
- Uses that period's budget for cost tracking

## Key Database Tables

### purpose_budget_allocations
Stores budget periods created from Gantt import:
```sql
CREATE TABLE purpose_budget_allocations (
    purpose TEXT,              -- "2026 RC Resource Definition"
    start_date TEXT,           -- "2026-01-15"
    end_date TEXT,             -- "2026-03-31"
    drilling_budget REAL,      -- $200,000
    earthworks_budget REAL,    -- $0
    fuel_budget REAL,          -- $0
    currency TEXT,             -- "AUD"
    in_scope INTEGER,          -- 1 (active) or 0 (out of scope)
    notes TEXT,                -- "Imported from Gantt: Contractor A Phase 1"
    PRIMARY KEY (purpose, start_date, end_date)
);
```

### budget_targets
Budget rates for cost calculation:
```sql
CREATE TABLE budget_targets (
    drill_type TEXT,    -- "RC", "HQ3", "PQ3"
    hole_type TEXT,     -- "RCRD", "DDGT", "DMET", etc.
    rate REAL,          -- $/metre
    PRIMARY KEY (drill_type, hole_type)
);
```

### hole_purposes
Assigns purposes to holes:
```sql
CREATE TABLE hole_purposes (
    hole_name TEXT PRIMARY KEY,
    purpose TEXT,       -- "2026 RC Resource Definition"
    planned_metres REAL,
    variance_metres REAL,
    variance_reason TEXT
);
```

## Quick Checklist for New Projects

- [ ] Define all drilling purposes
- [ ] Import hole list with planned metres
- [ ] Assign holes to purposes (CSV import or quick-assign table)
- [ ] Set budget rates for each drill type + hole type
- [ ] Export project Gantt chart as CSV
- [ ] Upload Gantt chart and map items to purposes
- [ ] Save budget allocations
- [ ] Start importing PLODs
- [ ] Monitor Budget vs Actual dashboard

## Troubleshooting

### "Gantt item won't map to purpose"
- Purpose might not exist in your system yet
- Create it in Drillhole Purposes section first
- Re-upload the Gantt chart

### "Budget showing $0 actual cost"
- Check that budget rates are set for the drill types being used
- Look in Admin → Budget → Audit section for missing rates
- Check that holes are assigned to purposes
- Verify PLODs are importing with the correct interval types

### "Wrong budget period being used"
- Check the PLOD date matches the expected period
- Verify start_date and end_date are correct in the imported budget allocation
- Dates are inclusive (start_date ≤ PLOD date ≤ end_date)

### "Import didn't work"
- Check Admin → Budget table refreshes with new rows
- Verify purposes were spelled correctly during mapping
- Check budget allocation notes show the Gantt item source
- Look for error messages in red text at top of page

## Future Enhancements

Planned features:
1. **Smart matching**: Auto-suggest purpose matches based on Gantt item names
2. **Cost projection**: Forecast spending based on planned metres and actual ROP
3. **Overspend alerts**: Flag approaching budget limits
4. **Multi-contract tracking**: Track spend by contractor across purposes
5. **Variance analysis**: Deep dive into cost and schedule variance
6. **Historical tracking**: Archive budget allocations from completed periods
