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
		self.nrRaces = 1
		self.colnames = ['Bib', 'Name', 'Machine', 'Categories']
		
		self.riderBibNames = []
		
		labelAlign = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
		vs = wx.BoxSizer(wx.VERTICAL)
		self.currentSelection = wx.StaticText( self, label='No round selected' )
		vs.Add( self.currentSelection )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( wx.StaticText( self, label='Number of races in this round:' ) )
		
		self.numberOfRaces = intctrl.IntCtrl( self, value=self.nrRaces, name='Number of races', min=1, max=255, limited=1, allow_none=1, style=wx.TE_PROCESS_ENTER )
		self.numberOfRaces.Bind( wx.EVT_TEXT_ENTER, self.onChangeNumberOfRaces )
		hs.Add (self.numberOfRaces )
		hs.AddStretchSpacer()
		hs.Add( wx.StaticText( self, label='Select race:' ) )
		self.raceSelection = wx.Choice( self, choices=[] )
		self.raceSelection.Bind( wx.EVT_CHOICE, self.onSelectRace )
		hs.Add( self.raceSelection )
		vs.Add( hs )
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( wx.StaticText( self, label='Bib:' ) )
		self.riderBibEntry = wx.Choice( self, choices=[] )
		#self.riderBibEntry.Bind( wx.EVT_CHOICE, self.onSelectBib )
		hs.Add( self.riderBibEntry )
		hs.Add( wx.StaticText( self, label='Name:' ) )
		self.riderNameEntry = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_LEFT, size=(300,-1))
		self.riderNameEntry.SetValue( '' )
		self.riderNameEntry.Bind( wx.EVT_TEXT_ENTER, self.onEnterRider )
		hs.Add (self.riderNameEntry )
		
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
					seasonName = database.getSeasonsList()[self.season]
					season = database.seasons[seasonName]
					evtName = list(season)[self.evt]
					evt = season[evtName]
					rndName = list(evt['rounds'])[self.rnd]
					races = evt['rounds'][rndName]
					curLen = len(races)
					if curLen < self.nrRaces:
						for i in range(self.nrRaces - curLen):
							races.append(None)
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
		
	def onEnterRider( self, event ):
		
		pass
		
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
			riders = database.getRiders()
			firstNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['FirstName'], reverse=False))
			sortedRiders = dict(sorted(firstNameSortedRiders.items(), key=lambda item: item[1]['LastName'], reverse=False))
			self.riderBibNames.clear()
			for bib in sortedRiders:
				rider = riders[bib]
				name = ', '.join( n for n in [rider['LastName'], rider['FirstName']] if n )
				if name:
					self.riderBibNames.append((bib, name))
			self.riderNameEntry.AutoComplete(riderNameCompleter([bibName[1] for bibName in self.riderBibNames]))
			#self.riderNameEntry.AutoComplete(riderNameCompleter([bibName[1] + ' (' + str(bibName[0]) + ')' for bibName in self.riderBibNames]))
			bibs = list(map(str, database.getBibs()))
			self.riderBibEntry.Clear()
			self.riderBibEntry.AppendItems( bibs )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		self.Layout()
