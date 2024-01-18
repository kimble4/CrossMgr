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


def keys2int(x):
    if isinstance(x, dict):
        return {int(k):v for k,v in x.items()}
    return x

class riderNameCompleter(wx.TextCompleter):
    def __init__(self, riderNames):
        wx.TextCompleter.__init__(self)
        self._iLastReturned = wx.NOT_FOUND
        self._sPrefix = ''
        self.riderNames = riderNames

    def Start(self, prefix):
        self._sPrefix = prefix.lower()
        self._iLastReturned = wx.NOT_FOUND
        for item in self.riderNames:
            if item.lower().startswith(self._sPrefix):
                return True
        return False

    def GetNext(self):
        for i in range(self._iLastReturned+1, len(self.riderNames)):
            if self.riderNames[i].lower().startswith(self._sPrefix):
                self._iLastReturned = i
                return self.riderNames[i]
        return ''

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
		
		self.numberOfRaces = intctrl.IntCtrl( self, value=self.nrRaces, name='Number of races', min=0, max=255, limited=1, allow_none=1, style=wx.TE_PROCESS_ENTER )
		self.numberOfRaces.Bind( wx.EVT_TEXT_ENTER, self.onChangeNumberOfRaces )
		hs.Add (self.numberOfRaces , flag=wx.ALIGN_CENTER_VERTICAL )
		hs.AddStretchSpacer()
		hs.Add( wx.StaticText( self, label='Select race:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		self.raceSelection = wx.Choice( self, choices=[] )
		self.raceSelection.Bind( wx.EVT_CHOICE, self.onSelectRace )
		hs.Add( self.raceSelection, flag=wx.ALIGN_CENTER_VERTICAL)
		vs.Add( hs )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( wx.StaticText( self, label='Bib:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		self.riderBibEntry = wx.Choice( self, choices=[] )
		self.riderBibEntry.Bind( wx.EVT_CHOICE, self.onSelectBib )
		hs.Add( self.riderBibEntry, flag=wx.ALIGN_CENTER_VERTICAL )
		hs.Add( wx.StaticText( self, label='Name:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		self.riderNameEntry = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_LEFT, size=(300,-1))
		self.riderNameEntry.SetValue( '' )
		self.riderNameEntry.Bind( wx.EVT_TEXT, self.onEnterRiderName )
		hs.Add (self.riderNameEntry, flag=wx.ALIGN_CENTER_VERTICAL )
		self.addToRaceButton = wx.Button( self, label='Add to race')
		self.addToRaceButton.SetToolTip( wx.ToolTip('Add rider to race'))
		self.Bind( wx.EVT_BUTTON, self.onAddToRaceButton, self.addToRaceButton )
		hs.Add( self.addToRaceButton, flag=wx.ALIGN_CENTER_VERTICAL )
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
		
	def onAddToRaceButton( self, event ):
		database = Model.database
		if database is None:
			return
		iBib = self.riderBibEntry.GetSelection()
		bib = sorted([bibName[0] for bibName in self.riderBibNames])[iBib]
		riderName = dict(self.riderBibNames)[bib]
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season)[self.evt]
					evt = season[evtName]
					rndName = list(evt['rounds'])[self.rnd]
					races = evt['rounds'][rndName]
					race = races[self.race]
					if str(bib) not in race:
						race[str(bib)] = { 'machine':None, 'categories':None}
						db.setChanged()
						self.refreshRaceAllocationTable()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
					
	def refreshRaceAllocationTable( self ):
		self.clearGrid(self.racersGrid)
		database = Model.database
		if database is None:
			return
		iBib = self.riderBibEntry.GetSelection()
		bib = sorted([bibName[0] for bibName in self.riderBibNames])[iBib]
		riderName = dict(self.riderBibNames)[bib]
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season)[self.evt]
				evt = season[evtName]
				rndName = list(evt['rounds'])[self.rnd]
				races = evt['rounds'][rndName]
				race = races[self.race]
				for bibStr in race:
					bib = int(bibStr)
					rider = database.getRider(bib)
					self.racersGrid.AppendRows(1)
					row = self.racersGrid.GetNumberRows() -1
					col = 0
					self.racersGrid.SetCellValue(row, col, bibStr)
					self.racersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
					col += 1
					self.racersGrid.SetCellValue(row, col, database.getRiderName(bib))
					col += 1
					if 'machine' in race[bibStr]:
						if race[bibStr]['machine'] is not None:
							self.racersGrid.SetCellValue(row, col, race[bibStr]['machine'])
						else:
							self.racersGrid.SetCellValue(row, col, '[UNSET]')
					col += 1
					# fixme categories
					
				self.racersGrid.AutoSize()
				self.Layout()
			except Exception as e:
				pass
				#Utils.logException( e, sys.exc_info() )		

	def refreshCurrentSelection( self ):
		database = Model.database
		if database is None:
			return
		selection = []
		title = 'No round selected'
		if self.season is not None and self.evt is not None and self.rnd is not None:
			seasonName = database.getSeasonsList()[self.season]
			selection.append( seasonName )
			season = database.seasons[seasonName]
			evtName = list(season)[self.evt]
			selection.append( evtName )
			evt = season[evtName]
			if 'rounds' in evt:
				rndName = list(evt['rounds'])[self.rnd]
				selection.append( rndName )
			title = ', '.join(n for n in selection)
		self.currentSelection.SetLabel( title )
		database.selection = selection
		
	def updateSelection( self, season, evt, rnd ):
		self.season = season
		self.evt = evt
		self.rnd = rnd
		database = Model.database
		if database is None:
			self.nrRaces = 0
			return
		nrRaces = 0
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season)[self.evt]
				evt = season[evtName]
				rndName = list(evt['rounds'])[self.rnd]
				races = evt['rounds'][rndName]
				nrRaces = len(races)
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		self.nrRaces = nrRaces
		
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
		print('RaceAllocation refresh')
		self.refreshCurrentSelection()
		self.refreshNumberOfRaces()
		database = Model.database
		if database is None:
			return
		try:
			#get the riders database, populate the bib selection drop-down and the rider name AutoComplete
			riders = database.getRiders()
			firstNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['FirstName'], reverse=False))
			sortedRiders = dict(sorted(firstNameSortedRiders.items(), key=lambda item: item[1]['LastName'], reverse=False))
			self.riderBibNames.clear()
			for bib in sortedRiders:
				rider = riders[bib]
				name = ', '.join( n for n in [rider['LastName'], rider['FirstName']] if n )
				if name:
					self.riderBibNames.append((bib, name))
			self.riderBibEntry.Clear()
			self.riderBibEntry.AppendItems( list(map(str ,sorted([bibName[0] for bibName in self.riderBibNames]))) )
			self.riderNameEntry.AutoComplete(riderNameCompleter([bibName[1] for bibName in self.riderBibNames]))
			
			#now, the allocation table
			self.refreshRaceAllocationTable()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		self.Layout()
