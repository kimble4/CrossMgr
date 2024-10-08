import os
import re
#import io
import sys
#import time
#import copy
#import json
#import glob
#import shutil
#import random
import datetime
#import operator
import webbrowser
import platform
#import zipfile
#import hashlib

import wx
import wx.adv as adv
from wx.lib.wordwrap import wordwrap
#import wx.lib.imagebrowser as imagebrowser
import wx.lib.agw.flatnotebook as flatnotebook
from html import escape
#from urllib.parse import quote
#from collections import defaultdict

import locale
try:
	localDateFormat = locale.nl_langinfo( locale.D_FMT )
	localTimeFormat = locale.nl_langinfo( locale.T_FMT )
except Exception:
	localDateFormat = '%Y-%m-%d'
	localTimeFormat = '%H:%M'

import pickle
from argparse import ArgumentParser
#import xlwt
import xlsxwriter

import Utils

from AddExcelInfo import AddExcelInfo
#from LogPrintStackStderr import LogPrintStackStderr
from Data				import Data, ManualEntryDialog
#from ForecastHistory	import ForecastHistory
#from NumKeypad			import NumKeypad
#from Actions			import Actions
#from Gantt				import Gantt
#from History			import History
from RiderDetail		import RiderDetail
from Results			import Results
from Categories			import Categories
from Properties			import Properties, PropertiesDialog, BatchPublishPropertiesDialog
#from Recommendations	import Recommendations
#from RaceAnimation		import RaceAnimation
#from Search				import SearchDialog
#from Situation			import Situation
#from GapChart			import GapChart
#from LapCounter			import LapCounter
#from Announcer			import Announcer
#from Primes				import Primes, GetGrid
#from Prizes				import Prizes
#from HistogramPanel		import HistogramPanel
#from UnmatchedTagsGantt	import UnmatchedTagsGantt
import FtpWriteFile
from FtpWriteFile		import realTimeFtpPublish
#from SetAutoCorrect		import SetAutoCorrectDialog
#from DNSManager			import DNSManagerDialog
#from USACExport			import USACExport
#from UCIExport			import UCIExport
#from UCIExcel			import UCIExcel
#from VTTAExport			import VTTAExport
#from JPResultsExport	import JPResultsExport
#from CrossResultsExport	import CrossResultsExport
#from WebScorerExport	import WebScorerExport
from HelpSearch			import HelpSearchDialog, getHelpURL
from Utils				import logCall, logException
from FileDrop			import FileDrop
#from RaceDB				import RaceDB, RaceDBUpload
#from SimulateData		import SimulateData
from NonBusyCall		import NonBusyCall
#from Playback			import Playback
#from Pulled				import Pulled
#from TeamResults		import TeamResults
#from BibEnter			import BibEnter
#from MissingRiders 		import MissingRiders
#from BackgroundJobMgr	import BackgroundJobMgr
#from Restart			import Restart
#from ReissueBibs	 	import ReissueBibsDialog
#from GiveTimes 			import GiveTimesDialog
#from FinishLynx			import FinishLynxDialog
import BatchPublishAttrs
import Model
#import JChipSetup
#import JChipImport
#import RaceResultImport
import JChip
#import OrionImport
#import AlienImport
#import ImpinjImport
#import IpicoImport
#import OutputStreamer
#import GpxImport
#import CmnImport
from JSONTimer import JSONTimer
from Undo import undo
#from Printing			import CrossMgrPrintout, CrossMgrPrintoutPNG, CrossMgrPrintoutPDF, CrossMgrPodiumPrintout, getRaceCategories
#from Printing			import ChoosePrintCategoriesDialog, ChoosePrintCategoriesPodiumDialog
from ExportGrid			import ExportGrid
#import SimulationLapTimes
import Version
from ReadSignOnSheet	import GetExcelLink, ResetExcelLinkCache, ExcelLink, ReportFields, SyncExcelLink, IsValidRaceDBExcel, GetTagNums
from SetGraphic			import SetGraphicDialog
#from GetResults			import GetCategoryDetails, UnstartedRaceWrapper, GetLapDetails, GetAnimationData, ResetVersionRAM
#from PhotoFinish		import DeletePhotos, okTakePhoto
from SendPhotoRequests	import SendPhotoRequests
#from PhotoViewer		import PhotoViewerDialog
#from ReadTTStartTimesSheet import ImportTTStartTimes, AutoImportTTStartTimes
#from TemplateSubstitute import TemplateSubstitute
from GetMatchingExcelFile import GetMatchingExcelFile
#import ChangeRaceStartTime
#from PageDialog			import PageDialog
import ChipReader
import Flags
import WebServer
import ImageIO
from ModuleUnpickler import ModuleUnpickler
#import GpxTimesImport

now = datetime.datetime.now

#import traceback
#'''
#Monkey patch threading so we can see where each thread gets started.
#import traceback
#import types
#threading_start = threading.Thread.start
#def loggingThreadStart( self, *args, **kwargs ):
	#threading_start( self, *args, **kwargs )
	#print self
	#traceback.print_stack()
	#print '----------------------------------'
#threading.Thread.start = types.MethodType(loggingThreadStart, None, threading.Thread)
#'''
#----------------------------------------------------------------------------------

