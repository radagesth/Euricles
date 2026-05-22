# Euricles GUI + Ejecutable — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear una interfaz gráfica de escritorio con asistente paso a paso (wizard) para Euricles y empaquetar todo como un `.exe` de doble clic para usuarios no técnicos.

**Architecture:** `gui.pyw` (entry point sin consola) importa `gui_app.py` (clase `EuriclesApp` con CustomTkinter). Los scrapers existentes no se modifican. El `.exe` se genera con PyInstaller (`--onefile --noconsole`).

**Tech Stack:** CustomTkinter 5.2+, threading, PyInstaller 6+, tkinter (stdlib)

---

## Archivos

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `euricles/gui.pyw` | Crear | Entry point sin consola |
| `euricles/gui_app.py` | Crear | Toda la lógica de UI |
| `euricles/euricles.spec` | Crear (auto) | Config de PyInstaller |
| `euricles/dist/Euricles.exe` | Generar | Ejecutable final |

---

## Task 1: Instalar dependencias de GUI y empaquetado

**Files:**
- Modify: `euricles/requirements.txt`

- [ ] **Instalar CustomTkinter**

```bash
pip install customtkinter>=5.2.0
```
Verificar: `python -c "import customtkinter; print(customtkinter.__version__)"` → imprime versión >= 5.2

- [ ] **Instalar PyInstaller**

```bash
pip install pyinstaller>=6.0
```
Verificar: `pyinstaller --version` → imprime versión >= 6.0

- [ ] **Actualizar requirements.txt**

Agregar al final de `euricles/requirements.txt`:
```
customtkinter>=5.2.0
pyinstaller>=6.0
```

---

## Task 2: Crear `gui_app.py` — estructura base y pasos 1 y 2

**Files:**
- Create: `euricles/gui_app.py`

- [ ] **Crear `euricles/gui_app.py` completo con pasos 1 y 2**

