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
import Flags

class Events( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.season = None
		self.evt = None
		self.rnd = None
		
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
		gbs.Add( wx.StaticText( self, label='Current selection:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT)

		row += 1		
		#commit button
		self.editRacesButton = wx.Button( self, label='Edit races')
		self.editRacesButton.SetToolTip( wx.ToolTip('Edit races'))
		self.editRacesButton.Disable()
		self.Bind( wx.EVT_BUTTON, self.commit, self.editRacesButton )
		gbs.Add( self.editRacesButton, pos=(row,0), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )

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
		
		self.currentSelection = wx.StaticText( self, label='None' )
		gbs.Add( self.currentSelection, pos=(row,1), span=(1,3), flag=wx.ALIGN_LEFT )
		
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
		
		
		
		vs.Add( gbs )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def selectSeason( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.season = row
			self.evt = None
			self.rnd = None
			self.editRacesButton.Disable()
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
			self.Bind( wx.EVT_MENU, lambda event: self.deleteSeason(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addSeason( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			print('add seson')
			with wx.TextEntryDialog(self, 'Enter the name for the new season:', caption='Add season', value='New Season', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newSeason = dlg.GetValue()
					with Model.LockDatabase() as db:
						if newSeason not in db.seasons:
							db.seasons[newSeason] = {}
							db.setChanged()
							wx.CallAfter( self.refresh )
						else:
							Utils.MessageOK( self, 'Season ' + newSeason +' already exists!', title = 'Season exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
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
			self.refreshSeasonsGrid()
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
			self.editRacesButton.Disable()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
			
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
			evtName = list(season)[row]
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
			print('add event')
			with wx.TextEntryDialog(self, 'Enter the name for the new event:', caption='Add event', value='New Event', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newEvent = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						if newEvent not in season:
							season[newEvent] = {}
							db.setChanged()
							wx.CallAfter( self.refresh )
						else:
							Utils.MessageOK( self, 'Event ' + newEvent +' already exists!', title = 'Event exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
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
					del season[event]
					db.setChanged()
					self.evt = None
					self.rnd = None
					wx.CallAfter( self.refresh )
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
			
	def selectRnd( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.rnd = row
			self.refreshCurrentSelection()
			self.editRacesButton.Enable()
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
			evtName = list(season)[self.evt]
			evt = season[evtName]
			rndName = list(evt)[row]
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
			print('add event')
			with wx.TextEntryDialog(self, 'Enter the name for the new round:', caption='Add round', value='New Round', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newRound = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season)[self.evt]
						evt = season[evtName]
						print('season: ' + seasonName + ', event: ' + evtName + ', rounds: ' + str(evt))
						if newRound not in evt:
							evt[newRound] = {}
							db.setChanged()
							wx.CallAfter( self.refresh )
						else:
							Utils.MessageOK( self, 'Round ' + newRound +' already exists!', title = 'Round exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
						
	def deleteRound( self, event, row ):
		database = Model.database
		if database is None:
			return
		seasonName = database.getSeasonsList()[self.season]
		season = database.seasons[seasonName]
		evtName = list(season)[self.evt]
		evt = season[evtName]
		rndName = list(evt)[row]
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete ' + rndName + '?\nThis will also delete ALL associated races!', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete event: ' + evtName)
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season)[self.evt]
					evt = season[evtName]
					rnd = self.roundsGrid.GetCellValue(row, 0)
					del evt[rnd]
					db.setChanged()
					self.rnd = None
					wx.CallAfter( self.refresh )
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
			
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
			self.seasonsGrid.SetCellValue(row, 1, str(len(database.seasons[seasonName])))
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
			for eventName in season:
				self.eventsGrid.AppendRows(1)
				row = self.eventsGrid.GetNumberRows() -1
				self.eventsGrid.SetCellValue(row, 0, eventName )
				self.eventsGrid.SetCellValue(row, 1, str(len(season[eventName])))
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
				evtName = list(season)[self.evt]
				self.roundsGrid.SetColLabelValue(0, evtName + '\'s rounds')
				evt = season[evtName]
				#print('season: ' + seasonName + ', event: ' + evtName + ', rounds: ' + str(evt))
				for rndName in evt:
					self.roundsGrid.AppendRows(1)
					row = self.roundsGrid.GetNumberRows() -1
					self.roundsGrid.SetCellValue(row, 0, rndName)
					self.roundsGrid.SetCellValue(row, 1, str(len(evt[rndName])))
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
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			selection.append( seasonName )
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season)[self.evt]
				selection.append( evtName )
				evt = season[evtName]
				if self.rnd is not None:
					rndName = list(evt)[self.rnd]
					selection.append( rndName )
			self.currentSelection.SetLabel( ', '.join(n for n in selection) )
		else:
			self.currentSelection.SetLabel( 'None' )
		database.selection = selection
		
	
	def commit( self, event=None ):
		Utils.writeLog('Events commit: ' + str(event))
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self ):
		self.refreshSeasonsGrid()
		self.refreshEventsGrid()
		self.refreshRoundsGrid()
		self.refreshCurrentSelection()
		self.Layout()
