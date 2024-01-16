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
import Flags

class RiderDetail( wx.Panel ):
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.bib = ''
		
		labelAlign = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
		vs = wx.BoxSizer(wx.VERTICAL)
		gbs = wx.GridBagSizer(5, 5)
		
		#rider fields
		row = 0
		gbs.Add( wx.StaticText( self, label='Rider bib#:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderBib = wx.ComboBox(self, value=self.bib, choices=[], name='Rider Bib', size=(100,-1) )
		self.Bind( wx.EVT_TEXT, self.onBibChanged, self.riderBib )
		gbs.Add( self.riderBib, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='First Name(s):'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderFirstName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(300,-1))
		gbs.Add( self.riderFirstName, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='Last Name:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderLastName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(300,-1))
		gbs.Add( self.riderLastName, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='Gender:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderGender = wx.Choice( self, choices=Model.Genders)
		gbs.Add( self.riderGender, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='NatCode:'), pos=(row,0), span=(1,1), flag=labelAlign )
		ncs = wx.BoxSizer(wx.HORIZONTAL)
		self.riderNat = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(100,-1))
		self.riderNat.SetToolTip( wx.ToolTip('IOC country code'))
		self.Bind( wx.EVT_TEXT_ENTER, self.onNatCodeChanged, self.riderNat )
		ncs.Add( self.riderNat )
		self.riderFlag = wx.StaticBitmap(self, -1, wx.NullBitmap, size=(44,28))
		ncs.AddSpacer(10)
		ncs.Add( self.riderFlag, flag=wx.ALIGN_CENTRE_VERTICAL)
		gbs.Add( ncs, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		row += 1
		gbs.Add( wx.StaticText( self, label='Last entered:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderLastEntered = wx.StaticText( self, label='')
		self.riderLastEntered.SetToolTip( wx.ToolTip('Date the rider was last entered in a race'))
		gbs.Add( self.riderLastEntered, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		
		# tag fields
		row = 0
		for i in range(10):
			gbs.Add( wx.StaticText( self, label='Tag' + str(i) + ':'), pos=(i,2), span=(1,1), flag=labelAlign )
			setattr(self, 'riderTagDate' + str(i), wx.StaticText( self, label='') )
			getattr(self, 'riderTagDate' + str(i), None).SetToolTip( wx.ToolTip('Date the tag was last copied / written'))
			gbs.Add( getattr(self, 'riderTagDate' + str(i), None), pos=(i,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'riderTag' + str(i), wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(360,-1)) )
			getattr(self, 'riderTag' + str(i), None).SetToolTip( wx.ToolTip('Tag number (Hexadecimal)'))
			self.Bind( wx.EVT_TEXT, lambda event, tag=i: self.onTagChanged(event, tag), getattr(self, 'riderTag' + str(i), None) )
			gbs.Add( getattr(self, 'riderTag' + str(i), None), pos=(i,4), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'btnTagCopy' + str(i), wx.Button( self, label='Copy') )
			getattr(self, 'btnTagCopy' + str(i), None).SetToolTip( wx.ToolTip('Copies the tag number to the clipboard'))
			getattr(self, 'btnTagCopy' + str(i), None).Disable()
			self.Bind( wx.EVT_BUTTON, lambda event, tag=i: self.copyTag(event, tag), getattr(self, 'btnTagCopy' + str(i), None) )
			gbs.Add( getattr(self, 'btnTagCopy' + str(i), None), pos=(i,5), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'btnTagWrite' + str(i), wx.Button( self, label='Write') )
			getattr(self, 'btnTagWrite' + str(i), None).SetToolTip( wx.ToolTip('Writes the tag'))
			getattr(self, 'btnTagWrite' + str(i), None).Disable()
			self.Bind( wx.EVT_BUTTON, lambda event, tag=i: self.writeTag(event, tag), getattr(self, 'btnTagWrite' + str(i), None) )
			gbs.Add( getattr(self, 'btnTagWrite' + str(i), None), pos=(i,6), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		
		vs.Add( gbs )
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		vs.Add( self.commitButton )
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
	
	def onBibChanged( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			rider = database.getRider(bib)
			self.riderFirstName.ChangeValue(rider['FirstName'])
			self.riderLastName.ChangeValue(rider['LastName'])
			self.riderGender.SetSelection(rider['Gender'])
			if 'NatCode' in rider:
				self.riderNat.ChangeValue(rider['NatCode'])
				image = Flags.GetFlagImage( rider['NatCode'])
				if image:
					self.riderFlag.SetBitmap(image.Scale(44, 28, wx.IMAGE_QUALITY_HIGH) )
				else:
					self.riderFlag.SetBitmap(wx.NullBitmap)
			else:
				self.riderNat.ChangeValue('')
				self.riderFlag.SetBitmap(wx.NullBitmap)
			if 'LastEntered' in rider:
				self.riderLastEntered.SetLabel('{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(rider['LastEntered'])) if rider['LastEntered'] > 0 else '' )
			else:
				self.riderLastEntered.SetLabel('')
			for i in range(10):
				if 'Tag' + (str(i) if i > 0 else '') in rider:
					getattr(self, 'riderTag' + str(i), None).ChangeValue(rider['Tag' + (str(i) if i > 0 else '')])
					getattr(self, 'riderTagDate' + str(i), None).SetLabel( '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(rider['Tag' + (str(i) if i > 0 else '') + 'LastWritten'])) if 'Tag' + (str(i) if i > 0 else '') + 'LastWritten' in rider else '' )
					getattr(self, 'btnTagCopy' + str(i), None).Enable()
					#getattr(self, 'btnTagWrite' + str(i), None).Enable()  #fixme
				else:
					getattr(self, 'riderTag' + str(i), None).ChangeValue('')
					getattr(self, 'riderTagDate' + str(i), None).SetLabel('')
					getattr(self, 'btnTagCopy' + str(i), None).Disable()
					getattr(self, 'btnTagWrite' + str(i), None).Disable()
		except KeyError:
			self.clearRiderData()
		except ValueError:
			self.bib = ''
			self.clearRiderData()
		self.Layout()
			
	def onNatCodeChanged( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			nat = self.riderNat.GetValue().upper()
			self.riderNat.ChangeValue(nat)
			image = Flags.GetFlagImage( nat )
			if image:
				self.riderFlag.SetBitmap(image.Scale(44, 28, wx.IMAGE_QUALITY_HIGH))
			else:
				self.riderFlag.SetBitmap(wx.NullBitmap)
		except ValueError:
			pass
			
	def onTagChanged( self, event, tag ):
		data = getattr(self, 'riderTag' + str(tag), None).GetValue().upper()
		getattr(self, 'riderTag' + str(tag), None).ChangeValue(re.sub('[^0-9A-F]','', data))

	def copyTag( self, event, tag ):
		database = Model.database
		if database is None:
			return
		data = getattr(self, 'riderTag' + str(tag), None).GetValue()
		if data:
			if getattr(database, 'copyTagsWithDelim', False):
				out = []
				for i in range(len(data), 0, -4):
					if i-4 < 0:
						out.insert(0, '0' * (4 - len(data)%4) +  data[0:i])
					else:
						out.insert(0, data[i-4:i])
				data = '-'.join(out)
			if wx.TheClipboard.Open():
				wx.TheClipboard.SetData(wx.TextDataObject(data))
				wx.TheClipboard.Close()
				with Model.LockDatabase() as db:
					db.riders[int(self.bib)]['Tag' + (str(tag) if tag > 0 else '') + 'LastWritten'] = int(datetime.datetime.now().timestamp())
					db.setChanged()
					
		else:
			Utils.writeLog('Tag'+ str(tag) + ': Nothing to copy!')
	
	def writeTag( self, event, tag ):
		print(event)
		print('write tag ' + str(tag))

	def clearRiderData( self ):
		self.riderFirstName.SetValue('')
		self.riderLastName.SetValue('')
		self.riderGender.SetSelection(Model.Open)
		self.riderNat.ChangeValue('')
		self.riderFlag.SetBitmap(wx.NullBitmap)
		self.riderLastEntered.SetLabel('')
		for i in range(10):
			getattr(self, 'riderTag' + str(i), None).ChangeValue('')
			getattr(self, 'riderTagDate' + str(i), None).SetLabel('')
			getattr(self, 'btnTagCopy' + str(i), None).Disable()
			getattr(self, 'btnTagWrite' + str(i), None).Disable()
	
	def setBib( self, bib ):
		self.bib = str(bib)
		self.refresh()
	
	def commit( self, event=None ):
		Utils.writeLog('RiderDetail commit: ' + str(event))
		database = Model.database
		if database is None:
			return
		try:
			bib = int(self.bib)
			if database.isRider(bib):
				with Model.LockDatabase() as db:
					db.riders[bib]['FirstName'] = self.riderFirstName.GetValue()
					db.riders[bib]['LastName'] = self.riderLastName.GetValue()
					db.riders[bib]['Gender'] = self.riderGender.GetSelection()
					db.riders[bib]['NatCode'] = self.riderNat.GetValue().upper()
					for i in range(10):
						data = getattr(self, 'riderTag' + str(i), None).GetValue()
						if data:
							db.riders[bib]['Tag' + (str(i) if i > 0 else '')] = data
						elif 'Tag' + (str(i) if i > 0 else '') in db.riders[bib]:
							del db.riders[bib]['Tag' + (str(i) if i > 0 else '')]
							del db.riders[bib]['Tag' + (str(i) if i > 0 else '') + 'LastWritten']
					db.setChanged()
			else:
				self.bib=''
		except Exception as e:
			#Utils.logException( e, sys.exc_info() )
			pass
		if event: #called by button
			self.refresh()
			self.Layout()
	
	def refresh( self ):
		database = Model.database
		if database is None:
			return
		bibs = list(map(str, database.getBibs()))
		bib = self.bib
		self.riderBib.Clear()
		self.riderBib.Set( bibs )
		self.riderBib.SetValue(bib)
