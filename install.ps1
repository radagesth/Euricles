<#
.SYNOPSIS
  Instalador portable de Euricles — Buscador de empleo Chile
.DESCRIPTION
  Compila el .exe con PyInstaller y lo instala en una carpeta propia.
  Crea acceso directo en el escritorio con el icono de Euricles.
#>

param(
    [switch]$CompileOnly,
    [switch]$NoShortcut,
    [string]$InstallDir = "$env:LOCALAPPDATA\Euricles"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExeName = "Euricles.exe"
$IconFile = "$ScriptRoot\euricles.ico"
$BuildDir = "$ScriptRoot\dist\Euricles"
$TargetExe = "$BuildDir\$ExeName"

# ── 1. Build icon if missing ──
if (-not (Test-Path $IconFile)) {
    Write-Host "🔨 Generando icono..." -ForegroundColor Yellow
    & python "$ScriptRoot\build_icon.py"
}

# ── 2. Compile with PyInstaller ──
if (-not (Test-Path $TargetExe)) {
    Write-Host "🔨 Compilando Euricles con PyInstaller..." -ForegroundColor Cyan
    & pip install pyinstaller -q
    & pyinstaller "$ScriptRoot\Euricles.spec" --clean --noconfirm
    if (-not (Test-Path $TargetExe)) {
        Write-Host "❌ Error: No se generó el ejecutable." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Compilación exitosa: $TargetExe" -ForegroundColor Green
} else {
    Write-Host "✅ Ejecutable ya compilado: $TargetExe" -ForegroundColor Green
}

if ($CompileOnly) {
    Write-Host "✅ Compilación completada. Usa -InstallDir para instalar." -ForegroundColor Green
    exit 0
}

# ── 3. Install ──
Write-Host "📦 Instalando en: $InstallDir" -ForegroundColor Cyan

# Remove old installation
if (Test-Path $InstallDir) {
    Remove-Item -Path "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

# Copy all files
Copy-Item -Path "$BuildDir\*" -Destination $InstallDir -Recurse -Force
Copy-Item -Path $IconFile -Destination "$InstallDir\euricles.ico" -Force

Write-Host "✅ Archivos copiados a: $InstallDir" -ForegroundColor Green

# ── 4. Desktop shortcut ──
if (-not $NoShortcut) {
    $WshShell = New-Object -ComObject WScript.Shell
    $Desktop = [Environment]::GetFolderPath("Desktop")
    $ShortcutPath = "$Desktop\Euricles.lnk"
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "$InstallDir\$ExeName"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.IconLocation = "$InstallDir\euricles.ico, 0"
    $Shortcut.Description = "Euricles — Buscador de empleo Chile"
    $Shortcut.Save()
    Write-Host "🖥️  Acceso directo creado en el escritorio" -ForegroundColor Green
}

# ── 5. Start menu shortcut ──
$StartMenu = [Environment]::GetFolderPath("StartMenu")
$StartMenuDir = "$StartMenu\Programs\Euricles"
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}
$WshShell2 = New-Object -ComObject WScript.Shell
$SMShortcut = $WshShell2.CreateShortcut("$StartMenuDir\Euricles.lnk")
$SMShortcut.TargetPath = "$InstallDir\$ExeName"
$SMShortcut.WorkingDirectory = $InstallDir
$SMShortcut.IconLocation = "$InstallDir\euricles.ico, 0"
$SMShortcut.Description = "Euricles — Buscador de empleo Chile"
$SMShortcut.Save()
Write-Host "📋  Acceso directo creado en menú Inicio" -ForegroundColor Green

# ── 6. Config dir ──
$ConfigDir = "$env:USERPROFILE\.euricles"
if (-not (Test-Path $ConfigDir)) {
    New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✅  EURICLES INSTALADO                      ║" -ForegroundColor Green
Write-Host "║   📂  $InstallDir" -ForegroundColor White
Write-Host "║   🖥️  Acceso directo en el escritorio        ║" -ForegroundColor White
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona Enter para ejecutar Euricles ahora..." -ForegroundColor Cyan
$key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Start-Process "$InstallDir\$ExeName"
