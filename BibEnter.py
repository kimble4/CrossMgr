import wx
import Utils
import Model
from EditEntry import DoDNF, DoDNS, DoPull, DoDQ
from NumKeypad import getRiderNumsFromText, enterCodes, validKeyCodes

class BibEnter( wx.Dialog ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__( parent, id, _("Bib Enter"),
						style=wx.DEFAULT_DIALOG_STYLE|wx.TAB_TRAVERSAL|wx.STAY_ON_TOP )
		
		self.quickBibs = [ '', '', '', '', '' ]
		
		self.quickButtons = []
		self.showQuickButtons = False

		fontPixels = 20
		font = wx.Font((0,fontPixels), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
						
		self.numEditLabel = wx.StaticText(self, label='{}'.format(_('Bib')))
		self.numEdit = wx.TextCtrl( self, style=wx.TE_RIGHT | wx.TE_PROCESS_ENTER )
		self.numEdit.Bind( wx.EVT_CHAR, self.handleNumKeypress )

		for w in (self.numEditLabel, self.numEdit):
			w.SetFont( font )
		
		nes = wx.BoxSizer( wx.HORIZONTAL )
		nes.Add( self.numEditLabel, flag=wx.ALIGN_CENTRE_VERTICAL )
		nes.Add( self.numEdit, 1, flag=wx.LEFT|wx.EXPAND, border=4 )
		
		self.hbs = wx.GridBagSizer( 2, 2 )
		for i, (label, actionFn) in enumerate( ((_('DN&F'),DoDNF), (_('DN&S'),DoDNS), (_('&Pull'),DoPull), (_('D&Q'),DoDQ)) ):
			btn = wx.Button( self, label=label, style=wx.BU_EXACTFIT )
			btn.SetFont( font )
			btn.Bind( wx.EVT_BUTTON, lambda event, fn = actionFn: self.doAction(fn) )
			self.hbs.Add( btn, (0, i), flag=wx.EXPAND )
		self.bibs = wx.Button( self, label='...', style=wx.BU_EXACTFIT )
		self.bibs.SetFont( font )
		self.bibs.SetToolTip('Show/hide quick bib entry')
		self.bibs.Bind( wx.EVT_BUTTON, self.onBibsButton )
		self.hbs.Add( self.bibs, (0, 4), flag=wx.EXPAND)
		
		for index, bib in enumerate( self.quickBibs ):
			btn = wx.Button( self, label=str(bib), style=wx.BU_EXACTFIT )
			btn.SetFont( font )
			btn.SetToolTip('Right-click to set bib')
			btn.Bind( wx.EVT_BUTTON, lambda event, i=index: self.doQuickBib(i) )
			btn.Bind( wx.EVT_RIGHT_DOWN,lambda event, i=index: self.onRightClick(i), btn)
			self.quickButtons.append(btn)
			self.hbs.Add( btn, (1, index), flag=wx.EXPAND )
			self.hbs.Hide(btn)

		self.mainSizer = wx.BoxSizer( wx.VERTICAL )
		self.mainSizer.Add( nes, flag=wx.ALL|wx.EXPAND, border=2 )
		self.mainSizer.Add( self.hbs, flag=wx.ALL, border=2 )
		self.SetSizerAndFit( self.mainSizer )
		
		accTable = [(wx.ACCEL_NORMAL, wx.WXK_F1 + i, self.quickButtons[i].GetId()) for i in range(min(11,len(self.quickButtons)))]
		print(accTable)
		aTable = wx.AcceleratorTable( accTable )
		self.SetAcceleratorTable(aTable)
		for index, btn in enumerate(self.quickButtons):
			self.Bind(wx.EVT_MENU, lambda event, i=index: self.doQuickBib(i), id=btn.GetId())
		
	def handleNumKeypress(self, event):
		keycode = event.GetKeyCode()
		if keycode in enterCodes:
			self.onEnterPress()
		elif keycode < 255:
			if keycode in validKeyCodes:
				event.Skip()
		else:
			event.Skip()
	
	def onEnterPress( self, event = None ):
		nums = getRiderNumsFromText( self.numEdit.GetValue() )
		if nums:
			mainWin = Utils.getMainWin()
			if mainWin is not None:
				mainWin.forecastHistory.logNum( nums )
		wx.CallAfter( self.numEdit.SetValue, '' )
	
	def doAction( self, action ):
		race = Model.race
		t = race.curRaceTime() if race and race.isRunning() else None
		success = False
		for num in getRiderNumsFromText( self.numEdit.GetValue() ):
			if action(self, num, t):
				success = True
		if success:
			self.numEdit.SetValue( '' )
			wx.CallAfter( Utils.refreshForecastHistory )
			
	def onBibsButton( self, event=None ):
		self.showQuickButtons = not self.showQuickButtons
		if self.showQuickButtons:
			for btn in self.quickButtons:
				self.hbs.Show(btn)
		else:
			for btn in self.quickButtons:
				self.hbs.Hide(btn)
		self.Fit()
		
	def doQuickBib( self,  i ):
		bib = self.quickBibs[i]
		if bib:
			mainWin = Utils.getMainWin()
			if mainWin is not None:
				mainWin.forecastHistory.logNum( bib )
		
	def onRightClick(self, i ):
		bib = self.numEdit.GetValue()
		if bib:
			self.quickBibs[i] = int(bib)
			self.quickButtons[i].SetLabel( str(self.quickBibs[i]).center(3, ' ') )
			self.hbs.Layout()
			self.Fit()
			wx.CallAfter( self.numEdit.SetValue, '' )
		
	def populateBibs( self ):
		race = Model.race
		if race:
			riders = Model.race.riders
			if riders:
				i = 0
				for bib in sorted(riders):
					if riders[bib].status == Model.Rider.Finisher:
						while i < len(self.quickBibs) and self.quickBibs[i] != '':
							i += 1
						if i < len(self.quickBibs):
							self.quickBibs[i] = bib
							self.quickButtons[i].SetLabel( str(self.quickBibs[i]).center(3, ' ') )
							i += 1
						else:
							break
				
		
if __name__ == '__main__':
	app = wx.App(False)
	mainWin = wx.Frame(None,title="CrossMan", size=(1024,600))
	bibEnter = BibEnter(mainWin)
	Model.newRace()
	Model.race.enableJChipIntegration = False
	Model.race.isTimeTrial = False
	bibEnter.Show()
	app.MainLoop()
	
