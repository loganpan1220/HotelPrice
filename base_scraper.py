"""
base_scraper.py — 所有平台爬蟲的抽象基底類別
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


@dataclass
class HotelResult:
    platform: str
    hotel_name: str
    price: float
    currency: str = "TWD"
    room_type: str = ""
    breakfast: bool = False
    free_cancel: bool = False
    rating: float = 0.0
    review_count: int = 0
    url: str = ""
    image_url: str = ""
    taxes_included: bool = False
    extra_info: dict = field(default_factory=dict)


class BaseScraper(ABC):
    PLATFORM_NAME: str = "Unknown"
    BASE_URL: str = ""

    def __init__(self, headless: bool = True, timeout: int = 20):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def search(self, destination: str, checkin: str, checkout: str,
               adults: int = 2, rooms: int = 1, children: int = 0) -> list:
        pass

    def build_search_url(self, **kwargs) -> str:
        raise NotImplementedError

    def _get_selenium_driver(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_page_load_timeout(self.timeout)
        return self.driver

    def quit_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None

    def __del__(self):
        self.quit_driver()
