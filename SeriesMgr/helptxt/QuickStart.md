[TOC]

# Introduction
Welcome to SeriesMgr!

SeriesMgr makes is easy to combine results from multiple events into an overallseries.  Series can be scored by:

* Points for Place (can be different for each event)
* Total Time
* Percentage of Finish Time / Winner's Time
* [TrueSkill](https://en.wikipedia.org/wiki/TrueSkill) - a ranking of the "best" competitors

SeriesMgr reads CrossMgr race files directly.  It also reads Excel spreadsheets.

# Identification

## Rider Identification

SeriesMgr uses __First Name__, __Last Name__ and __License__ to identify riders.  The fields __must__ be specified in the CrossMgr or Spreadsheet input.  Upper/lower case does not matter.

The __First Name__, __Last Name__ and __License__ (ignoring case) all must match *exactly* for a result to be considered from the same rider.  For example, "James Smith", "Jim Smith", "Jimmy Smith" and "J. Smith" will all be treated as different riders.

If you don't have a __License__ and want to use name only, you must still have a __License__ column in the input, but the values can be blank.

However, be aware that without a __License__ field you might get two people with the same name (eg. two Jim Smiths).  Because SeriesMgr cannot tell them apart, it will combine their results!

Of course, you can still differentiate the names (for example, change one "Jim Smith" to "James Smith").  You must do this in the race input as there is no way to fix this up after the fact.

SeriesMgr also supports __aliaes__ for names, teams and licenses.  Aliases allow you to map common misspellings/alternate spellings to a standard name.

## Category Identification

For CrossMgr races, the rider's category comes from the CrossMgr Categories screen based on the bib number ranges.  To control which Categories are considered in SeriesMgr, set the flag in the CrossMgr Categories screen.  For example, if you have a Beginner category you don't want to consider in a Series (or a Custom category, etc), make sure to uncheck the Series flag.

For spreadsheet races, SeriesMgr uses a __Race Category__ column or, if missing, the Excel Sheet name.  If using the Sheet name, all results in that sheet will be taken to be in that Category.

SeriesMgr expects that the Category name is unique with regards to gender.
For example, using "Cat 1/2" as the Category for both Men and Women won't work - SeriesMgr will rank everyone together in the same category.  To fix this, make sure the Category name contains the gender.  For example, "Cat 1/2 (Men)" and "Cat 1/2 (Women)" will work.

CrossMgr categories always contain the category gender in brackets on the end (for example, "Cat 1/2 (Men)").

## Team Identification

SeriesMgr computes Team results, but you don't have to use them.

If you are interested in Team results, the Team names must be present in the Race files.  Sometimes there is considerable variation in the same Team name (for example, "Beaches Cycling Club", "Beaches Cycling", "BCC").  You can map variations to a single name in the Team Alias screen.

Blank team names, or "Independent", "Ind.", "Ind" are treated separately and are not combined into an overall result.

# Races Screen

At the top, add the name of your Series and Organizer.

In each row, add the race, either a CrossMgr race file (.cmn) or an Excel sheet (.xlsx, .xls).

You can change the order of races by dragging the row in the grey column to the left of the race name.

* The __Event__ column can be used to give a common name to a group of races eg. those that take place on the same day, or at the same venue.  Races with the same text in the 'Event' field will get an 'Event Total' column in the HTML output, and be considered together for "Consider best n Events" purposes (see __Scoring Criteria__).  Otherwise, leave this blank.
* The __Race__ column can be edited to change how the race name is displayed in the results.
* The __Grade__ column is used to break ties (more on that later too).
* The __Points__ column is the points structure to be used to score that race.  This only applies if you are scoring by Points (more on that later).
* The __Team Points__ column is the points structure used to score teams for that race.

__Note:__  If specified, __Team Points__ is used to score the teams in the event.  The process is as follows:

1. Riders are first ranked individually by their __Points__ and finish order, as usual.
1. Individual points of the top N riders of each team are added together to create the __Team Score__.
1. Teams are ordered by decreasing __Team Score__, with ties being broken by the best result of top N team members.  This is the __Team Rank__.  Teams with no individually earned points will still be part of the __Team Rank__ - they will be ordered by the best team member's result.
1. __Team Points__ is then used to get the Points for Place from the __Team Rank__, and this is added to the team's overall result.
1. If __Team Points__ is unspecified, the __Team Score__ is added to the team's overall result.

For example, you could assign 10,8,6,5,4,3,2,1 as the points assigned for the team finish order.

## CrossMgr Races

These require the CrossMgr race file (.cmn) __and__ the accompanying Excel sheet containing the rider data.  Both files should be in the same folder, but only add the CrossMgr race file to SeriesMgr.

It is a good practice to open each CrossMgr race beforehand to ensure that its Excel file is accessible and the results are shown properly.

## Excel Races

SeriesMgr supports race results in Excel (either .xls or .xlsx).  SeriesMgr will read Excel sheets in USAC upload format.

1. Starting form the top of the sheet, SeriesMgr looks for a cell in the first column that is one of 'Pos','Pos.','Rank', 'Rider Place' or 'Place'.  This is the __Header Row__.  Rows about the __Header Row__ are ignored.
1. The __Header Row__ can contain other header values as described in the table below.  Unrecognized headers are ignored.  Upper/lower case does not matter.
1. Except for the __Pos__ column (or one of its equivalents) which must be in the first column, headers can be in any order.
1. Appropriate data are expected in the columns under each header.  Other data not under a header is ignored.
1. If the __Category__ column is not present, the rider's category is taken from the Excel sheet name.  This allows the Excel sheet to be organized with each Category name in each sheet.  Alternatively, if the __Category__ column is present, multiple categories can be submitted all in one sheet.

| Header        | Status | Description
|---------------|:-------------|:-------------
| 'Pos','Pos.','Rank', 'Rider Place' or 'Place'           | Required | Finish position of the rider starting from 1.  May also contain DNF, DQ, DNS, PUL.
| 'LastName','Last Name','LName','Rider Last Name','Name'| Required | Rider's last name
| 'FirstName','First Name','FName','Rider First Name'| Required | Rider's first name
| 'Licence','Licence #','Rider License #'| Required | Rider's license number
| 'Race Category','RaceCategory','Race_Category' | Optional | Rider Category.  If not present, the Category will be taken from the Excel Sheet name.
| 'Team','Team Name','TeamName','Rider Team','Club','Club Name','ClubName','Rider Club','Rider Club/Team' | Optional | Rider's team name.
| 'Time','Tm.','Rider Time' | Finish Time

# Scoring Criteria Screen

This screen configures how the series is scored.

## Score Competitors and Teams by:

| Selection | Description
|-----------|------------
| Points    | Score the series by total Points by Rank.  Races can use the same __Points Structures__, or use different ones.
| Time | Score the series by total Time.
| Percent Time | Points computed by Winner's Time / Rider's Time.
| TrueSkill | Use the [TrueSkill](https://en.wikipedia.org/wiki/TrueSkill) technique to score the Series.


__Note 1:__  If scoring by __Time__ or __Percent Time__, make sure that all riders that did not complete all laps in the race are marked as DNF.  Otherwise SeriesMgr will use their shorted finish times in its calculations.

__Node 2:__  If scoring by __Time__, and competitors have competed fewer that __Best Results__ events (see below), SeriesMgr will rank by decreasing events completed, then total time.  This prevents riders with missing events (and lower total time) to be ranked ahead of riders who have completed all events.

__Note 3:__ TrueSkill is a technique to find the "best" competitor in a series.  For example, if rider A consistently finishes ahead of B, and B consistently finishes ahead of C, TrueSkill will rank A ahead of than C *even though A and C have never raced each other*.

Or, say A has won 9 of a 12-race series and B wins the last 3.  TrueSkill will rank B ahead of A because she consistently beat A.
This contrasts with a series scored by Points, where A's wins earn her a greater number of points than B.

Or, if a rider consistently finishes in the same group, his score will not increase as he has not improved relative to other riders.  This contrasts with a series scored by Points where the rider will earn points for participating iregardless of unchanging fitness or skills.

For full details, see [here](https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/).

__Note 4:__ Of course, scoring a series by Points can be an incentive for riders to participate!  That's good for organizers.  TrueSkill is interesting, and can be good for predicting the results of future races, but isn't appropriate for a series.

## Consider Points or Time Bonuses from CrossMgr Primes

This option indicates that Points (for Series scored by Points) or Time Bonuses (for Series scored by Time) in the CrossMgr Primes screen should be considered.

## Consider Best Results

If you wish the Series to be scored based on the top N __Best__ results, specify it here.  (Not available for TrueSkill scoring)

## Consider Best Events

If you wish the Series to be scored based on the top N __Best__ events, specify it here.  (Not available for TrueSkill scoring)

## Must have Completed

If you wish to set a __minimum__ number of events before a Rider's should be included in the series results, specify it here.

## Tie Breaking Rules

The options available to break ties are fairly straightforward.

An exception is Grades.  Grades are specified by Race in the __Races__ screen.
__Grades__ can have values A-Z.  Results for a higher grade race take precedence over results for a lower-grade race in tie breaking.

For example, say riders A and B are tied in every way, but finished A=1, B=2 in the Regional Championship.  If you set the Regional Championship race to Grade A and all other races to Grade B, that race will "take priority" in the number of 1st place finishes to break the tie.

__Note:__ __Grades__ only apply when breaking ties for series scored by Points.

## Points Structures Screen

Specify the Points Structure(s) to use to score your races.
When scoring a series by Time, Time Percentage or TrueSkill, Points Structures are not considered.

You can specify any number of Points Structures, then select different ones in the Races screen.  This allows you to have different points-by-place earned by race.

The Points earned may stay the same or decrease by place.  For example, 5, 3, 2, 1, 1, 1 is a valid points structure.  There is no limit to the number of Points per place.

__Participation__ is the number of points earned for finishing a race (non-DNF).  You can also specify points earned for DNF, however, be careful as this may encourage riders to DNF on purpose just to earn the point.

# Category Options Screen

This screen allows you to change the sequence of the Categories in the output.  You can also control which categories are published, as well as the top N riders considered for the team results, or whether the Nth team member's result is to be used.

# Upgrades Screen

The Upgrades screen allows you to specify how points are handled if a rider upgrades during the season.

Follow the on-screen instructions.  Specify the upgrade progression of Categories (comma separated), then the Factor which indicates the fraction of points carried forward from the previous category.

If you don't want points earned in a previous category to be carried forward at all, specify the upgrade progression and set the Factor to 0.0.

In this way, SeriesMgr will purge riders from the previous category.  This prevents the possibility that an upgraded rider could win his/her old category.

# Name Aliases Screen

Use this screen to specify name aliases to fix misspellings in your given Race Results.  This is easier than fixing each race file or spreadsheet.

# License Aliases Screen

Use this screen to specify license aliases to fix misspellings in your given Race Results.

# Machine Aliases Screen

Use this screen to specify machine aliases to fix misspellings in your given Race Results.

# Team Aliases Screen

Use this screen to specify team aliases to fix misspellings in your given Race Results.

# Results Screen

Shows the individual SeriesResult for each category.  The Refresh button will recompute the results and is necessary if you have changed one of the Race files.

The publish buttons are fairly self-explanitory.  __Publish to HTML with (S)FTP__ will open a dialog where you can enter FTP/SFTP server details.

The __Post Publish Cmd__ is a command that is run after the publish.  This allows you to post-process the results (for example, copy them somewhere).  As per the Windows shell standard, you can use %* to refer to all files created by SeriesMgr in the publish.

# Team Results Screen

Similar to individual results, but for teams.

SeriesMgr treats blank team names, or teams with the value "Independent"/"Ind."/"Ind" (case independent) differently.  Specifically, it treats these entries all as "Independent" and will not accumulate points for them.

For example, all independent riders (or riders without a team) it will not show up under team "Independent".
