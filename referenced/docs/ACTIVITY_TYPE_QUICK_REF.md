# Activity Type Routing — Quick Reference

## The Problem You Had

MDM (Earthworks contractor) was being assigned to the **Drilling** contractor field.

```
BEFORE (WRONG):
Purpose: MDM Earthworks
  Drill WG: MDM        <-- MDM is not a drilling contractor!
  Drill $: $300,000
  EW WG: (empty)
```

## The Solution

Add an **Activity Type** column to your Gantt CSV.

```csv
Item Name,Start Date,End Date,Budget,Work Group,Activity Type
Tivan Phase 1,2026-01-15,2026-03-31,150000,Contractor A,Drilling
MDM Earthworks,2026-03-01,2026-05-31,300000,MDM,Earthworks
```

## Result

```
AFTER (CORRECT):
Purpose: Tivan Presence
  Drill WG: Contractor A  <-- Drilling contractor in Drilling field
  Drill $: $150,000
  EW WG: (empty)

Purpose: MDM Earthworks
  Drill WG: (empty)
  EW WG: MDM              <-- Earthworks contractor in Earthworks field
  EW $: $300,000
```

---

## How to Implement

### Step 1: Add Activity Type Column to Your Gantt CSV

Either:
- **Option A**: Add explicit "Activity Type" column with "Drilling" or "Earthworks"
- **Option B**: Let system auto-detect from item names (has keywords like "drill", "earthwork", "blast")

### Step 2: Upload as Usual

1. Admin → Budget → Import from Gantt Chart
2. Upload your CSV
3. See new "Activity Type" column in editor
4. Can override if auto-detection is wrong

### Step 3: Review Preview

Preview now shows **Activity** column:
```
Purpose         Activity      Items  Contractor  Budget
Tivan           Drilling      2      Contractor A $350k
MDM Earthworks  Earthworks    2      MDM         $300k
```

### Step 4: Import

Contractors automatically assigned to correct columns!

---

## Column Names That Work

Any of these (case-insensitive):
- "Activity Type"
- "Activity"
- "Type"
- "Work Type"
- "Work_Type"

---

## Valid Activity Type Values

- **Drilling**: "Drilling", "DRILLING", "Drill", "D"
- **Earthworks**: "Earthworks", "EW", "Excavation", "Blast"

Anything else = auto-detect from item name

---

## Auto-Detection Keywords

**Auto-detects as EARTHWORKS**:
- "earthwork", "excavat", "blast", "grade", "ew"

**Auto-detects as DRILLING**:
- "drill", "bore", "core"

If no keywords found → defaults to DRILLING

---

## Examples

### With Explicit Activity Type

```csv
Item,Start,End,Budget,Work Group,Activity Type
Tivan Phase 1,2026-01-15,2026-03-31,150000,Contractor A,Drilling
MDM Earthworks,2026-03-01,2026-05-31,300000,MDM,Earthworks
```

Result:
- Contractor A → Drilling field ✓
- MDM → Earthworks field ✓

### Auto-Detection (No Activity Type Column)

```csv
Item,Start,End,Budget,Work Group
Tivan Drilling Phase 1,2026-01-15,2026-03-31,150000,Contractor A
MDM Earthworks,2026-03-01,2026-05-31,300000,MDM
```

Result:
- "Tivan Drilling" contains "Drilling" → Drilling field ✓
- "MDM Earthworks" contains "Earthworks" → Earthworks field ✓

### Mixed with Override During Import

```csv
Item,Start,End,Budget,Work Group
Phase 1,2026-01-15,2026-03-31,150000,Contractor A
MDM Work,2026-03-01,2026-05-31,300000,MDM
```

During import:
- "Phase 1" → defaults to Drilling (no keywords)
  - You can override in Activity Type dropdown if wrong
- "MDM Work" → auto-detects as ? (ambiguous)
  - You manually select "Earthworks" in dropdown
  - Proceeds with correct routing

---

## In the Admin Budget Table

### Before Activity Type Routing
```
| Purpose | Drill WG | Drill $ | EW WG | EW $ |
| MDM     | MDM      | $300k   |       | $0   |  <-- PROBLEM
```

### After Activity Type Routing
```
| Purpose | Drill WG | Drill $ | EW WG | EW $ |
| MDM     |          | $0      | MDM   | $300k|  <-- CORRECT
```

---

## Tips

1. **Most important**: Use explicit Activity Type column
   - Eliminates ambiguity
   - Other people understand your CSV

2. **For standard contractors**:
   - Drilling companies → Activity Type = "Drilling"
   - Earthworks/EW companies → Activity Type = "Earthworks"
   - Equipment rental → depends on usage
   - Concrete → typically "Earthworks"

3. **If uncertain during import**:
   - Use dropdown to change Activity Type
   - See instant preview update
   - No need to re-upload

4. **Multiple contractors per purpose**:
   ```csv
   Tivan Phase 1,2026-01-15,2026-03-31,150000,Contractor A,Drilling
   Tivan Phase 2,2026-04-01,2026-06-30,200000,Contractor B,Drilling
   Tivan Earthworks,2026-03-01,2026-05-31,300000,MDM,Earthworks
   ```
   All map to "Tivan Presence"
   → One row with multiple contractors in different fields

---

## FAQ

**Q: What if I don't include Activity Type column?**
A: System auto-detects from item name. Override in editor if needed.

**Q: Can I change Activity Type after import?**
A: Yes. Go to Admin → Budget and edit manually. Or re-import with correct Activity Type.

**Q: What if an item has both Drilling and Earthworks work?**
A: Split into two CSV rows with different Activity Types, both mapping to same purpose.

**Q: Does Activity Type affect how items appear on Gantt?**
A: No, but it affects which work group is shown. You'll see correct contractor grouping.

**Q: Can I mix "Drilling" and "Earthworks" for same contractor?**
A: Yes. Example: Contractor A does both drilling and earthworks.
```csv
Tivan Phase 1,2026-01-15,2026-03-31,100000,Contractor A,Drilling
Tivan Prep Work,2026-02-01,2026-02-28,50000,Contractor A,Earthworks
```
→ Contractor A appears in both Drill WG and EW WG fields

---

## Your MDM Example

**Before**:
- MDM wrongly assigned to drilling_work_group

**Now**:
- Add Activity Type column with "Earthworks" for MDM items
- During import, see:
  ```
  MDM Earthworks | Earthworks | MDM | $300k
  ```
- After import:
  ```
  Purpose: MDM Earthworks
    Drill WG: (empty)
    EW WG: MDM ✓
    EW $: $300k ✓
  ```

Perfect!
