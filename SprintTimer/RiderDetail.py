import wx
import wx.lib.intctrl as intctrl
import Utils
from Utils				import logCall
import Model
from ReadSignOnSheet import GetTagNums, TagFields
import Flags

class RiderDetail( wx.Panel ):
	yellowColour = wx.Colour( 255, 255, 0 )
	orangeColour = wx.Colour( 255, 165, 0 )
	ignoreColour = wx.Colour( 180, 180, 180 )
		
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.SetDoubleBuffered( True )
		
		self.idCur = 0

		self.bib = None
		self.iLap = None
		self.entry = None
		self.firstCall = True
		
		self.visibleRow = None
		
		labelAlign = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
		
		hs = wx.BoxSizer( wx.VERTICAL )
		
		gbs = wx.GridBagSizer(7, 4)
		row = 0
		self.bibName = wx.StaticText( self, label = '{}: '.format(_('Bib')) )
		gbs.Add( self.bibName, pos=(row,0), span=(1,1), flag=labelAlign )
		self.bib = intctrl.IntCtrl( self, min=0, max=9999, allow_none=True, style=wx.TE_RIGHT | wx.TE_PROCESS_ENTER )
		self.bib.Bind( wx.EVT_TEXT, self.onbibChange )
		gbs.Add( self.bib, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		GetTranslation = _
		self.statusName = wx.StaticText( self, label = '{}: '.format(_('Status')) )
		gbs.Add( self.statusName, pos=(row,2), span=(1,1), flag=labelAlign )
		self.statusOption = wx.Choice( self, choices=[GetTranslation(n) for n in Model.Rider.statusNames], size=(150,-1) )
		gbs.Add( self.statusOption, pos=(row,3), span=(1,2), flag=wx.EXPAND )
		self.Bind(wx.EVT_CHOICE, self.onStatusChanged, self.statusOption)
		
		row += 1
		
		self.nameName = wx.StaticText( self, label = '{}: '.format(_('Name')) )
		gbs.Add( self.nameName, pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderName = wx.StaticText( self )
		gbs.Add( self.riderName, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		self.genderName = wx.StaticText( self, label = '{}: '.format(_('Gender')) )
		gbs.Add( self.genderName, pos=(row,2), span=(1,1), flag=labelAlign )
		self.riderGender = wx.StaticText( self )
		gbs.Add( self.riderGender, pos=(row,3), span=(1,2), flag=wx.EXPAND )
		
		row += 1
		
		self.machineName = wx.StaticText( self, label = '{}: '.format(_('Machine')) )
		gbs.Add( self.machineName, pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderMachine = wx.StaticText( self )
		gbs.Add( self.riderMachine, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		self.ageName = wx.StaticText( self, label = '{}: '.format(_('Age')) )
		gbs.Add( self.ageName, pos=(row,2), span=(1,1), flag=labelAlign )
		self.riderAge = wx.StaticText( self )
		gbs.Add( self.riderAge, pos=(row,3), span=(1,2), flag=wx.EXPAND )
		
		row += 1
		
		self.teamName = wx.StaticText( self, label = '{}: '.format(_('Team')) )
		gbs.Add( self.teamName, pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderTeam = wx.StaticText( self )
		gbs.Add( self.riderTeam, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		self.natcodeName = wx.StaticText( self, label = '{}: '.format(_('Nat')) )
		gbs.Add( self.natcodeName, pos=(row,2), span=(1,1), flag=labelAlign )
		self.riderNat = wx.StaticText( self )
		gbs.Add( self.riderNat, pos=(row,3), span=(1,1), flag=wx.EXPAND )
		self.riderFlag = wx.StaticBitmap(self, -1, wx.NullBitmap, size=(44,28))
		gbs.Add( self.riderFlag, pos=(row,4), span=(1,1), flag=wx.EXPAND )
		row += 1
		
		self.categoryName = wx.StaticText( self, label = '{}: '.format(_('Categories')) )
		gbs.Add( self.categoryName, pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP )
		self.category = wx.StaticText( self, label='' )
		gbs.Add( self.category, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		tagsfont = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.tagsName = wx.StaticText( self, label = '{}: '.format(_('Tag(s)')) )
		gbs.Add( self.tagsName, pos=(row,2), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_TOP )
		self.tags = wx.StaticText( self, style=wx.ALIGN_RIGHT )
		self.tags.SetFont(tagsfont)
		
		gbs.Add( self.tags, pos=(row,3), span=(1,3), flag=wx.EXPAND )
		hs.Add( gbs, proportion = 0 )
		
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		mainSizer.Add( hs, 1, flag=wx.EXPAND|wx.ALL, border=4 )
		self.SetSizer( mainSizer )
		self.hs = hs
	
	def onbibChange( self, event = None ):
		self.refresh()

	@logCall
	def onStatusChanged( self, event ):
		bib = self.bib.GetValue()
		race = Model.race
		if not race:
			return
		if bib not in race.riders:
			return
		statusOption = self.statusOption.GetSelection()
		race.setRiderStatus( bib, statusOption )
		race.setChanged()
		wx.CallAfter( self.refresh )
		
	def setRider( self, n = None ):
		Utils.SetValue( self.bib, int(n) if n is not None else None )

	def setbibSelect( self, bib ):
		self.setRider( bib )
	
	def refresh( self, forceUpdate=False ):
		bib = self.bib.GetValue()
		
		self.category.SetLabel('')
		self.riderName.SetLabel( '' )
		self.riderGender.SetLabel( '' )
		self.riderAge.SetLabel( '' )
		self.riderNat.SetLabel( '' )
		self.riderFlag.SetBitmap(wx.NullBitmap)
		self.riderMachine.SetLabel( '' )
		self.riderTeam.SetLabel( '' )
		self.tags.SetLabel( '' )
		
		tagNums = GetTagNums()
		
		with Model.LockRace() as race:
		
			if race is None or bib is None:
				return
				
			try:
				externalInfo = race.excelLink.read()
			except AttributeError:
				externalInfo = {}
			
			info = externalInfo.get(int(bib), {})
			riderName = ', '.join( n for n in [info.get('LastName', ''), info.get('FirstName', '')] if n )
			
			self.riderName.SetLabel( riderName )
			self.riderGender.SetLabel( '{}'.format(info.get('Gender', '')) )
			self.riderAge.SetLabel( '{}'.format(info.get('Age', '')) )
			
			natCode = info.get('NatCode', '')
			self.riderNat.SetLabel( '{}'.format(natCode) )
			image = Flags.GetFlagImage( natCode )
			if image:
				self.riderFlag.SetBitmap(image.Scale(44, 28, wx.IMAGE_QUALITY_HIGH) )
			
			self.riderTeam.SetLabel( '{}'.format(info.get('Team', '')) )
			self.riderMachine.SetLabel( '{}'.format(info.get('Machine', '')) )
			
			categories = race.getAllCategories()
			catList = []
			for category in categories:
				if race.inCategory(bib, category):
					catList.append(category.fullname)

			if catList:
				self.category.SetLabel(',\n'.join(catList))
			
			tags = []
			for tagName in TagFields:
				try:
					tags.append( '{}'.format(info[tagName]).lstrip('0').upper() )
				except (KeyError, ValueError):
					pass
			if tags:
				output = ''
				for i, m in enumerate(tags, 1):  
					output += (m.rjust(24) + [',', ',\n'][i % 2 == 0])
				self.tags.SetLabel( output )
			
			if bib not in race.riders:
				return
				
			self.statusOption.SetSelection( race.getRiderStatus( bib ) )
			
			self.Layout()
			
	def commit( self ):
		pass
		

