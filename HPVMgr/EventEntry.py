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
import Flags

bitmapCache = {}
class IOCCodeRenderer(wx.grid.GridCellRenderer):
	def getImgWidth( self, ioc, height ):
		img = Flags.GetFlagImage( ioc )
		if img:
			imgHeight = int( height * 0.8 )
			imgWidth = int( float(img.GetWidth()) / float(img.GetHeight()) * float(imgHeight) )
			padding = int(height * 0.1)
			return img, imgWidth, imgHeight, padding
		return None, 0, 0, 0

	def Draw(self, grid, attr, dc, rect, row, col, isSelected):
		text = grid.GetCellValue(row, col)

		dc.SetFont( attr.GetFont() )
		w, h = dc.GetTextExtent( text )
		
		ioc = text[:3]
		img, imgWidth, imgHeight, padding = self.getImgWidth(ioc, h)
		
		fg = attr.GetTextColour()
		bg = attr.GetBackgroundColour()
		if isSelected:
			fg, bg = bg, fg
		
		dc.SetBrush( wx.Brush(bg, wx.SOLID) )
		dc.SetPen( wx.TRANSPARENT_PEN )
		dc.DrawRectangle( rect )

		rectText = wx.Rect( rect.GetX()+padding+imgWidth, rect.GetY(), rect.GetWidth()-padding-imgWidth, rect.GetHeight() )
		
		hAlign, vAlign = attr.GetAlignment()
		dc.SetTextForeground( fg )
		dc.SetTextBackground( bg )
		grid.DrawTextRectangle(dc, text, rectText, hAlign, vAlign)

		if img:
			key = (ioc, imgHeight)
			if key not in bitmapCache:
				bitmapCache[key] = img.Scale(imgWidth, imgHeight, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
			dc.DrawBitmap( bitmapCache[key], rect.GetX(), rect.GetY()+(rect.GetHeight()-imgHeight)//2 )

	def GetBestSize(self, grid, attr, dc, row, col):
		text = grid.GetCellValue(row, col)
		dc.SetFont(attr.GetFont())
		w, h = dc.GetTextExtent( text )
		
		img, imgWidth, imgHeight, padding = self.getImgWidth(text[:3], h)
		if img:
			return wx.Size(w + imgWidth + padding, h)
		else:
			return wx.Size(w, h)

	def Clone(self):
		return IOCCodeRenderer()

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

class EventEntry( wx.Panel ):
	
	numCategories = 18
	yellowColour = wx.Colour( 255, 255, 0 )
	OrangeColour = wx.Colour( 255, 165, 0 )
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		self.season = None
		self.evt = None
		self.colnames = ['Bib', 'Name', 'Gender', 'Age', 'Nat', 'Factor', 'Machine', 'Categories', 'Team']
		
		bigFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		self.riderBibNames = []
		
		vs = wx.BoxSizer(wx.VERTICAL)
		self.currentSelection = wx.StaticText( self, label='No event selected' )
		self.currentSelection.SetFont( bigFont )
		vs.Add( self.currentSelection, flag=wx.ALIGN_CENTRE )
		
		gbs = wx.GridBagSizer(5, 5)
		
		
		gbs.Add( wx.StaticText( self, label='Name:' ), pos=(0,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		self.riderNameEntry = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_LEFT, size=(300,-1))
		self.riderNameEntry.SetValue( '' )
		self.riderNameEntry.Bind( wx.EVT_TEXT, self.onEditRiderName )
		self.riderNameEntry.Bind( wx.EVT_TEXT_ENTER, self.onEnterRiderName )
		gbs.Add( self.riderNameEntry, pos=(0,1), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		gbs.Add( wx.StaticText( self, label='Bib:' ), pos=(0,2), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		
		self.riderBibEntry = wx.ComboBox( self, value='', choices=[], name='Rider Bib', size=(100,-1), style=wx.TE_PROCESS_ENTER )
		self.riderBibEntry.Bind( wx.EVT_COMBOBOX, self.onSelectBib )
		self.riderBibEntry.Bind( wx.EVT_TEXT_ENTER, self.onSelectBib )
		gbs.Add( self.riderBibEntry, pos=(0,3), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		gbs.Add( wx.StaticText( self, label='Machine:' ), pos=(1,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		self.riderMachine = wx.ComboBox(self, value='', choices=[], name='Rider Machine', size=(300,-1), style=wx.TE_PROCESS_ENTER)
		self.riderMachine.Bind( wx.EVT_COMBOBOX, self.onSelectMachine )
		self.riderMachine.Bind( wx.EVT_TEXT_ENTER, self.onSelectMachine )
		self.riderMachine.Disable()
		gbs.Add( self.riderMachine, pos=(1,1), span=(1,1), flag=wx.EXPAND )
		gbs.Add( wx.StaticText( self, label='Team:' ), pos=(1,2), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		self.riderTeam = wx.ComboBox(self, value='', choices=[], name='Rider Team', size=(300,-1 ), style=wx.TE_PROCESS_ENTER|wx.TE_LEFT )
		self.riderTeam.Disable()
		gbs.Add( self.riderTeam, pos=(1,3), span=(1,1), flag=wx.EXPAND )
		self.categoriesLabel = wx.StaticText( self, label='Categories:' )
		gbs.Add( self.categoriesLabel, pos=(2,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		categoriesSizer = wx.GridBagSizer(2, 2)
		for i in range(EventEntry.numCategories):
			setattr(self, 'riderCategory' + str(i), wx.CheckBox(self, label='Category' + str(i) ) )
			getattr(self, 'riderCategory' + str(i), None).Bind( wx.EVT_CHECKBOX, lambda event, cat = i: self.onCategoryChanged(event, cat), getattr(self, 'riderCategory' + str(i), None) )
			getattr(self, 'riderCategory' + str(i), None).Disable()
			getattr(self, 'riderCategory' + str(i), None).Hide()
		for i in range(6):
			categoriesSizer.Add( getattr(self, 'riderCategory' + str(i), None), pos=(0,i), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		for i in range(6):
			categoriesSizer.Add( getattr(self, 'riderCategory' + str(i+6), None), pos=(1,i), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		for i in range(6):
			categoriesSizer.Add( getattr(self, 'riderCategory' + str(i+12), None), pos=(2,i), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		gbs.Add( categoriesSizer,  pos=(2,1), span=(1,3), flag=wx.EXPAND )
		
		#self.deleteAllButton = wx.Button( self, label='Delete all')
		#self.deleteAllButton.SetToolTip( wx.ToolTip('Deletes all racers from the event'))
		#self.Bind( wx.EVT_BUTTON, self.deleteAllRiders, self.deleteAllButton )
		#gbs.Add( self.deleteAllButton, pos=(3,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		self.deleteRiderButton = wx.Button( self, label='Delete racer')
		self.deleteRiderButton.SetToolTip( wx.ToolTip('Deletes currently selected racer from the event'))
		self.Bind( wx.EVT_BUTTON, self.deleteCurrentRider, self.deleteRiderButton )
		self.deleteRiderButton.Disable()
		gbs.Add( self.deleteRiderButton, pos=(3,1), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		self.addToRaceButton = wx.Button( self, label='Enter/Update racer')
		self.addToRaceButton.SetToolTip( wx.ToolTip('Adds the selected rider to the event or updates their details if already entered'))
		self.Bind( wx.EVT_BUTTON, self.onAddToRaceButton, self.addToRaceButton )
		self.addToRaceButton.Disable()
		gbs.Add( self.addToRaceButton, pos=(3,3), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		
		
		vs.Add( gbs, flag=wx.EXPAND )
		
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
		self.racersGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRacerRightClick )
		self.racersGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onRacerClick )
		self.racersGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.onLabelClick )
		vs.Add( self.racersGrid, flag=wx.EXPAND )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onSelectBib( self, event=None ):
		database = Model.database
		if database is None:
			return
		try:
			bib = int(self.riderBibEntry.GetValue())
			if not database.isRider(bib):
				if Utils.MessageOKCancel(self, 'Rider #' + str(bib) + ' does not exist.  Do you want to add them?', title='Rider does not exist'):
					mainwin = Utils.getMainWin()
					mainwin.riders.addNewRider( None, bib )
					mainwin.riderDetail.setBib(bib)
					wx.CallAfter(mainwin.showPage, mainwin.iRiderDetailPage )
				else:
					self.enableRiderControls(enable=False)
					return
			riderName = database.getRiderName(bib)
			self.enableRiderControls()
		except (ValueError, KeyError):
			bib = None
			riderName = ''
			self.enableRiderControls(enable=False)
		self.riderNameEntry.ChangeValue( riderName )
		self.updateMachinesChoices(bib)
		self.updateTeamSelection(bib)
		self.onSelectMachine()
		self.highlightBib(str(bib))
		
	def enableRiderControls( self, enable=True, clearName=True):
		if enable:
			self.riderMachine.Enable()
			self.riderTeam.Enable()
			self.deleteRiderButton.Enable()
			self.addToRaceButton.Enable()
			for i in range(EventEntry.numCategories):
				getattr(self, 'riderCategory' + str(i), None).Enable()
		else:
			self.riderMachine.Disable()
			self.riderTeam.Disable()
			self.deleteRiderButton.Disable()
			self.addToRaceButton.Disable()
			if clearName:
				self.riderNameEntry.ChangeValue( '' )
			self.riderMachine.ChangeValue( '' )
			self.riderTeam.ChangeValue( '' )
			for i in range(EventEntry.numCategories):
				getattr(self, 'riderCategory' + str(i), None).SetValue(False)
				getattr(self, 'riderCategory' + str(i), None).Disable()
	
	def onEditRiderName( self, event ):
		self.riderBibEntry.ChangeValue('')
		self.enableRiderControls(enable=False, clearName=False)
		self.updateMachinesChoices(None)
		self.updateTeamSelection(None)
		self.onSelectMachine(None)
		self.highlightBib(None)
	
	def onEnterRiderName( self, event ):
		name = re.sub("[^a-z ]", "", self.riderNameEntry.GetValue().lower())
		for bibName in self.riderBibNames:
			if name == re.sub("[^a-z ]", "", bibName[1].lower()):
				self.riderBibEntry.SetValue(str(bibName[0]))
				self.onSelectBib()
				return
		self.riderBibEntry.SetSelection(wx.NOT_FOUND)
		self.riderBibEntry.ChangeValue('')
		self.enableRiderControls(enable=False, clearName=False)
	
	def onCategoryChanged( self, event, iCat ):
		count = 0
		for i in range(EventEntry.numCategories):
			if getattr(self, 'riderCategory' + str(i), None).IsChecked():
				count += 1
		if count > 10:
			Utils.MessageOK( self, 'CrossMgr does not support more than 10 CustomCategories per rider!', 'Too many categories' )
			getattr(self, 'riderCategory' + str(iCat), None).SetValue(False)
			
	def onSelectMachine( self, event=None ):
		machine = self.riderMachine.GetValue()
		database = Model.database
		if database is None:
			return
		try:
			bib = int(self.riderBibEntry.GetValue())
			categories = []
			if not database.isRider(bib):
				return
			if 'Machines' not in database.riders[bib]:
				return
			for machineCategories in database.riders[bib]['Machines']:
				if machine == machineCategories[0]:
					categories = machineCategories[1]
					break
			if self.season is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				catCount = 0
				if 'categories' in season:
					if season['categories']:
						iCat = 0
						for categoryAbbrev in season['categories']:
							if categoryAbbrev[0] in categories:
								getattr(self, 'riderCategory' + str(iCat), None).SetValue(True)
							else:
								getattr(self, 'riderCategory' + str(iCat), None).SetValue(False)
							iCat += 1
		except ValueError: # invalid bib
			return
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
						
	def onLabelClick( self, event ):
		self.commit()
		self.refreshRaceAllocationTable()
		
	def onRacerRightClick( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		self.racersGrid.ClearSelection()
		try:
			bib = int(self.racersGrid.GetCellValue(row, 0))
			name = self.racersGrid.GetCellValue(row, 1)
		except:
			return
		menu = wx.Menu()
		menu.SetTitle('#' + str(bib) + ' ' + name)
		ed = menu.Append( wx.ID_ANY, 'Edit details', 'Edit rider details...' )
		self.Bind( wx.EVT_MENU, lambda event: self.editRiderDetails(event, bib), ed )
		delete = menu.Append( wx.ID_ANY, 'Delete racer', 'Delete this racer...' )
		self.Bind( wx.EVT_MENU, lambda event: self.deleteRider(event, bib), delete )
		deleteAll = menu.Append( wx.ID_ANY, 'Delete all racers', 'Delete all racers from the event...' )
		self.Bind( wx.EVT_MENU, lambda event: self.deleteAllRiders(event), deleteAll )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def onRacerClick( self, event ):
		row = event.GetRow()
		self.editRiderDetails( event, self.racersGrid.GetCellValue(row, 0))
			
	def editRiderDetails( self, event, bib ):
		bibStr = str(bib)
		self.highlightBib(bibStr)
		self.riderBibEntry.ChangeValue(bibStr)
		self.onSelectBib()
		
	def highlightBib( self, bibStr):
		self.racersGrid.ClearSelection()
		bibRow = -1
		for row in range(self.racersGrid.GetNumberRows()):
			if self.racersGrid.GetCellValue(row, 0) == bibStr:
				bibRow = row
				for col in range(self.racersGrid.GetNumberCols()):
					self.racersGrid.SetCellBackgroundColour(row, col, self.OrangeColour)
			else:
				for col in range(self.racersGrid.GetNumberCols()):
					self.racersGrid.SetCellBackgroundColour(row, col, wx.WHITE)
		self.racersGrid.AutoSize() #needed to make colour change take effect
		self.Layout()
		if bibRow == -1:
			return
		self.racersGrid.MakeCellVisible(bibRow, 0)
			
	def deleteCurrentRider( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			bib = int(self.riderBibEntry.GetValue())
			riderName = dict(self.riderBibNames)[bib]
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			evt = season['events'][evtName]
			for bibMachineCategoriesTeam in evt['racers']:
				if bibMachineCategoriesTeam[0] == bib:
					if Utils.MessageOKCancel( self, 'Are you sure you want to delete #' + str(bib) + ' ' + database.getRiderName(bib, True) + ' from this event?', 'Delete racer' ):
						self.deleteRider(event, bib)
					return
			else:
				Utils.MessageOK( self, '#' + str(bib) + ' ' + database.getRiderName(bib, True) + ' is not entered in this event!', 'Cannot delete racer', iconMask=wx.ICON_ERROR)
		except ValueError:
			return
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		
	def deleteRider( self, event, bib ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					for bibMachineCategoriesTeam in evt['racers']:
						if bibMachineCategoriesTeam[0] == bib:
							evt['racers'].remove(bibMachineCategoriesTeam)
					db.setChanged()
					self.refreshCurrentSelection()
					self.refreshRaceAllocationTable()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				
	def deleteAllRiders( self, event ):
		database = Model.database
		if database is None:
			return
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete all racers from this event?', 'Delete all racers' ):
			if self.season is not None and self.evt is not None:
				try:
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						evt['racers'].clear()
						db.setChanged()
						self.refreshCurrentSelection()
						self.refreshRaceAllocationTable()
				except Exception as e:
					Utils.logException( e, sys.exc_info() )
		
	def onAddToRaceButton( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None:
			try:
				bib = int(self.riderBibEntry.GetValue())
				dt = database.getCurEvtDate()
				if dt is None:
					dt = datetime.datetime.now()
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					if 'racers' not in evt:
						evt['racers'] = []
					for bibMachineCategoriesTeam in evt['racers']:
						if bibMachineCategoriesTeam[0] == bib:
							if not Utils.MessageOKCancel( self, '#' + str(bib)  + ' ' + database.getRiderName(bib, True) + ' is already in this event!\nDo you want to update their details?', 'Rider already entered'):
								Utils.writeLog( evtName + ': Not updating rider #: ' + str(bib) + ' ' + database.getRiderName(bib))
								self.refreshCurrentSelection()
								self.refreshRaceAllocationTable()
								return
							#delete the existing entry
							evt['racers'].remove(bibMachineCategoriesTeam)
							db.setChanged()
							#now continue to re-add them with the new details...
					machine = self.riderMachine.GetValue()
					team = self.riderTeam.GetValue().strip()
					foundTeam = False
					for teamAbbrevEntered in db.teams:
						if teamAbbrevEntered[0] == team:  #update entered date for team
							teamAbbrevEntered[2] = int(dt.timestamp())
							foundTeam = True
							break
					if not foundTeam and len(team) > 0:  #add a new team
						db.teams.append([team, team[0:6].strip().upper(), int(dt.timestamp())])
					categories = []
					for i in range(EventEntry.numCategories):
						if getattr(self, 'riderCategory' + str(i), None).IsChecked():
							categories.append(season['categories'][i][0])
					if len(categories) == 0:
						Utils.MessageOK( self, 'Rider #' + str(bib) + ' ' + database.getRiderName(bib, True) + ' has no categories!', 'No categories' )
					evt['racers'].append([bib, machine, categories, team])
					db.riders[bib]['LastEntered'] = int(dt.timestamp())
					if 'Machines' not in db.riders[bib]:
						db.riders[bib]['Machines'] = []
					found = False
					for machineCategoriesDate in db.riders[bib]['Machines']:
						if machine == machineCategoriesDate[0]:
							machineCategoriesDate[1] = categories
							if len(machineCategoriesDate) < 3:  #backwards compatibility with old format
								machineCategoriesDate.append( int(dt.timestamp()) )
							else:
								machineCategoriesDate[2] = int(dt.timestamp())
							found = True
							break
					if not found:
						if len(machine) > 0:
							db.riders[bib]['Machines'].append([machine, categories, int(dt.timestamp())])
					if len(team) > 0:
						db.riders[bib]['Team'] = team
					elif 'Team' in db.riders[bib]:
						del db.riders[bib]['Team']
					db.setChanged()
					self.riderBibEntry.ChangeValue('')
					self.riderNameEntry.ChangeValue('')
					self.updateMachinesChoices(None)
					self.enableRiderControls(enable=False)
					self.clearCategorySelections()
					self.refreshCurrentSelection()
					self.refreshRaceAllocationTable(makeLastRowVisible=True)
			except ValueError:
				return
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
					
	def refreshRaceAllocationTable( self, makeLastRowVisible=False ):
		self.clearGrid(self.racersGrid)
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				deletedRiders = []
				if 'racers' in evt:
					for bibMachineCategoriesTeam in evt['racers']:
						bib = bibMachineCategoriesTeam[0]
						rider = database.getRider(bib)
						self.racersGrid.AppendRows(1)
						row = self.racersGrid.GetNumberRows() -1
						col = 0
						self.racersGrid.SetCellValue(row, col, str(bib))
						self.racersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
						col += 1
						if rider is not None:
							self.racersGrid.SetCellValue(row, col, database.getRiderName(bib))
							col += 1
							self.racersGrid.SetCellValue(row, col, Model.Genders[rider['Gender']] if 'Gender' in rider else '')
							col += 1
							self.racersGrid.SetCellValue(row, col, str(database.getRiderAge(bib)) if database.getRiderAge(bib) else '' )
							self.racersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
							col += 1
							self.racersGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
							self.racersGrid.SetCellValue(row, col, rider['NatCode'] if 'NatCode' in rider else '')
							col += 1
							self.racersGrid.SetCellValue(row, col, str(rider['Factor']) if 'Factor' in rider else '' )
							self.racersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
							col += 1
						else:
							deletedRiders.append(bib)
							self.racersGrid.SetCellValue(row, col, '[DELETED RIDER]')
							col += 5
						if len(bibMachineCategoriesTeam) >=2:
							self.racersGrid.SetCellValue(row, col, bibMachineCategoriesTeam[1])
						col += 1
						if len(bibMachineCategoriesTeam) >=3:
							self.racersGrid.SetCellValue(row, col, ','.join(database.getAbbreviatedCategory(c) for c in bibMachineCategoriesTeam[2]))
						col += 1
						if len(bibMachineCategoriesTeam) >=4:
							self.racersGrid.SetCellValue(row, col, bibMachineCategoriesTeam[3])
						col += 1
						if rider is None:
							for c in range(col):
								self.racersGrid.SetCellBackgroundColour(row, c, self.yellowColour)
				if database.useFactors:
					self.racersGrid.ShowCol(5)
				else:
					self.racersGrid.HideCol(5)
				self.racersGrid.AutoSize()
				self.Layout()
				if makeLastRowVisible:
					self.racersGrid.MakeCellVisible(self.racersGrid.GetNumberRows()-1, 0)
				if len(deletedRiders) > 0:
					Utils.MessageOK( self, 'Racer(s) do not exist in Riders database:\n' + ', '.join([str(r) for r in deletedRiders if r]) + '\nThey will not be added to the sign-on sheet.', 'Riders do not exist')
			except Exception as e:
				Utils.logException( e, sys.exc_info() )

	def refreshCurrentSelection( self ):
		database = Model.database
		if database is None:
			return
		selection = []
		title = 'No event selected'
		if self.season is not None and self.evt is not None:
			seasonName = database.getSeasonsList()[self.season]
			selection.append( seasonName )
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			selection.append( evtName )
			evt = season['events'][evtName]
			title = ('{:%Y-%m-%d: }'.format(database.getCurEvtDate()) if database.getCurEvtDate() is not None else '') + ', '.join(n for n in selection)
			if 'racers' in evt:
				title += ' (' + str(len(evt['racers'])) + ' racers)'
		self.currentSelection.SetLabel( title )
		database.selection = selection
		
	def updateMachinesChoices( self, bib ):
		self.riderMachine.Clear()
		self.riderMachine.ChangeValue('')
		if bib is None:
			return
		database = Model.database
		if database is None:
			return
		try:
			machines = []
			rider = database.getRider(bib)
			if 'Machines' in rider:
				for machineCategoriesDate in sorted(rider['Machines'], key=lambda item: (item[2] if len(item) >= 3 and item[2] else 0) ):
					machines.append(machineCategoriesDate[0])
				self.riderMachine.Clear()
				self.riderMachine.Set( machines )
				if len(machines) > 0 :
					self.riderMachine.ChangeValue(machines[-1])
				self.onSelectMachine()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def updateTeamSelection( self, bib ):
		database = Model.database
		if database is None:
			return
		rider = database.getRider(bib)
		if rider is not None:
			if 'Team' in rider:
				self.riderTeam.SetValue(rider['Team'])
				return
		self.riderTeam.SetValue('')
			
	def clearCategorySelections( self ):
		for i in range(EventEntry.numCategories):
			getattr(self, 'riderCategory' + str(i), None).SetValue(False)

	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )
		self.racersGrid.ClearSelection()

	def commit( self, event=None ):
		Utils.writeLog('EventEntry commit: ' + str(event))
		if self.season is not None and self.evt is not None:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[self.season]
				season = db.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'racers' in evt:
					evt['racers'].sort(key=lambda a: a[0])  # Sort the racers list
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self ):
		Utils.writeLog('EventEntry refresh')
		database = Model.database
		if database is None:
			return
		try:
			self.riderBibEntry.Clear()
			self.riderBibNames.clear()
			#get current selection
			self.season = database.curSeason
			self.evt = database.curEvt
			self.refreshCurrentSelection()
			#get the riders database, populate the bib selection drop-down
			riders = database.getRiders()
			firstNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['FirstName'], reverse=False))
			sortedRiders = dict(sorted(firstNameSortedRiders.items(), key=lambda item: item[1]['LastName'], reverse=False))
			for bib in sortedRiders:
				name = database.getRiderName(bib, False)
				if name:
					self.riderBibNames.append((bib, name))
			self.riderBibEntry.AppendItems( list(map(str ,sorted([bibName[0] for bibName in self.riderBibNames]))) )
			#add the riders again in firstname lastname order - this seems to be a hot mess under windows?
			lastNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['LastName'], reverse=False))
			sortedRiders = dict(sorted(lastNameSortedRiders.items(), key=lambda item: item[1]['FirstName'], reverse=False))
			for bib in sortedRiders:
				name = database.getRiderName(bib, True)
				if name:
					self.riderBibNames.append((bib, name))
			#populate the AutoCompleter
			names = []
			[names.append(bibName[1]) for bibName in self.riderBibNames if bibName[1] not in names] #copy without duplicates (riders with only one name field)
			self.riderNameEntry.AutoComplete( riderNameCompleter(names) )
			#get the teams database, populate the ComboBox
			self.riderTeam.Set( [teamAbbrevEntered[0] for teamAbbrevEntered in database.teams] )
			#enable the categories checkboxes
			if self.season is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				catCount = 0
				if 'categories' in season:
					if season['categories']:
						for categoryAbbrev in season['categories']:
							getattr(self, 'riderCategory' + str(catCount), None).SetLabel(categoryAbbrev[0])
							getattr(self, 'riderCategory' + str(catCount), None).Show()
							getattr(self, 'riderCategory' + str(catCount), None).SetValue(False)
							catCount += 1
				if catCount == 0:
					self.categoriesLabel.SetLabel('Season has\nno Categories!')
				else:
					self.categoriesLabel.SetLabel('Categories:')
				for i in range(catCount, EventEntry.numCategories):
					getattr(self, 'riderCategory' + str(catCount), None).SetLabel('Category' + str(catCount))
					getattr(self, 'riderCategory' + str(catCount), None).SetValue(False)
					getattr(self, 'riderCategory' + str(catCount), None).Hide()
					catCount += 1
			#now, the allocation table
			self.refreshRaceAllocationTable()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		self.Layout()
