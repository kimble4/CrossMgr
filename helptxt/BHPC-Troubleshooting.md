[TOC]

# BHPC Troubleshooting

This document is intended to help BHPC volunteers resolve problems with the race timing system.  If you are not the British Human Power Club, then much of this won't make sense.  It has been added to the CrossMgr help so that it is easily available during races.

Topics are listed in approximate order of urgency.  The search facility may be useful!

## Before the race

### Changing a rider's race classes

This can be done in the sign-on system, or by editing the racers spreadsheet.  If you edit the spreadsheet your changes will be lost if it is re-written by the sign-on system.  Be careful with the spelling of category names, if they do not match, additional categories will be created.

This may be done retrospectively, so if you're short of time, make a pen & paper note of the change, and worry about it after the race.

### Moving a rider between fast and slow groups

As above, this can be done in the sign-on system or by editing the spreadsheet.  If done by editing the spreadsheet be sure to change the rider's EventCategory to match the destination race, otherwise CrossMgr will put them in their own start wave.


## During the race

The golden rule for when things go wrong during the race is that **if in doubt, get someone to video the rider's crossing the finish** (as a continuous recording) with a phone or whatever.  Have the race clock visible at some point in the recording so time indexes can be synced up later.

If CrossMgrVideo is functioning, manually triggering it will achieve this in an easier to process way.

### Tags aren't reading...

Yellow times on the Results page are extrapolated times.  **If everything is yellow, it means that tags are not being read!**

#### For a specific rider

Check RiderDetail.   Is the rider in the race?  (If not, check the sign-on sheet.)

Check the list of lap times...

If times are being recorded, but filtered:

- Check the minimum lap time
- If spurious reads are being accumulated, search the area around the finish line for spare tags/helmets/bikes.  Ensure that unclaimed tags are in the RF-blocking bag.

If times are not being recorded, check CrossMgrImpinj:

Are their tags being read?|Resolution
:----|:---------
Yes|Check the rider's details in the sign-on sheet - are the 'Tag' field(s) correct?
No|Probably a dodgy or missing tag.  Enter the rider's times manually until the end of the race.
Yes, but it's the wrong number|You can change this in the sign-on sheet and it will be applied retrospectively.
The tag is listed as 'stray'|A tag with the rider's number is within range of the RFID aerials and has been for some time.  Remove it from the area or place it in the RF-blocking bag.
The tag is being 'skipped'|As above.  Can also be a symptom of the tag reader's clock drifting with respect to the computer's.  Try pressing 'reset' in CrossMgrImpinj.  If this solves the problem, you have a clock drift issue, try enabling "**Recalculate clock offset as tag reads are reported**" or setting "**Repeat Seconds**" to zero in CrossMgrImpinj's Advanced settings.

#### For everyone

Check there are riders in the race.  There could be a problem with the sign-on sheet.

Otherwise, this is likely a problem with the RFID system.  Check CrossMgrImpinj is running and diagnose any connectivity issues.

### Trigger-O-Matic isn't triggering

The IR beam-break is a useful backup against RFID problems, but isn't reliable when the track is wide (eg. Darley Moor) or in bright sunlight.  The 'auto capture' button will trigger a recording manually, and its use should be encouraged for close finishes and where a rider's tags aren't reading.

### Power failure

If AC power (eg. from a generator or inverter) fails, the laptop will continue to operate on its internal battery.  This also powers the camera and Trigger-O-Matic, and should be sufficient for a couple of hours.

The RFID tag reader, Wireless router and GPS time source are powered by a redundant power supply.  If a DC (battery) source is present, they will continue to operate on DC power.  If enabled, the AC power failure alarm should sound, and CrossMgrImpinj will pop up a warning message.  The race clock is powered by AC power alone, and will cease functioning.

To avoid risk of damage from voltage fluctuations, **disconnect all the timing equipment before attempting to restart a generator**.  Reconnect only after the generator output has stabilised.

