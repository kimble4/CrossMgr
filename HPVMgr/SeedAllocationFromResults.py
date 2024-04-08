import os
import sys
import numpy
import wx
import wx.adv as adv
import wx.lib.filebrowsebutton as filebrowse
import traceback
import Utils
from Utils import logException
import HelpSearch
from Excel import GetExcelReader

class IntroPage(adv.WizardPageSimple):
	def __init__(self, parent, controller ):
		super().__init__(parent)
		self.controller = controller
		border = 4
		boldFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		boldFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		vbs = wx.BoxSizer( wx.VERTICAL )
		vbs.Add( wx.StaticText(self, label = _("Attempt to seed race allocations for:")),
					flag=wx.ALL, border = border )
		
		self.currentSelection = wx.StaticText( self, label='No round selected' )
		self.currentSelection.SetFont( boldFont )
		vbs.Add( self.currentSelection, flag=wx.ALL, border = border )
		
		self.fileHeading = wx.StaticText(self, label = _("\n\nSelect the Excel file containing the results.  It must contain 'Pos' and 'Bib' columns:") )
		vbs.Add( self.fileHeading, flag=wx.ALL, border = border )
		fileMask = [
			'Excel Worksheets (*.xlsx;*.xlsm;*.xls)|*.xlsx;*.xlsm;*.xls',
		]
		self.fbb = filebrowse.FileBrowseButton( self, -1, size=(800, -1),
												labelText = 'Excel worksheet:',
												fileMode=wx.FD_OPEN,
												fileMask='|'.join(fileMask),
												startDirectory=Utils.getFileDir())
		self.fbb.SetValue('')
		vbs.Add( self.fbb, flag=wx.ALL, border = border )
		
		self.SetSizer( vbs )
		
	def setInfo( self, database ):
		if database is None:
			return
		selection = []
		title = 'No round selected'
		seasonName = database.getSeasonsList()[database.curSeason]
		selection.append( seasonName )
		season = database.seasons[seasonName]
		evtName = list(season['events'])[database.curEvt]
		selection.append( evtName )
		evt = season['events'][evtName]
		rndName = list(evt['rounds'])[database.curRnd]
		selection.append( rndName )
		title = ', '.join(n for n in selection) + '{: (%Y-%m-%d) }'.format(database.getCurEvtDate()) if database.getCurEvtDate() is not None else ''
		self.currentSelection.SetLabel( title )
		
	def getFileName( self ):
		return self.fbb.GetValue()
	
class SheetNamePage(adv.WizardPageSimple):
	def __init__(self, parent):
		super().__init__(parent)
		self.choices = []
		self.expectedSheetName = None
		
		border = 4
		vbs = wx.BoxSizer( wx.VERTICAL )
		vbs.Add( wx.StaticText(self, label = _('Specify the sheet containing the results you want to use:')),
				flag=wx.ALL, border = border )
		self.ch = wx.Choice( self, -1, choices = self.choices )
		vbs.Add( self.ch, flag=wx.ALL, border = border )
		self.SetSizer( vbs )
	
	def setFileName( self, fileName ):
		reader = GetExcelReader( fileName )
		self.choices = reader.sheet_names()
		
		self.ch.Clear()
		self.ch.AppendItems( self.choices )
		self.ch.SetSelection( 0 )
	
	def getSheetName( self ):
		return self.choices[self.ch.GetCurrentSelection()]


