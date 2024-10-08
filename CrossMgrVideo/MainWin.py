import platform
import os

# Apply workaround for cv2 slow open cameras.
if platform.system() == 'Windows':
	os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"

import wx
import wx.adv
import wx.lib.mixins.listctrl as listmix
import wx.lib.intctrl
import re
import sys
import cv2
import sys
import math
import json
import time
import socket
import atexit
import base64
import random
import tempfile
import threading
import webbrowser
import platform
import pickle
import gzip
import sqlite3
from time import sleep
import numpy as np
from queue import Queue, Empty
import ast

from datetime import datetime, date, timedelta, time

now = datetime.now

import Utils
import CVUtil
import CamServer
#from Clock import Clock
from SocketListener import SocketListener
from MultiCast import multicast_group, multicast_port
from Database import GlobalDatabase, DBWriter, Database, BulkInsertDBRows
from ScaledBitmap import ScaledBitmap
from Composite import CompositePanel
from ManageDatabase import ManageDatabase
from PhotoDialog import PhotoPanel
from AddPhotoHeader import AddPhotoHeader
from AddExifToJpeg import AddExifToJpeg
from PublishPhotoOptions import PublishPhotoOptionsDialog
from roundbutton import RoundButton
from GetMyIP import GetMyIP
from FIFOCache import FIFOCacheSet
from Version import AppVerName
import WebServer
from DateSelectDialog import DateSelectDialog
from HelpSearch import HelpSearchDialog, getHelpURL

imageWidth, imageHeight = 640, 480

tdCaptureBeforeDefault = timedelta(seconds=0.5)
tdCaptureAfterDefault = timedelta(seconds=2.0)

closeFinishThreshold = 3.0/30.0	# Time gap when two finishes are considered close.
closeColors = ('E50000','D1D200','00BF00', 'FFFFFF')
capturePreviewThreshold = 1.0/6  # Preview capture if within this many seconds of realtime (1/6 second to match framerate of preview window)


def getCloseFinishBitmaps( size=(16,16) ):
	bm = []
	dc = wx.MemoryDC()
	for c in closeColors:
		bitmap = wx.Bitmap( *size )
		dc.SelectObject( bitmap )
		dc.SetPen( wx.Pen(wx.Colour(0,0,0), 1) )
		dc.SetBrush( wx.Brush(wx.Colour(*[int(c[i:i+2],16) for i in range(0,6,2)]) ) )
		dc.DrawRectangle( 0, 0, size[0]-1, size[1]-1 )
		bm.append( bitmap )
	return bm

def getCloseFinishIndex( delta ):
	if delta > closeFinishThreshold:
		return 2
	if delta > closeFinishThreshold/2:
		return 1
	return 0

def setFont( font, w ):
	w.SetFont( font )
	return w

def OpenHelp():
	webbrowser.open( os.path.join(Utils.getHelpFolder(), 'QuickStart.html'), new=0, autoraise=1 )
	
def getInfo():
	app = AppVerName.split()[0]
	uname = platform.uname()
	info = {
		'{}_AppVersion'.format(app):	AppVerName,
		'{}_Timestamp'.format(app):		datetime.now(),
		'{}_User'.format(app):			os.path.basename(os.path.expanduser("~")),
		'{}_Python'.format(app):		sys.version.replace('\n', ' '),
	}
	info.update( {'{}_{}'.format(app, a.capitalize()): getattr(uname, a)
		for a in ('system', 'release', 'version', 'machine', 'processor') if getattr(uname, a, '') } )
	return info

import Resolutions
cameraResolutionChoices = tuple( Resolutions.resolutions + ['MAXxMAX'] )

def pixelsFromRes( res ):
	res = re.split( '[^0-9]', res )
	try:
		return int(res[0]), int(res[1])
	except ValueError:
		return 20000, 20000

def getCameraResolutionChoice( resolution ):
	for i, res in enumerate(cameraResolutionChoices):
		if resolution == pixelsFromRes(res):
			return i
	return len(cameraResolutionChoices) - 1

FOURCC_DEFAULT = 'MJPG'

class ConfigDialog( wx.Dialog ):
	def __init__( self, parent, usb=0, fps=30, width=imageWidth, height=imageHeight, fourcc='', availableCameraUsb=None, release=True, warnAnyDisconnectedCamera=False, id=wx.ID_ANY ):
		super().__init__( parent, id, title=_('CrossMgr Video Configuration') )
		
		fps = int( fps )
		availableCameraUsb = availableCameraUsb or []
		sizer = wx.BoxSizer( wx.VERTICAL )
		
		self.title = wx.StaticText( self, label='CrossMgr Video Configuration' )
		self.title.SetFont( wx.Font( (0,24), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ) )
		pfgs = wx.FlexGridSizer( rows=0, cols=2, vgap=4, hgap=8 )
		
		pfgs.Add( wx.StaticText(self, label='Camera USB'+':'), flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT )
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.usb = wx.Choice( self, choices=['{}'.format(i) for i in range(CamServer.CameraUsbMax)] )
		self.usb.SetSelection( usb )
		hs.Add( self.usb )
		hs.Add( wx.StaticText(self, label='cameras detected on {}'.format(availableCameraUsb)), flag=wx.ALIGN_CENTRE_VERTICAL|wx.LEFT, border=8 )
		pfgs.Add( hs )
		
		pfgs.Add( wx.StaticText(self, label='Camera Resolution'+':'), flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT )
		self.cameraResolution = wx.Choice( self, choices=cameraResolutionChoices )
		self.cameraResolution.SetSelection( getCameraResolutionChoice((width, height)) )
		pfgs.Add( self.cameraResolution )
		
		pfgs.Add( wx.StaticText(self, label='Frames per second'+':'), flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT )
		self.fps = wx.lib.intctrl.IntCtrl( self, value=fps, min=10, max=1000 )
		pfgs.Add( self.fps )
		
		pfgs.Add( wx.StaticText(self, label='FourCC'+':'), flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT )
		self.fourccChoices = ['', 'MJPG']
		self.fourcc = wx.Choice( self, choices=self.fourccChoices )
		self.fourcc.SetSelection( self.fourccChoices.index(fourcc if fourcc in self.fourccChoices else FOURCC_DEFAULT) )
		pfgs.Add( self.fourcc )
		
		pfgs.AddSpacer( 1 )
		pfgs.Add( wx.StaticText(self, label='\n'.join([
				'After pressing Apply, check the "Actual" fps on the main screen.',
				'The camera may not support the frame rate at the desired resolution,',
				'or may lower the frame rate in low light.',
				"If your fps is low or your camera doesn't work, try FourCC=MJPG.",
			])), flag=wx.RIGHT, border=4 )
		
		pfgs.Add( wx.StaticText(self, label='Release camera when capture disabled'+':'), flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT )
		self.releaseCamera = wx.CheckBox( self )
		self.releaseCamera.SetValue( release )
		pfgs.Add( self.releaseCamera )
		
		pfgs.Add( wx.StaticText(self, label='Warn when any camera disconnects'+':'), flag=wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_RIGHT )
		self.warnAnyDisconnectedCamera = wx.CheckBox( self )
		self.warnAnyDisconnectedCamera.SetValue( warnAnyDisconnectedCamera )
		pfgs.Add( self.warnAnyDisconnectedCamera )
		
		sizer.Add( self.title, flag=wx.ALL, border=4 )
		sizer.AddSpacer( 8 )
		sizer.Add( pfgs, flag=wx.ALL, border=4 )
		
		btnSizer = self.CreateButtonSizer( wx.OK|wx.APPLY|wx.CANCEL|wx.HELP )
		self.Bind( wx.EVT_BUTTON, lambda event: self.EndModal(wx.ID_APPLY), id=wx.ID_APPLY )
		self.Bind( wx.EVT_BUTTON, lambda event: OpenHelp(), id=wx.ID_HELP )
		
		if btnSizer:
			sizer.Add( btnSizer, flag=wx.ALL|wx.EXPAND, border=8 )
		
		self.SetSizerAndFit( sizer )
		
	def GetValues( self ):
		width, height = pixelsFromRes(cameraResolutionChoices[self.cameraResolution.GetSelection()])
		return {
			'usb':			self.usb.GetSelection(),
			'width':		width,
			'height':		height,
			'fps':			self.fps.GetValue(),
			'fourcc':		self.fourccChoices[self.fourcc.GetSelection()]
		}
	
	def GetRelease( self ):
		return( self.releaseCamera.IsChecked() )
	
	def GetWarnAnyDisconnectedCamera( self ):
		return( self.warnAnyDisconnectedCamera.IsChecked() )

snapshotEnableColour = wx.Colour(0,0,100)
snapshotDisableColour = wx.Colour(100,100,0)
autoCaptureEnableColour = wx.Colour(100,0,100)
autoCaptureDisableColour = wx.Colour(100,100,0)
captureEnableColour = wx.Colour(0,100,0)
captureDisableColour = wx.Colour(100,0,0)
		
def CreateCaptureButtons( parent ):	
	snapshot = RoundButton( parent, label="SNAPSHOT", size=(90,90) )
	snapshot.SetBackgroundColour( wx.WHITE )
	snapshot.SetForegroundColour( snapshotEnableColour )
	snapshot.SetFontToFitLabel( wx.Font(wx.FontInfo(10).Bold()) )
	snapshot.SetToolTip( _('Record a Single Frame') )
	
	autoCapture = RoundButton( parent, label="AUTO\nCAPTURE", size=(90,90) )
	autoCapture.SetBackgroundColour( wx.WHITE )
	autoCapture.SetForegroundColour( autoCaptureEnableColour )
	autoCapture.SetFontToFitLabel( wx.Font(wx.FontInfo(10).Bold()) )
	autoCapture.SetToolTip( _('Capture Video for an Automatic Interval\nSet in "Config Auto Capture"') )
	
	capture = RoundButton( parent, label="CAPTURE", size=(90,90) )
	capture.SetBackgroundColour( wx.WHITE )
	capture.SetForegroundColour( captureEnableColour )
	capture.SetFontToFitLabel( wx.Font(wx.FontInfo(10).Bold()) )
	capture.SetToolTip( _('Capture Video\nwhile the Button is held down') )
		
	return snapshot, autoCapture, capture

class FocusDialog( wx.Dialog ):
	def __init__( self, parent, id=wx.ID_ANY ):
		super().__init__( parent, id,
			style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX,
			title=_('CrossMgr Video Focus')
		)
		
		self.bitmapSz = None
		sizer = wx.BoxSizer( wx.VERTICAL )
		self.SetBackgroundColour( wx.Colour(232,232,232) )
				
		btnSizer = wx.BoxSizer( wx.HORIZONTAL )
		self.logo = Utils.GetPngBitmap('CrossMgrHeader.png')
		
		self.title = wx.StaticText(self, label='CrossMgr Video\nFocus Window', style=wx.ALIGN_RIGHT )
		self.title.SetFont( wx.Font( (0,28), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ) )
		self.explain = wx.StaticText(self, label='Click and Drag to Zoom In')
		self.snapshot, self.autoCapture, self.capture = CreateCaptureButtons( self )
		
		btnSizer.Add( wx.StaticBitmap(self, wx.ID_ANY, self.logo) )
		btnSizer.Add( self.title, flag=wx.ALL, border=10 )
		btnSizer.Add( self.explain, flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL, border=4 )
		btnSizer.AddStretchSpacer()
		btnSizer.Add( self.snapshot, flag=wx.ALL, border=4 )
		btnSizer.Add( self.autoCapture, flag=wx.ALL, border=4 )
		btnSizer.Add( self.capture, flag=wx.ALL, border=4 )
		
		sizer.Add( btnSizer, flag=wx.EXPAND )
		
		self.bitmap = ScaledBitmap( self, inset=True )
		sizer.Add( self.bitmap, 1, wx.EXPAND )
		self.SetSizerAndFit( sizer )
		
	def SetBitmap( self, bitmap ):
		sz = bitmap.GetSize()
		if sz != self.bitmapSz:
			if self.bitmapSz is None:
				r = wx.GetClientDisplayRect()
				dWidth, dHeight = r.GetWidth(), r.GetHeight()
				self.SetSize( (int(dWidth*0.85), int(dHeight*0.85)) )
			self.bitmapSz = sz
			self.SetTitle( '{} {}x{}'.format( _('CrossMgr Video Focus'), *sz ) )
		return self.bitmap.SetBitmap( bitmap )
		
	def SetTestBitmap( self ):
		self.bitmap.SetTestBitmap()

