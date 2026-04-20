# Work Group Feature — Organize Drilling by Contractor/Team

## Overview

The Gantt chart now supports grouping by **Work Groups** (contractors, teams, crews). This allows you to:
- Organize drilling activities by who's doing the work
- Compare timelines across different teams/contractors
- Track parallel work by different groups
- Manage contract-specific budgets and timelines

## Features

✅ **Work Group Assignment**
- Assign each budget allocation to a work group
- Edit directly in Admin → Budget table
- Optional field (leave blank for "Unassigned")

✅ **Gantt Chart Grouping**
- Y-axis shows: "Work Group - Purpose"
- Visual organization by contractor/team
- Planned (blue) vs Actual (green) bars grouped by work group

✅ **Auto-Detection from Gantt Import**
- System automatically extracts work group from Gantt chart if column exists
- Looks for columns containing: "work", "group", "contractor", "team", "crew"
- You can edit before importing if needed

✅ **Summary Table**
- Work Group column in timeline summary
- Shows which contractor/team runs each purpose
- Sorted by work group for easy reading

## How to Use

### Method 1: Assign Work Groups Manually

1. Go to **Admin → Budget**
2. Look at the "Work Group" column in the budget allocation table
3. Click each cell to enter the work group name
   - Examples: "Contractor A", "Tivan Crew", "Smith Drilling", "Team 2"
4. Click **"Save Purpose Budget Allocations"**

### Method 2: Import from Gantt Chart

1. Prepare your Gantt chart CSV/Excel with a column for work group
   - Column names that work: "Work Group", "Contractor", "Team", "Crew"
2. Go to **Admin → Budget → Import from Gantt Chart**
3. Upload your file
4. System auto-detects the work group column
5. Edit in "Work Group" column if needed
6. Map purposes as usual
7. Click **"Import Gantt Chart Allocations"**
   - Work groups are imported along with dates

### Method 3: Spreadsheet Template

Example Gantt chart CSV format:
```
Item Name,Start Date,End Date,Budget,Work Group
Tivan Phase 1,2026-01-15,2026-03-31,150000,Contractor A
Tivan Phase 2,2026-04-01,2026-06-30,200000,Contractor B
MDM Earthworks,2026-03-01,2026-05-31,300000,Contractor A
```

## Gantt Chart Display

### Before (Ungrouped)
```
Purpose A (Contractor A)    [====PLAN====]
Purpose A (Contractor B)         [===PLAN===]
Purpose B (Contractor A)    [==PLAN==]
```

### After (Grouped by Work Group)
```
Contractor A - Purpose A    [====PLAN====]
Contractor A - Purpose B    [==PLAN==]
Contractor B - Purpose A         [===PLAN===]
```

## Database Structure

### purpose_budget_allocations Table
New column added:
```sql
work_group TEXT DEFAULT ''
```

Can contain any text:
- Contractor names: "Smith Drilling", "ABC Excavation"
- Team names: "Team 1", "Core Team", "Follow-up Crew"
- Location: "North Site", "South Pit"
- Any identifier you use to group work

### get_gantt_timeline_data() Function
Returns new field:
```python
{
    ...
    "WorkGroup": "Contractor A",  # NEW
    ...
}
```

## Examples

### Single Contractor, Multiple Purposes
```
Contractor A - Tivan Presence     [=========]
Contractor A - MDM Earthworks     [==========]
Contractor A - RC Definition      [===]
```

### Multiple Contractors, Same Purpose
```
Contractor A - Tivan Phase 1      [====]
Contractor B - Tivan Phase 2           [====]
Contractor C - Tivan Phase 3                [====]
```

### Complex Portfolio
```
Contractor A
  - Tivan Presence              [====PLAN====]
  - MDM Earthworks              [==========PLAN==========]
  
Contractor B
  - RC Definition               [===PLAN===]
  - Geotech Drilling            [========PLAN========]
  
Internal Team
  - Follow-up Work                              [==PLAN==]
```

## Work Group Names Best Practices

Good names:
- ✓ "Contractor A"
- ✓ "Smith Drilling Services"
- ✓ "Team 1 - Tivan Site"
- ✓ "ABC Excavation"
- ✓ "Internal - Core Team"

Avoid:
- ✗ Very long names (> 30 chars)
- ✗ Special characters (use letters, numbers, hyphens, spaces)
- ✗ Duplicates with different capitalization (use consistent naming)

## Summary Table Interpretation

The summary table now shows:
| Column | Meaning |
|--------|---------|
| Work Group | Which contractor/team |
| Purpose | What work |
| Planned Start | When scheduled |
| Actual Start | When actually happened |
| Start Variance | Days early/late |
| Planned/Actual Duration | How long took |

Example:
```
Work Group     Purpose              Variance
Contractor A   Tivan Presence       +5 days late
Contractor B   MDM Earthworks       -3 days early
Internal Team  Follow-up            Not started yet
```

## Insights with Work Groups

The insights dashboard highlights:
- **Early starters**: Work groups that beat schedule
- **Late starters**: Work groups that delayed
- **Not started**: Work groups with planned work but no drilling yet

Each is color-coded by work group for easy identification.

## Tips & Tricks

### Tip 1: Consistent Naming
Use the same work group names across all imports:
- ✓ Always "Contractor A" (not "Con A", "Contractor_A")
- Makes grouping and filtering more reliable

### Tip 2: Descriptive Names
Include location or context if helpful:
- "Smith Drilling - North Pit" (more descriptive)
- vs. "Smith" (ambiguous)

### Tip 3: Edit Existing Allocations
To change a work group on an existing budget allocation:
1. Go to **Admin → Budget**
2. Find the row
3. Click the Work Group cell
4. Type the new name
5. Click **Save**

### Tip 4: Filter by Work Group
While the chart isn't filterable yet, you can:
- Sort summary table by Work Group column
- Look at the Y-axis labels in the Gantt chart
- Use Gantt chart zoom to focus on one contractor

## Future Enhancements

Planned additions:
- 🔄 Filter Gantt chart by work group
- 💰 Cost tracking by work group
- 📊 Work group performance metrics
- 🎨 Custom colors per work group
- 📈 Work group comparison reports

## Troubleshooting

### Q: My work group doesn't appear in the chart
**A:** 
- Check that the budget allocation was saved with work group name
- Go to Admin → Budget and verify the "Work Group" column has a value
- Refresh the Gantt Chart tab

### Q: All my activities show "Unassigned"
**A:**
- Work groups haven't been assigned yet
- Edit in Admin → Budget table
- Or re-import from Gantt chart with work group column

### Q: Can I change work groups after importing?
**A:** Yes!
- Go to Admin → Budget
- Find the row
- Edit the Work Group cell
- Save

### Q: Should I leave work group blank?
**A:** 
- It's optional
- Blank entries show as "Unassigned"
- Use only if you don't track by contractor/team

## Summary

Work Groups provide organizational flexibility:
- **Contractor Management**: Track work by contractor
- **Team Coordination**: See parallel activities
- **Schedule Control**: Monitor each team's timeline
- **Portfolio View**: Understand who's doing what when

The feature integrates seamlessly with the existing Gantt import and budget system.
