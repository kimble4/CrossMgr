import os
import re
import sys
import datetime
import webbrowser
import platform
import gzip

import wx
import wx.adv as adv
from wx.lib.wordwrap import wordwrap
import wx.lib.agw.flatnotebook as flatnotebook
from html import escape

import locale
try:
	localDateFormat = locale.nl_langinfo( locale.D_FMT )
	localTimeFormat = locale.nl_langinfo( locale.T_FMT )
except Exception:
	localDateFormat = '%Y-%m-%d'
	localTimeFormat = '%H:%M'

import pickle
from argparse import ArgumentParser
import xlsxwriter

import Utils

from HelpSearch			import HelpSearchDialog, getHelpURL
from Utils				import logCall, logException
import Version
from Riders 			import Riders
from RiderDetail		import RiderDetail
from Teams				import Teams
from Events				import Events
from Categories			import Categories
from EventEntry			import EventEntry
from RaceAllocation		import RaceAllocation
from Impinj				import Impinj
from Settings			import Settings
import Model


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
	bitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'HPVMgrSplash.png'), wx.BITMAP_TYPE_PNG )
	
	#Write in the version number into the bitmap.
	w, h = bitmap.GetSize()
	dc = wx.MemoryDC()
	dc.SelectObject( bitmap )
	fontHeight = h//10
	dc.SetFont( wx.Font( (0,fontHeight), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ) )
	v = Version.AppVerName.split('-',2)
	yText = int(h * 0.44)
	for i, v in enumerate(Version.AppVerName.split('-',2)):
		dc.DrawText( v.replace('HPVMgr','Version'), w // 20, yText + i*fontHeight )
		
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
		
		self.filehistory = wx.FileHistory(8)
		dataDir = Utils.getHomeDir()
		configFileName = os.path.join(dataDir, 'HPVMgr.cfg')
		self.config = wx.Config(appName="HPVMgr",
								vendorName="BHPC",
								localFilename=configFileName
		)
		self.filehistory.Load(self.config)
		
		self.fileName = None
		
		defaultFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		self.defaultFontSize = self.config.ReadInt('fontSize') if self.config.ReadInt('fontSize') else defaultFont.GetFractionalPointSize()
		defaultFont.SetFractionalPointSize(self.defaultFontSize)
		self.SetFont(defaultFont)
		
		#Configure the main menu.
		self.menuBar = wx.MenuBar(wx.MB_DOCKABLE)

		#-----------------------------------------------------------------------
		self.fileMenu = wx.Menu()

		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_NEW, _("&New...\tCtrl+N"), _("Create a new database"), Utils.GetPngBitmap('document-new.png') )
		self.Bind(wx.EVT_MENU, self.menuNew, item )

		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_SAVE, _("&Save...\tCtrl+S"), _("Save the database"), Utils.GetPngBitmap('document-save.png') )
		self.Bind(wx.EVT_MENU, self.menuSave, item )

		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_SAVEAS, _("Save &As...\tCtrl+Shift+S"), _("Save the database to a new file"), Utils.GetPngBitmap('document-save.png') )
		self.Bind(wx.EVT_MENU, self.menuSaveAs, item )

		self.fileMenu.AppendSeparator()
		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_OPEN, _("&Open...\tCtrl+O"), _("Open a database"), Utils.GetPngBitmap('document-open.png') )
		self.Bind(wx.EVT_MENU, self.menuOpen, item )

		recent = wx.Menu()
		menu = self.fileMenu.AppendSubMenu( recent, _("Recent Fil&es") )
		menu.SetBitmap( Utils.GetPngBitmap('document-open-recent.png') )
		self.filehistory.UseMenu( recent )
		self.filehistory.AddFilesToMenu()
		
		item = AppendMenuItemBitmap( self.fileMenu, wx.ID_EXIT, _("E&xit\tCtrl+Q"), _("Exit HPVMgr"), Utils.GetPngBitmap('exit.png') )
		self.Bind(wx.EVT_MENU, self.menuExit, item )
		
		self.Bind(wx.EVT_MENU_RANGE, self.menuFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9)
		
		self.menuBar.Append( self.fileMenu, _("&File") )

		
		#-----------------------------------------------------------------------
		self.editMenu = wx.Menu()