class UseResultsPage(adv.WizardPageSimple):
	headerNames = ['Time of Day\n(local)', 'Race\nTime', 'Lat (°)', 'Long (°)', 'Race\n(km)', 'Lap\n(km)', 'Proximity\nto start (m)', 'Bearing\n(°)', 'Import\nlap']
	
	def __init__(self, parent):
		super().__init__(parent)
		border = 4
		vbs = wx.BoxSizer( wx.VERTICAL )
		
		self.headersFound = wx.StaticText(self, label = _('Header row not found!') )
		vbs.Add( self.headersFound, flag=wx.ALL, border = border )
		
		self.posFound = wx.StaticText(self, label = _('\'Pos\' column not found!') )
		vbs.Add( self.posFound, flag=wx.ALL, border = border )
		
		self.bibFound = wx.StaticText(self, label = _('\'Bib\' column not found!') )
		vbs.Add( self.bibFound, flag=wx.ALL, border = border )
		
		vbs.AddStretchSpacer()
		
		self.rankedFound = wx.StaticText(self, label = _('No finishers found!') )
		vbs.Add( self.rankedFound, flag=wx.ALL, border = border )
		
		self.nonFinishersFound = wx.StaticText(self, label = _('') )
		vbs.Add( self.nonFinishersFound, flag=wx.ALL, border = border )
				
		self.dnsFound = wx.StaticText(self, label = _('') )
		vbs.Add( self.dnsFound, flag=wx.ALL, border = border )
		
		vbs.AddStretchSpacer()
		
		self.includeNonfinishers = wx.CheckBox( self, label='Include non-finishers in ranking' )
		self.includeNonfinishers.SetValue( True )
		self.includeNonfinishers.Bind( wx.EVT_CHECKBOX, self.refresh )
		vbs.Add( self.includeNonfinishers, flag=wx.ALL, border = border )
		
		self.SetSizer( vbs )
		
	
	def readSheet( self, fileName, sheetName ):
		reader = GetExcelReader( fileName )
		headerRow = None
		headers = []
		
		
		# Try to find the header columns.
		# Look for the first row with more than 4 columns.
		for r, row in enumerate(reader.iter_list(sheetName)):
			cols = sum( 1 for d in row if d and '{}'.format(d).strip() )
			if cols > 4:
				headerRow = r
				headers = ['{}'.format(h or '').strip() for h in row]
				break

		# If we haven't found a header row yet, assume the first non-empty row is the header.
		if not headers:
			for r, row in enumerate(reader.iter_list(sheetName)):
				cols = sum( 1 for d in row if d and '{}'.format(d).strip() )
				if cols > 0:
					headerRow = r
					headers = ['{}'.format(h or '').strip() for h in row]
					break
		
		# Ignore empty columns on the end.
		while headers and (not headers[-1] or headers[-1].isspace()):
			headers.pop()
			
		if headerRow is not None:
			self.headersFound.SetLabel('Headers found in row ' + str(headerRow) )
			
		posCol, bibCol = None, None
		for i, header in enumerate(headers):
			if header.lower() == 'pos':
				posCol = i
			if header.lower() == 'bib':
				bibCol = i
				
		if bibCol is not None:
			self.bibFound.SetLabel('\'Bib\' found in column ' + str(bibCol) )
		else:
			return
		if posCol is not None:
			self.posFound.SetLabel('\'Pos\' found in column ' + str(posCol) )
		else:
			return
		
		#now get the data
		self.data = []
		for r, row in enumerate(reader.iter_list(sheetName)):
			if r > headerRow:
				self.data.append((row[posCol], row[bibCol]))
		self.refresh()
		
	def refresh( self, event=None ):
		self.ranking = []
		dns = []
		nf = []
		for posBib in self.data:
			try:
				pos = int(posBib[0])
				bib = int(posBib[1])
				self.ranking.append((pos, bib))
			except:
				if posBib[0] == 'DNS' or posBib[0] == 'NP':
					#DNS/NP riders are ignored
					dns.append(posBib[1])
				elif posBib[0] == 'OTL' or posBib[0] == 'PUL':
					#OTL and PUL come before DNF
					if self.includeNonfinishers.IsChecked():
						self.ranking.append((sys.maxsize-2, posBib[1]))
					else:
						nf.append(posBib[1])
				elif posBib[0] == 'DNF':
					#DNF comes before DQ
					if self.includeNonfinishers.IsChecked():
						self.ranking.append((sys.maxsize-1, posBib[1]))
					else:
						nf.append(posBib[1])
				elif posBib[0] == 'DQ':
					if self.includeNonfinishers.IsChecked():
						self.ranking.append((sys.maxsize, posBib[1]))
					else:
						nf.append(posBib[1])
		self.ranking.sort()
		
		if len(dns) > 0:
			outString = ''
			for i, bib in enumerate(dns):
				outString += str(bib) + ','
				if i%10 == 9 and i != len(dns) -1:
					outString += '\n'
			self.dnsFound.SetLabel('Ignored ' + str(len(dns)) + ' DNS/NP riders:\n' + outString[:-1])
		else:
			self.dnsFound.SetLabel('')
		
		if len(nf) > 0:
			outString = ''
			for i, bib in enumerate(nf):
				outString += str(bib) + ','
				if i%10 == 9 and i != len(nf) -1:
					outString += '\n'
			self.nonFinishersFound.SetLabel('Ignored ' + str(len(nf)) + ' Non-finishers:\n' + outString[:-1])
		else:
			self.nonFinishersFound.SetLabel('')
		
		outString = ''
		for i, posBib in enumerate(self.ranking):
			outString += str(posBib[1]) + ','
			if i%10 == 9 and i != len(self.ranking) -1:
				outString += '\n'
		self.rankedFound.SetLabel('Ranked ' + str(len(self.ranking)) + ' riders:\n' + outString[:-1])
		
		self.Layout()
	
	def getRanking( self ):
		return [n[1] for n in self.ranking]
		
