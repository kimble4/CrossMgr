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

#### E) Flying Sprints

These are timed using the dedicated SprintTimer application, rather than CrossMgr.  See SprintTimer's Quick-Start guide for how to set up and time a flying sprint event.

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

**Prerequisites:  Timing tent (or other suitable shelter) erected with AC power available.**

The setup process has been simplified by integrating the router and RFID reader into the flight-case, along with a redundant power supply and GPS time source.  This means that many of the connections are permanently in place, and you only need to connect the power source(s), Ethernet to the laptop and RFID aerials on race day.

![RFID reader etc. in flightcase](./images/flightcase_front.jpg "RFID reader etc. in flight-case")

1. Unpack the cables and loose equipment from the flight-case.  **Prop the flight-case lid open** by engaging the piece of aluminium profile on the right hand side of the lid with the protruding bolt in the base.
1. Locate the black **AC power cable** for the flight-case.  This has a standard **13A BS1363 mains plug** on one end (an adaptor should be present in the crate of timing equipment to adapt BS1363 to 16A IEC 60309 Ceeform), and a circular female **PowerCon** connector on the other.  Insert this in the male PowerCon socket on the side of the flight-case, and twist clockwise so it clicks into place.  Connect the other end to mains power (or a generator or inverter supply).  The AC power display on the power supply should light up and indicate the voltage and frequency of the AC supply, with a power draw in the region of about 15W as the router and tag reader boot up.  The DC power display will flash its backlight in alarm and show a voltage of 0V (occasionally this mis-reads as 99.99V), indicating that a DC supply is not present.
1. **DC power** of 12-36V can be connected using one (or more) of: **(A)** The small black **2.5mm DC barrel jack** inlet on the side of the flight-case.  (A short jack-jack cable is included to connect to a 2.1mm DC jack)  **(B)** The yellow **male XT60** connector on the side of the flight-case. (Cables are included to connect to spade terminals, or a 12V vehicle cigarette lighter socket) **(C)** The **female USB-C inlet** on the bottom left of the power supply panel. (Cables not included.  The USB power source must be 'laptop' rated - a standard phone-charging power bank cannot provide enough power to run the tag-reader)  Once connected, the DC power display should show a voltage appropriate for your power source, but no significant current/power will be drawn while AC power is present.
1. Ensure the **AC power failure alarm** switch is in the '**on**' position.  As long as DC power is present, the alarm will sound if the AC supply is interrupted.
1. Connect the **laptop's power supply** to AC power and the DC power inlet on the left side of the latop.
1. Locate the **red** Ethernet cable.  This has a standard RJ45 plug on one end, and a rugged RJ45-in-an-XLR-shell plug on the other.  Connect this end to either of the two RJ45 sockets on the side of the flight-case, and the standard RJ45 to the fiddly Ethernet socket on the left side of the laptop next to the power inlet.
1. Locate appropriately long **coaxial cables** (stored separately in in the crate of timing stuff) and connect the male N-connectors to the RFID aerials (which should have right-angle N adaptors attached), and the male RP-TNC connectors to the female RP-TNC connectors on the tag reader.  The far-side aerial should be the one covered in ScotchLite retro-reflective tape.  By convention, we connect the near-side aerial to channel [fixme] 1 on the tag reader, and the far-side aerial to channel 2.  (This makes it easier to determine which isn't working properly if there's a fault.)
1. Optional (only needed **for writing tags**): Locate the short coaxial cable with male TNC connector on one end and a male RP-TNC connector on the other, and use this to connect the 'desktop' aerial to channel 3 of the tag reader.  **Ensure that you've got the cable the right way round by paying particular attention to the central pins of these confusingly stupid connectors.**
1. Attach the camera to a tripod, and connect it to one of the **USB ports** on the left side of the laptop.
1. Locate the beige **USB-A to USB-C cable** and connect the **Trigger-O-Matic** to one of the **USB ports** on the left side of the laptop.  Ensure the auto-capture toggle switch is set to 'disable'.
1. Optional: Screw the **reflective IR beam break** unit onto its drainpipe and mount it on its stand beside the nearside RFID aerial.  Locate the black **male 3-pin XLR to female 3-pin XLR** cable and use it to connect the IR beam-break unit (alternatively, a tape-switch) to the XLR socket on the Trigger-O-Matic.
1. Optional: Erect the **Race Clock**'s stand (ensuring that the clamps are tightened and securing pins are in place, and fit the clock to it.  Rotate the clock gently until you feel the hole in the base of the top-hat drop into place around the excentric allen bolt on the end of the stand (this prevents it rotating in the wind).  Pick up and rotate the entire stand to point the clock in the right direction - **do not force it to rotate on the stand, or the securing pins will be damaged**.  Do not use the stand in strong winds - the clock may fall over and be damaged.
1. Locate the **Race Clock power cable** (stored separately in the crate of timing stuff), and connect the female PowerCon connector to the back of the clock (again, twisting clockwise to click into place).  Connect the BS1363 mains plug to AC power.  The clock should boot up and display the time of day and temperature as it searches for a WiFi network.

