[TOC]

## Settings

This screen contains a few configurable options pertaining to the operation of HPVMgr:


### Fields

Field|Description
:----|:----------
Default font size|Allows you to adjust the font size used within HPVMgr.  Note that the appearance of window title bars and menus are determined by your operating system.  You will need to restart HPVMgr for changes to the font size to take effect.
Database filename|The filename of the current database.
Allocate bib numbers starting from|Sets the lowest bib number that will be suggested when creating new riders.
Copy tags with delimiters...|Inserts a '-' between each group of 4 characters when copying a tag number using the buttons on the [RiderDetail][] screen.  Useful for Impinj *MultiReader*, or readability in general.
Tag template|Configures a Python format string used to generate each of the default tag numbers of new riders.  Eg. use "`{:04d}`" for the rider's bib number in decimal with 4 leading zeros, or "`{:x}`" for the rider's bib number in hexadecimal without leading zeroes.
EventCategory template|Configures a Python format string used to generate the `EventCategory` fields in the CrossMgr sign-on sheet.  Eg. "`Race{:d}`" for `Race1`, `Race2` etc.
Seconds before first TT rider start|Sets the delay in seconds between the race clock starting and the first time trial rider's automatically allocated start time.
Seconds between TT riders|Sets the interval between time trial riders when automatically allocating start times.
Use abbreviated team names in sign-on-sheet|If selected, team names will be written to the sign-on sheet in the abbreviated form defined on the [Teams][] screen.  Otherwise the full team name is used.  Useful if there are teams with very long names.
Include para-cycling Factors in sign-on sheet|If selected, rider Factors will be displayed in the [EventEntry][] and [RaceAllocation][] screens, and an appropriate column will be included in the sign-on sheet.  Otherwise, Factors are not used.

The "**Commit**" button saves edits to the in-memory database, but does not write them to disk.
