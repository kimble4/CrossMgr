
[TOC]

# Tools

## Start Recording

Analogious to 'Start Race' in CrossMgr.  This starts the race clock, and begins listening for data from the sprint timer unit, RFID reads (if enabled) from the tag reader, and manual bib entries.  If enabled, triggers will be sent to CrossMgrVideo.

## Finish Recording

Analogous to 'Finish Race' in CrossMgr.  This stops the race clock, and data from the sprint timer unit and RFID reader will be ignored.

## Resume Recording

This simply re-starts the race clock, in case you selected 'Finish Recording' too soon.

## Copy Log File to Clipboard
Copies the last 1,000 lines of the SprintTimer log file to the clipboard.
The log can then be pasted into an email.

When reporting problems with SprintTimer, please include the log.
It contains important diagnostics to find the problem.

## Reset Sprint Timer

Sends a 'reset' command to the sprint timer unit.  If a sprint is in progress, the time data will be lost.
