import wx
import re
import os
import sys
import Utils
#import ColGrid
from collections import defaultdict
#from Undo import undo
import datetime
import Flags
import Model

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

class Riders( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.colnames = ['Bib', 'Name', 'Gender', 'Age', 'Nat', 'License', 'Last Entered']
		self.sortBy = 0
		self.reverseSort = False
		
		bs = wx.BoxSizer(wx.VERTICAL)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(bs)
		bs.SetSizeHints(self)
	
		self.ridersGrid = wx.grid.Grid( self )
		self.ridersGrid.CreateGrid(0, len(self.colnames))
		for i, name in enumerate(self.colnames):
			self.ridersGrid.SetColLabelValue(i, name)

		self.ridersGrid.HideRowLabels()
		self.ridersGrid.AutoSize()
		
		self.ridersGrid.SetRowLabelSize( 0 )
		self.ridersGrid.SetMargins( 0, 0 )
		self.ridersGrid.AutoSizeColumns( True )
		self.ridersGrid.DisableDragColSize()
		self.ridersGrid.DisableDragRowSize()
		self.ridersGrid.EnableEditing(False)
		self.ridersGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRightClick )
		self.ridersGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onRightClick )
		self.ridersGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onDoubleClick )
		self.ridersGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		
		bs.Add(self.ridersGrid, 1, wx.GROW|wx.ALL, 5 )
		
		self.refresh()
		
	def doLabelClick( self, event ):
		col = event.GetCol()
		if self.sortBy == col:
			self.reverseSort = not self.reverseSort
		else:
			self.sortBy = col
			self.reverseSort = False
		#print('sort by ' + str(self.sortBy) + ' reverse ' + str(self.reverseSort))
		wx.CallAfter( self.refresh )
		
	def onDoubleClick (self, event ):
		row = event.GetRow()
		col = event.GetCol()
		try:
			bib = int(self.ridersGrid.GetCellValue(row, 0))
		except:
			return
		self.editRiderDetails( None, bib )
		
	def onRightClick( self, event ):
		row = event.GetRow()
		col = event.GetCol()
		menu = wx.Menu()
		if row == -1: # header row
			menu.SetTitle('Riders')
			add = menu.Append( wx.ID_ANY, 'Add new rider', 'Add a new rider...' )
			self.Bind( wx.EVT_MENU, lambda event: self.addNewRider(event, None), add )
		else:
			try:
				bib = int(self.ridersGrid.GetCellValue(row, 0))
				name = self.ridersGrid.GetCellValue(row, 1)
			except:
				return
			menu.SetTitle('#' + str(bib) + ' ' + name)
			ed = menu.Append( wx.ID_ANY, 'Edit details', 'Edit rider details...' )
			self.Bind( wx.EVT_MENU, lambda event: self.editRiderDetails(event, bib), ed )
			if not Model.database.isRider(bib-1):
				adb = menu.Append( wx.ID_ANY, 'Add new rider before', 'Add a new rider before...' )
				self.Bind( wx.EVT_MENU, lambda event: self.addNewRider(event, bib-1), adb )
			if not Model.database.isRider(bib+1):
				ada = menu.Append( wx.ID_ANY, 'Add new rider after', 'Add a new rider after...' )
				self.Bind( wx.EVT_MENU, lambda event: self.addNewRider(event, bib+1), ada )
			de = menu.Append( wx.ID_ANY, 'Delete rider', 'Delete this rider...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteRider(event, bib), de )
			add = menu.Append( wx.ID_ANY, 'Add new rider', 'Add a new rider...' )
			self.Bind( wx.EVT_MENU, lambda event: self.addNewRider(event, None), add )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addNewRider( self, event, bib ):
		if bib is None:
			with wx.NumberEntryDialog(self, 'Enter number for new rider:', 'Bib#:', 'New rider', 0, 1, 65535) as dlg:
				if dlg.ShowModal():
					bib = dlg.GetValue()
					print(bib)
		with Model.LockDatabase() as db:
			db.addRider(int(bib))
		self.refresh()
		
	def deleteRider( self, event, bib ):
		database = Model.database
		if database is None:
			return
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete #' + str(bib) + ' ' + database.getRiderName(bib) + '?', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete rider: ' + str(bib))
			with Model.LockDatabase() as db:
				db.deleteRider(int(bib))
			wx.CallAfter( self.refresh )
			
	def editRiderDetails(self, event, bib):
		mainwin = Utils.getMainWin()
		mainwin.riderDetail.setBib(bib)
		wx.CallAfter(mainwin.showPage, mainwin.iRiderDetailPage )

	def clearGrid( self ):
		if self.ridersGrid.GetNumberRows():
			self.ridersGrid.DeleteRows(0, self.ridersGrid.GetNumberRows())
			
	def refresh( self ):
		self.clearGrid()
		
		database = Model.database
		
		if database is None:
			return
		
		riders = database.getRiders()
		
		if self.sortBy == 1: # name
			firstNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['FirstName'], reverse=self.reverseSort))
			sortedRiders = dict(sorted(firstNameSortedRiders.items(), key=lambda item: item[1]['LastName'], reverse=self.reverseSort))
		elif self.sortBy == 2: # Gender
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['Gender']) if 'Gender' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 3: # Age
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['DOB']) if 'DOB' in item[1] else 0, reverse=self.reverseSort))
		elif self.sortBy == 4: # Natcode
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['NatCode']) if 'NatCode' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 5: # License
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['License']) if 'License' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 6: # Last entered
			sortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['LastEntered'], reverse=self.reverseSort))
		else: #default (bib)
			sortedRiders = dict(sorted(riders.items(), reverse=self.reverseSort))
		
		for bib in sortedRiders:
			rider = riders[bib]
			self.ridersGrid.AppendRows(1)
			row = self.ridersGrid.GetNumberRows() -1
			col = 0
			self.ridersGrid.SetCellValue(row, col, str(bib))
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			col+=1
			self.ridersGrid.SetCellValue(row, col, database.getRiderName(bib))
			col+=1
			self.ridersGrid.SetCellValue(row, col, Model.Genders[rider['Gender']] if 'Gender' in rider else '')
			col+=1
			age = ''
			self.ridersGrid.SetCellValue(row, col, str(database.getRiderAge(bib)) if database.getRiderAge(bib) else '' )
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			col+=1
			self.ridersGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
			self.ridersGrid.SetCellValue(row, col, rider['NatCode'] if 'NatCode' in rider else '')
			col+=1
			self.ridersGrid.SetCellValue(row, col, rider['License'] if 'License' in rider else '')
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			col+=1
			if rider['LastEntered']:
				dt = datetime.datetime.fromtimestamp(rider['LastEntered'])
			else:
				dt = ''
			self.ridersGrid.SetCellValue(row, col, str(dt))
			
		self.ridersGrid.AutoSizeColumns()