# 		item = self.undoMenuButton = wx.MenuItem( self.editMenu, wx.ID_UNDO , _("&Undo\tCtrl+Z"), _("Undo the last edit") )
# 		self.undoMenuButton.SetBitmap( Utils.GetPngBitmap('Undo-icon.png') )
# 		self.editMenu.Append( self.undoMenuButton )
# 		self.Bind(wx.EVT_MENU, self.menuUndo, item )
# 		self.undoMenuButton.Enable( False )
# 		
# 		self.redoMenuButton = wx.MenuItem( self.editMenu, wx.ID_REDO , _("&Redo\tCtrl+Y"), _("Redo the last edit") )
# 		self.redoMenuButton.SetBitmap( Utils.GetPngBitmap('Redo-icon.png') )
# 		item = self.editMenu.Append( self.redoMenuButton )
# 		self.Bind(wx.EVT_MENU, self.menuRedo, item )
# 		self.redoMenuButton.Enable( False )
# 		self.editMenu.AppendSeparator()
		
		item = self.editMenu.Append( wx.ID_ANY, _("&Commit changes...\tCtrl+O"), _("Commit changes...") )
		self.menuCommitID = item.GetId()
		self.Bind(wx.EVT_MENU, self.menuCommit, item )
		
		item = self.editMenu.Append( wx.ID_ANY, _("&Add Rider...\tCtrl+A"), _("Add a new Rider...") )
		self.menuAddID = item.GetId()
		self.Bind(wx.EVT_MENU, self.menuAddRider, item )
		
		item = self.editMenu.Append( wx.ID_ANY, _('&Delete Rider...\tCtrl+D'), _('Delete a rider...') )
		self.Bind( wx.EVT_MENU, self.menuDeleteRider, item )
		
		self.editMenuItem = self.menuBar.Append( self.editMenu, _("&Edit") )

	
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
		
		#self.fileDrop = FileDrop()	# Create a file drop target for all the main pages.
		
		#Add all the pages to the notebook.
		self.pages = []

		def addPage( page, name ):
			self.notebook.AddPage( page, name )
			self.pages.append( page )
			
		self.attrClassName = [
			[ 'riders',			Riders,				_('Riders') ],
			[ 'riderDetail',	RiderDetail,		_('RiderDetail') ],
			[ 'teams',			Teams,				_('Teams') ],
			[ 'events',			Events,				_('Events') ],
			[ 'categories',		Categories,			_('Categories') ],
			[ 'eventEntry',		EventEntry,			_('EventEntry') ],
			[ 'raceAllocation',	RaceAllocation,		_('RaceAllocation') ],
			[ 'impinj',			Impinj,				_('WriteTags') ],
			[ 'settings',		Settings,			_('Settings') ],
		]
		
		for i, (a, c, n) in enumerate(self.attrClassName):
			setattr( self, a, c(self.notebook) )
			#getattr( self, a ).SetDropTarget( self.fileDrop )
			addPage( getattr(self, a), '{}. {}'.format(i+1, n) )
			setattr( self, 'i' + a[0].upper() + a[1:] + 'Page', i )
		
		self.toolsMenu = wx.Menu()
		
		self.writeSignonMenuItem = self.toolsMenu.Append( wx.ID_ANY, _("Write Sign-on-shee&t...\tCtrl+T"), _("Write the CrossMgr sign-on sheet for current event") )
		self.Bind(wx.EVT_MENU, self.menuWriteSignon, self.writeSignonMenuItem )
		
		self.toolsMenu.AppendSeparator()

		item = self.toolsMenu.Append( wx.ID_ANY, _("Copy &Log File to Clipboard...\tCtrl+L"), _("Copy Log File to Clipboard") )
		self.Bind(wx.EVT_MENU, self.menuCopyLogFileToClipboard, item )

		self.toolsMenu.AppendSeparator()

		self.menuBar.Append( self.toolsMenu, _("&Tools") )
		
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
		self.helpMenu = wx.Menu()
		
		item = self.helpMenu.Append( wx.ID_HELP, _("&Help..."), _("Help with HPVMgr...") )
		self.Bind(wx.EVT_MENU, self.menuHelp, item )
		
		item = self.helpMenu.Append( wx.ID_ANY, _("Help Search..."), _("Search Help...") )
		self.Bind(wx.EVT_MENU, self.menuHelpSearch, item )
		self.helpSearch = HelpSearchDialog( self, title=_('Help Search') )

		#self.helpMenu.AppendSeparator()
		#item = self.helpMenu.Append( wx.ID_ANY, _("&What's New..."), _("What's New in CrossMgr...") )
		#self.Bind(wx.EVT_MENU, self.menuHelpWhatsNew, item )

		#self.helpMenu.AppendSeparator()
		#item = self.helpMenu.Append( wx.ID_ANY, _("&QuickStart..."), _("Get started with CrossMgr Now...") )
		#self.Bind(wx.EVT_MENU, self.menuHelpQuickStart, item )
		
		self.helpMenu.AppendSeparator()

		item = self.helpMenu.Append( wx.ID_ABOUT , _("&About..."), _("About HPVMgr...") )
		self.Bind(wx.EVT_MENU, self.menuAbout, item )

		#item = self.helpMenu.Append( wx.ID_ANY, _("&Tips at Startup..."), _("Enable/Disable Tips at Startup...") )
		#self.Bind(wx.EVT_MENU, self.menuTipAtStartup, item )


		self.menuBar.Append( self.helpMenu, _("&Help") )

		#------------------------------------------------------------------------------
		#------------------------------------------------------------------------------
		#------------------------------------------------------------------------------
		self.SetMenuBar( self.menuBar )

		#------------------------------------------------------------------------------
		#Set the accelerator table so we can switch windows with the function keys.
		accTable = [(wx.ACCEL_NORMAL, wx.WXK_F1 + i, jumpToIds[i]) for i in range(min(11,len(jumpToIds)))]
		self.contextHelpID = wx.ID_HELP
		self.Bind(wx.EVT_MENU, self.onContextHelp, id=self.contextHelpID )
		accTable.append( (wx.ACCEL_CTRL, ord('H'), self.contextHelpID) )
		accTable.append( (wx.ACCEL_SHIFT, wx.WXK_F1, self.contextHelpID) )
		accTable.append( (wx.ACCEL_CTRL, ord('O'), self.menuCommitID) )
		aTable = wx.AcceleratorTable( accTable )
		self.SetAcceleratorTable(aTable)
		
		#------------------------------------------------------------------------------
		self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
		
	def menuShowPage( self, event ):
		self.showPage( self.idPage[event.GetId()] )

	def menuUndo( self, event ):
		undo.doUndo()
		self.refresh()
		
	def menuRedo( self, event ):
		undo.doRedo()
		self.refresh()
		
	
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
		
	def menuPlaySounds( self, event ):
		self.playSounds = self.menuItemPlaySounds.IsChecked()
		self.config.WriteBool( 'playSounds', self.playSounds )
		
	def menuLaunchExcelAfterPublishingResults( self, event ):
		self.launchExcelAfterPublishingResults = self.menuItemLaunchExcelAfterPublishingResults.IsChecked()
		self.config.WriteBool( 'launchExcelAfterPublishingResults', self.launchExcelAfterPublishingResults )
			
	
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
	
	#--------------------------------------------------------------------------------------------
	
	@logCall
	def menuWriteSignon( self, event ):
		self.events.writeSignonSheet()
		
	@logCall
	def menuCommit( self, event ):
		self.commit()
	
	@logCall
	def menuAddRider( self, event ):
		self.riders.addNewRider( None, None )
	
	@logCall
	def menuDeleteRider( self, event):
		self.riders.deleteRider( None, None )
	
	@logCall
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
	

	# def getFormatFilename( self, filecode ):
	# 	return BatchPublishAttrs.formatFilename[filecode]( os.path.splitext(self.fileName or '')[0] )

	#--------------------------------------------------------------------------------------------
	
	@logCall
	def onCloseWindow( self, event ):
		database = Model.database
		if database:
			if database.hasChanged():
				ret = Utils.MessageYesNoCancel( self, _('Save changes before exiting?'), _('Changes unsaved'), iconMask = wx.ICON_QUESTION)
				if ret == wx.ID_YES:
					Utils.writeLog( 'Saving changes before exiting' )
					self.saveDatabase()
				elif ret == wx.ID_NO:
					Utils.writeLog( 'Exiting without saving changes!' )
				else:
					Utils.writeLog( 'Exit aborted' )
					return
		wx.Exit()

	@logCall
	def menuNew( self, event ):
		self.showPage(self.iRidersPage)
		Model.database = Model.Database()
		self.refreshAll()
		
		
	def updateRecentFiles( self ):
		self.filehistory.AddFileToHistory(Model.database.fileName)
		self.filehistory.Save(self.config)
		self.config.Write('dataFile', Model.database.fileName)
		self.config.Flush()

	@logCall
	def openDatabase( self, fileName, silent=False, backup=True ):
		busy = wx.BusyCursor()
		ext = os.path.splitext( fileName )[1]
		with Model.LockDatabase() as db:
			try:
			
				if ext == '.hdz':
					with gzip.open(fileName, "rt", encoding='UTF-8') as infile:
						Utils.writeLog( 'Loading database from: ' + str(fileName) )
						Model.database = Model.Database( fileName, jsonDataFile=infile )
						self.updateRecentFiles()
						self.showPage(self.iRidersPage)
						self.refreshAll()
				elif ext == '.hdb':
					with open(fileName, "r") as infile:
						Utils.writeLog( 'Loading database from: ' + str(fileName) )
						Model.database = Model.Database( fileName, jsonDataFile=infile )
						self.updateRecentFiles()
						self.showPage(self.iRidersPage)
						self.refreshAll()
				else:
					Utils.writeLog('Unrecognised file type: ' + ext)
					return
				if backup:
					backupFileName = fileName.rsplit('.', 1)[0] + '_backup_{:%Y-%m-%d}.hdz'.format(datetime.datetime.now())
					if not os.path.isfile(backupFileName):
						Utils.writeLog('Saving database backup to: ' + backupFileName )
						with Model.LockDatabase() as db:
							with gzip.open(backupFileName, "wt", encoding='UTF-8') as outfile:
								outfile.write(db.getDatabaseAsJSON())
								db.setChanged( False )
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				self.refreshAll()
				if silent:
				 	return
				Utils.MessageOK(self, '{} "{}"\n\n{}.'.format(_('Cannot Open File'), fileName, e), _('Cannot Open File'), iconMask=wx.ICON_ERROR )

	@logCall
	def menuOpen( self, event ):
		dlg = wx.FileDialog( self, message=_("Choose a Database file"),
							defaultFile = '',
							defaultDir = Utils.getFileDir(),
							wildcard = _('HPVMgr database (*.hdb;*.hdz)|*.hdb;*.hdz'),
							style=wx.FD_OPEN | wx.FD_CHANGE_DIR )
		if dlg.ShowModal() == wx.ID_OK:
			self.openDatabase( dlg.GetPath() )
	
	@logCall
	def menuSaveAs( self, event ):
		database = Model.database
		if database is None:
			return
		self.commit()
		with wx.FileDialog( self, message=_("Choose Database File"),
							defaultDir=Utils.getFileDir(), 
							defaultFile='new_database',
							wildcard=_("HPV database (*.hdb)|*.hdb"),
							style=wx.FD_SAVE ) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				fn = dlg.GetPath()
				if not fn.lower().endswith('.hdb'):
					fn += '.hdb'
				if os.path.exists(fn):
					if not Utils.MessageOKCancel(self, '\n\n'.join( [
							_("This file already exists:"),
							'{}',
							_("Overwrite?")]).format(fn), _("Overwrite Existing File?")):
						return
				Utils.writeLog('filename is now: ' + str(fn))
				database.fileName = fn
				database.setChanged()
				self.saveDatabase()
	
	@logCall
	def menuSave( self, event ):
		self.commit()
		self.saveDatabase()
		
	def saveDatabase( self ):
		database = Model.database
		if database is None:
			return
		fileName = database.fileName
		if fileName is None:
			Utils.MessageOK(self, _("Database filename is not set"), _("Error"), wx.ICON_ERROR )
			return
		Utils.writeLog( 'Saving database to ' + str(fileName) )
		with Model.LockDatabase() as db:
			with open(fileName, "w") as outfile:
				outfile.write(db.getDatabaseAsJSON())
				db.setChanged( False )
				self.updateRecentFiles()
		

	def menuFileHistory( self, event ):
		fileNum = event.GetId() - wx.ID_FILE1
		fileName = self.filehistory.GetHistoryFile(fileNum)
		self.filehistory.AddFileToHistory(fileName)  # move up the list
		self.openDatabase( fileName )
		
	
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
	
	@logCall
	def onContextHelp( self, event ):
		try:
			webbrowser.open( getHelpURL(self.attrClassName[self.notebook.GetSelection()][2] + '.html') )
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
_("""Manage HPV rider sign-on database.

Written for use by the British Human Power Club.

"""),
			500, wx.ClientDC(self))
		info.WebSite = ("https://github.com/kimble4/CrossMgr", "CrossMgr GitHub")
		info.Developers = ["Kim Wall (technical@bhpc.org.uk)"]

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
		
	def showEventEntryPage( self ):
		self.showPage( self.iEventEntryPage )

	def showRaceAllocationPage( self ):
		self.showPage( self.iRaceAllocationPage )

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

	def refresh( self ):
		self.refreshCurrentPage()

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
			self.numSelect = num

	#-------------------------------------------------------------
	

		



