[TOC]

## Data

This displays all sprint data, in the order in which it was recorded.

### Enter Bib

This box allows you to record the bib number of a rider in real time.  You should aim to press Enter close to their arrival at the timing traps.

The current timing status is displayed to the right of the bib entry box, along with the apparent time difference (Δt) between the sprint timer unit's realtime clock and the computer's.  (A Δt of 0.2s or so is expected due to network latency.)


### Data table

This contains a number of columns:

Field|Description
:----|:----------
Count|A simple numerical count of recorded sprints
Time of Day|The date and time (in the computer's timezone) that the sprint was recorded.  This will usually be the time that the rider arrived at the T1 timing gate.  If the sprint timer's realtime clock is not synchronised to GPS, the time that the data arrived at the computer will be used instead, and this field will be coloured yellow.
Bib|The rider's race number.  This will be a best-effort attempt to correlate manual bib entries or RFID reads with the time of day that the rider triggered the timing gate.  If there are multiple possibilities, they will be listed in order of correlation and the field will be coloured light blue.  If no bib number is available it will be left blank.  This field can be edited retrospectively, in which case it will be coloured orange.
Name|The rider's name.  If a sign-on spreadsheet is used, this will be determined automatically based on their bib number (if you need to make changes to the rider's name, do so in the sign-on spreadsheet).  If not, the field can be edited retrospectively.
Machine|The rider's machine.  If a sign-on spreadsheet is used, this will be determined automatically based on their bib number (if you need to make changes to the rider's name, do so in the sign-on spreadsheet).  If not, the field can be edited retrospectively.
Team|The rider's team.  If a sign-on spreadsheet is used, this will be determined automatically based on their bib number (if you need to make changes to the rider's name, do so in the sign-on spreadsheet).  If not, the field can be edited retrospectively.
Seconds|Duration of the sprint, in seconds.  If the sprint timer unit does not maintain a GPS fix for the entire duration of the sprint, this time will be uncompensated and coloured yellow.  (In testing, GPS compensation is unlikely to make a difference for durations of less than a few minutes.)
Speed|The rider's speed.
Unit|The speed unit.  This can be reconfigured partway through the event.  To re-calculate a speed in the current unit, select "Recalculate speed..." from the context menu.
Note|An arbitrary text field for recording information specific to the individual sprint.
Distance|The distance (in metres) used to calculate the sprint speed.  This can be reconfigured partway through the event (see [Properties][RaceOptionsProperties]), in case the timing gates have to be moved, and may be edited, either directly or via the context menu.
System µs|Sprint duration in microseconds, as recorded by the sprint timer unit's system clock.  This is independent of the high-speed timer or GPS compensation, so is less accurate, but serves as a sanity check for the compensation algorithm.
Satellites|Number of satellites locked by the sprint timer unit's GPS receiver when the sprint was recorded.
Lat|GPS latitude in decimal degrees (north is positive).
Long|GPS longitude in decimal degrees (east is positive).
Ele|GPS elevation in metres.

Sprints may be deleted via the context menu.  If you're unsure, it may be safer to clear the Bib field (so that sprint will not be included in the results) and leave the timing data intact.

### Show bib entry / RFID read times

If enabled, this display rows (shaded grey) in the data table for *all* manual bib entries and RFID tag reads, irrespective of whether they correlate with a recorded sprint.

The Count and timing/GPS columns will be empty, and the Time of Day will be that returned by the RFID reader, or when the enter key was pressed.  If people loiter near the RFID aerials with live tags while recording is in progress, the table can become unwieldy!
