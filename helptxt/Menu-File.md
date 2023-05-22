
[TOC]

# File

## New...
Creates a new race.  Opens the Property dialog to configure a new race.

## New Next...
Creates a new race based on an existing one.  New Next... will keep the same Name, Organizer, Commissaire and other properties and increment the race number.
After the new race is created, you just need to check the start time, duration and categories.
This feature allows you to create the next race in the day very quickly.

## New from RaceDB...
Creates a new race based on an Excel file generated from RaceDB.

## Open...
Open an existing race.

## Open Next...
Open the next race based on the existing one.  CrossMgr will look for a race with the next race number in the same folder.

## Open from RaceDB...
Select and Open an Event defined in RaceDB.

CrossMgr needs to communicate with the RaceDB server to get the Event and Registration information.
If the server is running on the same computer as CrossMgr, it will find it automatically.
If the RaceDB server is running on a different computer, establishing a connection is easy:

Select the event you want to open (or take the default), then press the __Open Event__ button on the bottom left.

If the CrossMgr race does not exist, it will be created.  If it does exist, it will be opened.  In both cases the race Excel sheet will be updated from the database.

CrossMgr Races are created/opened from the __Race Folder Base__ under a folder including the competition name.

For more information about how to configure RaceDB and CrossMgr see [CrossMgrIntegration][].

## Restore from Original Input...
Restores all entries for a race from the original entered data.  CrossMgr automatically creates a backup .csv file that it write all entries to.  If you make a lot of changes by accident, you can restore from the original data here.

Although not recommended, some advanced users have edited the .csv file manually, then "restored" from it.

## Recent Files
Keeps track of the last few files opened so then can be opened again quickly.

## Close Race
Closes the current race.  All changes are written to disk.  Clears CrossMgr.

## Exit
Shuts down CrossMgr.  If a race is running, the race clock will pick up exactly where it left off when the CrossMgr race file is opened again.
