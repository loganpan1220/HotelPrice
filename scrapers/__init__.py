from .agoda_scraper import AgodaScraper
from .booking_scraper import BookingScraper
from .hotels_scraper import HotelsScraper
from .trivago_scraper import TrivagoScraper

SCRAPERS = {
    "Agoda": AgodaScraper,
    "Booking.com": BookingScraper,
    "Hotels.com": HotelsScraper,
    "Trivago": TrivagoScraper,
}

PLATFORM_COLORS = {
    "Agoda": "#e4003b",
    "Booking.com": "#003580",
    "Hotels.com": "#d5001e",
    "Trivago": "#007aff",
}