If power to the tag reader is completely lost, keep an eye on CrossMgrImpinj and make sure the connection is restored on boot-up (the old laptop had a quirk in its Ethernet driver whereby the USB dongle needed to be hot-plugged before it would bring up the connection).

When AC power is successfully restored, remember to re-enable the power failure alarm for next time.

If the redundant power supply fails, the router (15V, centre positive) and tag reader (24V, centre positive) may be powered by their own wall-wart adaptors.  The tag reader may also be powered using 802.3af Power-over-Ethernet from a suitable 48V injector or POE switch.


### Results look wrong

**Yellow times on the Results page are extrapolated times.**  They are CrossMgr's best guess when it doesn't have a valid lap time to go on.  Don't be fooled into thinking that everything is working because you see yellow lap times.

#### Slash isn't winning

- Is it the slow race?
- Check the minimum lap time?
- Has another rider left a timing tag near the start line to accumulate spurious reads?
- Has he crashed into a hedge?
- Problem with the fundamental laws of physics?

#### Incorrect ranking in live results

If ranking by average speed, ensure that all categories have a lap distance set.  (CrossMgr's results page does not use average speed ranking while the race is in progress, so only the HTML output will be affected.)

#### Rider in their own start wave

Someone has edited the sign-on sheet to move a rider from one race to another and not updated their EventCategory accordingly.  Fix the sign-on sheet.

#### Time trial false start

In a manually/RFID started time trial you can delete a rider from the race and start them again.  (fixme: double-check this)

Otherwise, the safest approach is to time them with a stopwatch, pen and paper then fudge the results afterwards.

#### Spurious RFID reads during sprints

If someone brings their timing tags near the RFID aerials during a sprint event, they can accidentally claim another rider's times.  This is particularly bad, as it isn't their own results that get corrupted.

The best approach is vigilance, and to correct (or clear) the 'bib' field of the affected sprints as soon as possible.  Use the 'note' field to explain what happened.

If necessary you can identify the true rider using CrossMgrVideo after the event.

### There's an error message...

#### From CrossMgr

I can't think of any error messages that CrossMgr generates during a race?

#### From CrossMgrImpinj

CrossMgrImpinj is the application that allows CrossMgr to communicate with the Impinj RFID reader.  It can produce warning messages if something goes wrong with the RFID system.  It also monitors the redundant power supply via its GPIO port.

Error|Course of action
:----|:---------
Tag reader has disconnected (red screen on left)|Check the tag reader and router have power.  Check the relevant Ethernet blinkenlights.  Check the wiring.  Try resetting CrossMgrImpinj.  Attempt TCP/IP diagnostics using `ping` and/or a web browser (FireFox has shortcuts to the router and tag reader's web interfaces).  Power-cycle whatever isn't working and pray.
Not connected to CrossMgr (red screen on right)|This is normal if no race or RFID test is in progress; CrossMgr only listens for connections during a race or test.  If the race is running but it still fails to connect, check the RFID properties in CrossMgr.
An aerial has disconnected|Check the coaxial cables to the aerials.  Try another cable (coax is easily damaged, and water ingress through a nick in the jacket will obliterate its RF performance).  Reset CrossMgrImpinj.
A power source has disconnected|Check the power meters and blinkenlights to confirm.  Check the relevant power wiring.  Check that the generator is working (fuel/oil supply) and is on a level surface; that the battery is not depleted or that the mains supply hasn't tripped out or been switched off / unplugged at the far end.  Beware of tea urns.

#### From CrossMgrVideo

CrossMgr will warn if the camera disconnects.  Check the USB cable to the camera (there is a small weatherproof inline connector at the camera end), and that CrossMgrVideo hasn't switched to using the internal webcam.  Restart CrossMgrVideo if necessary, reconfigure the camera if necessary, and check the alignment/focus/aperture.

CrossMgrVideo will begin listening for triggers as soon as it has started up.

#### From Windows

##### Not Responding

While it may become (harmlessly) sluggish at busy times, CrossMgr freezing or going "Not Responding" is bad.  If it doesn't recover within 30 seconds, it's better to kill the process and restart CrossMgr than to continue waiting.  Under normal circumstances, CrossMgr writes race data to disk every minute, so you won't lose the whole race if you have to kill it.  If CrossMgrImpinj is still working, it will continue to log tag reads to its own file, so lost data can be reconstructed with a bit of effort.

Historically CrossMgrVideo would go "Not Responding" during intensive database access.  It would eventually recover on its own.  Setting it to 'Fast Preview' mode should avoid this happening.

##### Virus warnings

Windows Defender sometimes false-positives on the CrossMgr suite applications and warns that they are a virus.  Do not allow it to remove/quarantine the applications, otherwise you're going to have a really bad day.  (With any luck, there's still a copy of the installer `.exe`s in the Downloads directory.)

##### Windows update

This *should* be set to not install updates during racing hours.  Don't start a race while it's pestering for updates, in case it decides to unilaterally reboot the system.  Better to make everyone wait while Windows restarts.

### Dealing with DNFs

The best approach is to make a pen & paper note of the rider's bib number and approximate DNF time before touching Rider Detail.  The DNF time can always be entered retrospectively after the race if you are busy or unsure.

Keep an eye out for DNF riders deciding to resume the race, and for riders who haven't told you they've DNFed sneaking around behind the timing tent and generating spurious RFID reads.

In a fixed-laps race, it's better to set riders who abandon to PUL rather than DNF, so that they get credit for the laps they've completed.

### Race clock issues

As long as it has power and a WiFi signal the race clock *should* operate without any manual intervention.

When CrossMgr is running, the clock should connect to the WebSocket for the lap counter, and the `WebSock` LED will illuminate.  During the race, the `Net Act` LED should flash approximately once per second, as the race data is refreshed.

Problem|Course of action
:----|:---------
LED display is blank|Check the LCD and `Power` blinkenlight for evidence of power.  Ensure the PowerCon mains power connector has been twisted clockwise to engage.  If the LCD is active but nothing appears on the LED display, this is probably a hardware fault.
LED displays `i2cEr`, LCD blank or corrupt|Internal problem with the clock electronics.  Try pressing 'reboot' or cycling power.  If it persists, it may be a hardware fault.
Time and temperature displayed but not race time during race|Check the race is running.  Check the display on the back of the clock and confirm that it has a WiFi connection to the `BHPC_Timing` SSID (as broadcast by the wireless router in the flightcase with the tag reader).  The `WiFi` LED should illuminate steadily to indicate a connection.  If it fails to connect, check the router is operating, and perhaps move the clock closer to the router.
WiFi connected, but still no race time|If the `WebSock` LED does not light, the clock's connection to the CrossMgr PC may be misconfigured.  Check the clock documentation for more information.
Incorrect time of day|This should resolve itself automatically within a couple of minutes of connecting to the laptop and/or GPS time source via the wireless network.  The clock has its own battery-backed real-time clock; if this happens repeatedly the battery may need replacing.
Incorrect race time|This should only happen if the network connection has been lost during a race, and even then it should only drift by a matter of seconds.  Check the wireless router and try rebooting the clock or cycling power to re-establish the connection.  Otherwise, something may have gone hideously wrong with CrossMgr, and you have bigger issues.
Race time 'jumps'|Not a fault; the latency of the connection to CrossMgr is unpredictable, and the time may be stepped if it drifts too far.
LED display corrupted (part of it refreshing, while other parts remain unchanged)|This is a hardware fault, likely with one of the dozens of delicate solder joints that make up the LED display, and not the sort of thing that can be repaired at the track-side.  Disconnect the power so that riders aren't mislead by the corrupt display.
Clock rotates in the wind|The interface with the clock stand is keyed to prevent rotation by means of an allen bolt protruding from the end of the stand.  Ensure that the bolt has aligned with the hole in the bottom of the 'top hat' by slowly rotating the clock on the stand until you feel it drop into place.  Further rotation is still possible by hand (at risk of damage to the retaining pins), but the additional friction of the stand's clamps should be sufficient to keep it in place.  If the wind is particularly strong, remove the clock from the stand so it can't fall over.
No rider number for sprint|Not a fault.  The sprint timer did not supply a bib number, perhaps because it could not identify the rider.
No unit for sprint speed|Not a fault.  There's no good way to display a 'k' or an 'm' on a 7-segment display without resorting to Braille.  The unit will be whatever the sprint timer is set to.




The 'reboot' button will reboot the clock and immediately attempt to re-establish the connection.

If the network connection is not available, the clock may be operated manually as a simple stopwatch using the Start/Stop/Clear buttons.  When operating as a manual stopwatch all network functions are disabled.

### Live results not updating

Don't get too deep in the weeds troubleshooting live results issues during the race; collecting high-quality timing data is your priority!

Check the laptop has internet access.  (Is it connected to a WiFi network or hotspot?)  The upload process will use exponential backoff - if the connection is very slow it may update very infrequently.

Check the CrossMgr FTP properties.  If the settings are correct, this is probably a problem with the internet connection.

If the index page does not link to the current race, results may be uploaded but people won't be able to find them; re-publish the index.html.


## After the race

First, **back up all the race data**.  I like to create a .zip archive of the day's files before correcting and merging race results.

### Race duration issues

Setting the race duration for a criterium isn't an exact science.  Usually you want the next integer minute after the leader gets the bell, but you may need to tweak this if it gives the wrong number of laps.  If the lap times are less than a minute (eg. on a velodrome) you may need to remove some lap times to make it work.  Fixed duration or laps races avoid this issue.

### Problems merging races

Warnings that a rider is in both races are *probably* just because they've loitered near the finish line during the other group's race.  The spurious lap times will be filtered out automatically in the usual way, and are therefore harmless.

If something serious goes wrong during a merge it probably needs Kim to meditate on the data with the aid of a full development environment.  If that's not an option, you may have to export to Excel and attempt to combine the results using spreadsheets or something.

### Ranking seems wrong

If ranking by average speed, ensure that all categories have a lap distance set.

### Spurious (Women) classes in SeriesMgr table

A catgeory's gender has been set incorrectly in one of the race files, causing a separate category to be created (look at who's ranked in it to work out which race).  CrossMgr sometimes interprets categories with only female riders as being women's categories when they should be 'Open'.  Fix the categories in the relevant race, and refresh the results.


