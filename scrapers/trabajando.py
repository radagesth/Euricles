import logging
import urllib.parse
from .base import BaseScraper

logger = logging.getLogger(__name__)


class TrabajandoScraper(BaseScraper):
    portal_name = "TRABAJANDO.CL"
    base_url = "https://www.trabajando.cl"
    use_cloudscraper = False
    best_effort = True
    use_playwright = True

    def _search_keyword_playwright(self, page, keyword: str, location: str,
                                    limit: int, cancel_event=None) -> list[dict]:
        keyword_slug = urllib.parse.quote(keyword.replace(" ", "-").lower())
        url = f"{self.base_url}/trabajo-empleo/{keyword_slug}"

        logger.info("[TRABAJANDO] Buscando (best-effort): %s en %s", keyword, location or "Chile")
        jobs = []

        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeout

            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            if cancel_event and cancel_event.is_set():
                return jobs

            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            if cancel_event and cancel_event.is_set():
                return jobs

            cards = page.query_selector_all("div.result-box")
            if not cards:
                cards = page.query_selector_all("a[href*='/trabajo-empleo/']")

            for card in cards[:limit]:
                if cancel_event and cancel_event.is_set():
                    break
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

        if not jobs:
            logger.warning("[TRABAJANDO] Sin resultados para '%s'.", keyword)

        return jobs