def ShowSplashScreen():
	bitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'SprintTimerSplash.png'), wx.BITMAP_TYPE_PNG )
	
	#Write in the version number into the bitmap.
	w, h = bitmap.GetSize()
	dc = wx.MemoryDC()
	dc.SelectObject( bitmap )
	fontHeight = h//10
	dc.SetFont( wx.Font( (0,fontHeight), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ) )
	v = Version.AppVerName.split('-',2)
	yText = int(h * 0.44)
	for i, v in enumerate(Version.AppVerName.split('-',2)):
		dc.DrawText( v.replace('SprintTimer','Version'), w // 20, yText + i*fontHeight )
		
	dc.SelectObject( wx.NullBitmap )
	
	showSeconds = 2.5
	adv.SplashScreen(bitmap, adv.SPLASH_CENTRE_ON_SCREEN|adv.SPLASH_TIMEOUT, int(showSeconds*1000), None)
			
#----------------------------------------------------------------------------------

def replaceJsonVar( s, varName, value ):
	return s.replace( '{} = null'.format(varName), '{} = {}'.format(varName, Utils.ToJson(value, separators=(',',':'))), 1 )

#----------------------------------------------------------------------------------
def AppendMenuItemBitmap( menu, id, name, help, bitmap ):
	mi = wx.MenuItem( menu, id, name, help )
	mi.SetBitmap( bitmap )
	menu.Append( mi )
	return mi


class MainWin( wx.Frame ):
	def __init__( self, parent, id = wx.ID_ANY, title='', size=(200,200) ):
		super().__init__(parent, id, title, size=size)

		Utils.setMainWin( self )
		
		self.callLaterProcessRfidRefresh = None	# Used for delayed updates after chip reads.
		self.numTimes = []
		
		self.sprintTimer = JSONTimer()
		self.sprintTimerClockDelta = float("NAN")
		
		self.nonBusyRefresh = NonBusyCall( self.refresh, min_millis=1500, max_millis=7500 )

		#Add code to configure file history.
		self.filehistory = wx.FileHistory(8)
		dataDir = Utils.getHomeDir()
		configFileName = os.path.join(dataDir, 'SprintTimer.cfg')
		self.config = wx.Config(appName="SprintTimer",
								vendorName="BHPC",
								localFilename=configFileName
		)
		self.filehistory.Load(self.config)
		
		self.fileName = None
		#self.numSelect = None
		
		#Setup the objects for the race clock.
		self.timer = wx.Timer( self, id=wx.ID_ANY )
		self.secondCount = 0
		self.Bind( wx.EVT_TIMER, self.updateRaceClock, self.timer )
		
		#Configure the main menu.
		self.menuBar = wx.MenuBar(wx.MB_DOCKABLE)

		#-----------------------------------------------------------------------
		self.fileMenu = wx.Menu()

		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_NEW, _("&New..."), _("Create a new race"), Utils.GetPngBitmap('document-new.png') )
		self.Bind(wx.EVT_MENU, self.menuNew, item )

		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_ANY, _("New Nex&t..."), _("Create a new race starting from the current race"), Utils.GetPngBitmap('document-new-next.png') )
		self.Bind(wx.EVT_MENU, self.menuNewNext, item )

		self.fileMenu.AppendSeparator()
		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_OPEN, _("&Open..."), _("Open a race"), Utils.GetPngBitmap('document-open.png') )
		self.Bind(wx.EVT_MENU, self.menuOpen, item )
		
		recent = wx.Menu()
		menu = self.fileMenu.AppendSubMenu( recent, _("Recent Fil&es") )
		menu.SetBitmap( Utils.GetPngBitmap('document-open-recent.png') )
		self.filehistory.UseMenu( recent )
		self.filehistory.AddFilesToMenu()
		
		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_EXIT, _("E&xit"), _("Exit SprintTimer"), Utils.GetPngBitmap('exit.png') )
		self.Bind(wx.EVT_MENU, self.menuExit, item )
		
		self.Bind(wx.EVT_MENU_RANGE, self.menuFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
		
		self.menuBar.Append( self.fileMenu, _("&File") )

		#-----------------------------------------------------------------------
		self.publishMenu = wx.Menu()
		
		item = AppendMenuItemBitmap( self.publishMenu, wx.ID_ANY,
							_("&Batch Publish Files..."), _("Publish Multiple Results File Formats"), Utils.GetPngBitmap('batch_process_icon.png') )
		self.Bind(wx.EVT_MENU, self.menuPublishBatch, item )
		
		#'''
		#self.publishMenu.AppendSeparator()
		
		item = AppendMenuItemBitmap( self.publishMenu, wx.ID_ANY,
							_("&HTML Publish..."), _("Publish Results as HTML (.html)"), Utils.GetPngBitmap('html-icon.png') )
		self.Bind(wx.EVT_MENU, self.menuPublishHtmlRaceResults, item )

		
		item = AppendMenuItemBitmap( self.publishMenu, wx.ID_ANY,
							_("&Excel Publish..."), _("Publish Results as an Excel Spreadsheet (.xls)"), Utils.GetPngBitmap('excel-icon.png') )
		self.Bind(wx.EVT_MENU, self.menuPublishAsExcel, item )
		
		
		self.menuBar.Append( self.publishMenu, _("&Publish") )
		
		#-----------------------------------------------------------------------
		self.editMenu = wx.Menu()
		item = self.undoMenuButton = wx.MenuItem( self.editMenu, wx.ID_UNDO , _("&Undo\tCtrl+Z"), _("Undo the last edit") )
		self.undoMenuButton.SetBitmap( Utils.GetPngBitmap('Undo-icon.png') )
		self.editMenu.Append( self.undoMenuButton )
		self.Bind(wx.EVT_MENU, self.menuUndo, item )
		self.undoMenuButton.Enable( False )
		
		self.redoMenuButton = wx.MenuItem( self.editMenu, wx.ID_REDO , _("&Redo\tCtrl+Y"), _("Redo the last edit") )
		self.redoMenuButton.SetBitmap( Utils.GetPngBitmap('Redo-icon.png') )
		item = self.editMenu.Append( self.redoMenuButton )
		self.Bind(wx.EVT_MENU, self.menuRedo, item )
		self.redoMenuButton.Enable( False )
		self.editMenu.AppendSeparator()
		
		self.editMenuItem = self.menuBar.Append( self.editMenu, _("&Edit") )

		#-----------------------------------------------------------------------
		self.dataMgmtMenu = wx.Menu()
		
		item = AppendMenuItemBitmap( self.dataMgmtMenu, wx.ID_ANY, _("&Link to External Excel Data..."), _("Link to information in an Excel spreadsheet"),
			Utils.GetPngBitmap('excel-icon.png') )
		self.Bind(wx.EVT_MENU, self.menuLinkExcel, item )
		
		item  = self.dataMgmtMenu.Append( wx.ID_ANY, _("Add sprint manually"), _("Add sprint manuallyx") )
		self.Bind(wx.EVT_MENU, self.menuAddManualSprint, item )
		
		self.menuBar.Append( self.dataMgmtMenu, _("&DataMgmt") )

		#----------------------------------------------------------------------------------------------

		#Configure the field of the display.

		bookStyle = (
			  flatnotebook.FNB_NO_X_BUTTON
			| flatnotebook.FNB_NODRAG
			| flatnotebook.FNB_DROPDOWN_TABS_LIST
			| flatnotebook.FNB_NO_NAV_BUTTONS
		)
		self.notebook = flatnotebook.FlatNotebook( self, 1000, agwStyle=bookStyle )
		self.notebook.SetBackgroundColour( wx.WHITE )
		self.notebook.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanging )
		
		self.fileDrop = FileDrop()	# Create a file drop target for all the main pages.
		
		#Add all the pages to the notebook.
		self.pages = []

		def addPage( page, name ):
			self.notebook.AddPage( page, name )
			self.pages.append( page )
			
		self.attrClassName = [
			[ 'data',			Data,				_('Data') ],
			#[ 'actions',		Actions,			_('Actions') ],
			#[ 'record',			NumKeypad,			_('Record') ],
			[ 'results',		Results,			_('Results') ],
			#[ 'pulled',			Pulled,				_('Pulled') ],
			#[ 'history',		History,			_('Passings') ],
			[ 'riderDetail',	RiderDetail,		_('RiderDetail') ],
			#[ 'gantt', 			Gantt,				_('Chart') ],
			#[ 'recommendations',Recommendations,	_('Recommendations') ],
			[ 'categories', 	Categories,			_('Categories') ],
			[ 'properties',		Properties,			_('Properties') ],
			#[ 'prizes',			Prizes,				_('Prizes') ],
			#[ 'primes',			Primes,				_('Primes') ],
			#[ 'raceAnimation',	RaceAnimation,		_('Animation') ],
			#[ 'situation',		Situation,			_('Situation') ],
			#[ 'gapChart',		GapChart,			_('GapChart') ],
			#[ 'lapCounter',		LapCounter,			_('LapCounter') ],
			#[ 'announcer',		Announcer,			_('Announcer') ],
			#[ 'histogram',		HistogramPanel,		_('Histogram') ],
			#[ 'teamResults',	TeamResults,		_('Team Results') ],
		]
		self.attrWindowSet = {'results', 'history', 'gantt', 'raceAnimation', 'gapChart', 'announcer', 'lapCounter', 'teamResults'}
		
		for i, (a, c, n) in enumerate(self.attrClassName):
			setattr( self, a, c(self.notebook) )
			getattr( self, a ).SetDropTarget( self.fileDrop )
			addPage( getattr(self, a), '{}. {}'.format(i+1, n) )
			setattr( self, 'i' + a[0].upper() + a[1:] + 'Page', i )
		
		self.toolsMenu = wx.Menu()
		
		self.startRaceMenuItem = self.toolsMenu.Append( wx.ID_ANY, _("&Start Recording"), _("Start the race") )
		self.Bind(wx.EVT_MENU, self.menuStartRace, self.startRaceMenuItem )
		self.startRaceMenuItem.Enable(False)
		
		self.finishRaceMenuItem = self.toolsMenu.Append( wx.ID_ANY, _("&Finish Recording"), _("Finish the race.") )
		self.Bind(wx.EVT_MENU, self.menuFinishRace, self.finishRaceMenuItem )
		self.finishRaceMenuItem.Enable(False)
		
		self.resumeRaceMenuItem = self.toolsMenu.Append( wx.ID_ANY, _("&Resume recording"), _("Restart a finished race.") )
		self.Bind(wx.EVT_MENU, self.menuRestartRace, self.resumeRaceMenuItem )
		self.resumeRaceMenuItem.Enable(False)
		
		self.toolsMenu.AppendSeparator()

		item = self.toolsMenu.Append( wx.ID_ANY, _("Copy Log File to &Clipboard..."), _("Copy Log File to Clipboard") )
		self.Bind(wx.EVT_MENU, self.menuCopyLogFileToClipboard, item )

		self.toolsMenu.AppendSeparator()
		
		item = self.toolsMenu.Append( wx.ID_ANY, _("Reset sprint timer"), _("Reset sprint timer") )
		self.Bind(wx.EVT_MENU, self.resetSprintTimer, item )
		
		self.menuBar.Append( self.toolsMenu, _("&Tools") )
		
		#-----------------------------------------------------------------------
		self.optionsMenu = wx.Menu()
		
		item = self.menuItemPlaySounds = self.optionsMenu.Append( wx.ID_ANY, _("&Play Sounds"), _("Play Sounds"), wx.ITEM_CHECK )
		self.playSounds = self.config.ReadBool('playSounds', True)
		self.menuItemPlaySounds.Check( self.playSounds )
		self.Bind( wx.EVT_MENU, self.menuPlaySounds, item )
		
		self.optionsMenu.AppendSeparator()
		item = self.menuItemLaunchExcelAfterPublishingResults = self.optionsMenu.Append( wx.ID_ANY,
			_("&Launch Excel after Publishing Results"),
			_("Launch Excel after Publishing Results"), wx.ITEM_CHECK )
		self.launchExcelAfterPublishingResults = self.config.ReadBool('menuLaunchExcelAfterPublishingResults', True)
		self.menuItemLaunchExcelAfterPublishingResults.Check( self.launchExcelAfterPublishingResults )
		self.Bind( wx.EVT_MENU, self.menuLaunchExcelAfterPublishingResults, item )
		
		#'''
		#self.optionsMenu.AppendSeparator()
		item = self.optionsMenu.Append( wx.ID_ANY, _("Set Contact &Email..."), _("Set Contact Email for HTML Output") )
		self.Bind(wx.EVT_MENU, self.menuSetContactEmail, item )
		
		item = self.optionsMenu.Append( wx.ID_ANY, _("Set &Graphic..."), _("Set Graphic") )
		self.Bind(wx.EVT_MENU, self.menuSetGraphic, item )
		#'''
		
		#self.optionsMenu.AppendSeparator()
		#item = self.optionsMenu.Append( wx.ID_ANY, _("Set Default Contact &Email..."), _("Set Default Contact Email") )
		#self.Bind(wx.EVT_MENU, self.menuSetDefaultContactEmail, item )
		
		#item = self.optionsMenu.Append( wx.ID_ANY, _("Set Default &Graphic..."), _("Set Default Graphic") )
		#self.Bind(wx.EVT_MENU, self.menuSetDefaultGraphic, item )
		
		self.menuBar.Append( self.optionsMenu, _("&Options") )
		

		#------------------------------------------------------------------------------
		#Create a menu for quick navigation
		self.pageMenu = wx.Menu()
		self.idPage = {}
		jumpToIds = []
		for i, p in enumerate(self.pages):
			name = self.notebook.GetPageText(i)
			if i <= 11:
				item = self.pageMenu.Append( wx.ID_ANY, '{}\tF{}'.format(name, i+1), '{} {}'.format(_('Jump to'), name) )
			else:
				item = self.pageMenu.Append( wx.ID_ANY, name, '{} {}'.format(_('Jump to'), name) )
			self.idPage[item.GetId()] = i
			self.Bind(wx.EVT_MENU, self.menuShowPage, item )
			jumpToIds.append( item.GetId() )
			
		self.menuBar.Append( self.pageMenu, _("&JumpTo") )
		
		#------------------------------------------------------------------------------
		self.webMenu = wx.Menu()

		item = self.webMenu.Append( wx.ID_ANY, _("&Index Page..."), _("Index Page...") )
		self.Bind(wx.EVT_MENU, self.menuWebIndexPage, item )

		item = self.webMenu.Append( wx.ID_ANY, _("&QR Code Share Page..."), _("QR Code Share Page...") )
		self.Bind(wx.EVT_MENU, self.menuWebQRCodePage, item )
		
		self.menuBar.Append( self.webMenu, _("&Web") )
		
		#------------------------------------------------------------------------------
		self.helpMenu = wx.Menu()
		
		item = self.helpMenu.Append( wx.ID_HELP, _("&Help..."), _("Help with SprintTimer...") )
		self.Bind(wx.EVT_MENU, self.menuHelp, item )
		
		item = self.helpMenu.Append( wx.ID_ANY, _("Help &Search..."), _("Search Help...") )
		self.Bind(wx.EVT_MENU, self.menuHelpSearch, item )
		self.helpSearch = HelpSearchDialog( self, title=_('Help Search') )

		item = self.helpMenu.Append( wx.ID_ABOUT , _("&About..."), _("About SprintTimer...") )
		self.Bind(wx.EVT_MENU, self.menuAbout, item )

		self.menuBar.Append( self.helpMenu, _("&Help") )

		#------------------------------------------------------------------------------
		#------------------------------------------------------------------------------
		#------------------------------------------------------------------------------
		self.SetMenuBar( self.menuBar )

		#------------------------------------------------------------------------------
		#Set the accelerator table so we can switch windows with the function keys.
		accTable = [(wx.ACCEL_NORMAL, wx.WXK_F1 + i, jumpToIds[i]) for i in range(min(11,len(jumpToIds)))]
		#self.contextHelpID = wx.ID_HELP
		#self.Bind(wx.EVT_MENU, self.onContextHelp, id=self.contextHelpID )
		#accTable.append( (wx.ACCEL_CTRL, ord('H'), self.contextHelpID) )
		#accTable.append( (wx.ACCEL_SHIFT, wx.WXK_F1, self.contextHelpID) )
		#accTable.append( (wx.ACCEL_CTRL, ord('F'), self.menuFindID) )
		aTable = wx.AcceleratorTable( accTable )
		self.SetAcceleratorTable(aTable)
		
		#------------------------------------------------------------------------------
		self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
		self.Bind(JChip.EVT_CHIP_READER, self.handleChipReaderEvent)
		self.Bind(JSONTimer.EVT_SPRINT_TIMER, self.handleSprintTimerEvent)
		self.lastPhotoTime = now()
		

	@property
	def chipReader( self ):
		return ChipReader.chipReaderCur
		
	def handleChipReaderEvent( self, event ):  #this triggers CrossMgrVideo
		race = Model.race
		if not race or not race.isRunning() or not race.enableUSBCamera:
			return
		if not getattr(race, 'photosOnRifid', True):
			return
		if not getattr(race, 'tagNums', None):
			GetTagNums()
		if not race.tagNums:
			return
		
		requests = []
		for tag, dt in event.tagTimes:
			if race.startTime > dt:
				continue
			
			try:
				num = race.tagNums[tag]
			except (KeyError, TypeError, ValueError):
				continue
			
			requests.append( (num, (dt - race.startTime).total_seconds()) )
		
		success, error = SendPhotoRequests( requests )
		if success:
			race.photoCount += len(requests) * 2
			
	def handleSprintTimerEvent( self, event ):  
		race = Model.race
		if not race:
			return
		
		self.sprintTimerClockDelta = event.readerComputerTimeDiff
		if event.havePPS is not None:
			havePPS = event.havePPS
		else:
			havePPS = None
		self.data.updateClockDelta( self.sprintTimerClockDelta, havePPS )
		
		if event.sprintDict is None or not race.isRunning():
			#we didn't get a sprint, just the clock status
			return
		
		#get the start time
		startTime = event.receivedTime
		if event.readerComputerTimeDiff.total_seconds() < 1.0 and "sprintStart" in event.sprintDict and "sprintStartMillis" in event.sprintDict:
			# We have millisecond precision from the timer; use that
			startTime = datetime.datetime.fromtimestamp(event.sprintDict["sprintStart"])
			startTime += datetime.timedelta(milliseconds = event.sprintDict["sprintStartMillis"])
		elif event.isT2 and "sprintTime" in event.sprintDict:
			# Subtract sprint time from receivedTime for a guess at T1 time
			startTime -= datetime.timedelta(seconds = event.sprintDict["sprintTime"])
		else:
			#otherwise, we just use the receivedTime
			pass
			
		#record that a sprint is in progress
		if not event.isT2:
			if "T1micros" in event.sprintDict:
				if "sprintStart" in event.sprintDict:
					t = datetime.datetime.fromtimestamp(event.sprintDict["sprintStart"])
					if "sprintStartMillis" in event.sprintDict:
						t += datetime.timedelta(milliseconds = event.sprintDict["sprintStartMillis"])
				else:
					Utils.writeLog('Did not get a start time from the sprint timer (RTC not set?), using current time.')
					t = now()
				race.setInProgressSprintStart( t )
				Utils.PlaySound('boop.wav')
			else:
				# no current sprint
				race.setInProgressSprintStart( None )
				return
		else:
			race.setInProgressSprintStart( None )
			Utils.PlaySound('peeeep.wav')
			
		# Below triggers CrossMgrVideo
		if not race.enableUSBCamera:
			return
		
		dt = event.receivedTime
		if (not event.isT2) and (not race.photosAtRaceEndOnly):  
			# we want the T1 photo time, calculated above
			dt = startTime
		elif event.isT2 and race.photosAtRaceEndOnly:
			# we want the T2 photo time
			if event.readerComputerTimeDiff.total_seconds() < 1.0 and "sprintFinish" in event.sprintDict and "sprintFinishMillis" in event.sprintDict:
				# We have millisecond precision from the timer; use that
				dt = datetime.datetime.fromtimestamp(event.sprintDict["sprintFinish"])
				dt += datetime.timedelta(milliseconds = event.sprintDict["sprintFinishMillis"])
			#otherwise, we just use the receivedTime
		else:
			# No photos needed for this event
			return
		
		num = 0  # default to 0 because CrossMgrVideo will choke on None
		if "sprintBib" in event.sprintDict:
			num = event.sprintDict["sprintBib"]
			Utils.writeLog('Using bib #' + str(num) + ' from sprintDict for photo trigger')
		elif getattr(race, 'useSequentialBibs', False):
			num = race.nextSequentialBib
			Utils.writeLog('Using sequential bib #' + str(num) + ' for photo trigger')
		elif race.getInProgressSprintBib() is not None:
			num = race.getInProgressSprintBib()
			Utils.writeLog('Using in-progress bib #' + str(num) + ' for photo trigger')
		else:
			Utils.writeLog('Do not have a bib # for photo trigger')
			
		requests = [(num, (dt - race.startTime).total_seconds())]
		success, error = SendPhotoRequests( requests )
		if success:
			race.photoCount += len(requests) * 2
		
	
	def updateLapCounter( self, labels=None ):
		#labels = labels or []
		#self.lapCounter.SetLabels( labels )
		#self.lapCounterDialog.page.SetLabels( labels )
		WebServer.WsLapCounterRefresh()
		
	def menuUndo( self, event ):
		undo.doUndo()
		self.refresh()
		
	def menuRedo( self, event ):
		undo.doRedo()
		self.refresh()
				
				
	@logCall
	def menuStartRace( self, event ):
		race = Model.race
		if not race:
			return
		if race.isRunning():
			Utils.MessageOK( self, _('Race is already running.'), _('Already running') )
			return
		else:
			if not Utils.MessageOKCancel(self, _('Start the race now?.'), _('Start race') ):
				return
			
			ChipReader.chipReaderCur.reset( Model.race.chipReaderType if Model.race else None )
			
			undo.clear()
			undo.pushState()
			with Model.LockRace() as race:
				if race is None:
					return
				Model.resetCache()
				race.startRaceNow()
				self.startRaceMenuItem.Enable(False)
				self.finishRaceMenuItem.Enable(True)
				self.resumeRaceMenuItem.Enable(False)
				
			#OutputStreamer.writeRaceStart()
			
			# Refresh the main window
			self.refresh()
			
			# For safety, clear the undo stack after 8 seconds.
			undoResetTimer = wx.CallLater( 8000, undo.clear )
			
			if race.ftpUploadDuringRace:
				realTimeFtpPublish.publishEntry( True )
			
	@logCall
	def menuFinishRace( self, event, confirm = True ):
		if Model.race is None:
			return
		if confirm and not Utils.MessageOKCancel(self, _('Finish Race Now?'), _('Finish Race')):
			return
			
		with Model.LockRace() as race:
			race.finishRaceNow()
			#if race.numLaps is None:
				#race.numLaps = race.getMaxLap()
			#SetNoDataDNS()
			Model.resetCache()
			self.startRaceMenuItem.Enable(False)
			self.finishRaceMenuItem.Enable(False)
			self.resumeRaceMenuItem.Enable(True)
		
		self.writeRace()
		self.refresh()
		
		#OutputStreamer.writeRaceFinish()
		#OutputStreamer.StopStreamer()
		try:
			ChipReader.chipReaderCur.StopListener()
		except Exception:
			pass

		if getattr(Model.race, 'ftpUploadDuringRace', False):
			realTimeFtpPublish.publishEntry( True )
				
	
	@logCall
	def menuRestartRace( self, event ):
		race = Model.race
		if not race:
			return
		if race.isUnstarted():
			Utils.MessageOK( self, _('Cannot restart an Unstarted Race.'), _('Race Not Restarted') )
			return
		if race.isRunning():
			Utils.MessageOK( self, _('Race is already running.'), _('Race Not Restarted') )
			return
		
		if not Utils.MessageOKCancel(
				self,
				'{}'.format(_('Restart the Race Now?'),
				),
					_('Restart race')
				):
				return
		with Model.LockRace() as race:
			race.resumeRaceNow()
			Model.resetCache()
			self.startRaceMenuItem.Enable(False)
			self.resumeRaceMenuItem.Enable(False)
			self.finishRaceMenuItem.Enable(True)
			
		
		self.writeRace()
		self.refresh()
		
		# For safety, clear the undo stack after 8 seconds.
		undoResetTimer = wx.CallLater( 8000, undo.clear )
		
		#self.actions.onFinishRace( event, False )
			#self.showPage( self.iHistoryPage )			
			
		#with Restart(self) as dlg:
			#dlg.refresh()
			#dlg.ShowModal()
		
	def menuPlaySounds( self, event ):
		self.playSounds = self.menuItemPlaySounds.IsChecked()
		self.config.WriteBool( 'playSounds', self.playSounds )
		
	def menuLaunchExcelAfterPublishingResults( self, event ):
		self.launchExcelAfterPublishingResults = self.menuItemLaunchExcelAfterPublishingResults.IsChecked()
		self.config.WriteBool( 'launchExcelAfterPublishingResults', self.launchExcelAfterPublishingResults )
			
	def menuShowPage( self, event ):
		self.showPage( self.idPage[event.GetId()] )
		
		
	#--------------------------------------------------------------------------------------------
	
	def menuSetContactEmail( self, event = None ):
		if Model.race and Model.race.email:
			email = Model.race.email
		else:
			email = self.config.Read( 'email', 'results_name@results_address' )
		with wx.TextEntryDialog( self, message=_('Results Contact Email'), caption=_('Results Contact Email'), value=email ) as dlg:
			if dlg.ShowModal() != wx.ID_OK:
				return
			value = dlg.GetValue()
			if Model.race:
				Model.race.email = value
				Model.race.setChanged()
	
	def menuSetGraphic( self, event ):
		imgPath = self.getGraphicFName()
		with SetGraphicDialog( self, graphic = imgPath ) as dlg:
			if dlg.ShowModal() != wx.ID_OK:
				return
			imgPath = dlg.GetValue()
			self.config.Write( 'graphic', imgPath )
			self.config.Flush()
			if Model.race:
				try:
					Model.race.headerImage = ImageIO.toBufFromFile( imgPath )
				except Exception as e:
					print(e)
	
	#def menuSetDefaultContactEmail( self, event = None ):
		#email = self.config.Read( 'email', 'my_name@my_address' )
		#with wx.TextEntryDialog( self, message=_('Default Contact Email:'), caption=_('Default Contact Email for HTML output - New Races'), value=email ) as dlg:
			#if dlg.ShowModal() != wx.ID_OK:
				#return
			#value = dlg.GetValue()
			#self.config.Write( 'email', value )
			#self.config.Flush()
			#if Model.race:
				#Model.race.email = email

	#def menuSetDefaultGraphic( self, event ):
		#imgPath = self.getGraphicFName()
		#with SetGraphicDialog( self, graphic = imgPath ) as dlg:
			#if dlg.ShowModal() != wx.ID_OK:
				#return
			#imgPath = dlg.GetValue()
			#self.config.Write( 'graphic', imgPath )
			#self.config.Flush()
			#if Model.race:
				#try:
					#Model.race.headerImage = ImageIO.toBufFromFile( imgPath )
				#except Exception as e:
					#pass
	
	#--------------------------------------------------------------------------------------------
	
	def menuCopyLogFileToClipboard( self, event ):
		try:
			with open(redirectFileName) as f:
				logData = f.read()
		except IOError:
			Utils.MessageOK(self, _("Unable to open log file."), _("Error"), wx.ICON_ERROR )
			return
			
		logData = logData.split( '\n' )
		logData = logData[-1000:]
		logData = '\n'.join( logData )
		
		dataObj = wx.TextDataObject()
		dataObj.SetText(logData)
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData( dataObj )
			wx.TheClipboard.Close()
			Utils.MessageOK(self, '\n\n'.join( [_("Log file copied to clipboard."), _("You can now paste it into an email.")] ), _("Success") )
		else:
			Utils.MessageOK(self, _("Unable to open the clipboard."), _("Error"), wx.ICON_ERROR )
	
	def getGraphicFName( self ):
		defaultFName = os.path.join(Utils.getImageFolder(), 'CrossMgrHeader.png')
		graphicFName = self.config.Read( 'graphic', defaultFName )
		if graphicFName != defaultFName:
			try:
				with open(graphicFName) as f:
					return graphicFName
			except IOError:
				pass
		return defaultFName
	
	def getGraphicBase64( self ):
		try:
			return Model.race.headerImage
		except Exception:
			pass
		
		graphicFName = self.getGraphicFName()
		if not graphicFName:
			return None
		fileType = os.path.splitext(graphicFName)[1].lower()
		if not fileType:
			return None
		fileType = fileType[1:]
		if fileType == 'jpg':
			fileType = 'jpeg'
		if fileType not in ['png', 'gif', 'jpeg']:
			return None
		try:
			b64 = ImageIO.toBufFromFile( graphicFName )
			if b64 and Model.race:
				Model.race.headerImage = b64
			return b64
		except IOError:
			pass
		return None

	def getFormatFilename( self, filecode ):
		#if filecode == 'uciexcel' and not BatchPublishAttrs.formatFilename[filecode]:
			#def getUCIFileNames( fnameBase ):
				#xlFNames = []
				#path, fname = os.path.split( fnameBase )
				#for catName, category in getRaceCategories():
					#if catName == 'All' or not category.publishFlag:
						#continue
					#safeCatName = re.sub('[+!#$%&+~`".:;|\\/?*\[\] ]+', ' ', Utils.toAscii(catName))		
					#xlFNames.append( os.path.join( path, 'UCI-StartList-{}-{}.xlsx'.format(fname, safeCatName) ) )
					#xlFNames.append( os.path.join( path, 'UCI-Results-{}-{}.xlsx'.format(fname, safeCatName) ) )
				#return xlFNames
			#BatchPublishAttrs.formatFilename[filecode] = getUCIFileNames
	
		return BatchPublishAttrs.formatFilename[filecode]( os.path.splitext(self.fileName or '')[0] )

	@logCall
	def menuLinkExcel( self, event = None ):
		if not Model.race:
			Utils.MessageOK(self, _("You must have a valid race."), _("Link ExcelSheet"), iconMask=wx.ICON_ERROR)
			return
		#self.showResultsPage()
		#self.closeFindDialog()
		ResetExcelLinkCache()
		gel = GetExcelLink( self, getattr(Model.race, 'excelLink', None) )
		link = gel.show()
		undo.pushState()
		with Model.LockRace() as race:
			if not link:
				try:
					del race.excelLink
				except AttributeError:
					pass
			else:
				if os.path.dirname(link.fileName) == os.path.dirname(self.fileName):
					link.fileName = os.path.join( '.', os.path.basename(link.fileName) )
				Utils.writeLog( 'Excel file "{}"'.format(link.fileName) )
				race.excelLink = link
			race.setChanged()
			race.resetAllCaches()
		self.writeRace()
		ResetExcelLinkCache()
		self.refresh()
		
		#wx.CallAfter( self.menuFind )
		try:
			if race.excelLink.initCategoriesFromExcel:
				wx.CallAfter( self.showPage, self.iCategoriesPage )
		except AttributeError:
			pass
	
	#--------------------------------------------------------------------------------------------

	@logCall
	def menuPublishAsExcel( self, event=None, silent=False ):
		self.commit()
		if self.fileName is None or len(self.fileName) < 4:
			return
		
		race = Model.race
		if not race:
			return
		
		
		#raceCategories = [ (c.fullname, c) for c in race.getCategories(startWaveOnly=False, publishOnly=True) if race.hasCategory(c) ]
		raceCategories = [ (c.fullname, c) for c in race.getCategories(startWaveOnly=False, publishOnly=True) ]

		xlFName = self.getFormatFilename('excel')

		wb = xlsxwriter.Workbook( xlFName )
		formats = ExportGrid.getExcelFormatsXLSX( wb )
		
		ues = Utils.UniqueExcelSheetName()
		
		for catName, category in raceCategories:
			if catName == 'All' and len(raceCategories) > 1:
				continue
			sheetCur = wb.add_worksheet( ues.getSheetName(catName) )
			export = ExportGrid()
			export.setResultsOneList( category )
			export.toExcelSheetXLSX( formats, sheetCur )
			

		AddExcelInfo( wb )
		if silent:
			try:
				wb.close()
			except Exception as e:
				logException( e, sys.exc_info() )
			return
			
		try:
			wb.close()
			if self.launchExcelAfterPublishingResults:
				Utils.LaunchApplication( xlFName )
			Utils.MessageOK(self, '{}:\n\n   {}'.format(_('Excel file written to'), xlFName), _('Excel Write'))
		except IOError as e:
			logException( e, sys.exc_info() )
			Utils.MessageOK(self,
						'{} "{}"\n\n{}\n{}'.format(
							_('Cannot write'), xlFName,
							_('Check if this spreadsheet is already open.'),
							_('If so, close it, and try again.')
						),
						_('Excel File Error'), iconMask=wx.ICON_ERROR )
	
	#--------------------------------------------------------------------------------------------
	def getEmail( self ):
		if Model.race and Model.race.email is not None:
			return Model.race.email
		return self.config.Read('email', '')
	
	reLeadingWhitespace = re.compile( r'^[ \t]+', re.MULTILINE )
	reComments = re.compile( r'// .*$', re.MULTILINE )
	reBlankLines = re.compile( r'\n+' )
	reTestCode = re.compile( '/\*\(-\*/.*?/\*-\)\*/', re.MULTILINE )	# Use non-greedy match.
	reRemoveTags = re.compile( r'\<html\>|\</html\>|\<body\>|\</body\>|\<head\>|\</head\>', re.I )
	reFloatList = re.compile( r'([+-]?[0-9]+\.[0-9]+,\s*)+([+-]?[0-9]+\.[0-9]+)', re.MULTILINE )
	reBoolList = re.compile( r'((true|false),\s*)+(true|false)', re.MULTILINE )
	def cleanHtml( self, html ):
		#Remove leading whitespace, comments, consecutive blank lines and test code to save space.
		html = self.reLeadingWhitespace.sub( '', html )
		html = self.reComments.sub( '', html )
		html = self.reBlankLines.sub( '\n', html )
		html = self.reTestCode.sub( '', html )
		return html
	
	def getBasePayload( self, publishOnly=True ):
		race = Model.race
		
		payload = {}
		payload['raceName'] = os.path.basename(self.fileName or '')[:-4]
		iMachine = ReportFields.index('Machine')
		payload['infoFields'] = ReportFields[:iMachine] + ['Name'] + ReportFields[iMachine:]
		
		payload['organizer']		= getattr(race, 'organizer', '')
		payload['reverseDirection']	= False
		payload['finishTop']		= False
		payload['isTimeTrial']		= True
		payload['isBestNLaps']		= False
		payload['winAndOut']		= False
		payload['rfid']				= race.enableJChipIntegration
		payload['primes']			= []
		payload['raceNameText']		= race.name
		payload['raceDate']			= race.date
		payload['raceScheduledStart']= race.date + ' ' + race.scheduledStart
		payload['raceTimeZone']		= race.timezone
		payload['raceAddress']      = ', '.join( n for n in [race.city, race.stateProv, race.country] if n )
		payload['raceIsRunning']	= race.isRunning()
		payload['raceIsUnstarted']	= race.isUnstarted()
		payload['raceIsFinished']	= race.isFinished()
		payload['rankFinishersBy']	= 'fastest first' if not getattr(race, 'rankReverseOrder', False) else 'slowest first'
		payload['lapDetails']		= race.getLapDetails()
		payload['hideDetails']		= False
		payload['showCourseAnimation'] = False #getattr(race, 'showCourseAnimationInHtml', False)
		payload['licenseLinkTemplate'] = ''
		payload['roadRaceFinishTimes'] = False
		payload['estimateLapsDownFinishTime'] = False
		payload['email']				= self.getEmail()
		payload['version']				= Version.AppVerName
		
		notes = race.notes
		if notes.lstrip()[:6].lower().startswith( '<html>' ):
			#notes = TemplateSubstitute( notes, race.getTemplateValues() )
			notes = self.reRemoveTags.sub( '', notes )
			notes = notes.replace('<', '{-{').replace( '>', '}-}' )
			payload['raceNotes']	= notes
		else:
			#notes = TemplateSubstitute( escape(notes), race.getTemplateValues() )
			notes = self.reTagTrainingSpaces.sub( '>', notes ).replace( '</table>', '</table><br/>' )
			notes = notes.replace('<', '{-{').replace( '>', '}-}' ).replace('\n','{-{br/}-}')
			payload['raceNotes']	= notes
		if race.startTime:
			raceStartTime = (race.startTime - race.startTime.replace( hour=0, minute=0, second=0 )).total_seconds()
			payload['raceStartTime']= raceStartTime
		
		tLastRaceTime = race.lastRaceTime()
		tNow = now()
		payload['timestamp']			= [tNow.ctime(), tLastRaceTime]
		
		payload['data']					= race.getAnimationData( None, True )
		payload['catDetails']			= race.getCategoryDetails( True, publishOnly )
		
		#print('\n\npayload: ' + str(payload))
		
		return payload
	
	reTagTrainingSpaces = re.compile( '>\s+', re.MULTILINE|re.UNICODE )
	def addResultsToHtmlStr( self, html ):
		html = self.cleanHtml( html )
		
		payload = self.getBasePayload()		
		race = Model.race
		
		year, month, day = [int(v) for v in race.date.split('-')]
		timeComponents = [int(v) for v in race.scheduledStart.split(':')]
		if len(timeComponents) < 3:
			timeComponents.append( 0 )
		hour, minute, second = timeComponents
		raceTime = datetime.datetime( year, month, day, hour, minute, second )
		
		#------------------------------------------------------------------------
		title = '{} - {} {} {}'.format( race.title, _('Starting'), raceTime.strftime(localTimeFormat), raceTime.strftime(localDateFormat) )
		html = html.replace( 'SprintTimer Race Results by BHPC', escape(title) )
		if getattr(race, 'gaTrackingID', None):
			html = html.replace( '<!-- Google Analytics -->', gaSnippet.replace('UA-XXXX-Y', race.gaTrackingID) )
		if race.isRunning():
			html = html.replace( '<!-- Meta -->', '''
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"/>
<meta http-equiv="Pragma" content="no-cache"/>
<meta http-equiv="Expires" content="0"/>''' )
		
		#------------------------------------------------------------------------
		courseCoordinates, gpsPoints, gpsAltigraph, totalElevationGain, isPointToPoint, lengthKm = None, None, None, None, None, None
		geoTrack = getattr(race, 'geoTrack', None)
		if geoTrack is not None:
			courseCoordinates = geoTrack.asCoordinates()
			gpsPoints = geoTrack.asExportJson()
			gpsAltigraph = geoTrack.getAltigraph()
			totalElevationGain = geoTrack.totalElevationGainM
			isPointToPoint = getattr( geoTrack, 'isPointToPoint', False )
			lengthKm = geoTrack.lengthKm
		
		#------------------------------------------------------------------------
		codes = []
		if 'UCICode' in payload['infoFields']:
			codes.extend( r['UCICode'] for r in payload['data'].values() if r.get('UCICode',None) )
		if 'NatCode' in payload['infoFields']:
			codes.extend( r['NatCode'] for r in payload['data'].values() if r.get('NatCode',None) )
		payload['flags']				= Flags.GetFlagBase64ForUCI( codes )
		if gpsPoints:
			payload['gpsPoints']		= gpsPoints
		
		def sanitize( template ):
			#Sanitize the template into a safe json string.
			template = template.replace( '{{api_key}}', race.googleMapsApiKey )
			template = self.reLeadingWhitespace.sub( '', template )
			template = self.reComments.sub( '', template )
			template = self.reBlankLines.sub( '\n', template )
			template = template.replace( '<', '{-{' ).replace( '>', '}-}' )
			return template
		
		#If a map is defined, add the course viewers.
		if courseCoordinates:
			payload['courseCoordinates'] = courseCoordinates
			
			if race.googleMapsApiKey:
				#Add the course viewer template.
				templateFile = os.path.join(Utils.getHtmlFolder(), 'CourseViewerTemplate.html')
				try:
					with open(templateFile) as fp:
						template = fp.read()
					payload['courseViewerTemplate'] = sanitize( template )
				except Exception:
					pass
	
		#Add the rider dashboard.
		templateFile = os.path.join(Utils.getHtmlFolder(), 'RiderDashboard.html')
		#try:
		with open(templateFile) as fp:
			template = fp.read()
		payload['riderDashboard'] = sanitize( template )
		#except Exception:
		#	pass
	
		#Add the travel map if the riders have locations.
		#if race.googleMapsApiKey:
			#try:
				#excelLink = race.excelLink
				#if excelLink.hasField('City') and any(excelLink.hasField(f) for f in ('Prov','State','StateProv')):
					#templateFile = os.path.join(Utils.getHtmlFolder(), 'TravelMap.html')
					#try:
						#with open(templateFile) as fp:
							#template = fp.read()
						#payload['travelMap'] = sanitize( template )
					#except Exception:
						#pass
			#except Exception as e:
				#pass
		
		if totalElevationGain:
			payload['gpsTotalElevationGain'] = totalElevationGain
		if gpsAltigraph:
			payload['gpsAltigraph'] = gpsAltigraph
		if isPointToPoint:
			payload['gpsIsPointToPoint'] = isPointToPoint
		if lengthKm:
			payload['lengthKm'] = lengthKm

		html = replaceJsonVar( html, 'payload', payload )
		graphicBase64 = self.getGraphicBase64()
		if graphicBase64:
			try:
				iStart = html.index( 'src="data:image/png' )
				iEnd = html.index( '"/>', iStart )
				html = ''.join( [html[:iStart], 'src="{}"'.format(graphicBase64), html[iEnd+1:]] )
			except ValueError:
				pass
				
		#Clean up spurious decimal points.
		def fixBigFloat( f ):
			if len(f) > 6:
				try:
					d = f.split('.')[1]					# Get decimal part of the number.
					max_precision = 5
					if len(d) > max_precision:
						f = '{val:.{pr}f}'.format(pr=max_precision, val=float(f)).rstrip('0')	# Reformat with a shorter decimal and remove trailing zeros.
						if f.endswith('.'):
							f += '0'		# Ensure a zero follows the decimal point (json format spec).
				except IndexError:
					#Number does not have a decimal point.
					pass
			return f
			
		def floatListRepl( m ):
			return ','.join([fixBigFloat(f) for f in m.group().replace(',',' ').split()])
			
		html = self.reFloatList.sub( floatListRepl, html )
		
		#Convert true/false lists to 0/1.
		def boolListRepl( m ):
			return ','.join(['0' if f[:1] == 'f' else '1' for f in m.group().replace(',',' ').split() ])
			
		html = self.reBoolList.sub( boolListRepl, html )
		
		return html
	
	@logCall
	def menuPublishBatch( self, event ):
		self.commit()
		race = Model.race
		if self.fileName is None or len(self.fileName) < 4:
			Utils.MessageOK(self, '{}\n\n{}.'.format(_('No Race'), _('New/Open a Race and try again.')),
				_('No Race'), iconMask=wx.ICON_ERROR )
			return
		if race and not race.email:
			if Utils.MessageOKCancel( self,
				_('Your Email contact is not set.\n\nConfigure it now?'),
				_('Set Email Contact'), wx.ICON_EXCLAMATION ):
				self.menuSetContactEmail()
			
		with BatchPublishPropertiesDialog( self ) as dialog:
			ret = dialog.ShowModal()
		
	@logCall
	def menuPublishHtmlRaceResults( self, event=None, silent=False ):
		self.commit()
		if self.fileName is None or len(self.fileName) < 4:
			return
			
		if not silent and not self.getEmail():
			if Utils.MessageOKCancel( self,
				_('Your Email contact is not set.\n\nConfigure it now?'),
				_('Set Email Contact'), wx.ICON_EXCLAMATION ):
				self.menuSetContactEmail()
	
		#Read the html template.
		htmlFile = os.path.join(Utils.getHtmlFolder(), 'RaceAnimation.html')
		try:
			with open(htmlFile) as fp:
				html = fp.read()
		except Exception as e:
			logException( e, sys.exc_info() )
			if not silent:
				Utils.MessageOK(self, _('Cannot read HTML template file.  Check program installation.'),
								_('Html Template Read Error'), iconMask=wx.ICON_ERROR )
			return
			
		html = self.addResultsToHtmlStr( html )
			
		#Write out the results.
		fname = self.getFormatFilename('html')
		try:
			with open(fname, 'w') as fp:
				fp.write( html )
			if not silent:
				Utils.LaunchApplication( fname )
				Utils.MessageOK(self, '{}:\n\n   {}'.format(_('Html Race Animation written to'), fname), _('Html Write'))
		except Exception as e:
			logException( e, sys.exc_info() )
			if not silent:
				Utils.MessageOK(self, '{}\n\t\t{}\n({}).'.format(_('Cannot write HTML file'), e, fname),
								_('Html Write Error'), iconMask=wx.ICON_ERROR )
	
	@logCall
	def menuPublishHtmlIndex( self, event=None, silent=False ):
		self.commit()
		if self.fileName is None or len(self.fileName) < 4:
			return
		try:
			WebServer.WriteHtmlIndexPage()
		except Exception as e:
			logException( e, sys.exc_info() )
			if not silent:
				Utils.MessageOK(self, '{}\n\n{}.'.format(_('HTML Index Failure'), e),
								_('Error'), iconMask=wx.ICON_ERROR )
			
	@logCall
	def menuAddManualSprint( self, event ):
		race = Model.race
		if race is None:
			return
		
		with ManualEntryDialog(self) as dlg:
			dlg.ShowModal()
		self.refresh()
		
		
		
	#--------------------------------------------------------------------------------------------
	def doCleanup( self ):
		#self.showResultsPage()
		race = Model.race
		if race:
			try:
				race.resetAllCaches()
				self.writeRace()
				#Model.writeModelUpdate()
				self.config.Flush()
			except Exception as e:
				Utils.writeLog( 'call: doCleanup: (1) "{}"'.format(e) )

		try:
			self.timer.Stop()
		except AttributeError:
			pass
		except Exception as e:
			Utils.writeLog( 'call: doCleanup: (2) "{}"'.format(e) )

	
	@logCall
	def onCloseWindow( self, event ):
		self.doCleanup()
		wx.Exit()

	def writeRace( self, doCommit = True ):
		if doCommit:
			self.commit()
		with Model.LockRace() as race:
			if race is not None:
				with open(self.fileName, 'wb') as fp:
					Utils.writeLog( 'Dumping race to: ' + str(self.fileName))
					pickle.dump( race, fp, 2 )
				race.setChanged( False )

	#def setActiveCategories( self ):
		#with Model.LockRace() as race:
			#if race is None:
				#return
			#race.setActiveCategories()

	@logCall
	def menuNew( self, event ):
		#self.showPage(self.iActionsPage)
		#self.closeFindDialog()
		self.writeRace()
		
		race = Model.race
		if race:
			#geoTrack, geoTrackFName = getattr(race, 'geoTrack', None), getattr(race, 'geoTrackFName', None)
			excelLink = getattr(race, 'excelLink', None)
		else:
			excelLink = None
			
			
		#geoTrack, geoTrackFName = None, None		# Do not retain the GPX file after a full new.
		
		raceSave = Model.race
		
		Model.setRace( Model.Race() )
		race = Model.race
		
		#print(race)
		
		#if geoTrack:
			#race.geoTrack, race.geoTrackFName = geoTrack, geoTrackFName
			#distance = geoTrack.length if race.distanceUnit == race.UnitKm else geoTrack.length * 0.621371
			#if distance > 0.0:
				#for c in race.categories.values():
					#c.distance = distance
			#race.showOval = False
		if excelLink:
			race.excelLink = excelLink
			
		dlg = PropertiesDialog(self, title=_('Configure Race'), style=wx.DEFAULT_DIALOG_STYLE )
		#ApplyDefaultTemplate( race )
		dlg.properties.refresh()
		ret = dlg.ShowModal()
		fileName = dlg.GetPath()
		#categoriesFile = dlg.GetCategoriesFile()
		properties = dlg.properties	

		if ret != wx.ID_OK:
			Model.race = raceSave
			return
			
		#Check for existing file.
		if os.path.exists(fileName) and \
		   not Utils.MessageOKCancel(
				self,
				'{}.\n\n    "{}"\n\n{}?'.format(
					_('File already exists'), fileName, _('Overwrite')
				)
			):
			Model.race = raceSave
			return

		#Try to open the file.
		try:
			with open(fileName, 'w') as fp:
				pass
		except IOError:
			Utils.MessageOK( self, '{}\n\n    "{}"'.format(_('Cannot Open File'),fileName), _('Cannot Open File'), iconMask=wx.ICON_ERROR )
			Model.race = raceSave
			return

		race.resetAllCaches()
		
		#Create a new race and initialize it with the properties.
		self.fileName = fileName
		WebServer.SetFileName( self.fileName )
		Model.resetCache()
		ResetExcelLinkCache()
		properties.commit()
		
		self.updateRecentFiles()
		
		os.chdir(os.path.dirname(os.path.abspath(self.fileName)))
		Utils.writeLog( 'CWD is: {}'.format(os.getcwd()) )

		#importedCategories = False
		#if categoriesFile:
			#try:
				#with open(categoriesFile) as fp:
					#race.importCategories( fp )
				#importedCategories = True
			#except IOError:
				#Utils.MessageOK( self, "{}:\n{}".format(_('Cannot open file'), categoriesFile), _("File Open Error"), iconMask=wx.ICON_ERROR)
			#except (ValueError, IndexError):
				#Utils.MessageOK( self, "{}:\n{}".format(_('Bad file format'), categoriesFile), _("File Read Error"), iconMask=wx.ICON_ERROR)

		#Create some defaults so the page is not blank.
		#if not importedCategories:
			#race.categoriesImportFile = ''
			#race.setCategories( [{'name':'{} {}-{}'.format(_('Category'), max(1, i*100), (i+1)*100-1),
								  #'catStr':'{}-{}'.format(max(1, i*100), (i+1)*100-1)} for i in range(8)] )
		#else:
			#race.categoriesImportFile = categoriesFile
		self.startRaceMenuItem.Enable(True)
		self.finishRaceMenuItem.Enable(False)
		self.resumeRaceMenuItem.Enable(False)
		self.setNumSelect( None )
		self.writeRace()
		self.showPage(self.iDataPage)
		self.refreshAll()
	
	@logCall
	def menuNewNext( self, event ):
		race = Model.race
		if race is None:
			self.menuNew( event )
			return

		#self.closeFindDialog()
		#self.showPage(self.iActionsPage)
		race.resetAllCaches()
		ResetExcelLinkCache()
		self.writeRace()
		
		#Save categories, gpx track and Excel link and use them in the next race.
		categoriesSave = race.categories
		#geoTrack, geoTrackFName = getattr(race, 'geoTrack', None), getattr(race, 'geoTrackFName', None)
		excelLink = getattr(race, 'excelLink', None)
		race = None
		
		#Configure the next race.
		with PropertiesDialog(self, title=_('Configure Race'), style=wx.DEFAULT_DIALOG_STYLE ) as dlg:
			dlg.properties.refresh()
			dlg.properties.incNext()
			#dlg.properties.setEditable( True )
			dlg.folder.SetValue(os.path.dirname(self.fileName))
			dlg.properties.updateFileName()
			if dlg.ShowModal() != wx.ID_OK:
				return
			
			fileName = dlg.GetPath()
			#categoriesFile = dlg.GetCategoriesFile()

			#Check for existing file.
			if os.path.exists(fileName) and \
			   not Utils.MessageOKCancel(self, '{}\n\n    {}'.format(_('File already exists.  Overwrite?'), fileName), _('File Exists')):
				return

			#Try to open the file.
			try:
				with open(fileName, 'w') as fp:
					pass
			except IOError:
				Utils.MessageOK(self, '{}\n\n    "{}".'.format(_('Cannot open file.'), fileName), _('Cannot Open File'), iconMask=wx.ICON_ERROR )
				return
			except Exception as e:
				Utils.MessageOK(self, '{}\n\n    "{}".\n\n{}: {}'.format(_('Cannot open file.'), fileName, _('Error'), e), _('Cannot Open File'), iconMask=wx.ICON_ERROR )
				return

			#Create a new race and initialize it with the properties.
			self.fileName = fileName
			WebServer.SetFileName( self.fileName )
			Model.resetCache()
			ResetExcelLinkCache()
			
			os.chdir(os.path.dirname(os.path.abspath(self.fileName)))
			Utils.writeLog( 'CWD is: {}'.format(os.getcwd()) )
			
			#Save the current Ftp settings.
			ftpPublish = FtpWriteFile.FtpPublishDialog( self )

			Model.newRace()
			dlg.properties.commit()		# Apply the new properties from the dlg.
			ftpPublish.commit()			# Apply the ftp properties
			ftpPublish.Destroy()

		#Done with properties.  On with initializing the rest of the race.
		self.updateRecentFiles()

		#Restore the previous categories.
		race = Model.race
		#importedCategories = False
		#if categoriesFile:
			#try:
				#with open(categoriesFile) as fp:
					#race.importCategories( fp )
				#importedCategories = True
			#except IOError:
				#Utils.MessageOK( self, '{}:\n\n    {}'.format(_('Cannot open file'), categoriesFile), _("File Open Error"), iconMask=wx.ICON_ERROR)
			#except (ValueError, IndexError) as e:
				#Utils.MessageOK( self, '{}:\n\n    {}\n\n{}'.format(_('Bad file format'), categoriesFile, e), _("File Read Error"), iconMask=wx.ICON_ERROR)

		#if not importedCategories:
		race.categories = categoriesSave

		#if geoTrack:
			#race.geoTrack, race.geoTrackFName = geoTrack, geoTrackFName
			#distance = geoTrack.lengthKm if race.distanceUnit == race.UnitKm else geoTrack.lengthMiles
			#if distance > 0.0:
				#for c in race.categories.values():
					#c.distance = distance
			#race.showOval = False
		if excelLink:
			race.excelLink = excelLink
		
		self.startRaceMenuItem.Enable(True)
		self.finishRaceMenuItem.Enable(False)
		self.resumeRaceMenuItem.Enable(False)
		#self.setActiveCategories()
		self.setNumSelect( None )
		self.writeRace()
		self.showPage(self.iDataPage)
		self.refreshAll()

	def updateRecentFiles( self ):
		self.filehistory.AddFileToHistory(self.fileName)
		self.filehistory.Save(self.config)
		self.config.Flush()
		
	#def closeFindDialog( self ):
		#if getattr(self, 'findDialog', None):
			#self.findDialog.Show( False )

	def openRace( self, fileName ):
		if not fileName:
			Utils.writeLog('No filename; not opening race')
			return
		#self.showResultsPage()
		self.refresh()
		Model.resetCache()
		ResetExcelLinkCache()
		self.writeRace()
		#Model.writeModelUpdate()
		#self.closeFindDialog()
		
		#fileNameSave = self.fileName
		
		try:
			with open(fileName, 'rb') as fp, Model.LockRace() as race:
				try:
					race = pickle.load( fp, encoding='latin1', errors='replace' )
				except Exception:
					fp.seek( 0 )
					race = ModuleUnpickler( fp, module='SprintTimer', encoding='latin1', errors='replace' ).load()
				race.resetAllCaches()
				race.lastOpened = now()
				Model.setRace( race )
				#print(race)
			
			ChipReader.chipReaderCur.reset( race.chipReaderType )
			self.fileName = fileName
			Utils.writeLog('Opened race: ' + str(self.fileName))
			
			os.chdir(os.path.dirname(os.path.abspath(self.fileName)))
			Utils.writeLog( 'CWD is: {}'.format(os.getcwd()) )
			
			undo.clear()
			ResetExcelLinkCache()
			Model.resetCache()
			
			if race.isUnstarted():
				self.startRaceMenuItem.Enable(True)
				self.finishRaceMenuItem.Enable(False)
				self.resumeRaceMenuItem.Enable(False)
			elif race.isRunning():
				self.startRaceMenuItem.Enable(False)
				self.finishRaceMenuItem.Enable(True)
				self.resumeRaceMenuItem.Enable(False)
			elif race.isFinished():
				self.startRaceMenuItem.Enable(False)
				self.finishRaceMenuItem.Enable(False)
				self.resumeRaceMenuItem.Enable(True)
			else:
				self.startRaceMenuItem.Enable(True)
				self.finishRaceMenuItem.Enable(True)
				self.resumeRaceMenuItem.Enable(True)
			self.setNumSelect( None )
			self.showPage( self.iResultsPage if race.isFinished() else self.iDataPage )
			self.updateLapCounter()
			self.refreshAll()
			Utils.writeLog( '{}: {} {}'.format(Version.AppVerName, platform.system(), platform.release()) )
			Utils.writeLog( 'call: openRace: "{}"'.format(fileName) )
			
			self.updateRecentFiles()
			WebServer.SetFileName( self.fileName )

			excelLink = getattr(race, 'excelLink', None)
			if excelLink is None or not excelLink.fileName:
				return
				
			if os.path.isfile(excelLink.fileName):
				Utils.writeLog( 'openRace: Excel file "{}"'.format(excelLink.fileName) )
				return
				
			#Check if we have a missing spreadsheet but can find one in the same folder as the race.
			Utils.writeLog( 'openRace: cannot open Excel file "{}"'.format(excelLink.fileName) )
			newFileName = GetMatchingExcelFile(fileName, excelLink.fileName)
			if newFileName and Utils.MessageOKCancel(self,
				'{}:\n\n"{}"\n\n{}:\n\n"{}"\n\n{}'.format(
					_('Could not find Excel file'), excelLink.fileName,
					_('Found this Excel file in the race folder with matching name'), newFileName, _('Use this Excel file from now on?')
				),
				_('Excel Link Not Found') ):
				race.excelLink.fileName = newFileName
				race.setChanged()
				ResetExcelLinkCache()
				Model.resetCache()
				self.refreshAll()
				Utils.writeLog( 'openRace: changed Excel file to "{}"'.format(newFileName) )
				
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			Utils.MessageOK(self, '{} "{}"\n\n{}.'.format(_('Cannot Open File'), fileName, e), _('Cannot Open File'), iconMask=wx.ICON_ERROR )

	#@logCall
	def menuOpen( self, event ):
		dlg = wx.FileDialog( self, message=_("Choose a Race file"),
							defaultFile = '',
							defaultDir = Utils.getFileDir(),
							wildcard = _('SprintTimer files (*.spr)|*.spr'),
							style=wx.FD_OPEN | wx.FD_CHANGE_DIR )
		if dlg.ShowModal() == wx.ID_OK:
			busy = wx.BusyCursor()
			self.openRace( dlg.GetPath() )

	def menuFileHistory( self, event ):
		fileNum = event.GetId() - wx.ID_FILE1
		fileName = self.filehistory.GetHistoryFile(fileNum)
		self.filehistory.AddFileToHistory(fileName)  # move up the list
		self.openRace( fileName )

	#@logCall
	#def menuCloseRace(self, event ):
		#race = Model.race

		#if race is None or not self.fileName:
			#return

		#if race is not None and race.isRunning():
			#if not Utils.MessageOKCancel(self,	_('The current race is still running.\nFinish it and continue?'),
												#_('Current race running') ):
				#return
			#race.finishRaceNow()
		
		#Model.writeModelUpdate()
		#self.doCleanup()
		#Model.setRace( None )
		#self.refresh()
	
	@logCall
	def menuExit(self, event):
		self.onCloseWindow( event )

	#@logCall
	#def menuHelpQuickStart( self, event ):
		#try:
			#webbrowser.open( getHelpURL('QuickStart.html') )
		#except Exception as e:
			#logException( e, sys.exc_info() )
	
	#@logCall
	#def menuHelpWhatsNew( self, event ):
		#try:
			#webbrowser.open( getHelpURL('WhatsNew.html') )
		#except Exception as e:
			#logException( e, sys.exc_info() )
	
	@logCall
	def menuHelpSearch( self, event ):
		self.helpSearch.Show()
	
	@logCall
	def menuHelp( self, event ):
		try:
			webbrowser.open( getHelpURL('Main.html') )
		except Exception as e:
			logException( e, sys.exc_info() )
	
	#@logCall
	#def onContextHelp( self, event ):
		#try:
			#webbrowser.open( getHelpURL(self.attrClassName[self.notebook.GetSelection()][2] + '.html') )
		#except Exception as e:
			#logException( e, sys.exc_info() )
		
	@logCall
	def menuWebIndexPage( self, event ):
		if not Model.race:
			return
		try:
			Utils.writeLog('Opening {} in browser'.format(WebServer.GetCrossMgrHomePage()) )
			webbrowser.open( WebServer.GetCrossMgrHomePage(), new = 2, autoraise = True )
		except Exception as e:
			logException( e, sys.exc_info() )
	
	@logCall
	def menuWebQRCodePage( self, event ):
		if not Model.race:
			return
		try:
			webbrowser.open( WebServer.GetCrossMgrHomePage() + '/qrcode.html' , new = 2, autoraise = True )
		except Exception as e:
			logException( e, sys.exc_info() )
	
	@logCall
	def menuAbout( self, event ):
		#First we create and fill the info object
		info = wx.adv.AboutDialogInfo()
		info.Name = Version.AppVerName
		info.Version = ''
		info.Copyright = "(C) 2023-{}".format( now().year )
		info.Description = wordwrap(
_("""Score Cycling sprints with a high degree of automation.

Written for use by the British Human Power Club.

"""),
			500, wx.ClientDC(self))
		info.WebSite = ("https://github.com/kimble4/CrossMgr", "CrossMgr GitHub")
		info.Developers = ["Kim Wall (technical@bhpc.org.uk)",
					"Edward Sitarski (edward.sitarski@gmail.com)",
					"Mark Buckaway (mark@buckaway.ca)",
					"Andrew Paradowski (andrew.paradowski@gmail.com)",
					]

		licenseText = \
