
[TOC]

# Web

## Introduction

Riders and spectators appreciate live results at the race - it creates a richer experience for the participants and creates a more professional impression for you.

Like CrossMgr, SprintTimer makes it __extremely__ easy to publish real-time results at race on a local wireless network.
SprintTimer itself acts like a web server and serves up real-time content from its race data.

Of course, FTP publish is still available in SprintTimer (see ([SFTP][] for details) and is great for publishing to a public web site.

### Step 1:
__Make sure the SprintTimer computer is connected to a Wifi Network.__

1. The Wifi does not have to be connected to the external internet.  It is better if it isn't as members of the public will be connecting to it to get the race results on site.
1. Make sure the Wifi is __not__ password protected.  Riders and spectators need to connect to it.
1. If you are not using a chip reader, you can just connect the SprintTimer computer to a local wireless network produced from a wireless router.
1. If you are using a chip reader with SprintTimer, use a cable plugged into a wireless router to connect the SprintTimer computer to the chip reader.

### Step 2:
__Publish and Share the Page with Race Attendees__

1. SprintTimer makes sharing the results page easy.  On the __Index Page__ (see below), click on the __Share__ link.
1. Print out, or otherwise share the QR Code with race attendees and participants.  Participants connect to your local Wifi network, then using their QR Code app, they can instantly connect to the live results.  Alternatively, they can type in the url listed on the page.
1. Once connected, participants can easily share their connected by clickong in the __Share__ link right on the page.  This shows the QR Code page which makes it easy for other participants to get access to the page.

That's it!

## Current and Previous Race Results Web Pages

Although the Index page makes it convenient to show results from races, if you want to show live results on a screen at the event, it is more convenient to have one web page that follows the current race so you don't have to change it during the event.

There are two additional URLs that are recognized by CrossMgr/SprintTimer:

* CurrentResults.html
* PreviousResults.html

Current and Previous race results are displayed on the web page.

To get to these pages, open the Index page, then type "CurrentResults.html" or "PreviousResults.html" to the end of the browser's URL.

CurrentResults.html follows the running race in SprintTimer.
PreviousResults.html is updated when a next race starts.

These pages attempt to reconnect to CrossMgr/SprintTimer if they lose their connection.  You can also press the browser Refresh button.

Test this out yourself.  Start a Mass Start Race Simulation, open the Index page, and type "CurrentResults.html" in the browser's URL.
Switch the CurrentResults to Kiosk mode by selecting "Kiosk" in the dropdown next to the "Results".
To quick Kiosk mode, remove the options after the "?" in the URL.

### Notes:
__Remember:__ live results are a direct connection between your SprintTimer race and the web.  All changes you make will be immediately visible.  Use caution.

__Multiple versions of CrossMgr/SprintTimer open at the same time:__  The first instance open will act as the web server.  If the first on is closed, another will take over after a few seconds.

## Index Page
Opens a browser showing the SprintTimer web index page.

The current race is connected to real-time SprintTimer data.
Other races in the same folder will also be shown.

## QR Code Share Page
Opens a browser and loads the SprintTimer web QR Code Share page.

Publish this to allow people to connect to real-time results or the TTCountDown page.
Print this out and post it at the race.  This will allow people to easily access the real-time results.

## Controlling Results Web Page

### Changing the Results Web Page Format

On the Results web page there is a dropdown at the top which normally shows "Results".
This dropdown supports other display modes:

Mode|Description
:---|:----------
Results|Default.  Shows the results of the competition with animation.
Kiosk|Enables Kiosk Mode.  This cycles through each category showing one at a time.
Kiosk A|Enable Kiosk Arrival Mode.  Similar to Kiosk Mode, however, the riders are shown in reverse rank.  This allows finishing riders to see their finish time without being scrolled off the bottom of the screen.

### Results Web Page Parameters

The SprintTimer web page supports configuration through parameters instead of changing them on the screen.  These are passed to the web page in the usual manner: 

    [page_url]?param1=value&param1=value.

Parameter|Value|Description
:--------|:----|:----------
kioskMode|t or f|Enables Kiosk Mode.  Designed for a live results screen, in Kiosk Mode, one category is shown at a time, and all categories are cycled through.
arrivalMode|t or f|Enables Arrival Mode and only works if Kiosk Mode is set.  Designed for Gran Fondos, this options shows rider in reverse order (i.e. last rider first).  This makes it easy for finishing riders to see their time.  If riders are shown first-to-last, arriving riders are scrolled off the screen and cannot see their time easily.
lang|en or fr or es|Set default language.  Supports English, French and Spanish.  This just sets the default Language.  The display language can still be changed on the page.
highlight|list of comma separated bib numbers|Numbers to highlight in the results (for example, "highlight=31,21,15")
raceCat|race category|A race category to show by default instead of all categories.

Example:

    [page_url]?kioskMode=t&arrivalMode=t&lang=fr

Enable Kiosk Mode, enable Arrival Mode and set default language to French.
