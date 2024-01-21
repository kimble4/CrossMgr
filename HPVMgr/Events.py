import wx
import re
import os
import sys
import Utils
#import ColGrid
from collections import defaultdict
#from Undo import undo
import datetime
import Model
import xlsxwriter
from AddExcelInfo import AddExcelInfo 

class Events( wx.Panel ):
	
	def getExcelFormatsXLSX( workbook ):
		titleStyle = workbook.add_format({
			'bold': True,
			'font_size': 17,
		})

		headerStyleAlignLeft = workbook.add_format({
			'bottom':	2,
			'bold':		True,
			'text_wrap':True,
		})
		
		headerStyleAlignRight = workbook.add_format({
			'bottom':	2,
			'bold':		True,
			'text_wrap':True,
			'align':	'right',
		})
		
		styleAlignLeft = workbook.add_format()
		
		styleAlignRight = workbook.add_format({
			'align':	'right',
		})
		
		#---------------------------------------------------------------
		styleTime = workbook.add_format({
			'align':	'right',
			'num_format': 'hh:mm:ss.000',
		})
		
		styleMMSS = workbook.add_format({
			'align':	'right',
			'num_format': 'mm:ss.000',
		})
		
		styleSS = workbook.add_format({
			'align':	'right',
			'num_format': 'ss.000',
		})
		
		#---------------------------------------------------------------
		# Low-precision time formats
		#
		styleTimeLP = workbook.add_format({
			'align':	'right',
			'num_format': 'hh:mm:ss',
		})
		
		styleMMSSLP = workbook.add_format({
			'align':	'right',
			'num_format': 'mm:ss',
		})
		
		styleSSLP = workbook.add_format({
			'align':	'right',
			'num_format': 'ss',
		})
		
		return {
			'titleStyle':				titleStyle,
			'headerStyleAlignLeft':		headerStyleAlignLeft,
			'headerStyleAlignRight':	headerStyleAlignRight,
			'styleAlignLeft':			styleAlignLeft,
			'styleAlignRight':			styleAlignRight,
			'styleTime':				styleTime,
			'styleHHMMSS':				styleTime,
			'styleMMSS':				styleMMSS,
			'styleSS':					styleSS,

			'styleTimeLP':				styleTimeLP,
			'styleHHMMSSLP':			styleTimeLP,
			'styleMMSSLP':				styleMMSSLP,
			'styleSSLP':				styleSSLP,
		}
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.season = None
		self.evt = None
		self.rnd = None
		
		bigFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
		
		labelAlign = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
		vs = wx.BoxSizer(wx.VERTICAL)
		gbs = wx.GridBagSizer(5, 5)
		row = 0
		
		#seasons list
		self.seasonsGrid = wx.grid.Grid( self )
		self.seasonsGrid.CreateGrid(0, 2)
		self.seasonsGrid.SetColLabelValue(0, 'Season')
		self.seasonsGrid.SetColLabelValue(1, 'Events')
		self.seasonsGrid.HideRowLabels()
		self.seasonsGrid.SetRowLabelSize( 0 )
		self.seasonsGrid.SetMargins( 0, 0 )
		self.seasonsGrid.AutoSizeColumns( True )
		self.seasonsGrid.DisableDragColSize()
		self.seasonsGrid.DisableDragRowSize()
		self.seasonsGrid.EnableEditing(False)
		self.seasonsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onSeasonsRightClick )
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onSeasonsRightClick )
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectSeason )
		gbs.Add( self.seasonsGrid, pos=(row,0), span=(1,1), flag=wx.EXPAND )
		
		row += 1
		gbs.Add( wx.StaticText( self, label='Current selection:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		
		row += 1
		gbs.Add( wx.StaticText( self, label='Sign-on sheet:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		
		row = 0
		
		#events list
		self.eventsGrid = wx.grid.Grid( self )
		self.eventsGrid.CreateGrid(0, 2)
		self.eventsGrid.SetColLabelValue(0, 'Season\'s events')
		self.eventsGrid.SetColLabelValue(1, 'Rounds')
		self.eventsGrid.HideRowLabels()
		self.eventsGrid.SetRowLabelSize( 0 )
		self.eventsGrid.SetMargins( 0, 0 )
		self.eventsGrid.AutoSizeColumns( True )
		self.eventsGrid.DisableDragColSize()
		self.eventsGrid.DisableDragRowSize()
		self.eventsGrid.EnableEditing(False)
		self.seasonsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onEventsRightClick )
		self.eventsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onEventsRightClick )
		self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectEvt )
		gbs.Add( self.eventsGrid, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		row += 1
		
		#current selection
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.currentSelection = wx.StaticText( self, label='None' )
		self.currentSelection.SetFont(bigFont)
		hs.Add( self.currentSelection, flag=wx.ALIGN_CENTER_VERTICAL )
		
		hs.AddStretchSpacer()
		
		bs = wx.BoxSizer( wx.VERTICAL )
		#edit button
		self.editEntryButton = wx.Button( self, label='Edit entries')
		self.editEntryButton.SetToolTip( wx.ToolTip('Edit entries'))
		self.editEntryButton.Disable()
		self.Bind( wx.EVT_BUTTON, self.onEditEntryButton, self.editEntryButton )
		bs.Add( self.editEntryButton, flag=wx.ALIGN_RIGHT )
		
		#edit button
		self.editRacesButton = wx.Button( self, label='Edit races')
		self.editRacesButton.SetToolTip( wx.ToolTip('Edit races'))
		self.editRacesButton.Disable()
		self.Bind( wx.EVT_BUTTON, self.onEditRacesButton, self.editRacesButton )
		bs.Add( self.editRacesButton, flag=wx.ALIGN_RIGHT )
		
		hs.Add( bs, flag=wx.ALIGN_CENTER_VERTICAL)
	
		gbs.Add( hs, pos=(row,1), span=(1,2), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.EXPAND )
		
		row += 1
		
		#signon filename
		self.signonFileName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(600,-1))
		self.signonFileName.SetValue( '' )
		self.signonFileName.Disable()
		self.signonFileName.Bind( wx.EVT_TEXT_ENTER, self.onEditSignon )
		gbs.Add( self.signonFileName, pos=(row,1), span=(1,3), flag=wx.ALIGN_LEFT )
		
		row += 1
		
		#write button
		self.writeSignonButton = wx.Button( self, label='Write sign-on sheet')
		self.writeSignonButton.SetToolTip( wx.ToolTip('Click to write the sign-on sheet for the selected event to disk'))
		self.writeSignonButton.Disable()
		self.writeSignonButton.Bind( wx.EVT_BUTTON, self.writeSignonSheet )
		gbs.Add( self.writeSignonButton, pos=(row,1), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		row = 0
		#rounds list
		self.roundsGrid = wx.grid.Grid( self )
		self.roundsGrid.CreateGrid(0, 2)
		self.roundsGrid.SetColLabelValue(0, 'Event\'s rounds')
		self.roundsGrid.SetColLabelValue(1, 'Races')
		self.roundsGrid.HideRowLabels()
		#self.roundsGrid.AutoSize()
		self.roundsGrid.SetRowLabelSize( 0 )
		self.roundsGrid.SetMargins( 0, 0 )
		self.roundsGrid.AutoSizeColumns( True )
		self.roundsGrid.DisableDragColSize()
		self.roundsGrid.DisableDragRowSize()
		self.roundsGrid.EnableEditing(False)
		self.seasonsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRoundsRightClick )
		self.roundsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onRoundsRightClick )
		self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectRnd )
		gbs.Add( self.roundsGrid, pos=(row,2), span=(1,1), flag=wx.EXPAND )
		
		row += 3
		
		self.signonBrowseButton = wx.Button( self, label='{}...'.format(_('Browse')) )
		self.signonBrowseButton.Disable()
		self.signonBrowseButton.Bind( wx.EVT_BUTTON, self.onBrowseSignon )
		gbs.Add( self.signonBrowseButton, pos=(row,2), span=(1,1), flag=wx.ALIGN_TOP|wx.ALIGN_RIGHT )
	
		
		vs.Add( gbs )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def writeSignonSheet( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'signonFileName' in evt:
					xlFName = evt['signonFileName']
					if 'rounds' in evt:
						
						wb = xlsxwriter.Workbook( xlFName )
						formats = Events.getExcelFormatsXLSX( wb )
						ues = Utils.UniqueExcelSheetName()
						
						for rndName in evt['rounds']:
							sheetCur = wb.add_worksheet( ues.getSheetName(rndName) )
							database.getRoundAsExcelSheetXLSX( rndName, formats, sheetCur )
							
						AddExcelInfo( wb )
						try:
							wb.close()
							# if self.launchExcelAfterPublishingResults:
							# 	Utils.LaunchApplication( xlFName )
							Utils.writeLog( '{}: {}'.format(_('Excel file written to'), xlFName) )
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
						except Exception as e:
							Utils.logException( e, sys.exc_info() )
		
	def selectSeason( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.season = row
			self.evt = None
			self.rnd = None
			self.commit()
			self.updateSignonSheetName()
			self.editEntryButton.Disable()
			self.editRacesButton.Disable()
			self.refreshSeasonsGrid()
			self.refreshEventsGrid()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
			

	def onSeasonsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Seasons')
		add = menu.Append( wx.ID_ANY, 'Add new season', 'Add a new season...' )
		self.Bind( wx.EVT_MENU, self.addSeason, add )
		if row >= 1 or (row == 0 and len(self.seasonsGrid.GetCellValue(row, 0).strip()) > 0):
			delete = menu.Append( wx.ID_ANY, 'Delete ' + database.getSeasonsList()[row] + ' from list', 'Delete this season...' )
			self.Bind( wx.EVT_MENU, lambda event, r=row: self.deleteSeason(event, r), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addSeason( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			with wx.TextEntryDialog(self, 'Enter the name for the new season:', caption='Add season', value='New Season', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newSeason = dlg.GetValue()
					with Model.LockDatabase() as db:
						if newSeason not in db.seasons:
							db.seasons[newSeason] = { 'categories':None }
							db.setChanged()
							self.season = len(db.seasons) - 1
							self.commit()
						else:
							Utils.MessageOK( self, 'Season ' + newSeason +' already exists!', title = 'Season exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
					self.refreshSeasonsGrid()
					self.refreshEventsGrid()
					self.refreshRoundsGrid()
					self.refreshCurrentSelection()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
						
	def deleteSeason( self, event, row ):
		database = Model.database
		if database is None:
			return
		try:
			with Model.LockDatabase() as db:
				season = self.seasonsGrid.GetCellValue(row, 0)
				del db.seasons[season]
				db.setChanged()
			self.season = None
			self.refreshSeasonsGrid()
			self.refreshEventsGrid()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def selectEvt( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.evt = row
			self.rnd = None
			self.updateSignonSheetName()
			self.editEntryButton.Enable()
			self.editRacesButton.Disable()
			self.commit()
			self.refreshEventsGrid()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
			
	def updateSignonSheetName( self ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'signonFileName' in evt:
					self.signonFileName.SetValue(evt['signonFileName'])
					if evt['signonFileName']:
						self.writeSignonButton.Enable()
				else:
					self.signonFileName.SetValue('')
					self.writeSignonButton.Disable()
				self.signonFileName.Enable()
				self.signonBrowseButton.Enable()
				self.signonFileName.ShowPosition(self.signonFileName.GetLastPosition())
				return
		self.writeSignonButton.Disable()
		self.signonFileName.Disable()
		self.signonBrowseButton.Disable()
			
	def onEventsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Events')
		add = menu.Append( wx.ID_ANY, 'Add new event', 'Add a new event...' )
		self.Bind( wx.EVT_MENU, self.addEvent, add )
		if row >= 1 or (row == 0 and len(self.eventsGrid.GetCellValue(row, 0).strip()) > 0):
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[row]
			delete = menu.Append( wx.ID_ANY, 'Delete ' + evtName + ' from list', 'Delete this event...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteEvent(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addEvent( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		try:
			with wx.TextEntryDialog(self, 'Enter the name for the new event:', caption='Add event', value='New Event', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newEvent = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						if 'events' not in season:
							season['events'] = {}
						if newEvent not in season['events']:
							season['events'][newEvent] = {}
							db.setChanged()
							self.evt = len(season['events']) - 1
							self.editEntryButton.Enable()
							wx.CallAfter( self.commit )
						else:
							Utils.MessageOK( self, 'Event ' + newEvent +' already exists!', title = 'Event exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
				self.refreshEventsGrid()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
						
	def deleteEvent( self, event, row ):
		database = Model.database
		if database is None:
			return
		seasonName = database.getSeasonsList()[self.season]
		season = database.seasons[seasonName]
		evtName = list(season)[row]
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete ' + evtName + '?\nThis will also delete ALL associated rounds and races!', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete event: ' + evtName)
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					event = self.eventsGrid.GetCellValue(row, 0)
					del season['events'][event]
					db.setChanged()
					self.evt = None
					self.rnd = None
					self.commit()
				self.refreshEventsGrid()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
			
	def selectRnd( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.rnd = row
			self.editRacesButton.Enable()
			self.commit()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
		
	def onRoundsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Rounds')
		add = menu.Append( wx.ID_ANY, 'Add new round', 'Add a new round...' )
		self.Bind( wx.EVT_MENU, self.addRound, add )
		if row >= 1 or (row == 0 and len(self.eventsGrid.GetCellValue(row, 0).strip()) > 0):
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			evt = season['events'][evtName]
			rndName = list(evt['rounds'])[row]
			delete = menu.Append( wx.ID_ANY, 'Delete ' + rndName + ' from list', 'Delete this round...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteRound(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addRound( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		try:
			with wx.TextEntryDialog(self, 'Enter the name for the new round:', caption='Add round', value='New Round', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newRound = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						if 'rounds' not in evt:  # create rounds dict if it does not exist
							evt['rounds'] = {}
						#print('season: ' + seasonName + ', event: ' + evtName + ', rounds: ' + str(evt['rounds']))
						if newRound not in evt['rounds']:
							evt['rounds'][newRound] = []
							db.setChanged()
							self.rnd = len(evt['rounds'])-1
							self.commit()
						else:
							Utils.MessageOK( self, 'Round ' + newRound +' already exists!', title = 'Round exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
					self.refreshRoundsGrid()
					self.refreshCurrentSelection()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
						
	def deleteRound( self, event, row ):
		database = Model.database
		if database is None:
			return
		seasonName = database.getSeasonsList()[self.season]
		season = database.seasons[seasonName]
		evtName = list(season['events'])[self.evt]
		evt = season['events'][evtName]
		rndName = list(evt)[row]
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete ' + rndName + '?\nThis will also delete ALL associated races!', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete event: ' + evtName)
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rnd = self.roundsGrid.GetCellValue(row, 0)
					del evt['rounds'][rnd]
					db.setChanged()
					self.rnd = None
					self.commit()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				
	def onBrowseSignon( self, event ):
		database = Model.database
		if database is None:
			return
		defaultFileName = self.signonFileName.GetValue()
		if defaultFileName.endswith('.xlsx'):
			dirName = os.path.dirname( defaultFileName )
			fileName = os.path.basename( defaultFileName )
		else:
			dirName = defaultFileName
			if self.season is not None and self.evt is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				fileName = 'racers_' + list(season['events'])[self.evt].lower().replace(' ', '_') + '.xlsx'
			else:
				fileName = ''
			if not dirName:
				dirName = Utils.getDocumentsDir()
		with wx.FileDialog( self, message=_("Choose Sigon Sheet File"),
							defaultDir=dirName, 
							defaultFile=fileName,
							wildcard=_("CrossMgr sign-on sheet (*.xlsx)|*.xlsx"),
							style=wx.FD_SAVE ) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				fn = dlg.GetPath()
				self.signonFileName.SetValue( fn )
				if self.season is not None and self.evt is not None:
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						evt['signonFileName'] = fn
						database.setChanged()
						wx.CallAfter( self.refresh )
		self.signonFileName.ShowPosition(self.signonFileName.GetLastPosition())
			
	def onEditSignon( self, event ):
		database = Model.database
		if database is None:
			return
		fn = self.signonFileName.GetValue()
		if fn.endswith('.xlsx'):
			dirName = os.path.dirname( fn )
			fileName = os.path.basename( fn )
		else:
			Utils.MessageOK( self, 'Sign-on sheet should be an .xlsx file!', title = 'Incorrect filetype', iconMask = wx.ICON_ERROR )
			return
		if self.season is not None and self.evt is not None:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[self.season]
				season = db.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['event'][evtName]
				evt['signonFileName'] = fn
				database.setChanged()
		self.signonFileName.ShowPosition(self.signonFileName.GetLastPosition())
		
	def onEditEntryButton( self, event ):
		Utils.getMainWin().showEventEntryPage()
		
	def onEditRacesButton( self, event ):
		Utils.getMainWin().showRaceAllocationPage()
			
	def refreshSeasonsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.seasonsGrid )
		seasons = database.getSeasonsList()
		for seasonName in seasons:
			self.seasonsGrid.AppendRows(1)
			row = self.seasonsGrid.GetNumberRows() -1
			self.seasonsGrid.SetCellValue(row, 0, str(seasonName))
			self.seasonsGrid.SetCellValue(row, 1, str(len(database.seasons[seasonName]['events'])) if 'events' in database.seasons[seasonName] else '')
			self.seasonsGrid.SetCellAlignment(row, 1, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
		self.seasonsGrid.AutoSize()
	
	def refreshEventsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.eventsGrid )
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			self.eventsGrid.SetColLabelValue(0, seasonName + '\'s events')
			#print('season: ' + seasonName + ', events: ' + str(season))
			if 'events' in season:
				for eventName in season['events']:
					self.eventsGrid.AppendRows(1)
					row = self.eventsGrid.GetNumberRows() -1
					self.eventsGrid.SetCellValue(row, 0, eventName )
					self.eventsGrid.SetCellValue(row, 1, str(len(season['events'][eventName]['rounds'])) if 'rounds' in season['events'][eventName] else '')
					self.eventsGrid.SetCellAlignment(row, 1, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
		else:
			self.eventsGrid.SetColLabelValue(0, 'Season\'s events')
		self.eventsGrid.AutoSize()
			
	def refreshRoundsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.roundsGrid )
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				self.roundsGrid.SetColLabelValue(0, evtName + '\'s rounds')
				evt = season['events'][evtName]
				if 'rounds' in evt:
					#print('season: ' + seasonName + ', event: ' + evtName + ', rounds: ' + str(evt['rounds']))
					for rndName in evt['rounds']:
						self.roundsGrid.AppendRows(1)
						row = self.roundsGrid.GetNumberRows() -1
						self.roundsGrid.SetCellValue(row, 0, rndName)
						self.roundsGrid.SetCellValue(row, 1, str(len(evt['rounds'][rndName])) if 'rounds' in evt else '')
						self.roundsGrid.SetCellAlignment(row, 1, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)  
			else:
				self.roundsGrid.SetColLabelValue(0, 'Event\'s rounds')
		self.roundsGrid.AutoSize()

	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )
			
	def refreshCurrentSelection( self ):
		database = Model.database
		if database is None:
			return
		selection = []
		title = 'None'
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			selection.append( seasonName )
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				selection.append( evtName )
				evt = season['events'][evtName]
				if self.rnd is not None and 'rounds' in evt:
					rndName = list(evt['rounds'])[self.rnd]
					selection.append( rndName )
			title = ', '.join(n for n in selection)
		self.currentSelection.SetLabel( title )
		database.selection = selection
		
	def commit( self, event=None ):
		Utils.writeLog('Events commit: ' + str(event))
		with Model.LockDatabase() as db:
			db.curSeason = self.season
			db.curEvt = self.evt
			db.curRnd = self.rnd
			db.setChanged()
	
	def refresh( self ):
		Utils.writeLog('Events refresh')
		database = Model.database
		if database is not None:
			self.season = database.curSeason
			self.evt = database.curEvt
			self.rnd = database.curRnd
		self.refreshSeasonsGrid()
		self.refreshEventsGrid()
		self.refreshRoundsGrid()
		self.refreshCurrentSelection()
		self.updateSignonSheetName()
		self.Layout()
