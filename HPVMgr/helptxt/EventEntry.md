[TOC]

## Event Entry

This screen allows you to add riders to the currently selected [Event][Events], which will be shown at the top of the screen.

The table lists the currently entered racers.  You can delete racers from the list by right-clicking.

To add a racer to the event:

1. Select a **Rider** using the "**Bib**" drop-down, or by entering their name (last name first) in the "**Name**" field.  If the rider does not exist in the [Riders][] table, you will have to add them there first.
1. Select a previously-used **Machine** (or enter the name of a new one) in the "**Machine**" combobox.
1. Enter the name of the **Team** the rider is racing for in the "**Team**" field, leave blank if none.
1. Select the rider's [Categories][] for this event.  They will default to the values used last time their currently selected **Machine** was entered in an event.  No logic is applied to validate a given combination of categories, but an error message will appear if you exceed the CrossMgr limit of 10 `CustomCategory` fields per racer.
1. Click the "**Enter rider**" button to add them to the list.
1. If you have made a mistake, delete them from the list and re-add them.

* If you need to edit a racer's **Name**, **Gender**, **Age** or **Nationality**, make the relevant changes using the [RiderDetail][] screen.
* The "**Delete all**" button clears the racers list.

Adding and deleting racers manipulates the in-memory database directly.  There is no '**Commit**' button.