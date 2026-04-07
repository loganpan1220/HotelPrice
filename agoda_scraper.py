"""
agoda_scraper.py
爬取 Agoda 飯店搜尋結果
Agoda 為 React SPA，需要 Selenium 處理動態渲染
"""

import re
import time
from urllib.parse import quote_plus

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from .base_scraper import BaseScraper


class AgodaScraper(BaseScraper):

    PLATFORM_NAME = "Agoda"
    PLATFORM_URL = "https://www.agoda.com"
    PLATFORM_COLOR = "#e4003b"

    def build_url(self, hotel_name: str, checkin: str, checkout: str,
                  adults: int = 2, rooms: int = 1) -> str:
        # checkin / checkout 格式: YYYY-MM-DD
        checkin_parts = checkin.split("-")
        checkout_parts = checkout.split("-")
        return (
            f"https://www.agoda.com/search?"
            f"city=&"
            f"checkIn={checkin_parts[0]}-{checkin_parts[1]}-{checkin_parts[2]}&"
            f"checkOut={checkout_parts[0]}-{checkout_parts[1]}-{checkout_parts[2]}&"
            f"rooms={rooms}&adults={adults}&children=0&"
            f"textToSearch={quote_plus(hotel_name)}&"
            f"locale=zh-tw&currency=TWD"
        )

    def scrape(self, hotel_name: str, checkin: str, checkout: str,
               adults: int = 2, rooms: int = 1) -> list:
        results = []
        url = self.build_url(hotel_name, checkin, checkout, adults, rooms)

        soup = self.get_with_selenium(url, wait_seconds=5)
        if soup is None:
            return results

        # 等待房價卡片出現
        try:
            self.wait_for_element(By.CSS_SELECTOR, "[data-selenium='hotel-item']", timeout=12)
        except Exception:
            pass

        # 重新抓取 DOM（等待後）
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(self.driver.page_source, "lxml")

        # 尋找飯店卡片
        cards = soup.select("[data-selenium='hotel-item']")
        if not cards:
            cards = soup.select(".PropertyCard, .hotel-list-container li")

        for card in cards[:5]:  # 最多取前5筆
            try:
                # 飯店名稱
                name_el = card.select_one(
                    "[data-selenium='hotel-name'], .PropertyCard__HotelName, h3"
                )
                name = name_el.get_text(strip=True) if name_el else hotel_name

                # 價格
                price_el = card.select_one(
                    "[data-selenium='display-price'], .PropertyCardPrice__Value, "
                    ".price-info .price"
                )
                if not price_el:
                    continue
                price_text = price_el.get_text(strip=True)
                price_num = int(re.sub(r"[^\d]", "", price_text))

                # 連結
                link_el = card.select_one("a[href]")
                link = self.PLATFORM_URL + link_el["href"] if link_el else url

                # 房型
                room_el = card.select_one(
                    "[data-selenium='room-type-name'], .RoomName, .room-type"
                )
                room_type = room_el.get_text(strip=True) if room_el else "標準客房"

                results.append({
                    "platform": self.PLATFORM_NAME,
                    "hotel_name": name,
                    "price": price_num,
                    "currency": "TWD",
                    "room_type": room_type,
                    "url": link,
                    "note": "Agoda",
                })
            except Exception as e:
                print(f"[Agoda] 解析卡片失敗: {e}")
                continue

        return results
