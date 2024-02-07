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


class Categories( wx.Panel ):
	
	maxCategories = 18
	
	def __init__( self, parent, id = wx.ID_ANY ):
		super().__init__(parent, id)
		
		bigFont =  wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
		bigFont.SetFractionalPointSize( Utils.getMainWin().defaultFontSize + 4 )
		#bigFont.SetWeight( wx.FONTWEIGHT_BOLD )
		
		self.season = None

		self.colnames = ['Count', 'Category', 'Abbreviation']
		
		self.riderBibNames = []
		
		vs = wx.BoxSizer(wx.VERTICAL)
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		selectSeasonLabel = wx.StaticText( self, label='Select season:' )
		selectSeasonLabel.SetFont( bigFont )
		hs.Add(selectSeasonLabel, flag=wx.ALIGN_CENTER_VERTICAL )
		self.seasonSelection = wx.Choice( self, choices=[] )
		self.seasonSelection.SetFont( bigFont )
		self.seasonSelection.Bind( wx.EVT_CHOICE, self.onSelectSeason )
		hs.Add( self.seasonSelection, flag=wx.ALIGN_CENTER_VERTICAL)
		hs.AddStretchSpacer()
		self.copyCategoriesButton = wx.Button( self, label='Copy categories')
		self.copyCategoriesButton.SetToolTip( wx.ToolTip('Copy the categories list from another season'))
		self.Bind( wx.EVT_BUTTON, self.copyCategories, self.copyCategoriesButton )
		hs.Add( self.copyCategoriesButton )
		self.newCategoryButton = wx.Button( self, label='Add New')
		self.newCategoryButton.SetToolTip( wx.ToolTip('Add a new category'))
		self.Bind( wx.EVT_BUTTON, self.addCategory, self.newCategoryButton )
		hs.Add( self.newCategoryButton )
		vs.Add( hs, flag=wx.EXPAND)
		
		self.categoriesGrid = wx.grid.Grid( self )
		self.categoriesGrid.CreateGrid(0, len(self.colnames) )
		for i, name in enumerate(self.colnames):
			self.categoriesGrid.SetColLabelValue(i, name)
		self.categoriesGrid.HideRowLabels()
		self.categoriesGrid.SetRowLabelSize( 0 )
		self.categoriesGrid.SetMargins( 0, 0 )
		self.categoriesGrid.AutoSizeColumns( True )
		self.categoriesGrid.DisableDragColSize()
		self.categoriesGrid.DisableDragRowSize()
		self.categoriesGrid.EnableEditing(True)
		self.categoriesGrid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
		self.categoriesGrid.Bind( wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.onCategoriesRightClick )
		self.categoriesGrid.Bind( wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.onCategoriesRightClick )
		self.categoriesGrid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.onCategoriesEdited )
		vs.Add( self.categoriesGrid, flag=wx.EXPAND )
		
		vs.AddStretchSpacer()
		
		hs = wx.BoxSizer( wx.HORIZONTAL )
		
		#commit button
		self.commitButton = wx.Button( self, label='Commit')
		self.commitButton.SetToolTip( wx.ToolTip('Saves changes'))
		self.Bind( wx.EVT_BUTTON, self.commit, self.commitButton )
		hs.Add( self.commitButton, flag=wx.ALIGN_LEFT )
		
		#edited warning
		self.editedWarning = wx.StaticText( self, label='' )
		hs.Add( self.editedWarning, flag=wx.ALIGN_LEFT )
		
		vs.Add( hs, flag=wx.EXPAND)
		
		self.SetDoubleBuffered( True )
		self.SetSizer(vs)
		vs.SetSizeHints(self)
		
	def onSelectSeason( self, event ):
		self.season = self.seasonSelection.GetSelection()
		self.refreshCategoriesList()
		self.Layout()
		
	def onCategoriesRightClick( self, event ):
		database = Model.database
		if database is None:
			return
		row = event.GetRow()
		menu = wx.Menu()
		menu.SetTitle('Categories')
		add = menu.Append( wx.ID_ANY, 'Add new category', 'Add a new category...' )
		self.Bind( wx.EVT_MENU, self.addCategory, add )
		if row >= 1 or (row == 0 and len(self.categoriesGrid.GetCellValue(row, 1).strip()) > 0):
			delete = menu.Append( wx.ID_ANY, 'Delete ' + self.categoriesGrid.GetCellValue(row, 1) + ' from list', 'Delete this season...' )
			self.Bind( wx.EVT_MENU, lambda event: self.deleteCategory(event, row), delete )
		try:
			self.PopupMenu( menu )
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
			
	def onCategoriesEdited( self, event=None ):
		self.editedWarning.SetLabel('Edited!')
		
	def copyCategories( self, event ):
		database = Model.database
		if database is None:
			return
		try:
			with wx.SingleChoiceDialog( self, 'Select the season to copy categories from:', 'Copy categories', database.getSeasonsList()) as dlg:
				if dlg.ShowModal() == wx.ID_OK:
					source = dlg.GetStringSelection()
					season = database.seasons[source]
					if 'categories' in season:
						if season['categories']:
							for category in season['categories']:
								self.categoriesGrid.AppendRows(1)
								row = self.categoriesGrid.GetNumberRows() -1
								self.categoriesGrid.SetCellValue(row, 0, str(row+1))
								self.categoriesGrid.SetCellAlignment(row, 0, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
								self.categoriesGrid.SetCellValue(row, 1, category[0])
								self.categoriesGrid.SetCellValue(row, 2, category[1])
								self.categoriesGrid.SetCellAlignment(row, 2, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
					self.categoriesGrid.AutoSize()
					self.onCategoriesEdited()
					self.Layout()
		except Exception as e:
			Utils.logException( e, sys.exc_info() )
		
	def addCategory( self, event ):
		self.categoriesGrid.AppendRows(1)
		row = self.categoriesGrid.GetNumberRows() -1
		if row >= Categories.maxCategories:
			Utils.MessageOK( self, 'We do not support more than ' + str(Categories.maxCategories) + ' categories!', 'Too many categories' )
			self.categoriesGrid.DeleteRows(row, 1)
			return
		self.categoriesGrid.SetCellValue(row, 0, str(row+1))
		self.categoriesGrid.SetCellAlignment(row, 0, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
		self.categoriesGrid.SetCellValue(row, 1, 'New Category')
		self.categoriesGrid.SetCellValue(row, 2, 'NC')
		self.categoriesGrid.SetCellAlignment(row, 2, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
		self.categoriesGrid.AutoSize()
		self.editedWarning.SetLabel('Edited!')
		self.Layout()
			
	def deleteCategory( self, event, row ):
		self.categoriesGrid.DeleteRows(row, 1)
		self.categoriesGrid.AutoSize()
		self.editedWarning.SetLabel('Edited!')
		self.Layout()
		
	def refreshCategoriesList( self ):
		self.clearGrid( self.categoriesGrid )
		database = Model.database
		if database is None:
			return
		if self.season is not None:
			seasonName = database.getSeasonsList()[self.season]
			season = database.seasons[seasonName]
			if 'categories' in season:
				if season['categories']:
					for i, category in enumerate(season['categories']):
						self.categoriesGrid.AppendRows(1)
						row = self.categoriesGrid.GetNumberRows() -1
						self.categoriesGrid.SetCellValue(row, 0, str(i+1))
						self.categoriesGrid.SetCellAlignment(row, 0, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
						self.categoriesGrid.SetCellValue(row, 1, category[0])
						self.categoriesGrid.SetCellValue(row, 2, category[1])
						self.categoriesGrid.SetCellAlignment(row, 2, wx.ALIGN_CENTRE,  wx.ALIGN_CENTRE)
		self.categoriesGrid.AutoSize()
		self.editedWarning.SetLabel('')
		
	def clearGrid( self, grid ):
		rows = grid.GetNumberRows()
		#print('clearGrid deleting rows: ' + str(rows))
		if rows:
			grid.DeleteRows( 0, rows )
	
	def commit( self, event=None ):
		Utils.writeLog('Categories commit: ' + str(event))
		if event: #called by button
			database = Model.database
			if database is None:
				return
			try:
				with Model.LockDatabase() as db:
					seasonName = db.getSeasonsList()[self.season]
					season = db.seasons[seasonName]
					if season['categories'] is None:
						season['categories'] = []
					season['categories'].clear()
					for row in range(self.categoriesGrid.GetNumberRows()):
						season['categories'].append((self.categoriesGrid.GetCellValue(row, 1), (self.categoriesGrid.GetCellValue(row, 2))))
					db.setChanged()
					wx.CallAfter( self.refresh )
			except Exception as e:
				Utils.logException( e, sys.exc_info() )
				wx.CallAfter( self.refresh )
	
	def refresh( self ):
		Utils.writeLog('Categories refresh')
		database = Model.database
		if database is None:
			return
		self.season = database.curSeason
		self.seasonSelection.Clear()
		self.seasonSelection.AppendItems( database.getSeasonsList() )
		self.seasonSelection.SetSelection(self.season if self.season is not None else wx.NOT_FOUND)
		self.refreshCategoriesList()
		self.Layout()
