from .computrabajo import ComputrabajoScraper
from .trabajando import TrabajandoScraper
from .laborum import LaborumScraper
from .linkedin import LinkedInScraper

SCRAPER_REGISTRY = {
    "computrabajo": ComputrabajoScraper,
    "trabajando": TrabajandoScraper,
    "laborum": LaborumScraper,
    "linkedin": LinkedInScraper,
}
