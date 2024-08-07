import wx
import wx.adv
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
		
		#joystick capture enable checkbox
		self.joystickEntry = wx.CheckBox(self, label='Auto')
		self.joystickEntry.SetValue(False)
		self.joystickEntry.SetToolTip( wx.ToolTip('Enter bib automatically when triggered by Joystick device') )
		
		self.hbs.Add( self.joystickEntry, (0, 5), flag=wx.EXPAND)
		
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
		
		# Function key accelerators for buttons
		accTable = [(wx.ACCEL_NORMAL, wx.WXK_F1 + i, self.quickButtons[i].GetId()) for i in range(min(11,len(self.quickButtons)))]
		for i, btn in enumerate(self.quickButtons):
			self.Bind(wx.EVT_MENU, lambda event, i=i: self.doQuickBib(i), id=btn.GetId())
		# Ctrl+Fn to set bib
		for i in range (min(11,len(self.quickButtons))):
			id = wx.NewIdRef().GetId()
			accTable.append((wx.ACCEL_CTRL, wx.WXK_F1 + i, id))
			self.Bind(wx.EVT_MENU, lambda event, i=i: self.onRightClick(i), id=id)
		# F6 to show/hide quick buttons
		id = wx.NewIdRef().GetId()
		accTable.append((wx.ACCEL_NORMAL, wx.WXK_F6, id))
		self.Bind(wx.EVT_MENU, self.onBibsButton, id=id)
		# Ctrl-P to populate quick buttons
		id = wx.NewIdRef().GetId()
		accTable.append((wx.ACCEL_CTRL, ord('p'), id))
		self.Bind(wx.EVT_MENU, self.populateBibs, id=id)
		aTable = wx.AcceleratorTable( accTable )
		self.SetAcceleratorTable(aTable)
		
		# Add joystick capture
		self.joystick = wx.adv.Joystick()
		self.joystick.SetCapture( self )
		self.Bind(wx.EVT_JOY_BUTTON_DOWN, self.onJoystickButton)
		self.Bind(wx.EVT_SHOW, self.onShow)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		
	def handleNumKeypress(self, event):
		keycode = event.GetKeyCode()
		if keycode in enterCodes:
			self.onEnterPress()
		elif keycode < 255:
			if keycode in validKeyCodes:
				event.Skip()
		else:
			event.Skip()
			
	def onJoystickButton( self, event ):
		if not self.joystickEntry.IsChecked():
			return
		if event.ButtonIsDown( wx.JOY_BUTTON2 ):
			self.onEnterPress()
	
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
			self.setNameToolTip(bib, self.quickButtons[i])
		else:
			self.quickBibs[i] = ''
			self.quickButtons[i].SetLabel( '' )
			self.quickButtons[i].SetToolTip('Right-click to set bib')
		self.hbs.Layout()
		self.Fit()
		wx.CallAfter( self.numEdit.SetValue, '' )
		
	def canAddBib( self, bib ):
		for i in range(len(self.quickBibs)):
			if self.quickBibs[i] == bib:  # If we have the bib already...
				return False
			if self.quickBibs[i] == '':  # If we have an empty button...
				return True
		return False
		
	def populateBibs( self, event=None, bib=None ):
		race = Model.race
		if bib:
			for i in range(len(self.quickBibs)):
				if self.quickBibs[i] == '':
					self.quickBibs[i] = bib
					self.quickButtons[i].SetLabel( str(self.quickBibs[i]).center(3, ' ') )
					self.setNameToolTip(bib, self.quickButtons[i])
					break
		elif race:
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
							self.setNameToolTip(bib, self.quickButtons[i])
							i += 1
						else:
							break
						
	def setNameToolTip( self, bib=None, btn=None ):
		if not btn:
			return
		if bib:
			# Try to get the rider's name for tooltip
			race = Model.race
			riderName = None
			if race:
				try:
					externalInfo = race.excelLink.read()
					info = externalInfo.get(int(bib), {})
					riderName = ', '.join( n for n in [info.get('LastName', ''), info.get('FirstName', '')] if n )
				except AttributeError:
					pass
			if riderName:
				btn.SetToolTip( riderName )
			else:
				btn.SetToolTip( '#' + str(bib) )
		else:
			btn.SetToolTip( 'Right-click to set bib' )
			
	def onShow(self, event):
		race = Model.race
		if race and race.isTimeTrial:
			self.hbs.Show(self.joystickEntry)
		else:
			self.joystickEntry.SetValue(False)
			self.hbs.Hide(self.joystickEntry)
		self.Fit()
			
	def onClose(self, event):
		self.joystickEntry.SetValue(False)
		event.Skip()
		
if __name__ == '__main__':
	app = wx.App(False)
	mainWin = wx.Frame(None,title="CrossMan", size=(1024,600))
	bibEnter = BibEnter(mainWin)
	Model.newRace()
	Model.race.enableJChipIntegration = False
	Model.race.isTimeTrial = False
	bibEnter.Show()
	app.MainLoop()
	
