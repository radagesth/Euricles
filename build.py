"""
Build system for Euricles.
Uso:
  python build.py            # Compila .exe + genera instalador (.exe + portable)
  python build.py --exe      # Solo compilar .exe
  python build.py --install  # Compilar + instalar localmente
  python build.py --portable # Compilar + copiar a carpeta portable
  python build.py --installer # Solo generar instalador (requiere ISCC)
"""
import os
import sys
import io
import shutil
import subprocess
import argparse
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
DIST_DIR = ROOT / "dist" / "Euricles"
PORTABLE_DIR = ROOT / "Euricles_Portable"


def step(msg: str):
    print(f"\n  {'=' * 50}")
    print(f"  {msg}")
    print(f"  {'=' * 50}\n")


def run(cmd: list[str], desc: str):
    print(f"  -> {desc}...")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  !! Error:\n{result.stderr}")
        sys.exit(1)
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")


def build_icon():
    step("PASO 1/4 - Generando icono")
    run([sys.executable, "build_icon.py"], "Icono multiresolucion")
    assert (ROOT / "euricles.ico").exists(), "No se genero el icono"


def build_exe():
    step("PASO 2/4 - Compilando ejecutable con PyInstaller")
    run([sys.executable, "-m", "PyInstaller", "Euricles.spec", "--clean", "--noconfirm"], "PyInstaller")
    assert (DIST_DIR / "Euricles.exe").exists(), "No se genero el ejecutable"
    size = os.path.getsize(DIST_DIR / "Euricles.exe")
    print(f"\n  [OK] Ejecutable: {DIST_DIR / 'Euricles.exe'} ({size / 1024:.1f} KB)")


def build_portable():
    step("PASO 3/4 - Creando version portable")

    if PORTABLE_DIR.exists():
        shutil.rmtree(PORTABLE_DIR)
    shutil.copytree(DIST_DIR, PORTABLE_DIR)

    ico = ROOT / "euricles.ico"
    if ico.exists():
        shutil.copy2(ico, PORTABLE_DIR / "euricles.ico")

    size = sum(f.stat().st_size for f in PORTABLE_DIR.rglob("*") if f.is_file())
    print(f"\n  [OK] Portable: {PORTABLE_DIR} ({size / 1024:.1f} KB)")
    print(f"  [OK] Ejecuta: {PORTABLE_DIR / 'Euricles.exe'}")


def build_installer():
    step("PASO 4/4 - Generando instalador Inno Setup")

    iscc_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    iscc = None
    for p in iscc_paths:
        if os.path.exists(p):
            iscc = p
            break

    if iscc:
        out_dir = ROOT / "installer"
        out_dir.mkdir(exist_ok=True)
        run([iscc, "installer.iss"], "Inno Setup")
        for f in out_dir.glob("*.exe"):
            print(f"\n  [OK] Instalador: {f} ({os.path.getsize(f) / 1024:.1f} KB)")
    else:
        print("  [!!] Inno Setup no encontrado. Instalalo desde:")
        print("       https://jrsoftware.org/isdl.php")
        print("  O usa el instalador PowerShell: .\\install.ps1")


def main():
    parser = argparse.ArgumentParser(description="Build Euricles")
    parser.add_argument("--exe", action="store_true", help="Solo compilar .exe")
    parser.add_argument("--install", action="store_true", help="Compilar + instalar local")
    parser.add_argument("--portable", action="store_true", help="Compilar + crear version portable")
    parser.add_argument("--installer", action="store_true", help="Solo generar instalador Inno Setup")
    args = parser.parse_args()

    build_icon()
    build_exe()

    if args.exe:
        print("\n  [OK] Compilacion completada.")
        return

    if args.portable:
        build_portable()
        return

    if args.install:
        step("PASO FINAL - Instalando localmente")
        run([
            sys.executable, "-c",
            "import subprocess, sys; subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'install.ps1', '-CompileOnly'], cwd=sys.path[0])"
        ], "Instalacion PowerShell")
        return

    if args.installer:
        build_installer()
        return

    build_portable()
    build_installer()

    step("[OK] BUILD COMPLETADO")
    print(f"  [OK] Portable:  {PORTABLE_DIR}")
    print(f"  [OK] Ejecutable: {DIST_DIR / 'Euricles.exe'}")
    print(f"  [OK] Installer: {ROOT / 'installer' / 'Euricles_Installer_v1.0.0.exe'}")


if __name__ == "__main__":
    main()
