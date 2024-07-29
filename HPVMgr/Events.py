import wx
import re
import os
import sys
import Utils
from collections import defaultdict
import datetime
import Model
import xlsxwriter
from AddExcelInfo import AddExcelInfo 
import Version
import copy

class Events( wx.Panel ):
	
	OrangeColour = wx.Colour( 255, 165, 0 )
	
	def getExcelFormatsXLSX( workbook ):
		titleStyle = workbook.add_format({
			'bold': True,
			'font_size': 17,
		})

		headerStyleAlignLeft = workbook.add_format({
			'bottom':	2,
			'bold':		True,
			'text_wrap':True,
		})
		
		headerStyleAlignRight = workbook.add_format({
			'bottom':	2,
			'bold':		True,
			'text_wrap':True,
			'align':	'right',
		})
		
		styleAlignLeft = workbook.add_format()
		
		styleAlignRight = workbook.add_format({
			'align':	'right',
		})
		
		#---------------------------------------------------------------
		styleTime = workbook.add_format({
			'align':	'right',
			'num_format': 'hh:mm:ss.000',
		})
		
		styleMMSS = workbook.add_format({
			'align':	'right',
			'num_format': 'mm:ss.000',
		})
		
		styleSS = workbook.add_format({
			'align':	'right',
			'num_format': 'ss.000',
		})
		
		#---------------------------------------------------------------
		# Low-precision time formats
		#
		styleTimeLP = workbook.add_format({
			'align':	'right',
			'num_format': 'hh:mm:ss',
		})
		
		styleMMSSLP = workbook.add_format({
			'align':	'right',
			'num_format': 'mm:ss',
		})
		
		styleSSLP = workbook.add_format({
			'align':	'right',
			'num_format': 'ss',
		})
		
		return {
			'titleStyle':				titleStyle,
			'headerStyleAlignLeft':		headerStyleAlignLeft,
			'headerStyleAlignRight':	headerStyleAlignRight,
			'styleAlignLeft':			styleAlignLeft,
			'styleAlignRight':			styleAlignRight,
			'styleTime':				styleTime,
			'styleHHMMSS':				styleTime,
			'styleMMSS':				styleMMSS,
			'styleSS':					styleSS,

			'styleTimeLP':				styleTimeLP,
			'styleHHMMSSLP':			styleTimeLP,
			'styleMMSSLP':				styleMMSSLP,
			'styleSSLP':				styleSSLP,
		}
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		self.season = None
		self.evt = None
		self.rnd = None
		
		
		bigFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		labelAlign = wx.ALIGN_RIGHT | wx.ALIGN_CENTRE_VERTICAL
		vs = wx.BoxSizer(wx.VERTICAL)
		gbs = wx.GridBagSizer(5, 5)
		row = 0
		
		#seasons list
		self.seasonsGrid = wx.grid.Grid( self )
		self.seasonsGrid.CreateGrid(0, 2)
		self.seasonsGrid.SetColLabelValue(0, 'Season')
		self.seasonsGrid.SetColLabelValue(1, 'Events in season')
		self.seasonsGrid.HideRowLabels()
		self.seasonsGrid.SetRowLabelSize( 0 )
		self.seasonsGrid.SetMargins( 0, 0 )
		self.seasonsGrid.AutoSizeColumns( True )
		self.seasonsGrid.DisableDragColSize()
		self.seasonsGrid.DisableDragRowSize()
		self.seasonsGrid.EnableEditing(False)
		self.seasonsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onSeasonsRightClick )
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onSeasonsRightClick )
		self.seasonsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectSeason )
		gbs.Add( self.seasonsGrid, pos=(row,0), span=(1,1), flag=wx.EXPAND )
		
		row += 1
		gbs.Add( wx.StaticText( self, label='Current selection:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		
		row += 1
		gbs.Add( wx.StaticText( self, label='Sign-on spreadsheet:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		
		row += 2
		gbs.Add( wx.StaticText( self, label='Race allocation HTML page:' ), pos=(row,0), span=(1,1), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT )
		
		row = 0
		
		#events list
		self.eventsGrid = wx.grid.Grid( self )
		self.eventsGrid.CreateGrid(0, 3)
		self.eventsGrid.SetColLabelValue(0, 'Season\'s events')
		self.eventsGrid.SetColLabelValue(1, 'Date')
		self.eventsGrid.SetColLabelValue(2, 'Rounds in event')
		self.eventsGrid.HideRowLabels()
		self.eventsGrid.SetRowLabelSize( 0 )
		self.eventsGrid.SetMargins( 0, 0 )
		self.eventsGrid.AutoSizeColumns( True )
		self.eventsGrid.DisableDragColSize()
		self.eventsGrid.DisableDragRowSize()
		self.eventsGrid.EnableEditing(False)
		self.eventsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onEventsRightClick )
		self.eventsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onEventsRightClick )
		self.eventsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectEvt )
		gbs.Add( self.eventsGrid, pos=(row,1), span=(1,1), flag=wx.EXPAND )
		
		row += 1
		
		#current selection
		hs = wx.BoxSizer( wx.HORIZONTAL )
		self.currentSelection = wx.StaticText( self, label='None' )
		self.currentSelection.SetFont(bigFont)
		hs.Add( self.currentSelection, flag=wx.ALIGN_CENTER_VERTICAL )
		
		hs.AddStretchSpacer()
		
		bs = wx.BoxSizer( wx.VERTICAL )
		#edit button
		self.editEntryButton = wx.Button( self, label='Edit entries')
		self.editEntryButton.SetToolTip( wx.ToolTip('Go to the EventEntry screen to enter riders in the event...'))
		self.editEntryButton.Disable()
		self.Bind( wx.EVT_BUTTON, self.onEditEntryButton, self.editEntryButton )
		bs.Add( self.editEntryButton, flag=wx.ALIGN_RIGHT )
		
		#edit button
		self.editRacesButton = wx.Button( self, label='Edit races')
		self.editRacesButton.SetToolTip( wx.ToolTip('Go to the RaceAllocation screen to allocate racers to races...'))
		self.editRacesButton.Disable()
		self.Bind( wx.EVT_BUTTON, self.onEditRacesButton, self.editRacesButton )
		bs.Add( self.editRacesButton, flag=wx.ALIGN_RIGHT )
		
		hs.Add( bs, flag=wx.ALIGN_CENTER_VERTICAL)
	
		gbs.Add( hs, pos=(row,1), span=(1,4), flag=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.EXPAND )
		
		row += 1
		
		#signon filename
		self.signonFileName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(600,-1))
		self.signonFileName.SetToolTip( wx.ToolTip('Path to write the sign-on sheet (relative to the database file)') )
		self.signonFileName.SetValue( '' )
		self.signonFileName.Disable()
		self.signonFileName.Bind( wx.EVT_TEXT_ENTER, self.onEditSignon )
		gbs.Add( self.signonFileName, pos=(row,1), span=(1,3), flag=wx.ALIGN_LEFT )
		
		row += 1
		
		#write sign-on sheet button
		self.writeSignonButton = wx.Button( self, label='Write sign-on sheet')
		self.writeSignonButton.SetToolTip( wx.ToolTip('Click to write the sign-on sheet for the selected event to disk'))
		self.writeSignonButton.Disable()
		self.writeSignonButton.Bind( wx.EVT_BUTTON, self.writeSignonSheet )
		gbs.Add( self.writeSignonButton, pos=(row,1), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		row += 1
		
		#allocation filename
		self.allocationFileName = wx.TextCtrl( self, style=wx.TE_PROCESS_ENTER|wx.TE_RIGHT, size=(600,-1))
		self.allocationFileName.SetToolTip( wx.ToolTip('Path to write the race allocation (relative to the database file)') )
		self.allocationFileName.SetValue( '' )
		self.allocationFileName.Disable()
		self.allocationFileName.Bind( wx.EVT_TEXT_ENTER, self.onEditAllocation )
		gbs.Add( self.allocationFileName, pos=(row,1), span=(1,3), flag=wx.ALIGN_LEFT )
		
		row += 1
		
		#write allocation list button
		self.writeAllocationButton = wx.Button( self, label='Write allocation page')
		self.writeAllocationButton.SetToolTip( wx.ToolTip('Click to write the race allocation for the selected event to HTML'))
		self.writeAllocationButton.Disable()
		self.writeAllocationButton.Bind( wx.EVT_BUTTON, self.writeAllocationHTML )
		gbs.Add( self.writeAllocationButton, pos=(row,1), span=(1,1), flag=wx.ALIGN_BOTTOM|wx.ALIGN_LEFT )
		
		
		row = 0
		#rounds list
		self.roundsGrid = wx.grid.Grid( self )
		self.roundsGrid.CreateGrid(0, 2)
		self.roundsGrid.SetColLabelValue(0, 'Event\'s rounds')
		self.roundsGrid.SetColLabelValue(1, 'Races in round')
		self.roundsGrid.HideRowLabels()
		#self.roundsGrid.AutoSize()
		self.roundsGrid.SetRowLabelSize( 0 )
		self.roundsGrid.SetMargins( 0, 0 )
		self.roundsGrid.AutoSizeColumns( True )
		self.roundsGrid.DisableDragColSize()
		self.roundsGrid.DisableDragRowSize()
		self.roundsGrid.EnableEditing(False)
		self.roundsGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onRoundsRightClick )
		self.roundsGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onRoundsRightClick )
		self.roundsGrid.Bind( wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.selectRnd )
		gbs.Add( self.roundsGrid, pos=(row,2), span=(1,1), flag=wx.EXPAND )
		
		row += 2
		
		self.signonBrowseButton = wx.Button( self, label='{}...'.format(_('Browse')) )
		self.signonBrowseButton.Disable()
		self.signonBrowseButton.Bind( wx.EVT_BUTTON, self.onBrowseSignon )
		gbs.Add( self.signonBrowseButton, pos=(row,4), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
	
		row += 2
		
		self.allocationBrowseButton = wx.Button( self, label='{}...'.format(_('Browse')) )
		self.allocationBrowseButton.Disable()
		self.allocationBrowseButton.Bind( wx.EVT_BUTTON, self.onBrowseAllocation )
		gbs.Add( self.allocationBrowseButton, pos=(row,4), span=(1,1), flag=wx.ALIGN_CENTRE_VERTICAL )
		
		vs.Add( gbs )
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def writeSignonSheet( self, event=None ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'signonFileName' in evt:
					xlFName = evt['signonFileName']
					if not os.path.isabs(xlFName): 
						xlFName = os.path.normpath( os.path.join( os.path.dirname(database.fileName), xlFName) )  #signon sheet path is relative to database file
					if not os.path.isdir(os.path.dirname(xlFName)):
						Utils.MessageOK(self,
										'{}\n"{}"\n\n{}\n{}'.format(
											_('Cannot write'), xlFName,
											_('Destination directory does not exist!'),
											_('Check the sign-on sheet path.')
										),
										_('Cannot write sign-on sheet'), iconMask=wx.ICON_ERROR )
						return
					if xlFName and 'rounds' in evt:
						#check for unallocated racers before continuing
						unallocatedRacers = database.getUnallocatedRacers()
						if len(unallocatedRacers) > 0:
							Utils.writeLog('Not writing sign-on sheet, "' + evtName + '" has unallocated racers: ' + str(unallocatedRacers))
							Utils.MessageOK(self,
										'{}\n{}\n\n{}'.format(
											_('Racers are entered in the event but have not been allocated to races:'),
											', '.join('#' + str(bib) for bib in unallocatedRacers),
											_('Check the Race Allocation for each round.')
										),
										_('Cannot write sign-on sheet'), iconMask=wx.ICON_ERROR )
							return
						wb = xlsxwriter.Workbook( xlFName )
						formats = Events.getExcelFormatsXLSX( wb )
						ues = Utils.UniqueExcelSheetName()
						for rndName in evt['rounds']:
							rnd = evt['rounds'][rndName]
							nrRaces = len(rnd['races']) if 'races' in rnd else 0
							if nrRaces > 1:
								#first, individual sheets for each race
								for i in range(nrRaces):
									sheetCur = wb.add_worksheet( ues.getSheetName(rndName + ' Race' + str(i+1))  )
									database.getRoundAsExcelSheetXLSX( rndName, formats, sheetCur, raceNr=i+1 )
								#now, a combined sheet for the round (for use after merging races)
								sheetCur = wb.add_worksheet( ues.getSheetName(rndName + ' Combined') )
								database.getRoundAsExcelSheetXLSX( rndName, formats, sheetCur )
							else:
								#everyone in one race, only need a single sheet
								sheetCur = wb.add_worksheet( ues.getSheetName(rndName) )
								database.getRoundAsExcelSheetXLSX( rndName, formats, sheetCur )
						AddExcelInfo( wb )
						try:
							wb.close()
							# if self.launchExcelAfterPublishingResults:
							# 	Utils.LaunchApplication( xlFName )
							Utils.writeLog( '{}: {}'.format(_('Excel file written to'), xlFName) )
							Utils.MessageOK(self, '{}:\n\n   {}'.format(_('CrossMgr Excel file written to'), xlFName), _('Write sign-on sheet'))
							return
						except IOError as e:
							logException( e, sys.exc_info() )
							Utils.MessageOK(self,
										'{} "{}"\n\n{}\n{}'.format(
											_('Cannot write'), xlFName,
											_('Check if this spreadsheet is already open.'),
											_('If so, close it, and try again.')
										),
										_('Excel File Error'), iconMask=wx.ICON_ERROR )
							return
						except Exception as e:
							Utils.logException( e, sys.exc_info() )
							return
				Utils.MessageOK(self, 'Sign-on sheet filename is not set!\nConfigure the sign-on sheet location for "' + evtName + '" on the \'Events\' screen, and try again.', _('Write sign-on sheet'), iconMask = wx.ICON_ERROR)
				
	def writeAllocationHTML( self, event=None ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'allocationFileName' in evt:
					htmlFName = evt['allocationFileName']
					if not os.path.isabs(htmlFName): 
						htmlFName = os.path.normpath( os.path.join( os.path.dirname(database.fileName), htmlFName) )  #allocation page path is relative to database file
					if not os.path.isdir(os.path.dirname(htmlFName)):
						Utils.MessageOK(self,
										'{}\n"{}"\n\n{}\n{}'.format(
											_('Cannot write'), htmlFName,
											_('Destination directory does not exist!'),
											_('Check the allocation page path.')
										),
										_('Cannot write allocation page'), iconMask=wx.ICON_ERROR )
						return
					if htmlFName and 'rounds' in evt:
						#check for unallocated racers before continuing
						unallocatedRacers = database.getUnallocatedRacers()
						if len(unallocatedRacers) > 0:
							Utils.writeLog('Not writing allocation web page, "' + evtName + '" has unallocated racers: ' + str(unallocatedRacers))
							Utils.MessageOK(self,
										'{}\n{}\n\n{}'.format(
											_('Racers are entered in the event but have not been allocated to races:'),
											', '.join('#' + str(bib) for bib in unallocatedRacers),
											_('Check the Race Allocation for each round.')
										),
										_('Cannot write allocation page'), iconMask=wx.ICON_ERROR )
							return
						# Read the html header.
						htmlHeaderFile = os.path.join(Utils.getHtmlFolder(), 'AllocationHeader.html')
						try:
							with open(htmlHeaderFile, encoding='utf8') as fp:
								header = fp.read()
						except Exception as e:
							Utils.logException( e, sys.exc_info() )
							Utils.MessageOK(self, _('Cannot read HTML header file.  Check program installation.'),
											_('Html Header Read Error'), iconMask=wx.ICON_ERROR )
							return
						# Read the html footer.
						htmlFooterFile = os.path.join(Utils.getHtmlFolder(), 'AllocationFooter.html')
						try:
							with open(htmlFooterFile, encoding='utf8') as fp:
								footer = fp.read()
						except Exception as e:
							Utils.logException( e, sys.exc_info() )
							Utils.MessageOK(self, _('Cannot read HTML footer file.  Check program installation.'),
											_('Html Footer Read Error'), iconMask=wx.ICON_ERROR )
							return
						
						#main heading
						html = header + '<h1>' + evtName + ' ' + re.split(' |{', database.eventCategoryTemplate)[0] + ' Allocation<h1>\n'
						#generate the allocation tables
						processed = []
						for rndNr, rndName in enumerate(evt['rounds']):
							if rndNr in processed:
								continue
							processed.append(rndNr)
							rnd = evt['rounds'][rndName]
							#check if it's a time trial
							isTT = False
							if 'useStartTimes' in rnd:
								if rnd['useStartTimes']:
									isTT = True
							allocation = set(map(tuple, database.getRoundAllocation(rndName)))  #get allocation as a set of tuples for comparison
							namesList = ['Round ' + str(rndNr+1) + ' (' + rndName + ')']
							for nr, name in enumerate(evt['rounds']):  #inner loop comparing alocation to other rounds
								if nr not in processed:
									r = evt['rounds'][name]
									al = set(map(tuple, database.getRoundAllocation(name)))
									tt = False
									if 'useStartTimes' in r:
										if r['useStartTimes']:
											tt = True
									if al == allocation and tt == isTT:
										namesList.append('Round ' + str(nr+1) + ' (' + name + ')')
										processed.append(nr)
							
							nrRaces = len(rnd['races']) if 'races' in rnd else 0
							if nrRaces > 1:
								#multiple races
								html += '<h2>' + ',<br>'.join(namesList) + ':</h2>\n'
								if isTT:
									html += '<p class="allocation">Individual start times:</p>\n'
								for i in range(nrRaces):
									html += '<h3>' + database.eventCategoryTemplate.format(i+1) + ':</h3>\n'
									if isTT:
										html += database.getStartTimesHTML( rndName, raceNr=i+1 )
									else:
										html += database.getRoundAllocationHTML( rndName, raceNr=i+1 )
							else:
								#everyone in one race
								html += '<h2 class="alltogether">' + ',<br>'.join(namesList) + ':</h2>\n'
								if isTT:
									html += '<p class="allocation">Individual start times:</p>\n'
									html += database.getStartTimesHTML( rndName )
								else:
									html += '<p class="allocation">All racers in one group.</p>\n'
							html += '<hr>'
						#datestamp and footer
						html = html[:-4] + '<p class="datestamp">Generated at: ' + datetime.datetime.now().strftime("%Y-%b-%d %H:%M:%S") + '</p>\n'
						html += footer
							
						# Write out the results.
						try:
							with open(htmlFName, 'w', encoding='utf8') as fp:
								fp.write( html )
								Utils.MessageOK(self, '{}:\n\n   {}'.format(_('Html Race Allocation written to'), htmlFName), _('Html Write'))
							Utils.LaunchApplication( htmlFName )
						except Exception as e:
							Utils.logException( e, sys.exc_info() )
							Utils.MessageOK(self, '{}\n\t\t{}\n({}).'.format(_('Cannot write HTML file'), e, htmlFName),
											_('Html Write Error'), iconMask=wx.ICON_ERROR )
						return
				Utils.MessageOK(self, 'Allocation page filename is not set!\nConfigure the allocation page location for "' + evtName + '" on the \'Events\' screen, and try again.', _('Write allocation page'), iconMask = wx.ICON_ERROR)
		
	def selectSeason( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.season = row
			self.evt = None
			self.rnd = None
			self.commit()
			self.updateSignonSheetName()
			self.updateAllocationPageName()
			self.refreshSeasonsGrid()
			self.refreshEventsGrid()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
			

	def onSeasonsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Seasons')
		add = menu.Append( wx.ID_ANY, 'Add new season', 'Add a new season...' )
		self.Bind( wx.EVT_MENU, self.addSeason, add )
		if row >= 1 or (row == 0 and len(self.seasonsGrid.GetCellValue(row, 0).strip()) > 0):
			rename = menu.Append( wx.ID_ANY, 'Rename ' + database.getSeasonsList()[row], 'Rename this season...' )
			self.Bind( wx.EVT_MENU, lambda event, r=row: self.renameSeason(event, r), rename )
			duplicate = menu.Append( wx.ID_ANY, 'Duplicate ' + database.getSeasonsList()[row], 'Duplicate this season...' )
			self.Bind( wx.EVT_MENU, lambda event, r=row: self.duplicateSeason(event, r), duplicate )
			delete = menu.Append( wx.ID_ANY, 'Delete ' + database.getSeasonsList()[row] + ' from list', 'Delete this season...' )
			self.Bind( wx.EVT_MENU, lambda event, r=row: self.deleteSeason(event, r), delete )
			
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addSeason( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			with wx.TextEntryDialog(self, 'Enter the name for the new season:', caption='Add season', value='New Season', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newSeason = dlg.GetValue()
					with Model.LockDatabase() as db:
						if newSeason not in db.seasons:
							db.seasons[newSeason] = { 'categories':None }
							db.setChanged()
							self.season = len(db.seasons) - 1
							self.commit()
						else:
							Utils.MessageOK( self, 'Season ' + newSeason +' already exists!', title = 'Season exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
					self.refreshSeasonsGrid()
					self.refreshEventsGrid()
					self.refreshRoundsGrid()
					self.refreshCurrentSelection()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def renameSeason( self, event, row ):
		database = Model.database
		if database is None:
			return
		try:
			oldSeason = self.seasonsGrid.GetCellValue(row, 0)
			with wx.TextEntryDialog(self, 'Enter the new name for this season:', caption='Rename season', value=oldSeason, style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newSeason = dlg.GetValue()
					with Model.LockDatabase() as db:
						if newSeason not in db.seasons:
							db.seasons = {newSeason if k == oldSeason else k:v for k,v in db.seasons.items()}
							db.setChanged()
							self.season = len(db.seasons) - 1
							self.commit()
						else:
							Utils.MessageOK( self, 'Season ' + newSeason +' already exists!', title = 'Season exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
					self.refreshSeasonsGrid()
					self.refreshEventsGrid()
					self.refreshRoundsGrid()
					self.refreshCurrentSelection()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def duplicateSeason( self, event, row ):
		database = Model.database
		if database is None:
			return
		try:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[row]
				newSeason = 'Copy of ' + seasonName
				if newSeason not in db.seasons:
					season = db.seasons[seasonName]
					db.seasons[newSeason] = copy.deepcopy(season)
					db.setChanged()
					Utils.writeLog( 'duplicateSeason: Copied season "' + seasonName + '" to "' + newSeason +'"' )
					wx.CallAfter( self.refresh )
				else:
					Utils.MessageOK( self, 'Season "' + newSeason + '" already exists!', title = 'Season exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
		except Exception as e:
				Utils.logException( e, sys.exc_info() )
	
	def deleteSeason( self, event, row ):
		database = Model.database
		if database is None:
			return
		try:
			with Model.LockDatabase() as db:
				season = self.seasonsGrid.GetCellValue(row, 0)
				del db.seasons[season]
				db.setChanged()
			self.season = None
			self.refreshSeasonsGrid()
			self.refreshEventsGrid()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def selectEvt( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.evt = row
			self.rnd = None
			self.updateSignonSheetName()
			self.updateAllocationPageName()
			self.commit()
			self.refreshEventsGrid()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
			
	def updateSignonSheetName( self ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'signonFileName' in evt:
					self.signonFileName.SetValue(evt['signonFileName'])
					if evt['signonFileName']:
						self.writeSignonButton.Enable()
				else:
					self.signonFileName.SetValue('')
					self.writeSignonButton.Disable()
				self.signonFileName.Enable()
				self.signonBrowseButton.Enable()
				self.signonFileName.ShowPosition(self.signonFileName.GetLastPosition())
				return
		self.signonFileName.SetValue('')
		self.writeSignonButton.Disable()
		self.signonFileName.Disable()
		self.signonBrowseButton.Disable()
		
	def updateAllocationPageName( self ):
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None:
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				if 'allocationFileName' in evt:
					self.allocationFileName.SetValue(evt['allocationFileName'])
					if evt['allocationFileName']:
						self.writeAllocationButton.Enable()
				else:
					self.allocationFileName.SetValue('')
					self.writeAllocationButton.Disable()
				self.allocationFileName.Enable()
				self.allocationBrowseButton.Enable()
				self.allocationFileName.ShowPosition(self.allocationFileName.GetLastPosition())
				return
		self.allocationFileName.SetValue('')
		self.writeAllocationButton.Disable()
		self.allocationFileName.Disable()
		self.allocationBrowseButton.Disable()
			
	def onEventsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Events')
		add = menu.Append( wx.ID_ANY, 'Add new event', 'Add a new event...' )
		self.Bind( wx.EVT_MENU, self.addEvent, add )
		if row >= 1 or (row == 0 and len(self.eventsGrid.GetCellValue(row, 0).strip()) > 0):
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[row]
			rename = menu.Append( wx.ID_ANY, 'Rename ' + evtName, 'Rename this event...' )
			self.Bind( wx.EVT_MENU, lambda event: self.renameEvent(event, row), rename )
			changeEventDate = menu.Append( wx.ID_ANY, 'Change ' + evtName + '\'s date', 'Change event date...' )
			self.Bind( wx.EVT_MENU, lambda event: self.changeEventDate(event, row), changeEventDate )
			duplicateEvent = menu.Append( wx.ID_ANY, 'Duplicate ' + evtName, 'Duplicate event' )
			self.Bind( wx.EVT_MENU, lambda event: self.duplicateEvent(event, row), duplicateEvent )
			delete = menu.Append( wx.ID_ANY, 'Delete ' + evtName + ' from list', 'Delete this event...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteEvent(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addEvent( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		try:
			with wx.TextEntryDialog(self, 'Enter the name for the new event:', caption='Add event', value='New Event', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newEvent = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						if 'events' not in season:
							season['events'] = {}
						if newEvent not in season['events']:
							#init date field with today's date
							#season['events'][newEvent] = {"date":int(datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time()).timestamp())}
							season['events'][newEvent] = {}
							db.setChanged()
							self.evt = len(season['events']) - 1
							self.editEntryButton.Enable()
							wx.CallAfter( self.commit )
						else:
							Utils.MessageOK( self, 'Event ' + newEvent +' already exists!', title = 'Event exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
				self.refreshEventsGrid()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def renameEvent( self, event, row ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		try:
			oldEvent = self.eventsGrid.GetCellValue(row, 0)
			with wx.TextEntryDialog(self, 'Enter the new name for this event:', caption='Rename event', value=oldEvent, style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newEvent = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						if newEvent not in season['events']:
							season['events'] = {newEvent if k == oldEvent else k:v for k,v in season['events'].items()}
							db.setChanged()
							self.evt = len(season['events']) - 1
							self.editEntryButton.Enable()
							wx.CallAfter( self.commit )
						else:
							Utils.MessageOK( self, 'Event "' + newEvent +'" already exists!', title = 'Event exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
				self.refreshEventsGrid()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def changeEventDate( self, event, row ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		try:
			oldDate = self.eventsGrid.GetCellValue(row, 1)
			with wx.TextEntryDialog(self, 'Enter the new date for "' + self.eventsGrid.GetCellValue(row, 0) + '"\nin the format YYYY-MM-DD:', caption='Change event date', value=oldDate, style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newDate = dlg.GetValue()
					with Model.LockDatabase() as db:
						try:
							ts = int(datetime.datetime.strptime(newDate, '%Y-%m-%d').timestamp())
							seasonName = db.getSeasonsList()[self.season]
							season = db.seasons[seasonName]
							evtName = list(season['events'])[row]
							evt = season['events'][evtName]
							evt['date'] = ts
							db.setChanged()
							wx.CallAfter( self.commit )
						except ValueError:
							Utils.MessageOK( self, '"' + newDate + '" is not a valid date!', title = 'Invalid date', iconMask = wx.ICON_ERROR, pos = wx.DefaultPosition )
				self.refreshEventsGrid()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		
	def duplicateEvent( self, event, row ):
		database = Model.database
		if database is None:
			return
		if self.season is not None and self.evt is not None:
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[row]
					newEvent = 'Copy of ' + evtName
					if newEvent not in season['events']:
						evt = season['events'][evtName]
						season['events'][newEvent] = copy.deepcopy(evt)
						db.setChanged()
						Utils.writeLog( 'duplicateEvent: Copied event in season "' + seasonName + '" from event "' + evtName + '" to "' + newEvent + '"' )
						wx.CallAfter( self.refresh )
					else:
						Utils.MessageOK( self, 'Event "' + newEvent + '" already exists!', title = 'Event exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
			except Exception as e:
					Utils.logException( e, sys.exc_info() )
					
	def deleteEvent( self, event, row ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		seasonName = database.getSeasonsList()[self.season]
		season = database.seasons[seasonName]
		evtName = list(season['events'])[row]
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete ' + evtName + '?\nThis will also delete ALL associated rounds and races!', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete event: ' + evtName)
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					event = self.eventsGrid.GetCellValue(row, 0)
					del season['events'][event]
					db.setChanged()
					self.evt = None
					self.rnd = None
					self.commit()
				self.refreshEventsGrid()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
			
	def selectRnd( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		if row >= 0:
			self.rnd = row
			self.commit()
			self.refreshRoundsGrid()
			self.refreshCurrentSelection()
			self.Layout()
		
	def onRoundsRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Rounds')
		add = menu.Append( wx.ID_ANY, 'Add new round', 'Add a new round...' )
		self.Bind( wx.EVT_MENU, self.addRound, add )
		if row >= 1 or (row == 0 and len(self.eventsGrid.GetCellValue(row, 0).strip()) > 0):
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			evtName = list(season['events'])[self.evt]
			evt = season['events'][evtName]
			rndName = list(evt['rounds'])[row]
			rename = menu.Append( wx.ID_ANY, 'Rename ' + rndName, 'Rename this round...' )
			self.Bind( wx.EVT_MENU, lambda event: self.renameRound(event, row), rename )
			delete = menu.Append( wx.ID_ANY, 'Delete ' + rndName + ' from list', 'Delete this round...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteRound(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.writeLog( 'Results:doRightClick: {}'.format(e) )
			
	def addRound( self, event ):
		database = Model.database
		if database is None:
			return
		if self.season is None or self.evt is None:
			return
		try:
			with wx.TextEntryDialog(self, 'Enter the name for the new round:', caption='Add round', value='New Round', style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newRnd = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						if 'rounds' not in evt:  # create rounds dict if it does not exist
							evt['rounds'] = {}
						#print('season: ' + seasonName + ', event: ' + evtName + ', rounds: ' + str(evt['rounds']))
						if newRnd not in evt['rounds']:
							evt['rounds'][newRnd] = {}
							db.setChanged()
							self.rnd = len(evt['rounds'])-1
							self.commit()
						else:
							Utils.MessageOK( self, 'Round ' + newRound +' already exists!', title = 'Round exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
					self.refreshRoundsGrid()
					self.refreshCurrentSelection()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def renameRound( self, event, row ):
		database = Model.database
		if database is None:
			return
		if self.season is None or self.evt is None:
			return
		try:
			oldRnd = self.roundsGrid.GetCellValue(row, 0)
			with wx.TextEntryDialog(self, 'Enter the new name for this round:', caption='Rename round', value=oldRnd, style=wx.OK|wx.CANCEL) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					newRnd = dlg.GetValue()
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						if newRnd not in evt['rounds']:
							evt['rounds'] = {newRnd if k == oldRnd else k:v for k,v in evt['rounds'].items()}
							db.setChanged()
							self.rnd = len(evt['rounds'])-1
							self.commit()
						else:
							Utils.MessageOK( self, 'Round ' + newRound +' already exists!', title = 'Round exists', iconMask = wx.ICON_INFORMATION, pos = wx.DefaultPosition )
					self.refreshRoundsGrid()
					self.refreshCurrentSelection()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
						
	def deleteRound( self, event, row ):
		database = Model.database
		if database is None:
			return
		if self.season is None or self.evt is None:
			return
		seasonName = database.getSeasonsList()[self.season]
		season = database.seasons[seasonName]
		evtName = list(season['events'])[self.evt]
		evt = season['events'][evtName]
		rndName = list(evt['rounds'])[row]
		if Utils.MessageOKCancel( self, 'Are you sure you want to delete ' + rndName + '?\nThis will also delete ALL associated races!', title = 'Confirm delete?', iconMask = wx.ICON_QUESTION):
			Utils.writeLog('Delete event: ' + evtName)
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					evtName = list(season['events'])[self.evt]
					evt = season['events'][evtName]
					rnd = self.roundsGrid.GetCellValue(row, 0)
					del evt['rounds'][rnd]
					db.setChanged()
					self.rnd = None
					self.commit()
				self.refreshRoundsGrid()
				self.refreshCurrentSelection()
				self.Layout()
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				
	def onBrowseSignon( self, event ):
		database = Model.database
		if database is None:
			return
		defaultFileName = self.signonFileName.GetValue()
		if defaultFileName.endswith('.xlsx'):
			dirName = os.path.dirname( defaultFileName )
			fileName = os.path.basename( defaultFileName )
		else:
			dirName = defaultFileName
			if self.season is not None and self.evt is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				try:
					dt = '{:%Y-%m-%d_}'.format(datetime.datetime.fromtimestamp(evt['date']))
				except:
					dt = ''
				fileName = 'racers_' + dt + list(season['events'])[self.evt].lower().replace(' ', '_') + '.xlsx'
			else:
				fileName = ''
			if not dirName:
				dirName = Utils.getDocumentsDir()
		with wx.FileDialog( self, message=_("Choose Sigon Sheet File"),
							defaultDir=dirName, 
							defaultFile=fileName,
							wildcard=_("CrossMgr sign-on sheet (*.xlsx)|*.xlsx"),
							style=wx.FD_SAVE ) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				fn = os.path.relpath(os.path.abspath(dlg.GetPath()), start=os.path.dirname(os.path.abspath(database.fileName)) ) #sign-on sheet path is relative to database file
				self.signonFileName.SetValue( fn )
				if self.season is not None and self.evt is not None:
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						evt['signonFileName'] = fn
						database.setChanged()
						wx.CallAfter( self.refresh )
		self.signonFileName.ShowPosition(self.signonFileName.GetLastPosition())
			
	def onEditSignon( self, event ):
		database = Model.database
		if database is None:
			return
		fn = self.signonFileName.GetValue()
		if fn.endswith('.xlsx'):
			if not os.path.isdir(os.path.dirname(fn)):
				Utils.MessageOK(self, 'Sign-on sheet destination directory\n"' + os.path.abspath(os.path.dirname(fn)) + '"\ndoes not exist!\nCheck the path has been entered correctly.', 'Invalid path', iconMask=wx.ICON_ERROR )
				wx.CallAfter( self.updateSignonSheetName )
				return
			if os.path.isabs(fn):
				fn = os.path.relpath(fn, start=os.path.dirname(os.path.abspath(database.fileName)) ) #sign-on sheet path is relative to database file
				Utils.writeLog('Absolute sign-on sheet filename converted to: "' + fn + '" (relative to database file "' + database.fileName + '")')
				self.signonFileName.ChangeValue(fn)
		else:
			Utils.MessageOK( self, 'Sign-on sheet should be an .xlsx file!', title = 'Incorrect filetype', iconMask = wx.ICON_ERROR )
			return
		if self.season is not None and self.evt is not None:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[self.season]
				season = db.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				evt['signonFileName'] = fn
				database.setChanged()
		self.signonFileName.ShowPosition(self.signonFileName.GetLastPosition())
		
	def onBrowseAllocation( self, event ):
		database = Model.database
		if database is None:
			return
		defaultFileName = self.allocationFileName.GetValue()
		if defaultFileName.endswith('.html'):
			dirName = os.path.dirname( defaultFileName )
			fileName = os.path.basename( defaultFileName )
		else:
			dirName = defaultFileName
			if self.season is not None and self.evt is not None:
				seasonName = database.getSeasonsList()[self.season]
				season = database.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				try:
					dt = '{:%Y-%m-%d_}'.format(datetime.datetime.fromtimestamp(evt['date']))
				except:
					dt = ''
				fileName = 'race_allocations_' + dt + list(season['events'])[self.evt].lower().replace(' ', '_') + '.html'
			else:
				fileName = ''
			if not dirName:
				dirName = Utils.getDocumentsDir()
		with wx.FileDialog( self, message=_("Choose Allocation Page File"),
							defaultDir=dirName, 
							defaultFile=fileName,
							wildcard=_("HTML page (*.html)|*.html"),
							style=wx.FD_SAVE ) as dlg:
			if dlg.ShowModal() == wx.ID_OK:
				fn = os.path.relpath(os.path.abspath(dlg.GetPath()), start=os.path.dirname(os.path.abspath(database.fileName)) ) #allocation page path is relative to database file
				self.allocationFileName.SetValue( fn )
				if self.season is not None and self.evt is not None:
					with Model.LockDatabase() as db:
						seasonName = db.getSeasonsList()[self.season]
						season = db.seasons[seasonName]
						evtName = list(season['events'])[self.evt]
						evt = season['events'][evtName]
						evt['allocationFileName'] = fn
						database.setChanged()
						wx.CallAfter( self.refresh )
		self.allocationFileName.ShowPosition(self.allocationFileName.GetLastPosition())
		
	def onEditAllocation( self, event ):
		database = Model.database
		if database is None:
			return
		fn = self.allocationFileName.GetValue()
		if fn.endswith('.xlsx'):
			if not os.path.isdir(os.path.dirname(fn)):
				Utils.MessageOK(self, 'Allocation page destination directory\n"' + os.path.abspath(os.path.dirname(fn)) + '"\ndoes not exist!\nCheck the path has been entered correctly.', 'Invalid path', iconMask=wx.ICON_ERROR )
				wx.CallAfter( self.updateAllocationPageName )
				return
			if os.path.isabs(fn):
				fn = os.path.relpath(fn, start=os.path.dirname(os.path.abspath(database.fileName)) ) #sign-on sheet path is relative to database file
				Utils.writeLog('Absolute allocation page filename converted to: "' + fn + '" (relative to database file "' + database.fileName + '")')
				self.allocationFileName.ChangeValue(fn)
		else:
			Utils.MessageOK( self, 'Allocation page should be an .html file!', title = 'Incorrect filetype', iconMask = wx.ICON_ERROR )
			return
		if self.season is not None and self.evt is not None:
			with Model.LockDatabase() as db:
				seasonName = db.getSeasonsList()[self.season]
				season = db.seasons[seasonName]
				evtName = list(season['events'])[self.evt]
				evt = season['events'][evtName]
				evt['allocationFileName'] = fn
				database.setChanged()
		self.allocationFileName.ShowPosition(self.allocationFileName.GetLastPosition())
		
	def onEditEntryButton( self, event ):
		Utils.getMainWin().showEventEntryPage()
		
	def onEditRacesButton( self, event ):
		Utils.getMainWin().showRaceAllocationPage()
			
	def refreshSeasonsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.seasonsGrid )
		seasons = database.getSeasonsList()
		for seasonName in seasons:
			self.seasonsGrid.AppendRows(1)
			row = self.seasonsGrid.GetNumberRows() -1
			col = 0
			self.seasonsGrid.SetCellValue(row, col, str(seasonName))
			self.seasonsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curSeason else wx.WHITE)
			col += 1
			self.seasonsGrid.SetCellValue(row, col, str(len(database.seasons[seasonName]['events'])) if 'events' in database.seasons[seasonName] else '')
			self.seasonsGrid.SetCellAlignment(row, col, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
			self.seasonsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curSeason else wx.WHITE)
		self.seasonsGrid.AutoSize()
	
	def refreshEventsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.eventsGrid )
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			self.eventsGrid.SetColLabelValue(0, seasonName + '\'s events')
			#print('season: ' + seasonName + ', events: ' + str(season))
			if 'events' in season:
				for eventName in season['events']:
					self.eventsGrid.AppendRows(1)
					row = self.eventsGrid.GetNumberRows() -1
					col = 0
					self.eventsGrid.SetCellValue(row, col, eventName )
					self.eventsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curEvt else wx.WHITE)
					col += 1
					try:
						dt = '{:%Y-%m-%d}'.format(datetime.datetime.fromtimestamp(season['events'][eventName]['date']))
					except:
						dt = ''
					self.eventsGrid.SetCellValue(row, col, str(dt) if 'date' in season['events'][eventName] else '' )
					self.eventsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curEvt else wx.WHITE)
					col += 1
					self.eventsGrid.SetCellValue(row, col, str(len(season['events'][eventName]['rounds'])) if 'rounds' in season['events'][eventName] else '')
					self.eventsGrid.SetCellAlignment(row, col, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
					self.eventsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curEvt else wx.WHITE)
		else:
			self.eventsGrid.SetColLabelValue(0, 'Season\'s events')
		self.eventsGrid.AutoSize()
			
	def refreshRoundsGrid( self ):
		database = Model.database
		if database is None:
			return
		self.clearGrid( self.roundsGrid )
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if self.evt is not None and 'events' in season:
				evtName = list(season['events'])[self.evt]
				self.roundsGrid.SetColLabelValue(0, evtName + '\'s rounds')
				evt = season['events'][evtName]
				if 'rounds' in evt:
					#print('season: ' + seasonName + ', event: ' + evtName + ', rounds: ' + str(evt['rounds']))
					for rndName in evt['rounds']:
						self.roundsGrid.AppendRows(1)
						row = self.roundsGrid.GetNumberRows() -1
						col = 0
						self.roundsGrid.SetCellValue(row, col, rndName)
						self.roundsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curRnd else wx.WHITE)
						col += 1
						self.roundsGrid.SetCellValue(row, col, str(len(evt['rounds'][rndName]['races'])) if 'rounds' in evt and 'races' in evt['rounds'][rndName] else '')
						self.roundsGrid.SetCellAlignment(row, col, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
						self.roundsGrid.SetCellBackgroundColour(row, col, self.OrangeColour if row == database.curRnd else wx.WHITE)
			else:
				self.roundsGrid.SetColLabelValue(0, 'Event\'s rounds')
		self.roundsGrid.AutoSize()

	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )
			
	def refreshCurrentSelection( self ):
		database = Model.database
		selection = []
		title = None
		if database is None:
			title = 'No Database'
		else:
			if self.season is not None:
				seasonName = database.getSeasonsList()[self.season]
				selection.append( seasonName )
				season = database.seasons[seasonName]
				if self.evt is not None and 'events' in season:
					evtName = list(season['events'])[self.evt]
					selection.append( evtName )
					evt = season['events'][evtName]
					self.editEntryButton.Enable()
					if self.rnd is not None and 'rounds' in evt:
						rndName = list(evt['rounds'])[self.rnd]
						selection.append( rndName )
						self.editRacesButton.Enable()
					else:
						self.editRacesButton.Disable()
				else:
					self.editEntryButton.Disable()
					self.editRacesButton.Disable()
				title = ', '.join(n for n in selection)
			database.selection = selection
		self.currentSelection.SetLabel( title if title else 'No selection')
		Utils.getMainWin().SetTitle( ('* ' if database.hasChanged() else '' ) + ' — '.join( n for n in [title if title else 'No selection', Version.AppVerName] if n ) )
		
		
	def commit( self, event=None ):
		Utils.writeLog('Events commit: ' + str(event))
		with Model.LockDatabase() as db:
			db.curSeason = self.season
			db.curEvt = self.evt
			db.curRnd = self.rnd
			db.setChanged()
	
	def refresh( self ):
		Utils.writeLog('Events refresh')
		database = Model.database
		if database is not None:
			self.season = database.curSeason
			self.evt = database.curEvt
			self.rnd = database.curRnd
		self.refreshSeasonsGrid()
		self.refreshEventsGrid()
		self.refreshRoundsGrid()
		self.refreshCurrentSelection()
		self.updateSignonSheetName()
		self.updateAllocationPageName()
		self.Layout()
