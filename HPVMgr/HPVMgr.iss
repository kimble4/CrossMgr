; -- HPVMgr.iss --

[Setup]
#include "inno_setup.txt"
ArchitecturesInstallIn64BitMode=x64
DefaultDirName={commonpf}\HPVMgr
DefaultGroupName=CrossMgr
UninstallDisplayIcon={app}\HPVMgr.exe
Compression=lzma2/ultra64
SolidCompression=yes
ChangesAssociations=yes

[Registry]
; Automatically configure CrossMgr to launch .cmn files.
Root: HKCR; Subkey: ".hdb"; ValueType: string; ValueName: ""; ValueData: "HPVMgr"; Flags: uninsdeletevalue
Root: HKCR; Subkey: "HPVMgr"; ValueType: string; ValueName: ""; ValueData: "HPVMgr database File"; Flags: uninsdeletekey
Root: HKCR; Subkey: "HPVMgr\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\HPVMgr.exe,0"
Root: HKCR; Subkey: "HPVMgr\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\HPVMgr.exe"" ""%1"""

[Tasks] 
Name: "desktopicon"; Description: "Create a &desktop icon"; 
	
[Files]
Source: "*.*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\HPVMgr"; Filename: "{app}\HPVMgr.exe"
Name: "{userdesktop}\HPVMgr"; Filename: "{app}\HPVMgr.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\HPVMgr.exe"; Description: "Launch HPVMgr"; Flags: nowait postinstall skipifsilent
