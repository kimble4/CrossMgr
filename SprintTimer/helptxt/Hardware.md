[TOC]

## Sprint Timer Unit
### Overview

The Sprint-O-Matic is a hastily cobbled-together piece of prototype-quality hardware.  (Try not to break it!)

This was designed for simplicity around the ESP32 microcontroller, using off-the-shelf modules for low cost and ease of assembly.  Apart from the two test buttons there are no controls on the unit itself; all configuration (in as little as any is needed) should be done via the connected computer.

### Theory of operation

#### Latch inputs
A rider cycles between two timing gates (herein referred to as "T1" and "T2" respectively).  These may be some kind of mechanical switch, optical beam-break, or whatever.  When a gate is triggered it momentarily completes a circuit as the rider passes through.  Each of these triggers a high-speed [latch circuit](https://en.wikipedia.org/wiki/Flip-flop_(electronics)), which generates an [interrupt](https://en.wikipedia.org/wiki/Interrupt) in the ESP32 microcontroller.  The latches are only reset after a timing run has completed, this neatly avoids having to de-bounce the input signal (typically a HPV will trigger the timing gate more than once as it passes).

#### Hardware timer
The ESP32 contains a hardware timer that runs at a nominal 40MHz, derived from its crystal oscillator frequency of 240MHz.  When interrupts are received, the current value of this timer is stored.  This allows the time it takes for the rider to pass between gates to be measured with a high degree of precision.  This oscillator frequency is not stable with temperature, however.

#### GPS compensation
The sprint timer unit incorporates a GPS receiver module.  This has two main functions:

1. Setting the ESP32's Real Time Clock, so that the correct time of day may be recorded in the results.
1. Providing a accurate time signal, so that drift of the internal oscillator frequency can be measured and compensated for.

The time signal from the GPS takes the form of an electrical *Pulse Per Second*.  This also generates an interrupt in the ESP32.  Every second, the software calculates the true speed of the 40MHz hardware timer with respect to the PPS time signal.

When a sprint begins, the hardware timer is used to measure the time between the T1 trigger and the next PPS signal.  As the speed of the timer over this second is known, the measured time is corrected to obtain a true value.  Whole seconds are then counted by counting the PPS pulses.  When the T2 signal arrives, the time between the previous PPS and T2 is measured and corrected in the same way.  This allows for high accuracy to be maintained over an arbitrarily long period, irrespective of drift of the ESP32's oscillator frequency.

The limiting factor on precision is the ESP32's interrupt latency, which is of the order of tens of microseconds.  Overall precision is at least 0.1ms (that is, 1/10,000 of a second), which should be sufficient for sports timing.  (A different architecture could achieve much higher precision.)

##### Loss of GPS signal
This GPS compensation only works if the PPS time signal is available for the *entire* duration of the sprint.  In the event that a PPS pulse is missed, the software will fall back to using the 40MHz hardware timer directly without compensation (this will be flagged yellow on the [Data][] screen).  Additionally, sprint times are calculated independently using the system microseconds timer.  This is less precise and is also subject to oscillator drift, but serves as reassurance that the compensation algorithm has performed correctly.

In testing we found that oscillator drift at room temperatures was of the order of a millisecond in 5 minutes.  As such, this should not be a problem for courses of less than 1000 metres, unless the unit is subject to extreme temperatures.

#### Time of Day
Normally, the ESP32's real time clock is set from GPS time.  If a PPS signal is available this will be synced to microsecond precision, otherwise it will only be to the nearest second.  If a GPS fix is not available, the clock will be set from the host computer's time when it first connects, but no ongoing synchronisation is performed.  (This is intended as an interim measure while the GPS module acquires a fix.)

The time of day of T1 and T2 trigger times are recorded at the moment they happen.  It is therefore possible for the real time clock to be adjusted during a sprint, and for the difference between the times-of-day to differ from the sprint time recorded by the hardware timer.  This is Mostly Harmless, as the time-of-day values should only be used for sorting results, rather than calculating speed.


### Connections
The rear panel has the following sockets:

Port|Type|Purpose
:-------|:----|:----
5V Power|USB-B|For supplying 5 volt regulated DC to the timer, from a suitable USB power source.  (No data communications are performed on this port.)
Network|RJ45 in D-Size shell|100Mb Fast Ethernet connection to the host computer or Ethernet switch.  Both ruggedised XLR-style and normal RJ45 connectors will fit.  Power-over-Ethernet (802.3af or 48V passive) is accepted on this port, but *must not be connected at the same time as USB power*.
T1|3-pin XLR|Connection for the first timing gate.  Pinout is: 1=Ground, 2=12V supply, 3=active-low input (pulled up to 5V internally).
T2|3-pin XLR|Connection for the second timing gate.  Pinout is: 1=Ground, 2=12V supply, 3=active-low input (pulled up to 5V internally).
T1|RCA phono|Connection for the first timing gate.  Pinout is: shell=ground, tip=active-low input (pulled up to 5V internally).
T2|RCA phono|Connection for the second timing gate.  Pinout is: shell=ground, tip=active-low input (pulled up to 5V internally).

### SD Card slot
There is a slot for a MicroSD card on the left side of the unit.  Take care when inserting the card that it card is properly aligned with its holder, and does not end up rattling around inside the case.  To prevent data loss, do not remove the SD card while the timer is powered on.

The card should be formatted with the FAT32 filesystem.  Sprint data is automatically written to `data.csv`, while debugging information is written to `debug.txt` whenever the SD card is present.  These may be downloaded with the card in situ using a [web browser][WebInterface].

### Front panel
The front panel contains the LCD status display, the T1 and T2 latch LEDs and their associated test buttons.

#### Latch LEDs
Each of the timing gate inputs triggers a corresponding high-speed latch circuit.  When the latch is triggered, the LED will illuminate and the ESP32 microcontroller receives a single interrupt (this effectively filters out multiple triggers as a rider passes through the timing gate).  The latches are reset by the microcontroller under software control.

#### Test Buttons
These trigger the latch circuits in exactly the same way as a timing gate.  This is useful for testing, and to stop the timer after a spurious T1 event has been generated (eg. by someone inadvertently walking through the timing gate).

#### Status LCD
This is a simple 4-line text display, for optimal readability in bright sunlight.

##### Top line
This displays, from left to right:

1. Real time clock
1. Number of connected TCP/WebSocket clients
1. `SD` to indicate the SD card is present
1. Time source status (see below)
1. Number of GPS satellites locked

Time source status|Meaning
:-----|:----
`RTC`|The real-time clock has been set by the host computer.
`GPS`|Time has been obtained from GPS, but no Pulse-Per-Second signal is available.
`PPS`|Pulse-Ser-Second is active, and will be used to compensate the output of the internal timer.
`N/C`|The GPS module does not appear to be connected.  (This is a fault)
`N/D`|The GPS module is doing something, but is not returning valid data.  (This is a fault)

##### Second line
Display|Meaning
:------|:----
`RT clock not synced`|The timer is standing by, but the RTC has not yet been set.
`Waiting for GPS`|The timer is standing by, the RTC has been set, but there is no GPS fix.
`Waiting for PPS`|The timer is standing by, the RTC has been set to GPS time, but there is no Pulse-Per-Second signal.
`Waiting for T1`|The timer has a PPS signal, and is standing by.
`T1 = HH:MM:SS.DDD`|A Trap 1 event has been recorded at the displayed time of day.
`!  TESTING INPUTS  !`|[Input test mode][InputTestMode] is active.

##### Third line
Display|Meaning
:------|:----
`v20231213.1`|Firmware version
`Trap length nn.nnm`|The trap length in metres used to calculate riders' speeds.
`Waiting for T2...`|A sprint is currently being timed.
`T1 = HH:MM:SS.DDD`|A Trap 2 event has been recorded at the displayed time of day (ie. the sprint is over).
`! TIMING DISABLED !`|[Input test mode][InputTestMode] is active.

##### Lower line
Display|Meaning
:------|:----
`!ETH`|There is a problem with the Ethernet connection.
`IP=nnn.nnn.nnn.nnn`|The timer unit's IPv4 network address.  This is configured automatically using [DHCP](https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol).
`c0`|Which of the ESP32's cores the high-level application software is running on.  This should be "`c0`", if it reads "`c1`" a mistake has been made during firmware upload, and timing accuracy will be reduced.  (Core 1 should be dedicated to servicing the timing interrupts.)
`->nn seconds`|A sprint is in progress, this is an *estimate* of the duration.
`!PPS`|PPS signal was not available for the entire duration of the current sprint; GPS compensation of the internal timer will not be performed.
`#nnn`|The rider's bib number, if it has been determined by the SprintTimer application.
`n.nnns nn.nnnuuu`|Precise sprint time in seconds, calculated speed in units.
`n.nnns speed nn.nnn`|Precise sprint time in seconds, calculated speed in unknown units.

### Web Interface
The sprint timing unit has a web interface, which may be accessed by pointing a browser at the unit's IP address.  For example, `http://192.168.1.251/` where `192.168.1.251` is the IP address displayed on the lower line of the unit's display.  Note that this is using unencrypted HTTP on port 80.  Beware of modern browsers trying to use HTTPS, which won't connect, and disregard any security warnings.

The web interface gives a current status display similar to that on the LCD, but more verbose and self-explanatory.  Reload the page (usually by pressing F5) to refresh, it will not always update automatically.

Four buttons allow basic control of the timer:

Button|Function
:----|:----
Refresh|Immediately refreshes the page.
Clear|Clears the current sprint, even if it is in progress.
Settings|Takes you to a Settings page (see below).
Download CSV|Downloads the `data.csv` file from the timer's SD card.

Additionally, the version information may be clicked on to download the debugging log.

#### Settings page
This allows you to set the trap distance (in metres), select a unit for the speed display, or enable the input test mode.  Press 'Set' to apply the settings, or 'Back' to return to the main page.

### Input Test Mode
Input test mode can be enabled from the settings page of the web interface, or from the [Sprint Timer properties][SprintTimerProperties] of the SprintTimer application.

In test mode, the input latches are continuously reset by the microcontroller, with the effect that the [Latch LED][LatchLEDs] reflect the state of the inputs in real time.  This is useful for troubleshooting wiring problems and aligning optical beam-breaks.

### NTP server
The unit operates as a stratum 1 [NTP](https://en.wikipedia.org/wiki/Network_Time_Protocol) time server on UDP port 123.  This may be useful for synchronising the host computer's clock to GPS time.  If the PPS signal is not available, the stratum will be lowered accordingly.

### Debugging
Debugging data is recorded to debug.txt on the SD card.  This is also available in real-time by connecting a telnet client to TCP port 23.
