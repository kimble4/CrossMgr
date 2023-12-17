[TOC]

## Quick Start
### Introduction
Welcome to SprintTimer, a highly-automated sprint timing system designed for use by the [BHPC](https://www.bhpc.org.uk).

While timing sprints requires little more than some sort of automatic stopwatch, running a sprint event involves more than just timing.  This software has been designed so that as much of the organisation as possible can be done in advance, and as much of the data processing as possible can be done automatically, in order to streamline the process of herding riders through the timing gates and publishing results.

Crucially, the RFID system is used to identify riders as they pass through one of the timing gates.  Their details are then retrieved from a pre-prepared sign-on sheet, so that minimal work is needed to ensure that the recorded times are associated with the correct riders.  Additionally, CrossMgrVideo can be triggered to record timestamped images of the riders, as a back-up means of identification.

The [results table][Results] is generated automatically, and optionally uploaded to the Web in real time.


### Step 1: Creating a sign-on spreadsheet
A sign-on sheet is required to identify riders using the RFID tag system.  It is also a convenient way to manage extended rider data (names, teams, race classes, etc.), although the SprintTimer can function without it, using bib numbers alone.

The sign-on sheet takes the form of a Microsoft Excel `.xlsx` file, in the same format used by CrossMgr (this allows you to use a single sign-on sheet for a mixture of CrossMgr and SprintTimer events).  The format is documented in [DataMgmt][External Excel], but for basic operation all you will need are columns entitled `bib#`, `First Name`, `Last Name`, `Tag` and `EventCategory`

Create a Sheet for each round.  This will enable you to make changes on a round-by-round basis.

### Step 2: Connect the Sprint Timer Unit, RFID reader and camera
Connect the sprint timer unit to power and Ethernet, as described in the [hardware documentation][Hardware].  The timing gates may be connected later.  The timer should boot up and obtain an IP address from the DHCP server, which will be displayed at the bottom of the screen.  Leave it to obtain a GPS fix.

If you are using an RFID tag reader, connect that to power, Ethernet and the RFID aerials, and start the *CrossMgrImpinj* or *CrossMgrAlien* application if necessary.

If you will be using *CrossMgrVideo*, connect the USB camera to the computer, start *CrossMgrVideo* and ensure that the camera is aligned and the focus/exposure are correctly adjusted.

### Step 3: Create a sprint file
Now, start the SprintTime application, and select [File/New][File]

Enter an **Event Name** (which will become the filename) for your event, and select a **Race File Folder**.  Now click **OK** to the left of the window to create a race file.  Everything else can be configured later.

The window title will change to the name of your event, and you will be looking at an empty Data screen for an unstarted race.

### Step 4: Configure your event

Select the [Properties][] screen.  Fill in the remaining *General Info* and click **Commit**.  Changes will be saved to disk automatically.

From the [DataMgmt][] Menu, select **Link to External Excel Data**:

1. Browse to the location of your sign-on spreadsheet, and click **Next**.
1. Now select the name of the sheet containing the sign-on data for this sprint event, and click **Next**.
1. As you have named your columns with the headings that CrossMgr expects, the only thing you need to do on this page is select the **Initialize CrossMgr Categories from Excel EventCategory/CustomCategory and Bib# columns** option.  Click **Next**.

With any luck the summary page will announce status "*Success!*" with errors "*None*".  If not, check your spreadsheet format.  Click **Finish**.  You have now linked the sign-on data.

Move to the [Categories][] screen.  You should see categories corresponding to those in the sign-on sheet.  If the category names or rider numbers are incorrect, make the relevant changes in the spreadsheet.  Rearrange the order of the categories by clicking and dragging the grey square at the start of each row.  Check that the category genders are correct - CrossMgr sometimes makes incorrect assumptions where open categories only have riders of one gender.  When you are satisfied, Click **Commit**.

Now go back to the [Properties][] screen, and select the **Race Options** tab:

1. Set **Handle multiple attempts by using** to *Fastest speed*.
1. Select a speed unit. 
1. Leave **Show Lap Notes in HTML Output** enabled.
1. Set the **Min Possible Lap Time** to zero.
1. Disable **Allocate Sequential Bib Numbers**.

Click **Commit**

Move to the **Sprint Timer** tab:

1. Enable **Use sprint timer to obtain precise times**.
1. Set the **Remote IP Address** to that displayed on the bottom of the sprint timer unit's LCD.
1. Leave the port as `10123`.
1. Set the trap distance to an appropriate value.
1. Ensure that **Save extended debugging info to log** is disabled.

Click **Commit**.

### Step 5: Configure the RFID reader
Move to the **RFID** tab:

1. If you will be using an RFID system, select **Use RFID reader to identify riders**.
1. Set **RFID aerial position** to reflect your physical setup.
1. **Associate tag reads within _ seconds of trap time** can be left at the default value of `5`.
1. Select **Trigger camera on RFID read**.

Click **Commit**.

Click the **Setup/Test RFID Reader** button, and configure your reader.  Perform an RFID test to confirm that it is reading tags and identifying rider's bib numbers correctly.  When you are satisfied, click **OK**

### Step 6: Configure the camera
Move to the **Camera** tab.  Select the camera position - either T1 or T2 - and click **Commit**

### Step 7: (Optional) Live results:
Configure **Batch Publish** and **(S)FTP** for live upload of HTML results to your web server.  See [(S)FTP][SFTP] for more information.

### Step 8: Test the timing gates
Go back to the **Sprint Timer** tab and click on the **Timer input test...** button.  A *Sprint Timer Input Test* window should appear, and the LCD on the sprint timer unit should indicate that it is `TESTING INPUTS` and `TIMING DISABLED`.  If this does not work, check the network settings and try again.

Press the T1 and T2 test buttons on the front panel of the sprint timer unit.  The corresponding LEDs should illuminate while the buttons are held down and extinguished when released, and the `T1` and `T2` boxes on the *Sprint Timer Input Test* window will change colour.  If sounds are enabled, you should hear beeps loosely corresponding to each button press.

Assuming that is working correctly, you can now connect the timing gates to the inputs on the back of the sprint timer unit.  Perform any adjustment needed (eg. alignment of optical beams) so that the LEDs illuminate only when the gates are triggered.

When you are satisfied that the timing gates are working correctly, click **OK** to exit test mode.

### Step 9: Begin event
Check the LCD of the sprint timer to confirm that it is no longer in test mode and has a GPS/PPS signal.  If not, ensure that it has a good view of the sky (the GPS aerial is in the centre of the unit's top panel) and wait a bit longer, or continue without a GPS fix.

Chase all riders (and associated bikes/helmets/etc. with timing tags attached) out of RFID range, and remind them of the importance of staying well away from the RFID aerials until the event is over.  Arrange for a volunteer rider (who has tags and is in the sign-on sheet, and preferably has some sort of speedometer) to stay within shouting distance to test the system (this does not have to be a full race effort, but may require a few attempts to troubleshoot issues with the timing system).  Make sure that any spare written tags are in the RFID-proof bag.

Switch to the [Data][] screen.  Enable **Show bib entry / RFID read times** at the bottom of the screen.  Select **Start Recording** from the [Tools][] menu to start the race clock.  The *Bib Entry*/status bar will display "*Ready...*".  (Don't worry if the status bar shows "*Sprint timer not connected*", at this stage - it should update when data is received from the sprint timer unit.)

Test the sprint timer by triggering T1 and then T2 in sequence using the test buttons.  The LEDs should both light up and then extinguish, with the timing data appearing on the LCD and then in the Data screen after a short delay.  If sound is enabled, you should hear 'pips' (check the computer volume).  Confirm that the recorded **Time of day** is reasonable (if not, check your computer's real-time clock).  The *Bib Entry*/status bar should by now show a delta-t value and PPS status.  If the delta-t value is greater than 1 second, check your computer's real-time clock, and that there isn't a background application causing excessive system load.  The test sprint will not have any rider data associated with it (unless there is a live timing tag within RFID range).

Now signal to your volunteer to ride through the traps.  As the timing gates are triggered you should see the LEDs on the sprint timer unit light up in sequence and then go out, and the status bar will indicate when timing is in progress.  Meanwhile the RFID system should detect their tag, and a grey line containing their details will appear on the screen.  When the sprint is over, the timing data should appear, and - hopefully - associate it with the temporally adjacent RFID read to identify the rider.  Check that the calculated speed is broadly in agreement with the rider's speedometer - if not, check that you have measured and entered the trap distance correctly.

If you are using CrossMgrVideo, check that this has recorded triggers for the initial manual test, and then for the volunteer rider triggering the relevant timing gate and the RFID reader respectively.  The rider should be visible in the captured video!

If in doubt, test again.  It may be worth getting your volunteer to try a range of speeds.

If everything is working, you can send your volunteer to join the start queue, and either delete the test sprints, or clear their bib numbers so they do not count towards your volunteer's final result.  It may be worth marking any tests as such using the *Notes* field.

### Step 10: During the event
Signal to your marshals that the timing system is ready, and they may begin to dispatch riders.  Pay close attention to the system during the event.  Specific issues to watch out for include:

1. Confirm that the timing gates operate properly for every rider.
1. If T1 is triggered spuriously, stop the clock with the T2 test button before the next rider arrives.  The spurious time can be labelled as such using the *Notes* field.
1. Check that the RFID system identifies riders.  If it fails, enter their bib number manually, either using the **Enter Bib** box during the sprint, or by editing the bib field after it is added to the list.
1. Watch out for competitors who have completed their attempt wandering over with live tags and bagging other people's results.  It may be worth having a marshal to chase them away.
1. Unexpected software or hardware issues (timer unit not working, software freezes, power failure, freak gust of wind mis-aligning the optical beam, etc).  If non-trivial, signal to your marshals to stop dispatching riders in order to troubleshoot.

Once all competitors have completed their attempt(s), select **Finish Recording** from the [Tools][] menu.

### Step 11: After the event
At this point, you can switch to the [Results][] screen.  Select your EventCategory, and confirm that all competitors are accounted for.  Check that their times appear reasonable, and if not, go back to the [Data][] screen and (with help from CrossMgrVideo as appropriate) try to work out what went wrong.

*Consider Exiting the SprintTimer application and making a backup copy of the data file before making significant changes.*

When you are satisfied, you can output the results to HTML or Excel via [Publish][].

To import the results into SeriesMgr, publish them to Excel and load the Excel file.  SeriesMgr does not (yet?) support native import of .spr files.
