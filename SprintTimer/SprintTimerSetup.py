from distutils.core import setup
import os
import sys
import glob
import shutil
import zipfile
import datetime
import platform
import subprocess

if os.path.exists('build'):
	shutil.rmtree( 'build' )

gds = [
	r"c:\GoogleDrive\Downloads\Windows",
	r"C:\Users\edwar\Google Drive\Downloads\Windows",
	r"C:\Users\Edward Sitarski\Google Drive\Downloads\Windows",
]
for googleDrive in gds:
	if os.path.exists(googleDrive):
		break
googleDrive = os.path.join( googleDrive, 'CrossMgrVideo' )

# Compile the help files
from helptxt.compile import CompileHelp
CompileHelp( 'helptxt' )

# Copy all dependent files into this folder.
copyFiles = [
    "LapStats.py"
    "InSortedIntervalList.py"
    "minimal_intervals.py"
    "rsonlite.py"
    "Checklist.py"
    "GpxParse.py"
    "SetRangeMerge.py"
    "GeoAnimation.py"
    "Animation.py"
    "GanttChart.py"
    "Excel.py"
    "arial10.py"
    "GetResults.py"
    "FitSheetWrapper.py"
    "ReadSignOnSheet.py"
    "HelpIndex.py"
    "HelpSearch.py"
    "ModuleUnpickler.py"
    "ReadCategoriesFromExcel.py"
    "ReadPropertiesFromExcel.py"
    "ModuleUnpickler.py"
    "GetMatchingExcelFile.py"
    "ReorderableGrid.py"
    "SetGraphic.py"
    "imagebrowser.py"
    "scramble.py"
    "getuser.py"
    "NonBusyCall.py"
    "FileDrop.py"
    "ChipReader.py"
    "JChip.py"
    "RaceResult.py"
    "RaceResultImport.py"
    "ChipImport.py"
    "Undo.py"
    "HighPrecisionTimeEdit.py"
    "Ultra.py"
    "WebReader.py"
    "MyLapsServer.py"
    "JChipSetup.py"
    "SendPhotoRequests.py"
    "MultiCast.py"
    "FixCategories.py"
    "AddExcelInfo.py"
    "FtpUploadProgress.py"
]
for f in copyFiles:
	shutil.copy( os.path.join( '..', f), f )

if 'Linux' in platform.platform():
	sys.exit()

distDir = r'dist\SprintTimer'
distDirParent = os.path.dirname(distDir)
if os.path.exists(distDirParent):
	shutil.rmtree( distDirParent )
if not os.path.exists( distDirParent ):
	os.makedirs( distDirParent )

subprocess.call( [
	'pyinstaller',
	
	'SprintTimer.pyw',
	'--icon=images\SprintTimer.ico',
	'--clean',
	'--windowed',
	'--noconfirm',
	
	'--exclude-module=tcl',
	'--exclude-module=tk',
	'--exclude-module=Tkinter',
	'--exclude-module=_tkinter',
] )

# Copy additional dlls to distribution folder.
#wxHome = r'C:\Python27\Lib\site-packages\wx-2.8-msw-ansi\wx'
#try:
	#shutil.copy( os.path.join(wxHome, 'MSVCP71.dll'), distDir )
#except Exception:
	#pass
#try:
	#shutil.copy( os.path.join(wxHome, 'gdiplus.dll'), distDir )
#except Exception:
	#pass
	
# Add images and ffmpeg to the distribution folder.

def copyDir( d ):
	destD = os.path.join(distDir, d)
	if os.path.exists( destD ):
		shutil.rmtree( destD )
	os.mkdir( destD )
	for i in os.listdir( d ):
		if i[-3:] != '.db':	# Ignore .db files.
			shutil.copy( os.path.join(d, i), os.path.join(destD,i) )
			

for dir in ['SprintTimerImages', 'SprintTimerHtml', 'SprintTimerHtmlDoc', 'SprintTimerHelpIndex']: 
	copyDir( dir )

# Create the installer
inno = r'\Program Files (x86)\Inno Setup 5\ISCC.exe'
# Find the drive inno is installed on.
for drive in ['C', 'D']:
	innoTest = drive + ':' + inno
	if os.path.exists( innoTest ):
		inno = innoTest
		break
		
from Version import AppVerName
def make_inno_version():
	setup = {
		'AppName':				AppVerName.split()[0],
		'AppPublisher':			"Edward Sitarski",
		'AppContact':			"Edward Sitarski",
		'AppCopyright':			"Copyright (C) 2004-{} Edward Sitarski".format(datetime.date.today().year),
		'AppVerName':			AppVerName,
		'AppPublisherURL':		"http://www.sites.google.com/site/crossmgrsoftware/",
		'AppUpdatesURL':		"http://www.sites.google.com/site/crossmgrsoftware/downloads/",
		'VersionInfoVersion':	AppVerName.split()[1],
	}
	with open('inno_setup.txt', 'w') as f:
		for k, v in setup.items():
			f.write( '{}={}\n'.format(k,v) )
make_inno_version()
cmd = '"' + inno + '" ' + 'SprintTimer.iss'
print( cmd )
os.system( cmd )

# Create versioned executable.
from Version import AppVerName
vNum = AppVerName.split()[1]
vNum = vNum.replace( '.', '_' )
newExeName = 'SprintTimer_Setup_v' + vNum + '.exe'

try:
	os.remove( 'install\\' + newExeName )
except Exception:
	pass
	
shutil.copy( 'install\\SprintTimer_Setup.exe', 'install\\' + newExeName )
print( 'executable copied to: ' + newExeName )

# Create comprssed executable.
os.chdir( 'install' )
newExeName = os.path.basename( newExeName )
newZipName = newExeName.replace( '.exe', '.zip' )

try:
	os.remove( newZipName )
except Exception:
	pass

z = zipfile.ZipFile(newZipName, "w")
z.write( newExeName )
z.close()
print( 'executable compressed.' )

shutil.copy( newZipName, googleDrive )

from virus_total_apis import PublicApi as VirusTotalPublicApi
API_KEY = '64b7960464d4dbeed26ffa51cb2d3d2588cb95b1ab52fafd82fb8a5820b44779'
vt = VirusTotalPublicApi(API_KEY)
print ( 'VirusTotal Scan' )
vt.scan_file( os.path.abspath(newExeName) )



