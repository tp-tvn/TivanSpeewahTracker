# Gantt Import Workflow — Complete Guide

## Overview

The Gantt import now supports three types of items:
1. **Budget-Tracked Activities** — Items matched to existing purposes with budget allocation
2. **Timeline-Only Activities** — Items (like WSP contractor work) tracked on timeline but no budget
3. **Skipped Items** — Items not imported (discarded from timeline)

---

## Workflow Example: Mixed Gantt Chart

### Your Gantt Chart (CSV Format)

```csv
Item Name,Start Date,End Date,Budget,Work Group
Tivan Presence - Phase 1,2026-01-15,2026-03-31,150000,Contractor A
Tivan Presence - Phase 2,2026-04-01,2026-06-30,200000,Contractor B
MDM Earthworks,2026-03-01,2026-05-31,300000,Contractor A
WSP Site Setup,2026-01-20,2026-02-28,0,WSP
Bridge Construction,2026-05-15,2026-07-31,0,External
Site Access Road,2026-02-01,2026-02-28,0,
```

---

## Step 1: Upload the File

**Admin → Budget → Import from Gantt Chart**

- Click "Upload Gantt chart (CSV)"
- Select your file
- System reads columns automatically:
  - ✅ Detects: Item Name, Start Date, End Date, Budget, Work Group
  - **Important**: Budget column IS read (no manual entry needed!)
  - Supports: "budget", "amount", "cost", "Budget Amount", etc.

---

## Step 2: Auto-Matching

System compares each item to your existing purposes (fuzzy matching, 60% threshold):

```
Item                           Match Score    Status
────────────────────────────────────────────────────
Tivan Presence - Phase 1      0.74 (74%)     ✅ Auto-matched
Tivan Presence - Phase 2      0.78 (78%)     ✅ Auto-matched
MDM Earthworks                0.95 (95%)     ✅ Auto-matched
WSP Site Setup                0.12 (12%)     ❓ Needs input
Bridge Construction           0.05 (5%)      ❓ Needs input
Site Access Road              0.15 (15%)     ❓ Needs input
```

---

## Step 3: Handle Unmatched Items

**Option A: Create Timeline-Only Entries (Recommended for WSP)**

The unmatched items section shows:

```
Unmatched Items (Can Create Timeline-Only Entries)

3 items have no purpose assigned. Create timeline-only entries 
to show them on Gantt (no budget tracking). Useful for contractors 
like WSP with scheduled activities but external cost management.

| Gantt Item           | Start Date | End Date   | Work Group | Budget |
|─────────────────────|───────────|───────────|──────────|────────|
| WSP Site Setup      | 2026-01-20| 2026-02-28| WSP      | $0     |
| Bridge Construction | 2026-05-15| 2026-07-31| External | $0     |
| Site Access Road    | 2026-02-01| 2026-02-28|          | $0     |

☑ Create timeline-only purposes for these items
```

**Result**: WSP, Bridge, and Road become "timeline-only" purposes
- ✅ Appear on Gantt chart
- ❌ No budget allocation in admin table
- Perfect for contractor/external work with separate cost management

**Option B: Skip Them Entirely**

Leave the checkbox unchecked. Items won't appear anywhere.

**Option C: Manually Assign**

Before import, edit the "Map to Purpose" column to assign items to existing purposes if desired.

---

## Step 4: Preview & Budget Verification

**Budget-Tracked Items Preview**:

```
📊 Preview: How Gantt Items Will Be Aggregated

Multiple items for the same purpose will be combined 
(min start date, max end date, summed budget)

| Purpose              | Items | Start Date | End Date   | Total Budget | Work Group  |
|─────────────────────:|──────:|───────────:|───────────:|─────────────:|────────────:|
| Tivan Presence      | 2     | 2026-01-15| 2026-06-30| $350,000    | Contractor A|
| MDM Earthworks      | 1     | 2026-03-01| 2026-05-31| $300,000    | Contractor A|
```

**Key Points**:
- ✅ Budget amounts are read from your CSV (no manual entry!)
- ✅ Multiple items per purpose are summed: $150k + $200k = $350k
- ✅ Date ranges span min(starts) to max(ends)
- ✅ Work group uses first item's value (can edit in Admin Budget table later)

