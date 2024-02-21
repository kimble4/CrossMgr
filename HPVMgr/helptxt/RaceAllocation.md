[TOC]

## Race Allocation

A **Round** may be split into more than one **Race** in order to limit the numbers of riders on the track at once for safety reasons.  This screen allows you to allocate riders to specific races on a round-by-round basis.

The currently selected **Round** can be changed at the top of the screen.  To change the **Season** or **Event**, go to the [Events][] screen.

To allocate racers to races:

1. Set the "**Number of races in this round**" field to the appropriate number, and press <Enter>.  Setting this to zero (the default) will de-allocate all racers and prevent the round being added to the sign-on sheet.  This may prove useful to somebody some day perhaps, in a somewhat bizarre set of circumstances.
1. A warning that current allocations will be lost if you change the number of rounds will appear.  Click OK.
1. All **unallocated racers** will initially be added to **Race 1** and highlighted in **yellow**.
1. You can move racers between races by using the options in the right-click context menu.

* Select "**TT start times**" to enable pre-determined start times for a time trial.  A **StartTime** column wil be added to the sign-on sheet for this race.  Rider start times may be automatically allocated (see the relevant options in [Settings][]) or individually edited via the right-click context menu.  Clashing start times will be highlighted in **red**.
* The "**Copy allocation**" button may be used to copy the allocation from another **Round** in the same **Event**.  Note that any race-specific edits to riders' machines, categories or tags will also be copied.
* The "**Show machine/category details**" tickbox adds additional information columns to the tables.  You may need to turn this off to save space if you have a large number of races and/or a very narrow window.  When this is disabled, riders' machine and categories will be displayed as a tooltip.
* A racer's **Machine**, **Categories** and **Tags** may be changed using the options in the context menu.  This will only affect their entry for the current Race/Round; other Rounds in the Event will use the machine and categories entered on the [EventEntry][] screen, and the tags from the [RiderDetail][] screen.  **This is intended to allow specific changes to be made during an Event**, eg. when a racer swaps machines or removes a fairing due to mechanical problems, or if you have to exclude a stray tag from the race.  The edited machine and categories fields will be coloured **orange**; if tags have been edited, this will be indicated by the rider's bib number being coloured **orange**.
* If a racer does not exist in the [Riders][] database, their race allocation will be preserved but they will not be included in the sign-on sheet.  Such entries will be highlighted in **blue**.
* Use the "**Write sign-on sheet**" button after making changes to write the updated CrossMgr sign-on sheet to disk.

All changes made on the **RaceAllocation** screen manipulate the in-memory database directly.  There is no '**Commit**' button.
