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
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.season = None
		self.evt = None
		self.colnames = ['Bib', 'Name', 'Gender', 'Nat', 'Machine', 'Categories']
		
		self.riderBibNames = []
		
		vs = wx.BoxSizer(wx.VERTICAL)
		self.currentSelection = wx.StaticText( self, label='No event selected' )
		vs.Add( self.currentSelection )
		
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
		self.addToRaceButton = wx.Button( self, label='Enter rider')
		self.addToRaceButton.SetToolTip( wx.ToolTip('Adds the selected rider to the event'))
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
		self.racersGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRacerRightClick )
		# self.racersGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onSeasonsRightClick )
		# self.racersGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectSeason )
		vs.Add( self.racersGrid, flag=wx.EXPAND )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onSelectBib( self, event ):
		database = Model.database
		if database is None:
			return
		iBib = self.riderBibEntry.GetSelection()
		bib = sorted([bibName[0] for bibName in self.riderBibNames])[iBib]
		riderName = dict(self.riderBibNames)[bib]
		self.riderNameEntry.ChangeValue( riderName )
		
	def onEnterRiderName( self, event ):
		name = re.sub("[^a-z ]", "", self.riderNameEntry.GetValue())
		sortedBibNames = sorted([bibName[0] for bibName in self.riderBibNames])
		for bibName in self.riderBibNames:
			if name == re.sub("[^a-z ]", "", bibName[1].lower()):
				iBib = sortedBibNames.index(bibName[0])
				self.riderBibEntry.SetSelection(iBib)
				self.riderNameEntry.ChangeValue( bibName[1] )
				return
		self.riderBibEntry.SetSelection(wx.NOT_FOUND)
		
	def onRacerRightClick( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		try:
			bib = int(self.racersGrid.GetCellValue(row, 0))
			name = self.racersGrid.GetCellValue(row, 1)
		except:
			return
		menu = wx.Menu()
		menu.SetTitle('#' + str(bib) + ' ' + name)
		# ed = menu.Append( wx.ID_ANY, 'Edit details', 'Edit rider details...' )
		# self.Bind( wx.EVT_MENU, lambda event: self.editRiderDetails(event, bib), ed )
		delete = menu.Append( wx.ID_ANY, 'Delete rider', 'Delete this rider...' )
		self.Bind( wx.EVT_MENU, lambda event: self.deleteRider(event, bib), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def deleteRider(self, event, bib):
		database = Model.database
		if database is None:
			return
		riderName = dict(self.riderBibNames)[bib]
		if self.season is not None and self.evt is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season)[self.evt]
					evt = season[evtName]
					evt['racers'].remove(bib)
					db.setChanged()
					self.refreshCurrentSelection()
					self.refreshRaceAllocationTable()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		
	def onAddToRaceButton( self, event ):
		database = Model.database
		if database is None:
			return
		iBib = self.riderBibEntry.GetSelection()
		bib = sorted([bibName[0] for bibName in self.riderBibNames])[iBib]
		riderName = dict(self.riderBibNames)[bib]
		if self.season is not None and self.evt is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season)[self.evt]
					evt = season[evtName]
					if 'racers' not in evt:
						evt['racers'] = []
					if bib not in evt['racers']:
						evt['racers'].append(bib)
						evt['racers'].sort()
						db.setChanged()
					else:
						Utils.writeLog( evtName + ': Not adding duplicate bib: ' + str(bib))
					self.refreshCurrentSelection()
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
		if self.season is not None and self.evt is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season)[self.evt]
				evt = season[evtName]
				if 'racers' in evt:
					for bib in evt['racers']:
						rider = database.getRider(bib)
						self.racersGrid.AppendRows(1)
						row = self.racersGrid.GetNumberRows() -1
						col = 0
						self.racersGrid.SetCellValue(row, col, str(bib))
						self.racersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
						col += 1
						self.racersGrid.SetCellValue(row, col, database.getRiderName(bib))
						col += 1
						self.racersGrid.SetCellValue(row, col, Model.Genders[rider['Gender']] if 'Gender' in rider else '')
						col	+=	1
						self.racersGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
						self.racersGrid.SetCellValue(row, col, rider['NatCode'] if 'NatCode' in rider else '')
						# if 'machine' in race[bibStr]:
						# 	if race[bibStr]['machine'] is not None:
						# 		self.racersGrid.SetCellValue(row, col, race[bibStr]['machine'])
						# 	else:
						# 		self.racersGrid.SetCellValue(row, col, '[UNSET]')
						col += 1
					# fixme categories
					
				self.racersGrid.AutoSize()
				self.Layout()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )		

	def refreshCurrentSelection( self ):
		database = Model.database
		if database is None:
			return
		selection = []
		title = 'No round selected'
		if self.season is not None and self.evt is not None:
			seasonName = database.getSeasonsList()[self.season]
			selection.append( seasonName )
			season = database.seasons[seasonName]
			evtName = list(season)[self.evt]
			selection.append( evtName )
			evt = season[evtName]
			if 'racers' in evt:
				selection.append( str(len(evt['racers'])) + ' racers')
			title = ', '.join(n for n in selection)
		self.currentSelection.SetLabel( title )
		database.selection = selection
		
	def updateSelection( self, season, evt ):
		self.season = season
		self.evt = evt
		
	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )

	def commit( self, event=None ):
		Utils.writeLog('EventEntry commit: ' + str(event))
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self ):
		print('EventEntry refresh')
		self.refreshCurrentSelection()
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
