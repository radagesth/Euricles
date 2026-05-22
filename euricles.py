"""
Euricles — Bot de búsqueda de empleo en Chile
Uso: python euricles.py
"""

import sys
import io
import logging
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import config
import report
from scrapers import SCRAPER_REGISTRY
from scrapers.base import check_connectivity

log_dir = Path.home() / ".euricles" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"euricles_{datetime.now().strftime('%Y-%m-%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(log_file), encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

BANNER = r"""
  ███████╗██╗   ██╗██████╗ ██╗ ██████╗██╗     ███████╗███████╗
  ██╔════╝██║   ██║██╔══██╗██║██╔════╝██║     ██╔════╝██╔════╝
  █████╗  ██║   ██║██████╔╝██║██║     ██║     █████╗  ███████╗
  ██╔══╝  ██║   ██║██╔══██╗██║██║     ██║     ██╔══╝  ╚════██║
  ███████╗╚██████╔╝██║  ██║██║╚██████╗███████╗███████╗███████║
  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝╚══════╝╚══════╝
       Bot de búsqueda de empleo en Chile — by Euricles
"""


def _run_scraper(scraper_key: str, profile: dict, max_results: int, cancel_event=None) -> tuple[str, str, list]:
    scraper_cls = SCRAPER_REGISTRY[scraper_key]
    scraper = scraper_cls()
    try:
        jobs = scraper.search(profile, max_results, cancel_event)
        return scraper.portal_name, profile["name"], jobs
    except Exception as e:
        logger.error("[%s] Error inesperado: %s", scraper_key, e)
        return SCRAPER_REGISTRY[scraper_key].portal_name, profile["name"], []


def main():
    print(BANNER)

    if not check_connectivity():
        logger.error("No hay conexión a Internet. Verifica tu red.")
        sys.exit(1)
    logger.info("Conectividad verificada correctamente")

    profiles = config.SEARCH_PROFILES
    portals_enabled = {k: v for k, v in config.PORTALS.items() if v}
    max_results = config.MAX_RESULTS_PER_PORTAL
    output_dir = config.OUTPUT_DIR

    if not profiles:
        logger.error("No hay perfiles de búsqueda definidos en config.py.")
        sys.exit(1)

    if not portals_enabled:
        logger.error("No hay portales habilitados en config.py.")
        sys.exit(1)

    logger.info("Perfiles: %d  |  Portales activos: %s", len(profiles), ", ".join(portals_enabled))
    logger.info("Máx. resultados por portal: %d", max_results)
    logger.info("Logs guardados en: %s", log_file)
    print()

    results_by_profile: dict[str, dict[str, list]] = {
        p["name"]: {SCRAPER_REGISTRY[k].portal_name: [] for k in portals_enabled}
        for p in profiles
    }

    tasks = [
        (scraper_key, profile)
        for profile in profiles
        for scraper_key in portals_enabled
    ]

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_map = {
            executor.submit(_run_scraper, scraper_key, profile, max_results): (scraper_key, profile["name"])
            for scraper_key, profile in tasks
        }

        for future in as_completed(future_map):
            portal_name, profile_name, jobs = future.result()
            results_by_profile[profile_name][portal_name] = jobs
            logger.info("✓ [%s] '%s' → %d oferta(s)", portal_name, profile_name, len(jobs))

    print()
    logger.info("Generando reporte...")
    output_path = report.generate(results_by_profile, output_dir)

    total = sum(
        len(jobs)
        for portal_results in results_by_profile.values()
        for jobs in portal_results.values()
    )

    print()
    print("─" * 66)
    print(f"  BÚSQUEDA COMPLETADA")
    print(f"  Total de ofertas encontradas: {total}")
    print(f"  Reporte guardado en: {output_path}")
    print(f"  Logs: {log_file}")
    print("─" * 66)
    print()


if __name__ == "__main__":
    main()
