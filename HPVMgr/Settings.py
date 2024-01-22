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
		vs = wx.BoxSizer(wx.VERTICAL)
		hs = wx.BoxSizer(wx.HORIZONTAL)
		
		hs.Add( wx.StaticText( self, label='Default font size:'), flag=wx.ALIGN_CENTER_VERTICAL )
		self.fontSize = intctrl.IntCtrl( self, value=10, name='Default font size', min=6, max=72, limited=0, allow_none=0 )
		hs.Add( self.fontSize, flag=wx.ALIGN_CENTER_VERTICAL )
		vs.Add( hs, flag=wx.EXPAND )
		
		hs = wx.BoxSizer(wx.HORIZONTAL)
		self.dbFileNameLabel = wx.StaticText( self, label=_('Database filename:') )
		hs.Add( self.dbFileNameLabel, flag=wx.ALIGN_CENTRE_VERTICAL)
		self.dbFileName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.dbFileName.SetValue( Utils.getDocumentsDir() )
		hs.Add(self.dbFileName, flag=wx.ALIGN_CENTRE_VERTICAL  )
		self.btn = wx.Button( self, label='{}...'.format(_('Browse')) )
		self.btn.Bind( wx.EVT_BUTTON, self.onBrowseDatabase )
		hs.Add( self.btn, flag=wx.ALIGN_CENTER_VERTICAL )
		
		
		vs.Add( hs, flag=wx.EXPAND)
		
		self.copyTagsWithDelim = wx.CheckBox( self, label='Copy tags with delmiters (for MultiReader)' )
		vs.Add( self.copyTagsWithDelim )
		
		hs =  wx.BoxSizer(wx.HORIZONTAL)
		self.tagTemplateLabel = wx.StaticText( self, label=_('Tag template:') )
		hs.Add( self.tagTemplateLabel, flag=wx.ALIGN_CENTRE_VERTICAL )
		self.tagTemplate = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.tagTemplate.SetToolTip( wx.ToolTip('Python format string to init tags of new riders'))
		hs.Add( self.tagTemplate, flag=wx.ALIGN_CENTRE_VERTICAL )
		vs.Add( hs, flag=wx.EXPAND )
		
		hs =  wx.BoxSizer(wx.HORIZONTAL)
		self.eventCategoryTemplateLabel = wx.StaticText( self, label=_('EventCategory template:') )
		hs.Add( self.eventCategoryTemplateLabel, flag=wx.ALIGN_CENTRE_VERTICAL )
		self.eventCategoryTemplate = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.eventCategoryTemplate.SetToolTip( wx.ToolTip('Python format string for EventCategory names'))
		hs.Add( self.eventCategoryTemplate, flag=wx.ALIGN_CENTRE_VERTICAL )
		vs.Add( hs, flag=wx.EXPAND )
		
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		vs.Add( self.commitButton )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
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

	def commit( self, event=None ):
		Utils.writeLog('Settings commit: ' + str(event))
		database = Model.database
		if database is None:
			return
		with Model.LockDatabase() as db:
			fn = self.dbFileName.GetValue()
			oldfn = database.fileName
			if fn is not '' and fn != oldfn:
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
			db.copyTagsWithDelim = self.copyTagsWithDelim.IsChecked()
			db.tagTemplate = self.tagTemplate.GetValue()
			db.eventCategoryTemplate = self.eventCategoryTemplate.GetValue()
			db.setChanged()
			config = Utils.getMainWin().config
			config.Write('dataFile', fn)
			fontSize = self.fontSize.GetValue()
			if fontSize != Utils.getMainWin().defaultFontSize:
				Utils.MessageOK( self, 'Font change will take when the application is restarted.' )
			config.WriteInt('fontSize', fontSize)  #try changing mainwin here?
			config.Flush()
		if event: #called by button
			self.refresh()
			self.Layout()

	def refresh( self ):
		database = Model.database
		if database is None:
			self.dbFileName.SetValue('')
			return
		config = Utils.getMainWin().config
		fn = database.fileName
		self.fontSize.SetValue(config.ReadInt('fontSize') if config.ReadInt('fontSize') else Utils.getMainWin().defaultFontSize)
		self.dbFileName.SetValue( fn if fn else '' )
		self.dbFileName.ShowPosition(self.dbFileName.GetLastPosition())
		self.copyTagsWithDelim.SetValue( getattr(database, 'copyTagsWithDelim', False) )
		self.tagTemplate.SetValue( getattr(database, 'tagTemplate', '') )
		self.eventCategoryTemplate.SetValue( getattr(database, 'eventCategoryTemplate', '') )
