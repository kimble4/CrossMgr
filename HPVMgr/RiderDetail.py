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
		self.Bind( wx.EVT_TEXT, self.onEdited, self.riderFirstName )
		gbs.Add( self.riderFirstName, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='Last Name:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderLastName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(300,-1))
		self.Bind( wx.EVT_TEXT, self.onEdited, self.riderLastName )
		gbs.Add( self.riderLastName, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='Gender:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderGender = wx.Choice( self, choices=Model.Genders)
		self.Bind( wx.EVT_CHOICE, self.onEdited, self.riderGender )
		gbs.Add( self.riderGender, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='NatCode:'), pos=(row,0), span=(1,1), flag=labelAlign )
		ncs = wx.BoxSizer(wx.HORIZONTAL)
		self.riderNat = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(100,-1))
		self.riderNat.SetToolTip( wx.ToolTip('IOC country code'))
		self.Bind( wx.EVT_TEXT_ENTER, self.onNatCodeChanged, self.riderNat )
		self.riderNat.Bind( wx.EVT_KILL_FOCUS, self.onNatCodeChanged, self.riderNat )
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
			gbs.Add( wx.StaticText( self, label='Tag' + str(i) + ':'), pos=(row+i,2), span=(1,1), flag=labelAlign )
			setattr(self, 'riderTagDate' + str(i), wx.StaticText( self, label='') )
			getattr(self, 'riderTagDate' + str(i), None).SetToolTip( wx.ToolTip('Date the tag was last copied / written'))
			gbs.Add( getattr(self, 'riderTagDate' + str(i), None), pos=(row+i,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'riderTag' + str(i), wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(360,-1)) )
			getattr(self, 'riderTag' + str(i), None).SetToolTip( wx.ToolTip('Tag number (Hexadecimal)'))
			self.Bind( wx.EVT_TEXT, self.onEdited, getattr(self, 'riderTag' + str(i), None) )
			self.Bind( wx.EVT_TEXT_ENTER, lambda event, tag=i: self.onTagChanged(event, tag), getattr(self, 'riderTag' + str(i), None) )
			getattr(self, 'riderTag' + str(i), None).Bind( wx.EVT_KILL_FOCUS, lambda event, tag=i: self.onTagChanged(event, tag), getattr(self, 'riderTag' + str(i), None) )
			gbs.Add( getattr(self, 'riderTag' + str(i), None), pos=(row+i,4), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'btnTagCopy' + str(i), wx.Button( self, label='Copy') )
			getattr(self, 'btnTagCopy' + str(i), None).SetToolTip( wx.ToolTip('Copies the tag number to the clipboard'))
			getattr(self, 'btnTagCopy' + str(i), None).Disable()
			self.Bind( wx.EVT_BUTTON, lambda event, tag=i: self.copyTag(event, tag), getattr(self, 'btnTagCopy' + str(i), None) )
			gbs.Add( getattr(self, 'btnTagCopy' + str(i), None), pos=(row+i,5), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'btnTagWrite' + str(i), wx.Button( self, label='Write') )
			getattr(self, 'btnTagWrite' + str(i), None).SetToolTip( wx.ToolTip('Writes the tag'))
			getattr(self, 'btnTagWrite' + str(i), None).Disable()
			self.Bind( wx.EVT_BUTTON, lambda event, tag=i: self.writeTag(event, tag), getattr(self, 'btnTagWrite' + str(i), None) )
			gbs.Add( getattr(self, 'btnTagWrite' + str(i), None), pos=(row+i,6), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		row = 10
		
		#commit button
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		gbs.Add( self.commitButton, pos=(row,0), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		#edited warning
		self.editedWarning = wx.StaticText( self, label='' )
		gbs.Add( self.editedWarning, pos=(row,1), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		#machines list
		self.machinesGrid = wx.grid.Grid( self )
		self.machinesGrid.CreateGrid(0, 1)
		self.machinesGrid.SetColLabelValue(0, 'Rider\'s Machines')
		self.machinesGrid.HideRowLabels()
		#self.machinesGrid.AutoSize()
		self.machinesGrid.SetRowLabelSize( 0 )
		self.machinesGrid.SetMargins( 0, 0 )
		self.machinesGrid.AutoSizeColumns( True )
		self.machinesGrid.DisableDragColSize()
		self.machinesGrid.DisableDragRowSize()
		self.machinesGrid.EnableEditing(True)
		self.machinesGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onMachinesRightClick )
		self.machinesGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onMachinesRightClick )
		self.machinesGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onEdited )
		#self.machinesGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_DCLICK, self.onDoubleClick )
		#self.machinesGrid.Bind( wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.doLabelClick )
		# put a tooltip on the cells in a column
		#self.labelGrid.GetGridWindow().Bind(wx.EVT_MOTION, self.onMouseOver)
		gbs.Add( self.machinesGrid, pos=(row,2), span=(1,5), flag=wx.EXPAND )
		
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
			self.refreshMachinesGrid()
			self.onEdited( warn=False)
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
			self.onEdited()
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
		self.onEdited()
		
	def onEdited( self, event=None, warn=True ):
		if warn:
			self.editedWarning.SetLabel('Edited!')
		else:
			self.editedWarning.SetLabel('')

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
			
	def onMachinesRightClick( self, event ):
		row = event.GetRow()
		print(row)
		#col = event.GetCol()
		menu = wx.Menu()
		menu.SetTitle('#' + str(self.bib) + ' Machines')
		add = menu.Append( wx.ID_ANY, 'Add new machine', 'Add a new machine...' )
		self.Bind( wx.EVT_MENU, self.addMachine, add )
		delete = menu.Append( wx.ID_ANY, 'Delete machine from list', 'Delete this machine...' )
		self.Bind( wx.EVT_MENU, lambda event: self.deleteMachine(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
		
	def addMachine( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			with Model.LockDatabase() as db:
				rider = db.getRider(bib)
				if not 'Machines' in rider:
					rider['Machines'] = []
					db.setChanged()
				if 'New Machine' not in rider['Machines']:
					rider['Machines'].append('New Machine')
					db.setChanged()
			self.refreshMachinesGrid()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
	def deleteMachine( self, event, row ):
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			with Model.LockDatabase() as db:
				rider = db.getRider(bib)
				del rider['Machines'][row]
				db.setChanged()
			self.refreshMachinesGrid()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
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
		self.clearMachinesGrid()
			
	def clearMachinesGrid( self ):
		if self.machinesGrid.GetNumberRows():
			self.machinesGrid.DeleteRows(0, self.machinesGrid.GetNumberRows())
			
	def refreshMachinesGrid( self ):
		self.clearMachinesGrid()
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			rider = database.getRider(bib)
			self.machinesGrid.SetColLabelValue(0, rider['FirstName'] + ' ' + rider['LastName'] + '\'s Machines')
			if 'Machines' in rider:
				for machine in rider['Machines']:
					self.machinesGrid.AppendRows(1)
					row = self.machinesGrid.GetNumberRows() -1
					self.machinesGrid.SetCellValue(row, 0, str(machine))
			self.machinesGrid.AutoSizeColumns()
			self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
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
					for row in range(self.machinesGrid.GetNumberRows()):
						db.riders[bib]['Machines'][row] = self.machinesGrid.GetCellValue(row, 0).strip()
					if 'Machines' in db.riders[bib]:
						db.riders[bib]['Machines'][:] = [machine for machine in db.riders[bib]['Machines'] if machine]
					db.setChanged()
					self.onEdited( warn=False )
			else:
				self.bib=''
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
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
