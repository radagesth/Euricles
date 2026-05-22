# Euricles GUI — Especificación de Diseño

**Fecha:** 2026-05-15  
**Estado:** Aprobado

---

## Contexto

Euricles es un bot de búsqueda de empleo en Chile que actualmente se ejecuta por terminal. El objetivo de esta GUI es que cualquier persona, sin conocimientos de programación, pueda lanzar búsquedas, ver resultados y guardar el reporte `.txt` — todo desde una ventana de escritorio con doble clic.

---

## Decisiones de diseño

| Decisión | Elección |
|---|---|
| Estilo visual | Asistente paso a paso (wizard), tema verde |
| Resultados | Dentro de la app, con links clickeables |
| Ubicación del archivo | `euricles/gui.pyw` (misma carpeta que todo) |
| Tecnología | CustomTkinter (Python, aspecto moderno) |
| Lanzamiento | Doble clic en `gui.pyw` — sin consola negra |

---

## Flujo de pantallas

```
[Paso 1: ¿Qué buscas?]
  → Cargo / área de trabajo (campo de texto)
  → Ciudad (campo de texto, default "Santiago")
  → Modalidad (dropdown: Cualquiera / Remoto / Presencial / Híbrido)
  → Botón "Siguiente →"

[Paso 2: ¿Dónde buscamos?]
  → Checkboxes por portal:
      ☑ Computrabajo.cl
      ☑ Trabajando.cl
      ☑ Laborum.cl
      ☐ LinkedIn (etiqueta "opcional — puede fallar")
  → Botones "← Atrás" / "Siguiente →"

[Paso 3: Buscando...]
  → Ícono animado de búsqueda
  → Barra de progreso por portal (nombre + % completado)
  → Aviso "No cierres la ventana ⏳"
  → (sin botones — transición automática al terminar)

[Resultados]
  → Banner verde: "✅ ¡Listo! XX ofertas encontradas"
  → Chips con conteo por portal: "Computrabajo 18 | Trabajando 12 | Laborum 17"
  → Lista scrolleable de ofertas:
      - Título | Empresa | Ubicación | Fecha
      - Link "🔗 Ver oferta" (abre en navegador)
  → Botón "💾 Guardar .txt" (abre diálogo de guardar)
  → Botón "🔄 Nueva búsqueda" (vuelve al Paso 1)
```

---

## Arquitectura

```
euricles/
├── gui.pyw          ← entry point GUI (sin consola al hacer doble clic)
├── gui_app.py       ← lógica de la aplicación CustomTkinter
├── euricles.py      ← bot existente (sin cambios)
├── config.py        ← configuración existente (sin cambios)
├── report.py        ← reporte existente (sin cambios)
└── scrapers/        ← scrapers existentes (sin cambios)
```

**`gui.pyw`** — solo importa y lanza `gui_app.py`. La extensión `.pyw` evita la consola negra en Windows.

**`gui_app.py`** — clase `EuriclesApp(ctk.CTk)` con:
- `show_step(n)` — renderiza el paso indicado destruyendo el frame anterior
- `run_search()` — ejecuta los scrapers en un `threading.Thread` (no bloquea la UI)
- `update_progress(portal, pct)` — callback thread-safe via `after()` para actualizar barras
- `show_results(results)` — renderiza las cards de resultados con links

---

## Comportamiento de hilos

Los scrapers son bloqueantes (requests HTTP). Se ejecutan en un hilo separado para que la UI no se congele. Comunicación con la UI exclusivamente via `widget.after(0, callback)` — nunca llamadas directas desde el hilo worker.

---

## Requisitos adicionales

- Sin errores visibles al usuario en terminal — todos los errores se muestran dentro de la app como mensajes amigables
- Si un portal no devuelve resultados, se muestra "Sin resultados para este portal" en su sección
- El campo "Cargo" no puede estar vacío — botón Siguiente deshabilitado hasta que tenga texto
- Al abrir la app, los campos empiezan vacíos — el usuario escribe su búsqueda directamente (la GUI no depende de `config.py`)

---

## Dependencia nueva

```
customtkinter>=5.2.0
```

Un solo `pip install customtkinter` — sin Playwright adicional, Chromium ya instalado.
