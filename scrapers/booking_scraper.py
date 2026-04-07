"""
booking_scraper.py
爬取 Booking.com 飯店搜尋結果
Booking.com 有較強的反爬措施，使用 Selenium + 隨機延遲
"""

import re
from urllib.parse import quote_plus

from selenium.webdriver.common.by import By

from .base_scraper import BaseScraper


class BookingScraper(BaseScraper):

    PLATFORM_NAME = "Booking.com"
    PLATFORM_URL = "https://www.booking.com"
    PLATFORM_COLOR = "#003580"

    def build_url(self, hotel_name: str, checkin: str, checkout: str,
                  adults: int = 2, rooms: int = 1) -> str:
        ci_parts = checkin.split("-")
        co_parts = checkout.split("-")
        return (
            "https://www.booking.com/searchresults.zh-tw.html?"
            f"ss={quote_plus(hotel_name)}&"
            f"checkin_year={ci_parts[0]}&checkin_month={ci_parts[1]}&checkin_monthday={ci_parts[2]}&"
            f"checkout_year={co_parts[0]}&checkout_month={co_parts[1]}&checkout_monthday={co_parts[2]}&"
            f"group_adults={adults}&no_rooms={rooms}&group_children=0&"
            "selected_currency=TWD&lang=zh-tw"
        )

    def scrape(self, hotel_name: str, checkin: str, checkout: str,
               adults: int = 2, rooms: int = 1) -> list:
        results = []
        url = self.build_url(hotel_name, checkin, checkout, adults, rooms)

        soup = self.get_with_selenium(url, wait_seconds=5)
        if soup is None:
            return results

        # 等待搜尋結果
        try:
            self.wait_for_element(By.CSS_SELECTOR, "[data-testid='property-card']", timeout=15)
        except Exception:
            pass

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "lxml")

        cards = soup.select("[data-testid='property-card']")
        if not cards:
            # 備用 selector（Booking 常改版）
            cards = soup.select(".sr_property_block, .fc4b09bb54")

        for card in cards[:5]:
            try:
                # 飯店名稱
                name_el = card.select_one(
                    "[data-testid='title'], .fcab3e7310, h3"
                )
                name = name_el.get_text(strip=True) if name_el else hotel_name

                # 價格（TWD）
                price_el = card.select_one(
                    "[data-testid='price-and-discounted-price'], "
                    ".prco-valign-middle-helper, .bui-price-display__value"
                )
                if not price_el:
                    continue
                price_text = price_el.get_text(strip=True)
                price_num = int(re.sub(r"[^\d]", "", price_text))
                if price_num == 0:
                    continue

                # 連結
                link_el = card.select_one("a[data-testid='title-link'], a[href*='/hotel/']")
                link = link_el["href"] if link_el else url
                if link.startswith("/"):
                    link = self.PLATFORM_URL + link

                # 評分
                score_el = card.select_one("[data-testid='review-score'] div, .bui-review-score__badge")
                score = score_el.get_text(strip=True) if score_el else ""

                results.append({
                    "platform": self.PLATFORM_NAME,
                    "hotel_name": name,
                    "price": price_num,
                    "currency": "TWD",
                    "room_type": "標準客房",
                    "url": link,
                    "note": f"評分 {score}" if score else "Booking.com",
                })
            except Exception as e:
                print(f"[Booking.com] 解析卡片失敗: {e}")
                continue

        return results
