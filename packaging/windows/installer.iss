#define MyAppName "PrintWatch Desktop"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0-dev"
#endif
#define MyAppPublisher "Monty Labs"
#define MyAppURL "https://github.com/antonflor/elegoo-webcam-viewer"
#define MyAppExeName "PrintWatch Desktop.exe"

[Setup]
AppId={{C2150A65-F527-4E6C-A1A2-CA1AC4BB17AC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\PrintWatch Desktop
DisableProgramGroupPage=yes
OutputDir=..\..\dist-installer
OutputBaseFilename=PrintWatch-Desktop-{#MyAppVersion}-Windows-x64-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\icons\printwatch.ico
PrivilegesRequired=lowest

[Files]
Source: "..\..\dist\PrintWatch Desktop\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
