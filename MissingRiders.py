import wx
import Utils
import Model
from EditEntry import DoDNF, DoDNS, DoPull, DoDQ
from NumKeypad import getRiderNumsFromText, enterCodes, validKeyCodes
from ReorderableGrid import ReorderableGrid
import wx.grid as gridlib

class MissingRiders( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__( parent, id, _("Missing Riders"),
						style=wx.DEFAULT_DIALOG_STYLE|wx.TAB_TRAVERSAL|wx.STAY_ON_TOP )
		
		self.headerNames = ['Bib', 'Name', 'Status']
		
		self.showStrayRiders = wx.CheckBox( self, label='&Show stray riders' )
		self.showStrayRiders.SetToolTip('Include riders we have times for who are not in the sign-on spreadsheet')
		self.showStrayRiders.SetValue( True )
		self.showStrayRiders.Bind( wx.EVT_CHECKBOX, self.refresh )
		
		self.refreshButton = wx.Button(self, label='&Refresh')
		self.refreshButton.SetToolTip('Update the list')
		self.refreshButton.Bind( wx.EVT_BUTTON, self.refresh )
		
		self.grid = ReorderableGrid( self, style = wx.BORDER_SUNKEN )
		self.grid.DisableDragRowSize()
		self.grid.CreateGrid( 0, len(self.headerNames) )
		self.grid.SetColFormatBool( 7 )
		self.grid.SetColLabelSize( 64 )
		self.grid.SetRowLabelSize( 0 )
		self.grid.EnableReorderRows( False )
		#self.grid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.doCellRightClick )
		#self.grid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.doCellClick )
		self.sortCol = None
		
		self.mainSizer = wx.BoxSizer( wx.VERTICAL )
		hbs = wx.BoxSizer( wx.HORIZONTAL )
		hbs.Add( self.showStrayRiders, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border=2 )
		hbs.AddStretchSpacer()
		hbs.Add( self.refreshButton, flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALL, border=2 )
		self.mainSizer.Add( hbs, flag=wx.EXPAND|wx.TOP|wx.ALL, border = 4)
		self.mainSizer.Add( self.grid, flag=wx.EXPAND|wx.TOP|wx.ALL, border = 4)
		self.SetSizerAndFit( self.mainSizer )
		
		self.refresh()
		
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
		
		# Get everyone in the spreadsheet without a time...
		for bib in externalInfo:
			rider = race.getRider( bib )
			riderInfo = externalInfo.get(int(bib), {})
			riderName = ', '.join( n for n in [riderInfo.get('LastName', ''), riderInfo.get('FirstName', '')] if n)
			#if rider.status == Finisher and not rider.times:
				#status = 'Unseen'
			#else:
				#status = Model.Rider.statusNames[rider.status]
			if not rider.times:
				status = Model.Rider.statusNames[rider.status] if rider.status != Finisher else 'Unseen'
				riderList.update({bib:[str(riderName), status, False]})
		
		# Get everyone in the race without a spreadsheet entry...
		if self.showStrayRiders.GetValue():
			for bib, rider in race.riders.items():
				status = Model.Rider.statusNames[rider.status]
				if rider.times:
					if not externalInfo.get(bib):
						riderList.update({bib:['', status, True]})
		
		row = 0
		for bib in sorted(riderList):
			self.grid.InsertRows( pos=row+1, numRows=1)
			self.grid.SetCellValue( row, 0, str(bib) )
			self.grid.SetCellAlignment(row, 0, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE_VERTICAL)
			self.grid.SetCellValue( row, 1, riderList[bib][0] )
			self.grid.SetCellAlignment(row, 1, wx.ALIGN_LEFT, wx.ALIGN_CENTRE_VERTICAL)
			self.grid.SetCellValue( row, 2, riderList[bib][1] )
			if riderList[bib][2]: # Stray rider
				self.grid.SetCellBackgroundColour( row, 0, wx.Colour( 211, 211, 211 ) )
				self.grid.SetCellBackgroundColour( row, 1, wx.Colour( 211, 211, 211 ) )
				self.grid.SetCellBackgroundColour( row, 2, wx.Colour( 211, 211, 211 ) )
			row += 1
				
		self.grid.AutoSize()
		self.GetSizer().Layout()
		self.grid.EnableEditing(True)
		self.grid.ForceRefresh()
		self.Fit()
