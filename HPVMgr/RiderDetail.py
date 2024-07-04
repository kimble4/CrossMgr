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
		self.riderBib = wx.ComboBox(self, value=self.bib, choices=[], name='Rider Bib', size=(100,-1), style=wx.TE_PROCESS_ENTER)
		self.Bind( wx.EVT_TEXT, self.onBibChanged, self.riderBib )
		self.Bind( wx.EVT_TEXT_ENTER, self.onBibEnter, self.riderBib )
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
		gbs.Add( wx.StaticText( self, label='DOB:'), pos=(row,0), span=(1,1), flag=labelAlign )
		hs = wx.BoxSizer(wx.HORIZONTAL)
		self.riderDOB = wx.adv.DatePickerCtrl(self, style=wx.adv.DP_SHOWCENTURY|wx.adv.DP_ALLOWNONE, size=(200,-1), name="Date of Birth")
		self.riderDOB.SetNullText('Unset')
		self.Bind( wx.adv.EVT_DATE_CHANGED, self.onDOBChanged, self.riderDOB )
		hs.Add( self.riderDOB, flag=wx.ALIGN_CENTRE_VERTICAL )
		self.riderAge = wx.StaticText( self, label = '' )
		hs.Add( self.riderAge, flag=wx.ALIGN_CENTRE_VERTICAL )
		gbs.Add( hs, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		row += 1
		gbs.Add( wx.StaticText( self, label='NatCode:'), pos=(row,0), span=(1,1), flag=labelAlign )
		ncs = wx.BoxSizer(wx.HORIZONTAL)
		self.riderNat = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(200,-1))
		self.riderNat.SetToolTip( wx.ToolTip('IOC country code'))
		self.Bind( wx.EVT_TEXT_ENTER, self.onNatCodeChanged, self.riderNat )
		self.Bind( wx.EVT_TEXT, self.onEdited, self.riderNat )
		ncs.Add( self.riderNat )
		self.riderFlag = wx.StaticBitmap(self, -1, wx.NullBitmap, size=(44,28))
		ncs.AddSpacer(10)
		ncs.Add( self.riderFlag, flag=wx.ALIGN_CENTRE_VERTICAL)
		gbs.Add( ncs, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		row += 1
		gbs.Add( wx.StaticText( self, label='License:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderLicense = wx.TextCtrl( self, size=(300,-1))
		gbs.Add( self.riderLicense, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		self.Bind( wx.EVT_TEXT, self.onEdited, self.riderLicense )
		row += 1
		gbs.Add( wx.StaticText( self, label='Factor:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderFactor = wx.TextCtrl( self, size=(300,-1))
		gbs.Add( self.riderFactor, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		self.Bind( wx.EVT_TEXT, self.onEdited, self.riderFactor )
		row += 1
		gbs.Add( wx.StaticText( self, label='Team:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderTeam = wx.StaticText( self, label='')
		self.riderTeam.SetToolTip( wx.ToolTip('The last team the rider was entered for'))
		gbs.Add( self.riderTeam, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		row += 1
		gbs.Add( wx.StaticText( self, label='Last entered:'), pos=(row,0), span=(1,1), flag=labelAlign )
		self.riderLastEntered = wx.StaticText( self, label='')
		self.riderLastEntered.SetToolTip( wx.ToolTip('Date the rider was last entered in a race'))
		gbs.Add( self.riderLastEntered, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		row += 1
		self.deleteButton = wx.Button( self, label='Delete Rider')
		self.deleteButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.deleteRider, self.deleteButton )
		gbs.Add( self.deleteButton, pos=(row,0), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		# tag fields
		row = 0
		for i in range(10):
			gbs.Add( wx.StaticText( self, label='Tag' + str(i) + ':'), pos=(row+i,2), span=(1,1), flag=labelAlign )
			setattr(self, 'riderTagDate' + str(i), wx.StaticText( self, label='') )
			getattr(self, 'riderTagDate' + str(i), None).SetToolTip( wx.ToolTip('Date the tag was last copied / written'))
			gbs.Add( getattr(self, 'riderTagDate' + str(i), None), pos=(row+i,3), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'riderTag' + str(i), wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(360,-1)) )
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
		
		#machines list
		self.machinesGrid = wx.grid.Grid( self )
		self.machinesGrid.CreateGrid(0, 3)
		self.machinesGrid.SetColLabelValue(0, 'Rider\'s Machines')
		self.machinesGrid.SetColLabelValue(1, 'Categories')
		self.machinesGrid.SetColLabelValue(2, 'Last Entered')
		self.machinesGrid.HideRowLabels()
		self.machinesGrid.SetRowLabelSize( 0 )
		self.machinesGrid.SetMargins( 0, 0 )
		self.machinesGrid.AutoSizeColumns( True )
		self.machinesGrid.DisableDragColSize()
		self.machinesGrid.DisableDragRowSize()
		self.machinesGrid.EnableEditing(True)
		self.machinesGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onMachinesRightClick )
		self.machinesGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onMachinesRightClick )
		self.machinesGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onEdited )
		gbs.Add( self.machinesGrid, pos=(row,2), span=(1,5), flag=wx.EXPAND )
		
		vs.Add( gbs )
		vs.AddStretchSpacer()
		hs = wx.BoxSizer( wx.HORIZONTAL )
		#commit button
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Stores changes (CTRL-O)'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		hs.Add( self.commitButton, flag=wx.ALIGN_CENTRE_VERTICAL )
		
		#edited warning
		self.editedWarning = wx.StaticText( self, label='' )
		hs.Add( self.editedWarning, flag=wx.ALIGN_CENTRE_VERTICAL )
		
		
		vs.Add (hs)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onBibEnter( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			rider = database.getRider(bib)
		except KeyError:  # rider does not exist
			if Utils.MessageOKCancel( self, 'Rider #' + self.bib + ' does not exist, do you want to add them?', title = 'Add new rider?', iconMask = wx.ICON_QUESTION):
				with Model.LockDatabase() as db:
					db.addRider(bib)
				wx.CallAfter( self.refresh )
		except ValueError:  # invalid int
			pass
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
	def onBibChanged( self, event=None ):
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			rider = database.getRider(bib)
			if rider is not None:
				self.riderFirstName.ChangeValue(rider['FirstName'])
				self.riderLastName.ChangeValue(rider['LastName'])
				self.riderGender.SetSelection(rider['Gender'])
				if 'DOB' in rider:
					self.riderDOB.SetValue(wx.DateTime.FromTimeT(rider['DOB']) )
				else:
					self.riderDOB.SetValue( wx.InvalidDateTime )
				self.riderAge.SetLabel((' Age=' + str(database.getRiderAge(bib))) if database.getRiderAge(bib) else '')
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
				if 'License' in rider:
					self.riderLicense.ChangeValue(rider['License'])
				else:
					self.riderLicense.ChangeValue('')
				if 'Factor' in rider:
					self.riderFactor.ChangeValue(str(rider['Factor']))
				else:
					self.riderFactor.ChangeValue('')
				if 'Team' in rider:
					self.riderTeam.SetLabel(rider['Team'])
				else:
					self.riderTeam.SetLabel('')
				if 'LastEntered' in rider:
					self.riderLastEntered.SetLabel('{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(rider['LastEntered'])) if rider['LastEntered'] > 0 else '' )
				else:
					self.riderLastEntered.SetLabel('')
				for i in range(10):
					if 'Tag' + (str(i) if i > 0 else '') in rider:
						getattr(self, 'riderTag' + str(i), None).ChangeValue(rider['Tag' + (str(i) if i > 0 else '')])
						getattr(self, 'riderTagDate' + str(i), None).SetLabel( '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(rider['Tag' + (str(i) if i > 0 else '') + 'LastWritten'])) if 'Tag' + (str(i) if i > 0 else '') + 'LastWritten' in rider else '' )
						getattr(self, 'btnTagCopy' + str(i), None).Enable()
						getattr(self, 'btnTagWrite' + str(i), None).Enable()
					else:
						getattr(self, 'riderTag' + str(i), None).ChangeValue('')
						getattr(self, 'riderTagDate' + str(i), None).SetLabel('')
						getattr(self, 'btnTagCopy' + str(i), None).Disable()
						getattr(self, 'btnTagWrite' + str(i), None).Disable()
				self.refreshMachinesGrid()
				self.deleteButton.Enable()
				self.onEdited( warn=False)
			else: # rider does not exist
				self.refreshMachinesGrid()
				self.clearRiderData()
		except ValueError:  #invalid int
			self.clearRiderData()
		self.Layout()
		
	def onDOBChanged( self, event ):
		dob = self.riderDOB.GetValue()
		age = ''
		if dob.IsValid():
			if wx.DateTime.Now() - dob > wx.TimeSpan.Days(365):
				age = ' Age=' + str(int((wx.DateTime.Now() - dob).GetDays()/365))
		self.riderAge.SetLabel( age )
		self.onEdited()
			
	def onNatCodeChanged( self, event=None ):
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
			if event: 
				self.onEdited()
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
					wx.CallAfter( self.refresh )
		else:
			Utils.writeLog('Tag'+ str(tag) + ': Nothing to copy!')
			
	def writeTag( self, event, tag ):
		database = Model.database
		if database is None:
			return
		data = getattr(self, 'riderTag' + str(tag), None).GetValue()
		info = '#' + self.bib + ' ' + database.getRiderName(int(self.bib), True) + ' (Tag' + str(tag) + ')'
		if data:
			mainwin = Utils.getMainWin()
			mainwin.impinj.setTagToWrite( data, info )
			with Model.LockDatabase() as db:
				db.riders[int(self.bib)]['Tag' + (str(tag) if tag > 0 else '') + 'LastWritten'] = int(datetime.datetime.now().timestamp())
				db.setChanged()
			wx.CallAfter(mainwin.showPage, mainwin.iImpinjPage )

			
	def onMachinesRightClick( self, event ):
		row = event.GetRow()
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
			if not self.bib:
				return
			bib = int(self.bib)
			with wx.TextEntryDialog(self, 'Enter the name for the new machine:', caption='Add machine', value='New Machine', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					machine = dlg.GetValue()
					with Model.LockDatabase() as db:
						rider = db.getRider(bib)
						if not 'Machines' in rider:
							rider['Machines'] = []
						if 'New Machine' not in rider['Machines']:
							rider['Machines'].append([machine, [], None])
						db.setChanged()
			self.refreshMachinesGrid()
			self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
	def deleteMachine( self, event, row ):
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			if not self.bib:
				return
			bib = int(self.bib)
			with Model.LockDatabase() as db:
				rider = db.getRider(bib)
				if 'Machines' in rider and len (rider['Machines']) >= row:
					del rider['Machines'][row]
					db.setChanged()
					self.refreshMachinesGrid()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
	def clearRiderData( self ):
		self.riderFirstName.ChangeValue('')
		self.riderLastName.ChangeValue('')
		self.riderGender.SetSelection(Model.Open)
		self.riderNat.ChangeValue('')
		self.riderFlag.SetBitmap(wx.NullBitmap)
		self.riderLastEntered.SetLabel('')
		for i in range(10):
			getattr(self, 'riderTag' + str(i), None).ChangeValue('')
			getattr(self, 'riderTagDate' + str(i), None).SetLabel('')
			getattr(self, 'btnTagCopy' + str(i), None).Disable()
			getattr(self, 'btnTagWrite' + str(i), None).Disable()
		self.deleteButton.Disable()
		self.clearMachinesGrid()
		self.machinesGrid.AppendRows(1)
			
	def clearMachinesGrid( self ):
		rows = self.machinesGrid.GetNumberRows()
		if rows:
			self.machinesGrid.DeleteRows( 0, rows )
		self.machinesGrid.SetColLabelValue(0, 'Rider\'s Machines')
			
	def refreshMachinesGrid( self ):
		self.clearMachinesGrid()
		database = Model.database
		if database is None:
			return
		try:
			self.bib = self.riderBib.GetValue()
			bib = int(self.bib)
			rider = database.getRider(bib)
			if rider is not None:
				self.machinesGrid.SetColLabelValue(0, database.getRiderName(bib, True) + '\'s Machines')
				if 'Machines' in rider:
					for machineCategoriesDate in sorted(rider['Machines'], key=lambda item: (item[2] if len(item) >= 3 and item[2] else 0)):
						self.machinesGrid.AppendRows(1)
						row = self.machinesGrid.GetNumberRows() -1
						col = 0
						self.machinesGrid.SetCellValue(row, col, str(machineCategoriesDate[0]))
						col += 1
						self.machinesGrid.SetCellValue(row, col, ','.join(database.getAbbreviatedCategory(c) for c in machineCategoriesDate[1]))
						col += 1
						if len(machineCategoriesDate) < 3:
							dt = ''
						else:
							dt = '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(machineCategoriesDate[2])) if machineCategoriesDate[2] is not None else ''
							self.machinesGrid.SetCellAlignment(row, col, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
						self.machinesGrid.SetCellValue(row, col, dt)
				self.machinesGrid.AutoSize()
				self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
	
	def setBib( self, bib ):
		self.bib = str(bib)
		
	def deleteRider( self, event=None ):
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete #' + self.bib + ' ' + self.riderLastName.GetValue() + ', ' + self.riderFirstName.GetValue() + '?', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete rider: ' + self.bib)
			with Model.LockDatabase() as db:
				db.deleteRider(int(self.bib))
			self.bib = ''
			wx.CallAfter( self.refresh )
	
	def commit( self, event=None ):
		Utils.writeLog('RiderDetail commit: ' + str(event))
		database = Model.database
		if database is None:
			return
		try:
			self.onNatCodeChanged()
			bib = int(self.bib)
			if database.isRider(bib):
				with Model.LockDatabase() as db:
					db.riders[bib]['FirstName'] = self.riderFirstName.GetValue()
					db.riders[bib]['LastName'] = self.riderLastName.GetValue()
					db.riders[bib]['Gender'] = self.riderGender.GetSelection()
					if 'DOB' in db.riders[bib]:
						del db.riders[bib]['DOB']
					dob = self.riderDOB.GetValue()
					if dob.IsValid():
						if wx.DateTime.Now() - dob > wx.TimeSpan.Days(365):
							db.riders[bib]['DOB'] = int(dob.GetValue()/1000)
					db.riders[bib]['NatCode'] = self.riderNat.GetValue().upper()
					if 'License' in db.riders[bib]:
						del db.riders[bib]['License']
					if len(self.riderLicense.GetValue()) > 0:
						db.riders[bib]['License'] = self.riderLicense.GetValue()
					if 'Factor' in db.riders[bib]:
						del db.riders[bib]['Factor']
					if len(self.riderFactor.GetValue()) > 0:
						try:
							factor = float(self.riderFactor.GetValue())
							db.riders[bib]['Factor'] = factor
						except ValueError:
							pass
					for i in range(10):
						data = getattr(self, 'riderTag' + str(i), None).GetValue()
						if data:
							db.riders[bib]['Tag' + (str(i) if i > 0 else '')] = data
						else:
							if 'Tag' + (str(i) if i > 0 else '') in db.riders[bib]:
								del db.riders[bib]['Tag' + (str(i) if i > 0 else '')]
							if 'Tag' + (str(i) if i > 0 else '') + 'LastWritten' in db.riders[bib]:
								del db.riders[bib]['Tag' + (str(i) if i > 0 else '') + 'LastWritten']
					db.setChanged()
					self.onEdited( warn=False )
			else:
				if Utils.MessageOKCancel( self, 'Rider #' + self.bib + ' does not exist, do you want to add them?', title = 'Add new rider?', iconMask = wx.ICON_QUESTION):
					firstName = self.riderFirstName.GetValue()
					lastName = self.riderLastName.GetValue()
					dupBibs = database.duplicateRiderNames(firstName, lastName)
					if len(dupBibs) > 0: #Check for potential duplicates
						Utils.writeLog('Rider name "' + firstName + ' ' + lastName + '" is duplicate!')
						if not Utils.MessageOKCancel( self, 'Rider "' + firstName + ' ' + lastName + '" already exists with bib ' + ','.join('#' + str(b) for b in dupBibs) + ',  do you want to continue adding them as #' + self.bib + '?', title = 'Add new rider?', iconMask = wx.ICON_QUESTION):
							self.bib=''
							return
					with Model.LockDatabase() as db:
						db.addRider(bib, firstName=self.riderFirstName.GetValue() if self.riderFirstName.GetValue() else None, lastName=self.riderLastName.GetValue() if self.riderLastName.GetValue() else None, gender=self.riderGender.GetSelection())
						#populate the non-essential fields, if we have them
						dob = self.riderDOB.GetValue()
						if dob.IsValid():
							if wx.DateTime.Now() - dob > wx.TimeSpan.Days(365):
								db.riders[bib]['DOB'] = int(dob.GetValue()/1000)
						db.riders[bib]['NatCode'] = self.riderNat.GetValue().upper()
						if len(self.riderLicense.GetValue()) > 0:
							db.riders[bib]['License'] = self.riderLicense.GetValue()
						if len(self.riderFactor.GetValue()) > 0:
							try:
								factor = float(self.riderFactor.GetValue())
								db.riders[bib]['Factor'] = factor
							except ValueError:
								pass
						db.setChanged()
						self.onEdited( warn=False )
						wx.CallAfter( self.refresh )
				else:
					self.bib=''
					wx.CallAfter( self.refresh )
					return
		except ValueError:  # invalid int
			pass
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		if event: #called by button
			wx.CallAfter( self.refresh )
	
	def refresh( self ):
		database = Model.database
		if database is None:
			self.riderBib.Clear()
			return
		bibs = list(map(str, database.getBibs()))
		bib = self.bib
		self.riderBib.Set( bibs )
		self.riderBib.SetValue(bib)
