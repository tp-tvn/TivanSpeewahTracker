# Activity Type Routing — Assign Contractors to Correct Work Areas

## Problem Solved

**Before**: All work groups were assigned to the Drilling contractor field, even if they were Earthworks providers.

Example: MDM Earthworks
```
CSV Import:
  Item: MDM Earthworks
  Work Group: MDM
  Budget: $300,000

Previous Result (WRONG):
  Admin Budget Table showed:
  | Purpose | Drill WG | Drill $ | EW WG | EW $ |
  | MDM EW  | MDM      | $300k   |       | $0   |  <-- MDM in DRILLING field!
  
Problem: MDM is an earthworks contractor, not a drilling contractor!
```

**After**: Work groups are assigned to their correct activity type columns.

```
New Result (CORRECT):
  Admin Budget Table shows:
  | Purpose | Drill WG | Drill $ | EW WG | EW $   |
  | MDM EW  |          | $0      | MDM   | $300k  |  <-- MDM in EARTHWORKS field!
  
Benefit: MDM correctly identified as earthworks provider
```

---

## How It Works

Add an **Activity Type** column to your Gantt CSV. Two options:

### Option 1: Explicit Column (Most Clear)

Include `Activity Type` column with values: **"Drilling"** or **"Earthworks"**

```csv
Item Name,Start Date,End Date,Budget,Work Group,Activity Type
Tivan Presence - Phase 1,2026-01-15,2026-03-31,150000,Contractor A,Drilling
MDM Earthworks,2026-03-01,2026-05-31,300000,MDM,Earthworks
MDM Blasting,2026-02-15,2026-02-28,50000,MDM,Earthworks
```

### Option 2: Auto-Detection (If Column Not Provided)

System automatically detects from item name:

**Earthworks keywords**: "earthwork", "ew", "excavat", "blast", "grade"
```
"MDM Earthworks" → auto-detected as EARTHWORKS
"Blasting Work"  → auto-detected as EARTHWORKS
"Grade & Fill"   → auto-detected as EARTHWORKS
```

**Drilling keywords**: "drill", "bore", "core"
```
"Tivan Drilling"     → auto-detected as DRILLING
"Exploration Boring" → auto-detected as DRILLING
"Core Sampling"      → auto-detected as DRILLING
```

**Default**: If no keywords found, defaults to DRILLING

---

## Example: Complete Mixed Gantt Chart

### Your CSV with Activity Types

```csv
Item Name,Start Date,End Date,Budget,Work Group,Activity Type
Tivan Presence - Phase 1,2026-01-15,2026-03-31,150000,Contractor A,Drilling
Tivan Presence - Phase 2,2026-04-01,2026-06-30,200000,Contractor B,Drilling
MDM Earthworks,2026-03-01,2026-05-31,300000,MDM,Earthworks
MDM Blasting,2026-02-15,2026-02-28,50000,MDM,Earthworks
Contractor A Drilling,2026-01-10,2026-02-28,100000,Contractor A,Drilling
```

### Import Preview (Shows Separation by Activity Type)

The preview now shows how items are separated:

```
Purpose: Tivan Presence
  Activity: Drilling (2 items)
    Contractor: Contractor A + Contractor B
    Budget: $350,000 (150k + 200k)
    Timeline: Jan 15 to Jun 30

Purpose: MDM Earthworks
  Activity: Earthworks (2 items)
    Contractor: MDM
    Budget: $350,000 (300k + 50k)
    Timeline: Feb 15 to May 31

Purpose: Contractor A Drilling
  Activity: Drilling (1 item)
    Contractor: Contractor A
    Budget: $100,000
    Timeline: Jan 10 to Feb 28
```

### Admin Budget Table Result

```
| Purpose              | Drill WG | Drill $ | EW WG | EW $   |
|---------------------|----------|---------|-------|--------|
| Contractor A Drill   | Contrac..| $100k   |       | $0     |
| MDM Earthworks       |          | $0      | MDM   | $350k  |
| Tivan Presence      | Contrac..| $350k   |       | $0     |
```

**Correct Assignments**:
- ✓ MDM in Earthworks column ($350k)
- ✓ Contractor A in Drilling column ($350k from both Tivan and Contractor A Drilling)
- ✓ Contractor B in Drilling column ($200k from Tivan Phase 2)

---

## UI Changes During Import

### New Activity Type Column in Editor

When you upload the Gantt file, you see a new editable column:

```
Gantt Item                      | Start Date | End Date | Budget | Work Group | Activity Type | Map to Purpose
Tivan Presence - Phase 1        | 2026-01-15| 2026-03-31| 150000 | Contractor A | Drilling [dropdown] | Tivan Presence
MDM Earthworks                  | 2026-03-01| 2026-05-31| 300000 | MDM | Earthworks [dropdown] | MDM Earthworks
```

**Can Override**: You can change the Activity Type in the dropdown if auto-detection is wrong.

### Enhanced Preview Table

Shows Activity Type + Contractor assignment clearly:

```
Purpose          Activity    Items  Contractor    Budget      Start       End
Tivan Presence   Drilling    2      Contractor A  $350,000    2026-01-15  2026-06-30
MDM Earthworks   Earthworks  2      MDM           $350,000    2026-02-15  2026-05-31
```

Key insight: **Activity column shows where contractor is assigned**
- "Drilling" = assigned to drilling_work_group
- "Earthworks" = assigned to earthworks_work_group

