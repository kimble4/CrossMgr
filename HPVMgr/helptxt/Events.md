[TOC]

## Events

This screen displays a list of all **Seasons**, **Events** and **Rounds**:

#### Seasons
A **Season** represents a championship series, which consiststs of a number of individual **Events**.  A season will have a common set of [Categories][].

If you will be recycling bib numbers, it is not recommended to have more than one or two seasons per HPVMgr database file, as older sign-on sheets will become out of sync with the bib numbers in Riders list.

#### Events
An **Event** typically represents a day of racing.  It will contain at least one **Round**.  There will be a number of **Events** in a **Season**.

#### Rounds
A **Round** is an individual competition, for example a *30 minute criterium* or a *1-lap time trial*.  A **Round** may optionally be split into more than one **Race** to reduce the number of riders on the track simultaneously.

### Seasons/Events/Rounds tables
Click on table items to select a current **Season**, **Event** and **Round**, which will be highlighted in orange and displayed below the tables as the **Current selection**.  This will be used by the [EventEntry][] and [RaceAllocation][] screens.
Right-click to add, remove or rename items in the tables.

The "**Edit entries**" and "**Edit races**" buttons take you to the [EventEntry][] and [RaceAllocation][] screens respectively.

### Sign-on sheet
This sets the filename that the **CrossMgr sign-on sheet** of the currently selected **Event** will be written to.  (Each **Event** has a separate filename.)  Click "**Browse**" to select a directory and filename.

* The "**Write sign-on sheet**" button will write the currently selected sign-on sheet to disk.


All operations on the **Events** screen manipulate the in-memory database directly.  There is no '**Commit**' button.
