[TOC]

## Race Allocation

A **Round** may be split into more than one **Race** in order to limit the numbers of riders on the track at once for safety reasons.  This screen allows you to allocate riders to specific races on a round-by-round basis.

The currently selected **Round** can be changed at the top of the screen.  To change the **Season** or **Event**, go to the [Events][] screen.

To allocate racers to races:

1. Set the "**Number of races in this round**" field to the appropriate number, and press <Enter>.  Setting this to zero (the default) will de-allocate all racers and prevent the round being added to the sign-on sheet.  This may prove useful to somebody some day perhaps, in a somewhat bizarre set of circumstances.
1. A warning that current allocations will be lost if you change the number of rounds will appear.  Click OK.
1. All unallocated riders will initially be added to **Race 1**
1. You can move racers between races by using the options in the righ-click context menu.

* The "**Copy allocation**" button may be used to copy the allocation from another **Round** in the same **Event**.
* The "**Show machine/category details**" tickbox adds additional information columns to the tables.  You may need to turn this off if you have a large number of races and/or a very narrow window.
* A racer's **Machine** and **Categories** may be edited using the options in the context menu.  This will only affect their entry for the current Race/Round; other Rounds in the Event will maintain the details entered on the [EventEntry][] screen.  **This is intended to allow specific changes to be made during an Event**, eg. when a racer swaps machines or removes a fairing due to mechanical problems.
* Use the "**Write sign-on sheet**" button after making changes to write the updated CrossMgr sign-on sheet to disk.

All changes made on the **RaceAllocation** screen manipulate the in-memory database directly.  There is no '**Commit**' button.
