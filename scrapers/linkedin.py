import logging
import urllib.parse
import json
import os
from pathlib import Path
from .base import BaseScraper

logger = logging.getLogger(__name__)

SESSION_DIR = Path.home() / ".euricles" / "sessions"


class LinkedInScraper(BaseScraper):
    portal_name = "LINKEDIN"
    best_effort = True
    base_url = "https://www.linkedin.com"

    def _modality_to_param(self, modality: str) -> str:
        mapping = {"remoto": "2", "presencial": "1", "hibrido": "3"}
        return mapping.get(modality, "")

    def _load_session_state(self) -> dict | None:
        path = SESSION_DIR / "linkedin_state.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None

    def _save_session_state(self, state: dict):
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        path = SESSION_DIR / "linkedin_state.json"
        path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def _search_keyword(self, keyword: str, location: str, limit: int) -> list[dict]:
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            logger.error("[LINKEDIN] playwright no está instalado. Ejecuta: pip install playwright && playwright install chromium")
            return []

        keyword_encoded = urllib.parse.quote_plus(keyword)
        location_encoded = urllib.parse.quote_plus(location)

        params = f"?keywords={keyword_encoded}&location={location_encoded}&f_TPR=r604800"
        modality_param = self._modality_param({"modality": ""})
        if modality_param:
            params += f"&f_WT={modality_param}"
        url = f"{self.base_url}/jobs/search/{params}"

        logger.info("[LINKEDIN] Buscando (best-effort): %s en %s", keyword, location)
        jobs = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ],
                )
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="es-CL",
                    viewport={"width": 1920, "height": 1080},
                )

                saved_state = self._load_session_state()
                if saved_state:
                    try:
                        context.add_cookies(saved_state.get("cookies", []))
                        logger.info("[LINKEDIN] Sesión restaurada desde archivo")
                    except Exception as e:
                        logger.debug("[LINKEDIN] Error restaurando sesión: %s", e)

                page = context.new_page()

                try:
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)

                    try:
                        page.wait_for_selector("ul.jobs-search__results-list, .base-card, div.job-card-container", timeout=15000)
                    except PlaywrightTimeout:
                        logger.warning("[LINKEDIN] Timeout al cargar resultados para '%s'", keyword)
                        browser.close()
                        return []

                    for _ in range(3):
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(2000)

                    cards = page.query_selector_all(
                        "li.jobs-search__results-list > div, "
                        "div.base-card, "
                        "div.job-card-container, "
                        "li[class*='job-card']"
                    )

                    for card in cards[:limit]:
                        try:
                            title_el = card.query_selector(
                                "h3.base-search-card__title, "
                                "h3.job-card-list__title, "
                                "a.job-card-list__title, "
                                "h3"
                            )
                            title = title_el.inner_text().strip() if title_el else ""

                            company_el = card.query_selector(
                                "h4.base-search-card__subtitle, "
                                "h4.job-card-container__company-name, "
                                "h4"
                            )
                            company = company_el.inner_text().strip() if company_el else ""

                            location_el = card.query_selector(
                                "span.job-search-card__location, "
                                "span.job-card-container__metadata-item, "
                                "[class*='location']"
                            )
                            loc = location_el.inner_text().strip() if location_el else location

                            date_el = card.query_selector("time, [class*='date'], [class*='time']")
                            date = date_el.get_attribute("datetime") or date_el.inner_text().strip() if date_el else ""

                            link_el = card.query_selector("a[href*='/jobs/view/']")
                            href = link_el.get_attribute("href") if link_el else ""
                            if href and "?" in href:
                                href = href.split("?")[0]

                            if title and href:
                                jobs.append(self._make_job(title, company, loc, date, href))
                        except Exception as e:
                            logger.debug("[LINKEDIN] Error parseando oferta: %s", e)

                    try:
                        cookies = context.cookies()
                        self._save_session_state({"cookies": cookies})
                    except Exception:
                        pass

                except Exception as e:
                    logger.warning("[LINKEDIN] Error durante la navegación: %s", e)

                browser.close()

        except Exception as e:
            logger.warning("[LINKEDIN] Error inesperado (best-effort, ignorando): %s", e)

        if not jobs:
            logger.warning("[LINKEDIN] Sin resultados para '%s'. LinkedIn puede estar bloqueando el acceso.", keyword)

        return jobs