class SummaryPage(adv.WizardPageSimple):
	def __init__(self, parent):
		super().__init__(parent)
		self.ranking = []
		self.nrRaces = 0
		border = 4
		boldFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		boldFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		vbs = wx.BoxSizer( wx.VERTICAL )
		
		vbs.Add( wx.StaticText( self, label='This will overwrite the race allocation for:') )
		
		self.currentSelection = wx.StaticText( self, label='No round selected' )
		self.currentSelection.SetFont( boldFont )
		vbs.Add( self.currentSelection, flag=wx.ALL, border = border )
		
		vbs.AddStretchSpacer()
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		hs.Add( wx.StaticText( self, label='Races in this round:' ), flag=wx.ALIGN_CENTER_VERTICAL )
		
		self.numberOfRaces = wx.Choice(self, choices=[str(x) for x in range(0,6)], name='Races in this round')
		self.numberOfRaces.Bind( wx.EVT_CHOICE, self.onChangeNumberOfRaces )
		hs.Add( self.numberOfRaces, flag=wx.ALIGN_CENTER_VERTICAL )
		vbs.Add( hs, flag=wx.EXPAND )
		
		self.numberOfRiders = wx.StaticText( self, label='' )
		vbs.Add( self.numberOfRiders )
		
		vbs.AddStretchSpacer()
		
		vbs.Add( wx.StaticText( self, label='Racers in the spreadsheet who are not entered in the current race will be ignored.') )
		
		self.SetSizer(vbs)
		
	def onChangeNumberOfRaces( self, event ):
		self.nrRaces = self.numberOfRaces.GetCurrentSelection()
		self.refresh()
		
	def getNumberOfRaces( self ):
		return self.nrRaces
		
	def setInfo( self, database ):
		if database is None:
			return
		selection = []
		title = 'No round selected'
		seasonName = database.getSeasonsList()[database.curSeason]
		selection.append( seasonName )
		season = database.seasons[seasonName]
		evtName = list(season['events'])[database.curEvt]
		selection.append( evtName )
		evt = season['events'][evtName]
		rndName = list(evt['rounds'])[database.curRnd]
		selection.append( rndName )
		title = ', '.join(n for n in selection) + '{: (%Y-%m-%d) }'.format(database.getCurEvtDate()) if database.getCurEvtDate() is not None else ''
		self.currentSelection.SetLabel( title )
		self.refresh()
		
	def setRanking( self, ranking ):
		self.ranking = ranking
		
	def refresh( self, event=None):
		if self.nrRaces > 0:
			self.numberOfRiders.SetLabel('Of approximately ' + str(int(len(self.ranking)/self.nrRaces)) + ' racers')
		else:
			self.numberOfRiders.SetLabel('')
		
		
