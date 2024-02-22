import wx
import re
import os
import sys
import Model
import Utils
#import ColGrid
from collections import defaultdict
from FixCategories import FixCategories, SetCategory
#from GetResults import GetResults, RidersCanSwap
#from ExportGrid import ExportGrid
#from RiderDetail import ShowRiderDetailDialog
#from EditEntry import CorrectNumber, ShiftNumber, InsertNumber, DeleteEntry, SwapEntry
from Undo import undo
import datetime
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

#reNonDigits = re.compile( '[^0-9]' )
#reLapMatch = re.compile( '<?Lap>? ([0-9]+)' )

class Results( wx.Panel ):
	DisplayLapTimes = 0
	DisplayRaceTimes = 1
	DisplayLapSpeeds = 2
	DisplayRaceSpeeds = 3

	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.colnames = ['Pos', 'Bib', 'Name', 'Machine', 'Team', 'Gender', 'Nat', 'Seconds', 'Speed', 'Time of day', 'Note', 'Attempts']
		
		#self.category = None
		#self.showRiderData = True
		#self.selectDisplay = 0
		#self.firstDraw = True
		
		#self.rcInterp = set()
		#self.rcNumTime = set()
		#self.rcWorstLaps = set()
		#self.numSelect = None
		#self.isEmpty = True
		#self.reSplit = re.compile( '[\[\]\+= ]+' )	# separators for the fields.
		#self.iLap = None
		#self.entry = None
		#self.iRow, self.iCol = None, None
		#self.iLastLap = 0
		#self.fastestLapRC = None

		self.hbs = wx.BoxSizer(wx.HORIZONTAL)
		self.categoryLabel = wx.StaticText( self, label = _('Category:') )
		self.categoryChoice = wx.Choice( self )
		self.Bind(wx.EVT_CHOICE, self.doChooseCategory, self.categoryChoice)
		
		#self.showRiderDataToggle = wx.ToggleButton( self, label = _('Show Rider Data'), style=wx.BU_EXACTFIT )
		#self.showRiderDataToggle.SetValue( self.showRiderData )
		#self.Bind( wx.EVT_TOGGLEBUTTON, self.onShowRiderData, self.showRiderDataToggle )
		
		#self.showLapTimesRadio = wx.RadioButton( self, label = _('Lap Times'), style=wx.BU_EXACTFIT|wx.RB_GROUP )
		#self.showLapTimesRadio.SetValue( self.selectDisplay == Results.DisplayLapTimes )
		#self.Bind( wx.EVT_RADIOBUTTON, self.onSelectDisplayOption, self.showLapTimesRadio )
		#self.showLapTimesRadio.SetToolTip(wx.ToolTip(_('Useful for finding the fastest lap.')))
		
		#self.showRaceTimesRadio = wx.RadioButton( self, label = _('Race Times'), style=wx.BU_EXACTFIT )
		#self.showRaceTimesRadio.SetValue( self.selectDisplay == Results.DisplayRaceTimes )
		#self.Bind( wx.EVT_RADIOBUTTON, self.onSelectDisplayOption, self.showRaceTimesRadio )
		#self.showRaceTimesRadio.SetToolTip(wx.ToolTip(_('Useful for finding for Prime winners.\nAfter selecting, click on a lap header to sort.')))
		
		#self.showLapSpeedsRadio = wx.RadioButton( self, label = _('Lap Speeds'), style=wx.BU_EXACTFIT )
		#self.showLapSpeedsRadio.SetValue( self.selectDisplay == Results.DisplayLapSpeeds )
		#self.Bind( wx.EVT_RADIOBUTTON, self.onSelectDisplayOption, self.showLapSpeedsRadio )
		#self.showLapSpeedsRadio.SetToolTip(wx.ToolTip(_('Useful for finding the fastest lap.')))
		
		#self.showRaceSpeedsRadio = wx.RadioButton( self, label = _('Race Speeds'), style=wx.BU_EXACTFIT )
		#self.showRaceSpeedsRadio.SetValue( self.selectDisplay == Results.DisplayRaceSpeeds )
		#self.Bind( wx.EVT_RADIOBUTTON, self.onSelectDisplayOption, self.showRaceSpeedsRadio )
		#self.showRaceSpeedsRadio.SetToolTip(wx.ToolTip(_("Useful to predict how long a race will take based on rider's average speed.")))
		
		#f = self.showLapTimesRadio.GetFont()
		#self.boldFont = wx.Font( f.GetPointSize()+2, f.GetFamily(), f.GetStyle(), wx.FONTWEIGHT_BOLD, f.GetUnderlined() )
		
		
		#self.search = wx.SearchCtrl(self, size=(80,-1), style=wx.TE_PROCESS_ENTER )
		##self.search.ShowCancelButton( True )
		#self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self.search)
		#self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch, self.search)
		#self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.search)
		
		#bitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'Zoom-In-icon.png'), wx.BITMAP_TYPE_PNG )
		#self.zoomInButton = wx.BitmapButton( self, wx.ID_ZOOM_IN, bitmap, style=wx.BU_EXACTFIT | wx.BU_AUTODRAW )
		#self.Bind( wx.EVT_BUTTON, self.onZoomIn, self.zoomInButton )
		#bitmap = wx.Bitmap( os.path.join(Utils.getImageFolder(), 'Zoom-Out-icon.png'), wx.BITMAP_TYPE_PNG )
		#self.zoomOutButton = wx.BitmapButton( self, wx.ID_ZOOM_OUT, bitmap, style=wx.BU_EXACTFIT | wx.BU_AUTODRAW )
		#self.Bind( wx.EVT_BUTTON, self.onZoomOut, self.zoomOutButton )
		
		self.hbs.Add( self.categoryLabel, flag=wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		self.hbs.Add( self.categoryChoice, flag=wx.ALL, border=4 )
		#self.hbs.Add( self.showRiderDataToggle, flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.Add( self.showLapTimesRadio, flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.Add( self.showRaceTimesRadio, flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.Add( self.showLapSpeedsRadio, flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.Add( self.showRaceSpeedsRadio, flag=wx.ALL | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.AddStretchSpacer()
		#self.hbs.Add( self.search, flag=wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.Add( self.zoomInButton, flag=wx.TOP | wx.BOTTOM | wx.LEFT | wx.ALIGN_CENTRE_VERTICAL, border=4 )
		#self.hbs.Add( self.zoomOutButton, flag=wx.TOP | wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTRE_VERTICAL, border=4 )

		self.whiteColour = wx.Colour( 255, 255, 255 )
		self.blackColour = wx.Colour( 0, 0, 0 )
		self.yellowColour = wx.Colour( 255, 255, 0 )
		self.orangeColour = wx.Colour( 255, 165, 0 )
		self.greyColour = wx.Colour( 150, 150, 150 )
		self.lightGreyColour = wx.Colour ( 211, 211, 211 )
		self.greenColour = wx.Colour( 127, 210, 0 )
		self.lightBlueColour = wx.Colour( 153, 205, 255 )
		
		#self.splitter = wx.SplitterWindow( self )
		
		self.resultsGrid = wx.grid.Grid( self )
		self.resultsGrid.CreateGrid(0, len(self.colnames))
		for i, name in enumerate(self.colnames):
			self.resultsGrid.SetColLabelValue(i, name)

		self.resultsGrid.HideRowLabels()
		self.resultsGrid.AutoSize()
		
		self.resultsGrid.SetRowLabelSize( 0 )
		self.resultsGrid.SetMargins( 0, 0 )
		#self.labelGrid.SetRightAlign( True )
		self.resultsGrid.AutoSizeColumns( True )
		self.resultsGrid.DisableDragColSize()
		self.resultsGrid.DisableDragRowSize()
		self.resultsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRightClick )
		self.resultsGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChanged )
		# put a tooltip on the cells in a column
		#self.labelGrid.GetGridWindow().Bind(wx.EVT_MOTION, self.onMouseOver)
		#
		
		#self.lapGrid = ColGrid.ColGrid( self.splitter, style=wx.BORDER_SUNKEN )
		#self.lapGrid.SetRowLabelSize( 0 )
		#self.lapGrid.SetMargins( 0, 0 )
		#self.lapGrid.SetRightAlign( True )
		#self.lapGrid.AutoSizeColumns( True )
		#self.lapGrid.DisableDragColSize()
		#self.lapGrid.DisableDragRowSize()
		
		#self.splitter.SetMinimumPaneSize(100)
		#self.splitter.SplitVertically(self.labelGrid, self.lapGrid, 400)
		
		#Sync the two vertical scrollbars.
		#self.labelGrid.Bind(wx.EVT_SCROLLWIN, self.onScroll)
		#self.lapGrid.Bind(wx.EVT_SCROLLWIN, self.onScroll)
		
		#self.Bind( wx.grid.EVT_GRID_SELECT_CELL, self.doNumSelect )
		#self.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.doNumDrilldown )
		#self.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.doRightClick )
		#self.lapGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		#self.labelGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		#self.labelGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onLabelColumnRightClick )
		
		bs = wx.BoxSizer(wx.VERTICAL)
		bs.Add(self.hbs)
		#bs.Add(self.lapGrid, 1, wx.GROW|wx.ALL, 5)
		
		bs.Add(self.hbs, 0, wx.EXPAND )
		#bs.Add(self.splitter, 1, wx.EXPAND|wx.GROW|wx.ALL, 5 )
		bs.Add(self.resultsGrid, 1, wx.GROW|wx.ALL, 5 )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(bs)
		bs.SetSizeHints(self)
			
	def onRightClick( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		try:
			bib = int(self.resultsGrid.GetCellValue(row, 1))
		except:
			return
		menu = wx.Menu()
		menu.SetTitle('Change #' + str(bib) + ' status:')
		fin = menu.Append( wx.ID_ANY, 'Set Finisher', 'Set rider Finisher...' )
		self.Bind( wx.EVT_MENU, lambda event: self.setRiderFinisher(event, bib), fin )
		np = menu.Append( wx.ID_ANY, 'Set NP', 'Set rider NP...' )
		self.Bind( wx.EVT_MENU, lambda event: self.setRiderNP(event, bib), np )
		dns = menu.Append( wx.ID_ANY, 'Set DNS', 'Set rider DNS...' )
		self.Bind( wx.EVT_MENU, lambda event: self.setRiderDNS(event, bib), dns )
		dnf = menu.Append( wx.ID_ANY, 'Set DNF', 'Set rider DNF...' )
		self.Bind( wx.EVT_MENU, lambda event: self.setRiderDNF(event, bib), dnf )
		dq = menu.Append( wx.ID_ANY, 'Set DQ', 'Set rider DQ...' )
		self.Bind( wx.EVT_MENU, lambda event: self.setRiderDQ(event, bib), dq )
		
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def OnCellChanged( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		old = event.GetString()
		value = self.resultsGrid.GetCellValue(row, col)
		
		# restore the old value
		self.resultsGrid.SetCellValue(row, col, old)

	def setRiderDNF( self, event, bib ):
		race = Model.race
		if not race:
			return
		race.setRiderStatus( bib, Model.Rider.DNF )
		race.setChanged()
		self.refresh()
		
	def setRiderDNS( self, event, bib ):
		race = Model.race
		if not race:
			return
		race.setRiderStatus( bib, Model.Rider.DNS )
		race.setChanged()
		self.refresh()
		
	def setRiderDQ( self, event, bib ):
		race = Model.race
		if not race:
			return
		race.setRiderStatus( bib, Model.Rider.DQ )
		race.setChanged()
		self.refresh()
	
	def setRiderNP( self, event, bib ):
		race = Model.race
		if not race:
			return
		race.setRiderStatus( bib, Model.Rider.NP )
		race.setChanged()
		self.refresh()
	
	def setRiderFinisher( self, event, bib ):
		race = Model.race
		if not race:
			return
		race.setRiderStatus( bib, Model.Rider.Finisher )
		race.setChanged()
		self.refresh()
				
	def setCategoryAll( self ):
		FixCategories( self.categoryChoice, 0 )
		Model.setCategoryChoice( 0, 'resultsCategory' )
	
	def setCategory( self, category ):
		for i, c in enumerate(Model.race.getCategories( startWaveOnly=False ) if Model.race else [], 1):
			if c == category:
				SetCategory( self.categoryChoice, c )
				Model.setCategoryChoice( i, 'resultsCategory' )
				return
		SetCategory( self.categoryChoice, None )
		Model.setCategoryChoice( 0, 'resultsCategory' )
	
	def doChooseCategory( self, event ):
		Model.setCategoryChoice( self.categoryChoice.GetSelection(), 'resultsCategory' )
		self.refresh()

	def clearGrid( self ):
		if self.resultsGrid.GetNumberRows():
			self.resultsGrid.DeleteRows(0, self.resultsGrid.GetNumberRows())
		#self.resultsGrid.Set( data = [], colnames = [], textColour = {}, backgroundColour = {} )
		#self.resultsGrid.Reset()
		#self.lapGrid.Set( data = [], colnames = [], textColour = {}, backgroundColour = {} )
		#self.lapGrid.Reset()

	def refresh( self ):
		self.category = None
		#self.isEmpty = True
		#self.iLastLap = 0
		#self.rcInterp = set()	# Set of row/col coordinates of interpolated numbers.
		#self.rcNumTime = set()
		
		#self.search.SelectAll()
		
		#CloseFinishTime = 0.07
		#self.closeFinishBibs = defaultdict( list )
		self.clearGrid()
		
		race = Model.race
		if not race:
			return
		
		excelLink = getattr(race, 'excelLink', None)
		if excelLink:
			externalInfo = excelLink.read()
		
		category = FixCategories( self.categoryChoice, getattr(race, 'resultsCategory', 0) )
		self.hbs.Layout()
		#for si in self.hbs.GetChildren():
			#if si.IsWindow():
				#si.GetWindow().Refresh()
		self.category = category

		#Fix the speed column.
		speedUnit = None
		iSpeedCol = None
		try:
			iSpeedCol = next(i for i, c in enumerate(self.colnames) if c == _('Speed'))
		except StopIteration:
			pass
		if iSpeedCol is not None:
			if race.distanceUnit == Model.Race.UnitKm:
				speedUnit = 'kph'
			elif race.distanceUnit == Model.Race.UnitMiles:
				speedUnit = 'mph'
			else:
				speedUnit = 'm/s'
			self.resultsGrid.SetColLabelValue(iSpeedCol, _('Speed') + ' (' + speedUnit + ')' )

		res = race.getSprintResults(self.category)
		
		for i, bibSprintDicts in enumerate(res):
			bib = bibSprintDicts[0]
			status = race.getRiderStatus(bib) if race.getRiderStatus(bib) is not None else Model.Rider.NP
			name = ''
			if bib and excelLink is not None and ((excelLink.hasField('FirstName') or excelLink.hasField('LastName'))):
				try:
					name = ', '.join( n for n in [externalInfo[bib]['LastName'], externalInfo[bib]['FirstName']] if n )
				except:
					pass
			elif 'sprintNameEdited' in sprintDict:
					name = sprintDict['sprintNameEdited']
			gender = ''
			if bib and excelLink is not None and excelLink.hasField('Gender'):
				try:
					gender = externalInfo[bib]['Gender']
				except:
					pass
			elif 'sprintGenderEdited' in sprintDict:
					gender = sprintDict['sprintGenderEdited']
			natcode = ''
			if bib and excelLink is not None and excelLink.hasField('NatCode'):
				try:
					natcode = externalInfo[bib]['NatCode']
				except:
					if excelLink.hasField('UCICode'):
						try:
							natcode = externalInfo[bib]['UCIcode']
						except:
							pass
			elif 'sprintNatcodeEdited' in sprintDict:
					natcode = sprintDict['sprintNatcodeEdited']
			machine = ''
			if bib and excelLink is not None and excelLink.hasField('Machine'):
				try:
					machine = externalInfo[bib]['Machine']
					
				except:
					pass
			elif 'sprintMachineEdited' in sprintDict:
				machine = sprintDict['sprintMachineEdited']
			team = ''
			if bib and excelLink is not None and excelLink.hasField('Team'):
				try:
					team = externalInfo[bib]['Team']
				except:
					pass
			elif 'sprintTeamEdited' in sprintDict:
				team = sprintDict['sprintTeamEdited']
			if bibSprintDicts[1] is not None:
				sprintDict = bibSprintDicts[1][0]
				self.resultsGrid.AppendRows(1)
				row = self.resultsGrid.GetNumberRows() -1
				col = 0
				if status == Model.Rider.Finisher:
					self.resultsGrid.SetCellValue(row, col, str(i+1))
				else:
					self.resultsGrid.SetCellValue(row, col, Model.Rider.statusNames[status])
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(bib))
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(name))
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(machine))
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(team))
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(gender))
				col += 1
				self.resultsGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
				self.resultsGrid.SetCellValue(row, col, str(natcode))
				col += 1				
				self.resultsGrid.SetCellValue(row, col, str('{:.3f}'.format(sprintDict["sprintTime"])))
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				speed = float(sprintDict['sprintDistance']) / float(sprintDict['sprintTime'])
				if race.distanceUnit == Model.Race.UnitKm:
					self.resultsGrid.SetCellValue(row, col, str('{:.3f}'.format(speed*3.6)))
				elif race.distanceUnit == Model.Race.UnitMiles:
					self.resultsGrid.SetCellValue(row, col, str('{:.3f}'.format(speed*2.23694)))
				else:
					self.resultsGrid.SetCellValue(row, col, str('{:.3f}'.format(speed)))
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				if "sprintStart" in sprintDict:
					sprintStart = datetime.datetime.fromtimestamp(sprintDict['sprintStart'])
					if 'sprintStartMillis' in sprintDict:
						sprintStart += datetime.timedelta(milliseconds = sprintDict['sprintStartMillis'])
					self.resultsGrid.SetCellValue(row, col, sprintStart.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3])
					self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(sprintDict["sprintNote"]) if "sprintNote" in sprintDict else '')
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTER)
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(len(bibSprintDicts[1])))
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
			else:
				# No sprints for rider
				self.resultsGrid.AppendRows(1)
				row = self.resultsGrid.GetNumberRows() -1
				col = 0
				self.resultsGrid.SetCellValue(row, col, Model.Rider.statusNames[status])
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(bib))
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(name))
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(machine))
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(team))
				col += 1
				self.resultsGrid.SetCellValue(row, col, str(gender))
				col += 1
				self.resultsGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
				self.resultsGrid.SetCellValue(row, col, str(natcode))
				col += 5
				self.resultsGrid.SetCellValue(row, col, '0')
				self.resultsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTER)
		
		
		self.resultsGrid.AutoSizeColumns()