---

## Step 5: Import

Click "✅ Import Gantt Chart Allocations"

### Results:

**Budget-Tracked (3 purposes created/updated)**:
```
Purpose: Tivan Presence
├─ Drilling: $350,000 | Jan 15 to Jun 30 | Work Group: Contractor A
├─ Fuel: (auto-calculated) | Jan 15 to Jun 30
└─ Notes: Imported from Gantt (2 items)

Purpose: MDM Earthworks
├─ Drilling: $300,000 | Mar 1 to May 31 | Work Group: Contractor A
├─ Fuel: (auto-calculated) | Mar 1 to May 31
└─ Notes: Imported from Gantt (1 item)
```

**Timeline-Only (3 purposes created)**:
```
Purpose: WSP Site Setup
├─ Drilling: $0 (no budget) | Jan 20 to Feb 28 | Work Group: WSP
├─ Fuel: $0 | Jan 20 to Feb 28
└─ Notes: Timeline-only (no budget tracking)

Purpose: Bridge Construction
├─ Drilling: $0 (no budget) | May 15 to Jul 31 | Work Group: External
├─ Fuel: $0 | May 15 to Jul 31
└─ Notes: Timeline-only (no budget tracking)

Purpose: Site Access Road
├─ Drilling: $0 (no budget) | Feb 1 to Feb 28 | Work Group: (empty)
├─ Fuel: $0 | Feb 1 to Feb 28
└─ Notes: Timeline-only (no budget tracking)
```

---

## Step 6: View Results

### Admin Budget Table

Shows all 6 purposes (5 with budget, 1 timeline-only):

```
| In Scope | Purpose            | Drill WG | Drill $ | Drill Start | Drill End | EW WG | EW $  | EW Start | EW End | Fuel $ | Notes                  |
|:--------:|:------------------:|:--------:|:-------:|:-----------:|:---------:|:-----:|:-----:|:--------:|:------:|:------:|:---------------------:|
| ☑       | Bridge Construction| External | $0      | 2026-05-15 | 2026-07-31|       | $0    |          |        | $0     | Timeline-only (no ...) |
| ☑       | MDM Earthworks     | Contrac..| $300K   | 2026-03-01 | 2026-05-31|       | $0    |          |        | $300K  | Imported from Gantt... |
| ☑       | Site Access Road   |          | $0      | 2026-02-01 | 2026-02-28|       | $0    |          |        | $0     | Timeline-only (no ...) |
| ☑       | Tivan Presence     | Contrac..| $350K   | 2026-01-15 | 2026-06-30|       | $0    |          |        | $350K  | Imported from Gantt... |
| ☑       | WSP Site Setup     | WSP      | $0      | 2026-01-20 | 2026-02-28|       | $0    |          |        | $0     | Timeline-only (no ...) |
```

**Edit as needed**:
- Change Work Groups
- Adjust budgets
- Modify dates
- Add Earthworks activities
- Click "💾 Save All Budgets"

### Gantt Chart Tab

All activities appear, both tracked and timeline-only:

```
Contractor A - Tivan Presence    [====PLAN====]
                                  Jan    Feb    Mar    Apr    May    Jun
Contractor A - MDM Earthworks                        [=====PLAN=====]
Contractor B - Tivan Presence (Phase 2)                         [====PLAN====]
External - Bridge Construction                                              [====PLAN====]
WSP - WSP Site Setup             [==PLAN==]
(Road) - Site Access Road         [==PLAN]
```

**Key Features**:
- ✅ Tivan Presence shows combined timeline (Jan 15 to Jun 30)
- ✅ MDM Earthworks properly positioned
- ✅ WSP shows with $0 budget (timeline-only)
- ✅ Bridge and Road appear even though no budget
- ✅ Work groups clearly visible
- ✅ Fuel dates auto-calculated for tracked items

---

## Budget Column Support

The system recognizes these column names for budget:
- "Budget" ✅
- "Budget Amount"
- "Amount"
- "Cost"
- "Cost Amount"
- "Budget ($)"

