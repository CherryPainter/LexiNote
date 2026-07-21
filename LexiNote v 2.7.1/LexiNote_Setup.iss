; Inno Setup 安装脚本 - LexiNote v2.7.1
[Setup]
; 应用程序基本信息
AppId={{0AB8F8E8-2D82-4A41-9B7F-5A863C34F25E}
AppName=LexiNote
AppVersion=2.7.1
AppPublisher=LexiNote Team
AppPublisherURL=https://github.com/CherryPainter/LexiNote
AppSupportURL=https://github.com/CherryPainter/LexiNote
AppUpdatesURL=https://github.com/CherryPainter/LexiNote/releases
DefaultDirName={pf}\LexiNote
DefaultGroupName=LexiNote
AllowNoIcons=yes

; 安装程序版本信息（控制文件属性中显示的文件版本）
VersionInfoVersion=2.7.1.0
VersionInfoCompany=LexiNote Team
VersionInfoDescription=LexiNote Setup
VersionInfoCopyright=Copyright (C) 2026 LexiNote Team
VersionInfoProductName=LexiNote
VersionInfoProductVersion=2.7.1

LicenseFile=d:\Learn\data\py25\LexiNote\LexiNote v 2.7.1\LexiNote_EULA.txt
InfoBeforeFile=d:\Learn\data\py25\LexiNote\LexiNote v 2.7.1\LexiNote_Privacy_Policy.txt
InfoAfterFile=

; 安装程序设置
OutputDir=d:\Learn\data\py25\LexiNote\LexiNote v 2.7.1
OutputBaseFilename=LexiNote-Setup-v2.7.1
SetupIconFile=..\..\app.ico
Compression=lzma2/ultra64
SolidCompression=yes

; 现代风格设置
WizardStyle=modern
ShowLanguageDialog=no
WizardResizable=no
WizardImageFile=

; 组件设置（默认显示组件页面）
[Components]
Name: "main"; Description: "LexiNote 主程序"; Types: full compact custom; Flags: fixed
Name: "desktopicon"; Description: "桌面快捷方式"; Types: full compact; Flags: checkablealone

[Files]
; 主程序文件（Nuitka 单文件产物）
Source: "..\..\build\LexiNote.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\app.ico"; DestDir: "{app}"; Flags: ignoreversion
; 预置种子词库，首次启动自动迁移进 SQLite（不打包运行态数据库）
Source: "..\..\data\word_dict.json"; DestDir: "{app}\data"; Flags: ignoreversion

[Icons]
Name: "{group}\LexiNote"; Filename: "{app}\LexiNote.exe"; IconFilename: "{app}\app.ico"
Name: "{group}\卸载 LexiNote"; Filename: "{uninstallexe}"
Name: "{commondesktop}\LexiNote"; Filename: "{app}\LexiNote.exe"; IconFilename: "{app}\app.ico"; Components: desktopicon

[Run]
Filename: "{app}\LexiNote.exe"; Description: "运行 LexiNote"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\cache"
Type: filesandordirs; Name: "{app}\data\logs"

[Registry]
; 记录安装信息到注册表
Root: HKLM; Subkey: "Software\LexiNote"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKLM; Subkey: "Software\LexiNote"; ValueType: string; ValueName: "Version"; ValueData: "{#SetupSetting('AppVersion')}"; Flags: uninsdeletevalue

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
