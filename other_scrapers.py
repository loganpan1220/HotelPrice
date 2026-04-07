"""
Trip.com 爬蟲（在台灣/亞洲市場普及度高）
"""
import time
import random
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper, HotelResult


class TripScraper(BaseScraper):
    PLATFORM_NAME = "Trip.com"
    BASE_URL = "https://tw.trip.com/hotels/list"
    LOGO_COLOR = "#1890ff"

    def build_search_url(self, destination: str, checkin: str, checkout: str,
                         adults: int = 2, rooms: int = 1, children: int = 0) -> str:
        params = (
            f"?city={quote_plus(destination)}"
            f"&checkin={checkin}&checkout={checkout}"
            f"&adult={adults}&children={children}&rooms={rooms}"
            f"&curr=TWD&locale=zh-TW"
        )
        return self.BASE_URL + params

    def search(self, destination: str, checkin: str, checkout: str,
               adults: int = 2, rooms: int = 1, children: int = 0) -> list[HotelResult]:
        url = self.build_search_url(destination, checkin, checkout, adults, rooms, children)
        self.logger.info(f"[Trip.com] 搜尋 URL: {url}")
        results = []
        try:
            driver = self._get_selenium_driver()
            driver.get(url)
            time.sleep(random.uniform(4, 6))
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 800)")
                time.sleep(0.8)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            results = self._parse_results(soup, url)
        except Exception as e:
            self.logger.error(f"[Trip.com] 爬取失敗: {e}")
        finally:
            self.quit_driver()
        return results

    def _parse_results(self, soup: BeautifulSoup, base_url: str) -> list[HotelResult]:
        results = []
        cards = soup.select('.hotel-list-item') or soup.select('[class*="HotelCard"]')
        self.logger.info(f"[Trip.com] 找到 {len(cards)} 筆結果")
        for card in cards[:10]:
            try:
                name_el = card.select_one('[class*="hotel-name"]') or card.select_one('h3')
                name = name_el.get_text(strip=True) if name_el else "N/A"
                price_el = card.select_one('[class*="price"]')
                price = self._parse_price(price_el.get_text(strip=True) if price_el else "0")
                rating_el = card.select_one('[class*="rating"]') or card.select_one('[class*="score"]')
                rating = self._parse_rating(rating_el.get_text(strip=True) if rating_el else "0")
                link_el = card.select_one('a')
                hotel_url = link_el["href"] if link_el else base_url
                if hotel_url.startswith("/"):
                    hotel_url = "https://tw.trip.com" + hotel_url
                text = card.get_text()
                breakfast = "早餐" in text or "Breakfast" in text
                free_cancel = "免費取消" in text or "可取消" in text
                results.append(HotelResult(
                    platform=self.PLATFORM_NAME,
                    hotel_name=name,
                    price=price,
                    rating=rating,
                    url=hotel_url,
                    breakfast=breakfast,
                    free_cancel=free_cancel,
                    taxes_included=False,
                ))
            except Exception as e:
                self.logger.warning(f"[Trip.com] 解析卡片失敗: {e}")
        return results

    @staticmethod
    def _parse_price(text: str) -> float:
        digits = "".join(c for c in text if c.isdigit())
        return float(digits) if digits else 0.0

    @staticmethod
    def _parse_rating(text: str) -> float:
        import re
        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            val = float(match.group(1))
            return val if val <= 10 else val / 10
        return 0.0


# ─────────────────────────────────────────────────────────────────────────────

class HotelsScraper(BaseScraper):
    """Hotels.com 爬蟲"""
    PLATFORM_NAME = "Hotels.com"
    BASE_URL = "https://zh.hotels.com/search.do"
    LOGO_COLOR = "#d4111e"

    def build_search_url(self, destination: str, checkin: str, checkout: str,
                         adults: int = 2, rooms: int = 1, children: int = 0) -> str:
        params = (
            f"?q-destination={quote_plus(destination)}"
            f"&q-check-in={checkin}&q-check-out={checkout}"
            f"&q-rooms={rooms}&q-room-0-adults={adults}&q-room-0-children={children}"
        )
        return self.BASE_URL + params

    def search(self, destination: str, checkin: str, checkout: str,
               adults: int = 2, rooms: int = 1, children: int = 0) -> list[HotelResult]:
        url = self.build_search_url(destination, checkin, checkout, adults, rooms, children)
        self.logger.info(f"[Hotels.com] 搜尋 URL: {url}")
        results = []
        try:
            driver = self._get_selenium_driver()
            driver.get(url)
            time.sleep(random.uniform(4, 6))
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 800)")
                time.sleep(0.8)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            results = self._parse_results(soup, url)
        except Exception as e:
            self.logger.error(f"[Hotels.com] 爬取失敗: {e}")
        finally:
            self.quit_driver()
        return results

    def _parse_results(self, soup: BeautifulSoup, base_url: str) -> list[HotelResult]:
        results = []
        cards = soup.select('[data-stid="lodging-card-responsive"]') or soup.select('.uitk-card')
        self.logger.info(f"[Hotels.com] 找到 {len(cards)} 筆結果")
        for card in cards[:10]:
            try:
                name_el = card.select_one('h3') or card.select_one('[class*="name"]')
                name = name_el.get_text(strip=True) if name_el else "N/A"
                price_el = card.select_one('[data-stid="price-summary"]') or card.select_one('[class*="price"]')
                price = self._parse_price(price_el.get_text(strip=True) if price_el else "0")
                rating_el = card.select_one('[class*="rating"]')
                rating = self._parse_rating(rating_el.get_text(strip=True) if rating_el else "0")
                link_el = card.select_one('a')
                hotel_url = link_el["href"] if link_el else base_url
                if hotel_url.startswith("/"):
                    hotel_url = "https://zh.hotels.com" + hotel_url
                text = card.get_text()
                breakfast = "早餐" in text or "Breakfast" in text
                free_cancel = "免費取消" in text or "Free cancellation" in text
                results.append(HotelResult(
                    platform=self.PLATFORM_NAME,
                    hotel_name=name,
                    price=price,
                    rating=rating,
                    url=hotel_url,
                    breakfast=breakfast,
                    free_cancel=free_cancel,
                    taxes_included=True,
                ))
            except Exception as e:
                self.logger.warning(f"[Hotels.com] 解析卡片失敗: {e}")
        return results

    @staticmethod
    def _parse_price(text: str) -> float:
        digits = "".join(c for c in text if c.isdigit())
        return float(digits) if digits else 0.0

    @staticmethod
    def _parse_rating(text: str) -> float:
        import re
        match = re.search(r"(\d+\.?\d*)", text)
        if match:
            val = float(match.group(1))
            return val if val <= 10 else val / 10
        return 0.0