## Misc

### Clock synchronisation

Race timing depends on being able to synchronise the real-time clock in the tag reader (and where applicable, sprint timer) with that of the laptop.  While clock drift is negligible over the course of a race, this is complicated when Windows has a connection to the wider internet, allowing it to synchronise with an NTP server.  Symptoms of clock drift include triggers being offset in CrossMgrVideo and tag reads being erroneously 'skipped' by CrossMgrImpinj.

In an attempt to migitage these problems, our version of CrossMgrImpinj has been modified to provide the ability to monitor and correct the offset between the laptop and tag reader's clock in real time.

Additionally, a GPS-based stratum 1 NTP time server has been installed in the flightcase with the tag reader.  Once it has obtained a time signal, the laptop, router, tag reader and race clock should synchronise their real-time clocks to it over the course of a few minutes.  If this is done before the start of a race, everything should stay synchronised to within a few milliseconds.  On this basis, it is important to power up the flightcase as early as possible in the setup process, so it may begin to acquire a GPS fix.


### Dodgy Ethernet cable

If you need to mate an XLR-style Ethernet plug with a normal socket for troubleshooting, you can unscrew the shell by hand to reveal a conventional RJ45 plug.  Don't lose the shell.  RJ45 connectors don't react well to mud or having their tabs snapped off, so it's worth having a spare Ethernet cable to hand.

### Laptop power supply

The delicate Acer 3*1.1mm DC barrel connector is a conspicuous single point of failure.  Treat it with care.  A dongle to allow the use of an alternative power supply is a work in progress.
