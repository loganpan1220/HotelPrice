import streamlit as st
import pandas as pd
import time
import shutil
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ==========================================
# 區塊 1：雲端專用瀏覽器設定
# ==========================================
def get_driver():
    options = Options()
    options.add_argument('--headless=new')          # 新版無頭模式
    options.add_argument('--no-sandbox')            # 突破 Linux 權限限制
    options.add_argument('--disable-dev-shm-usage') # 解決記憶體不足問題
    options.add_argument('--disable-gpu')           # 關閉 GPU 硬體加速防呆
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 自動尋找 Streamlit Cloud 系統中的瀏覽器與驅動路徑
    chromium_path = shutil.which("chromium") or shutil.which("chromium-browser") or "/usr/bin/chromium"
    driver_path = shutil.which("chromedriver") or "/usr/bin/chromedriver"
    
    options.binary_location = chromium_path
    service = Service(executable_path=driver_path)
    
    return webdriver.Chrome(service=service, options=options)

# ==========================================
# 區塊 2：爬蟲核心邏輯
# ==========================================
def fetch_booking(target):
    try:
        driver = get_driver()
        url = f"https://www.booking.com/searchresults.zh-tw.html?ss={target}"
        driver.get(url)
        time.sleep(5) # 等待 JavaScript 渲染
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()
        
        results = []
        # 注意：Booking 的 class name 可能會隨時間變動，若抓不到請檢查 F12
        cards = soup.select('[data-testid="property-card"]')
        
        for card in cards[:5]: # 取前 5 筆
            name_elem = card.select_one('[data-testid="title"]')
            price_elem = card.select_one('[data-testid="price-and-discounted-price"]')
            
            name = name_elem.text.strip() if name_elem else "未知飯店"
            price_str = price_elem.text.strip() if price_elem else "0"
            
            # 清洗價格：只保留數字
            price_num = int(re.sub(r'[^\d]', '', price_str)) if re.sub(r'[^\d]', '', price_str) else 0
            
            if price_num > 0:
                results.append({"平台": "Booking.com", "飯店名稱": name, "最低價格": price_num})
                
        return results
    except Exception as e:
        st.error(f"Booking 爬取發生錯誤: {e}")
        return []

def fetch_agoda(target):
    return []

# ==========================================
# 區塊 3：Streamlit 互動介面
# ==========================================
st.set_page_config(page_title="智能飯店比價系統", page_icon="🏨", layout="centered")

st.title("飯店比價助手")
st.markdown("請輸入您想查詢的**飯店名稱**或**城市**，系統將自動為您抓取最新價格。")

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        search_target = st.text_input("輸入目標", placeholder="例如：台北飯店 或 大阪", label_visibility="collapsed")
    with col2:
        search_btn = st.button("開始比價", use_container_width=True, type="primary")

st.divider()

# ==========================================
# 區塊 4：執行與結果展示
# ==========================================
if search_btn:
    if not search_target.strip():
        st.warning("⚠️ 請先輸入想查詢的飯店或城市名稱喔！")
    else:
        with st.spinner(f"正在啟動系統，前往搜尋 **{search_target}** 的最新報價，請稍候..."):
            
            # 執行爬蟲
            res_booking = fetch_booking(search_target)
            res_agoda = fetch_agoda(search_target)
            
            # 彙整資料
            all_data = res_booking + res_agoda
            df = pd.DataFrame(all_data)

        if not df.empty:
            # 依照價格由低到高排序
            df = df.sort_values(by="最低價格")
            
            st.success(f"🎉 搜尋完成！共找到 {len(df)} 筆報價。")
            
            # 顯示表格
            st.subheader("📋 詳細比價清單")
            st.dataframe(
                df,
                column_config={
                    "最低價格": st.column_config.NumberColumn("最低價格 (TWD)", format="$%d")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # 顯示圖表
            st.subheader("📊 價格長條圖")
            st.bar_chart(data=df, x="飯店名稱", y="最低價格", color="平台")
            
        else:
            st.error("找不到相關飯店資訊。可能是關鍵字無效、平台防爬蟲機制阻擋，或是網頁結構(標籤)已經變更。")
