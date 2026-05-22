# ============================================================
#  EURICLES — Configuración de búsqueda
#  Edita este archivo para personalizar tus búsquedas de empleo
# ============================================================

SEARCH_PROFILES = [
    {
        "name": "Asistente administrativo",
        "keywords": ["Asistente", "administrativo", "Facturación"],
        "location": "Santiago",
        "modality": "cualquiera",
    },
    {
        "name": "Administrative Assistant",
        "keywords": ["Reports", "Invoicing & Billing", "power bi"],
        "location": "Chile",
        "modality": "",
    },
]

PORTALS = {
    "computrabajo": True,
    "trabajando": True,
    "laborum": True,
    "linkedin": True,
}

MAX_RESULTS_PER_PORTAL = 20
OUTPUT_DIR = "output"
REQUEST_DELAY = 1.5
RETRIES = 3
TIMEOUT = 20
CACHE_ENABLED = True
CACHE_TTL_HOURS = 6

# Configuración SMTP para envío de resultados por correo
# Euricles usará estas credenciales para enviar los reportes.
# Para Gmail usa una contraseña de aplicación (no la normal):
#   https://myaccount.google.com/apppasswords
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""        # o define variable de entorno EURICLES_SMTP_USER
SMTP_PASSWORD = ""    # o define variable de entorno EURICLES_SMTP_PASSWORD
