import logging
import urllib.parse
from .base import BaseScraper

logger = logging.getLogger(__name__)


class LaborumScraper(BaseScraper):
    portal_name = "LABORUM.CL"
    base_url = "https://www.laborum.cl"
    use_cloudscraper = False
    best_effort = True

    def _search_keyword(self, keyword: str, location: str, limit: int) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            logger.error("[LABORUM] playwright no instalado. pip install playwright && playwright install chromium")
            return []

        keyword_encoded = urllib.parse.quote_plus(keyword)
        location_encoded = urllib.parse.quote_plus(location) if location else ""

        url = f"{self.base_url}/empleos?q={keyword_encoded}"
        if location_encoded:
            url += f"&l={location_encoded}"

        logger.info("[LABORUM] Buscando (best-effort): %s en %s", keyword, location or "Chile")
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

                    # Scroll for lazy loading
                    for _ in range(3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(2000)

                    cards = page.query_selector_all(
                        "div.aviso, article.aviso, div.job-listing, "
                        "li[class*='aviso'], div[class*='aviso'], article[class*='job'], "
                        "div[class*='job-card'], div[class*='result-item']"
                    )
                    if not cards:
                        cards = page.query_selector_all("a[href*='/empleos/'], a[href*='/aviso/']")

                    for card in cards[:limit]:
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

                browser.close()

        except Exception as e:
            logger.warning("[LABORUM] Error inesperado (best-effort): %s", e)

        if not jobs:
            logger.warning("[LABORUM] Sin resultados para '%s'. El sitio usa JS intensivo.", keyword)

        return jobs
