import wx
import os
import openpyxl
import datetime
import Model
import Utils
import GetResults
from HighPrecisionTimeEdit import HighPrecisionTimeEdit

def GiveTimes( status=None, time=None ):
	if not status:
		return
	if not time:
		return
	
	with Model.LockRace() as race:
		if not race:
			return
		riders = race.getRiderNums()
		for bib in riders:
			rider = race.getRider(bib)
			if rider.status == status:
				startOffset = race.getStartOffset( bib )				# 0.0 if isTimeTrial.
				unfilteredTimes = [t for t in rider.times if t > startOffset]
				for t in unfilteredTimes:
					if rider.tStatus and t > rider.tStatus:
						#print('Deleting time ' + Utils.formatTime(t) + ' for rider ' + str(bib))
						race.numTimeInfo.delete( bib, t )
						race.deleteTime( bib, t )
						race.setChanged()
				unfilteredTimes = [t for t in rider.times if t > startOffset]  #refresh this as we've deleted times
				rider.setStatus( Model.Rider.Finisher )
				#print('Adding finish time ' + Utils.formatTime(time + startOffset) + ' for rider ' + str(bib))
				if len(unfilteredTimes) > 0:
					lastLapTime = unfilteredTimes[-1]
					race.numTimeInfo.change( bib, lastLapTime, time + startOffset)			# Change entry time (in rider time).
					race.deleteTime( bib, lastLapTime )							# Delete time (in rider time).
					race.addTime( bib, rider.riderTimeToRaceTime(time + startOffset) )		# Add time (in race time).
					race.setChanged()
				else:
					race.numTimeInfo.add( bib, time + startOffset )
					race.addTime( bib, rider.riderTimeToRaceTime(time + startOffset) )
					race.setChanged()
				unfilteredTimes = [t for t in rider.times if t > startOffset]  #refresh this as we've added times
				race.lapNote = getattr( race, 'lapNote', {} )
				for l, t in enumerate(unfilteredTimes):
					if t == time + startOffset:
						if l == 0:
							l += 1
						#print('Setting lap note')
						race.lapNote[(bib, l)] = 'Virtual finish for ' + _(Model.Rider.statusNames[status]) + ' rider'
						race.setChanged()
						break
	Utils.refresh()
	Utils.refreshForecastHistory()

