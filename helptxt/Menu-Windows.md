
[TOC]

# Windows

## Bib Enter...
Shows the __Bib Enter__ dialog.  This small dialog allows you to manually enter bib numbers, similar to the [Record][] screen.

Use the __Bib Enter__ dialog when you wish to keep up another screen while doing manual bib entry.  For example, if you are working with an official, you may wish to show the [Passings][] screen at all times so you can check entered numbers.  Or, you watch the [Chart][] screen and correct missing splits.

You can move the __Bib Enter__ dialog to the most convenient part of the screen.

Clicking the __'...'__ buton (or pressing F6) reveals 5 'speed dial' bib entry buttons, for when you only need to manually enter a small number of bibs over and over (eg. due to a rider with a bad RFID tag).
Clicking the button will enter the respective bib immediately.  Alternatively, you can use the function keys F1-F5.
To set the bib for a button, enter the number, then right-click on the button, or press its respective function key while holding Ctrl.
Ctrl-P will populate the buttons with the bibs of the first 5 finishers in the current race.

If the race is a [TimeTrial][], an additional checkbox labelled __'Auto'__ will be displayed.  When this is enabled, a __Joystick Button 2__ event will cause the currently entered number(s) to be submitted, equivalent of pressing the Enter key.  (Note that *the dialogue does not need to have input focus* for this to happen, and that since the textbox is cleared after submission, repeated button events have no effect.)  You can use this to start riders automatically as they trigger a tape-switch or optical beam-break.  This feature can be used at the same time as the joystick trigger functionality in CrossMgrVideo.


## Missing Riders...
Shows the __Missing Riders__ window.  Functionally similar to __Add DNS from external Excel data__ in the [DataMgmt][] menu, this lists riders who are in the race, but do not (yet) have recorded times.

Use this early in the race to help work out whether any riders have bad RFID tags, so that you can enter their times manually.

Unseen riders (ie. those who are potential finishers, but have no recorded times) will be shown in yellow.  You can set their status to DNS or DQ from the right-click context menu, or double-click to open the [RiderDetail][] dialog.  Unseen riders will disappear from the list when a lap time is recorded for them.  (If riders are still unseen at the end on the race, and __Consider Riders in Spreadsheet to be DNS if no race data__ is selected in [Properties][], they will be marked DNS when the race is finished.)

If __Show non-finishers__ is selected, non-finishers (DNS etc.) who have no recorded times will be displayed in white.

Additionally, if the __Show unmatched riders__ box is checked, any riders who have recorded times but do *not* appear in the linked Excel spreadsheet will be included in the list, coloured in grey.  These are likely to be invalid bib numbers that have been manually entered by mistake, but may be confused riders or the result of a problem with the spreadsheet.  (As they do not appear in the spreadsheet, there will not be any RFID tag or additional data for these riders - see __Unmatched RFID Tags__ below.)  If you are sure the entries are spurious, you can delete the bib from the race via the context menu.

The __Resize__ button resizes the window to fit the table.

The context menu includes the option __Add to Bib Enter__: This adds the bib number to an empty 'speed dial' button in the Bib Enter window (if one is available), for efficient manual entry of lap times.

## Windows
Opens/Closes screens in a separate window.  This is especially useful if you are using multiple screens and wish to show additional CrossMgr information while entering data in the main screen, or you wish to display the [LapCounter][] on another screen to show the riders.

Choose the screen you wish to open in a separate window.  Drag it/resize it as needed.

For example, you can show the Animation while doing data entry.  Or Results.  Or the Chart.  Or the Situation screen.  Or the Lap Counter.  Any, or all of the above.  Your choice.

The separate screens have identical capabilities as the regular screens.

## Unmatched RFID Tags
This window shows unmatched RFID tags in a Chart.

This screen shows if there are riders with RFID tag recordings that do not have corresponding information in the linked Excel spreadsheet.

If the Excel sheet is updated later so that the missing tags are included, the __Unmatched RFID Tags__ will be added to the race automatically.

Take a close look at the laps in the __Unmatched RFID Tags__ screen.
If the times appear to be in regular laps for a rider, this is an indication that:

1. The rider is genuinely in the race, but has the wrong tag or a missing tag in the Excel sheet.  Fix your spreadsheet.  Then get CrossMgr to refresh, say, by switching screens.  It will then automatically pull the unmatched RFID tags data into the race.
1. The rider thinks he/she is in this race, but is actually in another race that starts at a different time.  You need to tell the rider to compete in the right event.
1. The rider is knowingly riding in the wrong race (and was stupid enough not to remove his/her tag!).  This is serious.

If there is no pattern to the reads, they are likely to be spurious and can be ignored (rider's tag too close to the finish line).

The unmatched tags can be exported to Excel.  This allows you to cut-and-paste the missing tags into another sheet, or to do further analysis on where the tags came from.

A maximum of 200 unmatched times will be recorded.

If your races is so messed up that this does not work, consider creating another race and importing all the tags (see [ChipReader][]).

