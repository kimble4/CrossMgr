[TOC]

# BHPC Workflow

This is intended to be a step-by-step guide to timing a BHPC event.  If you are not the [British Human Power Club](https://www.bhpc.org.uk), this may still be informative, but our somewhat arcane classification and scoring methods mean it diverges from typical CrossMgr workflow in important ways.

# Setting up the files

## File structure conventions

At the time of writing, race data on the timing laptop is kept in "`C:\Users\BHPC\Documents\BHPC Racing\`".  Each racing season (year) will have its own directory, with sub-directories named `CrossMgr`, `Photos` and `SeriesMgr`.  Each of these will have sub-directories for each event (day of racing).

Directory|Used for...
:---|:------
`CrossMgr`|Files pertaining to organising and timing races.  This includes sign-on spreadsheets, race files, and generated results.  This is also a reasonable place to keep things like running order posters and any supplementary data such as GPX files, raw impinj logs and any media files that pertain to timing the race (eg. if you've videoed a finish, or scanned a handwritten results sheet).
`Photos`|Published finish-line photos from CrossMgrVideo.
`SeriesMgr`|This for SeriesMgr data and generated points tables.

This structure is reproduced on the BHPC Google Drive.

The first thing you will need to do to set up a race, is create a directory for the event under `C:\Users\BHPC\Documents\BHPC Racing\$year\CrossMgr\`, named something like "`07 Darley Moor"`

## Creating a Sign-on sheet

**This section intentionally left blank**; we intend to revamp the Sign-on software, so there's little point in documenting the old one.

Suffice to say that you should use the sign-on system to generate an Excel file containing a sheet for each Race, with columns for the rider's name, RFID tag number and race categories.  See [DataMgmt][] for more details of the format.


## Creating a CrossMgr race file

**The easiest way to create a CrossMgr race file is to open a known-good previous race and select [New Next][File] from the file menu.  This will preserve most of the settings of the previous race, so you only have to alter those that differ.**

To create a new CrossMgr race from scratch:

1. Open CrossMgr, and select [New][File] from the file menu.  The **Configure Race** dialog will appear.
1. Enter an event name.  Avoid the use of spaces here, as this will be used for the filename (spaces in filenames can unnecessarily complicate matters when files are uploaded to the web).
1. Use the **Browse...** button to set **Race File Folder** to the directory you created, eg. "`C:\Users\BHPC\Documents\BHPC Racing\2025\CrossMgr\07 Darley Moor`"
1. At this point you can click 'OK' (to the left of the **Configure Race** dialog), and your race file will be created.  By doing this and making changes later it is harder to accidentally lose your work than by configuring everything within the dialog.
1. You will now be looking at the Actions page for your unstarted race.  Switch to the [Properties][] screen, where you can begin configuring the various settings.

## Common configuration options

These options are common to all BHPC events and are unlikely to change between races.

### RFID

1. Within [Properties][], switch to the [RFID][] tab.
1. Enable **Use RFID Reader During Race**.
1. Select **Manual Start:  Collect every RFID read**.
1. Click **Setup/Test RDID Reader** and ensure the **Reader Type** is set to **JChip/Impinj/Alien**.
1. Click 'OK' to close the **Chip Reader Setup**
1. Click 'Commit' to save the changes.

### Web

1. Switch to the **Web** Tab
1. Set **Contact Email** to `compsec@bhpc.org.uk`
1. Set the graphic to the 200 pixel wide BHPC logo from `C:\Users\BHPC\Documents\BHPC Racing\bhpc_logo_200px.png`
1. Click 'Commit' to save the changes.

### (S)FTP

1. Switch to the [(S)FTP][FTP] tab.
1. Select the **FTPS (FTP with TLS)** protocol.
1. Set the **Host Name** to `ftp.websitelive.net`
1. The port should be set to `21`
1. The upload path should be `www2.bhpc.org.uk/public_html/wp-content/uploads/Events/liveresults`
1. Set the username and password.  (Not reproduced here for security reasons.)
1. Enable **Automatically Upload Results During Race**
1. **URL Path** should be `http://www.bhpc.org.uk/wp-content/uploads/Events/liveresults`
1. Click 'Commit' to save changes.

You can use the **Test Connection** button to confirm that the FTP details are correct.

### Batch Publish

1. Switch to the [Batch Publish][] tab.
1. Enable "**HTML**" and "**Index HTML**", and enable the FTP option for both.
1. Ensure all other formats are disabled.
1. Ensure BikeReg is set to **None**
1. The **Post Publish Command** field should be empty.
1. Click 'Commit' to save changes.

### Camera

1. Switch to the [Camera][] tab.
1. Select "**Photos on Every Lap**"
1. Click 'Commit' to save changes.

## Race-specific options

These options are specific to the race.

### General Info

1. Switch to the [General Info][] tab.
1. The **Event Name** should be correct from earlier.
1. Enter a full description in **Long Name**.  Spaces are fine.  For example "Darley Moor R1 40min +1lap CW faster group"
1. Fill in the location and **Date** fields.
1. For **Discipline**, enter "HPV"
1. **Race #** should be set to the number of the race in that event (day of racing).  For example, if you're splitting the field into fast and slow groups, the first race of the second round would be race #3.
1. **Scheduled start** is the published start time, don't worry if the race starts a bit late (this will be noted in the results automatically).
1. Race minutes should be set to the nominal length of the race.  (NB. for a criterium, this should be set considerably longer.)
1. Set **Organiser** to your name.
1. Leave the **Memo** field black, as it is appended to the filename.
1. Click 'Commit' to save changes.

### Race Options

The settings here will depend on the format of the event:

#### A) Criterium race

A criterium is a mass start race of a given duration, plus an extra whole lap.  CrossMgr cannot automate this fully, as it cannot determine exactly when the leader is going to get the bell.

1. Switch to the [Race Options][] tab.
1. Disable **Time Trial** and enable **Criterium**.
1. Enable **All Categories Finish After Fastest Rider's Last Lap**.
1. Enable **Set 'Autocorrect Lap Data' option by Default**.
1. Disable **Show times to 100s of a Second**.
1. Disable **Road Race Finish Times**.
1. Disable **Estimate Laps Down Finish Time**.
1. Set **Rank finishers by** to "**average speed**".
1. Enable **Consider Riders in Spreadheet to be DNS if no race data**.
1. Set **Lap time for 80% rule** to **2nd lap time**.
1. Set **Distance Unit** to **miles**.
1. Enable **Show Lap notes, Edits and Projected Times in HTML Output**.
1. Enable **Show Course Animation in Html**.
1. Set the **Min possible Lap Time** to a healthy margin less than whatever Slash was lapping at last time we raced on this track.  If in doubt, lower is better.
1. Set **Play reminder sound** to `10` seconds.
1. Leave **License Link...** empty.
1. Disable **Win and Out**.
1. Click 'Commit' to save changes.

#### B) Fixed number of laps

A mass-start race where all racers ride the same number of laps.  Riders will have to count their own laps, and should be encouraged to continue racing if they lose count (which they probably will).

1. Switch to the [Race Options][] tab.
1. Disable **Criterium**.
1. Disable **Time Trial**.
1. Disable **All Categories Finish After Fastest Rider's Last Lap**.
1. Enable **Set 'Autocorrect Lap Data' option by Default**.
1. Disable **Show times to 100s of a Second**.
1. Disable **Road Race Finish Times**.
1. Disable **Estimate Laps Down Finish Time**.
1. Set **Rank finishers by** to "**average speed**".
1. Enable **Consider Riders in Spreadheet to be DNS if no race data**
1. Set **Lap time for 80% rule** to **2nd lap time**.
1. Set **Distance Unit** to **miles**.
1. Enable **Show Lap notes, Edits and Projected Times in HTML Output**.
1. Enable **Show Course Animation in Html**.
1. Set the **Min possible Lap Time** to a healthy margin less than whatever Slash was lapping at last time we raced on this track.  If in doubt, lower is better.
1. Set **Play reminder sound** to `10` seconds.
1. Leave **License Link...** empty.
1. Disable **Win and Out**.
1. Click 'Commit' to save changes.

#### C) *n*-lap Time Trial

A time trial is where riders start individually one after another, and compete against the clock.

1. Switch to the [Race Options][] tab.
1. Disable **Criterium** and enable **Time Trial**.
1. Disable **Best n laps**.
1. Enable **All Categories Finish After Fastest Rider's Last Lap**.
1. Enable **Set 'Autocorrect Lap Data' option by Default**.
1. Enable **Show times to 100s of a Second**.
1. Disable **Road Race Finish Times**.
1. Disable **Estimate Laps Down Finish Time**.
1. Set **Rank finishers by** to "**average speed**".
1. Enable **Consider Riders in Spreadheet to be DNS if no race data**.
1. Set **Lap time for 80% rule** to **2nd lap time**.
1. Set **Distance Unit** to **miles**.
1. Enable **Show Lap notes, Edits and Projected Times in HTML Output**.
1. Enable **Show Course Animation in Html**.
1. Set the **Min possible Lap Time** to a healthy margin less than whatever Slash was lapping at last time we raced on this track.  If in doubt, lower is better.
1. Set **Play reminder sound** to `10` seconds.
1. Leave **License Link...** empty.
1. Disable **Win and Out**.
1. Click 'Commit' to save changes.

#### D) Best of *n* laps

A variation on a time trial, where riders complete several laps, but are only scored on one of them.  Good for velodromes.

1. Switch to the [Race Options][] tab.
1. Disable **Criterium** and enable **Time Trial**.
1. Enable **Best n laps**.
1. Enable **All Categories Finish After Fastest Rider's Last Lap**.
1. Enable **Set 'Autocorrect Lap Data' option by Default**.
1. Enable **Show times to 100s of a Second**.
1. Disable **Road Race Finish Times**.
1. Disable **Estimate Laps Down Finish Time**.
1. Set **Rank finishers by** to "**average speed**".
1. Enable **Consider Riders in Spreadheet to be DNS if no race data**.
1. Set **Lap time for 80% rule** to **2nd lap time**.
1. Set **Distance Unit** to **miles**.
1. Enable **Show Lap notes, Edits and Projected Times in HTML Output**.
1. Enable **Show Course Animation in Html**.
1. Set the **Min possible Lap Time** to a healthy margin less than whatever Slash was lapping at last time we raced on this track.  If in doubt, lower is better.
1. Set **Play reminder sound** to `10` seconds.
1. Leave **License Link...** empty.
1. Disable **Win and Out**.
1. Click 'Commit' to save changes.


### Set the course GPX

1. Switch to the [GPX][] tab.
1. Click **Import GPX Course**
1. Browse to the `.gpx` file of the track.  A selection of previously-used courses are available in `C:\Users\BHPC\Documents\BHPC Racing\track_gpx\`.  (If you are creating a new GPX, the best way to do it is to ride the track at racing speed with a GPS receiver set to record one trackpoint per second.  The speed and elevation data will be used to improve the animation.)
1. Select **Course is a loop**.
1. Once loaded, check the direction arrow on the map.  If necessary, use the **Reverse Course Direction** icon to point it the other way.
1. Click 'Commit' to save changes.

### Linking the sign-on sheet

1. Switch to the **Files/Excel** tab.
1. Click "**Link External Excel Sheet**
1. Browse to the location of your sign-on spreadsheet, and click **Next**.
1. Now select the name of the sheet containing the sign-on data for this race, and click **Next**.
1. As you have named your columns with the headings that CrossMgr expects, the only thing you need to do on this page is select the **Initialize CrossMgr Categories from Excel EventCategory/CustomCategory and Bib# columns** option.  Click **Next**.
1. With any luck the summary page will announce status "*Success!*" with errors "*None*".  If not, check your spreadsheet format.  Click **Finish**.  You have now linked the sign-on data.

### Categories

1. Move to the [Categories][] screen.  You should see categories corresponding to those in the sign-on sheet.  If the category names or rider numbers are incorrect, make the relevant changes in the spreadsheet.
1. Click the **Set Gpx Distance** button to ensure that the **Distance** is set for all categories.
1. **Dist. By** should be set to **Lap** for all categories.
1. **First Lap Dist.** should be empty for all categories.
1. Rearrange the order of the categories by clicking and dragging the grey square at the start of each row.  The **Start Wave** should be at the top, followed by *Custom* categories, in the order: Open, Partly-faired, Unfaired, Faired Multitrack, Multitrack, Street, Women, Women Part-faired, Arm-powered, Junior, Car-free.
1. Check that the category genders are correct - CrossMgr sometimes makes incorrect assumptions where open categories only have riders of one gender.
1. **Start Offset** should be zero for all categories.
1. If this is a *time trial*, *fixed laps* or *best of n laps* race, ensure the correct values are entered in the **Race Laps** and **Best Laps** columns for each category.  (For example, for a "best of three" round, set **Race Laps** to `3` and **Best Laps** to `1`.)  Otherwise, ensure these columns are empty.
1. Ensure the **Race Minutes** column is empty for all categories; the global setting in [General Info][] will be used instead.
1. **Publish** should be enabled for all categories.  **Series** should be enabled for all except the Start Wave.  (**Upload** is for results formats we do not use.)
1. When you are satisfied, Click **Commit** to save changes.

---

At this point your race file should be ready for use.


Either close CrossMgr, or use [New Next][File] to create the next race file based on the settings in this one.  (I like to create an additional dummy time trial with everyone in it to use for testing RFID tags before the racing starts.)

#### After creating multiple race files, double-check the following:

* File naming is consistent.
* The correct Sheet is selected in the sign-on Excel file.
* Start times are correct.
* Race Minutes is correct.
* Race direcion is correct, both in the GPX and the race name.

If you change a race's filename, the original file will be left in place.  You may want to delete the old file now so as not to use the wrong one by mistake on race day.

#  Race Day

## Hardware setup

## Testing

## Timing a race

## Packing up

# Post-processing results

## Finish line photos

## Fixing the timing data

## Scoring

## Clean up for next time

# Glossary

To avoid confusion, we have tried to be consistent with the CrossMgr suite's use of terms like 'Bib' and 'Category' as much as possible.

Term|Meaning
:---|:------
Alias|In SeriesMgr, aliases are used to unify different spellings of a **rider**, **machine** or **team** name across a **series**, for when a rider appears as "Joe Bloggs", "Joe Blogs" and "Joseph B" in the results of different races.
Bell|In cycle racing, a bell is rung to indicate that a **rider** has one lap remaining.
Bell Lap|The race leader's last lap.
Bib, number|A rider's race number, as printed on the side of their HPV, and used for manual entry into CrossMgr/SprintTimer
Carbon fibre|Lightweight composite material notable for its radio-blocking properties.  Do not attach RFID tags directly to carbon fibre.
Category|A class of rider (eg. Junior) or HPV (eg. Part-Faired).  In CrossMgr terms a [Category][Category Screen] is a list of bib numbers and associated meta-data that defines how they are timed and scored.
Class|Historical BHPC term equivalent to **category** that we try to avoid using.
Component Category|A sub-category that makes up a **Start Wave**.  We don't usually use these in BHPC racing, as unlike **CustomCategory** they cannot overlap.
Criterium|A type of cycle race where riders race for a certain period of time, and then complete an extra lap.  CrossMgr cannot handle this on its own, as it cannot know whether the leader will cross the finish line before or after the time period has elapsed until after it has happened.
CrossMgr|A software application designed for timing cyclocross races developed by Edward Sitarski.  The suite of applications that complement CrossMgr.
CrossMgrImpinj|A software application that allows **Impinj** **RFID** readers to be used with CrossMgr by emulating a **JChip** reader.
CrossMgrVideo|A software application that grabs short sequences of video from a **USB** camera and stores them in a database.  Used in combination with CrossMgr to collect time-stamped **finish line** images.
CustomCategory|CrossMgr term for an arbitrary [Category][Category Screen] that is used to generate a ranking, but does not control when riders start and finish.
DNF|*Did Not Finish* - status given to **riders** who fail to complete a **race**.
DNS (computing)|*Domain Name System* a system for resolving human-readable names like `www.bhpc.org.uk` to IP addresses like `92.53.241.24` and vice-versa, by querying a *DNS Server*.  A DNS server is not normally available at the track-side, so devices must be referred to by their IP address.
DNS (racing)|*Did Not Start* - status given to **riders** who fail to make it to the start line of a **race**.
DQ|*Disqualified* - status given to **riders** who will not be **ranked** due to some violation of TEH RULEZ.
Ethernet|The IEEE 802.3 standard for data communications (usually on twisted-pair cable, terminated with RJ45 modular connectors).  Ethernet is is typically used to carry TCP/IP.
Ethernet Switch|A device that forwards Ethernet packets from one wired network segment to another.  The **router** built into the flight-case with the BHPC's tag reader includes a 4-port Ethernet switch.
Event|In this context, a day of racing.  Particularly for **points** purposes.
Excel|A functional programming language masquerading as a piece of accountancy software that's commonly used for managing databases.  CrossMgr reads its **sign-on sheet** in Excel format, and can also use it to output results.
Fast Race|A BHPC **race** composed of mainly faster, or more experienced, riders.
Filtering|When CrossMgr ignores tag reads due to some internal logic  (eg. multiple tag reads occurring too close together to be distinct laps)
Finisher|Status given to **riders** who complete (or are expected to complete) a **race**.
Finish line|The place on the track where you set up your RFID aerials and finish line camera.  In BHPC events this is usually the same as the start line.
Finish order|The order in which **riders** cross the **finish line** at the end of a **race**.  This is the most important piece of race data, and if riders are close together cannot always be determined by **RFID** alone: Human observation or video evidence may be required.
Flag|A chequered flag is waved to indicate that riders are finishing the **race**.  We may refer to a rider 'getting the flag' when their race is over.
FTP(S), SFTP|*File Transfer Protocol (Secure)*, *SSH File Transfer Protocol* - Protocols used for transferring files over a TCP/IP network.  CrossMgr uses this to upload results to a website.
Gender|In CrossMgr terms this may be one of 'Open', 'Women' or 'Men'.  Most BHPC [Categories][Category Screen] are 'Open'.
GPS|*Global Positoning System*.  A satellite navigation system that can be used to determine positions in space and time.
GPX (track)|A standard file format used by **GPS** receivers to record positions over a period of time.  Used by CrossMgr to draw the race animation, and to import lap times for riders.
Hexadecimal, Hex|Numbers in base 16 (0-F), rather than the usual base 10 (0-9).  Used for tag numbers.
HPV|*Human Powered Vehicle*, for example a bicycle, tricycle, handcycle, wheelchair, velomobile, streamliner or pedal car.
Impinj|The manufacturer of the *Speedway* **RFID** reader we use for timing races, and by extension their tag/hardware/software/protocol ecosystem.
IP address|A numerical address used to uniquely identify a device on a **TCP/IP** network.
JChip|An electronic timing system designed for sports events.  CrossMgrImpinj converts **LLRP** data from the **Impinj** reader into JChip protocol data for CrossMgr.
Lap|One complete circuit of a race track.
Lapped|A **rider** who has become far enough ahead in a **race** that they overtake a rider who is logically still behind them is said to have *lapped* the slower rider.  Lapped riders are expected in BHPC races, due to the wide range of machines and athletic ability.
Lap Time|The **race time** at which a rider crosses the finish line at the end of a lap.  May be extrapolated in the event of a **missed read**.
Leader|The **rider** currently in first position of their **race** or **category**.
License|In CrossMgr, a (?unique) identifier of **rider** used in UCI-compliant bicycle racing.  The BHPC don't use this.
LLRP|*Low Level Reader Protocol*.  The protocol used to communicate with the Impinj RFID reader over the TCP/IP network.
Local Time|The **time of day** in the appropriate time zone (eg. *British Summer Time*).
Machine|Attribute of a **rider** used to record the name of their HPV.
Mass Start|A **race** where multiple riders start at the same time.  Contrast with **Time Trial**.
Mechanical|When a **rider** stops during a **race** due to a problem with their **HPV**.  They may resolve the problem and continue, or opt to **DNF**.
Merge|A BHPC process for combining the results of multiple **races** to determine the results of a single **round**.
Merge-O-Matic|Deprecated **Excel** macro used for combining BHPC race results in Excel format.  This functionality is now built into CrossMgr.
Missed Read|When a rider crosses the **finish line**, but the **RFID** system doesn't detect their **tag**.
MultiReader|**Impinj** application that is useful for testing and for changing the tag number of RFID tags.
NP|*Not Placed* - Non-judgemental status given to **riders** who should not be **ranked** for some reason (eg. you know that their lap times are incorrect).
(S)NTP|*(Simple) Network Time Protocol*.  A protocol used by computing devices to synchronise their **real time clocks** over a **TCP/IP** network.
Points|Points are calculated by SeriesMgr.  Points mean prizes.
Points Structure|In SeriesMgr, a Points Structure is a mapping of rankings to numbers of **points**.  You can have a different points structure for each round.
PowerCon|A rugged electrical connector often used for providing AC power to professional audio equipment.  Notable for being weatherproof and having a twist-lock latching action.
Publish|In CrossMgr terms, the act of producing (and optionally uploading) race results in an easily-read format.
PUL|*Pulled* - status given to **riders** who have been removed from a **race** by officials, typically for being too slow.
Race|An instance of people rushing about on bicycles.  A CrossMgr `.cmn` data file pertaining to a **race**.  Contrast: **round**, **event**.
RaceDB|A software application for managing race entries and results written by Edward Sitarski.  The BHPC were unable to use this, as its handling of categories is too inflexible.
Race Clock|In this context, a device built by Kim Wall in 2021 to display the Race Time on a large LED display at BHPC events.  The Race Clock is also available as a web page on the CrossMgr local webserver.
Race Time|Time elapsed since the start of a race.  Compare with **Time of Day**
Ranking|A list of riders in order of winningness.  Not the same as *finish order*, as riders are likely to be on different laps.
Real Time|In computing, the processing of data quickly enough to keep up with it as it happens.  Perhaps unintuitively, CrossMgr does not process timing data in real time.  As such, the timing computer becoming slow to process data due to being overloaded does not normally affect the accuracy of recorded lap times, even if the user interface becomes sluggish.
Real Time Clock (RTC)|A subsystem of a computing device that keeps track of the **time of day**.  Often physically distinct from other time sources that coordinate the internal operation of the computer.  Electronic race timing relies on synchronising (or at least, accounting for the discrepancy between) multiple real time clocks.
Results|The outcome of a **race** or **round**.  Will include ranking and time data, but not **points**.  Those are allocated later.
RFID|*Radio Frequency Identification*.  In this context a long-range high-throughput tag system suitable for tracking vehicles, warehouse inventory and sports timing, rather than the short-range systems used for card-entry type applications.
Rider|A participant in a **race**.
RJ45|The cheap plastic modular connectors used on twisted-pair **Ethernet** cables.  Notable for requiring special tools to fit, and having an easily-broken retaining tab.  RJ45 connectors do not react well to being dropped in mud.
Round|A particular type of **race**.  For example "30 minute criterium" "1-lap time trial".  At BHPC **events**, a **round** may be composed of more than one **race**, as the BHPC often splits the group for safety reasons.
Router|A device that forwards **TCP/IP** packets from one network to another.  The router built into the flight-case with the BHPC's tag reader is not actually used as a router; it is configured to work as an **Ethernet switch** and **WiFi** **access point**.
Series|A championship table for a racing season or **event**.  A SeriesMgr `.smn` file pertaining to a series.
SeriesMgr|A software application designed for allocating scores to a **series** of **race** results.  Part of the CrossMgr suite.
Sign-on sheet|An **Excel** file containing details of riders, used by CrossMgr to populate the [categories][Category Screen] table and look up rider's names, teams, etc.  Crucially, this is needed in order to match **tags** to **riders**.
Slow Race|A BHPC **race** composed of mainly slower or less experienced riders.
Sprint|A **time trial** run over a very short distance, usually with a flying start.  Due to the high speeds involved, precision timing equipment is needed to judge sprint events; the **Impinj** **RFID** system is not precise enough.
Sprint Time|The duration (ie. **race time**) of a **sprint**.
SprintTimer|A software application designed for timing flying sprints, written in 2023 by Kim Wall of the BHPC.  It borrows heavily from CrossMgr's codebase.
Sprint Timer Unit|A precision timing device designed for timing flying sprints, built in 2023 by Kim Wall of the BHPC.
Start Time|The **time of day** that a **mass start** **race** started at, or the **time of day** that individual **rider** started at in a **time trial** or **sprint**.
Start Wave|A CrossMgr term for a [Category][Category Screen] that defines a group of **riders** who start the **race** at the same time.  We would normally have a single Start Wave in a **race**.
Stopwatch|A standalone timing device that you can use to time **races** when you don't trust CrossMgr.
Stray tag|An **RFID tag** which has been within range of the **RFID** aerials for some time.  Usually an unused tag in the box of timing equipment, or a tag attached to a rider's helmet or HPV that has been left near the **finish line**.  Stray tags matching the **tag number** of a **rider** in the current **race** can cause all sorts of problems.
Tag|A physical RFID tag (as stuck to a rider's HPV or helmet), or the Product ID number encoded onto it.  Tag numbers are sent to CrossMgr whenever a tag passes within range of the **RFID** aerials.
Tape Switch|An momentary electrical switch in a long, flat format that may be operated by pressure at any point along its length.  These can be used to trigger a timing device when a wheel passes over them.
TCP/IP|*Transmission Control Protocol/Internet Protocol*.  The de-facto standard protocol for computer networking.  Used by the CrossMgr suite applications to communicate with each other and with external hardware over **Ethernet** or **WiFi**.
Team|In CrossMgr, a Team is an attribute of a **rider**.  **Points** may be calculated on a team basis.
Time of day, Wall time|The time of day, possibly including the date.  May be UTC or in the local timezone.  Contrast with **Race time**.
Time Trial|A type of **race** where **riders** start at different times, and compete against the clock.
Trigger|Something that causes CrossMgrVideo to record a snippet of video in its database.  Triggers may come from CrossMgr over **TCP/IP**, manually from the mouse or keyboard, or via a **USB** device.
Trigger-O-Matic|A hardware device that generates HID joystick button events that trigger CrossMgrVideo.  This provides a nice big physical button that can be pressed quickly regardless of what the computer is displaying at the time, and an interface for a tape-switch or optical beam-break device.
USB|*Universal Serial Bus*.  A standard system for connecting computing equipment that is frequently used to provide power to small electronic devices.
USB-A|The large, flat USB connector typically used on desktop computers and 'wall-wart' power supplies.
USB-B|The large square USB connector usually found on printers and scanners.  The Trigger-O-Matic, Race Clock and Sprint Timer Unit have USB-B connectors in the interests of durability.
USB-C, Micro USB-B, Mini USB-B|Various (incompatible) smaller USB connectors, usually found on small battery-powered computing devices like mobile phones and **GPS** receivers.  Some laptops use USB-C as a power connector, but notably not the Acer Aspire 5 that the BHPC uses for race timing at the time of writing; its USB-C port is for data only.
UTC|*Universal Time Coordinated*.  A pedant would point out that it's not technically the same thing as *Greenwich Mean Time*, but effectively that.  Software that has any sense tends to work with UTC internally, and only convert to local time for input and output.
Webserver|CrossMgr and SprintTimer run a local web server on port `8765`.  This can be used to view live results or the **race clock**.
WiFi|In this context, the IEEE 802.11 standard for Ethernet-like data communications over spread-spectrum radio.
WiFi Access Point|The base station of a **WiFi** network.  Usually bridges to a wired **Ethernet** network.
XLR|A latching electrical connector commonly used for signals on professional audio, video and lighting equipment.  It is robust and easily repaired in the field.


