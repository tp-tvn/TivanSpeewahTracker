# Quick Start: Gantt Chart Dashboard Tab

## In 2 Minutes

### Step 1: Get Your Data Ready
You need:
- **Planned dates**: From your Gantt chart
- **Actual dates**: From PLOD imports

### Step 2: Import Gantt Chart Dates
1. Go to **Admin → Budget**
2. Scroll to **"📊 Import from Gantt Chart"**
3. Upload your Gantt CSV/Excel
4. Map items to purposes
5. Click Import

### Step 3: Import PLOD Data
1. Go to **Import PLODs** tab
2. Upload your daily PLOD files
3. System processes automatically

### Step 4: View Gantt Chart
1. Click **"📅 Gantt Chart"** tab (top navigation)
2. See blue bars (planned) vs green bars (actual)
3. Read the summary table below

## What You'll See

```
📅 Gantt Chart Tab shows:

[Visual Timeline]
Purpose A  [====PLANNED====]
              [===ACTUAL===]

Purpose B  [====PLANNED====]
           [LATE - starts here]

Purpose C  [====PLANNED====]
           (Not started yet)

[Summary Table]
Shows exact dates and variance for each purpose

[Insights]
Total: 12 purposes
Started: 8
Not Yet Started: 4
Late Starts: 3
```

## What Each Color Means

- 🔵 **Blue bars** = Planned timeline (from Gantt chart)
- 🟢 **Green bars** = Actual drilling (from PLODs)
- 🟡 **Yellow highlights** = Started late
- 🟢 **Green highlights** = Started early
- 🔵 **Blue highlights** = Not yet started

## Common Questions

**Q: The chart is empty**
A: You need at least one Gantt import + one PLOD. Do both steps above.

**Q: Why don't dates match?**
A: Make sure hole names in PLODs match hole_purposes assignments. Check Admin → Drillhole Purposes.

**Q: Can I edit the chart?**
A: No, but you can edit dates in Admin → Budget table, then come back to Gantt tab.

**Q: Why are my 2026 purposes not showing?**
A: They'll show once you have PLODs dated in 2026. Until then, only planned bars show.

## Key Insights to Look For

✓ **On Schedule**: Planned and actual bars overlap perfectly
⚠️ **Late**: Actual starts significantly after planned
✓ **Early**: Actual starts before planned (good!)
? **Not Started**: Only blue bar, no green bar yet

## Data Used

| Source | What It Shows | Color |
|--------|---------------|-------|
| Budget Allocations (Gantt) | When you planned work | Blue |
| PLOD Data | When work actually happened | Green |

## Next Level: Analysis

Once you see the chart:

1. **Spot delays**: Yellow highlights show late starts
2. **Check progress**: Green bars show actual timeline so far
3. **Plan ahead**: Blue bars show what's coming
4. **Adjust budget**: Edit dates in Admin → Budget if needed

## For More Details

- **How it works**: See GANTT_CHART_TAB.md
- **Technical details**: See GANTT_CHART_IMPLEMENTATION.md
- **Importing dates**: See GANTT_IMPORT_GUIDE.md