```python
import sys
import os
import threading
import webbrowser
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import SCRAPER_REGISTRY
import report

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

PORTALS_LABELS = {
    "computrabajo": "Computrabajo.cl",
    "trabajando":   "Trabajando.cl",
    "laborum":      "Laborum.cl",
    "linkedin":     "LinkedIn  (puede fallar)",
}
MODALITIES = ["Cualquiera", "Remoto", "Presencial", "Híbrido"]


class EuriclesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Euricles — Buscador de Empleo Chile")
        self.geometry("480x540")
        self.resizable(False, False)

        self.cargo_var     = ctk.StringVar()
        self.ciudad_var    = ctk.StringVar(value="Santiago")
        self.modalidad_var = ctk.StringVar(value="Cualquiera")
        self.portal_vars   = {k: ctk.BooleanVar(value=(k != "linkedin")) for k in PORTALS_LABELS}
        self._progress_bars  = {}
        self._results        = {}
        self._current_frame  = None

        self._show_step1()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _clear(self):
        if self._current_frame:
            self._current_frame.destroy()

    def _header(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color="#16a34a", corner_radius=0, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="🌿  EURICLES",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color="white").pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(hdr, text="Buscador de empleo · Chile",
                     font=ctk.CTkFont(size=11),
                     text_color="#bbf7d0").pack(side="left")

    def _steps_bar(self, parent, current: int):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(pady=(12, 4))
        labels = ["1 Qué buscar", "2 Portales", "3 Resultados"]
        for i, lbl in enumerate(labels, 1):
            color = "#16a34a" if i <= current else "#cbd5e1"
            ctk.CTkLabel(row, text=lbl, font=ctk.CTkFont(size=10),
                         text_color=color).pack(side="left", padx=6)
            if i < 3:
                ctk.CTkLabel(row, text="›", text_color="#cbd5e1",
                             font=ctk.CTkFont(size=12)).pack(side="left")

    # ── Step 1: search form ───────────────────────────────────────────────────

    def _show_step1(self):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)
        self._steps_bar(f, 1)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="¿Qué trabajo buscas?",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#1e293b").pack(anchor="w", pady=(8, 16))

        ctk.CTkLabel(body, text="Cargo o área",
                     font=ctk.CTkFont(size=12), text_color="#64748b").pack(anchor="w")
        cargo_entry = ctk.CTkEntry(
            body, textvariable=self.cargo_var, height=38,
            placeholder_text="ej: Asistente administrativo",
            border_color="#bbf7d0", fg_color="#f0fdf4",
        )
        cargo_entry.pack(fill="x", pady=(2, 12))
        cargo_entry.focus()

        ctk.CTkLabel(body, text="Ciudad",
                     font=ctk.CTkFont(size=12), text_color="#64748b").pack(anchor="w")
        ctk.CTkEntry(body, textvariable=self.ciudad_var, height=38,
                     border_color="#bbf7d0", fg_color="#f0fdf4").pack(fill="x", pady=(2, 12))

        ctk.CTkLabel(body, text="Modalidad",
                     font=ctk.CTkFont(size=12), text_color="#64748b").pack(anchor="w")
        ctk.CTkOptionMenu(
            body, values=MODALITIES, variable=self.modalidad_var,
            fg_color="#f0fdf4", button_color="#16a34a",
            button_hover_color="#15803d",
        ).pack(fill="x", pady=(2, 0))

        btn = ctk.CTkButton(
            body, text="Siguiente →", height=42,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._show_step2,
        )
        btn.pack(fill="x", pady=(24, 0))
        btn.configure(state="disabled")

        def _check(*_):
            btn.configure(state="normal" if self.cargo_var.get().strip() else "disabled")
        self.cargo_var.trace_add("write", _check)

    # ── Step 2: portal selection ──────────────────────────────────────────────

    def _show_step2(self):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)
        self._steps_bar(f, 2)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="¿Dónde buscamos?",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#1e293b").pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(body, text="Selecciona los portales donde buscar:",
                     font=ctk.CTkFont(size=12), text_color="#64748b").pack(anchor="w", pady=(0, 12))

        for key, label in PORTALS_LABELS.items():
            row = ctk.CTkFrame(body, fg_color="#f0fdf4", corner_radius=8,
                               border_width=1, border_color="#bbf7d0")
            row.pack(fill="x", pady=4)
            ctk.CTkCheckBox(
                row, text=label, variable=self.portal_vars[key],
                checkmark_color="white", fg_color="#16a34a",
                hover_color="#15803d", font=ctk.CTkFont(size=12),
                text_color="#1e293b",
            ).pack(anchor="w", padx=12, pady=8)

        ctk.CTkLabel(body,
                     text="⚠  LinkedIn puede fallar por protecciones anti-bot",
                     font=ctk.CTkFont(size=10), text_color="#f59e0b").pack(anchor="w", pady=(4, 0))

        nav = ctk.CTkFrame(body, fg_color="transparent")
        nav.pack(fill="x", pady=(20, 0))
        ctk.CTkButton(nav, text="← Atrás", width=100, height=38,
                      fg_color="#f1f5f9", text_color="#64748b",
                      hover_color="#e2e8f0",
                      command=self._show_step1).pack(side="left")
        ctk.CTkButton(nav, text="Buscar trabajo 🔍", height=38,
                      fg_color="#16a34a", hover_color="#15803d",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._start_search).pack(side="right", fill="x",
                                                       expand=True, padx=(8, 0))

    # ── Step 3: progress ──────────────────────────────────────────────────────

    def _show_step3(self, selected_keys: list):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="🔍", font=ctk.CTkFont(size=36)).pack(pady=(20, 4))
        ctk.CTkLabel(body, text="Buscando ofertas...",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color="#1e293b").pack()
        ctk.CTkLabel(body,
                     text=f"Cargo: {self.cargo_var.get()}  ·  {self.ciudad_var.get()}",
                     font=ctk.CTkFont(size=11), text_color="#64748b").pack(pady=(2, 16))

        self._progress_bars = {}
        for key in selected_keys:
            label = PORTALS_LABELS[key]
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=160, anchor="w",
                         font=ctk.CTkFont(size=11),
                         text_color="#475569").pack(side="left")
            bar = ctk.CTkProgressBar(row, height=8, fg_color="#e2e8f0",
                                     progress_color="#16a34a")
            bar.set(0)
            bar.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self._progress_bars[key] = bar

        ctk.CTkLabel(body, text="⏳  No cierres esta ventana",
                     font=ctk.CTkFont(size=11), text_color="#f59e0b").pack(pady=(20, 0))

    # ── search execution ──────────────────────────────────────────────────────

    def _start_search(self):
        selected = [k for k, v in self.portal_vars.items() if v.get()]
        if not selected:
            return
        self._results = {}
        self._show_step3(selected)

        profile = {
            "name":     self.cargo_var.get().strip(),
            "keywords": [self.cargo_var.get().strip()],
            "location": self.ciudad_var.get().strip() or "Chile",
            "modality": "" if self.modalidad_var.get() == "Cualquiera"
                        else self.modalidad_var.get().lower(),
        }
        t = threading.Thread(target=self._search_worker,
                             args=(selected, profile), daemon=True)
        t.start()

    def _search_worker(self, selected_keys: list, profile: dict):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._scrape_one, key, profile): key
                for key in selected_keys
            }
            for future in as_completed(futures):
                key = futures[future]
                portal_name, jobs = future.result()
                self._results[portal_name] = jobs
                self.after(0, lambda k=key: self._on_portal_done(k))
        self.after(0, lambda: self._show_results(self._results))

    def _scrape_one(self, key: str, profile: dict) -> tuple:
        scraper = SCRAPER_REGISTRY[key]()
        try:
            jobs = scraper.search(profile, max_results=20)
        except Exception:
            jobs = []
        return scraper.portal_name, jobs

    def _on_portal_done(self, key: str):
        if key in self._progress_bars:
            self._progress_bars[key].set(1)

    # ── Step 4: results ───────────────────────────────────────────────────────

    def _show_results(self, results: dict):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)

        total = sum(len(j) for j in results.values())
        chips = "  ".join(
            f"{pn.split('.')[0]} {len(j)}" for pn, j in results.items()
        )
        banner = ctk.CTkFrame(f, fg_color="#16a34a", corner_radius=0, height=44)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        ctk.CTkLabel(banner,
                     text=f"✅  {total} ofertas encontradas   |   {chips}",
                     font=ctk.CTkFont(size=11), text_color="white").pack(side="left", padx=14)

        scroll = ctk.CTkScrollableFrame(f, fg_color="#f8fafc")
        scroll.pack(fill="both", expand=True)

        if total == 0:
            ctk.CTkLabel(scroll,
                         text="No se encontraron ofertas.\nIntenta con otras palabras clave.",
                         font=ctk.CTkFont(size=13), text_color="#94a3b8").pack(pady=40)
        else:
            for portal_name, jobs in results.items():
                if not jobs:
                    continue
                ctk.CTkLabel(scroll, text=f"  {portal_name}",
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color="#16a34a").pack(anchor="w", pady=(10, 2), padx=8)
                for job in jobs:
                    self._job_card(scroll, job)

        btns = ctk.CTkFrame(f, fg_color="#f0fdf4", corner_radius=0, height=54)
        btns.pack(fill="x", side="bottom")
        btns.pack_propagate(False)
        ctk.CTkButton(btns, text="💾  Guardar .txt", width=160, height=34,
                      fg_color="#16a34a", hover_color="#15803d",
                      command=lambda: self._save_txt(results)).pack(
                          side="left", padx=12, pady=10)
        ctk.CTkButton(btns, text="🔄  Nueva búsqueda", width=160, height=34,
                      fg_color="transparent", border_width=1,
                      border_color="#16a34a", text_color="#16a34a",
                      hover_color="#f0fdf4",
                      command=self._show_step1).pack(side="right", padx=12, pady=10)

    def _job_card(self, parent, job: dict):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=8,
                            border_width=1, border_color="#e2e8f0")
        card.pack(fill="x", padx=8, pady=3)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(inner, text=job["title"], anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#1e293b").pack(anchor="w")
        ctk.CTkLabel(inner,
                     text=f"{job['company']}  ·  {job['location']}  ·  {job['date']}",
                     anchor="w", font=ctk.CTkFont(size=10),
                     text_color="#64748b").pack(anchor="w")
        if job.get("url"):
            lnk = ctk.CTkLabel(inner, text="🔗 Ver oferta", anchor="w",
                               font=ctk.CTkFont(size=10),
                               text_color="#2563eb", cursor="hand2")
            lnk.pack(anchor="w")
            lnk.bind("<Button-1>", lambda e, u=job["url"]: webbrowser.open(u))

    def _save_txt(self, results: dict):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")],
            initialfile="euricles_resultados.txt",
            title="Guardar reporte",
        )
        if not path:
            return
        profile_name = self.cargo_var.get().strip()
        results_by_profile = {profile_name: results}
        tmp = tempfile.mkdtemp()
        try:
            generated = report.generate(results_by_profile, tmp)
            shutil.copy(generated, path)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        win = ctk.CTkToplevel(self)
        win.title("Guardado")
        win.geometry("300x110")
        win.grab_set()
        ctk.CTkLabel(win, text="✅  Archivo guardado correctamente",
                     font=ctk.CTkFont(size=13)).pack(pady=20)
        ctk.CTkButton(win, text="Cerrar", command=win.destroy,
                      fg_color="#16a34a").pack()


def launch():
    app = EuriclesApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
```

