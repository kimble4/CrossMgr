## Properties

This is where the SprintTimer is configured.  Many pages are similar or identical to those in CrossMgr.

### General Options
This is where you configure general info about the event.

Property|Description
:-------|:----------
Event Name|Name of the event - also used for the event's filename (along with the Race #).  Multiple races in the day will have the same Event Name, but with different race numbers.
Long Name|Long name of the event.  The __Long Name__ is useful if the __Event Name__ has organizers and sponsors that make the name unwieldy, or contain characers that don't work in file names.  For example "2017 National Championships p/b Trend Setter Organizer" is cumbersome to work with and contains a "slash" that can't be in a filename.  The __Long Name__ will be shown on all results, spreadsheets and web output if it is defined.  Otherwise the __Event Name__ is used.
Date|Date of the race.  Used in the filename and all output.
Race #|The number of the race in the day at the event.  Also used in the race filename.  This is automatically incremented when you do "File/New Next..."
Scheduled Start|Scheduled start of the race.  This is used in the results output.  Of course, the race could actually start at a different time.
Race Minutes|The __global__ number of minutes in the race for timed races (like CycloCross).  See __Notes__ below.
Discipline|The type of race (default Sprints).  This should reflect the type of race (Road, Mountain Bike, Criterium, etc.)
Organizer|Organizer of the race.  Included in the HTML results output.
Commissaire|The name of the race official.
Memo|Anything you wish to type in here (weather conditions, your mood, etc.).  This is saved with the race but does not appear on any output.

### Race Options
Options pertaining to results generation.

Property|Description
:-------|:----------
Handle multiple attempts by using|If more than one valid sprint is recorded for a rider, this selects which one is used to calculate the [Results][] table.  Note that "Shortest time" and "Longest time" only give fair results if *all* sprints are recorded over the same distance.  Meanwhile "Fastest speed" and "Slowest speed" rely on a distance being recorded in the [Data][] table for each sprint; sprints with no distance will be ignored.  "First attempt" and "Last attempt" are hopefully self-explanatory.
Speed Unit|Speed unit used when calculating [Results][]
Show Lap Notes in HTML Output|Whether to include the contents of the "Note" field in the web page.
Min. Possible Lap Time|Filtering of minimum sprint time, as used in CrossMgr.  Possibly useful to filter out glitches and timer tests?
Allocate Sequential Bib Numbers|If racers do not have allocated race numbers, this may be useful for processing results.
Starting from #|The next bib number to allocate in sequence.

### Sprint Timer
Configuing the connection to the sprint timer unit.

Property|Description
:-------|:----------
Use sprint timer to obtain precise times|Select this to enable TCP/IP communications with the sprint timer unit.  Normally this would be enabled.
Remote IP Address|IP address of the sprint timer.  This would normally be displayed on the front panel.
Remote Port|Default is 10123
Sprint trap distance|Distance between the T1 and T2 timing gates.  This is in metres, regardless of what unit is being used to display results.
Timer input test|Put the sprint timer unit into test mode.  The T1 and T2 LEDs will reflect the state of their inputs in approximately real-time, for testing the senors and wiring.  The optional "play sounds" setting may be helpful when aligning optical beam-breaks.
Save extended debugging info to log|For debugging communication issues with the sprint timer unit.  This will make the log file very large.

### RFID
Configuring the RFID tag reader.

Property|Description
:-------|:----------
Use RFID reader to identify riders|Enables the RFID system
RFID aerial position|Selects whether the RFID aerials are physically aligned with the T1 or T2 timing gate, for correlation of tag reads with sprint times.
Associate tag reads within n seconds of trap time|Number of seconds before/after the sprint to consider early/late tag reads.
Trigger Camera on RFID read|Whether to send an *additional* trigger to CrossMgrVideo when the RFID tag is read.  This is useful, as the trigger from the sprint timer unit does not always contain rider identification data.
Setup/Test Rfid Reader|Launches the [Chip Reader Setup][ChipReader] dialog.

### (S)FTP

Options for SFTP and FTP upload:

Option|Description
:-------|:----------
Protocol|Select one of FTP, FTPS (FTP with SSL encryption) or SFTP (SSH File Transfer Protocol)
Host Name|Name of the FTP/SFTP host to upload to.  In SFTP, CrossMgr also loads hosts from the user's local hosts file (as used by OpenSSH).
Port|Port of the FTP/SFTP host to upload to (resets to default after switching between FTP and SFTP).
Upload files to Path|The directory path on the host you wish to upload the files into.  If blank, files will be uploaded into the root directory.
User|FTP/SFTP User name
Password|FTP/SFTP Password
Automatically Upload Results During Race|If checked, CrossMgr will automatically upload live results during the race.
URL Path|URL where the results will be visible on the web server

#### Test Connection
Makes a connection to the FTP server, but does not attempt to upload anything.

#### Do Upload now
Immediately performs a (blocking) upload.

### Batch Publish
See [Publish][]

### Notes
Text that will appear in the HTML output.  Text entered here will be shown as-is in the HTML web page, including line breaks.  Describe weather conditions, give credit to the CrossMgr operator and number caller, or make notes about race participants.