**Example with different naming**:
```csv
Item Name,Start Date,End Date,Amount,Team
Tivan - Phase 1,2026-01-15,2026-03-31,150000,Contractor A
```

Column "Amount" will be auto-detected as budget. No manual entry needed!

---

## Common Scenarios

### Scenario 1: Contractor Costs Managed Externally

```
Item: "WSP Site Work"
Budget Column: $0 (or empty)
✅ Result: Timeline-only purpose (shows on Gantt, no budget tracking)
```

### Scenario 2: Multiple Items, One Purpose

```
Items: "Tivan Phase 1" ($150k) + "Tivan Phase 2" ($200k)
→ Mapped to purpose: "Tivan Presence"
✅ Result: Single entry with $350k budget (sum), Jan 15 to Jun 30 (span)
```

### Scenario 3: Splitting Activities

Want drilling and earthworks separate?

**Import as**: Both with "Tivan Presence"
↓ (Creates with $350k drilling)
**Edit in Admin → Budget**:
- Tivan Presence
  - Drilling: $200k, Jan 15 to Jun 30 (actual drill work)
  - Earthworks: $150k, Feb 1 to May 31 (separate contractor)

---

## Tips & Best Practices

### ✅ Do This:

1. **Include Budget Column in CSV**
   - Reduces transcription errors
   - Single source of truth
   ```csv
   Item Name,Start Date,End Date,Budget,Work Group
   Tivan Phase 1,2026-01-15,2026-03-31,150000,Contractor A
   ```

2. **Use Standard Column Names**
   - "Budget", "Start Date", "End Date"
   - System auto-detects variants
   - No setup needed

3. **Assign Work Groups in CSV**
   - Easier to manage contractor accountability
   - Shows in timeline visualization
   ```csv
   Work Group,Contractor,Team,Crew
   ```

4. **Create Timeline-Only for External Work**
   - WSP, external contractors, equipment rental
   - Shows full project scope on Gantt
   - No budget confusion

5. **Review Budget Aggregation**
   - Check preview table
   - Verify totals match your expectations
   - Especially important when combining multiple items

### ❌ Don't Do This:

1. **Leave Budget Column Out**
   - Will read as $0
   - You'll need to edit in Admin table manually

2. **Use Inconsistent Names**
   - "Budget", "Budget $", "Total Cost", "Amount"
   - Usually works, but check preview

3. **Mix Currencies**
   - Keep everything in same currency (AUD)
   - Conversion done separately if needed

4. **Skip Timeline-Only Items**
   - If WSP or contractor has scheduled work, keep them
   - Helps see full project timeline
   - Set budget=$0 for non-tracked work

---

## Troubleshooting

### "Could not identify required columns"

**Solution**: CSV must have columns containing:
- "item", "name", "title", or "activity" (purpose name)
- "start" or "start_date" (start date)
- "end" or "end_date" (end date)

Good: `Item Name, Start Date, End Date`
Bad: `WBS, Begin, Complete` ← No "start" or "end" keywords

### Budget shows as $0 in preview

**Possible causes**:
1. Budget column name not recognized
   - Check the error message for detected columns
   - Use standard name: "Budget"
2. Budget values are empty or invalid
   - Verify Excel numbers (not text)
   - Check for special characters

### Timeline-Only item doesn't appear on Gantt

- ✅ Is the checkbox "Create timeline-only purposes" checked?
- ✅ Do the start and end dates exist?
- ✅ Refresh the Gantt Chart page

### Work Group shows differently on Gantt

- If multiple items have different work groups for same purpose
- First item's work group is used
- Edit in Admin → Budget table to change

---

## Summary

The new Gantt import system:

| Feature | Before | Now |
|---------|--------|-----|
| Budget from CSV | ❌ Manual entry | ✅ Auto-read |
| Unmatched items | ❌ Discarded | ✅ Timeline-only option |
| WSP handling | ❌ Not visible | ✅ Shows on Gantt |
| Budget preview | ❌ No visibility | ✅ Full aggregation preview |
| Transcription errors | ⚠️ High risk | ✅ Eliminated |

You now have a complete, traceable workflow from Gantt chart to timeline visualization!
