"""
Euricles — Bot de busqueda de empleo en Chile
==============================================
Uso:
  python euricles.py                          # Usa perfiles de config.py
  python euricles.py --server                 # Modo servidor (JSON + email)
  python euricles.py --profile "Asistente"    # Perfil especifico
  python euricles.py --json                   # Salida JSON adicional
  python euricles.py --silent                 # Sin banner
  python euricles.py --email usuario@mail.com # Envia resultados por correo

Modo servidor (para cron / Task Scheduler):
  set EURICLES_TO_EMAIL=user@mail.com
  python euricles.py --server --silent
"""

import sys
import io
import logging
import os
import json
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import config
import report
from scrapers import SCRAPER_REGISTRY
from scrapers.base import check_connectivity
from email_sender import send_report

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
       Bot de busqueda de empleo en Chile — by Euricles
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Euricles — Buscador de empleo automatizado para Chile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python euricles.py
  python euricles.py --profile "Asistente" --json --silent
  python euricles.py --server --email admin@empresa.cl
  python euricles.py --server --silent          # Para cron / Task Scheduler
        """,
    )
    parser.add_argument("--profile", "-p", type=str, nargs="*",
                        help="Nombre(s) de perfil(es) a ejecutar (default: todos)")
    parser.add_argument("--server", action="store_true",
                        help="Modo servidor: salida JSON + envia email si configurado")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Genera archivo JSON con resultados")
    parser.add_argument("--email", "-e", type=str, nargs="?",
                        const=os.environ.get("EURICLES_TO_EMAIL", ""),
                        help="Envia resultados por correo (default: $EURICLES_TO_EMAIL)")
    parser.add_argument("--output", "-o", type=str, default=config.OUTPUT_DIR,
                        help="Directorio de salida para reportes")
    parser.add_argument("--silent", "-s", action="store_true",
                        help="Suprime el banner de inicio")
    parser.add_argument("--max-results", type=int, default=config.MAX_RESULTS_PER_PORTAL,
                        help=f"Max resultados por portal (default: {config.MAX_RESULTS_PER_PORTAL})")
    return parser.parse_args()


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
    args = parse_args()

    if not args.silent:
        print(BANNER)

    if not check_connectivity():
        logger.error("No hay conexion a Internet. Verifica tu red.")
        sys.exit(1)
    logger.info("Conectividad verificada correctamente")

    # ── Filtrar perfiles ──
    profiles = config.SEARCH_PROFILES
    if args.profile:
        filtered = [p for p in profiles if p["name"] in args.profile]
        if not filtered:
            logger.error("Ningun perfil coincide con: %s", ", ".join(args.profile))
            logger.info("Perfiles disponibles: %s", ", ".join(p["name"] for p in profiles))
            sys.exit(1)
        profiles = filtered

    portals_enabled = {k: v for k, v in config.PORTALS.items() if v}
    max_results = args.max_results
    output_dir = args.output

    if not profiles:
        logger.error("No hay perfiles de busqueda definidos en config.py.")
        sys.exit(1)

    if not portals_enabled:
        logger.error("No hay portales habilitados en config.py.")
        sys.exit(1)

    logger.info("Perfiles: %d  |  Portales activos: %s", len(profiles), ", ".join(portals_enabled))
    logger.info("Max resultados por portal: %d", max_results)
    logger.info("Logs: %s", log_file)
    print()

    # ── Ejecutar busquedas ──
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
            logger.info("[%s] '%s' → %d oferta(s)", portal_name, profile_name, len(jobs))

    # ── Generar reporte ──
    print()
    logger.info("Generando reporte...")
    txt_path = report.generate(results_by_profile, output_dir)

    # ── JSON output ──
    if args.json_out or args.server:
        json_path = os.path.join(output_dir, f"euricles_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.json")
        os.makedirs(output_dir, exist_ok=True)
        flat = []
        for pname, portals in results_by_profile.items():
            for portal, jobs in portals.items():
                for job in jobs:
                    flat.append({
                        "profile": pname,
                        "portal": portal,
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "date": job.get("date", ""),
                        "url": job.get("url", ""),
                    })
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"generated_at": datetime.now().isoformat(), "results": flat}, f,
                      ensure_ascii=False, indent=2)
        logger.info("JSON guardado: %s", json_path)

    # ── Enviar por email ──
    to_email = args.email or os.environ.get("EURICLES_TO_EMAIL", "")
    if to_email:
        logger.info("Enviando resultados a %s...", to_email)
        total = sum(len(j) for p in results_by_profile.values() for j in p.values())
        subject = f"Euricles — {total} ofertas encontradas"
        lines = [f"Resultados Euricles - {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
        for pname, portals in results_by_profile.items():
            for portal, jobs in portals.items():
                lines.append(f"[{portal}] ({pname}) — {len(jobs)} oferta(s)")
                for j in jobs:
                    lines.append(f"  • {j['title']} | {j['company']} | {j['location']}")
                    if j.get("url"):
                        lines.append(f"    {j['url']}")
                lines.append("")
        body = "\n".join(lines)
        ok, msg = send_report(
            to_email=to_email,
            subject=subject,
            body=body,
            smtp_host=config.SMTP_HOST,
            smtp_port=config.SMTP_PORT,
            smtp_user=config.SMTP_USER or os.environ.get("EURICLES_SMTP_USER", ""),
            smtp_password=config.SMTP_PASSWORD or os.environ.get("EURICLES_SMTP_PASSWORD", ""),
        )
        if ok:
            logger.info("Correo enviado correctamente a %s", to_email)
        else:
            logger.warning("Error al enviar correo: %s", msg)

    total = sum(len(j) for p in results_by_profile.values() for j in p.values())
    print()
    print("-" * 66)
    print(f"  BUSQUEDA COMPLETADA")
    print(f"  Total de ofertas encontradas: {total}")
    print(f"  Reporte: {txt_path}")
    print(f"  Logs: {log_file}")
    print("-" * 66)
    print()


if __name__ == "__main__":
    main()