### Detailed Breakdown Tab

Shows each item with its activity type for verification:

```
Purpose          Activity      Gantt Item              Contractor  Budget    Start       End
Tivan Presence   Drilling      Tivan Phase 1           Contractor A $150,000  2026-01-15  2026-03-31
Tivan Presence   Drilling      Tivan Phase 2           Contractor B $200,000  2026-04-01  2026-06-30
MDM Earthworks   Earthworks    MDM Earthworks          MDM         $300,000  2026-03-01  2026-05-31
MDM Earthworks   Earthworks    MDM Blasting            MDM         $50,000   2026-02-15  2026-02-28
```

---

## Column Names Supported

The system recognizes these column names for Activity Type:
- "Activity" ✓
- "Activity Type" ✓
- "Type" ✓
- "Work Type" ✓
- "Work_Type" ✓

Case-insensitive, spaces/underscores automatically converted.

---

## Valid Activity Type Values

Accepted values (case-insensitive):
- "Drilling", "DRILLING", "drilling", "Drill"
- "Earthworks", "EARTHWORKS", "earthworks", "EW", "Excavation"

Any other value triggers auto-detection from item name.

---

## Best Practices

### Do This:

1. **Include Activity Type column explicitly**
   ```csv
   Item Name,Activity Type,Work Group,Budget,Start,End
   Tivan Phase 1,Drilling,Contractor A,150000,...
   MDM Earthworks,Earthworks,MDM,300000,...
   ```
   - Crystal clear what each contractor does
   - No ambiguity or auto-detection needed
   - Other users understand the CSV structure

2. **Use consistent values**
   - Either "Drilling" or "Earthworks"
   - Not "Drill", "Drilling Work", "D", etc.
   - Makes auto-detection reliable

3. **Match contractor names to purpose names**
   ```csv
   Tivan Presence - Phase 1,Drilling,Contractor A,...
   ```
   Maps to purpose: "Tivan Presence"
   Contractor A goes to: drilling_work_group
   ✓ Correct

4. **Different contractors for same purpose if needed**
   ```csv
   Tivan Phase 1,Drilling,Contractor A,...
   Tivan Phase 2,Drilling,Contractor B,...
   Tivan Earthworks,Earthworks,MDM,...
   ```
   All map to "Tivan Presence"
   Result: Drilling has both Contractor A and B; Earthworks has MDM

### Don't Do This:

1. **Omit Activity Type and rely only on auto-detection**
   - Works, but not guaranteed
   - Item names might not contain keywords
   - Could assign wrong contractor

2. **Mix formats in same column**
   ```csv
   Activity Type
   Drilling
   EW
   Earthwork
   ```
   Inconsistency makes it harder to understand

3. **Create purposes for each contractor**
   ```csv
   (WRONG - creates extra clutter)
   Tivan Drilling,Drilling,Contractor A,...
   Tivan Earthworks,Earthworks,MDM,...
   (These should both map to "Tivan Presence")
   ```

---

## Migration: Existing Gantt Charts

If your Gantt CSV doesn't have Activity Type column:

### Option A: Add It (Recommended)
1. Open your Gantt CSV in Excel
2. Add new column: "Activity Type"
3. Fill in: "Drilling" or "Earthworks" for each item
4. Save and re-import

### Option B: Use Auto-Detection
1. Import as-is (no column needed)
2. System detects from item names
3. Manual correction in editor if needed
4. Override in "Activity Type" column during import

---

## Troubleshooting

### "Activity Type shows wrong value"

**Solution**: Override in the import editor

1. During Gantt import, see Activity Type column
2. For any incorrect assignment, click the dropdown
3. Change to correct value ("Drilling" or "Earthworks")
4. Proceed with import

### "Contractor appears in wrong field in Admin Budget"

**Cause**: Activity Type wasn't set or was set incorrectly

**Solution**: 
1. Go back to Gantt import
2. Check Activity Type column
3. Re-import with correct activity types
4. Or manually edit in Admin → Budget table

### "Auto-detection didn't work"

**Reason**: Item name doesn't contain keyword

Example: "Phase 1" doesn't contain "drilling" or "earthworks"
- Will default to Drilling

**Solution**:
1. Add Activity Type column explicitly
2. Or edit during import in Activity Type dropdown

---

## Summary

The Activity Type routing feature ensures:

✓ **MDM** and other earthworks contractors assigned to **Earthworks** columns
✓ **Drilling contractors** assigned to **Drilling** columns
✓ **Clear visibility** in preview showing which activity each contractor handles
✓ **Flexible**: Can override auto-detection during import
✓ **No manual data entry**: Activity Type read directly from CSV

Result: Correct contractor-to-activity assignment in your budget table!

---

## Example: Before and After

### Before (All contractors in Drilling field)
```
Tivan Presence
  Drill WG: Contractor A
  Drill Budget: $150,000
  
MDM Earthworks
  Drill WG: MDM          <-- WRONG! MDM is not a drilling contractor
  Drill Budget: $300,000
```

### After (Contractors in correct fields)
```
Tivan Presence
  Drill WG: Contractor A
  Drill Budget: $150,000
  EW WG: (empty)
  EW Budget: $0
  
MDM Earthworks
  Drill WG: (empty)
  Drill Budget: $0
  EW WG: MDM            <-- CORRECT! MDM in earthworks field
  EW Budget: $300,000
```

Much clearer!
