import logging
import urllib.parse
from .base import BaseScraper

logger = logging.getLogger(__name__)


class TrabajandoScraper(BaseScraper):
    portal_name = "TRABAJANDO.CL"
    base_url = "https://www.trabajando.cl"
    use_cloudscraper = False
    best_effort = True

    def _search_keyword(self, keyword: str, location: str, limit: int) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            logger.error("[TRABAJANDO] playwright no instalado. pip install playwright && playwright install chromium")
            return []

        keyword_slug = urllib.parse.quote(keyword.replace(" ", "-").lower())
        url = f"{self.base_url}/trabajo-empleo/{keyword_slug}"

        logger.info("[TRABAJANDO] Buscando (best-effort): %s en %s", keyword, location or "Chile")
        jobs = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="es-CL",
                    viewport={"width": 1920, "height": 1080},
                )
                page = context.new_page()

                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)

                    cards = page.query_selector_all("div.result-box")
                    if not cards:
                        cards = page.query_selector_all("a[href*='/trabajo-empleo/']")

                    for card in cards[:limit]:
                        try:
                            lines = [l.strip() for l in card.inner_text().split("\n") if l.strip()]

                            link_el = card.query_selector("a[href*='/trabajo/']")
                            if not link_el:
                                link_el = card.query_selector("a[href]")
                            href = link_el.get_attribute("href") if link_el else ""
                            full_url = href if href.startswith("http") else f"{self.base_url}{href}"

                            title = ""
                            company = ""
                            location_text = location
                            date_text = ""

                            for i, line in enumerate(lines):
                                if line.startswith("Hace ") and not title:
                                    date_text = line
                                elif i < len(lines) - 1 and lines[i + 1] in lines and not title:
                                    continue

                            if lines:
                                date_text = lines[0] if lines[0].startswith("Hace ") else ""
                                title = lines[1] if len(lines) > 1 else ""
                                company = lines[2] if len(lines) > 2 else ""
                                location_text = lines[3] if len(lines) > 3 else location

                            if not title:
                                title_el = card.query_selector("h2 a, h2, h3 a, h3")
                                title = title_el.inner_text().strip() if title_el else ""

                            if title:
                                jobs.append(self._make_job(title, company, location_text, date_text, full_url))
                        except Exception as e:
                            logger.debug("[TRABAJANDO] Error parseando oferta: %s", e)

                except PlaywrightTimeout:
                    logger.warning("[TRABAJANDO] Timeout al cargar '%s'", keyword)
                except Exception as e:
                    logger.warning("[TRABAJANDO] Error de navegacion: %s", e)

                browser.close()

        except Exception as e:
            logger.warning("[TRABAJANDO] Error inesperado (best-effort): %s", e)

        if not jobs:
            logger.warning("[TRABAJANDO] Sin resultados para '%s'.", keyword)

        return jobs
