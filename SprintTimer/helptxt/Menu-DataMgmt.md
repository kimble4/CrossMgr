
[TOC]

# DataMgmt

## Link to External Excel Data...
Link to an external Excel file containing additional rider data.  The import code is identical to that used by CrossMgr, though some data columns are not used by the SprintTimer application.

This option opens up a Wizard to configure a link to an Excel sheet.  The Excel sheet must have a header row with the column names.  The Wizard takes you through the following steps:

1. Choose the Excel workbook containing your additional data.
1. Choose the sheet within the Excel workbook.
1. Choose how the CrossMgr's fields should correspond to the column names in your Excel sheet.  The CrossMgr fields are on the first row, and the Excel column names are the drop-downs in the second row.  In the drop-downs, select the Excel column corresponding to the CrossMgr field.
The Excel sheet may contain more fields than CrossMgr uses, and the column names in the sheet do not have to be named the same as CrossMgr's names.  You just have to tell CrossMgr what Excel columns correspond to its fields.  CrossMgr can usually use the same Excel sheet used as the rider sign-on sheet or pre-reg download.
1. Consider the __Initialize CrossMgr Categories from Excel EventCategory and Bib# columns__ option.  If selected, CrossMgr will use the __EventCategory__ and __Bib#__ columns to Add missing categories, Update existing categories with bib numbers from the spreadsheet or Delete empty categories.  All Categories are initially added as __Open__ gender and 00:00:00 __Start Offset__ (see [Categories][] for details).  Changes to Categories made in CrossMgr __except bib numbers__ will be preserved when data in the Excel spreadsheet is updated, provided the Category is not empty and deleted.
1. After the configuration, CrossMgr will show how many records it was able to read from the Excel workbook.

Additional external information will now be shown throughout CrossMgr including in Results, HTML and Excel output.

Specifying a spreadsheet creates a dynamic "link" to the Excel sheet - CrossMgr does not store the Excel data inside CrossMgr.  If data in the Excel sheet changes at any time (before, during or after the race), CrossMgr will automatically pick up the changes and display them the next time the screen is refreshed (for example, after switching between screens).

This allows you to start a race without the full details entered into Excel, or without an Excel sheet entirely.  As the race is underway, you can update the spreadsheet, and the changes will automatically be reflected in the results when CrossMgr next updates.

If you move the the Excel file to a different folder, you will have to update the link to tell CrossMgr where to find the new location.

CrossMgr supports the following fields from an external Excel sheet:

Field|Description
:----|:----------
Bib#|Required.  Rider's bib number in the race.  Bib numbers should be allocated in logical number ranges if there are multiple categories in the race (for example, 1-99 = one category, 100-199 = another category, etc.)
LastName|Optional.  Rider's last name.  CrossMgr will automatically capitalize the last name. Used for display only.
FirstName|Optional.  Rider's first name. Used for display only.
Team|Optional.  Rider's team. Used for display only.
Team Code|Optional.  Rider's 3-letter team. Used for UCI DataRiver Excel upload.
Category|Optional.  Rider's category.  This field is shown in the Results as information only, and does not have to match the rider's racing category.
EventCategory|Optional.  If __Initialize CrossMgr Categories from Excel Category and Bib# columns__ is selected, values in this column will be added to the race as a category (if not already present), and this rider's bib number will be included in that category.  If __Initialize CrossMgr Categories from Excel Category and Bib# columns__ is not selected, the rider's category will be determined by matching the number ranges of the categories (see [Categories][] for details).
Age|Optional.  Rider's age.  Used for display only.
License|Optional.  Rider's license.  This can be the UCI code, a national code, or a regional code.  CrossMgr uses this for display only.
UCI ID|Optional.  Rider's UDI ID.  Will be included in UCI DataRiver upload Excel sheets.
NatCode|Optional.  Rider's Nation Code.  Will be included in UCI DataRiver upload Excel sheets.
Tag1-9|Optional for manual input, required for chip input.  Rider's chip tag.
CustomCategory1-9|Custom categories to add this rider to.

To save space, CrossMgr may combine the first and last names into one field as "LASTNAME, Firstname".  In the scoreboard, it uses a further shorthand of "LASTNAME, F" where "F" is the first letter of the first name.

### Notes on __Initialize CrossMgr Categories from Excel EventCategory and Bib# columns__

This feature is useful if you do not have number ranges for different categories and you want to initialize the bib numbers and categories from the Excel spreadsheet using the __Bib#__,  __EventCategory__ and __Custom Category__ columns.  The behavior is as follows:

1. Initialization:  For each existing Category in CrossMgr, remove all Bib numbers.
1. New Category: If a category is found in the spreadsheet in the EventCategory column that does not exist in CrossMgr, add the new category (StartOffset=00:00:00, Gender=Open, Type=Wave), and insert the Bib# of that rider.
1. Update Category:  If a category is found in the spreadsheet that exists in CrossMgr, add the Bib# to that category.
1. Finalization:  After reading the Excel sheet, all empty Categories in CrossMgr are deleted.

The first time the Excel Link is read, you will get all the categories in the spreadsheet into CrossMgr as __Start Wave__ categories.
You can then organize your into __Components__ (see [Categories][]) and add combined __Start Waves__ to match the schedule and structure of your race.

Subsequence reads of the spreadsheet will use the existing Categories, but of course, the bib numbers be replaced based on the categories in the spreadsheet.
This means that changes you make to categories (laps, start offset, start wave, etc.) will be preserved when the Excel spreadsheet changes.

Alternatively, you can import a Category structure before linking to the spreadsheet (or use "File/New Next..." from an existing race).

__Big Warning__:  This option tells CrossMgr that the spreadsheet is the "source of truth" for rider categories.  This means that any changes to rider categories made in CrossMgr will be over-written the next time the spreadsheet is read.  So, if you use this feature, don't make change to rider categories in CrossMgr - always do this in Excel.

## Add sprint manually

Allows you to input new sprint timing data directly, eg. from a stopwatch or non-networked timing system.  Useful for correcting grevious errors.
