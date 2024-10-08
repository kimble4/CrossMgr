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
		
		self.colnames = ['Bib', 'First Name', 'Last Name', 'Gender', 'Age', 'Nat', 'License', 'Factor', 'Team', 'Last Entered', 'Last Tag Written', 'Notes']
		self.sortBy = 0
		self.reverseSort = False
		
		bigFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		bs = wx.BoxSizer(wx.VERTICAL)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(bs)
		bs.SetSizeHints(self)
	
		self.riderCount = wx.StaticText( self, label='' )
		self.riderCount.SetFont( bigFont )
		bs.Add( self.riderCount, 1, wx.GROW|wx.ALL, 5)
	
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
		self.ridersGrid.ClearSelection()
		menu = wx.Menu()
		database = Model.database
		if database is None:
			return
		if row == -1: # header row
			menu.SetTitle('Riders')
			add = menu.Append( wx.ID_ANY, 'Add new rider', 'Add a new rider...' )
			self.Bind( wx.EVT_MENU, lambda event: self.addNewRider(event, None), add )
		else:
			try:
				bib = int(self.ridersGrid.GetCellValue(row, 0))
				name = database.getRiderName(bib)
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
			rn = menu.Append( wx.ID_ANY, 'Change bib', 'Renumber this rider...' )
			self.Bind( wx.EVT_MENU, lambda event: self.renumberRider(event, bib), rn )
			add = menu.Append( wx.ID_ANY, 'Add new rider', 'Add a new rider...' )
			self.Bind( wx.EVT_MENU, lambda event: self.addNewRider(event, None), add )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addNewRider( self, event, bib ):
		database = Model.database
		if database is None:
			return
		if bib is None:
			bib = database.getNextUnusedBib()
			with wx.NumberEntryDialog(self, 'Enter number for new rider:', 'Bib#:', 'New rider', bib, 1, 65535) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					bib = dlg.GetValue()
				else:
					return
		if not database.isRider( bib ):
			with Model.LockDatabase() as db:
				db.addRider(int(bib))
			mainWin = Utils.getMainWin()
			if mainWin.isShowingPage(mainWin.riderDetail):
				mainWin.riderDetail.setBib(bib)
				wx.CallAfter( mainWin.riderDetail.refresh )
			wx.CallAfter( self.refresh )
		else:
			Utils.MessageOK( self, 'Rider #' + str(bib) + ' ' + database.getRiderName(bib, True) + ' already exists!', title='Failed to add rider')
			
	def renumberRider( self, event, bib):
		database = Model.database
		if database is None:
			return
		if bib is None:
			with wx.NumberEntryDialog(self, 'Enter bib for rider to renumber:', 'Bib#:', 'Change bib', 0, 1, 65535) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					bib = dlg.GetValue()
				else:
					return
		newbib = database.getNextUnusedBib()
		with wx.NumberEntryDialog(self, 'Enter new number for #' + str(bib) + ' ' + database.getRiderName(bib, True) + ':', 'Bib#:', 'Change bib', newbib, 1, 65535) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				newbib = dlg.GetValue()
				if not database.isRider( newbib ):
					with Model.LockDatabase() as db:
						if Utils.MessageYesNo( self, 'Do you want to re-initialise ' + database.getRiderName(bib, True) + '\'s timing tags to match bib #' + str(newbib) + '?'  , title = 'Re-initialise tags?', iconMask = wx.ICON_QUESTION):
							db.renumberRider(bib, newbib, initTags=True)
						else:
							db.renumberRider(bib, newbib)
						if mainWin.isShowingPage(mainWin.riderDetail):
							mainWin.riderDetail.setBib(bib)
							wx.CallAfter( mainWin.riderDetail.refresh )
						wx.CallAfter( self.refresh )
				elif newbib == bib:
					Utils.MessageOK( self, 'Rider #' + str(bib) + ' ' + database.getRiderName(bib, True) + ' bib unchanged.', title='Did not change bib')
				else:
					Utils.MessageOK( self, 'Rider #' + str(newbib) + ' is ' + database.getRiderName(newbib, True) + '!', title='Failed to change bib')
		
	def deleteRider( self, event, bib ):
		database = Model.database
		if database is None:
			return
		if bib is None:
			with wx.NumberEntryDialog(self, 'Enter number for rider to delete:', 'Bib#:', 'Delete rider', 0, 1, 65535) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					bib = dlg.GetValue()
				else:
					return
		if database.isRider( bib ):
			if Utils.MessageOKCancel( self, 'Are you sure you want to delete #' + str(bib) + ' ' + database.getRiderName(bib, True) + '?\nThis deletes their tag data!\nThey will no longer be included in sign-on sheets for existing events.', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
				Utils.writeLog('Delete rider: ' + str(bib))
				with Model.LockDatabase() as db:
					db.deleteRider(int(bib))
				if mainWin.isShowingPage(mainWin.riderDetail):
					mainWin.riderDetail.setBib(bib)
					wx.CallAfter( mainWin.riderDetail.refresh )
				wx.CallAfter( self.refresh )
		else:
			Utils.MessageOK( self, 'Rider #' + str(bib) + ' does not exist!', title='Failed to delete rider')
			
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
			self.riderCount.SetLabel('No database')
			return
		
		#initial forward sort by bib
		riders = dict(sorted(database.getRiders().items()))
		
		self.riderCount.SetLabel(os.path.basename(database.fileName) + ': ' + str(len(riders)) + ' riders available')
		
		now = datetime.datetime.now().timestamp()
		
		if self.sortBy == 1: # first name
			lastNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['LastName'], reverse=self.reverseSort))
			sortedRiders = dict(sorted(lastNameSortedRiders.items(), key=lambda item: item[1]['FirstName'], reverse=self.reverseSort))
		elif self.sortBy == 2: # last Name
			firstNameSortedRiders = dict(sorted(riders.items(), key=lambda item: item[1]['FirstName'], reverse=self.reverseSort))
			sortedRiders = dict(sorted(firstNameSortedRiders.items(), key=lambda item: item[1]['LastName'], reverse=self.reverseSort))
		elif self.sortBy == 3: # Gender
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['Gender']) if 'Gender' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 4: # Age
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['DOB']) if 'DOB' in item[1] else now, reverse=self.reverseSort))
		elif self.sortBy == 5: # Natcode
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['NatCode']) if 'NatCode' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 6: # License
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['License']) if 'License' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 7: # Factor
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['Factor']) if 'Factor' in item[1] else 1, reverse=self.reverseSort))
		elif self.sortBy == 8: # Team
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['Team']) if 'Team' in item[1] else '', reverse=self.reverseSort))
		elif self.sortBy == 9: # Last entered
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['LastEntered']) if 'LastEntered' in item[1] else 0, reverse=self.reverseSort))
		elif self.sortBy == 10: # Last tag
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (database.getLastTagWritten(item[1])) if database.getLastTagWritten(item[1]) is not None else 0, reverse=self.reverseSort))
		elif self.sortBy == 11: # Notes
			sortedRiders = dict(sorted(riders.items(), key=lambda item: (item[1]['Notes']) if 'Notes' in item[1] else '', reverse=self.reverseSort))
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
			self.ridersGrid.SetCellValue(row, col, database.getRiderFirstName(bib))
			col+=1
			self.ridersGrid.SetCellValue(row, col, database.getRiderLastName(bib))
			col+=1
			self.ridersGrid.SetCellValue(row, col, Model.Genders[rider['Gender']] if 'Gender' in rider else '')
			col+=1
			age = ''
			self.ridersGrid.SetCellValue(row, col, str(database.getRiderAge(bib)) if database.getRiderAge(bib) else '' )
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
			col+=1
			self.ridersGrid.SetCellRenderer(row, col, IOCCodeRenderer() )
			self.ridersGrid.SetCellValue(row, col, rider['NatCode'] if 'NatCode' in rider else '')
			col+=1
			self.ridersGrid.SetCellValue(row, col, rider['License'] if 'License' in rider else '')
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			col+=1
			self.ridersGrid.SetCellValue(row, col, str(rider['Factor']) if 'Factor' in rider else '')
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			col+=1
			self.ridersGrid.SetCellValue(row, col, rider['Team'] if 'Team' in rider else '')
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
			col+=1
			if 'LastEntered' in rider and rider['LastEntered']:
				dt = '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(rider['LastEntered']))
				self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			else:
				dt = ''
			self.ridersGrid.SetCellValue(row, col, str(dt))
			col+=1
			dt = '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(database.getLastTagWritten(rider))) if database.getLastTagWritten(rider) is not None else ''
			self.ridersGrid.SetCellValue(row, col, dt)
			self.ridersGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			col+=1
			self.ridersGrid.SetCellValue(row, col, rider['Notes'] if 'Notes' in rider else '')
			
		self.ridersGrid.AutoSizeColumns()
