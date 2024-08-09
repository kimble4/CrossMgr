import wx
import re
import os
import sys
import Utils
#import ColGrid
from collections import defaultdict
#from Undo import undo
import datetime
import Flags
import Model

bitmapCache = {}
class IOCCodeRenderer(wx.grid.GridCellRenderer):
	def getImgWidth( self, ioc, height ):
		img = Flags.GetFlagImage( ioc )
		if img:
			imgHeight = int( height * 0.8 )
			imgWidth = int( float(img.GetWidth()) / float(img.GetHeight()) * float(imgHeight) )
			padding = int(height * 0.1)
			return img, imgWidth, imgHeight, padding
		return None, 0, 0, 0

	def Draw(self, grid, attr, dc, rect, row, col, isSelected):
		text = grid.GetCellValue(row, col)

		dc.SetFont( attr.GetFont() )
		w, h = dc.GetTextExtent( text )
		
		ioc = text[:3]
		img, imgWidth, imgHeight, padding = self.getImgWidth(ioc, h)
		
		fg = attr.GetTextColour()
		bg = attr.GetBackgroundColour()
		if isSelected:
			fg, bg = bg, fg
		
		dc.SetBrush( wx.Brush(bg, wx.SOLID) )
		dc.SetPen( wx.TRANSPARENT_PEN )
		dc.DrawRectangle( rect )

		rectText = wx.Rect( rect.GetX()+padding+imgWidth, rect.GetY(), rect.GetWidth()-padding-imgWidth, rect.GetHeight() )
		
		hAlign, vAlign = attr.GetAlignment()
		dc.SetTextForeground( fg )
		dc.SetTextBackground( bg )
		grid.DrawTextRectangle(dc, text, rectText, hAlign, vAlign)

		if img:
			key = (ioc, imgHeight)
			if key not in bitmapCache:
				bitmapCache[key] = img.Scale(imgWidth, imgHeight, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
			dc.DrawBitmap( bitmapCache[key], rect.GetX(), rect.GetY()+(rect.GetHeight()-imgHeight)//2 )

	def GetBestSize(self, grid, attr, dc, row, col):
		text = grid.GetCellValue(row, col)
		dc.SetFont(attr.GetFont())
		w, h = dc.GetTextExtent( text )
		
		img, imgWidth, imgHeight, padding = self.getImgWidth(text[:3], h)
		if img:
			return wx.Size(w + imgWidth + padding, h)
		else:
			return wx.Size(w, h)

	def Clone(self):
		return IOCCodeRenderer()

#reNonDigits = re.compile( '[^0-9]' )

class LookUp( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.colnames = ['Bib', 'First Name', 'Last Name', 'Gender', 'Age', 'Nat', 'License', 'Factor', 'Team', 'Last Entered', 'Last Tag Written']
		self.sortBy = 0
		self.reverseSort = False
		
		bigFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		gbs = wx.GridBagSizer( 2, 2 )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(gbs)
		gbs.SetSizeHints(self)
		
		row = 0
		
		self.lookupBib = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(600,-1))
		self.lookupBib.SetToolTip( wx.ToolTip('Bib number to look up') )
		self.Bind( wx.EVT_TEXT_ENTER, self.onBibChanged, self.lookupBib )
		self.lookupBibLabel = wx.StaticText( self, label='Race number:' )
		gbs.Add(self.lookupBib, pos=(row,2), span=(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		gbs.Add(self.lookupBibLabel, pos=(row,1), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		
		row += 1
		
		self.lookupTag = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(600,-1))
		self.lookupTag.SetToolTip( wx.ToolTip('Tag number to look up') )
		self.Bind( wx.EVT_TEXT_ENTER, self.onTagChanged, self.lookupTag )
		self.lookupTagLabel = wx.StaticText( self, label='Tag EPC:' )
		gbs.Add(self.lookupTag, pos=(row,2), span=(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )
		gbs.Add(self.lookupTagLabel, pos=(row,1), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		
		row += 1
		
		self.resultsArea = wx.StaticText( self, label='' )
		self.resultsArea.SetFont(bigFont)
		gbs.Add(self.resultsArea, pos=(row,2), span=(1,1), flag=wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL )

		self.riderFlag = wx.StaticBitmap(self, -1, wx.NullBitmap, size=(44,28))
		gbs.Add(self.riderFlag, pos=(row,1), span=(1,1), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL )
		
		self.refresh()
		
	def onBibChanged( self, event ):
		self.lookupTag.SetValue('')
		database = Model.database
		if database is None:
			return
		try:
			bib = int(self.lookupBib.GetValue().strip())
			output = ('#' + str(bib) + ': ' + database.getRiderName(bib))
			self.resultsArea.SetLabel(output.replace('&','&&'))
			self.updateFlag(bib)
			self.lookupBib.SetValue('')
		except ValueError:
			self.resultsArea.SetLabel('Bib #' + self.lookupBib.GetValue().strip() + ' Not valid')
			self.updateFlag()
		
	def onTagChanged( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			tag = self.lookupTag.GetValue().strip()
			bibTagNrs = database.lookupTag(tag)
			output=[]
			if len(bibTagNrs) == 0:
				output = ['Tag: ' + tag + ' Not Found']
			for bibTagNr in bibTagNrs:
				output.append('#' + str(bibTagNr[0]) + ': ' + database.getRiderName(bibTagNr[0]) + '\n(Tag ' + str(bibTagNr[1]) + ', ' + tag + ')')
			self.resultsArea.SetLabel(',\n'.join(output))
			self.updateFlag(bibTagNrs[0][0] if len(bibTagNrs) == 1 else None)
			self.lookupTag.SetValue('')
			self.lookupBib.SetValue('')
		except ValueError:
			self.resultsArea.SetLabel('Tag ' + self.lookupTag.GetValue().strip() + ': Not valid')
			self.updateFlag()
			
	def updateFlag( self, bib=None ):
		database = Model.database
		if database is None:
			return
		if bib is None:
			self.riderFlag.SetBitmap(wx.NullBitmap)
			return
		try:
			rider = database.getRider(bib)
			if rider is None:
				return
			nat = rider['NatCode'] if 'NatCode' in rider else ''
			image = Flags.GetFlagImage( nat )
			if image:
				self.riderFlag.SetBitmap(image.Scale(44, 28, wx.IMAGE_QUALITY_HIGH))
			else:
				self.riderFlag.SetBitmap(wx.NullBitmap)
		except ValueError:
			pass
	
	def refresh( self ):
		pass
