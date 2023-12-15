[TOC]

## Quick Start
### Introduction
Welcome to SprintTimer, a highly-automated sprint timing system designed for use by the [BHPC](https://www.bhpc.org.uk).

While timing sprints requires little more than some sort of automatic stopwatch, running a sprint event involves more than just timing.  This software has been designed so that as much of the organisation as possible can be done in advance, and as much of the data processing as possible can be done automatically, in order to streamline the process of herding riders through the timing gates and publishing results.

Crucially, the RFID system is used to identify riders as they pass through one of the timing gates.  Their details are then retrieved from a pre-prepared sign-on sheet, so that minimal work is needed to ensure that the recorded times are associated with the correct riders.  Additionally, CrossMgrVideo can be triggered to record timestamped images of the riders, as a back-up means of identification.

The [results table][Results] is generated automatically, and optionally uploaded to the web in real time.


### Step 1: Creating a sign-on spreadsheet
A sign-on sheet is required to identify riders using the RFID tag system.  It is also a convenient way to manage extended rider data (Names, Teams, race classes, etc.), although the SprintTimer can function without it, using bib numbers alone.

The sign-on sheet takes the form of a Microsoft Excel `.xlsx` file, in the same format used by CrossMgr (this allows you to use a single sign-on sheet for a mixture of CrossMgr and SprintTimer events).  The format is documented in [DataMgmt][External Excel], but for basic operation all you will need are columns entitled `bib#`, `First Name`, `Last Name`, `Tag` and `EventCategory`

Create a Sheet for each round.  This will enable you to make changes on a round-by-round basis.

### Step 2: Connect the Sprint Timer Unit, RFID reader and camera
Connect the sprint timer unit to power and Ethernet, as described in the [hardware documentation][Hardware].  The timing gates may be connected later.  The timer should boot up and obtain an IP address from the DHCP server, which will be displayed at the bottom of the screen.  Leave it to obtain a GPS fix.

If you are using an RFID tag reader, connect that to power, Ethernet and the RFID aerials, and start the CrossMgrImpinj or CrossMgrAlien application if necessary.

If you will be using CrossMgrVideo, connect the camera, start CrossMgrVideo and ensure that the camera is aligned and the focus/exposure are adjusted.

### Step 3: Create a sprint file
Now, start the SprintTime application, and select [File/New][File]

Enter an **Event Name** for your event, and select a **Race File Folder**.  Now click **OK** to the left of the window to create a race file.  Everything else can be configured later.

The window title will change to the name of your event, and you will be looking at an empty Data screen for an unstarted race.

### Step 4: Configure your event

Select the [Properties][] tab.  Fill in the remaining *General Info* and click **Commit**.  Changes will be saved to disk automatically.

Now move to the **Race Options** tab.  Set **Handle multiple attempts by using** to *Fastest speed*.  Select a speed unit.  Leave **Show Lap Notes in HTML Output** enabled, and set the **Min Possible Lap Time** to zero.  Disable **Allocate Sequential Bib Numbers**.  Again, click **Commit**

Move to the **Sprint Timer** tab, and enable **Use sprint timer to obtain precise times**.  Set the **Remote IP Address** to that displayed on the bottom of the sprint timer unit's LCD.  Leave the port as `10123`.  Set the trap distance to an appropriate value, and ensure that **Save extended debugging info to log** is disabled.  Click **Commit**

Move to the **RFID** tab....

