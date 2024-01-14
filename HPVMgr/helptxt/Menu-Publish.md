
[TOC]

# Publish

## Batch Publish Files...

This brings up a dialog that allows you to publish results in many formats.  __Publish All__ will update all the output file formats simultaneously so they are synchronized.  All output files are written to the same folder as the race file.

You can also generate individual output files by pressing the __Publish__ button.  __Publish__ will also open the application associated with the generated file (Excel for .xlsx, your browser for .html, etc.).

Some files have the option to publish with FTP to a remote server, allowing results to be published to a web site.  You need to configure the connection details of the remote FTP server to make this work (see [Properties][]).

### HTML
Publish the results as an HTML file.  Includes the Race Animation and the Chart if specified in [Properties][].

The HTML web page has a drop-down button next to the __Refresh__ button to control __Kiosk Mode__.
The options are __Results__ (regular), __Kiosk__ (__Kiosk Mode__ leader board) and __Kiosk Arrival__ (__Kiosk Mode__ with participants ordered by arrive time - most recent arrivals at the top).
__Kiosk Mode__ cycles through results for each category every 15 seconds.  It is useful to show results at live events.

__Kiosk Arrival__ mode is useful for Gran Fondos and Time Trials.
In this mode, the most recent finisher is shown at the top.
The position (both in the start wave and in any specific category) is shown in a separate column.

A competitor can quickly check his/her result at the top of the screen after crossing the finish rather than having to scroll down to the bottom of the screen.

__Tip:__ After selecting Kiosk mode, Press __F11__ to put the browser into full-screen mode (press F11 to exit full screen).  This shows the maximum screen area.

For automatic control, the HTML web page includes additional options that can be controlled by setting query values in the URL.
For example:

    <your-race>.html?kioskMode=t
   
This will put the page into __Kiosk Mode__.  In this mode, the page will automatically cycle through all categories while hiding the map, title, and all other non-essential information.  __Kiosk Mode__ is useful if you have a computer/big screen showing live results at the race.

	<your-race>.html?arrivalMode=t
	
In this mode, the most recent finisher is shown at the top of the results.

Modes can be combined together:

	<your-race>.html?kioskMode=t&arrivalMode=t

This combination combines category cycling with listing the latest result at the top.  Good for live Gran Fondos finishes.

You can also change the default language of the page:

	<your-race>.html?lang=__xx__
	
Where __xx__ is either __en__, __fr__ or __es__ for English, French or Spanish respectively.  When a language is specified with the __lang=xx__ option, it is shown first in the language list.

### Index HTML
Creates the Index (navigation) page for the event.

### Excel
Publish the results in Excel format (suitable for reading into SeriesMgr) one category per sheet.

### Post Publish Command

Runs a command after the publish.  This is useful if you want to move the files to another location, or perform other post-processing on the file.  You can use substitions in the command:

Substitution|Description
:-----------|:----------
%*         |Inserts all the published file names.
{=Value}    |Inserts a [Properties][] Notes value, for example {=EventName}, {=RaceDate}

### Details, Logic and Example of Live Results:

Publishing results during a race does not slow down or lock up SprintTimer even if it loses the connection with the FTP server or the publish fails.  This is because publishing is run in a separate background thread.  You will not notice it is happening.

Results are published with FTP in a way that balances response time with bandwidth.

You will see a publish latency of 4 seconds after each rider passes the traps, and no updates when there are no sprints.
The latency will increase when come through close together, to a maximum of 32 seconds.

The update logic was inspired by [exponential-backoff](http://en.wikipedia.org/wiki/Exponential_backoff), also used in TCP/IP.
The idea is to minimize bandwidth and while while maximizing response time.
