import wx
import wx.grid			as gridlib
from wx.lib import masked
import wx.lib.buttons

import bisect
import math
import Model
import Utils
#from ReorderableGrid import ReorderableGrid
#from HighPrecisionTimeEdit import HighPrecisionTimeEdit
#from PhotoFinish import TakePhoto
#from SendPhotoRequests import SendRenameRequests
from InputUtils import MakeKeypadButton
#import OutputStreamer

class CriteriumRecord( wx.Panel ):
	def __init__( self, parent, controller, id = wx.ID_ANY ):
		super().__init__(parent, id)
		# self.SetBackgroundColour( wx.Colour(173, 216, 230) )
		self.SetBackgroundColour( wx.WHITE )

		self.controller = controller
		
		
		#font = wx.Font((0,fontPixels), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		#dc = wx.WindowDC( self )
		#dc.SetFont( font )
		#wNum, hNum = dc.GetTextExtent( '999' )
		#wNum += 8
		#hNum += 8		

		outsideBorder = 4

		vsizer = wx.BoxSizer( wx.VERTICAL )
		fontPixels = 36
		buttonfont = wx.Font((0,int(fontPixels*.6)), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
		fontSize = 18
		self.font = wx.Font( (0,fontSize), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL )
		self.bigFont = wx.Font( (0,int(fontSize*2.0)), wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL )
		
		self.lapType = wx.StaticText( self, label=_('No race in progress') )
		self.lapType.SetFont( self.bigFont )
		
		hbs = wx.GridSizer( 1, 4, 4 )
		
		hbs.Add( self.lapType, flag=wx.EXPAND|wx.GROW )
		
		self.normalBtn = MakeKeypadButton( self, label='&Normal Lap', style=wx.EXPAND|wx.GROW, font = buttonfont)
		self.normalBtn.Bind( wx.EVT_BUTTON, self.DoReset )
		hbs.Add( self.normalBtn, flag=wx.EXPAND )
		
		self.bellBtn = MakeKeypadButton( self, label='Leader on &Bell Lap', style=wx.EXPAND|wx.GROW, font = buttonfont)
		self.bellBtn.Bind( wx.EVT_BUTTON, self.DoBell )
		hbs.Add( self.bellBtn, flag=wx.EXPAND )
		
		self.finishBtn = MakeKeypadButton( self, label='Leader has &Finished', style=wx.EXPAND|wx.GROW, font = buttonfont)
		self.finishBtn.Bind( wx.EVT_BUTTON, self.DoFinish )
		hbs.Add( self.finishBtn, flag=wx.EXPAND )
		
		vsizer.Add( hbs, flag=wx.EXPAND, border=4 )
	
		
		inputExplain = wx.StaticText( self, label=_('Use these buttons to tell CrossMgr when the leader is on the penultimate or final lap.\nOnce this is set, the race minutes value will be adjusted automatically when the leader finishes.') )
		inputExplain.SetFont( self.font )

		
		vsizer.Add( inputExplain, flag=wx.EXPAND|wx.ALL, border=4 )
		
				
		self.SetSizerAndFit(vsizer)
	
	def Layout( self ):
		self.GetSizer().Layout()
		
	def refresh( self ):
		race = Model.race
		Finisher = Model.Rider.Finisher
		raceIsValid = (race and race.isRunning())
		if raceIsValid:
			if race.isCriterium:
				self.lapType.SetLabel('Current lap is: ' + Model.Race.critStatusNames[race.critStatus])
				self.normalBtn.Enable(race.critStatus != Model.Race.CritNormalLap)
				self.bellBtn.Enable(race.critStatus != Model.Race.CritBellLap)
				self.finishBtn.Enable(race.critStatus != Model.Race.CritFinishLap)
			else:
				self.lapType.SetLabel('Race is not a criterium')
				self.normalBtn.Disable()
				self.bellBtn.Disable()
				self.finishBtn.Disable()
		else:
			self.lapType.SetLabel('No race in progress')
			self.normalBtn.Disable()
			self.bellBtn.Disable()
			self.finishBtn.Disable()
		
	def commit( self ):
		pass
	
	def DoReset( self, event ):
		race = Model.race
		if race and race.isRunning() and race.critStatus != Model.Race.CritNormalLap:
			race.critStatus = Model.Race.CritNormalLap
			if race.isCriterium:
				# Try to restore the race minutes
				critMinutes = getattr( race, 'critMinutes', None )
				if critMinutes:
					race.minutes = critMinutes
					race.setChanged()
					self.refresh()
					Utils.MessageOK( self, 'Resetting race time to ' + str(critMinutes) + ' minutes.', title = _('Resetting race time'))
					wx.CallAfter( Utils.refreshForecastHistory )

	def DoBell( self, event ):
		race = Model.race
		if race and race.isRunning() and race.critStatus != Model.Race.CritBellLap:
			prevStatus = race.critStatus
			race.critStatus = Model.Race.CritBellLap
			if race.isCriterium:
				self.refresh()
				Utils.PlaySound( 'bell.wav' )
				race.setChanged()
				if prevStatus == Model.Race.CritFinishLap:
					# If we're reverting from finish lap status, try to restore the race minutes
					critMinutes = getattr( race, 'critMinutes', None )
					if critMinutes:
						race.minutes = critMinutes
						Utils.MessageOK( self, 'Resetting race time to ' + str(critMinutes) + ' minutes.', title = _('Resetting race time'))
				wx.CallAfter( Utils.refreshForecastHistory )
	
	def DoFinish( self, event ):
		race = Model.race
		if race and race.isRunning() and race.critStatus != Model.Race.CritFinishLap:
			race.critStatus = Model.Race.CritFinishLap
			if race.isCriterium:
				critMinutes = getattr( race, 'critMinutes', None )
				if not critMinutes:
					# Save the original race minutes so it can be restored
					race.critMinutes = race.minutes
				# Get the time the leader's times
				leader = race.getLeader()
				category = race.getCategory( leader )
				try:
					leaderTimes = race.getCategoryTimesNums()[category][0]
				except KeyError:
					leaderTimes = race.getLeaderTimesNums()[0]
				
				t = race.curRaceTime()
				if leaderTimes:
					# Get the time the leader started this lap.
					leaderLap = bisect.bisect_right(leaderTimes, t) - 1
					leaderTime = leaderTimes[leaderLap]
					# Set the race minutes to next whole minute
					minutes = int(leaderTime/60.0) + 1
				else:
					# Use the current race time
					minutes = int(t/60.0) + 1
					
				self.refresh()
				race.minutes = minutes
				Utils.PlaySound( 'bell.wav' )
				race.setChanged()
				Utils.MessageOK( self, 'Setting race time to ' + str(minutes) + ' minutes.', title = _('Setting race time'))
				wx.CallAfter( Utils.refreshForecastHistory )
	
	
if __name__ == '__main__':
	Utils.disable_stdout_buffering()
	app = wx.App(False)
	mainWin = wx.Frame(None,title="CrossMan", size=(600,600))
	Model.setRace( Model.Race() )
	Model.getRace()._populate()
	CriteriumRecord = CriteriumRecord(mainWin, None)
	CriteriumRecord.refresh()
	mainWin.Show()
	app.MainLoop()
