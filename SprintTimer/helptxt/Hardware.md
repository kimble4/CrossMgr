[TOC]

## Sprint Timer Unit
### Overview

The Sprint-O-Matic is a hastily cobbled-together piece of prototype-quality hardware.  (Try not to break it!)

This was designed for simplicity around the ESP32 microcontroller, using off-the-shelf modules for low cost and ease of assembly.  Apart from the two test buttons there are no controls on the unit iself; all configuration (in as little as any is needed) should be done via the connected computer.

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
Each of the timing gate inputs triggers a corresponding high-speed latch circuit.  When the latch is triggered, the LED will illuminate and the ESP32 the microcontroller receives a single interrupt (this effectively filters out multiple triggers as a rider passes through the timing gate).  The latches are reset by the internal microcontroller under software control.

#### Test Buttons
These trigger the latch circuits in exactly the same way as a timing gate.  This is useful for testing, and to stop the timer after a spurious T1 event has been generated (eg. by someone inadvertantly walking through the timing gate).

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
`PPP`|Pulse-Ser-Second is active, and will be used to compensate the output of the internal timer.
`N/C`|The GPS module does not appear to be connected.  (This is a fault)
`N/D`|The GPS module is doing something, but is not returning valid data.  (This is a fault)

##### Second line
Display|Meaning
:------|:----
`RT clock not synced`|The timer is standing by, but the RTC has not yet been set.
`Waiting for GPS`|The timer is standing by, the RTC has been set, but there is no GPS fix.
`Waiting for PPS`|The timer is standing by, the RTC has been set to GPS time, but there is no Pulse-Per-Second signal.
`Waiting for T1`|The timer has a PPS signal, and is standing by.
`T1 = HH:MM:SS.DDD`|A Trap 1 event has been recorded at the displayed time of day.
`!  TESTING INPUTS  !`|[Input test mode][InputTestMode] is active.

##### Third line
Display|Meaning
:------|:----
`v20231213.1`|Firmware version
`Trap length nn.nnm`|The trap length in metres used to calculate riders' speeds.
`Waiting for T2...`|A sprint is currently being timed.
`T1 = HH:MM:SS.DDD`|A Trap 2 event has been recorded at the displayed time of day (ie. the sprint is over).
`! TIMING DISABLED !`|[Input test mode][InputTestMode] is active.

##### Lower line
Display|Meaning
:------|:----
`!ETH`|There is a problem with the Ethernet connection.
`IP=nnn.nnn.nnn.nnn`|The timer unit's IPv4 network address.  This is configured automatically using [DHCP](https://en.wikipedia.org/wiki/Dynamic_Host_Configuration_Protocol).
`c0`|Which of the ESP32's cores the high-level application software is running on.  This should be "`c0`", if it reads "`c1`" a mistake has been made during firmware upload, and timing accuracy will be reduced.  (Core 1 should be dedicated to servicing the timing interrupts.)
`→nn seconds`|A sprint is in progress, this is an *estimate* of the duration.
`!PPS`|PPS signal was not available for the duration of the current sprint; GPS compensation of the internal timer will not be performed.
`#nnn`|The rider's bib number, if it has been determined by the SprintTimer application.
`n.nnns nn.nnnuuu`|Precise sprint time in seconds, calculated speed in units.
`n.nnns speed nn.nnn`|Precise sprint time in seconds, calculated speed in unknown units.

### Web Interface
The sprint timing unit has a web interface, which may be accessed by pointing a browser at the unit's IP address.  For example, [`http://192.168.1.251/`](http://1921.68.1.251) where `192.168.1.251` is the IP address displayed on the lower line of the unit's display.  Note that this is using unencrypted HTTP on port 80.  Beware of modern browsers trying to use HTTPS, wich won't connect, and disregard any security warnings.

The web interface gives a current status display similar to that on the LCD, but more verbose and self-explanatory.  Reload the page (usually by pressing <f5>) to refresh, it will not always update automatically.

Four buttons allow basic control of the timer:

Button|Function
:----|:----
Refresh|Immediately refreshes the page.
Clear|Clears the current sprint, even if it is in progress.
Settings|Takes you to a Settings page (see below).
Download CSV|Downloads the `data.csv` file from the timer's SD card.

Additionally, the version information may be clicked on to download the debugging log.

#### Settings page
This allows you to set the trap distance (in metres), select a unit for the speed display, or enable the input test mode.  Press 'Set' to apply the settings, and 'Back' to return to the main page.

#### Input Test Mode
This can be enabled from the settings page of the web interface, or from the [Sprint Timer properties][SprintTimerProperties] of the SprintTimer application.  In test mode, the input latches are continuously reset by the microcontroller, with the effect that the [Latch LED][LatchLEDs] reflect the state of the inputs in real time.  This is useful for troubleshooting wiring problems and aligning optical beam-breaks.