_("""User Beware!

This program is experimental, under development and may have bugs.
Feedback is sincerely appreciated.
Donations are also appreciated - see website for details.

CRITICALLY IMPORTANT MESSAGE!
This program is not warranted for any use whatsoever.
It may not produce correct results, it might lose your data.
The authors of this program assume no responsibility or liability for data loss or erroneous results produced by this program.

Use entirely at your own risk.
Do not come back and tell me that this program screwed up your event!
Computers fail, screw-ups happen.  Always use a manual backup.
""")
		info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

		wx.adv.AboutBox(info)

	#--------------------------------------------------------------------------------------

	def getCurrentPage( self ):
		return self.pages[self.notebook.GetSelection()]
		
	def isShowingPage( self, page ):
		return page == self.pages[self.notebook.GetSelection()]
	
	def showPage( self, iPage ):
		self.callPageCommit( self.notebook.GetSelection() )
		self.callPageRefresh( iPage )
		self.notebook.SetSelection( iPage )
		self.pages[self.notebook.GetSelection()].Layout()
		
	#def showPageName( self, name ):
		#name = name.replace(' ', '')
		#for i, (a, c, n) in enumerate(self.attrClassName):
			#if n == name:
				#self.showPage( i )
				#break

	#def showRiderDetail( self, num = None ):
		#self.riderDetail.setRider( num )
		#self.showPage( self.iRiderDetaiPage )

	#def setRiderDetail( self, num = None ):
		#self.riderDetail.setRider( num )

	#def showResultsPage( self ):
		#self.showPage( self.iResultsPage )

	def callPageRefresh( self, i ):
		try:
			page = self.pages[i]
		except IndexError:
			return
		try:
			page.refresh()
		except AttributeError:
			pass

	def refreshWindows( self ):
		try:
			for d in (dialog for attr, name, menuItem, dialog in self.menuIdToWindowInfo.values() if dialog.IsShown()):
				try:
					wx.CallAfter( d.refresh )
				except AttributeError:
					pass
			if self.missingRiders.IsShown():
				try:
					wx.CallAfter( self.missingRiders.refresh )
				except AttributeError:
					pass
		except AttributeError:
			pass

	def callPageCommit( self, i ):
		try:
			self.pages[i].commit()
		except (AttributeError, IndexError):
			pass
		self.refreshWindows()

	def commit( self ):
		self.callPageCommit( self.notebook.GetSelection() )
				
	def refreshCurrentPage( self ):
		self.callPageRefresh( self.notebook.GetSelection() )
		self.refreshWindows()
		WebServer.WsRefresh()

	def refresh( self ):
		self.refreshCurrentPage()
		#self.forecastHistory.refresh()
		#if self.riderDetailDialog:
			#self.riderDetailDialog.refresh()
		#race = Model.race
		#self.menuItemHighPrecisionTimes.Check( bool(race and race.highPrecisionTimes) )
		#self.menuItemSyncCategories.Check( bool(race and race.syncCategories) )
		
		self.updateRaceClock()

	#def refreshTTStart( self ):
		#if self.notebook.GetSelection() in (self.iHistoryPage, self.iRecordPage):
			#self.refreshCurrentPage()

	def updateUndoStatus( self, event = None ):
		race = Model.race
		self.undoMenuButton.Enable( bool(not race.isRunning() and undo.isUndo()) )
		self.redoMenuButton.Enable( bool(not race.isRunning() and undo.isRedo()) )
		
	def onPageChanging( self, event ):
		notebook = event.GetEventObject()
		if notebook == self.notebook:
			self.callPageCommit( event.GetOldSelection() )
			self.callPageRefresh( event.GetSelection() )
		try:
			Utils.writeLog( 'page: {}\n'.format(notebook.GetPage(event.GetSelection()).__class__.__name__) )
		except IndexError:
			pass
		event.Skip()	# Required to properly repaint the screen.

	#def refreshRaceAnimation( self ):
		#if self.pages[self.notebook.GetSelection()] == self.raceAnimation:
			#self.raceAnimation.refresh()
			
	def refreshResults( self ):
		self.callPageRefresh( self.iResultsPage )
		#if Model.race.ftpUploadDuringRace:
			#wx.CallAfter( realTimeFtpPublish.publishEntry )
	
	def refreshAll( self ):
		self.refresh()
		iSelect = self.notebook.GetSelection()
		for i, p in enumerate(self.pages):
			if i != iSelect:
				self.callPageRefresh( i )

	def setNumSelect( self, num ):
		try:
			num = int(num)
		except (TypeError, ValueError):
			num = None
			
		if num is None or num != self.numSelect:
			#self.history.setNumSelect( num )
			#self.results.setNumSelect( num )
			#self.riderDetail.setNumSelect( num )
			#self.gantt.setNumSelect( num )
			#self.raceAnimation.setNumSelect( num )
			self.numSelect = num

	#-------------------------------------------------------------
	
	def processNumTimes( self ):
		if not self.numTimes:
			return False
		
		race = Model.race
		
		for num, t in self.numTimes:
			Utils.writeLog('RFID got bib:' + str(num))
			# add them to the sprintbibs list, don't process as lap times
			race.addSprintBib( num, t, doSetChanged = False )
			#race.addTime( num, t, doSetChanged=False )
		race.setChanged()
		
		#OutputStreamer.writeNumTimes( self.numTimes )
		
		#if race.enableUSBCamera:
			#photoRequests = [(num, t) for num, t in self.numTimes if okTakePhoto(num, t)]
			#if photoRequests:
				#success, error = SendPhotoRequests( photoRequests )
				#if success:
					#race.photoCount += len(photoRequests)
				#else:
					#Utils.writeLog( 'USB Camera Error: {}'.format(error) )
		
		del self.numTimes[:]
		return True
	
	def processRfidRefresh( self ):
		if self.processNumTimes():
			self.refresh()
			self.updateLapCounter()
			#if Model.race and Model.race.ftpUploadDuringRace:
				#realTimeFtpPublish.publishEntry()
	
	def processJChipListener( self, refreshNow=False ):
		race = Model.race
		if not race:
			return False
			
		if not race or not race.enableJChipIntegration:
			if ChipReader.chipReaderCur.IsListening():
				ChipReader.chipReaderCur.StopListener()
			return False
		
		if not ChipReader.chipReaderCur.IsListening():
			ChipReader.chipReaderCur.reset( race.chipReaderType )
			ChipReader.chipReaderCur.StartListener( race.startTime )
			GetTagNums( True )
	
		data = ChipReader.chipReaderCur.GetData()
		
		if not getattr(race, 'tagNums', None):
			GetTagNums()
		if not race.tagNums:
			return False
		
		for d in data:
			if d[0] != 'data':
				continue
			tag, dt = d[1], d[2]
			
			#Ignore unrecorded reads that happened before the restart time.
			#if race.rfidRestartTime and dt <= race.rfidRestartTime:
				#continue
			
			try:
				num = race.tagNums[tag]
			except KeyError:
				if race.isRunning() and race.startTime <= dt:
					print('got unmatched tag:' + str(tag))
					race.addUnmatchedTag( tag, (dt - race.startTime).total_seconds() )
				continue
			except (TypeError, ValueError):
				race.missingTags.add( tag )
				continue
				
			#Only process times after the start of the race.
			if race.isRunning() and race.startTime <= dt:
		
				#Always process times for mass start races and when timeTrialNoRFIDStart unset.
				#if not race.isTimeTrial or not race.timeTrialNoRFIDStart:
					#self.numTimes.append( (num, (dt - race.startTime).total_seconds()) )
				#else:
					#Only process the time if the rider has already started
					#rider = race.getRider( num )
					#if rider.firstTime is not None:
						#self.numTimes.append( (num, (dt - race.startTime).total_seconds()) )
					self.numTimes.append( (num, dt) )
		
		#Ensure that we don't update too often if riders arrive in a bunch.
		if not self.callLaterProcessRfidRefresh:
			class ProcessRfidRefresh( wx.Timer ):
				def __init__( self, *args, **kwargs ):
					self.mainWin = kwargs.pop('mainWin')
					super().__init__(*args, **kwargs)
				def Notify( self ):
					self.mainWin.processRfidRefresh()
			self.callLaterProcessRfidRefresh = ProcessRfidRefresh( mainWin=self )
		
		delayIntervals = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
		delayIntervals = (0.1, 0.25, 0.5, 0.75, 1.0)
		if not self.callLaterProcessRfidRefresh.IsRunning():
			#Start the timer for the first interval.
			self.clprIndex = 0
			self.clprTime = now() + datetime.timedelta( seconds=delayIntervals[0] )
			if refreshNow or not self.callLaterProcessRfidRefresh.Start( int(delayIntervals[0]*1000.0), True ):
				self.processRfidRefresh()
		elif (		(self.clprTime - now()).total_seconds() > delayIntervals[self.clprIndex] * 0.75 and
					self.clprIndex < len(delayIntervals)-1 ):
			#If we get another read within the last 25% of the interval, increase the update to the next interval.
			self.callLaterProcessRfidRefresh.Stop()
			self.clprIndex += 1
			self.clprTime += datetime.timedelta( seconds = delayIntervals[self.clprIndex] - delayIntervals[self.clprIndex-1] )
			delayToGo = max( 10, int((self.clprTime - now()).total_seconds() * 1000.0) )
			if refreshNow or not self.callLaterProcessRfidRefresh.Start( delayToGo, True ):
				self.processRfidRefresh()
		return False	# Never signal for an update.
	
	def processSprintTimer( self, refreshNow=False ):
		race = Model.race
		if not race:
			return False
		if not race or not race.enableSprintTimer:
			if self.SprintTimer.IsListening():
				self.SprintTimer.StopListener()
			return False
		
		if not self.sprintTimer.IsListening():
			self.updateSprintTimerSettings()
			self.sprintTimer.StartListener( HOST=race.sprintTimerAddress, PORT=race.sprintTimerPort)
	
		data = self.sprintTimer.GetData()
		
		update = False
		
		for d in data:
			if d[0] != 'data':
				continue
			sprintDict, receivedTime, readerComputerTimeDiff = d[1], d[2], d[3]
			
			sortTime = receivedTime;
			
			ppsGood = False
			if "ppsGood" in sprintDict:
				if sprintDict["ppsGood"] == True:
					ppsGood = True
			
			if ppsGood and "sprintStart" in sprintDict and (readerComputerTimeDiff.total_seconds() < race.getSyncTolerance() if race.getSyncTolerance() is not None else True) :
				#if the clocks are less than a second out, use the timer's time for the sprint
				sortTime = datetime.datetime.fromtimestamp(sprintDict["sprintStart"])
				if "sprintStartMillis" in sprintDict:
					sortTime += datetime.timedelta(milliseconds=sprintDict["sprintStartMillis"])
				Utils.writeLog('Trusting timer\'s clock for sprint start time: ' + str(sortTime))
			else:
				if "sprintTime" in sprintDict:
					sortTime -= datetime.timedelta(seconds=sprintDict["sprintTime"])
				Utils.writeLog('Using received time minus sprint duration for sprint start time: ' + str(sortTime))
			
			#print('race start: ' + str(race.startTime) + ' sortTime: ' + str(sortTime)) 
			if race.isRunning() and race.startTime <= sortTime:
				try:
					race.addSprint(sortTime, sprintDict)
					wx.CallLater( race.rfidTagAssociateSeconds*1000, self.refreshResults )
					update = True  #signal for an update.
				except (TypeError, ValueError) as e:
					#Utils.writeLog('Exception adding sprint: ' + str(e))
					continue
				
		return update or refreshNow	# signal for an update if needed.
	
	def sprintTimerTestMode( self, timerTestDialog=None, test=False):
		race = Model.race
		if not race:
			return
		
		if not self.sprintTimer:
			return
		
		self.sprintTimer.setTestMode( test, timerTestDialog=timerTestDialog)
		
	def resetSprintTimer( self, event = None ):
		race = Model.race
		if not race:
			return
		
		if not self.sprintTimer:
			return
		
		if Utils.MessageOKCancel( self, '{}\n{}'.format(_('Reset sprint timer?'), _('In-progress sprint will be lost.')),
									title = _('Reset sprint timer'), iconMask = wx.ICON_QUESTION ):
			self.sprintTimer.sendReset( True )
		
	
	def disconnectSprintTimer( self ):
		race = Model.race
		if not race:
			return
		
		if not self.sprintTimer:
			return
		
		if self.sprintTimer.IsListening():
			self.sprintTimer.StopListener()
			
	
	def updateSprintTimerSettings( self ):
		race = Model.race
		if not race:
			return
		
		if not self.sprintTimer:
			return
		
		self.sprintTimer.setSprintDistance( getattr(race, 'sprintDistance', None) )
		unit = JSONTimer.SPEED_UNKNOWN_UNIT
		if race.distanceUnit == Model.Race.UnitKm:
			unit = JSONTimer.SPEED_KPH
		elif race.distanceUnit == Model.Race.UnitMiles:
			unit = JSONTimer.SPEED_MPH
		self.sprintTimer.setSpeedUnit( unit )
		if self.sprintTimer.IsListening():
			# Only write now if the timer is connected, otherwise settings will be written automatically on reconnect
			self.sprintTimer.writeSettings()
		
	def sendBibToSprintTimer( self, bib ):
		race = Model.race
		if not race:
			return
		
		if not self.sprintTimer:
			return
		
		if self.sprintTimer.IsListening():
			self.sprintTimer.setBib( bib )
		

	def updateRaceClock( self, event = None ):

		doRefresh = False
		alsoRefresh = False
		race = Model.race
		
		if race is None:
			self.SetTitle( Version.AppVerName )
			ChipReader.chipReaderCur.StopListener()
			self.timer.Stop()
			return
		
		self.data.refreshRaceTime()
		
		if race.isUnstarted():
			status = _('Unstarted')
		elif race.isRunning():
			status = _('Running')
			if race.enableJChipIntegration:
				doRefresh = self.processJChipListener()
			elif ChipReader.chipReaderCur.IsListening():
				ChipReader.chipReaderCur.StopListener()
				
			if race.enableSprintTimer:
				alsoRefresh = self.processSprintTimer()
			elif self.sprintTimer.IsListening():
				self.sprintTimer.StopListener()
				
			#self.forecastHistory.updatedExpectedTimes( (now() - race.startTime).total_seconds() )
		else:
			status = _('Finished')

		if not race.isRunning():
			self.SetTitle( '{}-r{} - {} - {}'.format(
							race.name, race.raceNum,
							status,
							Version.AppVerName ) )
			self.timer.Stop()
			return

		self.SetTitle( '{} {}-r{} - {} - {}{}{}{}'.format(
						Utils.formatTime(race.curRaceTime()),
						race.name, race.raceNum,
						status, Version.AppVerName,
						' <{}>'.format(_('SprintTimer')) if race.enableSprintTimer else '',
						' <{}>'.format(_('RFID')) if ChipReader.chipReaderCur.IsListening() else '',
						' <{}>'.format(_('Photos')) if race.enableUSBCamera else '',
		) )

		
			

		self.secondCount += 1
		if self.secondCount % 45 == 0 and race.isChanged():
			self.writeRace()
			
		if doRefresh or alsoRefresh:
			self.nonBusyRefresh()
			self.updateLapCounter()
			if race.ftpUploadDuringRace:
				realTimeFtpPublish.publishEntry()
		elif self.secondCount % 5 == 0:  #Update the lap counter every 5 seconds in case it got out of sync
			self.updateLapCounter()
				
		if not self.timer.IsRunning():
			# Recalculate time to next call, in order to stay in sync with current sprint
			if race.getInProgressSprintTime():
				self.timer.Start( 1000 - (now() - race.inProgressSprintStart).microseconds // 1000, oneShot=wx.TIMER_ONE_SHOT )
			else:
				self.timer.Start( 1000 - (now() - race.startTime).microseconds // 1000, oneShot=wx.TIMER_ONE_SHOT )

# Set log file location.
dataDir = ''
redirectFileName = ''

def MainLoop():
	global dataDir
	global redirectFileName
	
	app = wx.App(False)
	app.SetAppName("SprintTimer")
	
	if 'WXMAC' in wx.Platform:
		wx.Log.SetActiveTarget( LogPrintStackStderr() )
			
	#random.seed()

	parser = ArgumentParser( prog="SprintTimer", description='Sprint Timing Software' )
	parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True, help='hide splash screen')
	parser.add_argument("-r", "--regular", action="store_false", dest="fullScreen", default=True, help='regular size (not full screen)')
	parser.add_argument("-l", "--log", action="store_false", dest="logToFile", default=True, help='log to Stdio rather than file')
	#parser.add_argument("-s", "--simulation", action="store_true", dest="simulation", default=False, help='run simulation automatically')
	#parser.add_argument("-t", "--tt", action="store_true", dest="timetrial", default=False, help='run time trial simulation')
	#parser.add_argument("-b", "--batchpublish", action="store_true", dest="batchpublish", default=False, help="do batch publish and exit")
	#parser.add_argument("-p", "--page", dest="page", default=None, nargs='?', help="page to show after launching")
	parser.add_argument(dest="filename", default=None, nargs='?', help="SprintTimer race file", metavar="RaceFile.spr")
	args = parser.parse_args()
	
	Utils.initTranslation()
	
	dataDir = Utils.getHomeDir()
	redirectFileName = os.path.join(dataDir, 'SprintTimer.log')
	
	print(args.logToFile)
			
	# Set up the log file.  Otherwise, show errors on the screen unbuffered.
	if not args.logToFile and __name__ == '__main__':
		pass
	else:
		try:
			logSize = os.path.getsize( redirectFileName )
			print(logsize)
			if logSize > 1000000:
				os.remove( redirectFileName )
		except Exception:
			pass

		try:
			app.RedirectStdio( filename=redirectFileName )
		except Exception as e:
			print(e)
	
	Utils.writeLog( 'start: {}'.format(Version.AppVerName) )
	Utils.writeLog( 'lang: "{}"'.format(Utils.lang) )
	Utils.writeLog( 'CWD is: {}'.format(os.getcwd()) )
	
	# Configure the main window.
	mainWin = MainWin( None, title=Version.AppVerName, size=(1128,600) )
	
	#Try to open a specified filename.
	fileName = args.filename
	
	#Try to load a race.
	raceLoaded = False
	if fileName:
		try:
			ext = os.path.splitext( fileName )[1]
			if ext == '.spr':
				mainWin.openRace( fileName )
				raceLoaded = True
			#elif ext in ('.xls', '.xlsx', '.xlsm') and IsValidRaceDBExcel(fileName):
				#mainWin.openRaceDBExcel( fileName )
				#raceLoaded = True
		except (IndexError, AttributeError, ValueError):
			pass

	#Check for batchpublish.  If so, do the publish and exit.
	#if args.batchpublish:
		#Utils.writeLog( 'Performing BatchPublish' )
		#if raceLoaded:
			#sys.exit( 0 if doBatchPublish( silent=True, cmdline=True ) else -1 )
		#else:
			#if fileName:
				#msg = 'Cannot load race file "{}".  Cannot do --batchpublish.'.format( fileName )
			#else:
				#msg = 'Missing race file.  Cannot do --batchpublish.'
			#print( msg, file=sys.stderr )
			#Utils.writeLog( msg )
			#sys.exit( -2 )
	
	# Set the upper left icon.
	icon = wx.Icon( os.path.join(Utils.getImageFolder(), 'SprintTimer16x16.ico'), wx.BITMAP_TYPE_ICO )
	mainWin.SetIcon( icon )

	# Show the main window.
	if args.fullScreen:
		mainWin.Maximize( True )
	mainWin.Show()

	if args.verbose:
		ShowSplashScreen()
		#ShowTipAtStartup()
	
	#mainWin.forecastHistory.setSash()
	
	#if args.simulation:
		#wx.CallAfter( mainWin.menuSimulate, userConfirm=False, isTimeTrial=args.timetrial)
	#if args.page:
		#wx.CallAfter( mainWin.showPageName, args.page )
	
	# Start processing events.
	app.MainLoop()

if __name__ == '__main__':
	MainLoop()
