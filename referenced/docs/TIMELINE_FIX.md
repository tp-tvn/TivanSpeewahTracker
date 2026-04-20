# Timeline & Summary Fix — Date Format Normalization

## Problem

The timeline and summary were not populating because duration calculations were returning 0 days.

**Root Cause**: Dates were stored in two different formats:
- Some in `YYYY-MM-DD` format (e.g., "2026-01-15")
- Some in `DD/MM/YYYY` format (e.g., "13/05/2026")

The duration calculation only worked with `YYYY-MM-DD`, so it failed on `DD/MM/YYYY` dates and returned 0.

## Solution

### 1. Fixed Duration Calculation
Updated `calc_duration()` function to handle both date formats:
- First tries `YYYY-MM-DD` format
- Falls back to `DD/MM/YYYY` format
- Returns correct duration in days

### 2. Date Normalization
Created `normalize_dates_to_iso_format()` function that:
- Scans all date columns in the database
- Converts any `DD/MM/YYYY` dates to `YYYY-MM-DD`
- Runs automatically when Admin Budget page loads

### 3. Results
```
Before: 70 date fields in mixed formats
        Duration calculations: 0 days (failed)
        Timeline: Not populating
        Summary: Empty

After:  All 70 dates normalized to YYYY-MM-DD
        Duration calculations: 10, 22, 4, 31 days (correct)
        Timeline: Populating properly
        Summary: Showing all data
```

## What Changed

### db.py
1. **Enhanced `calc_duration()` function** (lines ~2860-2890)
   - Now handles both YYYY-MM-DD and DD/MM/YYYY formats
   - Tries both formats, returns duration if either works
   - Returns 0 only if both formats fail to parse

2. **Added `normalize_dates_to_iso_format()` function** (lines ~2827-2875)
   - Scans purpose_budgets table for non-ISO dates
   - Converts DD/MM/YYYY → YYYY-MM-DD
   - Updates all 6 date columns: drilling_start_date, drilling_end_date, earthworks_start_date, earthworks_end_date, fuel_start_date, fuel_end_date
   - Returns count of normalized fields

### app.py
- Added automatic normalization call in Admin Budget section (line ~857)
- Runs every time page loads
- Ensures any new imports are immediately normalized
- No user action needed

## Verification

All durations now calculate correctly:
```
Purpose: 2025 Diamond Metallurgical Drilling
  - Drilling: 31 days (2025-07-07 to 2025-08-07) ✓
  - Earthworks: 10 days (2026-07-03 to 2026-07-13) ✓
  - Fuel: 10 days (2026-07-03 to 2026-07-13) ✓

Purpose: 2026 DD A Vein HG Infill Deferred 2025
  - Drilling: 22 days (2026-05-13 to 2026-06-04) ✓
  - Earthworks: 2 days (2026-05-10 to 2026-05-12) ✓
  - Fuel: 25 days (2026-05-10 to 2026-06-04) ✓
```

## How It Works

### When You Load Admin Budget Page
1. Page calls `db.normalize_dates_to_iso_format()`
2. Function scans for any `DD/MM/YYYY` format dates
3. Converts them to `YYYY-MM-DD`
4. Updates database (one-time fix per unique date)
5. Subsequent loads skip dates that are already ISO format

### When Timeline/Summary Display
1. `calc_duration()` is called with start and end dates
2. Tries YYYY-MM-DD format first
3. If that fails, tries DD/MM/YYYY format
4. Calculates duration correctly in both cases
5. Timeline summary populates with correct day counts

## No User Action Needed

✅ Fix is automatic
✅ Runs when you visit Admin Budget page
✅ Handles both old and new date formats
✅ One-time normalization per date value

## Future Imports

Any new Gantt imports will use the Activity Type routing, which ensures dates are imported in `YYYY-MM-DD` format, so this issue won't happen again.

## Testing

```
Before: 14 bad drilling dates, 15 bad earthworks dates
After:  All dates in YYYY-MM-DD format

Duration Calculations:
  Before: 0 days (format error)
  After: 31, 10, 22, 4 days (correct) ✓

Timeline Rows: 42 (same)
Unique Purposes: 16 (same)
Summary Population: Working ✓
```

## Summary

Timeline and summary are now **fully functional**:
- ✅ Dates normalized to standard ISO format (YYYY-MM-DD)
- ✅ Duration calculations work for all dates
- ✅ Timeline displays correctly
- ✅ Summary populates all fields
- ✅ Automatic fix runs on page load
- ✅ No future issues with date formats
