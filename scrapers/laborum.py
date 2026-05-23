import logging
import urllib.parse
from .base import BaseScraper

logger = logging.getLogger(__name__)


class LaborumScraper(BaseScraper):
    portal_name = "LABORUM.CL"
    base_url = "https://www.laborum.cl"
    use_cloudscraper = False
    best_effort = True
    use_playwright = True

    def _search_keyword_playwright(self, page, keyword: str, location: str,
                                    limit: int, cancel_event=None) -> list[dict]:
        keyword_encoded = urllib.parse.quote_plus(keyword)
        location_encoded = urllib.parse.quote_plus(location) if location else ""

        url = f"{self.base_url}/empleos?q={keyword_encoded}"
        if location_encoded:
            url += f"&l={location_encoded}"

        logger.info("[LABORUM] Buscando (best-effort): %s en %s", keyword, location or "Chile")
        jobs = []

        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeout

            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            for _ in range(3):
                if cancel_event and cancel_event.is_set():
                    return jobs
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

            if cancel_event and cancel_event.is_set():
                return jobs

            cards = page.query_selector_all(
                "div.aviso, article.aviso, div.job-listing, "
                "li[class*='aviso'], div[class*='aviso'], article[class*='job'], "
                "div[class*='job-card'], div[class*='result-item']"
            )
            if not cards:
                cards = page.query_selector_all("a[href*='/empleos/'], a[href*='/aviso/']")

            for card in cards[:limit]:
                if cancel_event and cancel_event.is_set():
                    break
                try:
                    title_el = card.query_selector(
                        "h2, h3, a.title, .job-title, [class*='titulo'], "
                        "[class*='title'], a[href*='/aviso/']"
                    )
                    title = title_el.inner_text().strip() if title_el else ""

                    link_el = card.query_selector("a[href]")
                    href = link_el.get_attribute("href") if link_el else ""
                    full_url = href if href.startswith("http") else f"{self.base_url}{href}"

                    company_el = card.query_selector(
                        ".empresa, .company-name, [class*='empresa'], [class*='company'], "
                        "[class*='employer']"
                    )
                    company = company_el.inner_text().strip() if company_el else ""

                    location_el = card.query_selector(
                        ".location, .ciudad, [class*='location'], [class*='ciudad'], "
                        "[class*='ubicacion']"
                    )
                    loc = location_el.inner_text().strip() if location_el else location

                    date_el = card.query_selector(
                        "time, .fecha, .date, [class*='fecha'], [class*='date']"
                    )
                    date = date_el.inner_text().strip() if date_el else ""
                    if date_el and date_el.get_attribute("datetime"):
                        date = date_el.get_attribute("datetime")

                    if title and full_url:
                        jobs.append(self._make_job(title, company, loc, date, full_url))
                except Exception as e:
                    logger.debug("[LABORUM] Error parseando oferta: %s", e)

        except PlaywrightTimeout:
            logger.warning("[LABORUM] Timeout al cargar '%s'", keyword)
        except Exception as e:
            logger.warning("[LABORUM] Error de navegacion: %s", e)

        if not jobs:
            logger.warning("[LABORUM] Sin resultados para '%s'. El sitio usa JS intensivo.", keyword)

        return jobs
