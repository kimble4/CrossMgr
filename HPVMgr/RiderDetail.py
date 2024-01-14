import wx
import re
import os
import sys
import Utils
#import ColGrid
from collections import defaultdict
#from Undo import undo
import datetime
#import Flags

#bitmapCache = {}
#class IOCCodeRenderer(wx.grid.GridCellRenderer):
	#def getImgWidth( self, ioc, height ):
		#img = Flags.GetFlagImage( ioc )
		#if img:
			#imgHeight = int( height * 0.8 )
			#imgWidth = int( float(img.GetWidth()) / float(img.GetHeight()) * float(imgHeight) )
			#padding = int(height * 0.1)
			#return img, imgWidth, imgHeight, padding
		#return None, 0, 0, 0

	#def Draw(self, grid, attr, dc, rect, row, col, isSelected):
		#text = grid.GetCellValue(row, col)

		#dc.SetFont( attr.GetFont() )
		#w, h = dc.GetTextExtent( text )
		
		#ioc = text[:3]
		#img, imgWidth, imgHeight, padding = self.getImgWidth(ioc, h)
		
		#fg = attr.GetTextColour()
		#bg = attr.GetBackgroundColour()
		#if isSelected:
			#fg, bg = bg, fg
		
		#dc.SetBrush( wx.Brush(bg, wx.SOLID) )
		#dc.SetPen( wx.TRANSPARENT_PEN )
		#dc.DrawRectangle( rect )

		#rectText = wx.Rect( rect.GetX()+padding+imgWidth, rect.GetY(), rect.GetWidth()-padding-imgWidth, rect.GetHeight() )
		
		#hAlign, vAlign = attr.GetAlignment()
		#dc.SetTextForeground( fg )
		#dc.SetTextBackground( bg )
		#grid.DrawTextRectangle(dc, text, rectText, hAlign, vAlign)

		#if img:
			#key = (ioc, imgHeight)
			#if key not in bitmapCache:
				#bitmapCache[key] = img.Scale(imgWidth, imgHeight, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
			#dc.DrawBitmap( bitmapCache[key], rect.GetX(), rect.GetY()+(rect.GetHeight()-imgHeight)//2 )

	#def GetBestSize(self, grid, attr, dc, row, col):
		#text = grid.GetCellValue(row, col)
		#dc.SetFont(attr.GetFont())
		#w, h = dc.GetTextExtent( text )
		
		#img, imgWidth, imgHeight, padding = self.getImgWidth(text[:3], h)
		#if img:
			#return wx.Size(w + imgWidth + padding, h)
		#else:
			#return wx.Size(w, h)

	#def Clone(self):
		#return IOCCodeRenderer()

#reNonDigits = re.compile( '[^0-9]' )

class RiderDetail( wx.Panel ):

	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		bs = wx.BoxSizer(wx.VERTICAL)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(bs)
		bs.SetSizeHints(self)
	


	def refresh( self ):
		pass
