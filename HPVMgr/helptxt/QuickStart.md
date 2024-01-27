[TOC]

## Quick Start

The HPVMgr application is designed to simplfy the BHPC's sign-on and tag management workflow, by dispensing with the need to manually edit sign-on sheets, and integrating the RFID tag writer so that tag numbers do not need to be tediously copied by hand.

### Setting up a new season

1. At the start of a new season, it is best to **make a copy of the existing database file**, preserving the previous season's sign-on data for reference.
1. Working on your new copy, switch to the [Events][] screen, and add the new **Season** to the seasons list.
1. Switch to the [Categories][] screen and set up the **Categories** for the new season.  (You may want to copy the categories from the previous season.)
1. Optionally delete previous seasons at this point.
1. Switch to the [Riders][] screen, and optionally delete any old riders who have not raced for a while.

### Setting up a new Event

1. Switch to the [Events][] screen, and select the relevant **Season**.
1. Right-click on the Events list and select "**Add new event**" from the context menu.  Enter a name for the event (eg. "`Hillingdon1`").
1. With the new **Event** selected, right-click on the **Rounds** list and select "**Add new round**" from the context menu.  Enter a name for the new round (eg. "`30min+1lap ACW`").
1. Repeat the above step until you have entered all the Rounds for the Event.
1. Enter a file name for the Sign-on sheet.  This is usually in the directory where the CrossMgr data files for the event will be kept.

### Entering riders in the Event

1. If you have new Riders who are not listed on the [Riders][] screen, add them to the database and fill in their details using the [RiderDetail][] page.
1. Select the **Event** on the [Events][] screen.
1. Switch to the [EventEntry][] screen.  The event name will appear at the top of the screen.
1. Select a **Rider** using the "**Bib**" drop-down, or by entering their name (last name first) in the "**Name**" field.
1. Select a previously-used **Machine** (or enter the name of a new one) in the "**Machine**" combobox.
1. Enter the name of the **Team** the rider is racing for in the "**Team**" field; leave blank if none.
1. Select the rider's [Categories][] for this event.
1. Click the "**Enter rider**" button to add them to the racers list.

### Allocating riders to races

1. Select the first round of the event on the [Events][] screen.
1. Switch to the [RaceAllocation][] screen.  The round name will appear at the top of the screen.
1. The **Number of races in this round** field will read `0`.  Change it to the appropriate number of races.  Don't worry about the warning at this point, as there is no allocation data to lose.
1. Using the right-click context menu options, move racers between races until you are happy with the allocation.  Usually slower and inexperienced racers are allocated to the first group (but exceptions may be made for logistical reasons).
1. Return to the [Events][] screen and select the next round.  Go to [RaceAllocation][] again.
1. You can use the "**Copy allocation**" button to copy the allocation you made for the previous round.  Otherwise, make whatever changes are needed to the number of races and allocations as described above.
1. When you are happy with all the allocations, click "**Write sign-on sheet**" to write the `.xlsx` file to disk for CrossMgr.

### Writing RFID tags

HPVMgr can control the Impinj reader directly in order to write RFID tags.  No more converting bib numbers to hexadecimal by hand!

1. Ensure that the **CrossMgrImpinj** application is not running, as only one application can use the RFID reader at a time.  (**CrossMgr**/**SprintTimer** do not talk to the tag reader directly and can be left minimised in the background.)
1. Switch to the [WriteTags][] screen and ensure the RFID reader is configured correctly.  (The settings should be saved after a successful connection to the reader.)
1. Click the "**Connect**" button to connect to the reader.  If this is not successful, you probably have an incorrect address or a network problem.
1. Select the **antenna** that you want to write tags with.
1. Ensure that "**Write to ALL tags within range**" is disabled, unless you know what you are doing!
1. With the connection to the reader established, switch to the [RiderDetail][] screen and select the rider whose tags you need to write.  (If you do not know their **Bib** number, you may find it easier to select the rider from the list on the [Riders][] screen first.)
1. Select a tag from the list.  The last-written dates may be hepful to avoid clashes with an existing tag on a spare helmet or similar.  (Unique tag numbers improve QuadReg performance and mean that stray tags can be excluded from a race retrospectively.)
1. Click the "**Write**" button.  You will be taken back to the [WriteTags][] screen, and the "**EPC to write**" field will be populated with the rider's tag number.
1. Ensure the tag you wish to write to is in place near the selected antenna, click "**Read Tags**" to refresh the inventory list.
1. Select the relevant tag by clicking on it in the list.  It will be added to the "**Destination tag**" field.
1. Click "**Write**" to write the new EPC to the tag.  If the write is successful, it will be highlighted green in the list.  If not, try moving the tag with respect to the antenna and trying again.
1. Go back to [RiderDetail][] and repeat the above steps for each additional tag/rider.  To streamline the process of writing large numbers of tags, a fresh tag inventory is performed automatically whenever you switch to the [WriteTags][] screen.


### Dealing with Machine or Category changes during an event

If a rider changes machine or category (eg. Swapping machines or removing a fairing due to mechanical problems), you have a choice:

#### If the change applies to the whole event:

1. Select the relevant Season and Event on the [Events][] screen.
1. Switch to the [EventEntry][] screen.
1. Delete the rider from the list using the right-click context menu.
1. Re-add the rider using their bib number or name, entering the new machine and category details.
1. Re-write the sign-on sheet.

#### If the change only applies to one round/race:

1. Select the relevant Season, Event and Round on the [Events][] screen.
1. Switch to the [RaceAllocation][] screen.
1. Right-click on the racer in the allocation list and select either "**Change machine**" or "**Change categories**" from the context menu.
1. This change will only affect the selected round/race; other rounds in the Event will continue to use the machine and categories as they were entered on the [EventEntry][] screen.
1. Re-write the sign-on sheet.

CrossMgr should pick up changes to the Sign-on sheet automatically the next time it needs to access that data.  If the race has finished, the easiest way to force a reload is to restart CrossMgr; you do not need to go through the *Link to External Excel Data* wizard again.

I would generally recommend making paper notes of changes and applying them retrospectively, rather than mucking about with the sign-on data during a race.
