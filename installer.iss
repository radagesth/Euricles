; Euricles Installer — Inno Setup Script
; Compila con: iscc installer.iss
; Requiere Inno Setup 6+ (https://jrsoftware.org/isdl.php)

#define MyAppName "Euricles"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Euricles"
#define MyAppURL "https://github.com/radagesth/Euricles"
#define MyAppExeName "Euricles.exe"

[Setup]
; Informacion basica
AppId={{B8A3C9E1-2D4F-4A6B-8C7D-9E0F1A2B3C4D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Directorios
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes

; Output
OutputDir=installer
OutputBaseFilename=Euricles_Installer_v{#MyAppVersion}
SetupIconFile=euricles.ico
UninstallDisplayIcon={app}\euricles.ico

; Compresion
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64
DiskSpanning=no

; Aspecto
WizardStyle=modern
WizardSizePercent=120
ShowLanguageDialog=auto
DisableWelcomePage=no
DisableFinishedPage=no

; Privilegios
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Version info
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} - Buscador de empleo Chile
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Messages]
spanish.WelcomeLabel2=Este asistente instalara [name/ver] en tu equipo.%n%nEs recomendable cerrar otras aplicaciones antes de continuar.
spanish.FinishedLabel=La instalacion de [name] ha finalizado correctamente.%n%nPuedes ejecutarlo desde el acceso directo en el escritorio.
spanish.HeadlineAppName=Euricles
spanish.SelectDirLabel3=El asistente instalara Euricles en la siguiente carpeta.

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
Name: "startmenu"; Description: "Crear acceso directo en el menu Inicio"; GroupDescription: "Accesos directos:"
Name: "autostart"; Description: "Ejecutar Euricles al iniciar Windows"; GroupDescription: "Opciones adicionales:"

[Files]
; Ejecutable principal
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion replacesameversion
; Icono
Source: "euricles.ico"; DestDir: "{app}"; Flags: ignoreversion
; Documentacion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
; Scrapers (necesarios para ejecucion desde codigo fuente)
Source: "scrapers\*.py"; DestDir: "{app}\scrapers"; Flags: ignoreversion

[Icons]
; Menu Inicio
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\euricles.ico"; Tasks: startmenu
Name: "{autoprograms}\{#MyAppName}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\euricles.ico"; Tasks: startmenu

; Escritorio
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\euricles.ico"; Tasks: desktopicon

; Inicio automatico
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\euricles.ico"; Tasks: autostart

[Run]
; Ejecutar despues de instalar (checkbox opcional)
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName} ahora"; Flags: nowait postinstall skipifsilent unchecked

[UninstallRun]
; Limpiar datos de usuario al desinstalar
Filename: "{cmd}"; Parameters: "/c rmdir /s /q ""{userappdata}\.euricles"""; Flags: runhidden

[UninstallDelete]
; Eliminar carpeta de instalacion completa
Type: filesandordirs; Name: "{app}"

[Registry]
; Registrar URL de actualizaciones (opcional)
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"; Flags: uninsdeletevalue

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ConfigPage := CreateInputQueryPage(
    wpSelectTasks,
    'Configuracion inicial',
    'Personaliza tu busqueda predeterminada',
    'Estos valores se usaran como predeterminados en Euricles. Puedes cambiarlos despues desde la aplicacion.'
  );

  ConfigPage.Add('Correo electronico (opcional):', False);
  ConfigPage.Add('Ciudad predeterminada:', False);

  ConfigPage.Values[0] := '';
  ConfigPage.Values[1] := 'Santiago';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigPath: string;
  ConfigJson: string;
begin
  if CurStep = ssPostInstall then
  begin
    ConfigPath := ExpandConstant('{userappdata}\.euricles');
    if not DirExists(ConfigPath) then
      CreateDir(ConfigPath);

    if (ConfigPage.Values[0] <> '') or (ConfigPage.Values[1] <> 'Santiago') then
    begin
      ConfigJson := '{'#13#10;
      if ConfigPage.Values[0] <> '' then
        ConfigJson := ConfigJson + '  "email": "' + ConfigPage.Values[0] + '",'#13#10;
      if ConfigPage.Values[1] <> 'Santiago' then
        ConfigJson := ConfigJson + '  "ciudad": "' + ConfigPage.Values[1] + '",'#13#10;
      ConfigJson := ConfigJson + '  "portal_computrabajo": true,'#13#10;
      ConfigJson := ConfigJson + '  "portal_trabajando": true,'#13#10;
      ConfigJson := ConfigJson + '  "portal_laborum": true,'#13#10;
      ConfigJson := ConfigJson + '  "portal_linkedin": false,'#13#10;
      ConfigJson := ConfigJson + '  "dark_mode": false'#13#10;
      ConfigJson := ConfigJson + '}';

      StringChangeEx(ConfigJson, '\', '\\', True);
      SaveStringToFile(ConfigPath + '\gui_config.json', ConfigJson, False);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox('Deseas eliminar tambien los datos de configuracion y cache?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\.euricles'), True, True, True);
    end;
  end;
end;
