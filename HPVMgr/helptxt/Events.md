[TOC]

## Events

This screen displays lists of all **Seasons**, **Events** and **Rounds**:

#### Seasons
A **Season** represents a championship series, which consiststs of a number of individual **Events**.  A season will have a common set of [Categories][].

If you will be recycling bib numbers, it is not recommended to have more than one or two seasons per HPVMgr database file, as older sign-on sheets will become out of sync with the bib numbers in Riders list.

#### Events
An **Event** typically represents a day of racing.  It has a date (used for calculating rider ages and the default sign-on sheet filename), and will contain at least one **Round**.  There will be a number of **Events** in a **Season**.

#### Rounds
A **Round** is an individual competition, for example a *30 minute criterium* or a *1-lap time trial*.  A **Round** may optionally be split into more than one **Race** to reduce the number of riders on the track simultaneously.

### Seasons/Events/Rounds tables

There are three tables at the top of the [Events][] screen, listing **Seasons** (along with the number of events in each season), **Events** (along with the number of rounds in each event) and **Rounds** (along with the number of races in each round.

Click on table items to select a current **Season**, **Event** and **Round**, which will be highlighted in orange and displayed below the tables as the **Current selection**.  This will be used by the [EventEntry][] and [RaceAllocation][] screens.  For convenience, the currently selected **round** may also be changed from the [RaceAllocation][] screen.

Use the right-click context menu to add, remove, duplicate or rename items in the tables.  Event dates may be also be edited via the context menu option.  (There is no duplicate option for rounds: Create a new round and use the "**Copy Allocation**" button on the [RaceAllocation][] screen instead.)

The "**Edit entries**" and "**Edit races**" buttons take you to the [EventEntry][] and [RaceAllocation][] screens respectively.

### Sign-on spreadsheet
This sets the filename that the **CrossMgr sign-on sheet** of the currently selected **Event** will be written to.  (Each **Event** has a separate filename.)  Click "**Browse**" to select a directory and filename.

* To simplify moving databases between machines, the sign-on sheet filenames are stored relative to the path of the current database `.hdb` file.
* The "**Write sign-on sheet**" button will write the currently selected sign-on sheet to disk.

### Race Allocation HTML page
This sets the filename to write a web page of the race allocations for the currently selected **Event** to.  This can be printed out or published on the web so that racers know which group they have been allocated to.   (Each **Event** has a separate filename.)  Click "**Browse**" to select a directory and filename.

* To simplify moving databases between machines, the allocation web page filenames are stored relative to the path of the current database `.hdb` file.
* The "**Write race allocation**" button will write the currently selected race allocation to disk.


All operations on the **Events** screen manipulate the in-memory database directly.  There is no '**Commit**' button.
