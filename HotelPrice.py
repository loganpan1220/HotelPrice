import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from concurrent.futures import ThreadPoolExecutor
import streamlit as st


# 1. 定義解析邏輯 (專門交給 BS4)
def parse_booking_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    results = []
    # 尋找所有飯店外層容器
    cards = soup.select('[data-testid="property-card"]')
    for card in cards:
        name = card.select_one('[data-testid="title"]').get_text(strip=True)
        price = card.select_one('[data-testid="price-and-discounted-price"]').get_text(strip=True)
        results.append({"飯店": name, "價格": price, "來源": "Booking"})
    return results


# 2. 定義爬取任務 (Selenium 負責拿 HTML)
def get_hotel_data(url, site_name):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    # 這裡可以加入 WebDriverWait 確保內容加載
    html = driver.page_source
    driver.quit()

    if site_name == "Booking":
        return parse_booking_html(html)
    # 這裡可以擴充 Agoda, Hotels.com 的解析器...


# 3. Streamlit 介面與多執行緒整合
def run_app():
    st.title("多站點同步比價")

    if st.button("開始同步搜查"):
        urls = [
            ("https://www.booking.com/...", "Booking"),
            ("https://www.agoda.com/...", "Agoda")
        ]

        all_data = []
        # 使用 ThreadPoolExecutor 同時爬取多個網站
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_hotel_data, url, name) for url, name in urls]
            for f in futures:
                all_data.extend(f.result())

        df = pd.DataFrame(all_data)
        st.table(df)