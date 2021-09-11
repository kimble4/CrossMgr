import wx
import sys
import math
import operator
from bisect import bisect_left
import Model
import Utils
from GanttChartPanel import makeColourGradient, makePastelColours, lighterColour
from GetResults import GetResults

class GapChartPanel(wx.Panel):
	def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
				size=wx.DefaultSize, style=wx.NO_BORDER,
				name="GapChartPanel" ):
		
		super().__init__(parent, id, pos, size, style, name)
		
		self.SetBackgroundColour(wx.WHITE)
		self.SetBackgroundStyle( wx.BG_STYLE_CUSTOM )
		
		self.data = None
		self.labels = None
		self.status = None
		self.maxLaps = 0
		self.earliestLapTimes = []
		self.maximumGap = 0.0
		self.yTop = self.yBottom = 0
		self.xLeft = self.xRight = 0
		self.xMove = self.yMove = 0
		
		class MoveTimer( wx.Timer ):
			def __init__( self, cb ):
				super().__init__()
				self.cb = cb
			
			def Notify( self ):
				wx.CallAfter( self.cb )
		
		self.moveTimer = MoveTimer( self.Refresh )
		
		self.colours = makeColourGradient(2.4,2.4,2.4,0,2,4,128,127,500)
		self.lighterColours = [lighterColour(c) for c in self.colours]
		
		self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.Bind(wx.EVT_MOTION, self.OnMove)

	def DoGetBestSize(self):
		return wx.Size(128, 100)

	def SetForegroundColour(self, colour):
		wx.Panel.SetForegroundColour(self, colour)
		self.Refresh()
		
	def SetBackgroundColour(self, colour):
		wx.Panel.SetBackgroundColour(self, colour)
		self.Refresh()
		
	def GetDefaultAttributes(self):
		"""
		Overridden base class virtual.  By default we should use
		the same font/colour attributes as the native wx.StaticText.
		"""
		return wx.StaticText.GetClassDefaultAttributes()

	def ShouldInheritColours(self):
		"""
		Overridden base class virtual.  If the parent has non-default
		colours then we want this control to inherit them.
		"""
		return True

	def SetData( self, data, labels = None, interp = None, ):
		"""
		* data is a list of lists.  Each a list of race times.
		* labels are the names of the series.  Optional.
		"""
		self.data = None
		self.labels = None
		if data and any( s for s in data ):
			self.data = data
			if labels:
				self.labels = ['{}'.format(lab) for lab in labels]
				if len(self.labels) < len(self.data):
					self.labels = self.labels + [''] * (len(self.data) - len(self.labels))
				elif len(self.labels) > len(self.data):
					self.labels = self.labels[:len(self.data)]
			else:
				self.labels = [''] * len(data)
			
		# Find the first lap times.
		self.earliestLapTimes = []
		if data:
			self.maxLaps = max( len(times) for times in data )
			self.earliestLapTimes = [min( times[iLap] for times in data if len(times) > iLap ) for iLap in range(self.maxLaps)]
		
		# Add a sentinal to avoid edge cases.
		self.earliestLapTimes.append( sys.float_info.max )
		
		# Find the maximum gap.
		self.maximumGap = 0.0
		for times in data:
			iLap = 0
			for t in times:
				while not (self.earliestLapTimes[iLap] <= t < self.earliestLapTimes[iLap+1]):
					iLap += 1
				self.maximumGap = max( self.maximumGap, t - self.earliestLapTimes[iLap] )
		
		self.interp = interp
		self.Refresh()
		
	def OnPaint(self, event ):
		dc = wx.PaintDC(self)
		self.Draw(dc)

	def OnSize(self, event):
		self.xMove = self.yMove = 0
		if self.moveTimer.IsRunning():
			self.moveTimer.Stop()
		self.Refresh()
		event.Skip()
		
	def OnMove( self, event ):
		self.xMove, self.yMove = event.GetPosition()
		if self.yTop <= self.yMove <= self.yBottom and self.xLeft <= self.xMove <= self.xRight:
			if not self.moveTimer.IsRunning():
				self.moveTimer.StartOnce( 50 )
			
	intervals = (1, 2, 5, 10, 15, 20, 30, 1*60, 2*60, 5*60, 10*60, 15*60, 20*60, 30*60, 1*60*60, 2*60*60, 4*60*60, 6*60*60, 8*60*60, 12*60*60) + tuple(24*60*60*k for k in range(1,200))
	def Draw( self, dc ):
		size = self.GetClientSize()
		width = size.width
		height = size.height
		
		backColour = self.GetBackgroundColour()
		backBrush = wx.Brush(backColour, wx.SOLID)
		greyPen = wx.Pen( wx.Colour(200, 200, 200), 1 )
		dc.SetBackground(backBrush)
		dc.Clear()
		
		tooSmall = (width < 50 or height < 24)
		
		if not self.data or tooSmall:
			self.empty = True
			if tooSmall:
				dc.SetPen( wx.BLACK_DASHED_PEN )
				dc.DrawLine( 0, height//2, width, height//2 )
			return
		
		self.empty = False
		
		# Draw the chart scale.
		border = min( width, height ) // 30
		scaleFontSize = 14
		scaleFont = wx.Font( (0, scaleFontSize), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL )
		
		# Height of drawing field.
		self.yTop = yTop = border + scaleFontSize + border//2
		self.yBottom = yBottom = height - border - scaleFontSize - border//2 - scaleFontSize - border//2

		# Labels
		labelFontSize = min( scaleFontSize, max(1, int( 1.0/1.15 * (yBottom - yTop) / len(self.labels) )) )
		labelFont = wx.Font( (0, labelFontSize), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL )
		
		dc.SetFont( labelFont )
		maxLabelWidth = max( dc.GetTextExtent(label)[0] for label in self.labels )
		
		dc.SetFont( scaleFont )

		# Vertical scale
		scaleTick = 1
		for i in range(bisect_left(self.intervals, self.maximumGap/2), -1, -1):
			if self.intervals[i] * 4 < self.maximumGap:
				scaleTick = self.intervals[i]
				break
		
		tickText = []
		tickTextWidth = scaleTextHeight = 0
		tVertMax = 1
		for i in range(len(self.intervals)):
			t = scaleTick * i
			tVertMax = max( t, tVertMax )
			tickText.append( Utils.formatTimeGap(t) )
			tWidth, scaleTextHeight = dc.GetTextExtent( tickText[-1] )
			tickTextWidth = max( tickTextWidth, tWidth )
			if t >= self.maximumGap:
				break
		
		# Width of the drawing field.		
		self.xLeft = xLeft = border + scaleTextHeight + border//2 + tickTextWidth + border//2
		self.xRight = xRight = width - border - maxLabelWidth - border//2
		xMost = xRight - int((xRight - xLeft) / (self.maxLaps))

		# Vertical axis label.
		tWidth, tHeight = dc.GetTextExtent( _('Gap') )
		xText = border
		yText = yTop + (yBottom - yTop)//2 + tWidth//2
		dc.DrawRotatedText( _('Gap'), xText, yText, 90 )
		
		dc.SetPen( greyPen )

		# Vertical scale text.
		for i, text in enumerate(tickText):
			tWidth, tHeight = dc.GetTextExtent( text )
			xText = border + scaleTextHeight + border//2 + tickTextWidth - tWidth
			yText = yTop + i * (yBottom - yTop) // (len(tickText)-1)
			dc.DrawText( text, xText, yText - labelFontSize//2 )
			dc.DrawLine( xLeft - 3, yText, xMost, yText )
		
		# Horizontal axis label.
		tWidth, tHeight = dc.GetTextExtent( _('Lap') )
		xText = xLeft + (xRight - xLeft)//2 - tWidth//2
		yText = height - border - tHeight
		dc.DrawText( _('Lap'), xText, yText )
		
		# Horizontal scale text.
		yText = height - border - scaleTextHeight*2 - border//2
		xTextRightLast = 0
		for lap in range(self.maxLaps):
			text = str(lap)
			tWidth, tHeight = dc.GetTextExtent( text )
			xText = xLeft + lap * (xRight - xLeft)//self.maxLaps - tWidth//2
			dc.DrawLine( xText + tWidth//2, yTop, xText + tWidth//2, yBottom+3 )
			if xText > xTextRightLast:
				dc.DrawText( text, xText, yText )
				dc.DrawText( text, xText, border )
				xTextRightLast = xText + tWidth + border
		
		# Border
		dc.DrawLines( ((xMost, yTop), (xLeft, yTop), (xLeft, yBottom), (xMost, yBottom)) )
		
		# Draw the gap lines and labels.
		dc.SetFont( labelFont )
		xText = xRight + border//2

		yDelta = yBottom - yTop
		points = []
		labelXY = []
		for iData, times in enumerate(data):
			points.clear()
			iLap = 0
			for t in times:
				while not (self.earliestLapTimes[iLap] <= t < self.earliestLapTimes[iLap+1]):
					iLap += 1
				gap = t - self.earliestLapTimes[iLap]
				y = int(yTop + yDelta * (gap / tVertMax))
				x = int(xLeft + iLap * (xRight - xLeft) / self.maxLaps)
				points.append( (x, y) )
			dc.SetPen( wx.Pen(self.colours[iData % len(self.colours)], 4) )
			dc.DrawLines( points )
			
			# Record the label and connect it to the gap line.
			labelXY.append( (labels[iData], *points[-1]) )

		# Sort by the finish gaps.
		labelXY.sort( key=operator.itemgetter(2) )
		dc.SetPen( greyPen )

		# Construct a list of rectangles for each label so we can check for overlaps.
		# Default to putting the label next to the corresponding gap.
		labelLineHeight = int(labelFontSize*1.15)
		xyRects = [[x, y, wx.Rect(x, y, 10, labelLineHeight), label] for label, x, y in labelXY]
		del labelXY
		
		# Check the labels and reposition to remove overlaps.
		for p in range(len(xyRects)):
			# Check if two adjacent labels overlap each other.
			foundConflict = False
			for b in range(len(xyRects)-1):
				if xyRects[b][2].Bottom > xyRects[b+1][2].Top:
					foundConflict = True
					
					# Find the top of the conflict group
					for a in range(b, 0, -1):
						if xyRects[a][2].Top > xyRects[a-1][2].Bottom:
							break
					else:
						a = 0
						
					# Find the bottom of the conflict group
					for c in range(b, len(xyRects)-1):
						if xyRects[c][2].Bottom < xyRects[c+1][2].Top:
							break
					else:
						c = len(xyRects) - 1
					
					xyRectsConflict = xyRects[a:c+1]
						
					# Compute the least-squares error for the non-overlapping position for the conflict labels.
					tCentroid = sum( xyr[1] for xyr in xyRectsConflict ) / len(xyRectsConflict)
					y = tCentroid - labelLineHeight*(len(xyRectsConflict) - 1) / 2
					
					# Ensure we don't go off the drawing area.
					if y < yTop:
						y = yTop
					elif y + labelLineHeight*(len(xyRectsConflict)-1) > yBottom:
						y = yBottom - labelLineHeight*(len(xyRectsConflict)-1)

					# Reposition the labels so they don't overlap.
					y = int(y)			
					for xyr in xyRectsConflict:
						xyr[2].SetY( y )
						y += labelLineHeight
			
			if not foundConflict:
				break
			
		# Draw the labels in their optimal non-overlapping positions.
		border2 = border//2
		border4 = border//4
		labelFontSize2 = labelFontSize//2
		for x, y, r, label in xyRects:
			yText = r.GetY() - labelFontSize2
			dc.DrawLines( ((x, y), (x + border4, y), (xText - border2, yText + labelFontSize2), (xText - border4, yText + labelFontSize2)) )
			dc.DrawText( label, xText, yText )
		
		if self.yTop <= self.yMove <= self.yBottom and self.xLeft <= self.xMove <= self.xRight:
			gap = self.maximumGap * (self.yMove - self.yTop) / (self.yBottom - self.yTop)
			text = Utils.formatTimeGap( gap )
			tWidth, tHeight = dc.GetTextExtent( text )
			xText = border + scaleTextHeight + border2 + tickTextWidth - tWidth
			dc.SetPen( wx.BLACK_PEN )
			dc.SetBrush( wx.YELLOW_BRUSH )
			dc.DrawLine( self.xLeft - border2, self.yMove, self.xRight + border2, self.yMove )
			dc.DrawRoundedRectangle( xText - border4, self.yMove - labelFontSize2 - border4, tWidth + border2, tHeight + border2, border4 )
			dc.DrawText( text, xText, self.yMove - labelFontSize2 )
			
		# Draw outlines around the groups separated by less than a second.
		
			
	def OnEraseBackground(self, event):
		pass
		
if __name__ == '__main__':
	
	Model.setRace( Model.Race() )
	race = Model.getRace()
	race._populate()

	data = []
	labels = []
	interp = []
	category = None
	for num in race.riders.keys():
		category = race.getCategory( num )
		break
	for rr in GetResults( category ):
		data.append( rr.raceTimes )
		labels.append( str(rr.num) )
		interp.append( rr.interp )
	
	app = wx.App(False)
	mainWin = wx.Frame(None,title="GapChartPanel", size=(600,400))
	gapChart = GapChartPanel( mainWin )
	gapChart.SetData( data, labels, interp )

	mainWin.Show()
	app.MainLoop()