class GiveTimesDialog( wx.Dialog ):
	statusList = [ 'DNF', 'DNS' ]
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id, title=_('Give non-finishers a finish time'))
		self.leaderTime = 0
		self.useLastFinisherTime = 0
		self.status = Model.Rider.DNF
		self.SetBackgroundColour( wx.WHITE )
		
		vs = wx.BoxSizer( wx.VERTICAL )

		title = wx.StaticText( self, label=_("Gives riders who did not finish a virtual finish time.") )
		explain = []
		explain.append( wx.StaticText( self, label=_("Be careful!  There is no Undo.") ) )
		explain.append( wx.StaticText( self, label=_("This deletes times after the status time of riders who did not finish the race,") ) )
		explain.append( wx.StaticText( self, label=_("gives them a final lap time as specified below, and sets their status to 'Finisher'.") ) )
		explain.append( wx.StaticText( self, label=_("Their average speed and ranked position should therefore reflect the number of laps that they were") ) )
		explain.append( wx.StaticText( self, label=_("able to complete successfully.") ) )
		
		fgs = wx.FlexGridSizer(vgap=4, hgap=4, rows=0, cols=2)
		fgs.AddGrowableCol( 1, 1 )
		
		GetTranslation = _
		self.statusName = wx.StaticText( self, label = '{} '.format(_('Change finish time of riders with status:')) )
		fgs.Add( self.statusName, 1, flag=wx.TOP|wx.ALIGN_LEFT )
		self.statusOption = wx.Choice( self, choices=[GetTranslation(n) for n in self.statusList] )
		fgs.Add( self.statusOption, 1, flag=wx.TOP|wx.ALIGN_LEFT )
		self.Bind(wx.EVT_CHOICE, self.onStatusChanged, self.statusOption)
		
		self.useLeaderTime = wx.RadioButton( self, label=_("Winner's time"), style = wx.RB_GROUP )
		self.useLastFinisherTime = wx.RadioButton( self, label=_("Last finisher's time") )
		self.useNominalTime = wx.RadioButton( self, label=_("Nominal race time") )
		self.useCustomTime = wx.RadioButton( self, label=_("Custom") )
		self.Bind( wx.EVT_RADIOBUTTON,self.onSelectTime ) 
		fgs.Add( wx.StaticText( self, label = _("To:")), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		fgs.Add( self.useLeaderTime, 1, flag=wx.TOP|wx.ALIGN_LEFT )
		fgs.AddSpacer( 16 )
		fgs.Add( self.useLastFinisherTime, 1, flag=wx.TOP|wx.ALIGN_LEFT )
		fgs.AddSpacer( 16 )
		fgs.Add( self.useNominalTime, 1, flag=wx.TOP|wx.ALIGN_LEFT )
		fgs.AddSpacer( 16 )
		fgs.Add( self.useCustomTime, 1, flag=wx.TOP|wx.ALIGN_LEFT )
		
		fgs.Add( wx.StaticText( self, label = _("Time:")), flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL )
		self.timeToUse = HighPrecisionTimeEdit( self, size=(140, -1))
		fgs.Add (self.timeToUse, 1, flag=wx.TOP|wx.ALIGN_LEFT )

		vs.Add( title, flag=wx.ALL, border=4 )
		vs.AddSpacer( 8 )
		for e in explain:
			vs.Add( e, flag=wx.LEFT|wx.RIGHT, border=4 )
		vs.AddSpacer( 8 )
		
		vs.Add(fgs, flag=wx.ALL, border=4 )
			
		btnSizer = self.CreateStdDialogButtonSizer( wx.OK|wx.CANCEL )
		self.Bind( wx.EVT_BUTTON, self.onOK, id=wx.ID_OK )
		if btnSizer:
			vs.Add( btnSizer, flag = wx.ALL|wx.EXPAND, border=4 )
			
		self.SetSizerAndFit( vs )
		self.refresh()
		
	def onSelectTime( self, event ):
		if self.useLeaderTime.GetValue():
			self.timeToUse.SetSeconds( self.leaderTime )
		elif self.useLastFinisherTime.GetValue():
			self.timeToUse.SetSeconds( self.lastFinisherTime )
		elif self.useNominalTime.GetValue():
			self.timeToUse.SetSeconds( self.race.minutes*60 )
		elif self.useCustomTime.GetValue():
			self.timeToUse.SetSeconds( 0 )
		return
	
	def onStatusChanged( self, event ):
		if self.statusOption.GetSelection() == 0:
			self.status = Model.Rider.DNF
		elif self.statusOption.GetSelection() == 1:
			self.status = Model.Rider.DNS
		else:
			self.status = None

	def refresh( self ):
		race = Model.race
		if not race:
			return
		self.race = race
		results = GetResults.GetResultsWithData( None )
		lastTime = 0
		for r in results:
			if (r.status == Model.Rider.Finisher):
				t = r.lastTime - r.raceTimes[0]
				if t > lastTime:
					lastTime = t
		self.lastFinisherTime = lastTime
		if results and results[0].status == Model.Rider.Finisher:
			self.leaderTime = results[0].lastTime - results[0].raceTimes[0]
		else:
			self.leaderTime = 0
		self.useLastFinisherTime.SetValue(True)
		self.timeToUse.SetSeconds( self.lastFinisherTime )
		self.statusOption.SetSelection( 1 if self.status == Model.Rider.DNS else 0 )

	def onOK( self, event ):
		if not Utils.MessageOKCancel( self, _('Are you sure you want to change rider finish times?') + '\n' + _('(You cannot undo.)') + '\n' + _(Model.Rider.statusNames[self.status]) + ' ' + _('riders will be given finish time: ') + self.timeToUse.GetValue(), _('Are you sure?') ):
			return
		finishTime = self.timeToUse.GetSeconds()
		GiveTimes( status=self.status, time=finishTime )
		Utils.refresh()
		self.EndModal( wx.ID_OK )
		
if __name__ == '__main__':
	Utils.disable_stdout_buffering()
	app = wx.App(False)
	mainWin = wx.Frame(None,title="CrossMan", size=(600,600))
	giveDNF = GiveDNFDialog(mainWin)
	mainWin.Show()
	giveDNF.ShowModal()
	app.MainLoop()	
