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
import wx.lib.intctrl as intctrl


class Teams( wx.Panel ):
	
	maxCategories = 18
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		bigFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		#bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		self.season = None

		self.colnames = ['Team', 'Abbreviation', 'Last Entered']
		
		self.riderBibNames = []
		
		vs = wx.BoxSizer(wx.VERTICAL)
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.deleteAllButton = wx.Button( self, label='Delete All')
		self.deleteAllButton.SetToolTip( wx.ToolTip('Delete all teams'))
		self.Bind( wx.EVT_BUTTON, self.deleteAll, self.deleteAllButton )
		hs.Add( self.deleteAllButton )
		self.newTeamButton = wx.Button( self, label='Add New')
		self.newTeamButton.SetToolTip( wx.ToolTip('Add a new team'))
		self.Bind( wx.EVT_BUTTON, self.addTeam, self.newTeamButton )
		hs.Add( self.newTeamButton )
		vs.Add( hs, flag=wx.EXPAND)
		
		self.teamsGrid = wx.grid.Grid( self )
		self.teamsGrid.CreateGrid(0, len(self.colnames) )
		for i, name in enumerate(self.colnames):
			self.teamsGrid.SetColLabelValue(i, name)
		self.teamsGrid.HideRowLabels()
		self.teamsGrid.SetRowLabelSize( 0 )
		self.teamsGrid.SetMargins( 0, 0 )
		self.teamsGrid.AutoSizeColumns( True )
		self.teamsGrid.DisableDragColSize()
		self.teamsGrid.DisableDragRowSize()
		self.teamsGrid.EnableEditing(True)
		self.teamsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.teamsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onTeamsRightClick )
		# self.teamsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onCategoriesRightClick )
		self.teamsGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onTeamsEdited )
		vs.Add( self.teamsGrid, flag=wx.EXPAND )
		
		vs.AddStretchSpacer()
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		
		#commit button
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Stores changes (Ctrl-O)'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		hs.Add( self.commitButton, flag=wx.ALIGN_LEFT )
		
		#edited warning
		self.editedWarning = wx.StaticText( self, label='' )
		hs.Add( self.editedWarning, flag=wx.ALIGN_LEFT )
		
		vs.Add( hs, flag=wx.EXPAND)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onTeamsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Teams')
		if row >= 1 or (row == 0 and len(self.teamsGrid.GetCellValue(row, 0).strip()) > 0):
			delete = menu.Append( wx.ID_ANY, 'Delete ' + self.teamsGrid.GetCellValue(row, 0) + ' from list', 'Delete this team...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteTeam(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def onTeamsEdited( self, event=None ):
		row = event.GetRow()
		col = event.GetCol()
		database = Model.database
		if col == 2:
			if database is not None:
				self.teamsGrid.SetCellValue(row, col, '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(database.teams[row][2])) if database.teams[row][2] is not None else '')
			else:
				self.teamsGrid.SetCellValue(row, col, '')
		else:
			self.editedWarning.SetLabel('Edited!')
		
	def deleteAll( self, event):
		self.clearGrid( self.teamsGrid )
		self.teamsGrid.AutoSize()
		self.editedWarning.SetLabel('Edited!')
		self.Layout()
		
	def addTeam( self, event ):
		self.teamsGrid.AppendRows(1)
		row = self.teamsGrid.GetNumberRows() -1
		self.teamsGrid.SetCellValue(row, 0, 'New Team')
		self.teamsGrid.SetCellValue(row, 1, 'NEW')
		self.teamsGrid.SetCellAlignment(row, 1, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
		self.teamsGrid.AutoSize()
		self.editedWarning.SetLabel('Edited!')
		self.Layout()
			
	def deleteTeam( self, event, row ):
		self.teamsGrid.DeleteRows(row, 1)
		self.teamsGrid.AutoSize()
		self.editedWarning.SetLabel('Edited!')
		self.Layout()
		
	def refreshTeamsList( self ):
		self.clearGrid( self.teamsGrid )
		database = Model.database
		if database is None:
			return
		for teamAbbrevEntered in database.teams:
			self.teamsGrid.AppendRows(1)
			row = self.teamsGrid.GetNumberRows() -1
			col = 0
			self.teamsGrid.SetCellValue(row, col, teamAbbrevEntered[0])
			col += 1
			self.teamsGrid.SetCellValue(row, col, teamAbbrevEntered[1])
			self.teamsGrid.SetCellAlignment(row, col, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
			col += 1
			self.teamsGrid.SetCellValue(row, col, '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(teamAbbrevEntered[2])) if teamAbbrevEntered[2] is not None else '')
			self.teamsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
		self.teamsGrid.AutoSize()
		self.editedWarning.SetLabel('')
		
	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )
	
	def commit( self, event=None ):
		Utils.writeLog('Teams commit: ' + str(event))
		if event: #called by button
			database = Model.database
			if database is None:
				return
			try:
				with Model.LockDatabase() as db:
					db.teams.clear()
					for row in range(self.teamsGrid.GetNumberRows()):
						db.teams.append([self.teamsGrid.GetCellValue(row, 0), self.teamsGrid.GetCellValue(row, 1), None])
					db.setChanged()
					wx.CallAfter( self.refresh )
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				wx.CallAfter( self.refresh )
	
	def refresh( self ):
		Utils.writeLog('Teams refresh')
		database = Model.database
		if database is None:
			return
		self.refreshTeamsList()
		self.Layout()
