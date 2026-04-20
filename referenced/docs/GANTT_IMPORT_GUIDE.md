# Gantt Chart Import Guide

## Overview
The Gantt chart import feature allows you to automatically populate budget allocation start/end dates from a Gantt chart spreadsheet. This eliminates the need for manual date alignment and supports multiple instances of the same purpose (different contractors, different time periods).

## How It Works

### Step 1: Prepare Your Gantt Chart CSV/Excel
Export your Gantt chart as a CSV or Excel file with the following columns:
- **Item Name** (required): The activity/item name from your Gantt chart
- **Start Date** (required): YYYY-MM-DD format
- **End Date** (required): YYYY-MM-DD format
- **Budget** (optional): The budget amount for this activity

Example:
```
Item Name,Start Date,End Date,Budget
Tivan Presence - Phase 1,2026-01-15,2026-03-31,150000
MDM Earthworks - Mobilisation,2026-02-01,2026-02-28,50000
MDM Earthworks - Main Works,2026-03-01,2026-05-31,300000
```

Column names are flexible - the system looks for common keywords:
- **Name columns**: item, name, title, activity
- **Start columns**: start, start_date, begin
- **End columns**: end, end_date, finish
- **Budget columns**: budget, amount, cost

### Step 2: Upload in Admin Panel
1. Go to **Admin → Budget**
2. Scroll to **"📊 Import from Gantt Chart"** section
3. Click **"Upload Gantt chart (CSV)"** 
4. Select your prepared CSV or Excel file

### Step 3: Map Items to Purposes
The system will parse your file and display all items in a table with columns:
- **Gantt Item**: The item name from your file
- **Start Date**: Parsed start date
- **End Date**: Parsed end date
- **Budget**: The budget amount
- **Map to Purpose**: *Your selection here*

In the "Map to Purpose" column:
- Click the cell and select which purpose this Gantt item belongs to
- You can assign multiple items to the same purpose (for different time periods)
- Leave blank to skip items you don't want to import

### Step 4: Review Preview
Below the mapping table, you'll see a "Preview of Budget Allocations to Create" showing:
- **Purpose**: The mapped purpose
- **Start Date**: When this budget period starts
- **End Date**: When it ends
- **Budget ($)**: The budget amount
- **Source**: Which Gantt item created this

This preview helps you verify the mapping is correct before importing.

### Step 5: Import
Click **"✅ Import Gantt Chart Allocations"** to create the budget allocations.

The system will:
1. Create a new budget allocation for each mapped item
2. Set the drilling budget to the amount from your Gantt chart
3. Store the Gantt item name as the source in notes
4. Refresh the budget table above so you can see the new allocations immediately

## Multiple Instances Per Purpose

If a purpose appears multiple times in your Gantt chart (different contractors, different time periods), the system handles this naturally:

```
Item Name,Start Date,End Date,Budget
Tivan Presence - Contractor A,2026-01-15,2026-03-31,150000
Tivan Presence - Contractor B,2026-04-01,2026-06-30,200000
```

When you map both to the purpose "Tivan Presence", the system creates **two separate budget allocations**:
1. Tivan Presence (2026-01-15 to 2026-03-31): $150,000
2. Tivan Presence (2026-04-01 to 2026-06-30): $200,000

This allows the system to:
- Track spending against the correct budget period
- Detect which allocation a PLOD matches when assigning costs
- Project spending and flag overspend for each period independently

## Column Name Flexibility

The system is flexible with column names. These would all work:

| Works | Reason |
|-------|--------|
| Item Name, Activity Name, Title | Contains "item", "name", or "activity" |
| Start Date, Begin Date, Date From | Contains "start", "start_date", or "begin" |
| End Date, Finish Date, Date To | Contains "end", "end_date", or "finish" |
| Budget, Amount, Cost | Contains "budget", "amount", or "cost" |

## Date Format Requirements

Dates should be in **YYYY-MM-DD** format or compatible Excel date format. The system automatically:
- Strips time components if present
- Converts Excel date serial numbers
- Handles ISO 8601 format variations

## Troubleshooting

### "Could not identify required columns"
- Verify your file has columns containing these keywords:
  - At least one of: item, name, title, activity
  - At least one of: start, start_date, begin
  - At least one of: end, end_date, finish

### Date parsing errors
- Check dates are in YYYY-MM-DD format or valid Excel date
- Ensure no extra characters (spaces, quotes) around dates
- If using Excel, export as CSV and re-upload

### Mapping not working
- Make sure you've imported drillhole purposes first
- The purpose list in the "Map to Purpose" dropdown comes from your existing purposes
- Create new purposes in the "Drillhole Purposes" section if needed

## After Import

Once imported, the budget allocations:
- Appear in the main budget allocation table
- Are available for cost matching (PLODs will match to the correct period)
- Enable date-based budget period forecasting
- Allow separate tracking of spending by contractor/period

You can still edit the imported allocations in the main table (Start Date, End Date, Budget amounts, etc.) if needed.
