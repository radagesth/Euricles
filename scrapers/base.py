import time
import random
import json
import os
import hashlib
import logging
import socket
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

MODALITY_MAP = {
    "remoto": "remoto",
    "presencial": "presencial",
    "hibrido": "hibrido",
    "híbrido": "hibrido",
    "cualquiera": "",
}

CACHE_DIR = Path.home() / ".euricles" / "cache"
CACHE_TTL = timedelta(hours=6)
REQUEST_TIMEOUT = 20
RETRIES = 3


def check_connectivity(host: str = "8.8.8.8", port: int = 53, timeout: float = 3) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except OSError:
        return False


def clean_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    tracking_params = {"utm_source", "utm_medium", "utm_campaign", "e", "ref", "trk"}
    for param in tracking_params:
        query.pop(param, None)
    parsed = parsed._replace(query=urlencode(query, doseq=True))
    return urlunparse(parsed)


def _cache_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _load_cache(key: str) -> str | None:
    path = CACHE_DIR / key
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        saved_at = datetime.fromisoformat(data["saved_at"])
        if datetime.now() - saved_at > CACHE_TTL:
            path.unlink(missing_ok=True)
            return None
        return data["html"]
    except Exception:
        return None


def _save_cache(key: str, html: str):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        data = {"saved_at": datetime.now().isoformat(), "html": html}
        (CACHE_DIR / key).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.debug("Error guardando caché: %s", e)


class BaseScraper(ABC):
    portal_name: str = "Unknown"
    best_effort: bool = False
    base_url: str = ""
    use_cloudscraper: bool = False

    def __init__(self):
        self._session = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            if self.use_cloudscraper:
                try:
                    import cloudscraper
                    self._session = cloudscraper.create_scraper()
                except ImportError:
                    logger.warning("[%s] cloudscraper no disponible, usando requests", self.portal_name)
                    self._session = requests.Session()
            else:
                self._session = requests.Session()
            self._session.headers.update(self._get_headers())
        return self._session

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _safe_request(self, url: str, retries: int = RETRIES, delay: float = 1.5, use_cache: bool = True) -> requests.Response | None:
        clean = clean_url(url)
        if use_cache:
            cached = _load_cache(_cache_key(clean))
            if cached is not None:
                logger.info("[%s] Cache hit para %s", self.portal_name, url[:60])
                resp = requests.Response()
                resp.status_code = 200
                resp._content = cached.encode("utf-8")
                resp.headers["Content-Type"] = "text/html; charset=utf-8"
                resp.url = clean
                return resp

        for attempt in range(1, retries + 1):
            try:
                time.sleep(delay + random.uniform(0, 0.8))
                session = self._get_session()
                response = session.get(clean, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                response.encoding = response.apparent_encoding or "utf-8"
                if use_cache and response.text:
                    _save_cache(_cache_key(clean), response.text)
                return response
            except requests.RequestException as e:
                logger.warning("[%s] Intento %d/%d fallido para %s: %s", self.portal_name, attempt, retries, url, e)
                if attempt < retries:
                    time.sleep(delay * attempt)
        return None

    def _parse_html(self, response: requests.Response) -> BeautifulSoup:
        return BeautifulSoup(response.text, "lxml")

    def _make_job(self, title: str, company: str, location: str, date: str, url: str) -> dict:
        return {
            "title": title.strip() if title else "Sin título",
            "company": company.strip() if company else "Empresa no especificada",
            "location": location.strip() if location else "No especificada",
            "date": date.strip() if date else "Fecha no disponible",
            "url": clean_url(url.strip()) if url else "",
            "portal": self.portal_name,
            "best_effort": self.best_effort,
        }

    def _modality_param(self, profile: dict) -> str:
        modality = profile.get("modality", "").strip().lower()
        modality = MODALITY_MAP.get(modality, modality)
        return self._modality_to_param(modality)

    def _modality_to_param(self, modality: str) -> str:
        return ""

    def search(self, profile: dict, max_results: int = 20, cancel_event=None) -> list[dict]:
        jobs = []
        keywords = profile.get("keywords", [])
        location = profile.get("location", "")

        for keyword in keywords:
            if cancel_event and cancel_event.is_set():
                logger.info("[%s] Búsqueda cancelada por el usuario", self.portal_name)
                break
            if len(jobs) >= max_results:
                break
            time.sleep(random.uniform(0.5, 1.5))
            found = self._search_keyword(keyword, location, max_results - len(jobs))
            jobs.extend(found)
            logger.info("[%s] '%s' → %d oferta(s) (acumulado: %d)", self.portal_name, keyword, len(found), len(jobs))

        seen = set()
        unique = []
        for job in jobs:
            if job["url"] not in seen:
                seen.add(job["url"])
                unique.append(job)
        return unique[:max_results]

    @abstractmethod
    def _search_keyword(self, keyword: str, location: str, limit: int) -> list[dict]:
        pass