class GetAllocation:
	def __init__( self, parent, database):
		self.database = database

		img_filename = os.path.join( Utils.getImageFolder(), 'excel_2003_2_01.png' )
		bitmap = wx.Bitmap(img_filename) if img_filename and os.path.exists(img_filename) else wx.NullBitmap
		
		self.parent = parent
		self.wizard = adv.Wizard()
		self.wizard.SetExtraStyle( adv.WIZARD_EX_HELPBUTTON )
		self.wizard.Create( parent, title = _('Seed race allocation from results sheet'), bitmap = bitmap )
		
		self.introPage		= IntroPage( self.wizard, self )
		self.sheetNamePage	= SheetNamePage( self.wizard )
		self.useResultsPage	= UseResultsPage( self.wizard )
		self.summaryPage	= SummaryPage( self.wizard )
		
		self.wizard.Bind( adv.EVT_WIZARD_PAGE_CHANGING, self.onPageChanging )
		self.wizard.Bind( adv.EVT_WIZARD_CANCEL, self.onCancel )
		self.wizard.Bind( adv.EVT_WIZARD_HELP,
			lambda evt: HelpSearch.showHelp('Menu-Tools.html#seed-race-allocation-from-results-sheet') )
		
		adv.WizardPageSimple.Chain( self.introPage, self.sheetNamePage )
		adv.WizardPageSimple.Chain( self.sheetNamePage, self.useResultsPage )
		adv.WizardPageSimple.Chain( self.useResultsPage, self.summaryPage )
		
		self.wizard.SetPageSize( wx.Size(1024,800) )
		self.wizard.GetPageAreaSizer().Add( self.introPage )
		
		self.introPage.setInfo( self.database )

	def show( self ):
		if self.wizard.RunWizard(self.introPage):
			return
	
	def onCancel( self, evt ):
		page = evt.GetPage()
		if page == self.introPage:
			pass
		elif page == self.summaryPage:
			pass

		
	def onPageChanging( self, evt ):
		isForward = evt.GetDirection()
		if not isForward:
			return
		page = evt.GetPage()
		
		if page == self.introPage:
			self.fileName = self.introPage.getFileName()
			try:
				open(self.fileName).close()
				self.sheetNamePage.setFileName(self.fileName)
			except (IOError, FileNotFoundError):
				if self.fileName == '':
					message = _('Please specify an Excel file.')
				else:
					message = '{}\n\n   "{}".\n\n{}'.format(
						_('Cannot open file'),
						self.fileName,
						_('Please check the file name and/or its read permissions.'),
					)
				Utils.MessageOK( self.wizard, message, title=_('File Open Error'), iconMask=wx.ICON_ERROR)
				evt.Veto()
		elif page == self.sheetNamePage:
			self.sheetName = self.sheetNamePage.getSheetName()
			self.useResultsPage.readSheet(self.fileName, self.sheetName)
		elif page == self.useResultsPage:
			self.summaryPage.setInfo( self.database )
			self.summaryPage.setRanking(self.useResultsPage.getRanking())
		elif page == self.summaryPage:
			#actually modify the database
			if self.database is None:
				return
			nrRaces = self.summaryPage.getNumberOfRaces()
			ranking = self.useResultsPage.getRanking()
			ranking.reverse() #start with the slower riders
			allocations = numpy.array_split(ranking, nrRaces) if nrRaces > 0 else [] #handle 0 races case gracefully by clearing the allocations
			if self.database.curSeason is not None and self.database.curEvt is not None and self.database.curRnd is not None:
				try:
					seasonName = self.database.getSeasonsList()[self.database.curSeason]
					season = self.database.seasons[seasonName]
					evtName = list(season['events'])[self.database.curEvt]
					evt = season['events'][evtName]
					rndName = list(evt['rounds'])[self.database.curRnd]
					rnd = evt['rounds'][rndName]
					#this overwrites the existing allocation!
					rnd['races'] = []
					for i in range(nrRaces):
						rnd['races'].append([])
					for i, racers in enumerate(allocations):
						race = rnd['races'][i]
						for bib in sorted(racers.tolist()):
							raceEntryDict = {'bib': bib}
							race.append(raceEntryDict)
					self.database.setChanged()
					Utils.writeLog('Seeded race allocation from ' + self.fileName)
				except Exception as e:
					Utils.logException( e, sys.exc_info() )
		
	def onPageChanged( self, evt ):
		isForward = evt.GetDirection()

