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
import wx.lib.intctrl as intctrl

class Settings( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		self.parent = parent
		
		self.tagTemplates = {}
		
		vs = wx.BoxSizer(wx.VERTICAL)
		gbs = wx.GridBagSizer(5, 5)
		
		row = 0
		
		gbs.Add( wx.StaticText( self, label='Default font size:'), pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		self.fontSize = intctrl.IntCtrl( self, value=10, name='Default font size', min=6, max=72, limited=0, allow_none=0 )
		self.fontSize.Bind( wx.EVT_TEXT, self.onEdited)
		gbs.Add( self.fontSize, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )

		row += 1

		self.dbFileNameLabel = wx.StaticText( self, label=_('Database filename:') )
		gbs.Add( self.dbFileNameLabel, pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
		self.dbFileName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.dbFileName.SetValue( Utils.getDocumentsDir() )
		self.dbFileName.Bind( wx.EVT_TEXT, self.onEdited)
		gbs.Add(self.dbFileName, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL  )
		self.btn = wx.Button( self, label='{}...'.format(_('Browse')) )
		self.btn.Bind( wx.EVT_BUTTON, self.onBrowseDatabase )
		gbs.Add( self.btn, pos=(row,3), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL )
		
		row += 1

		gbs.Add( wx.StaticText(self, label='Allocate bib numbers starting from: '), pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.allocateBibsFrom = intctrl.IntCtrl( self, value=1, name='Allocate bibs from', min=0, limited=0, allow_none=1, style=wx.TE_PROCESS_ENTER )
		self.allocateBibsFrom.Bind( wx.EVT_TEXT, self.onEdited)
		gbs.Add( self.allocateBibsFrom, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		
		self.copyTagsWithDelim = wx.CheckBox( self, label='Copy tags with delimiters (for MultiReader)' )
		self.copyTagsWithDelim.Bind( wx.EVT_CHECKBOX, self.onEdited)
		gbs.Add( self.copyTagsWithDelim, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )

		row += 1
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.tagTemplateNr = wx.Choice( self, choices=['Tag'+str(n) for n in range(10)] )
		self.tagTemplateNr.SetSelection(0)
		self.Bind( wx.EVT_CHOICE, self.onChangeTagTemplateNr, self.tagTemplateNr )
		hs.Add( self.tagTemplateNr, flag=wx.ALIGN_CENTER_VERTICAL )
		self.tagTemplateLabel = wx.StaticText( self, label=_(' template: ') )
		hs.Add( self.tagTemplateLabel, flag=wx.ALIGN_CENTRE_VERTICAL )
		gbs.Add( hs, pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		
		self.tagTemplate = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.tagTemplate.SetToolTip( wx.ToolTip('Python format string to init tags of new riders'))
		self.tagTemplate.Bind( wx.EVT_TEXT, self.onTagTemplateChanged )
		
		gbs.Add( self.tagTemplate, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		
		self.eventCategoryTemplateLabel = wx.StaticText( self, label=_('EventCategory template:') )
		gbs.Add( self.eventCategoryTemplateLabel, pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.eventCategoryTemplate = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.eventCategoryTemplate.SetToolTip( wx.ToolTip('Python format string for EventCategory names'))
		self.eventCategoryTemplate.Bind( wx.EVT_TEXT, self.onEdited)
		gbs.Add( self.eventCategoryTemplate, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )

		row += 1
		
		gbs.Add( wx.StaticText( self, label='Seconds before first TT rider start:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.ttStartDelay = intctrl.IntCtrl( self, value=60, name='TT start delay', min=0, max=3600, limited=1, allow_none=0 )
		self.ttStartDelay.Bind( wx.EVT_TEXT, self.onEdited)
		gbs.Add( self.ttStartDelay, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		
		gbs.Add( wx.StaticText( self, label='Seconds between TT riders:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.ttInterval = intctrl.IntCtrl( self, value=30, name='TT interval', min=1, max=3600, limited=1, allow_none=0 )
		self.ttInterval.Bind( wx.EVT_TEXT, self.onEdited)
		gbs.Add( self.ttInterval, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		
		self.writeAbbreviatedTeams = wx.CheckBox( self, label='Use abbreviated team names in sign-on sheet' )
		self.writeAbbreviatedTeams.Bind( wx.EVT_CHECKBOX, self.onEdited)
		gbs.Add( self.writeAbbreviatedTeams, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		row += 1
		
		self.useFactors = wx.CheckBox( self, label='Include para-cycling Factors in sign-on sheet' )
		self.useFactors.Bind( wx.EVT_CHECKBOX, self.onEdited)
		gbs.Add(self.useFactors, pos=(row,1), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL)
		
		vs.Add(gbs, flag=wx.EXPAND )
		vs.AddStretchSpacer()
		
		#commit button
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		hs.Add( self.commitButton )
		#edited warning
		self.editedWarning = wx.StaticText( self, label='' )
		hs.Add( self.editedWarning, flag=wx.ALIGN_CENTRE_VERTICAL )
		
		vs.Add( hs )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onEdited( self, event=None, warn=True ):
		if warn:
			self.editedWarning.SetLabel('Edited!')
		else:
			self.editedWarning.SetLabel('')
		
	def onBrowseDatabase( self, event ):
		database = Model.database
		if database is None:
			return
		defaultFile = self.dbFileName.GetValue()
		if defaultFile.endswith('.hdb'):
			dirName = os.path.dirname( defaultFile )
			fileName = os.path.basename( defaultFile )
		else:
			dirName = defaultFile
			fileName = ''
			if not dirName:
				dirName = Utils.getDocumentsDir()
		with wx.FileDialog( self, message=_("Choose Database File"),
							defaultDir=dirName, 
							defaultFile=fileName,
							wildcard=_("HPV database (*.hdb)|*.hdb"),
							style=wx.FD_SAVE ) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				fn = dlg.GetPath()
				if not fn.lower().endswith('.hdb'):
					fn += '.hdb'
				oldfn = database.fileName
				self.dbFileName.SetValue( fn )
				if fn != oldfn:
					if (
						not fn or
						Utils.MessageOKCancel(self.parent, '\n\n'.join( [
							_("The filename will be changed to:"),
							'{}',
							_("Continue?")]).format(fn), _("Change Filename?"))
					):
						if os.path.exists(fn):
							if not Utils.MessageOKCancel(self.parent, '\n\n'.join( [
									_("This file already exists:"),
									'{}',
									_("Overwrite?")]).format(fn), _("Overwrite Existing File?")):
								return
						Utils.writeLog('filename is now: ' + str(fn))
						database.fileName = fn
						database.setChanged()
		self.dbFileName.ShowPosition(self.dbFileName.GetLastPosition())
		
	def onChangeTagTemplateNr( self, event=None ):
		n = self.tagTemplateNr.GetSelection()
		if n is not wx.NOT_FOUND:
			self.tagTemplate.ChangeValue(self.tagTemplates[n] if n in self.tagTemplates else '')
		else:
			self.tagTemplate.ChangeValue('')
			
	def onTagTemplateChanged( self, event ):
		n = self.tagTemplateNr.GetSelection()
		if n is not wx.NOT_FOUND:
			self.tagTemplates[n] = self.tagTemplate.GetValue()
			self.onEdited()

	def commit( self, event=None ):
		Utils.writeLog('Settings commit: ' + str(event))
		config = Utils.getMainWin().config
		fontSize = self.fontSize.GetValue()
		if fontSize != Utils.getMainWin().defaultFontSize:
			Utils.MessageOK( self, 'Font change will take when the application is restarted.' )
		config.WriteInt('fontSize', fontSize)
		database = Model.database
		if database is None:
			config.Flush()
			if event: #called by button
				self.refresh()
				self.Layout()
			return
		with Model.LockDatabase() as db:
			fn = self.dbFileName.GetValue()
			oldfn = database.fileName
			if fn != '' and fn != oldfn:
				if (
					not fn or
					Utils.MessageOKCancel(self.parent, '\n\n'.join( [
						_("The filename will be changed to:"),
						'{}',
						_("Continue?")]).format(fn), _("Change Filename?"))
				):
					if os.path.exists(fn):
						if not Utils.MessageOKCancel(self.parent, '\n\n'.join( [
								_("This file already exists:"),
								'{}',
								_("Overwrite?")]).format(fn), _("Overwrite Existing File?")):
							return
					Utils.writeLog('filename is now: ' + str(fn))
					db.fileName = fn
			db.allocateBibsFrom = self.allocateBibsFrom.GetValue()
			db.copyTagsWithDelim = self.copyTagsWithDelim.IsChecked()
			# n = self.tagTemplateNr.GetSelection()
			# if n is not wx.NOT_FOUND:
			# 	db.tagTemplates[n] = self.tagTemplate.GetValue()
			for k, v in self.tagTemplates.items():
				db.tagTemplates[k] = v
			db.eventCategoryTemplate = self.eventCategoryTemplate.GetValue()
			db.writeAbbreviatedTeams = self.writeAbbreviatedTeams.IsChecked()
			db.ttStartDelay = self.ttStartDelay.GetValue()
			db.ttInterval = self.ttInterval.GetValue()
			db.useFactors = self.useFactors.IsChecked()
			db.setChanged()
			config.Write('dataFile', fn)
			self.onEdited(warn=False)
		if event: #called by button
			self.refresh()
			self.Layout()

	def refresh( self ):
		Utils.writeLog('Settings refresh')
		config = Utils.getMainWin().config
		self.fontSize.SetValue(config.ReadInt('fontSize') if config.ReadInt('fontSize') else Utils.getMainWin().defaultFontSize)
		self.tagTemplates.clear()
		database = Model.database
		if database is None:
			self.dbFileName.SetValue('')
			return
		fn = database.fileName
		self.dbFileName.SetValue( fn if fn else '' )
		self.dbFileName.ShowPosition(self.dbFileName.GetLastPosition())
		self.allocateBibsFrom.SetValue( getattr(database, 'allocateBibsFrom', '1') )
		self.copyTagsWithDelim.SetValue( getattr(database, 'copyTagsWithDelim', False) )
		for k, v in database.tagTemplates.items():
			self.tagTemplates[k] = v
		self.onChangeTagTemplateNr()
		self.eventCategoryTemplate.SetValue( getattr(database, 'eventCategoryTemplate', '') )
		self.ttStartDelay.SetValue( getattr(database, 'ttStartDelay', 60) )
		self.ttInterval.SetValue( getattr(database, 'ttInterval', 30) )
		self.writeAbbreviatedTeams.SetValue( getattr(database, 'writeAbbreviatedTeams', False) )
		self.useFactors.SetValue( getattr(database, 'useFactors', False) )
		self.onEdited(warn=False)
