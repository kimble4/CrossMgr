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
	
	maxRaces = 5
	whiteColour = wx.Colour( 255, 255, 255 )
	orangeColour = wx.Colour( 255, 165, 0 )
	
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
		
		self.numberOfRaces = intctrl.IntCtrl( self, value=self.nrRaces, name='Number of races', min=0, max=RaceAllocation.maxRaces, limited=1, allow_none=1, style=wx.TE_PROCESS_ENTER )
		self.numberOfRaces.Bind( wx.EVT_TEXT_ENTER, self.onChangeNumberOfRaces )
		hs.Add (self.numberOfRaces , flag=wx.ALIGN_CENTER_VERTICAL )
		hs.AddStretchSpacer()
		# hs.Add( wx.StaticText( self, label='Select race:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		# self.raceSelection = wx.Choice( self, choices=[] )
		# self.raceSelection.Bind( wx.EVT_CHOICE, self.onSelectRace )
		# hs.Add( self.raceSelection, flag=wx.ALIGN_CENTER_VERTICAL)
		vs.Add( hs )
		
		gbs = wx.GridBagSizer(5, 5)
		for i in range(RaceAllocation.maxRaces):
			setattr(self, 'raceGridTitle' + str(i), wx.StaticText(self, label='Race ' + str(i+1)) )
			setattr(self, 'raceGrid' + str(i), wx.grid.Grid( self ) )
			getattr(self, 'raceGrid' + str(i), None).CreateGrid(0, len(self.colnames) )
			for col, name in enumerate(self.colnames):
				getattr(self, 'raceGrid' + str(i), None).SetColLabelValue(col, name)
			getattr(self, 'raceGrid' + str(i), None).HideRowLabels()
			getattr(self, 'raceGrid' + str(i), None).SetRowLabelSize( 0 )
			getattr(self, 'raceGrid' + str(i), None).SetMargins( 0, 0 )
			getattr(self, 'raceGrid' + str(i), None).AutoSizeColumns( True )
			getattr(self, 'raceGrid' + str(i), None).DisableDragColSize()
			getattr(self, 'raceGrid' + str(i), None).DisableDragRowSize()
			getattr(self, 'raceGrid' + str(i), None).EnableEditing(False)
			getattr(self, 'raceGrid' + str(i), None).SetSelectionMode(wx.grid.Grid.GridSelectRows)
			getattr(self, 'raceGrid' + str(i), None).Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, lambda event, race=i: self.onRacerRightClick(event, race) )
			# getattr(self, 'raceGrid' + str(i), None).Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onSeasonsRightClick )
			# getattr(self, 'raceGrid' + str(i), None).Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectSeason )
			gbs.Add( getattr(self, 'raceGridTitle' + str(i), None), pos=(0,i), span=(1,1), flag=wx.ALIGN_CENTRE )
			gbs.Add( getattr(self, 'raceGrid' + str(i), None), pos=(1,i), span=(1,1), flag=wx.EXPAND )
		vs.Add( gbs,  flag=wx.EXPAND )
		
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		#commit button
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		hs.Add( self.commitButton, flag=wx.ALIGN_LEFT )
		#edited warning
		self.editedWarning = wx.StaticText( self, label='' )
		hs.Add( self.editedWarning, flag=wx.ALIGN_CENTER_VERTICAL )
		
		vs.Add( hs, flag=wx.EXPAND)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onRacerRightClick( self, event, race ):
		row = event.GetRow()
		col = event.GetCol()
		try:
			bib = int(getattr(self, 'raceGrid' + str(race), None).GetCellValue(row, 0))
			name = getattr(self, 'raceGrid' + str(race), None).GetCellValue(row, 1)
		except:
			return
		menu = wx.Menu()
		menu.SetTitle('#' + str(bib) + ' ' + name)
		if race < self.nrRaces - 1:
			right = menu.Append( wx.ID_ANY, 'Move to next', 'Move rider to next race...' )
			self.Bind( wx.EVT_MENU, lambda event: self.moveRacerToNextRace(event, bib, race), right )
		if race > 0:
			left = menu.Append( wx.ID_ANY, 'Move to previous', 'Move rider to previous race...' )
			self.Bind( wx.EVT_MENU, lambda event: self.moveRacerToPreviousRace(event, bib, race), left )
		editMachine = menu.Append( wx.ID_ANY, 'Change machine', 'Change machine for this race only...' )
		self.Bind( wx.EVT_MENU, lambda event: self.editRacerMachine(event, bib, race), editMachine )
		editCategories = menu.Append( wx.ID_ANY, 'Change categories', 'Change categories for this race only...' )
		self.Bind( wx.EVT_MENU, lambda event: self.editRacerCategories(event, bib, race), editCategories )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def moveRacerToNextRace( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd[iRace]
					newRace = rnd[iRace+1]
					for bibMachineCategories in sorted(race):
						if bibMachineCategories[0] == bib:
							race.remove(bibMachineCategories)
							newRace.append(bibMachineCategories)
							db.setChanged()
							break
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def moveRacerToPreviousRace( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd[iRace]
					newRace = rnd[iRace-1]
					for bibMachineCategories in sorted(race):
						if bibMachineCategories[0] == bib:
							race.remove(bibMachineCategories)
							newRace.append(bibMachineCategories)
							db.setChanged()
							break
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def editRacerMachine( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd[iRace]
					rider = database.getRider(bib)
					machineChoices = ['[Enter New]']
					if 'Machines' in rider:
						for machineCategories in rider['Machines']:
							machineChoices.append(machineCategories[0])
					with wx.SingleChoiceDialog(self, 'Select machine for #' + str(bib) + ' ' + database.getRiderName(bib, True) + ' in race ' + str(iRace+1), 'Change machine', machineChoices ) as dlg:
						if dlg.ShowModal() == wx.ID_OK:
							if dlg.GetSelection() == 0: #enter new
								with wx.TextEntryDialog(self, 'Enter the name for the new machine:', caption='Change machine', value='', style=wx.OK|wx.CANCEL) as entryDlg:
									if entryDlg.ShowModal() == wx.ID_OK:
										newMachine = entryDlg.GetValue()
										if 'Machines' not in db.riders[bib]:
											db.riders[bib]['Machines'] = []
										found = False
										for machineCategories in db.riders[bib]['Machines']:
											if newMachine == machineCategories[0]:
												found = True
												break
										if not found:
											db.riders[bib]['Machines'].append((newMachine, []))
									else:
										return
							else: #selected from list
								newMachine = dlg.GetStringSelection()
							for bibMachineCategories in race:
								if bibMachineCategories[0] == bib:
									race.remove(bibMachineCategories)
									race.append([bibMachineCategories[0], newMachine, bibMachineCategories[2]])
									db.setChanged()
									print(race)
									break
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def editRacerCategories( self, event, bib, iRace ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.rnd]
					rnd = evt['rounds'][rndName]
					race = rnd[iRace]
					rider = database.getRider(bib)
					evtRacersDict = {}
					if 'racers' in evt:
						for bibMachineCategories in evt['racers']:
							evtRacersDict[bibMachineCategories[0]] = (bibMachineCategories[1], bibMachineCategories[2])
					editCategories = None
					for bibMachineCategories in race:
						if bibMachineCategories[0] == bib:
							editedCategories = bibMachineCategories[2]
					catChoices = []
					catSelectedOrig = []
					catSelected = []
					#get the original categories for the event
					if 'categories' in season:
						if season['categories']:  
							iCategory = 0
							for categoryAbbrev in season['categories']:
								catChanged = False
								catChoices.append(categoryAbbrev[0])
								#check for previous change
								if editedCategories is not None:
									if categoryAbbrev[0] in editedCategories:
										catSelected.append(iCategory)
										catChanged = True
								# use the event category
								if categoryAbbrev[0] in evtRacersDict[bib][1]:
									catSelectedOrig.append(iCategory)
									if not catChanged:
										catSelected.append(iCategory)
								iCategory += 1
						with wx.MultiChoiceDialog(self, 'Select categories', 'Change categories', catChoices) as dlg:
							dlg.SetSelections(catSelected)
							if dlg.ShowModal() == wx.ID_OK:
								newSelections = dlg.GetSelections()
								if newSelections == catSelected:
									Utils.writeLog('editRacerCategories: No change to #' + str(bib) + '\'s categories')
									return
								if newSelections == catSelectedOrig:
									Utils.writeLog('editRacerCategories: Reverting #' + str(bib) + '\'s categories to event default')
									for bibMachineCategories in race:
										if bibMachineCategories[0] == bib:
											race.remove(bibMachineCategories)
											race.append([bibMachineCategories[0], bibMachineCategories[1], None])
											db.setChanged()
											self.refreshRaceTables()
									return
								iChoice = 0
								selectedCategories = []
								for category in catChoices:
									if iChoice in newSelections:
										selectedCategories.append(category)
									iChoice += 1
								for bibMachineCategories in race:
									if bibMachineCategories[0] == bib:
										race.remove(bibMachineCategories)
										race.append([bibMachineCategories[0], bibMachineCategories[1], selectedCategories])
										db.setChanged()
										break
				self.refreshRaceTables()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
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
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						rndName = list(evt['rounds'])[self.rnd]
						rnd = evt['rounds'][rndName]
						curLen = len(rnd)
						if curLen < self.nrRaces:
							for i in range(self.nrRaces - curLen):
								rnd.append([])
						elif curLen > self.nrRaces:
							for i in range(curLen - self.nrRaces):
								rnd.pop()
						db.setChanged()
					self.refreshRaceTables()
				except Exception as e:
					Utils.logException( e, sys.exc_info() )
			self.refreshNumberOfRaces()
			
	def refreshRaceTables( self ):
		for i in range(RaceAllocation.maxRaces):
			self.clearGrid( getattr(self, 'raceGrid' + str(i), None) )
		database = Model.database
		if database is None:
			return
		try:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			evt = season['events'][evtName]
			rndName = list(evt['rounds'])[self.rnd]
			rnd = evt['rounds'][rndName]
			evtRacersDict = {}
			if 'racers' in evt:
				for bibMachineCategories in evt['racers']:
					evtRacersDict[bibMachineCategories[0]] = (bibMachineCategories[1], bibMachineCategories[2])
			iRace = 0
			allocatedBibs = []
			for race in rnd:
				#print(race)
				for bibMachineCategories in sorted(race):
					eventsMachineCategories = evtRacersDict[bibMachineCategories[0]]
					getattr(self, 'raceGrid' + str(iRace), None).AppendRows(1)
					row = getattr(self, 'raceGrid' + str(iRace), None).GetNumberRows() -1
					col = 0
					getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(bibMachineCategories[0]))
					getattr(self, 'raceGrid' + str(iRace), None).SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
					col += 1
					getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, database.getRiderName(bibMachineCategories[0]) )
					col += 1
					if bibMachineCategories[1] is None:
						# machine has not been changed from event default
						getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(eventsMachineCategories[0]))
						getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.whiteColour)
					else:
						getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, str(bibMachineCategories[1]))
						getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.orangeColour)
					col += 1
					if bibMachineCategories[2] is None:
						# categories have not been changed from event default
						getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, ','.join(self.getAbbreviatedCategory(c) for c in eventsMachineCategories[1]))
						getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.whiteColour)
					else:
						getattr(self, 'raceGrid' + str(iRace), None).SetCellValue(row, col, ','.join(self.getAbbreviatedCategory(c) for c in bibMachineCategories[2]))
						getattr(self, 'raceGrid' + str(iRace), None).SetCellBackgroundColour(row, col, self.orangeColour)
					allocatedBibs.append(bibMachineCategories[0])
				getattr(self, 'raceGrid' + str(iRace), None).AutoSize()
				iRace += 1
			# add all unallocated bibs to first race
			unallocatedRiders = False
			if 'racers' in evt:
				for bibMachineCategories in sorted(evt['racers']):
					if bibMachineCategories[0] not in allocatedBibs:
						self.raceGrid0.AppendRows(1)
						row = self.raceGrid0.GetNumberRows() -1
						col = 0
						self.raceGrid0.SetCellValue(row, col, str(bibMachineCategories[0]))
						self.raceGrid0.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
						col += 1
						self.raceGrid0.SetCellValue(row, col, database.getRiderName(bibMachineCategories[0]) )
						col += 1
						self.raceGrid0.SetCellValue(row, col, str(bibMachineCategories[1]))
						col += 1
						self.raceGrid0.SetCellValue(row, col, ','.join(self.getAbbreviatedCategory(c) for c in bibMachineCategories[2]))
						unallocatedRiders = True
				self.raceGrid0.AutoSize()
			if unallocatedRiders:
				self.editedWarning.SetLabel('Edited!')
			self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		
	def refreshNumberOfRaces( self ):
		self.numberOfRaces.SetValue(self.nrRaces)
		for i in range(self.nrRaces):
			getattr(self, 'raceGrid' + str(i), None).Show()
			getattr(self, 'raceGridTitle' + str(i), None).Show()
		for i in range(self.nrRaces, RaceAllocation.maxRaces):
			getattr(self, 'raceGrid' + str(i), None).Hide()
			getattr(self, 'raceGridTitle' + str(i), None).Hide()
		self.Layout()
		
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
			evtName = list(season['events'])[self.evt]
			selection.append( evtName )
			evt = season['events'][evtName]
			rndName = list(evt['rounds'])[self.rnd]
			selection.append( rndName )
			title = ', '.join(n for n in selection)
		self.currentSelection.SetLabel( title )
		database.selection = selection
		
	def getAbbreviatedCategory( self, categoryName ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				catCount = 0
				if 'categories' in season:
					for categoryAbbrev in season['categories']:
						if categoryName.lower() == categoryAbbrev[0].lower():
							return categoryAbbrev[1]
		return ''
		
	def clearGrid( self, grid ):
		if grid is None:
			return
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )

	def commit( self, event=None ):
		Utils.writeLog('RaceAllocation commit: ' + str(event))
		database = Model.database
		if database is None:
			return
		try:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[self.season]
				season = db.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				rnd.clear()
				for i in range(self.nrRaces):
					racers = []
					for row in range(getattr(self, 'raceGrid' + str(i), None).GetNumberRows()):
						racers.append((int(getattr(self, 'raceGrid' + str(i), None).GetCellValue(row, 0)), None, None))
					rnd.append(racers)
				db.setChanged()
			self.editedWarning.SetLabel('')
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
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
			self.refreshCurrentSelection()
			#number of races
			if self.season is not None and self.evt is not None and self.rnd is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				self.nrRaces = len(rnd)
				self.numberOfRaces.ChangeValue(self.nrRaces)
				self.refreshNumberOfRaces()
				self.refreshRaceTables()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			self.nrRaces = 0
		self.Layout()
