# ChipReader

If using CrossMgrImpinj or CrossMgrAlien to talk to the Impinj or Alien reader, make sure those programs are running and the reader is plugged in, on the network, etc.  Then skip to "Do Reader Test".

__JChip:__ make sure you have your [JChip Documentation](http://mts.greentag.to/ControlPanelSoftManual.pdf) ready if you are configuring JChip for the first time.

__RaceResult:__ make sure your RaceResult reader is plugged into the network.

__JChip:__ The JChip Setup Dialog provides the needed parameters to allow you to configure JChip.  Go to the "7 Setting of Connections" section in the JChip "Control Panel Soft Manual" and configure a JChip connection as follows:

__MyLaps:__ configure your MyLaps client(s) to connect to the SprintTimer computer using port 3097 (the default).

__CrossMgrImpinj and CrossMgrAlien bridge:__ SprintTimer will find these programs automatically as they are running on the same machine.

SprintTimer communicates with the reader through a TCP/IP interface (that is, an internet connection).  This can be done with cable or wireless.  SprintTimer listens for a connection on all network connections including cable and wireless.  Check what hardware you need to accomplish this.

Field|Value|Description
:----|:----|:----------
Type|JChip/Impinj/Alien or RaceResult|The type of reader you are using.
Remote IP Address|One of the IP addresses shown on the screen|__JChip/Impinj/Alien:__ this is the IP address of the SprintTimer computer.  If there are more then one, one is generally for the LAN and the other is for the wireless connection.  To tell which is which, on Windows, in a "cmd" window, run "ipconfig".  On Mac/Linux, open a terminal and run "ifconfig".  Choose the IP address which matches you connection - LAN or wireless that you are using to connect the JChip receiver.  __RaceResult:__ this is the IP address of the RaceResult reader.  If you are on a LAN, the __AutoConnect__ button should find the reader automatically.  If not, or you are using a static IP, enter the IP of the RaceResult reader here.
Remote Port|53135 or 3601|__JChip/Impnj/Alien:__ port on the SprintTimer computer that JChip reader or bridge programs connect to.  __RaceResult__ port that SprintTimer uses to talk to RaceResult.  You should not have to change these.

__JChip__

The __Remote IP Address__ will be the one shown in SprintTimer.  Don't worry about the other JChip fields, however, the CrossMgr connection must be checked for "Use".
You may have to power down/power up JChip after making this change.

__RaceResult__

The __Remote IP Address__ is the address of the RaceResult reader.  If the AutoDetect button cannot find it on the LAN, of if you are using a fixed IP, you will have to enter it manually.

__MyLaps__

The MyLaps reader must be configured to connect to the SprintTimer computer on port 3097 (the default).

Be extra careful to ensure that the the MyLaps reader and the SprintTimer computer have the same clock time as there is no way for SprintTimer to synchronize to the MyLaps clock automatically.
The clocks should be synchronized automatically if both the MyLaps reader and the SprintTimer computer are connected to the internet.

#### Reader Test

Press the "Start RFID Test" button in SprintTimer.  This tells SprintTimer to connect to the reader and start processing tag reads.

You may receive a warning if you do not have an Excel sheet configured.
If you just want to test the receiver, you don't need to worry about the warning.  If you are trying to use RFID tags during a race, you will need a properly configured Excel sheet to associate the tags to the rider information.

__JChip:__ turn on the JChip receiver.  In the Messages section, you should soon see the connection succeed.  If not, check that you have the correct "Remote IP Address" and "Remote Port".  Make sure you open port 50353 on your operating system.

__RaceResult:__ make sure it is on and plugged into the network.  If SprintTimer cannot find it, you may need to open port 3601 in Windows.

__Impinj/Alien__: ensure the CrossMgrImpinj and CrossMgrAlien programs are running.  Make sure you open port 50353 and port 5084 on your operating system.

After starting the test, you should immediately see the connection between SprintTimer and the reader..

If Windows asks you if it is OK for SprintTimer to open a port - don't worry - it's OK.

Now, walk through the antenna (or across the matt) with some chips.  You should see the connection and tag information showing up in the "Messages" section.  Something like this:

>    listening for RFID connection...  
>    *******************************************  
>    connected: RFID receiver  
>    waiting: for RFID receiver to respond  
>    receiver name: JCHIP-TEST12  
>    transmitting: GT command to RFID receiver (gettime)  
>    getTime: 013005032=14:00:50.32  
>    timeAdjustment: RFID time will be adjusted by 0:00:00.02 to match computer  
>    transmitting: S0000 command to RFID receiver (start transmission)  
>    1: tag=413A74, time=2012-07-24 14:00:50.3510, Bib=not found  
>    2: tag=413A3B, time=2012-07-24 14:00:50.3510, Bib=not found  
>    ...  

You can see some of the nuts-and-bolts of the communication between the two systems.

Meanwhile, the "Bibs seen" section will maintain a list of the riders whose tags have been reported by the reader during the test - this is useful for determining whether riders have working tags - just herd them through the finish line while the RFID test is in progress.  The number in brackets is the number of unique tag IDs that have been seen for that rider (useful for determining if multiple tags are reading properly).  Riders who have not been seen yet will be greyed out and appear at the bottom of the list.  Press the "Clear seen bibs list" button to reset the count.

The "Send bib numbers to race clock during test" option causes rider numbers to be output on the lapcounter websocket as the tag reads arrive.  This uses an extension to the protocol designed for the BHPC sprint timer; it is not (currently) supported by the lap counter web page.

When you have finished testing, press the "Stop RFID Test" button or close the dialog.

It is recommended that you test the RFID receiver connection before every race.
