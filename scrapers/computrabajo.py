import logging
import urllib.parse
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ComputrabajoScraper(BaseScraper):
    portal_name = "COMPUTRABAJO.CL"
    base_url = "https://cl.computrabajo.com"

    def _modality_to_param(self, modality: str) -> str:
        mapping = {"remoto": "2", "presencial": "1", "hibrido": "3"}
        return mapping.get(modality, "")

    def _search_keyword(self, keyword: str, location: str, limit: int) -> list[dict]:
        keyword_slug = urllib.parse.quote_plus(keyword.replace(" ", "-"))
        location_encoded = urllib.parse.quote_plus(location) if location else ""

        url = f"{self.base_url}/trabajo-de-{keyword_slug}"
        params = {}
        if location_encoded:
            params["l"] = location_encoded

        logger.info("[%s] Buscando: %s en %s", self.portal_name, keyword, location or "Chile")

        if params:
            url += "?" + urllib.parse.urlencode(params)

        response = self._safe_request(url)
        if not response:
            return []

        soup = self._parse_html(response)
        jobs = []

        articles = soup.select("article.box_offer, div[data-code], .js-o-pac")
        if not articles:
            articles = soup.select("article[data-code]")

        for article in articles[:limit]:
            try:
                title_el = article.select_one("h2.fs18, h2 a, .js-o-pac h2, a[title]")
                title = title_el.get_text(strip=True) if title_el else ""

                link_el = article.select_one("h2 a, a.js-o-pac")
                href = link_el.get("href", "") if link_el else ""
                full_url = href if href.startswith("http") else f"{self.base_url}{href}"

                company_el = article.select_one("a.fc_base.t_ellipsis, p.fc_base a, span.fc_base")
                company = company_el.get_text(strip=True) if company_el else ""

                location_el = article.select_one("span.fs13 + span, p.fs13 span, .ellipsis.fs13")
                loc = location_el.get_text(strip=True) if location_el else location

                date_el = article.select_one("p.fs13 span.fc_aux, span.fc_aux, time")
                date = date_el.get_text(strip=True) if date_el else ""

                if title and full_url:
                    jobs.append(self._make_job(title, company, loc, date, full_url))
            except Exception as e:
                logger.debug("[%s] Error parseando oferta: %s", self.portal_name, e)

        if not jobs:
            logger.warning("[%s] No se encontraron ofertas para '%s'. Los selectores pueden necesitar actualización.", self.portal_name, keyword)

        return jobs