- [ ] **Verificar que la GUI abre sin errores**

```bash
cd C:\Users\roder\euricles
python gui_app.py
```
Esperado: ventana verde con campos de búsqueda visible.

---

## Task 3: Crear `gui.pyw` (entry point sin consola)

**Files:**
- Create: `euricles/gui.pyw`

- [ ] **Crear `gui.pyw`**

```python
from gui_app import launch
launch()
```

- [ ] **Verificar doble clic — sin consola negra**

Hacer doble clic en `C:\Users\roder\euricles\gui.pyw` desde el Explorador de Windows.  
Esperado: ventana Euricles abre directo, sin consola negra de fondo.

---

## Task 4: Construir el ejecutable con PyInstaller

**Files:**
- Generate: `euricles/dist/Euricles.exe`

- [ ] **Ejecutar PyInstaller**

```bash
cd C:\Users\roder\euricles
pyinstaller --onefile --noconsole --name Euricles ^
  --add-data "scrapers;scrapers" ^
  --hidden-import scrapers.computrabajo ^
  --hidden-import scrapers.trabajando ^
  --hidden-import scrapers.laborum ^
  --hidden-import scrapers.linkedin ^
  --hidden-import lxml.etree ^
  --hidden-import lxml._elementpath ^
  --hidden-import bs4 ^
  --collect-data customtkinter ^
  gui.pyw
```