class TriggerDialog( wx.Dialog ):
	def __init__( self, parent, id=wx.ID_ANY ):
		super().__init__( parent, id, title=_('CrossMgr Video Trigger Editor') )
		
		self.db = None
		self.triggerId = None
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		gs = wx.FlexGridSizer( 2, 2, 4 )
		gs.AddGrowableCol( 1 )
		fieldNames = [h.replace('_', ' ').title() for h in GlobalDatabase().triggerEditFields]
		fieldNames.remove('Publish')
		self.editFields = []
		for f in fieldNames:
			gs.Add( wx.StaticText(self, label=f), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
			e = wx.TextCtrl(self, size=(500,-1) )
			gs.Add( e )
			self.editFields.append(e)
		gs.Add( wx.StaticText(self, label='Publish'), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		e = wx.CheckBox( self )
		gs.Add( e )
		self.editFields.append(e)
		
		btnSizer = self.CreateButtonSizer( wx.OK|wx.CANCEL )
		self.Bind( wx.EVT_BUTTON, self.onOK, id=wx.ID_OK )
		
		sizer.Add( gs, flag=wx.ALL, border=4 )
		if btnSizer:
			sizer.Add( btnSizer, flag=wx.ALL|wx.EXPAND, border=4 )
		self.SetSizerAndFit( sizer )
	
	def set( self, db, triggerId ):
		self.db = db
		self.triggerId = triggerId
		ef = db.getTriggerEditFields( triggerId )
		for e, f in zip(self.editFields, Database.triggerEditFields):
			v = ef.get(f,'')
			if f == 'publish':
				e.SetValue( bool( v ) )
			else:
				e.SetValue( '{}'.format(v or '') )
	
	def get( self ):
		values = {}
		for f, e in zip(Database.triggerEditFields, self.editFields):
			v = e.GetValue()
			if f == 'bib':
				try:
					v = int(v)
				except Exception:
					v = ''
			if f == 'publish':
				if v:
					v = 1
				else:
					v = 0
			values[f] = v
		return values
	
	def commit( self ):
		GlobalDatabase().setTriggerEditFields( self.triggerId, **self.get() )
	
	def onOK( self, event ):
		self.commit()
		self.EndModal( wx.ID_OK )
		
class AutoCaptureDialog( wx.Dialog ):
	def __init__( self, parent, id=wx.ID_ANY ):
		super().__init__( parent, id, title=_('CrossMgr Video Auto Capture') )
		
		sizer = wx.BoxSizer( wx.VERTICAL )
		
		sizer.Add( wx.StaticText(self, label="Configure what to Capture on each Trigger"), flag=wx.ALL, border=8 )

		gs = wx.FlexGridSizer( 2, 2, 4 )
		gs.AddGrowableCol( 1 )
		
		gs.Add( wx.StaticText(self, label="Capture"), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		self.autoCaptureClosestFrames = wx.Choice( self, choices=('by Seconds', 'Closest Frame to Trigger', 'Closest 2 Frames to Trigger') )
		self.autoCaptureClosestFrames.Bind( wx.EVT_CHOICE, self.onChoice )
		gs.Add( self.autoCaptureClosestFrames )
		
		fieldNames = ('Capture Seconds Before Trigger', 'Capture Seconds After Trigger')
		self.labelFields = []
		self.editFields = []
		for f in fieldNames:
			self.labelFields.append( wx.StaticText(self, label=f) )
			gs.Add( self.labelFields[-1], flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
			self.editFields.append( wx.TextCtrl(self, size=(60,-1) ) )
			gs.Add( self.editFields[-1] )
			
		gs.Add( wx.StaticText(self, label="Seqential bib for captures"), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		self.sequentialBibs = wx.CheckBox( self )
		gs.Add( self.sequentialBibs )
		gs.Add( wx.StaticText(self, label="Play shutter sound"), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		self.shutterSound = wx.CheckBox( self )
		gs.Add( self.shutterSound )
			
		sizer.Add( gs, flag=wx.ALL, border=4 )
		
		btnSizer = self.CreateButtonSizer( wx.OK|wx.CANCEL )		
		if btnSizer:
			sizer.Add( btnSizer, flag=wx.ALL|wx.EXPAND, border=4 )
		
		self.SetSizerAndFit( sizer )
	
	def onChoice( self, event=None ):
		enable = (self.autoCaptureClosestFrames.GetSelection() == 0)
		for w in (self.labelFields + self.editFields):
			w.Enable( enable )
	
	def set( self, s_before, s_after, autoCaptureClosestFrames=0, sequentialBibs=True, shutterSound=True ):
		for w, v in zip( self.editFields, (s_before, s_after) ):
			w.SetValue( '{:.3f}'.format(v) )
		self.autoCaptureClosestFrames.SetSelection( autoCaptureClosestFrames )
		self.sequentialBibs.SetValue( sequentialBibs )
		self.shutterSound.SetValue( shutterSound )
		self.onChoice()
	
	def get( self ):
		def fixValue( v ):
			try:
				return abs(float(v))
			except Exception:
				return None
		return [fixValue(e.GetValue()) for e in self.editFields] + [self.autoCaptureClosestFrames.GetSelection()] + [self.sequentialBibs.GetValue()] + [self.shutterSound.GetValue()]
		
class AutoWidthListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
	def __init__(self, parent, ID = wx.ID_ANY, pos=wx.DefaultPosition,
				 size=wx.DefaultSize, style=0):
		wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
		listmix.ListCtrlAutoWidthMixin.__init__(self)

class MainWin( wx.Frame ):
	def __init__( self, parent, id = wx.ID_ANY, title='', size=(1000,800) ):
		super().__init__( parent, id, title, size=size )
		
		Utils.setMainWin( self )
		
		self.db = GlobalDatabase()
		
		self.bufferSecs = 10
		self.curFPS = 30.0
		self.setFPS( 30 )
		self.xFinish = None
		self.cameraDisconnected = True
		
		self.tFrameCount = self.tLaunch = self.tLast = now()
		self.frameCount = 0
		self.fpt = timedelta(seconds=0)
		self.iTriggerSelect = None
		self.iTriggerAdded = None
		self.triggerInfo = None
		self.tsMax = None
		self.inCapture = 0	# Use an integer so we can support reentrant captures.
		
		self.captureTimer = wx.CallLater( 10, self.stopCapture )
		self.availableCameraUsb = []
		
		self.tdCaptureBefore = tdCaptureBeforeDefault
		self.tdCaptureAfter = tdCaptureAfterDefault
		self.autoCaptureClosestFrames = 0
		self.shutterSound = True
		self.autoCaptureSequentialBibs = True
		self.lastCapturePreview = datetime.min
		
		self.isShutdown = False

		dataDir = Utils.getHomeDir()
		configFileName = os.path.join(dataDir, 'CrossMgrVideo.cfg')
		self.config = wx.Config(appName="CrossMgrVideo",
								vendorName="Edward.Sitarski@gmail.com",
								localFilename=configFileName
		)
		
		self.requestQ = Queue()		# Select photos from photobuf.
		self.dbWriterQ = Queue()	# Photos waiting to be written
		self.messageQ = Queue()		# Collection point for all status/failure messages.
		self.captureProgressQ = Queue()	# Notification of captures in progress.
		
		self.pauseBitmap = Utils.getBitmap('pause.png') # Store these in memory so we can quickly swap them
		self.recordBitmap = Utils.getBitmap('record.png')
		
		#-------------------------------------------

		self.menuBar = wx.MenuBar(wx.MB_DOCKABLE)
		if 'WXMAC' in wx.Platform:
			self.appleMenu = self.menuBar.OSXGetAppleMenu()
			self.appleMenu.SetTitle("CrossMgrVideo")
			self.appleMenu.Insert(0, wx.ID_ABOUT, "&About")
			self.Bind(wx.EVT_MENU, self.OnAboutBox, id=wx.ID_ABOUT)
		else:
			self.fileMenu = wx.Menu()
			item = self.fileMenu.Append( wx.ID_EXIT, "Exit", "Exit CrossMgrVideo" )
			self.Bind(wx.EVT_MENU, self.onCloseWindow, id=wx.ID_EXIT)
			self.menuBar.Append(self.fileMenu, "&File")

		#-------------------------------------------
		self.toolsMenu = wx.Menu()
		
		self.disableCapture = self.toolsMenu.Append( wx.ID_ANY, "&Disable Capture\tCtrl+D", "Disable the capture thread", kind=wx.ITEM_CHECK)
		self.disableCapture.Check( False )
		self.Bind(wx.EVT_MENU, self.onMenuDisableCapture, self.disableCapture )
		
		item = self.toolsMenu.Append( wx.ID_ANY, "R&eset Camera\tCtrl+R", "Reset the camera configuration" )
		self.Bind(wx.EVT_MENU, self.resetCamera, item )
		
		item = self.toolsMenu.Append( wx.ID_ANY, "Monitor/&Focus\tCtrl+F", "Large window to focus the camera" )
		self.Bind(wx.EVT_MENU, self.onFocus, item )

		item = self.toolsMenu.Append( wx.ID_ANY, "&Configure Autocapture", "Configure Autocapture parameters" )
		self.Bind(wx.EVT_MENU, self.autoCaptureConfig, item )

		item = self.toolsMenu.Append( wx.ID_ANY, "&Manage Database", "Manage the database" )
		self.Bind(wx.EVT_MENU, self.manageDatabase, item )
		
		self.toolsMenu.AppendSeparator()
		item = self.toolsMenu.Append( wx.ID_ANY, "Copy &Log File to Clipboard", "Copy Log File to Clipboard" )
		self.Bind(wx.EVT_MENU, self.copyLogFileToClipboard, item )

		self.toolsMenu.AppendSeparator()
		item = self.toolsMenu.Append( wx.ID_ANY, "Export Photos...", "Export photos and triggers" )
		self.Bind(wx.EVT_MENU, self.exportDB, item )

		item = self.toolsMenu.Append( wx.ID_ANY, "Import Photos...", "Import photos and triggers" )
		self.Bind(wx.EVT_MENU, self.importDB, item )

		self.menuBar.Append(self.toolsMenu, "&Tools")

		#-------------------------------------------
		if 'WXMAC' not in wx.Platform:
			self.helpMenu = wx.Menu()
			
			item = self.helpMenu.Append( wx.ID_HELP, "&Help", "CrossMgrVideo QuickHelp" )
			self.Bind(wx.EVT_MENU, self.onHelp, item )
			
			item = self.helpMenu.Append( wx.ID_ANY, _("Help &Search..."), _("Search Help...") )
			self.Bind(wx.EVT_MENU, self.menuHelpSearch, item )
			self.helpSearch = HelpSearchDialog( self, title=_('Help Search') )
			
			item = self.helpMenu.Append( wx.ID_ABOUT, "&About", "About CrossMgrVideo" )
			self.Bind(wx.EVT_MENU, self.OnAboutBox, item )
			
			self.menuBar.Append(self.helpMenu, "Help")
		#-------------------------------------------

		self.SetMenuBar( self.menuBar )
		
		self.SetBackgroundColour( wx.Colour(232,232,232) )
		
		self.focusDialog = FocusDialog( self )
		self.autoCaptureDialog = AutoCaptureDialog( self )
		self.triggerDialog = TriggerDialog( self )
				
		mainSizer = wx.BoxSizer( wx.VERTICAL )
		
		#------------------------------------------------------------------------------------------------
		headerSizer = wx.BoxSizer( wx.HORIZONTAL )
		
		self.logo = Utils.GetPngBitmap('CrossMgrHeader.png')
		headerSizer.Add( wx.StaticBitmap(self, wx.ID_ANY, self.logo) )
		
		self.title = wx.StaticText(self, label='CrossMgr Video\nVersion {}'.format(AppVerName.split()[1]), style=wx.ALIGN_RIGHT )
		self.title.SetFont( wx.Font( (0,28), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL ) )
		headerSizer.Add( self.title, flag=wx.ALL, border=10 )
		
		# clock = Clock( self, size=(90,90) )
		# clock.SetBackgroundColour( self.GetBackgroundColour() )
		# clock.Start()

		# headerSizer.Add( clock, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT|wx.RIGHT, border=4 )
		
		#------------------------------------------------------------------------------
		self.usb = wx.StaticText( self, label='[0, 2, 4, 6, 8]' )
		self.cameraResolution = wx.StaticText( self )
		self.targetFPS = wx.StaticText( self, label='30.0 fps' )
		self.actualFPS = wx.StaticText( self, label='30.0 fps' )
		self.fourcc = wx.StaticText( self, label=FOURCC_DEFAULT )
		
		boldFont = self.usb.GetFont()
		boldFont.SetWeight( wx.BOLD )
		for w in (self.usb, self.cameraResolution, self.targetFPS, self.actualFPS, self.fourcc):
			w.SetFont( boldFont )
		
		fgs = wx.FlexGridSizer( 2, 2, 2 )	# 2 Cols
		fgs.Add( wx.StaticText(self, label='Camera USB:'), flag=wx.ALIGN_RIGHT )
		fgs.Add( self.usb )
		
		fgs.Add( wx.StaticText(self, label='Resolution:'), flag=wx.ALIGN_RIGHT )
		fgs.Add( self.cameraResolution, flag=wx.ALIGN_RIGHT )
		
		fgs.Add( wx.StaticText(self, label='FourCC:'), flag=wx.ALIGN_RIGHT )
		fgs.Add( self.fourcc, flag=wx.ALIGN_RIGHT )
		
		fgs.Add( wx.StaticText(self, label='Target:'), flag=wx.ALIGN_RIGHT )
		fgs.Add( self.targetFPS, flag=wx.EXPAND|wx.ALIGN_RIGHT )
		
		fgs.Add( wx.StaticText(self, label='Actual:'), flag=wx.ALIGN_RIGHT )
		fgs.Add( self.actualFPS, flag=wx.EXPAND|wx.ALIGN_RIGHT )
		
		self.focus = wx.Button( self, label="Monitor/Focus" )
		self.focus.Bind( wx.EVT_BUTTON, self.onFocus )
		
		self.reset = wx.Button( self, label="Reset Camera" )
		self.reset.Bind( wx.EVT_BUTTON, self.resetCamera )
		
		self.manage = wx.Button( self, label="Manage Database" )
		self.manage.Bind( wx.EVT_BUTTON, self.manageDatabase )
		
		self.autoCaptureBtn = wx.Button( self, label="Config Auto Capture" )
		self.autoCaptureBtn.Bind( wx.EVT_BUTTON, self.autoCaptureConfig )
		
		self.webBtn = wx.Button( self, label="Web Page" )
		self.webBtn.Bind( wx.EVT_BUTTON, self.onWeb )
		
		self.help = wx.Button( self, wx.ID_HELP )
		self.help.Bind( wx.EVT_BUTTON, self.onHelp )
		
		self.snapshot, self.autoCapture, self.capture = CreateCaptureButtons( self )
		
		self.snapshot.Bind( wx.EVT_LEFT_DOWN, self.onStartSnapshot )
		self.focusDialog.snapshot.Bind( wx.EVT_LEFT_DOWN, self.onStartSnapshot )
		self.autoCapture.Bind( wx.EVT_LEFT_DOWN, self.onStartAutoCapture )
		self.focusDialog.autoCapture.Bind( wx.EVT_LEFT_DOWN, self.onStartAutoCapture )
		self.capture.Bind( wx.EVT_LEFT_DOWN, self.onStartCapture )
		self.capture.Bind( wx.EVT_LEFT_UP, self.onStopCapture )
		self.focusDialog.capture.Bind( wx.EVT_LEFT_DOWN, self.onStartCapture )
		self.focusDialog.capture.Bind( wx.EVT_LEFT_UP, self.onStopCapture )
		
		headerSizer.Add( fgs, flag=wx.ALIGN_CENTER_VERTICAL )
		
		fgs = wx.FlexGridSizer( rows=2, cols=0, hgap=8, vgap=4 )
		
		fgs.Add( self.focus, flag=wx.EXPAND )
		fgs.Add( self.reset, flag=wx.EXPAND )
		fgs.Add( self.manage, flag=wx.EXPAND )
		fgs.Add( self.autoCaptureBtn, flag=wx.EXPAND )
		fgs.Add( self.webBtn, flag=wx.EXPAND )
		fgs.Add( self.help, flag=wx.EXPAND )
		
		headerSizer.Add( fgs, flag=wx.ALIGN_CENTRE|wx.LEFT, border=4 )
		headerSizer.AddStretchSpacer()
		
		headerSizer.Add( self.snapshot, flag=wx.ALIGN_CENTRE_VERTICAL|wx.LEFT, border=8 )
		headerSizer.Add( self.autoCapture, flag=wx.ALIGN_CENTRE_VERTICAL|wx.LEFT, border=8 )
		headerSizer.Add( self.capture, flag=wx.ALIGN_CENTRE_VERTICAL|wx.LEFT|wx.RIGHT, border=8 )

		#------------------------------------------------------------------------------
		mainSizer.Add( headerSizer, flag=wx.EXPAND )
		
		#------------------------------------------------------------------------------------------------
		self.notebook = wx.Notebook( self, size=(-1,wx.GetDisplaySize()[1]//2), style=wx.NB_BOTTOM )
		self.notebook.Bind( wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onNotebook )
		
		self.photoPanel = PhotoPanel( self.notebook )
		self.finishStrip = CompositePanel( self.notebook )
		
		self.notebook.AddPage(self.photoPanel, "Images")
		self.notebook.AddPage(self.finishStrip, "Finish Strip")
		
		self.primaryBitmap = ScaledBitmap( self, style=wx.BORDER_SUNKEN, size=(int(imageWidth*0.4), int(imageHeight*0.4)) )
		self.primaryBitmap.SetTestBitmap()
		self.primaryBitmap.Bind( wx.EVT_LEFT_UP, self.onFocus )
		self.primaryBitmap.Bind( wx.EVT_RIGHT_UP, self.onFocus )
		
		hsDate = wx.BoxSizer( wx.HORIZONTAL )
		hsDate.Add( wx.StaticText(self, label='Show Triggers for'), flag=wx.ALIGN_CENTER_VERTICAL )
		tQuery = now()
		self.date = wx.adv.DatePickerCtrl(
			self,
			dt=wx.DateTime.FromDMY( tQuery.day, tQuery.month-1, tQuery.year ),
			style=wx.adv.DP_DROPDOWN|wx.adv.DP_SHOWCENTURY
		)
		self.date.Bind( wx.adv.EVT_DATE_CHANGED, self.onQueryDateChanged )
		hsDate.Add( self.date, flag=wx.LEFT, border=2 )
		
		self.dateSelect = wx.Button( self, label='Select &Date' )
		hsDate.Add( self.dateSelect, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=2 )
		self.dateSelect.Bind( wx.EVT_BUTTON, self.onDateSelect )
		
		hsDate.Add( wx.StaticText(self, label='Filter by Bib'), flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=12 )
		self.bib = wx.lib.intctrl.IntCtrl( self, style=wx.TE_PROCESS_ENTER, size=(64,-1), min=1, allow_none=True, value=None )
		self.bib.Bind( wx.EVT_TEXT, self.onQueryBibChanged )
		hsDate.Add( self.bib, flag=wx.LEFT, border=2 )
		
		self.refreshBtn = wx.Button( self, label="&Refresh" )
		self.refreshBtn.Bind( wx.EVT_BUTTON, lambda event: self.refreshTriggers(replace=True, selectLatest=False) )
		hsDate.Add( self.refreshBtn, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=8 )
		
		self.publishPhotos = wx.Button( self, label="Publish P&hotos" )
		self.publishPhotos.SetToolTip( "Write a JPG for each Trigger into a Folder" )
		self.publishPhotos.Bind( wx.EVT_BUTTON, self.onPublishPhotos )
		hsDate.Add( self.publishPhotos, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=32 )
		
		self.publishWebPage = wx.Button( self, label="Photo &Web Page" )
		self.publishWebPage.SetToolTip( "Write a JPG for each Trigger and create a Web Page" )
		self.publishWebPage.Bind( wx.EVT_BUTTON, self.onPublishWebPage )
		hsDate.Add( self.publishWebPage, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=32 )
		
		self.autoSelect = wx.Choice( self, choices=['Autoselect latest', 'Fast preview', 'Scroll triggers', 'Autoselect off', 'Minimise DB', 'Min DB (no preview)'] )
		self.autoSelect.Bind (wx.EVT_CHOICE, self.onAutoSelect )
		hsDate.Add( self.autoSelect, flag=wx.ALIGN_CENTER_VERTICAL|wx.LEFT, border=32 )
		
		self.tsQueryLower = date(tQuery.year, tQuery.month, tQuery.day)
		self.tsQueryUpper = self.tsQueryLower + timedelta(days=1)
		self.bibQuery = None
		
		self.triggerList = AutoWidthListCtrl( self, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_HRULES|wx.LC_SINGLE_SEL )
		
		self.sm_close = getCloseFinishBitmaps()
		images = self.sm_close.copy()
		self.sm_up = Utils.GetPngBitmap('SmallUpArrow.png')
		self.sm_dn = Utils.GetPngBitmap('SmallDownArrow.png')
		images.extend( [self.sm_up, self.sm_dn] )
		self.triggerList.SetSmallImages( images )
		
		self.fieldCol = {f:c for c, f in enumerate('ts bib name machine team wave race_name frames view kmh mph publish note'.split())}
		self.fieldHeaders = ['Triggered at', 'Bib', 'Name', 'Machine', 'Team', 'Wave', 'Race', 'Frames', 'View', 'km/h', 'mph', 'Publish', 'Note']
		formatRightHeaders = {'Bib','Frames','km/h','mph'}
		formatMiddleHeaders = {'View', 'Publish'}
		self.hiddenTriggerCols = []
		for i, h in enumerate(self.fieldHeaders):
			if h in formatRightHeaders:
				align = wx.LIST_FORMAT_RIGHT
			elif h in formatMiddleHeaders:
				align = wx.LIST_FORMAT_CENTRE
			else:
				align = wx.LIST_FORMAT_LEFT
			self.triggerList.InsertColumn( i, h, align )
		self.iNoteCol = self.fieldCol['note']
		
		self.triggerList.Bind( wx.EVT_LIST_ITEM_SELECTED, self.onTriggerSelected )
		self.triggerList.Bind( wx.EVT_LIST_ITEM_ACTIVATED, self.onTriggerEdit )
		self.triggerList.Bind( wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onTriggerRightClick )
		self.triggerList.Bind( wx.EVT_LIST_KEY_DOWN, self.onTriggerKey )
		#self.triggerList.Bind( wx.EVT_LIST_DELETE_ITEM, self.onTriggerDelete )
		self.triggerList.Bind( wx.EVT_LIST_COL_RIGHT_CLICK, self.onTriggerColumnRightClick )
		
		vsTriggers = wx.BoxSizer( wx.VERTICAL )
		vsTriggers.Add( hsDate )
		vsTriggers.Add( self.triggerList, 1, flag=wx.EXPAND|wx.TOP, border=2)
		
		#------------------------------------------------------------------------------------------------
		mainSizer.Add( self.notebook, 1, flag=wx.EXPAND )
		
		border=2
		row1Sizer = wx.BoxSizer( wx.HORIZONTAL )
		vbs = wx.BoxSizer (wx.VERTICAL)
		vbs.Add( self.primaryBitmap, flag=wx.ALL, border=border )
		
		captureProgress = wx.BoxSizer( wx.HORIZONTAL )
		self.capturingIcon = wx.StaticBitmap( self, bitmap=self.pauseBitmap )
		captureProgress.Add( self.capturingIcon )
		pts = wx.BoxSizer (wx.VERTICAL)
		self.capturingText =  wx.StaticText(self, label='Waiting for trigger...')
		pts.Add( self.capturingText, flag=wx.ALIGN_LEFT )
		self.capturingTime =  wx.StaticText(self, label='')
		pts.Add( self.capturingTime, flag=wx.ALIGN_LEFT )
		captureProgress.Add( pts, flag=wx.ALL, border=border )
		vbs.Add(captureProgress, flag=wx.ALL, border=border )
		row1Sizer.Add( vbs, flag=wx.ALL, border=border )
		row1Sizer.Add( vsTriggers, 1, flag=wx.TOP|wx.BOTTOM|wx.RIGHT|wx.EXPAND, border=border )
		mainSizer.Add( row1Sizer, flag=wx.EXPAND )
				
		self.Bind(wx.EVT_CLOSE, self.onCloseWindow)

		self.readOptions()
		self.updateFPS( int(float(self.targetFPS.GetLabel().split()[0])) )
		self.updateAutoCaptureLabel()
		self.SetSizerAndFit( mainSizer )
		
		# Add joystick capture.  Trigger capture while button 1 on the joystick is pressed.
		self.capturing = False
		self.joystick = wx.adv.Joystick()
		self.joystick.SetCapture( self )
		self.Bind(wx.EVT_JOY_BUTTON_DOWN, self.onJoystickButton)
		self.Bind(wx.EVT_JOY_BUTTON_UP, self.onJoystickButton)
		
		# Add keyboard accellerators.

		idStartAutoCapture = wx.NewIdRef()
		idToggleCapture = wx.NewIdRef()
		
		entries = [wx.AcceleratorEntry()]
		entries[0].Set(wx.ACCEL_CTRL, ord('A'), idStartAutoCapture)

		self.Bind(wx.EVT_MENU, self.onStartAutoCaptureAccel, id=idStartAutoCapture)		
		self.SetAcceleratorTable( wx.AcceleratorTable(entries) )

		# Start the message reporting thread so we can see what is going on.
		self.messageThread = threading.Thread( target=self.showMessages, daemon=True )
		self.messageThread.start()
		
		wx.CallLater( 300, self.refreshTriggers, selectLatest=True )
		
		# Add event handlers to the app as this is the last window to process events.
		'''
		# Do not process the space key as it messes up when typing into the notes dialog.
		wx.App.Get().Bind( wx.EVT_CHAR_HOOK, self.OnKeyDown )
		wx.App.Get().Bind( wx.EVT_KEY_UP, self.OnKeyUp )
		'''
	
	'''
	def OnKeyDown( self, event ):
		#print( 'OnKeyDown', event.GetKeyCode() )
		if not self.capturing:
			if event.GetKeyCode() == wx.WXK_SHIFT:
				# Toggle Capture on shift key.  Use Shift key as it doesn't auto-repeat.
				self.capturing = True
				event.SetEventObject( self.capture )
				self.onStartCapture( event )
			elif event.GetKeyCode() == wx.WXK_SPACE:
				# Trigger Auto Capture on Space Bar.
				event.SetEventObject( self.autoCapture )
				self.onStartAutoCapture( event )
		event.Skip()
	
	def OnKeyUp( self, event ):
		#print( 'OnKeyUp', event.GetKeyCode() )
		if self.capturing and event.GetKeyCode() == wx.WXK_SHIFT:
			# Toggle capture on shift key.  Use Shft as it doesn't auto-repeat.
			self.capturing = False
			event.SetEventObject( self.capture )
			self.onStopCapture( event )
		event.Skip()
	'''
	
	def OnAboutBox(self, e):
		description = "CrossMgrVideo - USB Camera support\nModified for use by the BHPC"

		licence = """CrossMgrVideo is free software; you can redistribute 
	it and/or modify it under the terms of the GNU General Public License as 
	published by the Free Software Foundation; either version 2 of the License, 
	or (at your option) any later version.

	CrossMgrVideo is distributed in the hope that it will be useful, 
	but WITHOUT ANY WARRANTY; without even the implied warranty of 
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
	See the GNU General Public License for more details. You should have 
	received a copy of the GNU General Public License along with File Hunter; 
	if not, write to the Free Software Foundation, Inc., 59 Temple Place, 
	Suite 330, Boston, MA  02111-1307  USA"""

		info = wx.adv.AboutDialogInfo()

		crossMgrPng = os.path.join( Utils.getImageFolder(), 'CrossMgrVideo.png' )
		info.SetIcon(wx.Icon(crossMgrPng, wx.BITMAP_TYPE_PNG))
		info.SetName('CrossMgrVideo')
		info.SetVersion(AppVerName.split(' ')[1])
		info.SetDescription(description)
		info.SetCopyright('(C) 2019-{} Edward Sitarski'.format(datetime.today().strftime('%Y')))
		info.SetWebSite('https://github.com/kimble4/CrossMgr')
		info.SetLicence(licence)

		wx.adv.AboutBox(info, self)

	def onHelp( self, event ):
		OpenHelp()
		
	def menuHelpSearch( self, event ):
		self.helpSearch.Show()
		
	def onWeb( self, event ):
		url = 'http://{}:{}'.format( GetMyIP(), WebServer.PORT_NUMBER )
		dateStrInitial = self.date.GetValue().Format('%Y-%m-%d')
		dateStrCur = datetime.now().strftime('%Y-%m-%d')
		if dateStrInitial != dateStrCur:
			url += '?date={}'.format( dateStrInitial )
		webbrowser.open( url, new=0, autoraise=1 )
		
	def exportDB( self, event ):
		fname = os.path.join( os.path.expanduser("~"), 'CrossMgrVideo-{}.gz'.format(self.tsQueryLower.strftime('%Y-%m-%d')) )
		with wx.MessageDialog( self,
				'Export all photos for this day.\n\n\tPhotos will be exported to:\n\n"{}"'.format(fname),
				'Photo Export',
				style=wx.OK|wx.CANCEL|wx.ICON_INFORMATION ) as dlg:
			if dlg.ShowModal() != wx.ID_OK:
				return		
		
		if os.path.exists(fname):
			os.remove( fname )

		progress = wx.ProgressDialog( 'Export Progress', 'Initializing...' )
		progress.SetRange( 1 )
		progress.Show()
		
		def getUpdateCB( msg ):
			msg += ' ({}/{})'
			def updateCB( count, total ):
				progress.Update( count, msg.format(count, total) )
			return updateCB

		db = GlobalDatabase()
		
		triggerFields = [f for f in db.triggerFieldsAll if f != 'id']
		photoFields = ['ts', 'jpg']
		
		tsQueryLower, tsQueryUpper = self.tsQueryLower, self.tsQueryUpper

		with gzip.open( fname, 'wb' ) as f:
			# Write out some info as a file header.
			pickle.dump( getInfo(), f, -1 )
			
			# Write out the fields we are using.
			pickle.dump( triggerFields, f, -1 )
			pickle.dump( photoFields, f, -1 )
			
			#-----------------------------------------------------------
			triggerTS = [row[0] for row in db.runQuery( 'SELECT ts FROM trigger WHERE ts BETWEEN ? and ? ORDER BY ts', (tsQueryLower, tsQueryUpper))]
			
			progress.SetRange( max(1,len(triggerTS)) )
			
			pickle.dump( triggerTS, f, -1 )
			showUpdate = getUpdateCB( 'Exporting triggers' )
			with db.dbLock, db.conn:
				for count, row in enumerate(db.conn.execute( 'SELECT {} FROM trigger WHERE ts BETWEEN ? AND ? ORDER BY ts'.format(','.join(triggerFields)), (tsQueryLower, tsQueryUpper) )):
					obj = {f:v for f,v in zip(triggerFields, row)}
					pickle.dump( obj, f, -1 )
					if count % 25 == 0:
						showUpdate( count, len(triggerTS) )
		
			#-----------------------------------------------------------
			# Purge duplicates.
			photoTS = sorted(set(row[0] for row in db.runQuery( 'SELECT ts FROM photo WHERE ts BETWEEN ? and ?', (tsQueryLower, tsQueryUpper))))
			
			progress.SetRange( max(1,len(photoTS)) )
			
			pickle.dump( photoTS, f, -1 )
			showUpdate = getUpdateCB( 'Exporting photos' )
			with db.dbLock, db.conn:
				tsSeen = set()
				count = 0
				for row in db.conn.execute( 'SELECT {} FROM photo WHERE ts BETWEEN ? AND ? ORDER BY ts'.format(','.join(photoFields)), (tsQueryLower, tsQueryUpper) ):
					if row[0] not in tsSeen:
						tsSeen.add( row[0] )
						obj = {f:v for f,v in zip(photoFields, row)}
						pickle.dump( obj, f, -1 )
						if count % 25 == 0:
							showUpdate( count, len(photoTS) )
						count += 1
				
		progress.Destroy()
	
	def importDB( self, event ):
		with wx.FileDialog(self, "Open CrossMgrVideo Import file", wildcard="Files (*.gz)|*.gz",
						   style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
			if fileDialog.ShowModal() == wx.ID_CANCEL:
				return
			fname = fileDialog.GetPath()

		# Check if the import file is valid.
		try:
			with gzip.open( fname, 'rb' ) as f:
				info = pickle.load( f )
				app = AppVerName.split()[0]
				key = '{}_AppVersion'.format(app)
				assert key in info
		except Exception as e:
			with wx.MessageDialog( self, 'Exception: {}'.format(e), 'Improper File', style=wx.OK|wx.ICON_ERROR ) as dlg:
				dlg.ShowModal()
				return
	
		progress = wx.ProgressDialog( 'Import Progress', 'Initializing...' )
		progress.SetRange( 1 )
		progress.Show()
		
		def getUpdateCB( msg ):
			msg += ' ({}/{})'
			def updateCB( count, total ):
				progress.Update( count, msg.format(count, total) )
			return updateCB

		db = GlobalDatabase()
		
		with gzip.open( fname, 'rb' ) as f:
			info = pickle.load( f )

			# Read the fields used to write the export file.
			triggerFields = pickle.load( f )
			photoFields = pickle.load( f )
			
			# For compatability, ensure there are no unexpected import fields.
			triggerFieldsSet = set( f for f in db.triggerFieldsAll if f != 'id' )
			triggerFields = [f for f in triggerFields if f in triggerFieldsSet]

			#-----------------------------------------------------------
			triggerTS = pickle.load( f )
			
			progress.SetRange( max(1,len(triggerTS)) )
			db.deleteTss( 'trigger', triggerTS, getUpdateCB('Removing exisiting triggers') )
			
			showUpdate = getUpdateCB( 'Importing Triggers' )
			with BulkInsertDBRows( 'trigger', triggerFields, db ) as bid:
				for count in range(len(triggerTS)):
					obj = pickle.load( f )
					bid.append( [obj[f] for f in triggerFields] )
					if count % 25 == 0:
						showUpdate(count, len(triggerTS) )
		
			#-----------------------------------------------------------
			photoTS = pickle.load( f )
			
			progress.SetRange( max(1,len(photoTS)) )
			db.deleteTss( 'photo', photoTS, getUpdateCB('Removing exisiting photos')  )
			
			showUpdate = getUpdateCB( 'Importing Photos' )
			with BulkInsertDBRows( 'photo', photoFields, db ) as bid:
				for count in range(len(photoTS)):
					obj = pickle.load( f )
					obj['jpg'] = sqlite3.Binary( obj['jpg'] )
					bid.append( [obj[f] for f in photoFields] )
					if count % 25 == 0:
						showUpdate(count, len(photoTS))
				
		progress.Destroy()
		self.refreshTriggers( replace=True )
	
	def setFPS( self, fps ):
		self.fps = int(fps if fps > 0 else 30)
		self.frameDelay = 1.0 / self.fps
		self.frameCountUpdate = int(self.fps * 2)
	
	def updateFPS( self, fps ):
		self.setFPS( fps )
		self.targetFPS.SetLabel( '{:.1f} fps'.format(float(self.fps)) )

	def updateActualFPS( self, actualFPS ):
		oldLabel = self.actualFPS.GetLabel()
		newLabel = '{:.1f} fps'.format(actualFPS)
		if oldLabel != newLabel:
			self.actualFPS.SetLabel( '{:.1f} fps'.format(actualFPS) )
			self.GetSizer().Layout()
		self.curFPS = actualFPS
		
	def updateCameraUsb( self, availableCameraUsb ):
		if not self.cameraDisconnected and self.currentUSB not in availableCameraUsb:
			self.cameraDisconnected = True
			self.messageQ.put( ('USB', 'In-use camera ' + str(self.currentUSB) + ' has disconnected!') )
			Utils.PlaySound('awooga.wav')
			with wx.MessageDialog(self, 'In-use camera ' + str(self.currentUSB) + ' has disconnected!', 'CrossMgrVideo', style=wx.ICON_WARNING) as dlg:
				dlg.SetExtendedMessage('Check the connections and make sure the correct camera device is being used.\nAvailable USB devices: ' + str(availableCameraUsb))
				dlg.ShowModal()
		elif not self.cameraDisconnected and self.warnAnyDisconnectedCamera and len(availableCameraUsb) < len(self.availableCameraUsb):
			self.cameraDisconnected = True
			self.messageQ.put( ('USB', 'A camera has disconnected! (current devices: ' + str(availableCameraUsb) + ')' ) )
			Utils.PlaySound('awooga.wav')
			with wx.MessageDialog(self, 'A camera has disconnected!', 'CrossMgrVideo', style=wx.ICON_WARNING) as dlg:
				dlg.SetExtendedMessage('Check the connections and make sure the correct camera device is being used.\nAvailable USB devices: ' + str(availableCameraUsb))
				dlg.ShowModal()
		elif self.cameraDisconnected and self.currentUSB in availableCameraUsb:
			self.cameraDisconnected = False
			self.messageQ.put( ('USB', 'Now using camera ' + str(self.currentUSB)) )
		self.availableCameraUsb = availableCameraUsb

	def updateAutoCaptureLabel( self ):
		def f( n ):
			s = '{:0.1f}'.format( n )
			return s[:-2] if s.endswith('.0') else s
		
		if self.autoCaptureClosestFrames:
			label = '\n'.join( ['AUTO','CAPTURE','CLOSEST {}'.format(self.autoCaptureClosestFrames)] )
		else:
			label = '\n'.join( ['AUTO','CAPTURE','{} .. {}'.format(f(-self.tdCaptureBefore.total_seconds()), f(self.tdCaptureAfter.total_seconds()))] )
		for btn in (self.autoCapture, self.focusDialog.autoCapture):
			btn.SetLabel( label )
			btn.SetFontToFitLabel()
			wx.CallAfter( btn.Refresh )

	def setQueryDate( self, d ):  # d is a datetime.date
		self.tsQueryLower = d
		self.tsQueryUpper = self.tsQueryLower + timedelta( days=1 )
		tNow = now()
		if self.tsQueryUpper < date(tNow.year, tNow.month, tNow.day):  # if a historical date is selected...
			self.autoSelect.SetSelection( 3 )  # Autoselect off
		elif self.autoSelect.GetSelection() > 2:  # if we're selecting today's date and autoselect is off...
			self.autoSelect.SetSelection( self.config.ReadInt( 'AutoSelect', 3 ) )  # revert to saved setting
		self.refreshTriggers( replace=True, selectLatest=True )
		wx.CallAfter( self.date.SetValue, wx.DateTime(d.day, d.month-1, d.year) )
		
	def onDateSelect( self, event ):
		triggerDates = GlobalDatabase().getTriggerDates()
		triggerDates.sort( reverse=True )
		with DateSelectDialog( self, triggerDates ) as dlg:
			if dlg.ShowModal() == wx.ID_OK and dlg.GetDate():
				self.setQueryDate( dlg.GetDate() ) # dlg returns a datetime.date

	def copyLogFileToClipboard( self, event ):
		logFileName = getLogFileName()
		try:
			with open(logFileName) as f:
				logData = f.read()
		except IOError:
			with wx.MessageDialog(self, "Unable to open log file.", "Error", style=wx.OK|wx.ICON_ERROR) as dlg:
				dlg.ShowModal()
			return
			
		logData = logData.split( '\n' )
		logData = logData[-1000:]
		logData = '\n'.join( logData )
		
		dataObj = wx.TextDataObject()
		dataObj.SetText( logData )
		if wx.TheClipboard.Open():
			wx.TheClipboard.SetData( dataObj )
			wx.TheClipboard.Close()
			with wx.MessageDialog(self, '\n\n'.join( ("Log file copied to clipboard.", "You can now paste it into an email.") ), "Success", style=wx.OK) as dlg:
				dlg.ShowModal()
		else:
			with wx.MessageDialog(self, "Unable to open the clipboard.", "Error", style=wx.OK|wx.ICON_ERROR) as dlg:
				dlg.ShowModal()

	def onQueryDateChanged( self, event ):
		v = self.date.GetValue()
		self.setQueryDate( date( v.GetYear(), v.GetMonth() + 1, v.GetDay() ) )  # this should be a date, not a datetime
		
	def onQueryBibChanged( self, event ):
		self.bibQuery = self.bib.GetValue()
		if self.bibQuery:  # If filtering by bib
			self.autoSelect.SetSelection( 3 )  # Autoselect off
		elif self.autoSelect.GetSelection() > 2:  # If we're not filtering and autoselect is off...
			self.autoSelect.SetSelection( self.config.ReadInt( 'AutoSelect', 3 ) )  # revert to saved setting
		self.refreshTriggers( replace=True )
		
	def filterLastBibWave( self, infoList):
		''' Filter out all photos but the last by bib and wave. '''
		seen = set()
		infoListNew = []
		for info in reversed(infoList):
			key = (info['bib'], info['wave'])
			if key not in seen:
				seen.add( key )
				infoListNew.append( info )
		infoListNew.reverse()
		return infoListNew
	
	def filterSelected( self, infoList):
		seen = set()
		infoListNew = []
		for info in infoList:
			if info['publish']:
				infoListNew.append( info )
		return infoListNew
		
	def refreshPhotoPanel( self ):
		self.photoPanel.playStop()
		self.photoPanel.set(
			self.finishStrip.getIJpg(), self.triggerInfo, self.finishStrip.GetTsJpgs(), self.fps,
			editCB=self.doTriggerEdit,
			updateCB=lambda fields: self.updateTriggerRow(self.iTriggerSelect, fields),
			publishCB=self.doTriggerPublish
		)
		wx.CallAfter( self.photoPanel.doRestoreView, self.triggerInfo )
		
	def onNotebook( self, event ):
		self.iTriggerAdded = None
		self.onTriggerSelected()
		self.refreshPhotoPanel()
		
	def onPublishPhotos( self, event ):
		infoList = [self.getTriggerInfo(row) for row in range(self.triggerList.GetItemCount())]
		if not infoList:
			with wx.MessageDialog( self,
					"Please select a date with videos.",
					"Nothing to Publish",
					style=wx.OK ) as dlg:
				dlg.ShowModal()
				return
				
		if not hasattr(self, 'publishPhotoOptionsPhotoDialog'):
			self.publishPhotoOptionsPhotoDialog = PublishPhotoOptionsDialog( self, webPublish=False )
		if self.publishPhotoOptionsPhotoDialog.ShowModal() != wx.ID_OK:
			return
		values = self.publishPhotoOptionsPhotoDialog.GetValues()
		dirname = values['dirname']
		if not dirname:
			return
		if values['lastBibWaveOnly'] == 1:
			infoList = self.filterLastBibWave( infoList )
		elif values['lastBibWaveOnly'] == 2:
			infoList = self.filterSelected( infoList )
			
		def write_photos( dirname, infoList ):
			unknown = 0
			for info in infoList:
				tsBest, jpgBest = GlobalDatabase().getBestTriggerPhoto( info['id'] )
				if jpgBest is None:
					continue
				args = {k:info[k] for k in ('ts', 'bib', 'first_name', 'last_name', 'machine', 'team', 'race_name', 'kmh')}
				try:
					args['raceSeconds'] = (info['ts'] - info['ts_start']).total_seconds()
				except Exception:
					pass
				if isinstance(args['kmh'], str):
					args['kmh'] = float( '0' + re.sub( '[^0-9.]', '', args['kmh'] ) )
					
				jpg = CVUtil.bitmapToJPeg( AddPhotoHeader(CVUtil.jpegToBitmap(jpgBest), **args) )
				try:
					bib = int(info['bib'])
					bib = '{:04d}'.format(bib)
				except Exception:
					unknown += 1 
					bib = 'unknown-' + str(unknown)
				
				fname = Utils.RemoveDisallowedFilenameChars( '{}-{}-{},{}.jpg'.format(
						bib,
						info['ts'].strftime('%Y%m%dT%H%M%S'),
						info['last_name'],
						info['first_name'],
					)
				)
				comment = json.dumps( {k:info[k] for k in ('bib', 'first_name', 'last_name', 'machine', 'team', 'race_name')} )
				try:
					with open(os.path.join(dirname, fname), 'wb') as f:
						f.write( AddExifToJpeg(jpg, info['ts'], comment) )
				except Exception:
					pass
		
		# Write in a thread so we don't slow down the main capture loop.
		args = (
			dirname,
			infoList,
		)
		threading.Thread( target=write_photos, args=args, name='write_photos', daemon=True ).start()
	
	def onPublishWebPage( self, event ):
		infoList = [self.getTriggerInfo(row) for row in range(self.triggerList.GetItemCount())]
		if not infoList:
			with wx.MessageDialog( self,
					"Please select a date with videos.",
					"Nothing to Publish",
					style=wx.OK ) as dlg:
				dlg.ShowModal()
				return
				
		if not hasattr(self, 'publishPhotoOptionsWebDialog'):
			self.publishPhotoOptionsWebDialog = PublishPhotoOptionsDialog( self, webPublish=True )
		if self.publishPhotoOptionsWebDialog.ShowModal() != wx.ID_OK:
			return
		values = self.publishPhotoOptionsWebDialog.GetValues()
		dirname = values['dirname']
		if not dirname:
			return
		singleFile = (values['htmlOption'] == 1)
		
		if values['lastBibWaveOnly'] == 1:
			infoList = self.filterLastBibWave( infoList )
		elif values['lastBibWaveOnly'] == 2:
			infoList = self.filterSelected( infoList )
			
		class DateTimeEncoder( json.JSONEncoder ):
			def default(self, o):
				if isinstance(o, datetime):
					return o.isoformat()
				return json.JSONEncoder.default(self, o)
		
		def publish_web_photos( dirname, infoList, singleFile ):
			if not infoList:
				return
			
			dateStr = infoList[0]['ts'].strftime('%Y-%m-%d')
			fname = os.path.join( dirname, 'index.html' )
			ftemplate = os.path.join( Utils.getHtmlFolder(), 'PhotoPage.html' )
			
			with open(fname, 'w', encoding='utf8') as fOut, open(ftemplate, encoding='utf8') as fIn:
				for line in fIn:
					lineStrip = line.strip()
					if lineStrip == '<script src="ScaledBitmap.js"></script>':
						fOut.write( '<script>\n' )
						with open( os.path.join(Utils.getHtmlFolder(), 'ScaledBitmap.js'), encoding='utf8' ) as fsb:
							fOut.write( fsb.read() )
						fOut.write( '\n</script>\n' )
						continue
					
					if not lineStrip.startswith( 'var photo_info' ):
						fOut.write( line )
						continue
						
					# Write out all the photo info.
					fOut.write( 'var photo_info = [\n' )
					for iInfo, info in enumerate(infoList):
						tsBest, jpgBest = GlobalDatabase().getBestTriggerPhoto( info['id'] )

						if jpgBest is None:
							continue
						args = {k:info[k] for k in ('ts', 'bib', 'machine', 'team', 'race_name', 'kmh')}
						if info['last_name'] == 'Auto' or info['last_name'] == 'Capture' or info['last_name'] == 'Snapshot':
							args['first_name'] = 'Unknown Rider'
							args['last_name'] = ''
						else:
							args['first_name'] = info['first_name']
							args['last_name'] = info['last_name']
						try:
							if info['ts_view'] is not None:
								args['ts'] = info['ts_view']
								args['raceSeconds'] = (info['ts_view'] - info['ts_start']).total_seconds() if info['ts_start'] != info['ts'] else None
							else:
								args['raceSeconds'] = (info['ts'] - info['ts_start']).total_seconds()
						except Exception:
							args['raceSeconds'] = None
						if isinstance(args['kmh'], str):
							args['kmh'] = float( '0' + re.sub( '[^0-9.]', '', args['kmh'] ) )

						comment = json.dumps( {k:info[k] for k in ('bib', 'first_name', 'last_name', 'machine', 'team', 'race_name')} )
						jpg = CVUtil.bitmapToJPeg( AddPhotoHeader(CVUtil.jpegToBitmap(jpgBest), **args) )
						jpg = AddExifToJpeg( jpg, info['ts'], comment )

						if iInfo:
							fOut.write( ',\n' )
						
						if singleFile:
							args['photo'] = 'data:image/jpeg;base64,{}'.format( base64.standard_b64encode(jpg).decode() )
						else:
							photo_fname = '{}-{:06X}.jpeg'.format(dateStr, iInfo)
							with open(os.path.join(os.path.dirname(fname), photo_fname), 'wb') as fPhoto:
								fPhoto.write( jpg )
							args['photo'] = './{}'.format( photo_fname )
						
						json.dump( args, fOut, cls=DateTimeEncoder )
					
					fOut.write( '];\n' )
					
			webbrowser.open( fname, new=0, autoraise=1 )

		# Write in a thread so we don't slow down the main capture loop.
		args = (
			dirname,
			infoList,
			singleFile,
		)
		threading.Thread( target=publish_web_photos, args=args, name='publish_web', daemon=True ).start()
		# write_photos( *args )
		
	def onAutoSelect(self, event):
		if self.autoSelect.GetCurrentSelection() == 0:
			tNow = now()
			self.tsQueryLower = date(tNow.year, tNow.month, tNow.day)
			self.tsQueryUpper = self.tsQueryLower + timedelta( days=1 )
			wx.CallAfter( self.date.SetValue, wx.DateTime(tNow.day, tNow.month-1, tNow.year) )
		if self.autoSelect.GetCurrentSelection() >= 4:
			wx.CallAfter( self.photoPanel.SetTestBitmap )
		self.iTriggerAdded = None
		self.refreshTriggers(replace=True, selectLatest=False)
		self.writeOptions()
	
	def GetListCtrl( self ):
		return self.triggerList
	
	def GetSortImages(self):
		return (self.sm_dn, self.sm_up)
	
	def getTriggerRowFromID( self, id ):
		for row in range(self.triggerList.GetItemCount()):
			if self.triggerList.GetItemData(row) == id:
				return row
		return None

	def updateTriggerColumnWidths( self ):
		for c in range(self.triggerList.GetColumnCount()):
			if not c in self.hiddenTriggerCols:
				self.triggerList.SetColumnWidth(c, wx.LIST_AUTOSIZE_USEHEADER if c != self.iNoteCol else 100 )
			else:
				#if column is hidden, just set the width to zero
				self.triggerList.SetColumnWidth( c, 0 )
				
	def updateTriggerRow( self, row, fields ):
		''' Update the row in the UI only. '''
		if 'name' not in fields:
			fields = self.computeTriggerFields( fields )
		for k, v in fields.items():
			if k in self.fieldCol:
				if k == 'ts':
					v = v.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
				if k == 'bib':
					v = '{:>6}'.format(v)
				elif k == 'frames':
					v = '{}'.format(v) if v else ''
				elif isinstance(v, float):
					v = '{:.2f}'.format(v) if v else ''
				else:
					v = '{}'.format(v) if v is not None else ''
				self.triggerList.SetItem( row, self.fieldCol[k], v )

	def updateTriggerRowID( self, id, fields ):
		if fields:
			row = self.getTriggerRowFromID( id )
			if row is not None:
				self.updateTriggerRow( row, fields )
	
	def computeTriggerFields( self, fields ):
		if 'last_name' in fields and 'first_name' in fields:
			fields['name'] = ', '.join( n for n in (fields['last_name'], fields['first_name']) if n )
		if 'kmh' in fields:
			fields['mph'] = (fields['kmh'] * 0.621371) if fields['kmh'] else 0.0
		if 'frames' in fields and 'closest_frames' in fields:
			fields['frames'] = max(fields['frames'], fields['closest_frames'])
		if 'ts_view' in fields and fields['ts_view'] is not None and fields['ts_view'] != fields['ts']:
			# ts_view defaults to the same value as ts - only display if it has been changed
			fields['view'] = fields['ts_view'].strftime('%H:%M:%S.%f')[:-3]
		elif 'zoom_frame' in fields and fields['zoom_frame'] >= 0:
			# Otherwise, use the frame number for backward compatibility
			fields['view'] = 'Frame ' + str(fields['zoom_frame'])
		else:
			fields['view'] = ''
		if 'publish' in fields:
			fields['publish'] = 'Y' if fields['publish'] > 0 else ''
		return fields
	
	def getTriggerInfo( self, row ):
		return self.computeTriggerFields( GlobalDatabase().getTriggerFields(self.triggerList.GetItemData(row)) )
	
	def refreshTriggers( self, replace=False, iTriggerRow=None, selectLatest=None):
		'''
			Refreshes the trigger list from the database.
			If any rows have zero frames, it fixes the number of frames by reading the database.
		'''
		
		if self.autoSelect.GetSelection() >= 4:  #minimise DB access; do not refresh triggers from database
			return
			
		tNow = now()
		
		if selectLatest == None and self.autoSelect.GetSelection() < 2:
			selectLatest = True

		if replace:
			tsLower = self.tsQueryLower
			tsUpper = self.tsQueryUpper
		elif self.tsQueryUpper < date(tNow.year, tNow.month, tNow.day): #if a historical date is selected
			if selectLatest:
				# Replace list with the current day's
				replace = True
				tsLower = (self.tsMax or datetime(tNow.year, tNow.month, tNow.day)) + timedelta(seconds=0.00001)
				tsUpper = tsLower + timedelta(days=1)
				# Reset query date to current day
				self.tsQueryLower = date(tNow.year, tNow.month, tNow.day)
				self.tsQueryUpper = self.tsQueryLower + timedelta( days=1 )
				wx.CallAfter( self.date.SetValue, wx.DateTime(tNow.day, tNow.month-1, tNow.year) )
			else:
				#if we're not selecting latest, leave the historical trigger list unchanged
				return
		else:
			tsLower = (self.tsMax or datetime(tNow.year, tNow.month, tNow.day)) + timedelta(seconds=0.00001)
			tsUpper = tsLower + timedelta(days=1)
			
		if selectLatest:
			# Reset the bib filter
			self.bib.ChangeValue(None)  # Does not generate an EVT_TEXT event
			self.bibQuery = None
		
		# Read the triggers from the database before we repaint the screen to avoid flashing.
		counts = GlobalDatabase().updateTriggerPhotoCountInterval( tsLower, tsUpper )
		triggers = GlobalDatabase().getTriggers( tsLower, tsUpper, self.bibQuery )		
		if triggers:
			self.tsMax = triggers[-1].ts
		
		self.lastTriggerRefresh = tNow
		self.finishStrip.Set( None )
		
		if replace:
			#self.tsMax = None  #this causes duplicate entries when not replacing
			self.iTriggerSelect = None
			self.triggerInfo = {}
			self.triggerList.DeleteAllItems()

		tsLower, tsUpper = datetime.max, datetime.min
		for i, trig in enumerate(triggers):
			if not trig.closest_frames and trig.s_before == 0.0 and trig.s_after == 0.0:
				trig = trig._replace( s_before=tdCaptureBeforeDefault.total_seconds(), s_after=tdCaptureAfterDefault.total_seconds() )
			
			# Color code whether this is a close finish.
			tsPrev = triggers[i-1].ts if i != 0 else (trig.ts - timedelta(days=1))
			tsNext = triggers[i+1].ts if i < len(triggers)-1 else (trig.ts + timedelta(days=1))
			deltaFinish = min( (trig.ts-tsPrev).total_seconds(), (tsNext-trig.ts).total_seconds() )
			row = self.triggerList.InsertItem( self.triggerList.GetItemCount(), trig.ts.strftime('%H:%M:%S.%f')[:-3], getCloseFinishIndex(deltaFinish) )
			self.updateTriggerRow( row, trig._asdict() )			
			self.triggerList.SetItemData( row, trig.id )	# item data is the trigger id.
			tsPrev = trig.ts
		
		self.updateTriggerColumnWidths()
		
		# Unconditionally refresh the photos if the triggerList is empty.
		if self.triggerList.GetItemCount() == 0:
			wx.CallAfter( self.onTriggerSelected, iTriggerSelect=iTriggerRow or 0 )
			return

		# Figure out which photo to refresh.
		if iTriggerRow is None:
			iTriggerRow = self.triggerList.GetItemCount()-1
		else:
			iTriggerRow = min( max(0, iTriggerRow), self.triggerList.GetItemCount()-1 )
			
		if selectLatest or self.autoSelect.GetSelection() < 3:
			self.triggerList.EnsureVisible( iTriggerRow )
		if selectLatest:
			if not replace:
				self.iTriggerAdded = iTriggerRow
			self.triggerList.Select( iTriggerRow )
			#wx.CallAfter( self.onTriggerSelected, iTriggerSelect=iTriggerRow or 0 )  # this appears to be unecessary as the Select() generates an event

	def dbInactivityUpdate( self ):
		# Do actions when the database goes inactive.
		if not self.inCapture:
			self.captureProgressQ.put( { 'cmd':'idle', 'ts':now() } )
			wx.CallAfter( self.refreshCaptureProgress )
			self.refreshTriggers()
		else:
			self.captureProgressQ.put( { 'cmd':'busy', 'ts':now() } )
			wx.CallAfter( self.refreshCaptureProgress )
			
	def Start( self ):
		self.messageQ.put( ('', '************************************************') )
		self.messageQ.put( ('started', now().strftime('%Y-%m-%d %H:%M:%S')) )
		self.startThreads()

	def updateSnapshot( self, t, f ):
		self.snapshotCount = getattr(self, 'snapshotCount', 0) + 1
		self.dbWriterQ.put( ('photo', t, f) )
		self.dbWriterQ.put( (
			'trigger',
			{
				'ts':				t,
				's_before':			0.0,
				's_after':			0.0,
				'closest_frames':	1,
				'ts_start':			t,
				'bib':				self.snapshotCount if self.autoCaptureSequentialBibs else '',
				'first_name':		'',
				'last_name':		'Snapshot',
				'machine':			'',
				'team':				'',
				'wave':				'',
				'race_name':		'',
				'ts_view':			t
			}
		) )
		self.doUpdateAutoCapture( t, self.snapshotCount, self.snapshot, snapshotEnableColour )
		
	def onStartSnapshot( self, event ):
		self.onStartAutoCapture( event, isSnapshot=True )
		
	def waitForDB( self ):
		# Waits for the database to finish writing all the photos and triggers.
		self.dbWriterQ.put( ('flush',) )
		self.dbWriterQ.join()
		
	def doUpdateAutoCapture( self, tStartCapture, count, btn, colour ):
		self.waitForDB()

		# Update missing trigger information.
		# We do this here to avoid any database access delay at the start of the capture.
		triggers = GlobalDatabase().getTriggers( tStartCapture, tStartCapture, count )
		if triggers:
			id = triggers[-1].id
			self.updateTriggerRowID( id, GlobalDatabase().initCaptureTriggerData(id) )

		# Reset the foreground colors to exit auto capture mode.
		for b in (btn if isinstance(btn, list) else [btn]):
			b.SetForegroundColour( colour )
			wx.CallAfter( b.Refresh )
		
		# Explicitly call a refresh if we are out of the last capture.
		if self.inCapture > 0:
			self.inCapture -= 1
		if self.inCapture == 0:
			self.captureProgressQ.put( { 'cmd':'idle', 'ts':now() } )
			wx.CallAfter( self.refreshCaptureProgress )
			self.refreshTriggers()

	def onStartAutoCapture( self, event, isSnapshot=False, joystick=False ):
		tNow = now()
		self.inCapture += 1
		
		# A snapshot is an auto-capture with one closest frame.
		if isSnapshot:
			btn = self.snapshot
			enableColour = snapshotEnableColour
			disableColour = snapshotDisableColour
			count = self.snapshotCount = getattr(self, 'snapshotCount', 0) + 1
			last_name = 'Snapshot'

			closest_frames = 1								# Snapshot is one frame.
			s_before = 0.0
			s_after = 0.0
		else:
			btn = self.autoCapture
			enableColour = autoCaptureEnableColour
			disableColour = autoCaptureDisableColour
			count = self.autoCaptureCount = getattr(self, 'autoCaptureCount', 0) + 1
			last_name = 'Auto'

			closest_frames = self.autoCaptureClosestFrames	# will zero if capturing by time interval.
			s_before = 0.0	if closest_frames else self.tdCaptureBefore.total_seconds()
			s_after = 0.0	if closest_frames else self.tdCaptureAfter.total_seconds()
		
		first_name = 'Joystick' if joystick else None

		
		btn.SetForegroundColour( disableColour )
		wx.CallAfter( btn.Refresh )
		
		self.requestQ.put( {
				'time':				tNow,
				's_before':			s_before,
				's_after':			s_after,
				'closest_frames':	closest_frames,
				'ts_start':			tNow,
				'bib':				count if self.autoCaptureSequentialBibs else '',
				'last_name':		last_name,
				'first_name':		first_name,
			}
		)
		
		wx.CallLater( max(0, int(s_after*1000.0)) + 200, self.doUpdateAutoCapture, tNow, count, btn, enableColour )
		
	def onStartAutoCaptureAccel( self, event ):
		self.onStartAutoCapture( event )

	def onToggleCapture( self, event ):
		self.capturing ^= True

		event.SetEventObject( self.capture )
		if self.capturing:
			self.onStartCapture( event )
		else:
			self.onStopCapture( event )

	def onJoystickButton( self, event ):
		startCaptureBtn	= event.ButtonIsDown( wx.JOY_BUTTON1 )
		autoCaptureBtn	= event.ButtonIsDown( wx.JOY_BUTTON2 )
		snapshotBtn = event.ButtonIsDown( wx.JOY_BUTTON3 )

		if startCaptureBtn:
			if not self.capturing:
				self.capturing = True
				event.SetEventObject( self.capture )
				self.onStartCapture( event, joystick=True )
			return
			
		if not startCaptureBtn:
			if self.capturing:
				self.capturing = False
				event.SetEventObject( self.capture )
				self.onStopCapture( event )

		if autoCaptureBtn:
			event.SetEventObject( self.autoCapture )
			self.onStartAutoCapture( event, joystick=True )
			
		if snapshotBtn:
			event.SetEventObject( self.autoCapture )
			self.onStartAutoCapture( event, isSnapshot=True, joystick=True )
	
	def onStartCapture( self, event, joystick=False ):
		self.photoPanel.playStop()
		
		wx.BeginBusyCursor()
		tNow = self.tStartCapture = now()
		self.inCapture += 1
		
		first_name = 'Joystick' if joystick else None
		
		self.captureCount = getattr(self, 'captureCount', 0) + 1
		self.requestQ.put( {
				'time':				tNow,
				'ts_start':			tNow,
				's_before':			0.0,			# seconds before 0.0
				's_after':			60.0*10.0,		# seconds after a default end time.
				'closest_frames':	0,
				'bib':				self.captureCount if self.autoCaptureSequentialBibs else '',
				'last_name':		'Capture',
				'first_name':		first_name,
			}
		)
		self.camInQ.put( {'cmd':'start_capture', 'tStart':tNow} )

		event.GetEventObject().SetForegroundColour( captureDisableColour )
			
		wx.CallAfter( event.GetEventObject().Refresh )		
	
	def onStopCapture( self, event ):
		self.camInQ.put( {'cmd':'stop_capture'} )
		
		s_after = (now() - self.tStartCapture).total_seconds()
		tStartCapture = self.tStartCapture
		captureCount = self.captureCount

		captureLatency = timedelta( seconds=0.0 )
		
		self.waitForDB()
		
		# Update the capture trigger info.
		triggers = GlobalDatabase().getTriggers( tStartCapture, tStartCapture, captureCount )
		if triggers:
			id = triggers[0].id
			GlobalDatabase().updateTriggerBeforeAfter( id, 0.0, s_after )
			self.updateTriggerRowID( id, GlobalDatabase().initCaptureTriggerData(id) )

		# Re-enable the UI.
		event.GetEventObject().SetForegroundColour( captureEnableColour )
		wx.EndBusyCursor()
		wx.CallAfter( event.GetEventObject().Refresh )
		
		if self.inCapture > 0:
			self.inCapture -= 1
		if self.inCapture == 0:
			self.captureProgressQ.put( { 'cmd':'idle', 'ts':now() } )
			wx.CallAfter( self.refreshCaptureProgress )
			self.refreshTriggers()

	def showLastTrigger( self ):
		iTriggerRow = self.triggerList.GetItemCount() - 1
		if iTriggerRow < 0:
			return
		self.triggerList.EnsureVisible( iTriggerRow )
		for r in range(self.triggerList.GetItemCount()-1):
			self.triggerList.Select(r, 0)
		self.onTriggerSelected( iTriggerSelect=iTriggerRow )
		self.triggerList.Select( iTriggerRow )
		
	def playNextTrigger( self, tsStart ):
		lastTriggerRow = self.triggerList.GetItemCount() - 1
		if self.iTriggerSelect >= lastTriggerRow:
			wx.CallAfter( self.photoPanel.cancelAutoplay )
		else:
			self.iTriggerSelect += 1
			self.triggerList.Select( self.iTriggerSelect )
			self.triggerList.EnsureVisible( self.iTriggerSelect )
			wx.CallLater( 1000, self.photoPanel.playFromTs, tsStart )
	
	def autoCaptureConfig( self, event ):
		self.autoCaptureDialog.set( self.tdCaptureBefore.total_seconds(), self.tdCaptureAfter.total_seconds(), self.autoCaptureClosestFrames, self.autoCaptureSequentialBibs, self.shutterSound )
		if self.autoCaptureDialog.ShowModal() == wx.ID_OK:
			s_before, s_after, autoCaptureClosestFrames, autoCaptureSequentialBibs, shutterSound = self.autoCaptureDialog.get()
			self.tdCaptureBefore = timedelta(seconds=s_before) if s_before is not None else tdCaptureBeforeDefault
			self.tdCaptureAfter  = timedelta(seconds=s_after)  if s_after  is not None else tdCaptureAfterDefault
			self.autoCaptureClosestFrames = autoCaptureClosestFrames
			self.autoCaptureSequentialBibs = autoCaptureSequentialBibs
			self.shutterSound = shutterSound
			self.writeOptions()
			self.updateAutoCaptureLabel()
 		
	def onFocus( self, event ):
		if self.focusDialog.IsShown():
			return
		self.captureEnable()
		self.focusDialog.Move((4,4))
		self.camInQ.put( {'cmd':'send_update', 'name':'focus', 'freq':1} )
		self.focusDialog.Show()
	
	def onTriggerSelected( self, event=None, iTriggerSelect=None, fastPreview=False):
		# Do nothing if we are in minimise DB access mode
		if self.autoSelect.GetSelection() >= 4:
			self.iTriggerSelect = None
			if event is not None:
				self.triggerList.Select(event.Index, on=0) # immediately deselect trigger
			return
		
		# Determine which trigger we are updating (either specified or from the event).
		if iTriggerSelect is None:
			if event is not None:
				self.iTriggerSelect = event.Index
			else:
				self.iTriggerSelect = sys.maxsize
		else:
			self.iTriggerSelect = iTriggerSelect
		
		if self.iTriggerSelect >= self.triggerList.GetItemCount():
			if self.triggerList.GetItemCount() == 0:
				# If there are no triggers to show, update to a blank screen.
				self.ts = None
				self.tsJpg = []
				self.finishStrip.Set( self.tsJpg )
				self.refreshPhotoPanel()
				return
			else:
				self.iTriggerSelect = self.triggerList.GetItemCount() - 1
		
		# If this is a newly added trigger, should we do a fast preview?
		if self.iTriggerSelect == self.iTriggerAdded:
			fastPreview = self.autoSelect.GetSelection() == 1
		else:
			self.iTriggerAdded = None
			
		# Update the screen based on the new trigger.
		with wx.BusyCursor():
			self.finishStrip.Set( None )	# Clear the current finish strip so nothing gets updated.
			self.refreshPhotoPanel()
			
			triggerInfo = self.triggerInfo = self.getTriggerInfo( self.iTriggerSelect )
			self.ts = self.triggerInfo['ts']
			s_before, s_after = abs(self.triggerInfo['s_before']), abs(self.triggerInfo['s_after'])
			if s_before == 0.0 and s_after == 0.0:
				s_before, s_after = tdCaptureBeforeDefault.total_seconds(), tdCaptureAfterDefault.total_seconds()
			
			# Get all the photos for this trigger from the database.
			# This call can be slow.
			self.ts = triggerInfo['ts']
			if triggerInfo['closest_frames']:
				self.tsJpg = GlobalDatabase().getPhotosClosest( self.ts, triggerInfo['closest_frames'] )
			elif fastPreview:
				# Only fetch a single frame; this is considerably faster
				self.tsJpg = GlobalDatabase().getPhotosClosest( self.ts, 1 )
				if self.tsJpg[0][0] < self.ts - timedelta(seconds=s_before):  # If the closest frame in the database is historical, discard it
					self.tsJpg = []
			else:
				self.tsJpg = GlobalDatabase().getPhotos( self.ts - timedelta(seconds=s_before), self.ts + timedelta(seconds=s_after) )
			
			# Update the frame information.
			if not fastPreview and triggerInfo['frames'] != len(self.tsJpg):
				triggerInfo['frames'] = len(self.tsJpg)
				self.dbWriterQ.put( ('photoCount', self.triggerInfo['id'], len(self.tsJpg)) )
				self.updateTriggerRow( self.iTriggerSelect, {'frames':len(self.tsJpg)} )
			
			# Update the main UI.
			if fastPreview:
				# Switch to Images tab
				if self.notebook.GetSelection() != 0:
					self.notebook.ChangeSelection(0)  # This does not generate a page change event
				# Directly draw the frame on the photoPanel without populating the finishStrip
				self.photoPanel.set(1, None, self.tsJpg, self.fps, editCB=None, updateCB=None )
				# De-select the trigger and clear self.iTriggerAdded so re-selecting the trigger causes a full fetch
				self.triggerList.Select( -1, on=False )
				self.iTriggerAdded = None
			else:
				self.finishStrip.Set( self.tsJpg, leftToRight=[None, True, False][triggerInfo.get('finish_direction', 0)], triggerTS=triggerInfo['ts'] )
				self.refreshPhotoPanel()
	
	def onTriggerRightClick( self, event ):
		self.iTriggerSelect = event.Index
		if self.iTriggerSelect < 0:
			self.iTriggerSelect = 0
			return
		
		self.triggerList.Select( self.iTriggerSelect )
		
		if not hasattr(self, "triggerDeleteID"):
			self.triggerDeleteID = wx.NewIdRef()
			self.triggerEditID = wx.NewIdRef()
			self.triggerPublishID = wx.NewIdRef()
			self.publishTriggersID = wx.NewIdRef()
			self.unpublishRaceID = wx.NewIdRef()
			self.unpublishAllID = wx.NewIdRef()
			self.Bind(wx.EVT_MENU, lambda event: self.doTriggerDelete(), id=self.triggerDeleteID)
			self.Bind(wx.EVT_MENU, lambda event: self.doTriggerEdit(),   id=self.triggerEditID)
			self.Bind(wx.EVT_MENU, lambda event: self.doTriggerPublish(), id=self.triggerPublishID)
			self.Bind(wx.EVT_MENU, lambda event: self.doPublishTriggers(), id=self.publishTriggersID)
			self.Bind(wx.EVT_MENU, lambda event: self.doUnpublishRace(), id=self.unpublishRaceID)
			self.Bind(wx.EVT_MENU, lambda event: self.doUnpublishRace( allRaces=True ), id=self.unpublishAllID)
			

		menu = wx.Menu()
		menu.Append(self.triggerPublishID,   "Toggle Publish")
		menu.Append(self.triggerEditID,   "Edit...")
		menu.Append(self.triggerDeleteID, "Delete...")
		menu.Append(self.publishTriggersID, "Publish wave finishes from here")
		menu.Append(self.unpublishRaceID, "Unpublish this race")
		menu.Append(self.unpublishAllID, "Unpublish all races")

		self.PopupMenu(menu)
		menu.Destroy()
		
		
	def doTriggerDelete( self, confirm=True ):
		iTriggerSelect = self.iTriggerSelect
		triggerInfo = self.getTriggerInfo( iTriggerSelect )
		message = ', '.join( f for f in (triggerInfo['ts'].strftime('%H:%M:%S.%f')[:-3], '{}'.format(triggerInfo['bib']),
			triggerInfo['last_name'], triggerInfo['first_name'], triggerInfo['team'], triggerInfo['wave'], triggerInfo['race_name']) if f )
		if not confirm or wx.MessageDialog( self, '{}:\n\n{}'.format('Confirm Delete', message), 'Confirm Delete',
				style=wx.OK|wx.CANCEL|wx.ICON_QUESTION ).ShowModal() == wx.ID_OK:		
			GlobalDatabase().deleteTrigger( triggerInfo['id'], self.tdCaptureBefore.total_seconds(), self.tdCaptureAfter.total_seconds() )
			self.refreshTriggers( replace=True, iTriggerRow=iTriggerSelect )
	
	def onTriggerDelete( self, event ):
		self.iTriggerSelect = event.Index
		self.doTriggerDelete()
	
	def onTriggerKey( self, event ):
		if event.GetKeyCode() == 127 and self.iTriggerSelect != None:
			self.doTriggerDelete()
		
	def doTriggerEdit( self ):
		data = self.getTriggerInfo( self.iTriggerSelect )
		self.triggerDialog.set( self.db, data['id'] )
		self.triggerDialog.CenterOnParent()
		if self.triggerDialog.ShowModal() == wx.ID_OK:
			row = self.iTriggerSelect
			fields = self.triggerDialog.get()
			self.updateTriggerRow( row, fields )
			self.updateTriggerColumnWidths()
			self.triggerInfo.update( fields )
		return self.triggerInfo
	
	def onTriggerEdit( self, event ):
		self.iTriggerSelect = event.Index
		self.doTriggerEdit()
		
	def doTriggerPublish( self ):  # Toggle 'publish' flag for a trigger
		if self.iTriggerSelect is None:
			return
		data = self.getTriggerInfo( self.iTriggerSelect )
		values = {}
		if data['publish']:
			data['publish'] = ''
			values['publish'] = '0'
		else:
			data['publish'] = 'Y'
			values['publish'] = '1'
		self.updateTriggerRow( self.iTriggerSelect, data )
		self.updateTriggerColumnWidths()
		self.triggerInfo.update( data )
		GlobalDatabase().setTriggerEditFields( data['id'], **values )
				
	
	def doPublishTriggers( self ):  # Set publish flag for this and subsequent triggers for each bib
		if self.iTriggerSelect is None:
			return
		
		with wx.BusyCursor():
			data = self.getTriggerInfo( self.iTriggerSelect )
			raceName, wave = data['race_name'], data['wave']
			bibsSeen = []
			
			for iTriggerRow in range(self.iTriggerSelect, self.triggerList.GetItemCount()):
				data = self.getTriggerInfo( iTriggerRow )
				if data['race_name'] == raceName and data['wave'] == wave:
					bib = data['bib']
					if not bib in bibsSeen:
						bibsSeen.append( bib )
						values = {}
						data['publish'] = 'Y'
						values['publish'] = '1'
						self.updateTriggerRow( iTriggerRow, data )
						self.triggerInfo.update( data )
						GlobalDatabase().setTriggerEditFields( data['id'], **values )
			self.updateTriggerColumnWidths()
			
	def doUnpublishRace( self, allRaces=False ):  # Clear publish flag for all triggers in this race
		if self.iTriggerSelect is None:
			return
		
		with wx.BusyCursor():
			data = self.getTriggerInfo( self.iTriggerSelect )
			raceName = data['race_name']
			
			for iTriggerRow in range(self.triggerList.GetItemCount()):
				data = self.getTriggerInfo( iTriggerRow )
				if allRaces or data['race_name'] == raceName:
					if data['publish']:
						values = {}
						data['publish'] = ''
						values['publish'] = '0'
						self.updateTriggerRow( iTriggerRow, data )
						self.triggerInfo.update( data )
						GlobalDatabase().setTriggerEditFields( data['id'], **values )
			self.updateTriggerColumnWidths()
		
		
	def onTriggerColumnRightClick( self, event ):
		# Create and display a popup menu of columns on right-click event
		menu = wx.Menu()
		menu.SetTitle( 'Show/Hide columns' )
		for c in range(self.triggerList.GetColumnCount() - 1):  # Don't hide the note column
			menuItem = menu.AppendCheckItem( wx.ID_ANY, self.fieldHeaders[c] )
			self.Bind(wx.EVT_MENU, self.onToggleTriggerColumn, menuItem)
			if not c in self.hiddenTriggerCols:
				menu.Check( menuItem.GetId(), True )
		self.PopupMenu(menu)
		menu.Destroy()
		
	def onToggleTriggerColumn( self, event ):
		#find the column number
		label = event.GetEventObject().FindItemById(event.GetId()).GetItemLabel()
		c = self.fieldHeaders.index(label)
		#add or remove from hidden columns and update width
		if c in self.hiddenTriggerCols:
			self.hiddenTriggerCols.remove( c )
		else:
			self.hiddenTriggerCols.append( c )
		self.updateTriggerColumnWidths()
		
	def showMessages( self ):
		while True:
			message = self.messageQ.get()
			assert len(message) == 2, 'Incorrect message length'
			cmd, info = message
			print( 'Message:', '{}:  {}'.format(cmd, info) if cmd else info )
			#wx.CallAfter( self.messageManager.write, '{}:  {}'.format(cmd, info) if cmd else info )
			
	def refreshCaptureProgress( self ):
		# Get the latest (by timestamp, then order) message from the queue, discarding the rest
		message = None
		ts = datetime.min
		try:
			for m in iter( self.captureProgressQ.get_nowait, None ):
				if m.get('ts', datetime.min) >= ts:
					message = m
					if self.autoSelect.GetSelection() >= 4 and m.get('cmd') == 'capture':  #add the trigger directly to the list, bypassing the database
						self.addTriggerDirectlyToList( m )
					ts = m.get('ts')
		except Empty:
			pass
		
		# Update the progress text
		if message:
			cmd = message.get('cmd')
			if cmd == 'capture':
				ts = message.get('ts', now())
				bib = message.get('bib')
				# Update the status icon
				self.capturingIcon.SetBitmap( self.recordBitmap )
				# Update status text
				if bib:
					self.capturingText.SetLabel( 'Capturing #' + str(bib) + ':' )
				else:
					self.capturingText.SetLabel( 'Capturing:' )
				self.capturingTime.SetLabel( ts.strftime('%H:%M:%S.%f')[:-3] )
				# Do preview of capture in progress only if the trigger timestamp is within capturePreviewThreshold of realtime, otherwise there'll be nothing to see
				if self.autoSelect.GetSelection() < 5 and abs( now() - ts ) <= timedelta(seconds=capturePreviewThreshold):
					if now() - self.lastCapturePreview >= timedelta(seconds=1):  # Rate limit 
					# Play the camera sound
						if self.shutterSound:
							Utils.PlaySound('shutter.wav')
						if self.autoSelect.GetSelection() <= 1:  #Autoselect latest / Fast preview
							# Switch to Images tab
							if self.notebook.GetSelection() != 0:
								self.notebook.ChangeSelection(0)  # This does not generate a page change event
							# Copy the current primaryBitmap directly into the photoPanel - avoids database access and decoding jpegs
							self.photoPanel.setPreview( self.primaryBitmap.GetBitmap(), ts )
						elif self.autoSelect.GetSelection() == 4:  # Minimise DB access
							# Switch to Images tab
							if self.notebook.GetSelection() != 0:
								self.notebook.ChangeSelection(0)
							# Copy the current primaryBitmap directly into the photoPanel without a timestamp
							self.photoPanel.setPreview( self.primaryBitmap.GetBitmap() )
						self.lastCapturePreview = now()
			elif cmd == 'busy':
				ts = message.get('ts', now())
				# Update the status text
				self.capturingText.SetLabel( 'Capturing...' )
				self.capturingTime.SetLabel( '' )
			elif cmd == 'idle':
				# Update the status icon
				self.capturingIcon.SetBitmap( self.pauseBitmap )
				# Update the status text
				self.capturingText.SetLabel( 'Waiting for trigger...' )
				self.capturingTime.SetLabel( '' )
				
	def addTriggerDirectlyToList( self, trigger ):
		row = self.triggerList.InsertItem( self.triggerList.GetItemCount(), trigger['ts'].strftime('%H:%M:%S.%f')[:-3], 3 )  #getCloseFinishIndex of 3 draws white box
		self.updateTriggerRow( row, trigger )
		self.updateTriggerColumnWidths()
		self.triggerList.EnsureVisible( row )
		
	def startThreads( self ):
		self.grabFrameOK = False
		
		self.listenerThread = SocketListener( self.requestQ, self.messageQ )
		error = self.listenerThread.test()
		if error:
			wx.MessageBox('Socket Error:\n\n"{}" group={}, port={}\n\nIs another CrossMgrVideo running on this computer?'.format(
					error,
					multicast_group, multicast_port,
				),
				"Socket Error",
				wx.OK | wx.ICON_ERROR
			)
			# wx.Exit()
		
		self.camInQ, self.camReader = CamServer.getCamServer( self.getCameraInfo() )
		self.cameraThread = threading.Thread( target=self.processCamera, daemon=True )
		
		self.eventThread = threading.Thread( target=self.processRequests, daemon=True )
		
		# self.dbInactivityUpdate is called when database activity ceases.
		# This functions updates the trigger list, we don't need to worry about updating the UI.
		self.dbWriterThread = threading.Thread(
			target=DBWriter,
			args=(self.dbWriterQ, lambda: wx.CallAfter(self.dbInactivityUpdate), GlobalDatabase().fname),
			daemon=True
		)
		
		self.cameraThread.start()
		self.eventThread.start()
		self.dbWriterThread.start()
		self.listenerThread.start()
		
		self.grabFrameOK = True
		self.messageQ.put( ('threads', 'Successfully Launched') )
		
		self.primaryFreq = 5
		self.camInQ.put( {'cmd':'send_update', 'name':'primary', 'freq':self.primaryFreq} )
		return True
	
	def stopCapture( self ):
		self.dbWriterQ.put( ('flush',) )
	
	def processCamera( self ):
		
		#---------------------------------------------------------------
		def responseHandler( msg ):
			self.dbWriterQ.put( ('ts_frames', msg['ts_frames']) )
		
		#---------------------------------------------------------------
		def updateHandler( msg ):
			name, lastFrame = msg['name'], CVUtil.toFrame(msg['frame'], False)
			
			if name == 'primary':
				if lastFrame is None:
					wx.CallAfter( self.primaryBitmap.SetTestBitmap )
				else:
					wx.CallAfter( self.primaryBitmap.SetBitmap, CVUtil.frameToBitmap(lastFrame) )
					
			elif name == 'focus':
				if self.focusDialog.IsShown():
					if lastFrame is None:
						wx.CallAfter( self.focusDialog.SetTestBitmap )
					else:
						wx.CallAfter( self.focusDialog.SetBitmap, CVUtil.frameToBitmap(lastFrame) )
				else:
					self.camInQ.put( {'cmd':'cancel_update', 'name':'focus'} )

		#---------------------------------------------------------------
		def focusHandler( msg ):
			if self.focusDialog.IsShown():
				if lastFrame is None:
					wx.CallAfter( self.focusDialog.SetTestBitmap )
				else:
					wx.CallAfter( self.focusDialog.SetBitmap, CVUtil.frameToBitmap(lastFrame) )
			else:
				self.camInQ.put( {'cmd':'cancel_update', 'name':'focus'} )

		#---------------------------------------------------------------
		def infoHandler( msg ):
			vals = {name:update_value for name, property_index, call_status, update_value in msg['retvals']}
			wx.CallAfter( self.setCameraResolution, int(vals['frame_width']), int(vals['frame_height']) )
			
		#---------------------------------------------------------------
		def cameraUsbHandler( msg ):
			wx.CallAfter( self.updateCameraUsb, msg['usb_available'] )
			wx.CallAfter( self.setUsb, msg['usb_cur'] )
			
		#---------------------------------------------------------------
		def fpsHandler( msg ):
			wx.CallAfter( self.updateActualFPS, msg['fps_actual'] )

		handlers = {
			'response':		responseHandler,
			'update':		updateHandler,
			'focus':		focusHandler,
			'info':			infoHandler,
			'cameraUsb':	cameraUsbHandler,
			'fps':			fpsHandler,
		}
		
		while not self.isShutdown:
			msg = self.camReader.get()
			
			if self.isShutdown:
				break
				
			try:
				handler = handlers[msg['cmd']]
			except KeyError:
				if msg['cmd'] == 'terminate':
					break
				continue
			
			handler( msg )
		
	def processRequests( self ):
		bibMissing = 99999
		secsFilter = 0.1		# Minimum separation required between triggers to register.
		tSearchLast = {}		# Last trigger time of each bib.
		tPast = now() - timedelta(days=7)	# Time in the past outside the cache filter.
		tSearchPrev = tPast		# Previous trigger time.
		while True:
			msg = self.requestQ.get()	# Blocking get.
			self.camInQ.put( {'cmd':'resume'} )  # Send this immediately so the capture thread can resume as quickly as possible
			wx.CallAfter( self.captureEnable )   # Sort the UI out later
			
			tSearch = msg['time']
			advanceSeconds = msg.get('advanceSeconds', 0.0)
			tSearch += timedelta(seconds=advanceSeconds)
			
			# Filter triggers that are too close together for the same bib number.
			bib = msg.get('bib', bibMissing)
			if (tSearch - tSearchLast.get(bib, tPast)).total_seconds() < secsFilter:
				tSearchLast[bib] = tSearch
				continue
			
			# If there have been no triggers within the filter time, it is safe to delete the entire cache.
			# Better for memory efficiency.
			if (tSearch - tSearchPrev).total_seconds() > secsFilter:
				tSearchLast.clear()
			tSearchPrev = tSearch
			tSearchLast[bib] = tSearch	# Record the last trigger time for this rider.
			
			closest_frames = msg.get('closest_frames', self.autoCaptureClosestFrames)
			s_before = 0.0	if closest_frames else msg.get('s_before', self.tdCaptureBefore.total_seconds())	# Use the configured capture interval, not the default.
			s_after  = 0.0	if closest_frames else msg.get('s_after', self.tdCaptureAfter.total_seconds())
			
			# Write this trigger to the database.
			
			trigger = {
						'ts':				tSearch - timedelta(seconds=advanceSeconds),
						's_before':			s_before,
						's_after':			s_after,
						'ts_start':			msg.get('ts_start', None) or now(),
						'closest_frames':	closest_frames,
						'bib':				bib,
						'first_name':		msg.get('first_name','') or msg.get('firstName',''),
						'last_name':		msg.get('last_name','') or msg.get('lastName',''),
						'machine':			msg.get('machine',''),
						'team':				msg.get('team',''),
						'wave':				msg.get('wave',''),
						'race_name':		msg.get('race_name','') or msg.get('raceName',''),
						'ts_view':			tSearch - timedelta(seconds=advanceSeconds),
					}
			
			self.dbWriterQ.put( ('trigger', trigger.copy()) )
			# Request the video frames required for the trigger.
			tStart, tEnd = tSearch-self.tdCaptureBefore, tSearch+self.tdCaptureAfter
			if closest_frames:
				self.camInQ.put( {'cmd':'query_closest', 't':tSearch, 'closest_frames':closest_frames} )
			else:
				self.camInQ.put( {'cmd':'query', 'tStart':tStart, 'tEnd':tEnd} )
			
			# Notify of capture in progress
			trigger['cmd'] = 'capture'
			self.captureProgressQ.put( trigger )
			wx.CallAfter( self.refreshCaptureProgress )
	
	def shutdown( self ):
		# Ensure that all images in the queue are saved.
		self.isShutdown = True
		if hasattr(self, 'dbWriterThread'):
			if hasattr(self, 'camInQ' ):
				self.camInQ.put( {'cmd':'terminate'} )
			self.dbWriterQ.put( ('terminate', ) )
			self.dbWriterThread.join( 2.0 )
			
	def setDBName( self, dbName ):
		if dbName != GlobalDatabase().fname:
			if hasattr(self, 'dbWriterThread'):
				self.dbWriterQ.put( ('terminate', ) )
				self.dbWriterThread.join()
			try:
				GlobalDatabase( dbName )
			except Exception:
				GlobalDatabase()
			
			self.dbWriterQ = Queue()
			self.dbWriterThread = threading.Thread(
				target=DBWriter,
				args=(self.dbWriterQ, lambda: wx.CallAfter(self.dbInactivityUpdate), GlobalDatabase().fname),
				daemon=True
			)
			self.dbWriterThread.start()
	
	def onMenuDisableCapture( self, event ):
		if self.disableCapture.IsChecked():
			if self.releaseCamera:
				self.camInQ.put( {'cmd':'suspend-release'} )
			else:
				self.camInQ.put( {'cmd':'suspend'} )
			self.capturingIcon.SetBitmap( Utils.getBitmap('stop.png') )
			self.capturingText.SetLabel( 'Capture disabled!' )
			self.capturingTime.SetLabel( '' )
		else:
			self.camInQ.put( {'cmd':'resume'} )
			self.capturingIcon.SetBitmap( self.pauseBitmap )
			self.capturingText.SetLabel( 'Waiting for trigger...' )
			self.capturingTime.SetLabel( '' )
	
	def captureEnable( self, enable=True ):
		if enable:
			if self.disableCapture.IsChecked():
				self.camInQ.put( {'cmd':'resume'} )
				self.disableCapture.Check( False )
				self.capturingIcon.SetBitmap( self.pauseBitmap )
				self.capturingText.SetLabel( 'Waiting for trigger...' )
				self.capturingTime.SetLabel( '' )
		else:
			if not self.disableCapture.IsChecked():
				if self.releaseCamera:
					self.camInQ.put( {'cmd':'suspend-release'} )
				else:
					self.camInQ.put( {'cmd':'suspend'} )
				self.disableCapture.Check( True )
				self.capturingIcon.SetBitmap( Utils.getBitmap('stop.png') )
				self.capturingText.SetLabel( 'Capture disabled!' )
				self.capturingTime.SetLabel( '' )
	
	def resetCamera( self, event=None ):
		status = False
		self.captureEnable( True )
		while True:
			self.camInQ.put( {'cmd':'get_usb'} )
			sleep( 1.0 )	# Give the usb scan a chance to work.
			
			width, height = self.getCameraResolution()
			info = {'usb':self.getUsb(), 'fps':self.fps, 'width':width, 'height':height, 'fourcc':self.fourcc.GetLabel(), 'availableCameraUsb':self.availableCameraUsb}
			with ConfigDialog( self, **info, release=self.releaseCamera, warnAnyDisconnectedCamera=self.warnAnyDisconnectedCamera ) as dlg:
				ret = dlg.ShowModal()
				if ret == wx.ID_CANCEL:
					return status
				info = dlg.GetValues()
				release = dlg.GetRelease()
				warnAnyDisconnectedCamera = dlg.GetWarnAnyDisconnectedCamera()

			self.camInQ.put( {'cmd':'cam_info', 'info':info} )			

			self.setUsb( info['usb'] )
			self.setCameraResolution( info['width'], info['height'] )
			self.updateFPS( info['fps'] )
			self.fourcc.SetLabel( info['fourcc'] )
			self.releaseCamera = release
			self.warnAnyDisconnectedCamera = warnAnyDisconnectedCamera
			
			self.GetSizer().Layout()

			self.writeOptions()
			
			status = True
			if ret == wx.ID_OK:
				return status
				
		return status
	
	def manageDatabase( self, event ):
		trigFirst, trigLast = GlobalDatabase().getTimestampRange()
		dlg = ManageDatabase( self, GlobalDatabase().getsize(), GlobalDatabase().fname, trigFirst, trigLast, title='Manage Database' )
		if dlg.ShowModal() == wx.ID_OK:
			work = wx.BusyCursor()
			tsLower, tsUpper, vacuum, dbName = dlg.GetValues()
			self.setDBName( dbName )
			if tsUpper:
				tsUpper = datetime.combine( tsUpper, time(23,59,59,999999) )
			GlobalDatabase().cleanBetween( tsLower, tsUpper )
			if vacuum:
				GlobalDatabase().vacuum()
			wx.CallAfter( self.finishStrip.Clear )
			wx.CallAfter( self.refreshTriggers, True )
		dlg.Destroy()
	
	def setUsb( self, num ):
		try:
			self.currentUSB = int(num)
		except:
			self.currentUSB = None
		oldLabel = self.usb.GetLabel()
		label = '{} {}'.format(num, self.availableCameraUsb)
		if label != oldLabel:
			self.usb.SetLabel( label )
			try:
				self.GetSizer().Layout()
			except AttributeError:
				pass
		
	def getUsb( self ):
		return int(self.usb.GetLabel().split()[0])
		
	def setCameraResolution( self, width, height ):
		self.cameraResolution.SetLabel( '{}x{}'.format(width if width < 5000 else 'MAX', height if height < 5000 else 'MAX') )
			
	def getCameraFPS( self ):
		return int(float(self.targetFPS.GetLabel().split()[0]))
		
	def getCameraResolution( self ):
		try:
			return pixelsFromRes( self.cameraResolution.GetLabel() )
		except Exception:
			return 640, 480
	
	def getFourCC( self ):
		return self.fourcc.GetLabel()
	
	def onCloseWindow( self, event ):
		self.writeOptions()
		self.shutdown()
		#wx.Exit()
		sys.exit()
		
	def writeOptions( self ):
		self.config.Write( 'DBName', GlobalDatabase().fname )
		self.config.Write( 'CameraDevice', str(self.getUsb()) )
		self.config.Write( 'CameraResolution', self.cameraResolution.GetLabel() )
		self.config.Write( 'FPS', self.targetFPS.GetLabel() )
		self.config.Write( 'FourCC', self.fourcc.GetLabel() )
		self.config.Write( 'ReleaseCamera', ('1' if self.releaseCamera else '0') )
		self.config.Write( 'WarnAnyDisconnectedCamera', ('1' if self.warnAnyDisconnectedCamera else '0') )
		self.config.Write( 'SecondsBefore', '{:.3f}'.format(self.tdCaptureBefore.total_seconds()) )
		self.config.Write( 'SecondsAfter', '{:.3f}'.format(self.tdCaptureAfter.total_seconds()) )
		self.config.WriteFloat( 'ZoomMagnification', self.finishStrip.GetZoomMagnification() )
		self.config.Write( 'HiddenTriggerCols', repr(self.hiddenTriggerCols) )
		self.config.WriteInt( 'ClosestFrames', self.autoCaptureClosestFrames )
		self.config.WriteBool( 'SequentialBibs', self.autoCaptureSequentialBibs )
		self.config.WriteBool( 'ShutterSound', self.shutterSound )
		self.config.WriteInt ('AutoSelect', self.autoSelect.GetSelection() )
		self.config.Flush()
	
	def readOptions( self ):
		self.setDBName( self.config.Read('DBName', '') )
		self.setUsb( self.config.Read('CameraDevice', '0') )
		self.cameraResolution.SetLabel( self.config.Read('CameraResolution', '640x480') )
		self.targetFPS.SetLabel( self.config.Read('FPS', '30.000') )
		self.fourcc.SetLabel( self.config.Read('FourCC', FOURCC_DEFAULT) )
		release = self.config.Read('ReleaseCamera', '0')
		if int(release):
			self.releaseCamera = True
		else:
			self.releaseCamera = False
		warn = self.config.Read('WarnAnyDisconnectedCamera', '0')
		if int(warn):
			self.warnAnyDisconnectedCamera = True
		else:
			self.warnAnyDisconnectedCamera = False
		s_before = self.config.Read('SecondsBefore', '0.5')
		s_after = self.config.Read('SecondsAfter', '2.0')
		try:
			self.tdCaptureBefore = timedelta(seconds=abs(float(s_before)))
		except Exception:
			pass
		try:
			self.tdCaptureAfter = timedelta(seconds=abs(float(s_after)))
		except Exception:
			pass
		self.finishStrip.SetZoomMagnification( self.config.ReadFloat('ZoomMagnification', 0.5) )
		self.hiddenTriggerCols = ast.literal_eval( self.config.Read( 'HiddenTriggerCols', '[]' ) )
		self.autoCaptureClosestFrames = self.config.ReadInt( 'ClosestFrames', 0 )
		self.autoCaptureSequentialBibs = self.config.ReadBool( 'SequentialBibs', True )
		self.shutterSound = self.config.ReadBool( 'ShutterSound', True )
		self.autoSelect.SetSelection( self.config.ReadInt( 'AutoSelect', 0 ) )
		
	def getCameraInfo( self ):
		width, height = self.getCameraResolution()
		return {'usb':self.getUsb(), 'fps':self.getCameraFPS(), 'width':width, 'height':height, 'fourcc':self.getFourCC()}

def disable_stdout_buffering():
	fileno = sys.stdout.fileno()
	temp_fd = os.dup(fileno)
	sys.stdout.close()
	os.dup2(temp_fd, fileno)
	os.close(temp_fd)
	sys.stdout = os.fdopen(fileno, "w", 0)
	
def getLogFileName():
	return os.path.join(Utils.getHomeDir(), 'CrossMgrVideo.log')

redirectFileName = None
mainWin = None
def MainLoop():
	global mainWin, redirectFileName, imageWidth, imageHeight
	
	app = wx.App(False)
	app.SetAppName("CrossMgrVideo")

	displayWidth, displayHeight = wx.GetDisplaySize()
	if imageWidth*2 + 32 > displayWidth or imageHeight*2 + 32 > displayHeight:
		imageWidth /= 2
		imageHeight /= 2

	mainWin = MainWin( None, title=AppVerName, size=(1000,500) )
	
	dataDir = Utils.getHomeDir()
	redirectFileName = getLogFileName()
	
	# Set up the log file.  Otherwise, show errors on the screen.
	if __name__ == '__main__':
		'''disable_stdout_buffering()'''
		pass
	else:
		try:
			logSize = os.path.getsize( redirectFileName )
			if logSize > 1000000:
				os.remove( redirectFileName )
		except Exception:
			pass
	
		try:
			app.RedirectStdio( redirectFileName )
		except Exception:
			pass
			
		try:
			with open(redirectFileName, 'a', encoding='utf8') as pf:
				pf.write( '********************************************\n' )
				pf.write( '{}: {} Started.\n'.format(now().strftime('%Y-%m-%d_%H:%M:%S'), AppVerName) )
		except Exception:
			pass
	
	mainWin.Show()

	# Set the upper left icon.
	try:
		icon = wx.Icon( os.path.join(Utils.getImageFolder(), 'CrossMgrVideo.ico'), wx.BITMAP_TYPE_ICO )
		mainWin.SetIcon( icon )
	except Exception:
		pass

	# Start processing events.
	mainWin.Start()
	#wx.CallLater( 1500, mainWin.resetCamera )
	app.MainLoop()

@atexit.register
def shutdown():
	if mainWin:
		mainWin.shutdown()
	
if __name__ == '__main__':
	MainLoop()
	
