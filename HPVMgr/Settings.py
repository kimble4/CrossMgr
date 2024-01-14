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

class Settings( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		self.parent = parent
		bs = wx.BoxSizer(wx.VERTICAL)
		hs = wx.BoxSizer(wx.HORIZONTAL)
		self.dbFileNameLabel = wx.StaticText( self, label=_('Database filename:') )
		self.dbFileName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER, size=(500,-1))
		self.dbFileName.SetValue( Utils.getDocumentsDir() )
		self.Bind( wx.EVT_TEXT_ENTER, self.onFileNameChanged, self.dbFileName )
		hs.Add(self.dbFileName, flag=wx.EXPAND  )
		self.btn = wx.Button( self, label='{}...'.format(_('Browse')) )
		self.btn.Bind( wx.EVT_BUTTON, self.onBrowseDatabase )
		hs.Add( self.btn, flag=wx.ALIGN_CENTER_VERTICAL )
		
		bs.Add( self.dbFileNameLabel )
		bs.Add( hs, flag=wx.EXPAND)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(bs)
		bs.SetSizeHints(self)
	
	def onFileNameChanged( self, event ):
		fn = self.dbFileName.GetValue()
		database = Model.database
		if database is None:
			return
		oldfn = database.fileName
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
				print('filename is now: ' + str(fn))
				database.fileName = fn
				database.setChanged()
		
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
							style=wx.FD_OPEN ) as dlg:
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
						print('filename is now: ' + str(fn))
						database.fileName = fn
						database.setChanged()
		

	def refresh( self ):
		database = Model.database
		if database is None:
			self.dbFileName.SetValue('')
			return
		fn = database.fileName if database.fileName is not None else ''
		self.dbFileName.SetValue( fn )
