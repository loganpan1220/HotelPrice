import streamlit as st
import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
# 記得如果要在 Streamlit Cloud 跑，上面這些 import 和套件都要有

# ==========================================
# 區塊 1：瀏覽器與爬蟲核心設定 (保留你原本的心血)
# ==========================================
def get_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 推薦寫法：使用 webdriver-manager
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def fetch_booking(target):
    # 這裡放你原本寫好的 Booking 爬蟲邏輯
    driver = get_driver()
    url = f"https://www.booking.com/searchresults.zh-tw.html?ss={target}"
    driver.get(url)
    time.sleep(4)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    
    results = []
    cards = soup.select('[data-testid="property-card"]') # 注意：標籤可能會變
    for card in cards[:5]:
        name = card.select_one('[data-testid="title"]').text if card.select_one('[data-testid="title"]') else "未知"
        price_str = card.select_one('[data-testid="price-and-discounted-price"]').text if card.select_one('[data-testid="price-and-discounted-price"]') else "0"
        
        # 把價格轉成純數字，方便後續排序
        import re
        price_num = int(re.sub(r'[^\d]', '', price_str)) if re.sub(r'[^\d]', '', price_str) else 0
        
        results.append({"平台": "Booking", "飯店名稱": name, "價格": price_num})
    return results

def fetch_agoda(target):
    # 這裡放你原本寫好的 Agoda 爬蟲邏輯 (請確保能抓到真實資料)
    # ... (你的 Agoda 程式碼) ...
    return [] # 測試階段如果 Agoda 還沒寫好，先回傳空清單避免報錯


# ==========================================
# 區塊 2：Streamlit 互動介面與連動 (新的介面)
# ==========================================
st.set_page_config(page_title="智能飯店比價系統", page_icon="🏨", layout="centered")

st.title("🏨 智能飯店比價助手")
st.markdown("請輸入您想查詢的**飯店名稱**或**城市**，系統將自動從平台為您抓取最新價格。")

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        search_target = st.text_input("輸入目標", placeholder="例如：台北W飯店 或 大阪", label_visibility="collapsed")
    with col2:
        search_btn = st.button("開始比價", use_container_width=True, type="primary")

st.divider()

# ==========================================
# 區塊 3：觸發爬蟲與顯示結果 (把區塊 1 和 2 連接起來)
# ==========================================
if search_btn:
    if not search_target.strip():
        st.warning("⚠️ 請先輸入想查詢的飯店或城市名稱喔！")
    else:
        with st.spinner(f"正在前往平台搜尋 **{search_target}** 的最新報價，請稍候..."):
            
            # 這裡就是呼叫你上面寫好的爬蟲函數 (已將假資料替換為真實函數)
            res_booking = fetch_booking(search_target)
            res_agoda = fetch_agoda(search_target)
            
            # 把所有平台的結果合併成一個清單
            all_data = res_booking + res_agoda
            df = pd.DataFrame(all_data)

        if not df.empty:
            # 依照價格由低到高排序
            df = df.sort_values(by="價格")
            
            st.success(f"🎉 搜尋完成！共找到 {len(df)} 筆報價。")
            
            st.subheader("📋 詳細比價清單")
            st.dataframe(
                df,
                column_config={
                    "價格": st.column_config.NumberColumn("最低價格 (TWD)", format="$%d")
                },
                use_container_width=True,
                hide_index=True
            )
            
            st.subheader("📊 價格走勢圖")
            st.bar_chart(data=df, x="飯店名稱", y="價格", color="平台")
            
        else:
            st.error("找不到相關飯店資訊，可能是防爬蟲機制阻擋，或請確認網頁原始碼的標籤是否變更。")
