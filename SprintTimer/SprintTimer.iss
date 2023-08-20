; -- SprintTimer.iss --

[Setup]
#include "inno_setup.txt"
ArchitecturesInstallIn64BitMode=x64
DefaultDirName={commonpf}\SprintTimer
DefaultGroupName=CrossMgr
UninstallDisplayIcon={app}\SprintTimer.exe
Compression=lzma2/ultra64
SolidCompression=yes
ChangesAssociations=yes

[Registry]
; Automatically configure CrossMgr to launch .cmn files.
Root: HKCR; Subkey: ".spr"; ValueType: string; ValueName: ""; ValueData: "SprintTimer"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "SprintTimer"; ValueType: string; ValueName: ""; ValueData: "SprintTimer Race File"; Flags: uninsdeletekey
kaRoot: HKCR; Subkey: "SprintTimer\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\SprintTimer.exe,0"
Root: HKCR; Subkey: "SprintTimer\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\SprintTimer.exe"" ""%1"""

[Tasks] 
Name: "desktopicon"; Description: "Create a &desktop icon"; 
	
[Files]
Source: "*.*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\SprintTimer"; Filename: "{app}\SprintTimer.exe"
Name: "{userdesktop}\SprintTimer"; Filename: "{app}\SprintTimer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SprintTimer.exe"; Description: "Launch SprintTimer"; Flags: nowait postinstall skipifsilent
