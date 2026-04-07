"""
Demo 模式 — 產生模擬資料，供無法實際爬蟲時展示 UI 功能
"""
import random
import numpy as np
from .base_scraper import HotelResult

HOTELS_POOL = [
    "台北君悅酒店", "寒舍艾麗酒店", "台北文華東方酒店",
    "台北晶華酒店", "美麗信花園酒店", "台北馥敦飯店",
    "老爺行旅", "西華飯店", "喜來登大飯店",
    "萬豪酒店", "凱撒飯店", "天成文旅",
    "艾美酒店", "台北諾富特", "北投亞太飯店",
]

ROOM_TYPES = ["豪華雙人房", "標準雙人房", "豪華套房", "商務客房", "家庭房"]

PLATFORMS = {
    "Booking.com": {"color": "#003580", "tax": False, "base_mult": 1.00},
    "Agoda":        {"color": "#e5261d", "tax": True,  "base_mult": 0.95},
    "Trip.com":     {"color": "#1890ff", "tax": False, "base_mult": 0.97},
    "Hotels.com":   {"color": "#d4111e", "tax": True,  "base_mult": 1.02},
}


def generate_mock_results(destination: str, nights: int = 1) -> list[HotelResult]:
    """產生模擬搜尋結果（供示範用）"""
    results = []
    # 選 6 間飯店，每間在各平台都有報價
    selected_hotels = random.sample(HOTELS_POOL, min(6, len(HOTELS_POOL)))

    for hotel_name in selected_hotels:
        base_price = random.randint(2500, 12000)
        base_rating = round(random.uniform(7.5, 9.8), 1)
        base_reviews = random.randint(500, 8000)
        room_type = random.choice(ROOM_TYPES)
        breakfast = random.random() > 0.5
        free_cancel = random.random() > 0.4

        for platform, meta in PLATFORMS.items():
            noise = np.random.normal(0, 0.04)  # ±4% 價格波動
            price = max(500, base_price * meta["base_mult"] * (1 + noise))
            # 偶爾某平台沒有這間飯店
            if random.random() < 0.15:
                continue
            results.append(HotelResult(
                platform=platform,
                hotel_name=f"{hotel_name}（{destination}）",
                price=round(price, 0),
                room_type=room_type,
                breakfast=breakfast and (random.random() > 0.3),
                free_cancel=free_cancel,
                rating=min(10.0, round(base_rating + random.uniform(-0.3, 0.3), 1)),
                review_count=int(base_reviews * random.uniform(0.8, 1.2)),
                url=f"https://example.com/{platform.lower()}/{hotel_name}",
                taxes_included=meta["tax"],
            ))
    return results
