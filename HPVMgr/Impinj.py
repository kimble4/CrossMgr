import wx
import wx.adv
import wx.lib.intctrl
import wx.lib.masked			as masked
import wx.lib.agw.hyperlink as hl
import re
import os
import sys
import time
import datetime
import traceback
import secrets

import Utils

from pyllrp import *
from pyllrp.TagInventory import TagInventory
from pyllrp.AutoDetect import AutoDetect

from TagWriterCustom import TagWriterCustom
from AdvancedDialog import AdvancedDialog

ImpinjHostNamePrefix = 'SpeedwayR-'
ImpinjHostNameSuffix = '.local'
ImpinjInboundPort = 5084

if 'WXMSW' in wx.Platform:
	IpAddrCtrl = masked.IpAddrCtrl
else:
	class IpAddrCtrl( wx.TextCtrl ):
		def GetAddress( self ):
			ipaddress = self.GetValue()
			return ipaddress.strip()

def toInt( s, d = 1 ):
	try:
		n = int(s)
	except ValueError:
		n = d
	return n

class TemplateValidator(wx.Validator):
	validChars = set( '0123456789ABCDEF#' )

	def __init__( self ):
		wx.Validator.__init__(self)
		self.Bind(wx.EVT_CHAR, self.OnChar)

	def Clone(self):
		return TemplateValidator()

	def Validate(self, win):
		tc = self.GetWindow()
		val = tc.GetValue()
		return all( x in self.validChars for x in val )

	def OnChar(self, event):
		key = event.GetKeyCode()

		if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
			event.Skip()
			return

		if chr(key) in self.validChars:
			event.Skip()
			return
			
		if not wx.Validator_IsSilent():
			wx.Bell()

