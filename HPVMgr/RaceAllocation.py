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


class RaceAllocation( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.season = None
		self.evt = None
		self.rnd = None
		self.race = 0
		self.nrRaces = 0
		self.colnames = ['Bib', 'Name', 'Machine', 'Categories']
		
		self.riderBibNames = []
		
		vs = wx.BoxSizer(wx.VERTICAL)
		self.currentSelection = wx.StaticText( self, label='No round selected' )
		vs.Add( self.currentSelection )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( wx.StaticText( self, label='Number of races in this round:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		
		self.numberOfRaces = intctrl.IntCtrl( self, value=self.nrRaces, name='Number of races', min=0, max=5, limited=1, allow_none=1, style=wx.TE_PROCESS_ENTER )
		self.numberOfRaces.Bind( wx.EVT_TEXT_ENTER, self.onChangeNumberOfRaces )
		hs.Add (self.numberOfRaces , flag=wx.ALIGN_CENTER_VERTICAL )
		hs.AddStretchSpacer()
		# hs.Add( wx.StaticText( self, label='Select race:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		# self.raceSelection = wx.Choice( self, choices=[] )
		# self.raceSelection.Bind( wx.EVT_CHOICE, self.onSelectRace )
		# hs.Add( self.raceSelection, flag=wx.ALIGN_CENTER_VERTICAL)
		vs.Add( hs )
		
		self.racersGrid = wx.grid.Grid( self )
		self.racersGrid.CreateGrid(0, len(self.colnames) )
		for i, name in enumerate(self.colnames):
			self.racersGrid.SetColLabelValue(i, name)
		self.racersGrid.HideRowLabels()
		self.racersGrid.SetRowLabelSize( 0 )
		self.racersGrid.SetMargins( 0, 0 )
		self.racersGrid.AutoSizeColumns( True )
		self.racersGrid.DisableDragColSize()
		self.racersGrid.DisableDragRowSize()
		self.racersGrid.EnableEditing(False)
		self.racersGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		# self.racersGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onSeasonsRightClick )
		# self.racersGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onSeasonsRightClick )
		# self.racersGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectSeason )
		vs.Add( self.racersGrid, flag=wx.EXPAND )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onChangeNumberOfRaces( self, event ):
		database = Model.database
		if database is None:
			return
		if self.numberOfRaces.GetValue() != self.nrRaces:
			if not Utils.MessageOKCancel( self, 'Are you sure you want to change the number of races?\nExisting race allocations will be lost!', title='Change number of races', iconMask=wx.ICON_QUESTION):
				self.numberOfRaces.SetValue(self.nrRaces)
				return
			self.nrRaces = self.numberOfRaces.GetValue()
			if self.season is not None and self.evt is not None and self.rnd is not None:
				try:
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season)[self.evt]
						evt = season[evtName]
						rndName = list(evt['rounds'])[self.rnd]
						races = evt['rounds'][rndName]
						curLen = len(races)
						if curLen < self.nrRaces:
							for i in range(self.nrRaces - curLen):
								races.append({})
						elif curLen > self.nrRaces:
							for i in range(curLen - self.nrRaces):
								races.pop()
						print( races )
				except Exception as e:
					Utils.logException( e, sys.exc_info() )
			self.refreshNumberOfRaces()
			
	def refreshNumberOfRaces( self ):
		self.numberOfRaces.SetValue(self.nrRaces)
		self.raceSelection.Clear()
		self.raceSelection.AppendItems( list(map(str, list(range(1, self.numberOfRaces.GetValue() + 1)))) )
		if self.race > self.numberOfRaces.GetValue():
			self.race = 0
		self.raceSelection.SetSelection(self.race)
		
	def onSelectRace( self, event ):
		self.race = self.raceSelection.GetSelection()
		print('race is now ' + str(self.race))
		
	def onSelectBib( self, event ):
		database = Model.database
		if database is None:
			return
		iBib = self.riderBibEntry.GetSelection()
		bib = sorted([bibName[0] for bibName in self.riderBibNames])[iBib]
		riderName = dict(self.riderBibNames)[bib]
		self.riderNameEntry.ChangeValue( riderName )
		
	def onEnterRiderName( self, event ):
		name = re.sub("[^a-z ]", "", self.riderNameEntry.GetValue().lower())
		sortedBibNames = sorted([bibName[0] for bibName in self.riderBibNames])
		for bibName in self.riderBibNames:
			if name == re.sub("[^a-z ]", "", bibName[1].lower()):
				iBib = sortedBibNames.index(bibName[0])
				self.riderBibEntry.SetSelection(iBib)
				self.riderNameEntry.ChangeValue( bibName[1] )
				return
		self.riderBibEntry.SetSelection(wx.NOT_FOUND)
		
	
		
	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )

	def commit( self, event=None ):
		Utils.writeLog('RaceAllocation commit: ' + str(event))
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self ):
		Utils.writeLog('RaceAllocation refresh')
		database = Model.database
		if database is None:
			return
		try:
			#get current selection
			self.season = database.curSeason
			self.evt = database.curEvt
			self.rnd = database.curRnd
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		self.Layout()
