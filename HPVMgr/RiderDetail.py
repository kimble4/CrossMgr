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
		row = 0
		
		gbs.Add( wx.StaticText( self, label='Rider bib#:'), pos=(row,0), span=(1,1), flag=labelAlign  )
		self.riderBib = wx.ComboBox(self, value=self.bib, choices=[], name='Rider Bib', size=(100,-1) )
		self.Bind( wx.EVT_TEXT, self.onBibChanged, self.riderBib )
		gbs.Add( self.riderBib, pos=(row,1), span=(1,1))
		row+= 1
		gbs.Add( wx.StaticText( self, label='First Name(s):'), pos=(row,0), span=(1,1), flag=labelAlign  )
		self.riderFirstName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(300,-1))
		gbs.Add( self.riderFirstName, pos=(row,1), span=(1,1) )
		row+= 1
		gbs.Add( wx.StaticText( self, label='Last Name:'), pos=(row,0), span=(1,1), flag=labelAlign  )
		self.riderLastName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(300,-1))
		gbs.Add( self.riderLastName, pos=(row,1), span=(1,1) )
		row+= 1
		gbs.Add( wx.StaticText( self, label='Gender:'), pos=(row,0), span=(1,1), flag=labelAlign  )
		self.riderGender = wx.Choice( self, choices=Model.Genders)
		gbs.Add( self.riderGender, pos=(row,1), span=(1,1) )
		row+= 1
		gbs.Add( wx.StaticText( self, label='NatCode:'), pos=(row,0), span=(1,1), flag=labelAlign  )
		ncs = wx.BoxSizer(wx.HORIZONTAL)
		self.riderNat = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(100,-1))
		self.Bind( wx.EVT_TEXT_ENTER, self.onNatCodeChanged, self.riderNat )
		ncs.Add( self.riderNat )
		self.riderFlag = wx.StaticBitmap(self, -1, wx.NullBitmap, size=(44,28))
		ncs.AddSpacer(10)
		ncs.Add( self.riderFlag, flag=wx.ALIGN_CENTRE_VERTICAL)
		gbs.Add( ncs, pos=(row,1), span=(1,1))
		
		
		vs.Add( gbs )
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
		except KeyError:
			self.clearRiderData()
		except ValueError:
			self.bib = ''
			self.clearRiderData()
			
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

	def clearRiderData( self ):
		self.riderFirstName.SetValue('')
		self.riderLastName.SetValue('')
		self.riderGender.SetSelection(Model.Open)
		self.riderNat.ChangeValue('')
		self.riderFlag.SetBitmap(wx.NullBitmap)
	
	def setBib( self, bib ):
		self.bib = str(bib)
		self.refresh()
	
	def commit( self ):
		print('riderdetail commit')
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
					db.setChanged()
			else:
				self.bib=''
		except:
			pass
	
	def refresh( self ):
		database = Model.database
		if database is None:
			return
		bibs = list(map(str, database.getBibs()))
		bib = self.bib
		self.riderBib.Clear()
		self.riderBib.Set( bibs )
		self.riderBib.SetValue(bib)
