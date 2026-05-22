"""
Euricles Installer — Instalador autónomo para Windows.
Se compila a si mismo con PyInstaller generando un instalador.exe
que funciona en cualquier PC con Windows sin dependencias externas.
"""
import os
import sys
import shutil
import subprocess
import tempfile
import base64
import struct
import zipfile
import io
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DIST_EXE = SCRIPT_DIR / "dist" / "Euricles.exe"
ICO_PATH = SCRIPT_DIR / "euricles.ico"
OUTPUT_DIR = SCRIPT_DIR / "installer"
OUTPUT_EXE = OUTPUT_DIR / "Euricles_Installer_v1.0.0.exe"

PAYLOAD_ZIP = None

# ── Build the installer payload ──────────────────────────────────


def _build_payload() -> bytes:
    """Create a self-extracting zip with the app + icon."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(str(DIST_EXE), "Euricles.exe")
        if ICO_PATH.exists():
            z.write(str(ICO_PATH), "euricles.ico")
    return buf.getvalue()


# ── Installer logic (runs inside the final .exe) ──────────────


def _run_installer():
    """Main installer routine — executed in the compiled .exe."""
    import tkinter as tk
    from tkinter import filedialog, messagebox
    import subprocess
    import zipfile
    import sys
    import os
    import io
    from pathlib import Path
    import ctypes

    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def run_as_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

    def create_shortcut(target, shortcut_path, working_dir, icon_path, description):
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.TargetPath = str(target)
            shortcut.WorkingDirectory = str(working_dir)
            shortcut.IconLocation = f"{icon_path},0" if icon_path else ""
            shortcut.Description = description
            shortcut.Save()
            return True
        except Exception:
            try:
                import ctypes
                from ctypes import wintypes
                # Fallback using PowerShell
                ps_script = f"""
                $WshShell = New-Object -ComObject WScript.Shell
                $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
                $Shortcut.TargetPath = '{target}'
                $Shortcut.WorkingDirectory = '{working_dir}'
                $Shortcut.IconLocation = '{icon_path},0'
                $Shortcut.Description = '{description}'
                $Shortcut.Save()
                """
                subprocess.run(["powershell", "-Command", ps_script],
                               capture_output=True, creationflags=0x08000000)
                return True
            except Exception:
                return False

    root = tk.Tk()
    root.withdraw()

    # ── Extract payload ──
    payload = _get_payload()
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        exe_data = z.read("Euricles.exe")
        ico_data = z.read("euricles.ico") if "euricles.ico" in z.namelist() else None

    # ── Ask install dir ──
    default_dir = os.path.join(os.environ.get("LOCALAPPDATA", "C:\\Program Files"), "Euricles")
    install_dir = Path(filedialog.askdirectory(
        title="Selecciona la carpeta de instalacion para Euricles",
        initialdir=default_dir,
        mustexist=False,
    ))

    if not install_dir:
        sys.exit(0)

    # ── Create dir if needed ──
    install_dir.mkdir(parents=True, exist_ok=True)

    # ── Write files ──
    (install_dir / "Euricles.exe").write_bytes(exe_data)
    if ico_data:
        (install_dir / "euricles.ico").write_bytes(ico_data)

    # ── Create desktop shortcut ──
    desktop = Path.home() / "Desktop"
    shortcut_path = desktop / "Euricles.lnk"
    create_shortcut(
        install_dir / "Euricles.exe",
        shortcut_path,
        install_dir,
        install_dir / "euricles.ico" if ico_data else None,
        "Euricles - Buscador de empleo Chile",
    )

    # ── Create start menu shortcut ──
    start_menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Euricles"
    start_menu.mkdir(parents=True, exist_ok=True)
    create_shortcut(
        install_dir / "Euricles.exe",
        start_menu / "Euricles.lnk",
        install_dir,
        install_dir / "euricles.ico" if ico_data else None,
        "Euricles - Buscador de empleo Chile",
    )

    # ── Done ──
    messagebox.showinfo(
        "Instalacion completada",
        f"Euricles se ha instalado correctamente en:\n{install_dir}\n\n"
        f"Se han creado accesos directos en el escritorio y menu Inicio."
    )

    # ── Run ──
    if messagebox.askyesno("Ejecutar", "Deseas ejecutar Euricles ahora?"):
        subprocess.Popen([str(install_dir / "Euricles.exe")], cwd=str(install_dir))

    root.destroy()


def _get_payload():
    """Return the embedded zip payload (injected at build time)."""
    return base64.b64decode(PAYLOAD_ZIP)


# ── Build the installer executable ──────────────────────────────


def build():
    """Inject the payload into the installer script and compile with PyInstaller."""
    global PAYLOAD_ZIP

    print("=" * 56)
    print("  EURICLES — Generador de Instalador Windows")
    print("=" * 56)

    # 1. Validate inputs
    if not DIST_EXE.exists():
        print(f"ERROR: No se encuentra {DIST_EXE}.")
        print("Ejecuta primero: python -m PyInstaller Euricles.spec --clean --noconfirm")
        sys.exit(1)

    # 2. Build the payload zip
    print("\n[1/3] Empaquetando aplicacion...")
    payload = _build_payload()
    payload_b64 = base64.b64encode(payload).decode("ascii")
    print(f"      Payload: {len(payload) / 1024:.1f} KB comprimido")

    # 3. Generate the installer script with embedded payload
    print("[2/3] Generando instalador autónomo...")

    installer_source = Path(__file__).read_text(encoding="utf-8")
    # Inject payload
    installer_source = installer_source.replace(
        'PAYLOAD_ZIP = None',
        f'PAYLOAD_ZIP = "{payload_b64}"'
    )

    # Create temporary directory
    tmp_dir = Path(tempfile.mkdtemp(prefix="euricles_installer_"))
    installer_file = tmp_dir / "installer_build.py"
    installer_file.write_text(installer_source, encoding="utf-8")

    # 4. Compile installer with PyInstaller
    print("[3/3] Compilando instalador.exe con PyInstaller (esto toma tiempo)...")

    OUTPUT_DIR.mkdir(exist_ok=True)

    result = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name", "Euricles_Installer_v1.0.0",
            "--distpath", str(OUTPUT_DIR),
            "--workpath", str(tmp_dir / "build"),
            "--specpath", str(tmp_dir),
            "--add-data", f"{ICO_PATH};." if ICO_PATH.exists() else "",
            "--hidden-import", "win32com.client",
            str(installer_file),
        ],
        cwd=str(tmp_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERROR al compilar instalador:\n{result.stderr[-2000:]}")
        shutil.rmtree(tmp_dir, ignore_errors=True)
        sys.exit(1)

    # 5. Clean up
    shutil.rmtree(tmp_dir, ignore_errors=True)

    # Remove potential _internal folder created by PyInstaller
    internal_dir = OUTPUT_DIR / "Euricles_Installer_v1.0.0"
    if internal_dir.exists():
        internal_exe = internal_dir / "Euricles_Installer_v1.0.0.exe"
        if internal_exe.exists():
            shutil.copy2(internal_exe, OUTPUT_DIR / "Euricles_Installer_v1.0.0.exe")
            shutil.rmtree(internal_dir)

    if OUTPUT_EXE.exists():
        size_mb = OUTPUT_EXE.stat().st_size / (1024 * 1024)
        print(f"\n  INSTALADOR GENERADO: {OUTPUT_EXE}")
        print(f"  Tamaño: {size_mb:.1f} MB")
        print(f"\n  Distribuye este .exe en cualquier PC con Windows.")
        print(f"  El usuario solo debe ejecutarlo y elegir la carpeta de instalación.")
    else:
        print("ERROR: No se generó el instalador.")
        # List output dir contents
        for f in OUTPUT_DIR.iterdir():
            print(f"  {f.name} ({f.stat().st_size} bytes)")
        sys.exit(1)


# ── Entry point ─────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        _run_installer()
    else:
        build()
