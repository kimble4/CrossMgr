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
		
		self.season = ''
		self.event = ''
		self.rnd = ''
		
		labelAlign = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
		vs = wx.BoxSizer(wx.VERTICAL)
		gbs = wx.GridBagSizer(5, 5)
		row = 0
		
		#seasons list
		self.seasonsGrid = wx.grid.Grid( self )
		self.seasonsGrid.CreateGrid(0, 1)
		self.seasonsGrid.SetColLabelValue(0, 'Seasons')
		self.seasonsGrid.HideRowLabels()
		#self.seasonsGrid.AutoSize()
		self.seasonsGrid.SetRowLabelSize( 0 )
		self.seasonsGrid.SetMargins( 0, 0 )
		self.seasonsGrid.AutoSizeColumns( True )
		self.seasonsGrid.DisableDragColSize()
		self.seasonsGrid.DisableDragRowSize()
		self.seasonsGrid.EnableEditing(True)
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onSeasonsRightClick )
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onSeasonsRightClick )
		# self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onEdited )
		#self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onDoubleClick )
		#self.seasonsGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		# put a tooltip on the cells in a column
		#self.labelGrid.GetGridWindow().Bind(wx.EVT_MOTION, self.onMouseOver)
		gbs.Add( self.seasonsGrid, pos=(row,0), span=(1,1), flag=wx.EXPAND )
		
		row += 1
		
		#commit button
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		gbs.Add( self.commitButton, pos=(row,0), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		row = 0
		
		#events list
		self.eventsGrid = wx.grid.Grid( self )
		self.eventsGrid.CreateGrid(0, 1)
		self.eventsGrid.SetColLabelValue(0, 'Season\'s events')
		self.eventsGrid.HideRowLabels()
		#self.eventsGrid.AutoSize()
		self.eventsGrid.SetRowLabelSize( 0 )
		self.eventsGrid.SetMargins( 0, 0 )
		self.eventsGrid.AutoSizeColumns( True )
		self.eventsGrid.DisableDragColSize()
		self.eventsGrid.DisableDragRowSize()
		self.eventsGrid.EnableEditing(True)
		# self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.oneventsRightClick )
		# self.eventsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.oneventsRightClick )
		# self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onEdited )
		#self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onDoubleClick )
		#self.eventsGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		# put a tooltip on the cells in a column
		#self.labelGrid.GetGridWindow().Bind(wx.EVT_MOTION, self.onMouseOver)
		gbs.Add( self.eventsGrid, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		row = 0
		#rounds list
		self.roundsGrid = wx.grid.Grid( self )
		self.roundsGrid.CreateGrid(0, 1)
		self.roundsGrid.SetColLabelValue(0, 'Event\'s Rounds')
		self.roundsGrid.HideRowLabels()
		#self.roundsGrid.AutoSize()
		self.roundsGrid.SetRowLabelSize( 0 )
		self.roundsGrid.SetMargins( 0, 0 )
		self.roundsGrid.AutoSizeColumns( True )
		self.roundsGrid.DisableDragColSize()
		self.roundsGrid.DisableDragRowSize()
		self.roundsGrid.EnableEditing(True)
		# self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onroundsRightClick )
		# self.roundsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onroundsRightClick )
		# self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onEdited )
		#self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onDoubleClick )
		#self.roundsGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		# put a tooltip on the cells in a column
		#self.labelGrid.GetGridWindow().Bind(wx.EVT_MOTION, self.onMouseOver)
		gbs.Add( self.roundsGrid, pos=(row,2), span=(1,1), flag=wx.EXPAND )
		
		
		
		vs.Add( gbs )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
		
	def onSeasonsRightClick( self, event ):
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Seasons')
		add = menu.Append( wx.ID_ANY, 'Add new season', 'Add a new season...' )
		self.Bind( wx.EVT_MENU, self.addSeason, add )
		if row >= 1 or (row == 0 and len(self.seasonsGrid.GetCellValue(row, 0).strip()) > 0):
			delete = menu.Append( wx.ID_ANY, 'Delete season from list', 'Delete this season...' )
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
			# self.bib = self.riderBib.GetValue()
			# bib = int(self.bib)
			# with Model.LockDatabase() as db:
			# 	rider = db.getRider(bib)
			# 	del rider['Machines'][row]
			# 	db.setChanged()
			# self.refreshMachinesGrid()
			self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def refreshSeasonsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.seasonsGrid )
		seasons = list(map(str, database.getSeasons()))
		for season in seasons:
			self.seasonsGrid.AppendRows(1)
			row = self.seasonsGrid.GetNumberRows() -1
			self.seasonsGrid.SetCellValue(row, 0, str(season))
		if self.seasonsGrid.GetNumberRows() == 0:
			self.seasonsGrid.AppendRows(1)
		else:
			#select current seasons
			pass
	
	def refreshEventsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.eventsGrid )
		if self.season:
			events = list(map(str, database.getEvents(self.season)))
			for event in events:
				self.eventsGrid.AppendRows(1)
				row = self.eventsGrid.GetNumberRows() -1
				self.eventsGrid.SetCellValue(row, 0, str(season))
		if self.seasonsGrid.GetNumberRows() == 0:
			self.seasonsGrid.AppendRows(1)
			
	def refreshRoundsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.roundsGrid )
		if self.rnd:
			rounds = list(map(str, database.getRounds(self.event)))
			for rnd in rounds:
				self.roundsGrid.AppendRows(1)
				row = self.roundsGrid.GetNumberRows() -1
				self.roundsGrid.SetCellValue(row, 0, str(rnd))
		if self.roundsGrid.GetNumberRows() == 0:
			self.roundsGrid.AppendRows(1)
	

	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )
	
	def commit( self, event=None ):
		Utils.writeLog('Events commit: ' + str(event))
		pass
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self ):
		self.refreshSeasonsGrid()
		self.refreshEventsGrid()
		self.refreshRoundsGrid()
		self.Layout()
