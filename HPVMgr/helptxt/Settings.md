[TOC]

## Settings

This screen contains a few configurable options pertaining to the operation of HPVMgr:


### Fields

Field|Description
:----|:----------
Default font size|Allows you to adjust the font size used within HPVMgr.  Note that the appearance of window title bars and menus are determined by your operating system.  You will need to restart HPVMgr for changes to the font size to take effect.
Database filename|The filename of the current database.
Copy tags with delimiters...|Inserts a '-' between each group of 4 characters when copying a tag number using the buttons on the [RiderDetail][] screen.  Useful for Impinj *MultiReader*, or readability in general.
Tag template|Configures a Python format string used to generate each of the default tag numbers of new riders.  Eg. use "`{:04d}`" for the rider's bib number in decimal with 4 leading zeros, or "`{:x}`" for the rider's bib number in hexadecimal without leading zeroes.
EventCategory template|Configures a Python format string used to generate the `EventCategory` fields in the CrossMgr sign-on sheet.  Eg. "`Race{:d}`" for `Race1`, `Race2` etc.
Use abbreviated team names in sign-on-sheet|If selected, team names will be written to the sign-on sheet in the abbreviated form defined on the [Teams][] screen.  Otherwise the full team name is used.  Useful if there are teams with very long names.

The "**Commit**" button saves edits to the in-memory database, but does not write them to disk.