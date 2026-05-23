# Euricles — Manual de Instalacion y Funcionamiento

Euricles es un buscador automatizado de ofertas de empleo en Chile. Consulta
Computrabajo.cl, Trabajando.cl, Laborum.cl y LinkedIn simultaneamente, filtra
por cargo, ubicacion y modalidad, y genera reportes en TXT, CSV y JSON.

Este manual describe los **3 sub-productos** de distribucion:

1. [Version Servidor](#1-sub-producto-1-version-servidor) — headless, para
   servidores Windows/Linux, programable con cron o Task Scheduler
2. [Version Instalador Windows](#2-sub-producto-2-version-instalador-windows)
   — instalador EXE profesional con Inno Setup
3. [Version Stand Alone](#3-sub-producto-3-version-stand-alone-portable)
   — carpeta portable, listo para ejecutar sin instalacion

---

## 1. Sub-producto 1: Version Servidor

Disenada para ejecucion headless en servidores, contenedores o maquinas
virtuales. Soporta automatizacion via cron (Linux) o Task Scheduler (Windows)
y envio de resultados por correo electronico.

### 1.1 Requisitos del Servidor

| Requisito | Version minima |
|-----------|---------------|
| Python    | 3.10+ |
| Playwright | 1.40+ (con Chromium instalado) |
| SO        | Windows Server 2016+, Ubuntu 20.04+, Debian 11+, CentOS 8+ |
| RAM       | 512 MB minimo / 2 GB recomendado |
| Disco     | 500 MB libres |
| Red       | Conexion a internet (puertos 80/443) |

### 1.2 Instalacion en Servidor

```bash
# 1. Clonar repositorio
git clone https://github.com/radagesth/Euricles.git
cd Euricles

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
.venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar Chromium para Playwright
playwright install chromium
```

### 1.3 Configuracion

Editar `config.py` para definir los perfiles de busqueda y credenciales SMTP:

```python
# Perfiles de busqueda
SEARCH_PROFILES = [
    {
        "name": "Asistente administrativo",
        "keywords": ["Asistente", "administrativo", "Facturacion"],
        "location": "Santiago",
        "modality": "cualquiera",
    },
]

# SMTP para envio automatico de resultados
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "tu-correo@gmail.com"
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"   # App password de Gmail
```

O usar variables de entorno (recomendado para produccion):

```bash
export EURICLES_SMTP_USER="tu-correo@gmail.com"
export EURICLES_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"
export EURICLES_TO_EMAIL="destinatario@empresa.cl"
```

### 1.4 Modos de ejecucion

#### Ejecucion basica (todos los perfiles)

```bash
python euricles.py
```

#### Ejecucion con perfil especifico

```bash
python euricles.py --profile "Asistente administrativo"
python euricles.py --profile "Asistente" "Administrative"  # multiples
```

#### Modo servidor (JSON + email automatico)

```bash
python euricles.py --server --silent
```

#### Solo generar JSON

```bash
python euricles.py --json
```

#### Enviar resultados por correo

```bash
python euricles.py --email destinatario@empresa.cl
```

El destinatario tambien puede definirse via variable de entorno:

```bash
export EURICLES_TO_EMAIL="destinatario@empresa.cl"
python euricles.py --email    # Toma el valor de la variable
```

#### Personalizar directorio de salida

```bash
python euricles.py --output /var/reportes/euricles
```

#### Sin banner (para logs limpios)

```bash
python euricles.py --silent
```

### 1.5 Automatizacion (Programar ejecuciones)

#### Linux — cron

Editar crontab (`crontab -e`) para ejecutar diariamente:

```cron
# Todos los dias a las 8:00 AM
0 8 * * * cd /opt/euricles && .venv/bin/python euricles.py --server --silent >> /var/log/euricles.log 2>&1

# Cada 12 horas
0 */12 * * * cd /opt/euricles && .venv/bin/python euricles.py --server --silent
```

#### Windows — Task Scheduler

```powershell
# Crear tarea programada (diaria a las 8:00 AM)
$action = New-ScheduledTaskAction -Execute "C:\Euricles\.venv\Scripts\python.exe" `
    -Argument "euricles.py --server --silent" `
    -WorkingDirectory "C:\Euricles"
$trigger = New-ScheduledTaskTrigger -Daily -At 08:00
Register-ScheduledTask -TaskName "Euricles Daily Search" -Action $action -Trigger $trigger -RunLevel Highest
```

#### Docker (opcional)

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install playwright && playwright install chromium
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "euricles.py", "--server", "--silent"]
```

```bash
docker build -t euricles-server .
docker run -e EURICLES_SMTP_USER=... -e EURICLES_SMTP_PASSWORD=... euricles-server
```

### 1.6 Salidas generadas

| Formato | Archivo | Contenido |
|---------|---------|-----------|
| TXT     | `output/euricles_YYYY-MM-DD_HH-MM.txt` | Reporte legible con resumen por perfil y portal |
| CSV     | `output/euricles_YYYY-MM-DD_HH-MM.csv` | Columnas: Perfil, Portal, Titulo, Empresa, Ubicacion, Fecha, URL |
| JSON    | `output/euricles_YYYY-MM-DD_HH-MM.json` | Estructura: `{generated_at, results: [{profile, portal, title, ...}]}` |

### 1.7 Logs

Los logs se almacenan en `~/.euricles/logs/euricles_YYYY-MM-DD.log` con
rotacion diaria automatica.

```bash
tail -f ~/.euricles/logs/euricles_2026-05-23.log
```

---

## 2. Sub-producto 2: Version Instalador Windows

Instalador profesional generado con Inno Setup. Incluye el ejecutable
compilado con PyInstaller (autocontenido, no requiere Python). Crea accesos
directos en escritorio y menu Inicio, y ofrece desinstalador limpio.

### 2.1 Requisitos del Equipo

| Requisito | Detalle |
|-----------|---------|
| SO        | Windows 10/11, Windows Server 2016+ (64-bit) |
| RAM       | 1 GB minimo / 4 GB recomendado |
| Disco     | 200 MB libres |
| Red       | Conexion a internet para busquedas |
| Requisito adicional | Playwright Chromium se instala automaticamente en `%LOCALAPPDATA%\Euricles` |

### 2.2 Instalacion

1. Descargar `Euricles_Installer_v1.0.0.exe` desde
   [GitHub Releases](https://github.com/radagesth/Euricles/releases)
2. Ejecutar el instalador (clic derecho → "Ejecutar como administrador")
3. Seleccionar carpeta de instalacion (default: `%LOCALAPPDATA%\Euricles`)
4. Opcional: ingresar correo electronico y ciudad predeterminados
5. Elegir accesos directos deseados:
   - [x] Acceso directo en el escritorio
   - [x] Acceso directo en el menu Inicio
   - [ ] Ejecutar Euricles al iniciar Windows
6. Clic en "Instalar"
7. Opcional: marcar "Ejecutar Euricles ahora" y clic en "Finalizar"

### 2.3 Primer uso

1. Al abrir Euricles, se muestra la pantalla de busqueda (Paso 1)
2. Completar los campos:
   - **Cargo o area**: ej: "Asistente administrativo"
   - **Palabras clave adicionales**: ej: "Power BI, facturacion, SAP"
   - **Ciudad**: ej: "Santiago"
   - **Modalidad**: Cualquiera / Remoto / Presencial / Hibrido
   - **Correo** (opcional): para recibir resultados por email
3. Clic en "Siguiente"
4. Seleccionar portales a consultar (todos activados por defecto)
5. Clic en "Buscar trabajo"

### 2.4 Configuracion de Correo (Primer envio)

Al hacer clic en "Enviar por correo" sin credenciales configuradas:

1. Completar los campos del dialogo SMTP:
   - **Servidor SMTP**: `smtp.gmail.com` (default)
   - **Puerto**: `587` (default)
   - **Usuario**: tu direccion de correo
   - **Contrasena de aplicacion**: generada desde Google/GitHub/Outlook
   - [x] **Recordar configuracion**: guarda las credenciales localmente
2. Clic en "Enviar"

> **Importante**: Para Gmail, usar una **contrasena de aplicacion**
> (no la contrasena normal). Crear en: https://myaccount.google.com/apppasswords

### 2.5 Exportacion de resultados

| Formato | Boton | Descripcion |
|---------|-------|-------------|
| TXT     | 💾 Guardar .txt | Reporte con resumen por portal, incluye URLs |
| CSV     | 📊 Guardar .csv | Archivo compatible con Excel, columnas: Perfil, Portal, Titulo, Empresa, Ubicacion, Fecha, URL |
| Email   | ✉ Enviar por correo | Envia CSV adjunto via SMTP |

### 2.6 Personalizacion

La configuracion de la GUI (campos, portales seleccionados, modo oscuro,
credenciales SMTP) se persiste en `~/.euricles/gui_config.json`.

Para configurar credenciales SMTP de forma permanente antes de ejecutar
la GUI, editar `config.py` o definir las variables de entorno:

```
EURICLES_SMTP_USER=tu-correo@gmail.com
EURICLES_SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

### 2.7 Desinstalacion

1. Menu Inicio → Euricles → "Desinstalar Euricles"
2. O: Panel de control → Programas y características → Euricles → Desinstalar
3. Opcional: marcar "Eliminar datos de configuracion y cache"
4. Clic en "Si" para confirmar

---

## 3. Sub-producto 3: Version Stand Alone (Portable)

Version autocontenida en una carpeta. No requiere instalacion ni
modificacion del sistema. Ideal para USB, equipos compartidos o
pruebas rapidas.

### 3.1 Requisitos

| Requisito | Detalle |
|-----------|---------|
| SO        | Windows 10/11 64-bit |
| RAM       | 1 GB minimo |
| Disco     | 150 MB libres |
| Red       | Conexion a internet |
| Dependencias externas | Ninguna (todo incluido en `Euricles.exe`) |

### 3.2 Descarga

La version portable se distribuye como:

- **Carpeta**: `Euricles_Portable/` (72 MB)
  - `Euricles.exe` — ejecutable principal
  - `euricles.ico` — icono
- **Opcional**: `Euricles_Portable.rar` comprimido (~30 MB)

### 3.3 Uso

```powershell
# 1. Descargar y extraer Euricles_Portable.rar
# 2. Ejecutar directamente:
.\Euricles_Portable\Euricles.exe

# (Opcional) Crear acceso directo en escritorio:
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Euricles.lnk'); $SC.TargetPath = 'C:\ruta\Euricles_Portable\Euricles.exe'; $SC.WorkingDirectory = 'C:\ruta\Euricles_Portable'; $SC.IconLocation = 'C:\ruta\Euricles_Portable\euricles.ico,0'; $SC.Save()"
```

### 3.4 Para generar la version portable desde codigo fuente

```powershell
# Requiere Python 3.10+ y las dependencias instaladas
python build.py --portable

# Genera: Euricles_Portable/Euricles.exe + euricles.ico
```

### 3.5 Limpieza

Para eliminar la version portable, simplemente borrar la carpeta
`Euricles_Portable/` y el archivo `Euricles_Portable.rar` (si existe).

Los datos de configuracion y cache se almacenan en `~/.euricles/`.
Para eliminarlos: `rmdir /s /q %USERPROFILE%\.euricles`

---

## Apendice A: Comparativa de Sub-productos

| Caracteristica | Servidor | Instalador Windows | Stand Alone |
|---------------|----------|--------------------|-------------|
| Requiere Python | Si | No | No |
| Requiere instalacion | Clonar + pip | Si (instalador EXE) | No (extraer y ejecutar) |
| Interfaz grafica | No (headless) | Si (CustomTkinter) | Si (CustomTkinter) |
| CLI avanzado | Si | Limitado | Limitado |
| Programable (cron/Task Scheduler) | Si | Parcial (via CLI basico) | No |
| Envio automatico de email | Si | Manual (desde GUI) | Manual (desde GUI) |
| Salida JSON | Si | No | No |
| Tamaño en disco | ~200 MB (con Python) | ~73 MB | ~73 MB |
| Ideal para | Servidores, CI/CD, automatizacion | Usuarios domesticos | USB, equipos compartidos |
| Distribucion | Git clone / Docker | Instalador EXE | Carpeta comprimida |

## Apendice B: Variables de Entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `EURICLES_SMTP_USER` | Usuario SMTP para envio de correo | — |
| `EURICLES_SMTP_PASSWORD` | Contrasena de aplicacion SMTP | — |
| `EURICLES_TO_EMAIL` | Destinatario por defecto para `--email` | — |

## Apendice C: Solucion de Problemas

| Problema | Causa | Solucion |
|----------|-------|----------|
| LinkedIn devuelve 0 resultados | Anti-bot / sesion expirada | Ejecutar de nuevo; es modo best-effort |
| "Playwright no instalado" | Falta Chromium | `playwright install chromium` |
| Error SMTP "Authentication failed" | Contrasena normal (no app password) | Usar contrasena de aplicacion |
| El instalador no se abre | Bloqueado por Windows Defender | Clic derecho → "Ejecutar como administrador" |
| No se encuentran resultados | Selectores HTML obsoletos | Los scrapers necesitan actualizacion |
| Error "No se genero el ejecutable" | PyInstaller fallo | Verificar dependencias: `pip install -r requirements.txt` |
