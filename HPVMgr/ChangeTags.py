import wx
import Utils
import Model
import os
import datetime
import sys
import re

class ChangeTagsDialog( wx.Dialog ):
	
	orangeColour = wx.Colour( 255, 165, 0 )
	
	def __init__( self, parent, bib, race, id = wx.ID_ANY):
		self.parent = parent
		self.season = None
		self.evt = None
		self.rnd = None
		self.race = race
		self.bib = bib
		
		displaySize = list( wx.GetDisplaySize() )
		size = (min(displaySize[0], 640), displaySize[1]/2)
		super().__init__( parent, id, 'Change tags', size=size, pos=wx.DefaultPosition, 
			style = wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX )
		
		
		
		# Set the upper left icon.
		icon = wx.Icon( os.path.join(Utils.getImageFolder(), 'HPVMgr16x16.ico'), wx.BITMAP_TYPE_ICO )
		self.SetIcon( icon )
		
		self.SetLayoutAdaptationMode(wx.DIALOG_ADAPTATION_MODE_ENABLED)
		
		self.mainSizer = wx.BoxSizer( wx.VERTICAL )
		self.nameLabel = wx.StaticText( self, label='Tags for rider:' ) 
		self.mainSizer.Add( self.nameLabel )
		
		gbs = wx.GridBagSizer(0, 0)
		
		# tag fields
		row = 0
		for i in range(10):
			gbs.Add( wx.StaticText( self, label='Tag' + str(i) + ':'), pos=(row+i,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
			setattr(self, 'riderTag' + str(i), wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(360,-1)) )
			getattr(self, 'riderTag' + str(i), None).SetToolTip( wx.ToolTip('Tag number (Hexadecimal)'))
			self.Bind( wx.EVT_TEXT_ENTER, lambda event, tag=i: self.onTagChanged(event, tag), getattr(self, 'riderTag' + str(i), None) )
			# getattr(self, 'riderTag' + str(i), None).Bind( wx.EVT_KILL_FOCUS, lambda event, tag=i: self.onTagChanged(event, tag), getattr(self, 'riderTag' + str(i), None) )
			gbs.Add( getattr(self, 'riderTag' + str(i), None), pos=(row+i,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			setattr(self, 'btnTagRevert' + str(i), wx.Button( self, label='Revert') )
			getattr(self, 'btnTagRevert' + str(i), None).SetToolTip( wx.ToolTip('Reverts the tag to the global value'))
			self.Bind( wx.EVT_BUTTON, lambda event, tag=i: self.revertTag(event, tag), getattr(self, 'btnTagRevert' + str(i), None) )
			gbs.Add( getattr(self, 'btnTagRevert' + str(i), None), pos=(row+i,2), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
			row += 1
		
		self.mainSizer.Add(gbs)
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.cancelButton = wx.Button( self, wx.ID_CANCEL)
		self.okButton = wx.Button( self, wx.ID_OK)
		self.okButton.Bind( wx.EVT_BUTTON, self.onOkButton )
		hs.Add( self.cancelButton )
		hs.Add( self.okButton ) 
		self.mainSizer.Add( hs, flag=wx.ALIGN_RIGHT )
		
		self.SetSizer( self.mainSizer )
		
		self.refresh()
		self.Fit()
		
	def onTagChanged( self, event, tag):
		data = re.sub('[^0-9A-F]','', getattr(self, 'riderTag' + str(tag), None).GetValue().upper())
		getattr(self, 'riderTag' + str(tag), None).ChangeValue(data)
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				race = rnd['races'][self.race]
				rider = database.getRider(self.bib)
				if getattr(self, 'riderTag' + str(tag), None).GetValue() == rider['Tag' + (str(tag) if tag > 0 else '')]:
					getattr(self, 'riderTag' + str(tag), None).SetBackgroundColour(wx.WHITE)
				else:
					getattr(self, 'riderTag' + str(tag), None).SetBackgroundColour(self.orangeColour)
			except Exception as e:
				Utils.logException( e, sys.exc_info() )	
		
	def onOkButton( self, event ):
		try:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[self.season]
				season = db.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				race = rnd['races'][self.race]
				rider = db.getRider(self.bib)
				for raceEntryDict in race:
					if raceEntryDict['bib'] == self.bib:
						for i in range(10):
							data = re.sub('[^0-9A-F]','', getattr(self, 'riderTag' + str(i), None).GetValue().upper())
							if data == rider['Tag' + (str(i) if i > 0 else '')]: # tag is default
								if 'tag' + (str(i) if i > 0 else '') in raceEntryDict:  # remove override field from raceEntryDict
									Utils.writeLog('ChangeTags/onOkButton: Removing edited tag' + str(i) + ' for rider #' + str(self.bib) + ' in race ' + str(self.race+1) + ': ' + raceEntryDict['tag' + (str(i) if i > 0 else '')])
									del raceEntryDict['tag' + (str(i) if i > 0 else '')]
									db.setChanged()
							else: # tag is edited, save to raceEntryDict
								Utils.writeLog('ChangeTags/onOkButton: Edited tag' + str(i) + ' for rider #' + str(self.bib) + ' in race ' + str(self.race+1) + ': ' + data)
								raceEntryDict['tag' + (str(i) if i > 0 else '')] = data
								db.setChanged()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		if self.IsModal():
			self.EndModal(event.EventObject.Id)
		else:
			self.Close()
		
	def revertTag( self, event, tag ):
		database = Model.database
		if database is None:
			return
		try:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			evt = season['events'][evtName]
			rndName = list(evt['rounds'])[self.rnd]
			rnd = evt['rounds'][rndName]
			race = rnd['races'][self.race]
			rider = database.getRider(self.bib)
			for raceEntryDict in race:
				if raceEntryDict['bib'] == self.bib:
					if 'Tag' + (str(tag) if tag > 0 else '') in rider:
						getattr(self, 'riderTag' + str(tag), None).ChangeValue(rider['Tag' + (str(tag) if tag > 0 else '')])
						getattr(self, 'riderTag' + str(tag), None).SetBackgroundColour(wx.WHITE)
					return
			Utils.writeLog('ChangeTags/revertTag: Failed to find bib ' + str(self.bib) + ' in raceEntryDict')
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		
	def refresh( self, event=None):
		database = Model.database
		if database is None:
			return
		self.nameLabel.SetLabel( 'Tags for racer #' + str(self.bib) + ' ' + database.getRiderName(self.bib, True) + ' in race ' + str(self.race+1) + ':\n' )
		self.season = database.curSeason
		self.evt = database.curEvt
		self.rnd = database.curRnd
		if self.season is not None and self.evt is not None and self.rnd is not None:
			try:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				rndName = list(evt['rounds'])[self.rnd]
				rnd = evt['rounds'][rndName]
				race = rnd['races'][self.race]
				rider = database.getRider(self.bib)
				for raceEntryDict in race:
					if raceEntryDict['bib'] == self.bib:
						for i in range(10):
							if 'tag' + (str(i) if i > 0 else '') not in raceEntryDict or raceEntryDict['tag' + (str(i) if i > 0 else '')] is None:
								if 'Tag' + (str(i) if i > 0 else '') in rider:
									getattr(self, 'riderTag' + str(i), None).ChangeValue(rider['Tag' + (str(i) if i > 0 else '')])
								getattr(self, 'riderTag' + str(i), None).SetBackgroundColour(wx.WHITE)
							else:
								getattr(self, 'riderTag' + str(i), None).ChangeValue(raceEntryDict['tag' + (str(i) if i > 0 else '')])
								getattr(self, 'riderTag' + str(i), None).SetBackgroundColour(self.orangeColour)
						return
				Utils.writeLog('ChangeTags/refresh: Failed to find bib ' + str(self.bib) + ' in raceEntryDict')
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
		for i in range(10):
			getattr(self, 'riderTag' + str(i), None).ChangeValue('')
			getattr(self, 'riderTag' + str(i), None).SetBackgroundColour(wx.WHITE)