class Impinj( wx.Panel ):
	
	EPCHexCharsMax = 24
	
	StatusIdle, StatusError, StatusSuccess, StatusAttempt = [0, 1, 2, 3]
	
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		self.parent = parent
		
		self.LightGreen = wx.Colour(153,255,153)
		self.LightRed = wx.Colour(255,153,153)
		self.Grey = wx.Colour(80,80,80)
		
		self.tagWriter = None
		self.status = self.StatusIdle
		self.destination = None
		self.useAntenna = 0
		
		bigFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		vs = wx.BoxSizer( wx.VERTICAL )
		
		gbs = wx.GridBagSizer( 5, 5 )
		
		row = 0
		title = wx.StaticText(self, label='Impinj RFID tag Reading and Writing')
		title.SetFont(bigFont)
		gbs.Add(title, pos=(row,0), span=(1,4), flag=wx.ALIGN_CENTRE|wx.ALIGN_TOP )
		
		row += 1
		self.useHostName = wx.RadioButton( self, label = 'Host Name:', style=wx.RB_GROUP )
		gbs.Add( self.useHostName, pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		hb = wx.BoxSizer( wx.HORIZONTAL )
		hb.Add( wx.StaticText(self, label = ImpinjHostNamePrefix), flag=wx.ALIGN_CENTER_VERTICAL )
		if 'WXMAC' in wx.Platform:
			self.impinjHostName = masked.TextCtrl( self,
								defaultValue = '00-00-00',
								useFixedWidthFont = True,
								size=(120,-1),
							)
		else:
			self.impinjHostName = masked.TextCtrl( self,
								mask         = 'NN-NN-NN',
								defaultValue = '00-00-00',
								useFixedWidthFont = True,
								size=(120,-1),
							)
		hb.Add( self.impinjHostName )
		hb.Add( wx.StaticText(self, label = ImpinjHostNameSuffix), flag=wx.ALIGN_CENTER_VERTICAL )
		hb.Add( wx.StaticText(self, label = ' : ' + '{}'.format(ImpinjInboundPort)), flag=wx.ALIGN_CENTER_VERTICAL )
		gbs.Add( hb, pos=(row,1), span=(1,1), flag=wx.ALIGN_LEFT )
		
		row += 1
		self.useStaticAddress = wx.RadioButton( self, label='IP:' )
		gbs.Add( self.useStaticAddress, pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		hb = wx.BoxSizer( wx.HORIZONTAL )
		self.impinjHost = IpAddrCtrl( self, style=wx.TE_PROCESS_TAB, size=(175,-1) )
		hb.Add( self.impinjHost )
		hb.Add( wx.StaticText(self, label = ' : ' + '{}'.format(ImpinjInboundPort)), flag=wx.ALIGN_CENTER_VERTICAL )

		gbs.Add( hb, pos=(row,1), span=(1,1), flag=wx.ALIGN_LEFT )
		row += 1
		
		self.autoDetectButton = wx.Button(self, label='Auto Detect Reader')
		self.autoDetectButton.SetToolTip( wx.ToolTip( 'Attempt to detect the tag reader automatically' ) )
		self.autoDetectButton.Bind( wx.EVT_BUTTON, self.doAutoDetect )
		gbs.Add( self.autoDetectButton, pos=(row,1), span=(1,2), flag=wx.ALIGN_LEFT )
		row += 1

		fgs = wx.FlexGridSizer( 2, 3, 2, 2 )
		fgs.AddGrowableCol( 1 )
		fgs.Add( wx.StaticText(self, label='Transmit Power:') )
		self.transmitPower_dBm = wx.StaticText( self, label='Max', size=(75,-1), style=wx.ALIGN_RIGHT )
		fgs.Add( self.transmitPower_dBm, flag=wx.LEFT, border=2 )
		fgs.Add( wx.StaticText(self, label='dBm'), flag=wx.LEFT, border=2 )

		fgs.Add( wx.StaticText(self, label='Receive Sensitivity:') )
		self.receiveSensitivity_dB = wx.StaticText( self, label='Max', size=(75,-1), style=wx.ALIGN_RIGHT )
		fgs.Add( self.receiveSensitivity_dB, flag=wx.LEFT, border=2 )
		fgs.Add( wx.StaticText(self, label='dB'), flag=wx.LEFT, border=2 )		
		gbs.Add( fgs, pos=(row, 0), span=(1, 2) )
		
		advancedButton = wx.Button( self, label="Advanced..." )
		advancedButton.SetToolTip( wx.ToolTip( 'Adjust gain parameters and view reader info') )
		advancedButton.Bind( wx.EVT_BUTTON, self.doAdvancedButton )
		gbs.Add( advancedButton, pos=(row, 2), span=(1, 1), flag=wx.ALIGN_CENTRE_VERTICAL )
		gbs.Add(wx.StaticText(self, label='Write antenna:'), pos=(row, 3), span=(1, 1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.antennaChoice = wx.Choice( self, choices=[], name='Antenna selection' )
		self.antennaChoice.Bind( wx.EVT_CHOICE, self.onChooseAntenna )
		gbs.Add( self.antennaChoice, pos=(row, 4), span=(1, 1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL)
		
		row += 1
		gbs.Add( wx.StaticLine(self, style=wx.LI_HORIZONTAL), pos=(row,0), span=(1,4) )
		
		row += 1
		self.writeAllTags = wx.CheckBox(self, label='Write to ALL tags within range')
		self.writeAllTags.SetToolTip(wx.ToolTip( 'If selected, all tags within range will be overwritten simultaneously' ) )
		self.writeAllTags.Bind( wx.EVT_CHECKBOX, self.onWriteAllTagsBox )
		self.writeAllTags.SetValue( False )
		gbs.Add( self.writeAllTags, pos=(row, 3), span=(1,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL)
		
		
		row += 1
		gbs.Add( wx.StaticText( self, label='EPC to write:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.tagToWrite = wx.TextCtrl( self, style=wx.TE_RIGHT|wx.TE_PROCESS_ENTER, size=(360,-1))
		self.tagToWrite.SetToolTip( wx.ToolTip( 'Tag number (Hexadecimal)' ) )
		self.tagToWrite.Bind( wx.EVT_TEXT_ENTER, self.onTagToWriteChanged )
		#self.tagToWrite.Bind( wx.EVT_KILL_FOCUS, self.onTagToWriteChanged )  #seems to become uneditable under windows?
		gbs.Add( self.tagToWrite, pos=(row,1), span=(1,1), flag=wx.ALIGN_LEFT )
		self.epcInfo = wx.StaticText( self, label='' )
		self.epcInfo.SetToolTip( wx.ToolTip( 'Rider associated with this tag' ))
		gbs.Add( self.epcInfo, pos=(row,2), span=(1,2), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		gbs.Add( wx.StaticText(self, label='Destination tag:'), pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		self.destinationTag = wx.StaticText( self, label= 'None' )
		self.destinationTag.SetToolTip( wx.ToolTip( 'Tag that will be overwritten' ) )
		gbs.Add( self.destinationTag, pos=(row,1), span=(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTRE_VERTICAL )
		
		self.writeButton = wx.Button( self, label = 'Write' )
		self.writeButton.SetToolTip( wx.ToolTip( 'Write this EPC to destination tag' ) )
		self.writeButton.Enabled = False
		self.writeButton.Bind( wx.EVT_BUTTON, self.onWriteButton )
		gbs.Add( self.writeButton, pos=(row,2), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.writeSuccess = wx.Gauge( self, style=wx.GA_HORIZONTAL, range = 100 )
		self.writeSuccess.SetToolTip( wx.ToolTip( 'Write progress bar' ) )
		gbs.Add( self.writeSuccess, pos=(row,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		self.readButton = wx.Button( self, label = 'Read Tags' )
		self.readButton.SetToolTip( wx.ToolTip( 'Perform an inventory run') )
		self.readButton.Enabled = False
		self.readButton.Bind( wx.EVT_BUTTON, self.onReadButton )
		gbs.Add( self.readButton, pos=(row,4), span=(1,1), flag=wx.ALIGN_TOP )
		
		
		
		row = 1
		gbs.Add( wx.StaticText(self, label='Reader status:'), pos=(row,2), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.statusLabel = wx.StaticText( self, label = 'Not Connected' )
		self.statusLabel.SetFont(bigFont)
		gbs.Add( self.statusLabel, pos=(row,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		self.resetButton = wx.Button( self, label = 'Connect' )
		self.resetButton.SetToolTip( wx.ToolTip( 'Attempt to connect to the tag reader') )
		self.resetButton.Bind( wx.EVT_BUTTON, self.doReset )
		gbs.Add( self.resetButton, pos=(row,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		self.disconnectButton = wx.Button(self, label='Disconnect')
		self.disconnectButton.SetToolTip( wx.ToolTip( 'Disconnect from the tag reader') )
		self.disconnectButton.Bind( wx.EVT_BUTTON, self.doDisconnect )
		gbs.Add( self.disconnectButton, pos=(row,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		
		vs.Add( gbs, flag=wx.EXPAND)
		
		self.colnames = ['Tag EPC (Hexadecimal)', 'Tag EPC (ASCII printable)', 'Peak RSSI (dB)', 'Antenna' ]
		
		self.tagsGrid = wx.grid.Grid( self )
		self.tagsGrid.CreateGrid(0, len(self.colnames))
		for i, name in enumerate(self.colnames):
			self.tagsGrid.SetColLabelValue(i, name)
		self.tagsGrid.HideRowLabels()
		self.tagsGrid.AutoSize()
		
		self.tagsGrid.SetRowLabelSize( 0 )
		self.tagsGrid.SetMargins( 0, 0 )
		self.tagsGrid.AutoSizeColumns( True )
		self.tagsGrid.DisableDragColSize()
		self.tagsGrid.DisableDragRowSize()
		self.tagsGrid.EnableEditing(False)
		self.tagsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onTagsClick )

		vs.Add( self.tagsGrid, flag=wx.EXPAND )

		self.setWriteSuccess( False )

		#wx.CallAfter( self.doReset )  # hangs on startup without tag reader
		
		self.useHostName.SetValue( True )
		self.useStaticAddress.SetValue( False )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		
	def onTagToWriteChanged( self, event=None ):
		data = self.tagToWrite.GetValue().upper()
		self.tagToWrite.ChangeValue(re.sub('[^0-9A-F]','', data)) #strip non-hex chars
		self.epcInfo.SetLabel('')

	def onChooseAntenna( self, event ):
		self.useAntenna = self.antennaChoice.GetSelection()
		config = Utils.getMainWin().config
		config.WriteInt( 'useAntenna', self.useAntenna )
		config.Flush()

	def onWriteAllTagsBox( self, event ):
		if self.writeAllTags.IsChecked():
			Utils.MessageOK( self,  'All tags within range will be overwritten\nwith the same EPC simultaneously!\nDo NOT use this at the trackside!', 'Warning', iconMask = wx.ICON_WARNING)
			self.destinationTag.SetLabel('ALL visible tags')
			boldFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
			boldFont.SetWeight( wx.FONTWEIGHT_BOLD )
			self.destinationTag.SetFont( boldFont )
		else:
			self.destinationTag.SetLabel('')
			self.destinationTag.SetFont( wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT) )
			
	def onTagsClick( self, event ):
		if not self.writeAllTags.IsChecked():
			row = event.GetRow()
			data = self.tagsGrid.GetCellValue(row, 0)
			self.destination = re.sub('[^0-9A-F]','', data).zfill(self.EPCHexCharsMax) #strip non-hex chars and fill with leading zeros
			self.destinationTag.SetLabel(data)

	def setWriteSuccess( self, success ):
		self.writeSuccess.SetValue( 100 if success else 0 )
	
	reTemplate = re.compile( '#+' )
	def getFormatStr( self ):
		template = self.template.GetValue()
		if '#' not in template:
			template = '#' + template
		
		while True:
			m = self.reTemplate.search( template )
			if not m:
				break
			template = template[:m.start(0)] + '{{n:0{}d}}'.format(len(m.group(0))) + template[m.end(0):]
			
		return template
	
	
	def shutdown( self ):
		if self.tagWriter:
			try:
				self.tagWriter.Disconnect()
			except Exception as e:
				pass
		self.tagWriter = None
		
	def doAdvancedButton( self, event = None ):
		if not self.tagWriter:
			with wx.MessageDialog(self, "You must be connected to an RFID reader.", "Error: not connected to Reader") as md:
				md.ShowModal()
			return
			
		with AdvancedDialog(
				self,
				receive_sensitivity_table=self.tagWriter.receive_sensitivity_table, receive_dB=self.receiveSensitivity_dB.GetLabel(),
				transmit_power_table=self.tagWriter.transmit_power_table, transmit_dBm=self.transmitPower_dBm.GetLabel(),
				general_capabilities=self.tagWriter.general_capabilities,
			) as advDlg:
			if advDlg.ShowModal() == wx.ID_OK:
				r, t = advDlg.get()
				self.receiveSensitivity_dB.SetLabel(r)
				self.transmitPower_dBm.SetLabel(t)
				self.doReset()	

	def doDisconnect(self, event = None ):
		self.shutdown()
		self.setStatus( self.StatusAttempt )

	def doReset( self, event = None ):
		with wx.BusyCursor():
			self.shutdown()
			self.setStatus( self.StatusAttempt )
			
			self.tagWriter = TagWriterCustom( self.getHost() )
			try:
				self.tagWriter.Connect( self.receiveSensitivity_dB.GetLabel(), self.transmitPower_dBm.GetLabel() )
				for k, v in self.tagWriter.general_capabilities:
					if k == 'MaxNumberOfAntennaSupported':
						self.antennaChoice.Clear()
						self.antennaChoice.Append( 'All' )
						self.antennaChoice.AppendItems( [str(i) for i in range( 1, v+1 )] )
						self.antennaChoice.SetSelection(self.useAntenna if self.useAntenna < v else 0 )
				self.writeOptions()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				
				self.setStatus( self.StatusError )
				
				Utils.MessageOK( self, 'Reader Connection Fails to "{}": {}\n\nCheck the reader connection and configuration.\nThen press "Reset Connection"'.format(self.getHost(), e),
								'Reader Connection Fails' )
				self.tagWriter = None
				self.readButton.Disable()
				self.writeButton.Disable()
				return
			self.readButton.Enable()
			self.writeButton.Enable()
			self.setStatus( self.StatusSuccess )
	
	def doAutoDetect( self, event ):
		wx.BeginBusyCursor()
		self.shutdown()
		impinjHost, computerIP = AutoDetect( ImpinjInboundPort )
		wx.EndBusyCursor()
		
		if impinjHost:
			self.useStaticAddress.SetValue( True )
			self.useHostName.SetValue( False )
			
			self.impinjHost.SetValue( impinjHost )
			self.doReset()
			wx.Bell()
		else:
			dlg = wx.MessageDialog(self, 'Auto Detect Failed.\nCheck that reader has power and is connected to the router.',
									'Auto Detect Failed',
									wx.OK|wx.ICON_INFORMATION )
			dlg.ShowModal()
			dlg.Destroy()
	
	def writeOptions( self ):
		config = Utils.getMainWin().config
		
		config.Write( 'UseHostName', 'True' if self.useHostName.GetValue() else 'False' )
		config.Write( 'ImpinjHostName', ImpinjHostNamePrefix + self.impinjHostName.GetValue() + ImpinjHostNameSuffix )
		config.Write( 'ImpinjAddr', self.impinjHost.GetAddress() )
		config.Write( 'ImpinjPort', '{}'.format(ImpinjInboundPort) )
		config.Write( 'ReceiveSensitivity_dB', '{}'.format(self.receiveSensitivity_dB.GetLabel()) )
		config.Write( 'TransmitPower_dBm', '{}'.format(self.transmitPower_dBm.GetLabel()) )
	
	def readOptions( self ):
		config = Utils.getMainWin().config
		
		useHostName = (config.Read('UseHostName', 'True').upper()[:1] == 'T')
		self.useHostName.SetValue( useHostName )
		self.useStaticAddress.SetValue( not useHostName )
		self.impinjHostName.SetValue( config.Read('ImpinjHostName', ImpinjHostNamePrefix + '00-00-00' + ImpinjHostNameSuffix)[len(ImpinjHostNamePrefix):-len(ImpinjHostNameSuffix)] )
		self.impinjHost.SetValue( config.Read('ImpinjAddr', '0.0.0.0') )
		self.useAntenna = config.ReadInt('useAntenna', 0)
		self.receiveSensitivity_dB.SetLabel( config.Read('ReceiveSensitivity_dB', 'Max') )
		self.transmitPower_dBm.SetLabel( config.Read('TransmitPower_dBm', 'Max') )
	
	def setStatus( self, status ):
		self.status = status
		if status == self.StatusIdle:
			self.statusLabel.SetLabel( 'Not Connected' )
			self.resetButton.SetLabel( 'Connect' )
			self.resetButton.SetToolTip( wx.ToolTip( 'Attempt to connect to the tag reader') )
		elif status == self.StatusAttempt:
			self.statusLabel.SetLabel( 'Not Connected' )
			self.resetButton.SetLabel( 'Connect' )
			self.resetButton.SetToolTip( wx.ToolTip( 'Attempt to connect to the tag reader') )
		elif status == self.StatusSuccess:
			self.statusLabel.SetLabel( 'Connected' )
			self.resetButton.SetLabel( 'Reset Connection' )
			self.resetButton.SetToolTip( wx.ToolTip( 'Reset the connection to the tag reader') )
		else:
			self.statusLabel.SetLabel( 'Connection Failed' )
			self.resetButton.SetLabel( 'Retry Connection' )
			self.resetButton.SetToolTip( wx.ToolTip( 'Attempt to connect to the tag reader') )
		self.Layout()
		
	def getHost( self ):
		if self.useHostName.GetValue():
			host = ImpinjHostNamePrefix + self.impinjHostName.GetValue().strip() + ImpinjHostNameSuffix
		else:
			host = self.impinjHost.GetAddress()
		return host
	
	def onWriteButton( self, event ):
		if not self.tagWriter:
			Utils.MessageOK( self, 'Reader not connected.\n\nSet reader connection parameters and press "Reset Connection".', 'Reader Not Connected' )
			return
			
		if self.writeAllTags.IsChecked():
			destination = ''
		else:
			destination = self.destination
			if destination is None:
				Utils.MessageOK( self,  'Please perform a read, then select a tag to overwrite.', 'No destination tag' )
				return
				
		#strip non-hex chars and fill with leading zeros
		data = re.sub('[^0-9A-F]','', self.tagToWrite.GetValue().upper())
		self.tagToWrite.ChangeValue(data)
		writeValue = data.zfill(self.EPCHexCharsMax)
		
		antenna = self.useAntenna if self.useAntenna > 0 else None
		
		self.setWriteSuccess( False )
		with wx.BusyCursor():
		
			try:
				#Utils.writeLog('Impinj: Writing tag 0x' + writeValue)
				self.tagWriter.WriteTag( destination, writeValue, antenna )
			except Exception as e:
				Utils.MessageOK( self, 'Write Fails: {}\n\nCheck the reader connection.\n\n{}'.format(e, traceback.format_exc()),
								'Write Fails' )
				Utils.writeLog('Impinj:Failed writing tag 0x' + writeValue)
				Utils.logException( e, sys.exc_info() )
			self.writeSuccess.SetValue( 50 )
		wx.CallLater( 100, self.onReadButton, None )
		
	def onReadButton( self, event=None, justRead=False ):
		self.clearGrid(self.tagsGrid)
		
		if not self.tagWriter:
			Utils.MessageOK( self,  'Reader not connected.\n\nSet reader connection parameters and press "Reset Connection".',
									'Reader Not Connected' )
			return
		
		if event or justRead:
			justRead = True
		
		tagInventory = None
		
		def tagInventoryKey( x ):
			try:
				return int(x, 16)
			except ValueError:
				return 0
				
		with wx.BusyCursor():
			try:
				tagInventory, otherMessages = self.tagWriter.GetTagInventory()
				tagDetail = { t['Tag']:t for t in self.tagWriter.tagDetail }
				tagInventory = [(t, tagDetail[t].get('PeakRSSI',''), tagDetail[t].get('AntennaID','')) for t in sorted(tagInventory, key = tagInventoryKey)]
				Utils.writeLog('Impinj: Read tag inventory: ' + str(tagInventory))
			except Exception as e:
				Utils.MessageOK( self, 'Read Fails: {}\n\nCheck the reader connection.\n\n{}'.format(e, traceback.format_exc()),
								'Read Fails' )
				Utils.logException( e, sys.exc_info() )
			
			success = False
			
			for tag in tagInventory: #first pass
				asciiValue=bytes.fromhex(tag[0]).decode(encoding="Latin1")
				asciiValue= ''.join([c for c in asciiValue if c.isprintable()])
				if self.useAntenna == 0 or tag[2] == self.useAntenna:
					self.tagsGrid.AppendRows(1)
					row = self.tagsGrid.GetNumberRows() -1
					col = 0
					self.tagsGrid.SetCellValue(row, col, str(tag[0]))
					self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
					col += 1
					self.tagsGrid.SetCellValue(row, col, '"' + asciiValue + '"' )
					self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
					col += 1
					self.tagsGrid.SetCellValue(row, col, str(tag[1]))
					self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
					col += 1
					self.tagsGrid.SetCellValue(row, col, str(tag[2]))
					self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)  
					col += 1
					if not justRead:
						if str(tag[0]).zfill(self.EPCHexCharsMax) == self.tagToWrite.GetValue().zfill(self.EPCHexCharsMax):
							for c in range(col):
								self.tagsGrid.SetCellBackgroundColour(row, c, self.LightGreen)
							success = True
							Utils.writeLog('Impinj: Successfully wrote tag: 0x' + tag[0])
						elif str(tag[0]).zfill(self.EPCHexCharsMax) == self.destination:
							for c in range(col):
								self.tagsGrid.SetCellBackgroundColour(row, c, self.LightRed)
						else:
							for c in range(col):
								self.tagsGrid.SetCellBackgroundColour(row, c, wx.WHITE)
					else:
						for c in range(col):
								self.tagsGrid.SetCellBackgroundColour(row, c, wx.WHITE)
			
			if self.useAntenna > 0: # second pass listing tags not on our antenna
				for tag in tagInventory:
					if tag[2] != self.useAntenna:
						self.tagsGrid.AppendRows(1)
						row = self.tagsGrid.GetNumberRows() -1
						col = 0
						self.tagsGrid.SetCellValue(row, col, str(tag[0]))
						self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
						col += 1
						self.tagsGrid.SetCellValue(row, col, '"' + asciiValue + '"')
						self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
						col += 1
						self.tagsGrid.SetCellValue(row, col, str(tag[1]))
						self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)
						col += 1
						self.tagsGrid.SetCellValue(row, col, str(tag[2]))
						self.tagsGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT,  wx.ALIGN_CENTRE)  
						col += 1
						for c in range(col):
							self.tagsGrid.SetCellTextColour(row, c, self.Grey)
			self.tagsGrid.AutoSize()
			totalWidth = 0
			self.setWriteSuccess( success )
			if success and not self.writeAllTags.IsChecked():
				self.destinationTag.SetLabel('')
				self.destination = None
				wx.Bell()
			self.Layout()
				
	def setTagToWrite( self, tag, info=None ):
		Utils.writeLog('Impinj set tag to: ' + str(tag))
		self.tagToWrite.ChangeValue(str(tag))
		self.onTagToWriteChanged()
		self.epcInfo.SetLabel( info if info else '')
		if self.status == self.StatusSuccess:
			self.writeButton.Enable()
			
	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		if rows:
			grid.DeleteRows( 0, rows )
				
	def commit( self, event=None ):
		Utils.writeLog('Impinj commit: ' + str(event))
				
	def refresh( self ):
		Utils.writeLog('Impinj refresh')
		self.readOptions()
		if self.status == self.StatusSuccess:
			wx.CallAfter( self.onReadButton, justRead=True)
		
