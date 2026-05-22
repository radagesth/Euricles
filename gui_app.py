import sys
import os
import threading
import webbrowser
import shutil
import tempfile
import json
import csv
import io as _io
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import filedialog
from pathlib import Path
from datetime import datetime

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import SCRAPER_REGISTRY
from scrapers.base import check_connectivity
import report

CONFIG_DIR = Path.home() / ".euricles"
CONFIG_FILE = CONFIG_DIR / "gui_config.json"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

PORTALS_LABELS = {
    "computrabajo": "Computrabajo.cl",
    "trabajando":   "Trabajando.cl",
    "laborum":      "Laborum.cl",
    "linkedin":     "LinkedIn  (puede fallar)",
}
MODALITIES = ["Cualquiera", "Remoto", "Presencial", "Híbrido"]


def _center_window(win, w: int, h: int):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry(f"{w}x{h}+{x}+{y}")


def _load_gui_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_gui_config(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class EuriclesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Euricles — Buscador de Empleo Chile")
        self.resizable(False, False)
        _center_window(self, 520, 600)

        saved = _load_gui_config()

        self.cargo_var      = ctk.StringVar(value=saved.get("cargo", ""))
        self.keywords_var   = ctk.StringVar(value=saved.get("keywords", ""))
        self.ciudad_var     = ctk.StringVar(value=saved.get("ciudad", "Santiago"))
        self.modalidad_var  = ctk.StringVar(value=saved.get("modalidad", "Cualquiera"))
        self.dark_mode      = ctk.BooleanVar(value=saved.get("dark_mode", False))
        self.portal_vars    = {
            k: ctk.BooleanVar(value=saved.get("portals", {}).get(k, (k != "linkedin")))
            for k in PORTALS_LABELS
        }
        self._cancel_event  = threading.Event()
        self._progress_bars = {}
        self._results       = {}
        self._current_frame = None
        self._search_thread = None

        self._apply_theme()
        self._show_step1()

    def _apply_theme(self):
        mode = "dark" if self.dark_mode.get() else "light"
        ctk.set_appearance_mode(mode)

    # ── helpers ───────────────────────────────────────────────────

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

    # ── Step 1: search form ───────────────────────────────────────

    def _show_step1(self):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)
        self._steps_bar(f, 1)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="¿Qué trabajo buscas?",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=["#1e293b", "#e2e8f0"]).pack(anchor="w", pady=(8, 16))

        ctk.CTkLabel(body, text="Cargo o área",
                     font=ctk.CTkFont(size=12), text_color=["#64748b", "#94a3b8"]).pack(anchor="w")
        ctk.CTkEntry(body, textvariable=self.cargo_var, height=38,
                     placeholder_text="ej: Asistente administrativo",
                     border_color="#bbf7d0", fg_color=["#f0fdf4", "#1e293b"]).pack(fill="x", pady=(2, 6))
        self.cargo_var.trace_add("write", lambda *_: self._save_config())

        ctk.CTkLabel(body, text="Palabras clave adicionales (separadas por coma)",
                     font=ctk.CTkFont(size=12), text_color=["#64748b", "#94a3b8"]).pack(anchor="w")
        ctk.CTkEntry(body, textvariable=self.keywords_var, height=38,
                     placeholder_text="ej: Power BI, facturación, SAP",
                     border_color="#bbf7d0", fg_color=["#f0fdf4", "#1e293b"]).pack(fill="x", pady=(2, 6))
        self.keywords_var.trace_add("write", lambda *_: self._save_config())

        ctk.CTkLabel(body, text="Ciudad",
                     font=ctk.CTkFont(size=12), text_color=["#64748b", "#94a3b8"]).pack(anchor="w")
        ctk.CTkEntry(body, textvariable=self.ciudad_var, height=38,
                     border_color="#bbf7d0", fg_color=["#f0fdf4", "#1e293b"]).pack(fill="x", pady=(2, 6))
        self.ciudad_var.trace_add("write", lambda *_: self._save_config())

        ctk.CTkLabel(body, text="Modalidad",
                     font=ctk.CTkFont(size=12), text_color=["#64748b", "#94a3b8"]).pack(anchor="w")
        modalidad_menu = ctk.CTkOptionMenu(
            body, values=MODALITIES, variable=self.modalidad_var,
            fg_color=["#f0fdf4", "#1e293b"], button_color="#16a34a",
            button_hover_color="#15803d",
            text_color=["#1e293b", "#e2e8f0"],
            dropdown_text_color=["#1e293b", "#e2e8f0"],
            dropdown_fg_color=["white", "#1e293b"],
            dropdown_hover_color="#bbf7d0",
        )
        modalidad_menu.pack(fill="x", pady=(2, 6))
        modalidad_menu.set(self.modalidad_var.get())
        self.modalidad_var.trace_add("write", lambda *_: self._save_config())

        theme_row = ctk.CTkFrame(body, fg_color="transparent")
        theme_row.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(theme_row, text="Modo oscuro",
                     font=ctk.CTkFont(size=12), text_color=["#64748b", "#94a3b8"]).pack(side="left")
        ctk.CTkSwitch(theme_row, variable=self.dark_mode, text="",
                      fg_color="#cbd5e1", progress_color="#16a34a",
                      command=self._toggle_theme).pack(side="right")

        btn = ctk.CTkButton(
            body, text="Siguiente →", height=42,
            fg_color="#16a34a", hover_color="#15803d",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._show_step2,
        )
        btn.pack(fill="x", pady=(20, 0))

        def _check(*_):
            btn.configure(state="normal" if self.cargo_var.get().strip() else "disabled")
        self.cargo_var.trace_add("write", _check)
        _check()

    def _toggle_theme(self):
        self._apply_theme()
        self._save_config()
        self._show_step1()

    def _save_config(self):
        data = {
            "cargo": self.cargo_var.get(),
            "keywords": self.keywords_var.get(),
            "ciudad": self.ciudad_var.get(),
            "modalidad": self.modalidad_var.get(),
            "dark_mode": self.dark_mode.get(),
            "portals": {k: v.get() for k, v in self.portal_vars.items()},
        }
        _save_gui_config(data)

    # ── Step 2: portal selection ──────────────────────────────────

    def _show_step2(self):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)
        self._steps_bar(f, 2)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="¿Dónde buscamos?",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=["#1e293b", "#e2e8f0"]).pack(anchor="w", pady=(8, 4))
        ctk.CTkLabel(body, text="Selecciona los portales donde buscar:",
                     font=ctk.CTkFont(size=12), text_color=["#64748b", "#94a3b8"]).pack(anchor="w", pady=(0, 12))

        for key, label in PORTALS_LABELS.items():
            row = ctk.CTkFrame(body, fg_color=["#f0fdf4", "#1e293b"], corner_radius=8,
                               border_width=1, border_color="#bbf7d0")
            row.pack(fill="x", pady=4)
            cb = ctk.CTkCheckBox(
                row, text=label, variable=self.portal_vars[key],
                checkmark_color="white", fg_color="#16a34a",
                hover_color="#15803d", font=ctk.CTkFont(size=12),
                text_color=["#1e293b", "#e2e8f0"],
                command=self._save_config,
            )
            cb.pack(anchor="w", padx=12, pady=8)

        ctk.CTkLabel(body,
                     text="⚠  LinkedIn puede fallar por protecciones anti-bot",
                     font=ctk.CTkFont(size=10), text_color="#f59e0b").pack(anchor="w", pady=(4, 0))

        nav = ctk.CTkFrame(body, fg_color="transparent")
        nav.pack(fill="x", pady=(20, 0))
        ctk.CTkButton(nav, text="← Atrás", width=100, height=38,
                      fg_color=["#f1f5f9", "#334155"], text_color=["#64748b", "#94a3b8"],
                      hover_color=["#e2e8f0", "#475569"],
                      command=self._show_step1).pack(side="left")
        ctk.CTkButton(nav, text="Buscar trabajo 🔍", height=38,
                      fg_color="#16a34a", hover_color="#15803d",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._start_search).pack(side="right", fill="x",
                                                       expand=True, padx=(8, 0))

    # ── Step 3: progress ──────────────────────────────────────────

    def _show_step3(self, selected_keys: list):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="🔍", font=ctk.CTkFont(size=36)).pack(pady=(20, 4))
        ctk.CTkLabel(body, text="Buscando ofertas...",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=["#1e293b", "#e2e8f0"]).pack()
        ctk.CTkLabel(body,
                     text=f"Cargo: {self.cargo_var.get()}  ·  {self.ciudad_var.get()}",
                     font=ctk.CTkFont(size=11), text_color=["#64748b", "#94a3b8"]).pack(pady=(2, 16))

        ctk.CTkLabel(body, text="Progreso global",
                     font=ctk.CTkFont(size=11), text_color=["#475569", "#94a3b8"]).pack(anchor="w")
        self._global_bar = ctk.CTkProgressBar(body, height=10, fg_color="#e2e8f0",
                                               progress_color="#16a34a")
        self._global_bar.set(0)
        self._global_bar.pack(fill="x", pady=(0, 12))

        self._progress_bars = {}
        for key in selected_keys:
            label = PORTALS_LABELS[key]
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, width=160, anchor="w",
                         font=ctk.CTkFont(size=11),
                         text_color=["#475569", "#94a3b8"]).pack(side="left")
            bar = ctk.CTkProgressBar(row, height=8, fg_color="#e2e8f0",
                                     progress_color="#16a34a")
            bar.set(0)
            bar.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self._progress_bars[key] = bar

        cancel_row = ctk.CTkFrame(body, fg_color="transparent")
        cancel_row.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(cancel_row, text="⏳  No cierres esta ventana",
                     font=ctk.CTkFont(size=11), text_color="#f59e0b").pack(side="left")
        self._cancel_btn = ctk.CTkButton(cancel_row, text="✕ Cancelar", width=100, height=32,
                                          fg_color="#ef4444", hover_color="#dc2626",
                                          font=ctk.CTkFont(size=11, weight="bold"),
                                          command=self._cancel_search)
        self._cancel_btn.pack(side="right")

    def _cancel_search(self):
        self._cancel_event.set()
        self._cancel_btn.configure(text="Cancelando...", state="disabled")

    # ── search execution ──────────────────────────────────────────

    def _start_search(self):
        if not check_connectivity():
            self._show_error("Sin conexión a Internet", "Verifica tu red e intenta de nuevo.")
            return

        selected = [k for k, v in self.portal_vars.items() if v.get()]
        if not selected:
            return
        self._cancel_event.clear()
        self._results = {}
        self._show_step3(selected)
        self._total_portals = len(selected)
        self._completed_portals = 0

        cargo = self.cargo_var.get().strip()
        extra = [kw.strip() for kw in self.keywords_var.get().split(",") if kw.strip()]
        keywords = [cargo] + extra

        profile = {
            "name":     cargo,
            "keywords": keywords,
            "location": self.ciudad_var.get().strip() or "Chile",
            "modality": "" if self.modalidad_var.get() == "Cualquiera"
                        else self.modalidad_var.get().lower(),
        }
        self._search_thread = threading.Thread(
            target=self._search_worker, args=(selected, profile), daemon=True
        )
        self._search_thread.start()

    def _search_worker(self, selected_keys: list, profile: dict):
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._scrape_one, key, profile): key
                for key in selected_keys
            }
            for future in as_completed(futures):
                if self._cancel_event.is_set():
                    break
                key = futures[future]
                portal_name, jobs = future.result()
                self._results[portal_name] = jobs
                self._completed_portals += 1
                self.after(0, lambda k=key: self._on_portal_done(k))
        if self._cancel_event.is_set():
            self.after(0, self._show_cancelled)
        else:
            self.after(0, lambda: self._show_results(self._results))

    def _scrape_one(self, key: str, profile: dict) -> tuple:
        scraper = SCRAPER_REGISTRY[key]()
        try:
            jobs = scraper.search(profile, max_results=20, cancel_event=self._cancel_event)
        except Exception as e:
            logger = __import__("logging").getLogger(__name__)
            logger.error("[%s] Error: %s", key, e)
            jobs = []
        return scraper.portal_name, jobs

    def _on_portal_done(self, key: str):
        if key in self._progress_bars:
            self._progress_bars[key].set(1)
        if self._total_portals > 0:
            self._global_bar.set(self._completed_portals / self._total_portals)

    def _show_error(self, title: str, message: str):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("350x130")
        win.grab_set()
        _center_window(win, 350, 130)
        ctk.CTkLabel(win, text=f"⚠  {message}",
                     font=ctk.CTkFont(size=12)).pack(pady=24)
        ctk.CTkButton(win, text="Cerrar", command=win.destroy,
                      fg_color="#16a34a").pack()

    # ── Step 4: results ───────────────────────────────────────────

    def _show_cancelled(self):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        f.pack(fill="both", expand=True)
        self._current_frame = f

        self._header(f)

        body = ctk.CTkFrame(f, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=32)

        ctk.CTkLabel(body, text="⏹", font=ctk.CTkFont(size=36)).pack(pady=(40, 8))
        ctk.CTkLabel(body, text="Búsqueda cancelada",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=["#1e293b", "#e2e8f0"]).pack()
        found = sum(len(j) for j in self._results.values())
        ctk.CTkLabel(body, text=f"{found} oferta(s) encontrada(s) antes de cancelar",
                     font=ctk.CTkFont(size=12),
                     text_color=["#64748b", "#94a3b8"]).pack(pady=(4, 20))

        ctk.CTkButton(body, text="🔄  Nueva búsqueda", height=38,
                      fg_color="#16a34a", hover_color="#15803d",
                      command=self._show_step1).pack()

    def _show_results(self, results: dict):
        self._clear()
        f = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
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

        scroll = ctk.CTkScrollableFrame(f, fg_color=["#f8fafc", "#0f172a"])
        scroll.pack(fill="both", expand=True)

        if total == 0:
            ctk.CTkLabel(scroll,
                         text="No se encontraron ofertas.\nIntenta con otras palabras clave.",
                         font=ctk.CTkFont(size=13),
                         text_color=["#94a3b8", "#64748b"]).pack(pady=40)
        else:
            for portal_name, jobs in results.items():
                if not jobs:
                    continue
                ctk.CTkLabel(scroll, text=f"  {portal_name}",
                             font=ctk.CTkFont(size=11, weight="bold"),
                             text_color="#16a34a").pack(anchor="w", pady=(10, 2), padx=8)
                for job in jobs:
                    self._job_card(scroll, job)

        btns = ctk.CTkFrame(f, fg_color=["#f0fdf4", "#1e293b"], corner_radius=0, height=54)
        btns.pack(fill="x", side="bottom")
        btns.pack_propagate(False)
        ctk.CTkButton(btns, text="💾  Guardar .txt", height=34,
                      fg_color="#16a34a", hover_color="#15803d",
                      command=lambda: self._save_txt(results)).pack(side="left", padx=(12, 4), pady=10)
        ctk.CTkButton(btns, text="📊  Guardar .csv", height=34,
                      fg_color="#2563eb", hover_color="#1d4ed8",
                      command=lambda: self._save_csv(results)).pack(side="left", padx=4, pady=10)
        ctk.CTkButton(btns, text="🔄  Nueva búsqueda", height=34,
                      fg_color="transparent", border_width=1,
                      border_color="#16a34a", text_color="#16a34a",
                      hover_color=["#f0fdf4", "#1e293b"],
                      command=self._show_step1).pack(side="right", padx=12, pady=10)

    def _job_card(self, parent, job: dict):
        card = ctk.CTkFrame(parent, fg_color=["white", "#1e293b"], corner_radius=8,
                            border_width=1, border_color=["#e2e8f0", "#334155"])
        card.pack(fill="x", padx=8, pady=3)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=6)
        ctk.CTkLabel(inner, text=job["title"], anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=["#1e293b", "#e2e8f0"]).pack(anchor="w")
        ctk.CTkLabel(inner,
                     text=f"{job['company']}  ·  {job['location']}  ·  {job['date']}",
                     anchor="w", font=ctk.CTkFont(size=10),
                     text_color=["#64748b", "#94a3b8"]).pack(anchor="w")
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
        self._show_saved_dialog()

    def _save_csv(self, results: dict):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
            initialfile="euricles_resultados.csv",
            title="Guardar como CSV",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Portal", "Título", "Empresa", "Ubicación", "Fecha", "URL"])
                for portal_name, jobs in results.items():
                    for job in jobs:
                        writer.writerow([
                            portal_name,
                            job.get("title", ""),
                            job.get("company", ""),
                            job.get("location", ""),
                            job.get("date", ""),
                            job.get("url", ""),
                        ])
            self._show_saved_dialog()
        except Exception as e:
            self._show_error("Error", f"No se pudo guardar el CSV: {e}")

    def _show_saved_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Guardado")
        win.geometry("300x110")
        win.grab_set()
        _center_window(win, 300, 110)
        ctk.CTkLabel(win, text="✅  Archivo guardado correctamente",
                     font=ctk.CTkFont(size=13)).pack(pady=20)
        ctk.CTkButton(win, text="Cerrar", command=win.destroy,
                      fg_color="#16a34a").pack()


def launch():
    app = EuriclesApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
