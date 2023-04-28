import wx
import Utils
import Model
import os
from EditEntry import DoDNS, DoDQ
from NumKeypad import getRiderNumsFromText, enterCodes, validKeyCodes
from ReorderableGrid import ReorderableGrid
from RiderDetail import ShowRiderDetailDialog
from Undo import undo
import wx.grid as gridlib

class MissingRiders( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY):
		displaySize = list( wx.GetDisplaySize() )
		size = (min(displaySize[0], 640), displaySize[1]/2)
		super().__init__( parent, id, _("Missing Riders"), size=size, pos=wx.DefaultPosition, 
			style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX )
		
		# Set the upper left icon.
		icon = wx.Icon( os.path.join(Utils.getImageFolder(), 'CrossMgr16x16.ico'), wx.BITMAP_TYPE_ICO )
		self.SetIcon( icon )
		
		self.SetLayoutAdaptationMode(wx.DIALOG_ADAPTATION_MODE_ENABLED)
		
		self.headerNames = ['Bib', 'Name', 'Machine', 'Team', 'Status']
		
		self.showStrayRiders = wx.CheckBox( self, label='&Show unmatched riders' )
		self.showStrayRiders.SetToolTip('Include riders we have times for who are not in the sign-on spreadsheet.  RFID tags which do not have a rider associated with them can be seen in the \'Unmatched RFID Tags\' window.')
		self.showStrayRiders.SetValue( True )
		self.showStrayRiders.Bind( wx.EVT_CHECKBOX, self.refresh )
		
		#self.refreshButton = wx.Button(self, label='&Refresh')
		#self.refreshButton.SetToolTip('Update the list')
		#self.refreshButton.Bind( wx.EVT_BUTTON, self.refresh )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.CreateGrid( 0, len(self.headerNames) )
		#self.grid.SetColLabelSize( 32 )
		self.grid.SetRowLabelSize( 0 )
		self.grid.EnableReorderRows( False )
		self.grid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.doCellRightClick )
		self.grid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.doCellDoubleClick )
		
		self.mainSizer = wx.BoxSizer( wx.VERTICAL )
		hbs = wx.BoxSizer( wx.HORIZONTAL )
		hbs.Add( self.showStrayRiders, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border=2 )
		hbs.AddStretchSpacer()
		#hbs.Add( self.refreshButton, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border=2 )
		self.mainSizer.Add( hbs, flag=wx.EXPAND|wx.TOP|wx.ALL, border = 4)
		self.mainSizer.Add( self.grid, flag=wx.EXPAND|wx.TOP|wx.ALL, border = 4)
		self.SetSizer( self.mainSizer )
		
		self.refresh()
		self.Fit()
		
	def doCellDoubleClick( self, event ):
		ShowRiderDetailDialog( self, self.bibNames[event.GetRow()][0] )
		wx.CallAfter( self.refresh )
		
	def doCellRightClick( self, event ):
		bib, name = self.bibNames[event.GetRow()]
		menu = wx.Menu()
		item = menu.Append( wx.ID_ANY, '#' + str(bib) + ' ' +  name, 'Rider Detail...' )
		self.Bind( wx.EVT_MENU, lambda evt: self.riderDetailCallback(bib), item )
		item = menu.Append( wx.ID_ANY, 'Set DNS', 'Set DNS...' )
		self.Bind( wx.EVT_MENU, lambda evt: self.setDNSCallback(bib), item )
		item = menu.Append( wx.ID_ANY, 'Set DQ', 'Set DQ...' )
		self.Bind( wx.EVT_MENU, lambda evt: self.setDQCallback(bib), item )
		item = menu.Append( wx.ID_ANY, 'Delete Rider', 'Delete rider...' )
		self.Bind( wx.EVT_MENU, lambda evt: self.deleteRider(bib), item )
		
		self.PopupMenu( menu )
		
	def riderDetailCallback( self, bib ):
		ShowRiderDetailDialog( self, bib )
		wx.CallAfter( self.refresh )
	
	def setDNSCallback( self, bib ):
		DoDNS( self, bib )
		wx.CallAfter( self.refresh )
		
	def setDQCallback( self, bib ):
		DoDQ( self, bib )
		wx.CallAfter( self.refresh )
		
	def deleteRider( self, bib ):
		if not Model.race:
			return
			
		with Model.LockRace() as race:
			if not bib in race:
				wx.CallAfter( self.refresh )
				return
			
		if Utils.MessageOKCancel( self, '{}: {}: {}'.format(_('Bib'), bib, _("Confirm Delete")), _("Delete Rider") ):
			undo.pushState()
			with Model.LockRace() as race:
				race.deleteRider( bib )
			wx.CallAfter( self.refresh )
			wx.CallAfter( Utils.refreshForecastHistory )
			wx.CallAfter( Utils.refresh )
		
	def refresh( self, event=None ):
		Finisher = Model.Rider.Finisher
		race = Model.race
		if not race:
			return
		
		try:
			externalInfo = race.excelLink.read()
		except Exception:
			return
		
		self.grid.ClearGrid()
		if (self.grid.GetNumberRows() > 0):
			self.grid.DeleteRows( 0, self.grid.GetNumberRows() )
		for col, headerName in enumerate(self.headerNames):
			self.grid.SetColLabelValue( col, headerName )
			attr = gridlib.GridCellAttr()
			attr.SetAlignment( wx.ALIGN_CENTRE, wx.ALIGN_TOP )
			attr.SetReadOnly( True )
			self.grid.SetColAttr( col, attr )
		
		riderList = {}
		self.bibNames = []
		showMachineCol = False
		showTeamCol = False
		
		# Get everyone in the spreadsheet without a time...
		for bib in externalInfo:
			rider = race.getRider( bib )
			riderInfo = externalInfo.get(int(bib), {})
			riderName = ', '.join( n for n in [riderInfo.get('LastName', ''), riderInfo.get('FirstName', '')] if n)
			riderMachine = riderInfo.get('Machine')
			if riderMachine:
				showMachineCol = True
			riderTeam = riderInfo.get('Team')
			if riderTeam:
				showTeamCol = True
			if not rider.times:
				if rider.status == Finisher:
					riderList.update({bib:[riderName, riderMachine, riderTeam, 'Unseen', 1]})
				else:
					status = Model.Rider.statusNames[rider.status]
					riderList.update({bib:[riderName, riderMachine, riderTeam, status, 0]})
					
		# Get everyone in the race without a spreadsheet entry...
		if self.showStrayRiders.GetValue():
			for bib, rider in race.riders.items():
				status = Model.Rider.statusNames[rider.status]
				if rider.times:
					if not externalInfo.get(bib):
						riderList.update({bib:['', '', '', status, 2]})
		row = 0
		for bib in sorted(riderList):
			self.bibNames.append((bib, riderList[bib][0]))
			self.grid.InsertRows( pos=row+1, numRows=1)
			self.grid.SetCellValue( row, 0, str(bib) )
			self.grid.SetCellAlignment(row, 0, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE_VERTICAL)
			self.grid.SetCellValue( row, 1, riderList[bib][0] )
			self.grid.SetCellAlignment(row, 1, wx.ALIGN_LEFT, wx.ALIGN_CENTRE_VERTICAL)
			self.grid.SetCellValue( row, 2, riderList[bib][1] )
			self.grid.SetCellAlignment(row, 2, wx.ALIGN_LEFT, wx.ALIGN_CENTRE_VERTICAL)
			self.grid.SetCellValue( row, 3, riderList[bib][2] )
			self.grid.SetCellAlignment(row, 3, wx.ALIGN_LEFT, wx.ALIGN_CENTRE_VERTICAL)
			self.grid.SetCellValue( row, 4, riderList[bib][3] )
			self.grid.SetCellAlignment(row, 4, wx.ALIGN_LEFT, wx.ALIGN_CENTRE_VERTICAL)
			# Colour rows in table
			for i in range(len(self.headerNames)):
				if riderList[bib][4] == 1: # Missing rider:
					self.grid.SetCellBackgroundColour( row, i, wx.Colour( 255, 255, 0 ) )
				elif riderList[bib][4] == 2: # Stray rider
					self.grid.SetCellBackgroundColour( row, i, wx.Colour( 211, 211, 211 ) )
				else:
					self.grid.SetCellBackgroundColour( row, i, wx.Colour( 255, 255, 255 ) )
			row += 1
		
		if showMachineCol:
			self.grid.ShowCol(2)
		else:
			self.grid.HideCol(2)
			
		if showTeamCol:
			self.grid.ShowCol(3)
		else:
			self.grid.HideCol(3)
		
		self.grid.AutoSize()
		self.Layout()
		self.grid.EnableEditing(True)
		self.grid.ForceRefresh()
