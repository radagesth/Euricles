<#
.SYNOPSIS
  Compilador de instalador Euricles para Windows.
.DESCRIPTION
  Descarga Inno Setup portable, compila installer.iss y genera
  un instalador .exe listo para distribuir en cualquier PC con Windows.
  No requiere instalacion previa de Inno Setup.
#>

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$IsccDir    = "$env:TEMP\iscc-portable"
$IsccExe    = "$IsccDir\ISCC.exe"
$InstallerOut = "$ScriptRoot\installer"

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  EURICLES — Generador de Instalador Windows       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 1. Verificar que el .exe compilado existe ──
$ExePath = "$ScriptRoot\dist\Euricles.exe"
if (-not (Test-Path $ExePath)) {
    Write-Host "[1/5] Ejecutable no encontrado. Compilando con PyInstaller..." -ForegroundColor Yellow
    Push-Location $ScriptRoot
    & python -m PyInstaller --clean --noconfirm Euricles.spec 2>&1 | Out-Null
    Pop-Location
    if (-not (Test-Path $ExePath)) {
        Write-Host "ERROR: No se pudo compilar el ejecutable." -ForegroundColor Red
        exit 1
    }
    Write-Host "[1/5] Ejecutable compilado correctamente." -ForegroundColor Green
} else {
    Write-Host "[1/5] Ejecutable encontrado: $($ExePath)" -ForegroundColor Green
}

# ── 2. Verificar icono ──
$IcoPath = "$ScriptRoot\euricles.ico"
if (-not (Test-Path $IcoPath)) {
    Write-Host "[2/5] Icono no encontrado. Generando..." -ForegroundColor Yellow
    & python "$ScriptRoot\build_icon.py"
} else {
    Write-Host "[2/5] Icono encontrado." -ForegroundColor Green
}

# ── 3. Descargar Inno Setup portable ──
$IsccUrl = "https://github.com/jrsoftware/issrc/releases/download/is-6_4_2/InnoSetup-6.4.2.exe"
$IsccInstaller = "$env:TEMP\innosetup-installer.exe"

if (-not (Test-Path $IsccExe)) {
    Write-Host "[3/5] Descargando Inno Setup portable..." -ForegroundColor Yellow

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $web = New-Object System.Net.WebClient
        Write-Host "  Descargando desde $IsccUrl ..."
        $web.DownloadFile($IsccUrl, $IsccInstaller)
        Write-Host "  Descarga completada." -ForegroundColor Green
    } catch {
        Write-Host "  Error descargando: $_" -ForegroundColor Red
        Write-Host "  Intentando con url alternativa..." -ForegroundColor Yellow
        $IsccUrl = "https://files.jrsoftware.org/is/6/innosetup-6.4.2.exe"
        try {
            $web.DownloadFile($IsccUrl, $IsccInstaller)
        } catch {
            Write-Host "  Error: No se pudo descargar Inno Setup." -ForegroundColor Red
            Write-Host "  Instalalo manualmente desde: https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
            Write-Host "  Luego ejecuta: iscc installer.iss" -ForegroundColor Yellow
            exit 1
        }
    }

    # Extraer ISCC.exe del instalador usando 7-Zip o el installer mismo
    Write-Host "  Extrayendo ISCC.exe..." -ForegroundColor Yellow

    # El instalador de Inno Setup puede extraerse en modo silencioso
    # Primero intentamos extraer solo ISCC
    if (Test-Path $IsccDir) { Remove-Item $IsccDir -Recurse -Force -ErrorAction SilentlyContinue }
    New-Item -ItemType Directory -Path $IsccDir -Force | Out-Null

    # Inno Setup installer soporta /VERYSILENT /SUPPRESSMSGBOXES /DIR="..."
    # Pero solo extrae si es el instalador completo. Usamos extract batch.
    try {
        Start-Process -FilePath $IsccInstaller -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /DIR=`"$IsccDir`" /COMPONENTS=compiler" -Wait -NoNewWindow
    } catch {
        Write-Host "  Error en extraccion automatica." -ForegroundColor Red
    }

    # Si no se extrajo, buscar ISCC en la ubicacion
    if (-not (Test-Path $IsccExe)) {
        $isccCandidates = @(
            "$IsccDir\ISCC.exe",
            "$IsccDir\Inno Setup 6\ISCC.exe",
            "$IsccDir\Inno Setup 5\ISCC.exe",
            "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
        )
        foreach ($cand in $isccCandidates) {
            if (Test-Path $cand) {
                $IsccExe = $cand
                break
            }
        }
    }

    if (-not (Test-Path $IsccExe)) {
        Write-Host "  No se pudo extraer ISCC.exe. Buscando instalacion existente..." -ForegroundColor Yellow
        $existingIscc = @(
            "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles}\Inno Setup 5\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe"
        )
        foreach ($cand in $existingIscc) {
            if (Test-Path $cand) {
                $IsccExe = $cand
                Write-Host "  Encontrado ISCC.exe en: $IsccExe" -ForegroundColor Green
                break
            }
        }
    }
} else {
    Write-Host "[3/5] Inno Setup portable ya descargado." -ForegroundColor Green
}

# ── 4. Compilar instalador ──
if (-not (Test-Path $IsccExe)) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Red
    Write-Host "║  No se encontro ISCC.exe                          ║" -ForegroundColor Red
    Write-Host "║  Instala Inno Setup desde:                        ║" -ForegroundColor Red
    Write-Host "║  https://jrsoftware.org/isdl.php                  ║" -ForegroundColor Red
    Write-Host "║  Luego ejecuta manualmente:                       ║" -ForegroundColor Red
    Write-Host "║  iscc installer.iss                               ║" -ForegroundColor Red
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Red
    exit 1
}

Write-Host "[4/5] Compilando instalador con Inno Setup..." -ForegroundColor Cyan
Write-Host "  ISCC: $IsccExe" -ForegroundColor Gray
Write-Host "  Script: $ScriptRoot\installer.iss" -ForegroundColor Gray

if (-not (Test-Path $InstallerOut)) {
    New-Item -ItemType Directory -Path $InstallerOut -Force | Out-Null
}

Push-Location $ScriptRoot
try {
    $output = & $IsccExe "installer.iss" 2>&1
    $exitCode = $LASTEXITCODE
    foreach ($line in $output) {
        Write-Host "  $line"
    }
    if ($exitCode -ne 0) {
        Write-Host "  ERROR: Inno Setup fallo con codigo $exitCode" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# ── 5. Resultado ──
$InstallerFiles = Get-ChildItem "$InstallerOut\*.exe" -ErrorAction SilentlyContinue
if ($InstallerFiles) {
    $InstallerFile = $InstallerFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $size = [math]::Round($InstallerFile.Length / 1MB, 1)
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  INSTALADOR GENERADO EXITOSAMENTE                 ║" -ForegroundColor Green
    Write-Host "╠════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "║  Archivo: $($InstallerFile.Name)" -ForegroundColor White
    Write-Host "║  Tamano:  $size MB" -ForegroundColor White
    Write-Host "║  Ruta:    $($InstallerFile.FullName)" -ForegroundColor White
    Write-Host "╚════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "Distribuye $($InstallerFile.Name) en cualquier PC con Windows." -ForegroundColor Cyan
    Write-Host "El instalador incluye todo lo necesario para ejecutar Euricles." -ForegroundColor Cyan
} else {
    Write-Host "ERROR: No se genero el instalador." -ForegroundColor Red
    exit 1
}