### Stourport variation

* Due to problems caused by reading tags of riders on the far side of the track, we have found that it works better to use the **desktop aerial**, lying on the ground facing upwards at the trackside in place of the usual nearside aerial.
* This limits the pickup range to approximately 3 metres (about half the width of the track), and prevents spurious reads.
* Connect it to port 2 of the tag reader, and the software will not need to be re-configured.

### Sprint timer

* Additional steps are needed if you will be using the Sprint Timer Unit.  See the **SprintTimer** quick start guide for more information.

## Software startup and Testing

### CrossMgrVideo

1. **Boot up the laptop**, and ensure that it is receiving external power.
1. Start **CrossMgrVideo**.  Hopefully you should see the view from the finish-line camera in the preview window (bottom left).  (If instead you see an image from the laptop's internal camera, check the connections and try using the Reset Camera dialog to select the right one.) 
1. Click **Config Auto Capture**.  Capture should be set to "**by seconds**".  `3` seconds before and `5` seconds after the trigger are reasonable.  Ensure that **Sequential bib for capture** is disabled, and enable **Play shutter sound** (note that the sound is only played for real-time captures; those triggered retrospectively by CrossMgr are silent).
1. Check that the autoselect mode (lower right, above the trigger list) is set to "** Fast Preview**"
1. Click **Monitor/Focus**, and open the cover of the camera's weatherproof case.  Adjust the **aperture ring** on the camera lens until the image is correctly exposed, allowing for likely changes in ambient light.  The focus should hopefully not need adjusting.  Close the weatherproof case and align the camera so it is looking straight across the finish line, with either a mark on the track or the RFID cable in view as a reference point.
1. Align the **IR beam break** with the ScotchLite reflector on the RFID aerial on the far side of the track.  The LED should [fixme] light up when the beam is detected.  The drainpipe helps to keep sunlight out of the sensor, but range is limited to about 10 metres at best, so this will not always work.
1. **Confirm that video is captured** when the **Auto-capture** button on the Trigger-O-Matic is pressed.  Now enable the Auto-Capture toggle switch on the Trigger-O-Matic and confirm that video is captured when the IR beam is broken.  Optionally disable the toggle switch for now, so as not to waste disk space capturing people warming-up.
1. Minimise CrossMgrVideo and leave it running in the background.

### CrossMgrImpinj

1. Start CrossMgrImpinj.
1. It should immediately establish a connection to the tag reader and the left pane will turn green.  Otherwise check the [BHPC troubleshooting guide][Communications Tagreader] for help diagnosing the communication problem.
1. Confirm that **Antenna Ports** `1` and `2` are enabled.  Icons should appear to indicate that the respective aerials are connected.
1. Confirm that **Monitor Power** is enabled for all power sources.  Icons should appear to indicate that the respective supplies are present.
1. Click **Advanced**.  **Report Method** shuold be set to "**Quad Regresssion**", with **Remove Outliers** enabled.  Set **Antenna Choice** to "**Max Signal dB**"
1. Set **Tag Population** to 16.
1. Leave **Transmit Power** and **Receiver Sensitivity** blank.
1. Set **Connection Timeout** to `3` seconds, **Keepalive** to `2` seconds, and **Repeat** to `3` seconds.
1. Enable **Recalculate clock offset...** and **Beep on Read**
1. Click OK, and OK to "*Reset reader now?*".
1. If riders are milling around, you should start to see tag reads in the left hand pane, confirming that the RFID system is operating.  Otherwise, grab a tag and bring it in and out of range.  Ensure that you see reads from both antennas.
1. Minimise CrossMgrImpinj and leave it running in the background.

### Internet Connection (Optional)

* If you will be using live results, ensure that the laptop's WiFi is connected to something that provides internet connectivity.  Typically this will be a smartphone or portable hotspot, but you might be able to use eg. the Club-house WiFi at Hillingdon.

### CrossMgr

1. Open a **File Explorer** window and navigate to the race file directory you created for the day's racing.
1. Make any **last-minute changes to the sign-on sheet**.
1. Double-click the `.cmn` file for the first race.  CrossMgr should start and you should be looking at the [Actions][] screen.  *Do not* click on the big friendly '**Start Race**' button until you mean it!
1. Switch to [Properties][] and double-check the settings in each of the tabs.  Refer to the earlier part of this guide if necessary.  If you will be using it, confirm that the FTP upload works.
1. Also check the [Categories][] screen.
1. If this is all okay, go to [Properties/RFID][RFID], and click **Setup/Test RFID Reader...**
1. Start the **RFID test**.  CrossMgrImpinj should establish a connection and you should start to see tag reads in the **Messages** pane.
1. You can leave the RFID test running until the race is about to start.  This allows you to check that rider's tags are working.

### Race Clock

* With the **RFID test running**, now is a good time to check the **Race Clock**:  Look at the display on the back of the clock.  By now it should have connected to the `BHPC_Timing` WiFi network, and have established a WebSocket connection to CrossMgr, causing the respective LEDs to illuminate.
* Check the LED display is working properly.  If the heartbeat is enabled, you should see the last LED in the display (middle of the leftmost digit) flashing red a couple of times a second.  This confirms that data is making its way to all pixels in the display.
* If there are problems, check the [BHPC troubleshooting guide][Clock Issues] for more details.
* Ensure that the clock is facing in a direction that allows racers to see it properly, that the stand is secure, that the power cable is not a trip hazard, and that people aren't standing in front of the display.

### Someone needs tags!

* This is usually the point in proceedings where someone will come to you with a sob story about having to remove their timing tags for a pedal car race, leaving them on their other helmet or their fairing being eaten by a grue.  Alternately, you may have established that their existing tags are don't work properly during the RFID test, or are in danger of peeling off.

* First, check that you haven't already got a set of new tags for them in the tag bag - *riders will not always remember if they asked for new tags at sign on*.  If you have to write new tags:

1. Dig out the blank tags, and cut a pair of them off the roll.  Mark the front of the tags with the rider's bib number in permanent marker pen.
1. Establish what the rider's tag numbers should be in hexadecimal [fixme], and write this on the back of the tags' backing sheet.  *Do not trust yourself to hold this in short-term memory; someone will distract you and this is how mistakes get made*.
1. Stop the RFID test, if running, and close CrossMgr.
1. Close CrossMgrImpinj to free up the tag reader.
1. If the desktop aerial is not connected to port 3, follow the instructions above to connect it.
1. Start the Impinj **MultiReader** application, and *connect to the configured reader*.
1. Place the tags on top of the desktop aerial (weighing them down with something non-conductive so they don't blow away).
1. Click the **START Inventory Run** button.  Two tag numbers shold appear in the list to the left.  Stop the inventory run.
1. Right-click on one of the tag numbers, and select **Change EPC**.  [fixme]
1. Referring to the tags backing sheet, enter the new tag number as a hexadecimal number, and click **Write tag**.
1. Close the window, and change the EPC of the *other* tag in the same way.
1. Do the inventory run again; you should only see the correct tag number.
1. Give the tags to the rider, close MultiReader.
1. Restart CrossMgrImpinj.
1. Reopen the CrossMgr race file and re-start the RFID test.  If carbon fibre or similar are involved, this might be a good time to check the new tags work actually work once attached to the HPV.

## Timing a race

### Final checklist:
* **Timing tent** guy ropes etc secure?
* Are the **RFID aerials** pegged or weighed down?
* Does the organiser have the **bell** and **flags**?
* Do you know where the **first aid kit** is?
* If you are using a **generator**, does it have plenty of fuel and oil?  Do you know how to restart it?
* Check the flight-case **power supply**:  Are AC and DC power present?  Is the AC power failure **alarm enabled**?
* Is the **laptop** running on AC power?  Is its battery charged?
* Are there any **notifications** from Windows (eg. wanting to reboot for updates, virus warnings) that might cause problems?
* Does the **GPS time source** have a satellite signal (orange LED lit or flashing)?  Does it have a time signal (blue LED lit or preferably flashing once per second)?
* Check **CrossMgrVideo**:  Is the camera aligned, with correct **focus and exposure**?
* Is the **IR beam break** aligned and operating the Trigger-O-Matic correctly?
* Check **CrossMgrImpinj**.  Is it connected and reading tags?  Are tags being read on both antennas?  Press the reset button and confirm the **clock offset** is still reasonable (typically 3600 seconds to within one second).
* Is **CrossMgr** open with the **correct race** file?
* Is the **RFID test** successful?
* Is the **Race Clock** working and visible?
* Does someone have a **backup stopwatch** ready?
* **If you're racing**, is your bike ready, do you have your helmet and elbow pads on?
* Get a **headcount of riders **on the start line.  Does it match your sign-on sheet?  Establish the **known DNSes**.
* Do you have a **pen and paper** ready to note down DNFs, incidents etc. as they happen?  Write the race name on it clearly.
* Do you have a device that can **video the finish** if the timing system fails?

### Starting the mass-start race

1. Finish the RFID test.  Switch to the [Actions][] screen and click the **Start Race** button.  The race will not start until you click '**OK**' on the dialog that pops up.
1. Tell the person starting the race that you're ready.  Pay attention.
1. Click '**OK**' when they say "Go!"
1. Switch to the [Results][] screen.  Riders whose tags were read immediately after the start will be listed.  Others will not.
1. Open the [Missing Riders][Windows] window.  This will show who hasn't yet been accounted for.
1. Enable the **Auto-Capture** toggle switch on the Trigger-O-Matic.
1. As the riders come round for their first lap, keep an eye out for anyone whose tags aren't reading.  Refer to the [BHPC troubleshooting guide][BHPC Troubleshooting] if necessary.
1. Check that CrossMgrVideo is being triggered by CrossMgr, and capturing video successfully.

Once all riders are accounted for, you shouldn't have to do anything other than keep abreast of DNFs and similar incidents.  Keep an eye out for missed reads and other problems, and check the camera exposure if the ambient light level changes drastically.

### Race finish


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
BHPC|The [British Human Power Club](https://www.bhpc.org.uk/)
Bib, number|A rider's race number, as printed on the side of their HPV, and used for manual entry into CrossMgr/SprintTimer
Carbon fibre|Lightweight composite material notable for its radio-blocking properties.  Do not attach RFID tags directly to carbon fibre.
Category|A class of rider (eg. Junior) or HPV (eg. Part-Faired).  In CrossMgr terms a [Category][Category Screen] is a list of bib numbers and associated meta-data that defines how they are timed and scored.
Class|Historical **BHPC** term equivalent to **category** that we try to avoid using.
Component Category|A sub-category that makes up a **Start Wave**.  We don't usually use these in **BHPC** racing, as unlike **CustomCategory** they cannot overlap.
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
Ethernet Switch|A device that forwards Ethernet packets from one wired network segment to another.  The **router** built into the flight-case with the **BHPC**'s tag reader includes a 4-port Ethernet switch.
Event|In this context, a day of racing.  Particularly for **points** purposes.
Excel|A functional programming language masquerading as a piece of accountancy software that's commonly used for managing databases.  CrossMgr reads its **sign-on sheet** in Excel format, and can also use it to output results.
Fast Race|A **BHPC** **race** composed of mainly faster, or more experienced, riders.
Filtering|When CrossMgr ignores tag reads due to some internal logic  (eg. multiple tag reads occurring too close together to be distinct laps)
Finisher|Status given to **riders** who complete (or are expected to complete) a **race**.
Finish line|The place on the track where you set up your RFID aerials and finish line camera.  In **BHPC** events this is usually the same as the start line.
Finish order|The order in which **riders** cross the **finish line** at the end of a **race**.  This is the most important piece of race data, and if riders are close together cannot always be determined by **RFID** alone: Human observation or video evidence may be required.
Flag|A chequered flag is waved to indicate that riders are finishing the **race**.  We may refer to a rider 'getting the flag' when their race is over.
FTP(S), SFTP|*File Transfer Protocol (Secure)*, *SSH File Transfer Protocol* - Protocols used for transferring files over a TCP/IP network.  CrossMgr uses this to upload results to a website.
Gender|In CrossMgr terms this may be one of 'Open', 'Women' or 'Men'.  Most **BHPC** [Categories][Category Screen] are 'Open'.
GPS|*Global Positoning System*.  A satellite navigation system that can be used to determine positions in space and time.
GPX (track)|A standard file format used by **GPS** receivers to record positions over a period of time.  Used by CrossMgr to draw the race animation, and to import lap times for riders.
Hexadecimal, Hex|Numbers in base 16 (0-F), rather than the usual base 10 (0-9).  Used for tag numbers.
HPV|*Human Powered Vehicle*, for example a bicycle, tricycle, handcycle, wheelchair, velomobile, streamliner or pedal car.
Impinj|The manufacturer of the *Speedway* **RFID** reader we use for timing races, and by extension their tag/hardware/software/protocol ecosystem.
IP address|A numerical address used to uniquely identify a device on a **TCP/IP** network.
JChip|An electronic timing system designed for sports events.  CrossMgrImpinj converts **LLRP** data from the **Impinj** reader into JChip protocol data for CrossMgr.
Lap|One complete circuit of a race track.
Lapped|A **rider** who has become far enough ahead in a **race** that they overtake a rider who is logically still behind them is said to have *lapped* the slower rider.  Lapped riders are expected in **BHPC** **races**, due to the wide range of **machines** and athletic ability.
Lap Time|The **race time** at which a rider crosses the finish line at the end of a lap.  May be extrapolated in the event of a **missed read**.
Leader|The **rider** currently in first position of their **race** or **category**.
License|In CrossMgr, a (?unique) identifier of **rider** used in **UCI**-compliant bicycle racing.  The **BHPC** don't use this.
LLRP|*Low Level Reader Protocol*.  The protocol used to communicate with the Impinj RFID reader over the TCP/IP network.
Local Time|The **time of day** in the appropriate time zone (eg. *British Summer Time*).
Machine|Attribute of a **rider** used to record the name of their HPV.
Mass Start|A **race** where multiple riders start at the same time.  Contrast with **Time Trial**.
Mechanical|When a **rider** stops during a **race** due to a problem with their **HPV**.  They may resolve the problem and continue, or opt to **DNF**.
Merge|A BHPC process for combining the results of multiple **races** to determine the results of a single **round**.
Merge-O-Matic|Deprecated **Excel** macro used for combining BHPC race results in Excel format.  This functionality is now built into CrossMgr.
Missed Read|When a rider crosses the **finish line**, but the **RFID** system doesn't detect their **tag**.
MultiReader|**Impinj** application that is useful for testing and for changing the tag number of RFID tags.
N-connector|A chunky threaded coaxial connector used on the **trackside RFID aerials**.  Sometimes used on laboratory test equipment, and in specialist RF applications.
NP|*Not Placed* - Non-judgemental status given to **riders** who should not be **ranked** for some reason (eg. because you know that their lap times are incorrect).
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
RJ45|The cheap plastic modular connectors used on twisted-pair **Ethernet** cables.  Notable for requiring special tools to fit, and having an easily-broken retaining tab.  RJ45 connectors do not react well to being dropped in mud.  Some of our equipment uses RJ45 connectors in an **XLR** shell, for increased ruggedness.
Round|A particular type of **race**.  For example "30 minute criterium" "1-lap time trial".  At BHPC **events**, a **round** may be composed of more than one **race**, as the BHPC often splits the group for safety reasons.
Router|A device that forwards **TCP/IP** packets from one network to another.  The router built into the flight-case with the BHPC's tag reader is not actually used as a router; it is configured to work as an **Ethernet switch** and **WiFi** **access point**.
RP-TNC|*Reverse-Polarity Threaded Neill–Concelman*.  Confusing variation of the **TNC** coaxial connector with gender of the central pins swapped.  Used on the **RFID tag reader**.
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
TNC|*Threaded Neill–Concelman*.  A small threaded coaxial connector used on the **desktop RFID aerial**.  Fiddly relative of the *Bayonet Neill–Concelman* connector usually found on laboratory test equipment and some professional video equipment.  Contrast with **RP-TNC**
Trigger|Something that causes CrossMgrVideo to record a snippet of video in its database.  Triggers may come from CrossMgr over **TCP/IP**, manually from the mouse or keyboard, or via a **USB** device.
Trigger-O-Matic|A hardware device that generates HID joystick button events that trigger CrossMgrVideo.  This provides a nice big physical button that can be pressed quickly regardless of what the computer is displaying at the time, and an interface for a tape-switch or optical beam-break device.
UCI|*Union Cycliste Internationale*.  Boring governing body who delight in banning things, and have a strange obsession with socks.
USB|*Universal Serial Bus*.  A standard system for connecting computing equipment that is frequently used to provide power to small electronic devices.
USB-A|The large, flat USB connector typically used on desktop computers and 'wall-wart' power supplies.
USB-B|The large square USB connector usually found on printers and scanners.  The Trigger-O-Matic, Race Clock and Sprint Timer Unit have USB-B connectors in the interests of durability.
USB-C, Micro USB-B, Mini USB-B|Various (incompatible) smaller USB connectors, usually found on small battery-powered computing devices like mobile phones and **GPS** receivers.  Some laptops use USB-C as a power connector, but notably not the Acer Aspire 5 that the BHPC uses for race timing at the time of writing; its USB-C port is for data only.
UTC|*Universal Time Coordinated*.  A pedant would point out that it's not technically the same thing as *Greenwich Mean Time*, but effectively that.  Software that has any sense tends to work with UTC internally, and only convert to local time for input and output.
Webserver|CrossMgr and SprintTimer run a local web server on port `8765`.  This can be used to view live results or the **race clock**.
WiFi|In this context, the IEEE 802.11 standard for Ethernet-like data communications over spread-spectrum radio.
WiFi Access Point|The base station of a **WiFi** network.  Usually bridges to a wired **Ethernet** network.
XLR|A latching electrical connector commonly used for signals on professional audio, video and lighting equipment.  It is robust and easily repaired in the field.