For example:

    Notes for {=EventName}:
    
    Warning to the following riders for incorrect number placement:
    {=BibList 113, 117, 164}
    
    Special thanks to the following riders for helping out after the race:
    {=BibList 142, 153, 163}

This example uses "variables" which insert race information without having to retype it again.  Variables have the form "{=VariableName}" (no spaces around the "{", "=" or "}").
"BibList" is a special variable that takes a list of bib numbers and expends them into a list (more on that later).

You can also embed Html tags in notes to get nicer formatting or more powerful features, like hyperlinks.  To do so, your note must then start with `<html>` and end with `</html>`.  With Html tags, you can specify a hyperlink to a URL with `<a href="http://XXX">HyperLink</a>`, use a list with `<ol></ol>`, etc.  When using Html, you control your own line breaks: insert `<br/>` where you want a newline.

For example:

    <html>
    <h2>Big Race</h2>
    <p>
    Organizer: <strong> <a href="mailto:organizer.email@gmail.com">Email: Awesome Organizer</a> </strong> <br/>
    CrossMgr Operator: <strong> <a href="mailto:operator.email@gmail.com">Email: Awesome Operator</a> </strong> <br/>
    </p>
    </html>

Notes get even more powerful with html and variables.  For example:

    <html>
    <h2>{=EventName}</h2>
    <h2>{=City}, {=StateProv}, {=Country}</h2>
    <p>
    Organizer: <strong> <a href="mailto:organizer.email@gmail.com">Email: {=Organizer}</a> </strong> <br/>
    Commissaire: <strong> {=Commissaire} </strong> <br/>
    Start Time: <strong> {=StartTime} </strong> <br/>
    Start Method: <strong> {=StartMethod} </strong> <br/>
    </p>
    <p>
    Warning to the following riders for incorrect number placement:
    {=BibList 113, 117, 164}
    </p>
    <p>
    Special thanks to the following riders for helping out after the race:
    {=BibList 142, 153, 163}
    </p>
    </html>

Take notice of the "{=BibList 113, 117, 164}" variable.
"BibList" takes a list of bib numbers and expands them into a list with the "Bib: Last Name, First Name, License, UCI ID, Team" fields from the spreadsheet.  The "Bib", "BibList" and "BibTable" variables  make it easy to add full information about riders (see below for more details).

Variables can be conveniently inserted from the "Insert Variable..." button.  This is also helpful if you forget a variable name.

Variable names are case sensitive, so be careful.  The supported variables are:

Variable|Value
:-------|:----
{=EventName}|Name of the event
{=EventTitle}|Title of the event
{=RaceNum}|Race number
{=City}|City
{=StateProv}|StateProv
{=Country}|Country
{=Commissaire}|Commissaire
{=Organizer}|Organizer
{=Memo}|Memo
{=Discipline}|Discipline
{=RaceType}|"Time Trial" if the the Time Trial flag is set, otherwise "Mass Start"
{=RaceDate}|Date of the race
{=InputMethod}|Data input method.  Either "RFID" or "Manual".
{=StartTime}|Actual start time of the race if the races is started, else the "Scheduled Start Time" from General Options.
{=StartMethod}|Either "Automatic: Triggered by first tag read" or "Manual"
{=CameraStatus}|Either "USB Camera Enabled" or "USB Camera Not Enabled"
{=PhotoCount}|Number of photos taken during the race.  Will be zero if the usb camera is not enabled.
{=ExcelLink}|The file and sheet name of the Excel sheet linked to this race.
{=GPXFile}|The file name of the course in GPX format.
{=Bib NNN}|Expand the bib number NNN to show rider information including "Bib: Last Name, First Name, License, UCIID, Team".
{=BibList AAA, BBB, CCC, DDD, ...}|Expands the comma-separator bib numbers into a list showing "Bib: Last Name, First Name, License, UCIID, Team" in each line.
{=BibTable AAA, BBB, CCC, DDD, ...}|Expands the comma-separator bib numbers into a table showing "Bib: Last Name, First Name, License, UCIID, Team" in each row.
{=Path}|Full path name of the race file.
{=DirName}|Directory of the race file (no file name).
{=FileName}|File name of the race file (no directory name).

### Camera
Requires __CrossMgrVideo__

#### USB Camera Options
Select whether the camera should be triggered by the T1 or T2 timing gate, or disabled.
It may additionally be triggered by RFID reads - see the [RFID][] settings.

### Race Clock
The BHPC Race Clock uses the [CrossMgr lap couter WebSocket interface][https://github.com/kimble4/CrossMgrLapCounter], which is extended here for displaying sprint results in real time.  The clock should be configured to connect to the IP address of the SprintTimer computer.

Property|Description
:-------|:----------
Sprint Data Timeout|Number of seconds to display sprint data for after it happens.
Show sprint time on race clock|Whether to include the sprint time.
Show sprint speed on race clock|Whether to include the sprint speed, if available (note that the 7-segment display can't indicate the unit).
Show rider bib on race clock|Whether to include the rider's bib number, if available.

### Files/Excel
Shows the current data file name, and details of the [linked Excel sheet][External Excel].  Category and Template files are not (currently) implimented.

