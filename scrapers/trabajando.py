import logging
import urllib.parse
from .base import BaseScraper

logger = logging.getLogger(__name__)


class TrabajandoScraper(BaseScraper):
    portal_name = "TRABAJANDO.CL"
    base_url = "https://www.trabajando.cl"
    use_cloudscraper = True

    def _modality_to_param(self, modality: str) -> str:
        mapping = {"remoto": "remoto", "presencial": "presencial", "hibrido": "hibrido"}
        return mapping.get(modality, "")

    def _search_keyword(self, keyword: str, location: str, limit: int) -> list[dict]:
        keyword_encoded = urllib.parse.quote_plus(keyword)
        location_encoded = urllib.parse.quote_plus(location) if location else ""

        url = f"{self.base_url}/trabajo/busqueda?que={keyword_encoded}"
        if location_encoded:
            url += f"&donde={location_encoded}"

        logger.info("[%s] Buscando: %s en %s", self.portal_name, keyword, location or "Chile")

        response = self._safe_request(url, use_cache=False)
        if not response:
            return []

        soup = self._parse_html(response)
        jobs = []

        cards = soup.select("div.jobCard, article.job-item, div.aviso-item, li.aviso")
        if not cards:
            cards = soup.select("div[class*='job'], article[class*='job'], div[class*='aviso']")

        for card in cards[:limit]:
            try:
                title_el = card.select_one("h2, h3, .job-title, .titulo-aviso, a[class*='title']")
                title = title_el.get_text(strip=True) if title_el else ""

                link_el = card.select_one("a[href]")
                href = link_el.get("href", "") if link_el else ""
                full_url = href if href.startswith("http") else f"{self.base_url}{href}"

                company_el = card.select_one(".empresa, .company, [class*='empresa'], [class*='company']")
                company = company_el.get_text(strip=True) if company_el else ""

                location_el = card.select_one(".region, .location, [class*='region'], [class*='location']")
                loc = location_el.get_text(strip=True) if location_el else location

                date_el = card.select_one(".fecha, .date, time, [class*='fecha'], [class*='date']")
                date = date_el.get_text(strip=True) if date_el else ""

                if title and full_url:
                    jobs.append(self._make_job(title, company, loc, date, full_url))
            except Exception as e:
                logger.debug("[%s] Error parseando oferta: %s", self.portal_name, e)

        if not jobs:
            logger.warning("[%s] No se encontraron ofertas para '%s'. Los selectores pueden necesitar actualización.", self.portal_name, keyword)

        return jobs
