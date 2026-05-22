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
