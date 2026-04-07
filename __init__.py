from .base_scraper import BaseScraper, HotelResult
from .booking_scraper import BookingScraper
from .agoda_scraper import AgodaScraper
from .other_scrapers import TripScraper, HotelsScraper
from .mock_data import generate_mock_results

__all__ = [
    "BaseScraper", "HotelResult",
    "BookingScraper", "AgodaScraper",
    "TripScraper", "HotelsScraper",
    "generate_mock_results",
]