# Set log file location.
dataDir = ''
redirectFileName = ''

def MainLoop():
	global dataDir
	global redirectFileName
	
	app = wx.App(False)
	app.SetAppName("HPVMgr")
	
	if 'WXMAC' in wx.Platform:
		wx.Log.SetActiveTarget( LogPrintStackStderr() )
			
	#random.seed()

	parser = ArgumentParser( prog="HPVMgr", description='Sprint Timing Software' )
	parser.add_argument("-q", "--quiet", action="store_false", dest="verbose", default=True, help='hide splash screen')
	parser.add_argument("-r", "--regular", action="store_false", dest="fullScreen", default=True, help='regular size (not full screen)')
	parser.add_argument("-l", "--log", action="store_false", dest="logToFile", default=True, help='log to Stdio rather than file')
	parser.add_argument(dest="filename", default=None, nargs='?', help="HPVMgr data file", metavar="Database.hdb")
	args = parser.parse_args()
	
	Utils.initTranslation()
	
	dataDir = Utils.getHomeDir()
	redirectFileName = os.path.join(dataDir, 'HPVMgr.log')
	
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
	mainWin = MainWin( None, title=Version.AppVerName, size=(1400,768) )
	
	#Try to open a specified filename.
	fileName = args.filename
	
	#Try to load a race.
	#raceLoaded = False
	if fileName:
		try:
			ext = os.path.splitext( fileName )[1]
			if ext == '.hdb' or ext == '.hdz':
				mainWin.openDatabase( fileName )
		except (IndexError, AttributeError, ValueError):
			pass
	else:
		db = mainWin.config.Read('dataFile', '')
		if db:
			mainWin.openDatabase(db, silent=True)

	# Set the upper left icon.
	icon = wx.Icon( os.path.join(Utils.getImageFolder(), 'HPVMgr16x16.ico'), wx.BITMAP_TYPE_ICO )
	mainWin.SetIcon( icon )

	# Show the main window.
	if args.fullScreen:
		mainWin.Maximize( True )
	mainWin.Show()

	if args.verbose:
		ShowSplashScreen()
		#ShowTipAtStartup()
		
	
	# Start processing events.
	app.MainLoop()

if __name__ == '__main__':
	MainLoop()