Esperado: sin errores. Aparece `dist/Euricles.exe` al finalizar.

- [ ] **Copiar archivos de datos al lado del .exe**

El .exe necesita `config.py` y el directorio `output/` accesibles cuando corre. Copiarlos junto al ejecutable:

```bash
copy C:\Users\roder\euricles\config.py C:\Users\roder\euricles\dist\config.py
mkdir C:\Users\roder\euricles\dist\output
```

- [ ] **Verificar el ejecutable**

Hacer doble clic en `C:\Users\roder\euricles\dist\Euricles.exe`.  
Esperado: abre la ventana del asistente, sin consola, sin errores.

- [ ] **Probar búsqueda real desde el .exe**

1. Escribir "administrador" en el campo cargo
2. Ciudad: Santiago
3. Activar Computrabajo y Trabajando, desactivar el resto
4. Hacer clic en "Buscar trabajo 🔍"
5. Esperar la pantalla de progreso y los resultados
6. Guardar .txt en el escritorio  
Esperado: archivo `.txt` generado correctamente en la ubicación elegida.

---

## Task 5: Crear acceso directo al `.exe` en el escritorio

**Files:**
- Generate: `C:\Users\roder\Desktop\Euricles.lnk`

- [ ] **Crear acceso directo al .exe**

```powershell
$s = New-Object -ComObject WScript.Shell
$lnk = $s.CreateShortcut("$env:USERPROFILE\Desktop\Euricles.lnk")
$lnk.TargetPath = "C:\Users\roder\euricles\dist\Euricles.exe"
$lnk.WorkingDirectory = "C:\Users\roder\euricles\dist"
$lnk.Description = "Euricles - Buscador de Empleo Chile"
$lnk.IconLocation = "C:\Users\roder\euricles\dist\Euricles.exe,0"
$lnk.Save()
```

Esperado: ícono `Euricles` en el escritorio. Doble clic abre la app.

---

## Verificación final

1. Doble clic en `Euricles` del escritorio → ventana verde del asistente
2. Completar búsqueda → pantalla de progreso con barras → resultados con ofertas
3. Clic en "🔗 Ver oferta" → abre el navegador en la oferta correcta
4. Clic en "💾 Guardar .txt" → diálogo de guardar → archivo generado con contenido
5. Clic en "🔄 Nueva búsqueda" → regresa al paso 1 con campos limpios
