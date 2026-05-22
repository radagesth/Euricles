<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/radagesth/Euricles/main/euricles.ico">
  <img align="right" width="80" height="80" src="https://raw.githubusercontent.com/radagesth/Euricles/main/euricles.ico">
</picture>

# 🌿 Euricles — Buscador de Empleo Chile

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)](https://windows.com)

Euricles es un buscador automatizado de ofertas de empleo en Chile. Consulta múltiples portales de trabajo simultáneamente, filtra por cargo, ubicación y modalidad, y genera reportes organizados en formato TXT y CSV.

---

## ✨ Características

| | Funcionalidad |
|---|---|
| 🔍 | **Búsqueda en 4 portales**: [Computrabajo.cl](https://cl.computrabajo.com), [Trabajando.cl](https://www.trabajando.cl), [Laborum.cl](https://www.laborum.cl), [LinkedIn](https://www.linkedin.com) |
| 🖥️ | **Interfaz gráfica** moderna con CustomTkinter (modo claro/oscuro) |
| ⌨️ | **CLI** para automatización y scripts |
| 📄 | **Exportación TXT y CSV** (compatible con Excel) |
| 🎯 | **Múltiples palabras clave** y perfiles de búsqueda |
| 🌍 | **Filtro por ubicación** (ciudad o región) |
| 🏢 | **Filtro por modalidad** (remoto, presencial, híbrido) |
| ⚡ | **Búsqueda paralela** en todos los portales |
| 💾 | **Caché inteligente** (evita requests repetidos) |
| 🔌 | **Verificación de conectividad** antes de buscar |
| 📝 | **Logging a archivo** en `~/.euricles/logs/` |
| ⏹️ | **Cancelación** de búsqueda en curso |
| 🎨 | **Icono propio** multiresolución |
| 📦 | **Instalador** PowerShell y script Inno Setup |
| ✉️ | **Envío por correo** de resultados con CSV adjunto (SMTP) |

---

## 📦 Instalación

### Opción 1: Portable (recomendado)

```powershell
# Compila y genera carpeta portable
python build.py --portable

# Ejecuta directamente
.\Euricles_Portable\Euricles.exe
```

### Opción 2: Instalación completa

```powershell
# Compila, copia a %LOCALAPPDATA%\Euricles y crea accesos directos
.\install.ps1
```

### Opción 3: Instalador Windows (.exe)

Genera un instalador profesional con Inno Setup (descarga automática):

```powershell
# Opcion A: Script PowerShell (descarga Inno Setup automaticamente)
.\build_installer.ps1

# Opcion B: Via build.py (si Inno Setup ya esta instalado)
python build.py --installer

# El instalador se genera en: installer/Euricles_Installer_v1.0.0.exe
```

Distribuye ese `.exe` en cualquier PC con Windows. El instalador:
- No requiere Python ni dependencias externas
- Pregunta la carpeta de instalación
- Crea accesos directos en escritorio y menú Inicio
- Configura correo y ciudad predeterminados
- Incluye desinstalador limpio (elimina datos de usuario si se solicita)

### Opción 4: Desde código fuente

```bash
pip install -r requirements.txt
playwright install chromium      # necesario solo para LinkedIn
python gui.pyw                   # interfaz gráfica
# o
python euricles.py               # línea de comandos
```

---

## 🚀 Uso Rápido

### Interfaz Gráfica

```bash
python gui.pyw
```

1. **Paso 1**: Ingresa el cargo, palabras clave adicionales, ciudad y modalidad
2. **Paso 2**: Selecciona los portales a consultar
3. **Paso 3**: Visualiza el progreso en tiempo real
4. **Paso 4**: Revisa los resultados y guarda en TXT o CSV

### Línea de Comandos

```bash
python euricles.py
```

Los perfiles de búsqueda se configuran en `config.py`:

```python
SEARCH_PROFILES = [
    {
        "name": "Asistente administrativo",
        "keywords": ["Asistente", "administrativo", "Facturación"],
        "location": "Santiago",
        "modality": "cualquiera",
    },
]
```

---

## 🏗️ Estructura del Proyecto

```
euricles/
├── euricles.py              # CLI principal
├── gui.pyw                  # Lanzador GUI
├── gui_app.py               # Interfaz gráfica (CustomTkinter)
├── config.py                # Configuración de búsqueda
├── report.py                # Generación de reportes TXT/CSV
├── build.py                 # Sistema de build
├── build_icon.py            # Generador de icono
├── install.ps1              # Instalador PowerShell
├── installer.iss            # Script Inno Setup
├── requirements.txt         # Dependencias
├── euricles.ico             # Icono multiresolución
├── scrapers/
│   ├── base.py              # Clase base con caché, rate limiting, conectividad
│   ├── computrabajo.py      # Scraper Computrabajo.cl
│   ├── trabajando.py        # Scraper Trabajando.cl
│   ├── laborum.py           # Scraper Laborum.cl
│   └── linkedin.py          # Scraper LinkedIn (Playwright)
└── tests/
    ├── test_base.py         # Tests de utilidades base
    ├── test_config.py       # Tests de configuración
    ├── test_linkedin.py     # Tests scraper LinkedIn
    └── test_report.py       # Tests de generación de reportes
```

---

## 🧪 Tests

```bash
python -m pytest tests/ -v
```

---

## ⚙️ Configuración

Edita `config.py` para personalizar:

| Variable | Descripción | Default |
|---|---|---|
| `SEARCH_PROFILES` | Perfiles de búsqueda (nombre, keywords, ubicación, modalidad) | — |
| `PORTALS` | Portales habilitados/deshabilitados | Todos activos |
| `MAX_RESULTS_PER_PORTAL` | Máximo de resultados por portal/perfil | 20 |
| `CACHE_ENABLED` | Activar caché de respuestas | True |
| `CACHE_TTL_HOURS` | Tiempo de vida del caché | 6 horas |
| `SMTP_HOST` | Servidor SMTP para envío de correo | smtp.gmail.com |
| `SMTP_PORT` | Puerto SMTP | 587 |
| `SMTP_USER` | Usuario SMTP (o variable `EURICLES_SMTP_USER`) | — |
| `SMTP_PASSWORD` | Contraseña SMTP (o variable `EURICLES_SMTP_PASSWORD`) | — |

La configuración de la GUI se persiste automáticamente en `~/.euricles/gui_config.json`.

---

## ⚠️ Limitaciones conocidas

- **LinkedIn**: Requiere `playwright install chromium` y puede fallar por protecciones anti-bot (modo *best-effort*)
- **Trabajando.cl / Laborum.cl**: Dependen del HTML estático; si los sitios cambian su estructura, los selectores CSS pueden quedar obsoletos
- **Cloudflare**: Algunos sitios pueden bloquear el scraping automatizado

---

## 📄 Licencia

MIT
