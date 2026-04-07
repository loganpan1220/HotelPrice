"""
訂房比價系統 — Streamlit 主程式
執行方式: streamlit run app.py
"""
import concurrent.futures, io, time
from datetime import date, timedelta
import numpy as np
import pandas as pd
import streamlit as st
from data_processor import (
    export_to_csv, find_best_deals, get_platform_stats,
    get_price_summary, pivot_price_table, results_to_dataframe, PLATFORM_COLORS,
)
from scrapers import AgodaScraper, BookingScraper, HotelsScraper, TripScraper, generate_mock_results

# ─── 頁面設定 ──────────────────────────────────────────────────────────────────
st.set_page_config(page_title="訂房比價系統", page_icon="🏨", layout="wide",
                   initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap');
html,body,[class*="css"]{font-family:'Noto Sans TC',sans-serif;}
.hero-banner{background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460);border-radius:16px;
  padding:2.5rem 2rem;margin-bottom:1.5rem;text-align:center;position:relative;overflow:hidden;}
.hero-banner::before{content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at 20% 50%,rgba(99,179,237,0.15),transparent 60%),
             radial-gradient(ellipse at 80% 30%,rgba(236,72,153,0.1),transparent 50%);}
.hero-title{font-size:2.4rem;font-weight:700;color:#fff;margin:0;
  text-shadow:0 2px 12px rgba(0,0,0,0.4);position:relative;}
.hero-sub{color:rgba(255,255,255,0.7);margin-top:.5rem;font-size:1rem;position:relative;}
.platform-badge{display:inline-block;padding:2px 10px;border-radius:20px;
  font-size:.78rem;font-weight:600;color:#fff;margin:2px;}
.deal-card{background:linear-gradient(135deg,#fff9f0,#fff3e0);border:2px solid #f59e0b;
  border-radius:14px;padding:1.2rem;margin-bottom:.8rem;}
.deal-name{font-weight:700;font-size:1.05rem;color:#1e293b;}
.deal-price{font-size:1.3rem;font-weight:700;color:#b45309;}
.deal-platform{font-size:.85rem;color:#64748b;}
.deal-score{float:right;background:#f59e0b;color:#fff;border-radius:8px;
  padding:2px 8px;font-size:.85rem;font-weight:700;}
.warning-box{background:#fffbeb;border:1px solid #f59e0b;border-radius:10px;
  padding:.8rem 1rem;font-size:.88rem;color:#92400e;}
</style>
""", unsafe_allow_html=True)

# ─── 側邊欄 ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔍 搜尋條件")
    destination = st.text_input("目的地 / 飯店名稱", value="台北", placeholder="例：台北、花蓮、京都")
    today = date.today()
    col_ci, col_co = st.columns(2)
    with col_ci: checkin = st.date_input("入住", value=today+timedelta(7), min_value=today)
    with col_co: checkout = st.date_input("退房", value=today+timedelta(9), min_value=today+timedelta(1))
    nights = max(1, (checkout - checkin).days)
    st.markdown(f"📅 住宿 **{nights}** 晚")
    col_a, col_r = st.columns(2)
    with col_a: adults = st.number_input("成人", 1, 8, 2)
    with col_r: rooms = st.number_input("房間數", 1, 5, 1)
    children = st.number_input("兒童", 0, 6, 0)

    st.divider()
    st.markdown("### ⚙️ 平台選擇")
    use_booking = st.checkbox("Booking.com", True)
    use_agoda   = st.checkbox("Agoda", True)
    use_trip    = st.checkbox("Trip.com", True)
    use_hotels  = st.checkbox("Hotels.com", True)

    st.divider()
    st.markdown("### 🛠 模式設定")
    demo_mode = st.toggle("Demo 模式（模擬資料）", True,
        help="關閉後實際爬取各平台，需安裝 ChromeDriver")
    headless = st.checkbox("無頭模式（背景執行瀏覽器）", True)

    st.divider()
    st.markdown("### 🔽 篩選與排序")
    max_price = st.slider("最高每晚預算 (TWD)", 1000, 30000, 15000, 500)
    min_rating = st.slider("最低評分", 0.0, 10.0, 7.0, 0.5)
    filter_breakfast   = st.checkbox("僅顯示含早餐")
    filter_free_cancel = st.checkbox("僅顯示免費取消")
    sort_by = st.selectbox("排序方式", ["每晚價格(TWD)", "評分", "超值分數"])

    st.divider()
    search_btn = st.button("🚀 開始搜尋比價", use_container_width=True, type="primary")

# ─── 主頁面 ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-banner">
  <div class="hero-title">🏨 訂房比價系統</div>
  <div class="hero-sub">一次輸入，同步比較 Booking.com · Agoda · Trip.com · Hotels.com</div>
</div>
""", unsafe_allow_html=True)

if not search_btn:
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.info("**① 輸入目的地**\n\n城市或飯店名稱", icon="🗺️")
    with c2: st.info("**② 選擇日期與人數**\n\n入住/退房日期及人數", icon="📅")
    with c3: st.info("**③ 點擊搜尋**\n\n同時查詢多個平台", icon="🔍")
    with c4: st.info("**④ 比較結果**\n\n自動整理超值排行", icon="💰")
    st.markdown("""<div class="warning-box">⚠️ <b>注意：</b>實際爬蟲模式需安裝
    <code>chromedriver</code>，各平台可能設有反爬蟲機制。建議先以 <b>Demo 模式</b> 體驗功能。
    </div>""", unsafe_allow_html=True)
    st.stop()

# ─── 執行搜尋 ──────────────────────────────────────────────────────────────────
ci_str, co_str = checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d")
all_results, bar = [], st.progress(0, text="準備搜尋中...")

if demo_mode:
    bar.progress(30, text="產生模擬資料中...")
    time.sleep(0.6)
    all_results = generate_mock_results(destination, nights)
    bar.progress(100, text="完成！")
else:
    scrapers = []
    if use_booking: scrapers.append(BookingScraper(headless=headless))
    if use_agoda:   scrapers.append(AgodaScraper(headless=headless))
    if use_trip:    scrapers.append(TripScraper(headless=headless))
    if use_hotels:  scrapers.append(HotelsScraper(headless=headless))
    total = len(scrapers) or 1
    done = 0
    def _run(s):
        return s.search(destination, ci_str, co_str, int(adults), int(rooms), int(children))
    with concurrent.futures.ThreadPoolExecutor(max_workers=total) as pool:
        fs = {pool.submit(_run, s): s.PLATFORM_NAME for s in scrapers}
        for f in concurrent.futures.as_completed(fs):
            pn = fs[f]; done += 1; pct = int(done/total*95)
            try:
                res = f.result(); all_results.extend(res)
                bar.progress(pct, text=f"✅ {pn} 完成（{len(res)} 筆）")
            except Exception as e:
                bar.progress(pct, text=f"❌ {pn} 失敗: {e}")
    bar.progress(100, text="全部完成！")

time.sleep(0.3); bar.empty()
if not all_results:
    st.error("未取得任何結果，請確認網路連線或切換至 Demo 模式。"); st.stop()

# ─── 資料處理 ──────────────────────────────────────────────────────────────────
df_raw = results_to_dataframe(all_results)
best_full = find_best_deals(df_raw, top_n=len(df_raw))
if not best_full.empty and "超值分數" in best_full.columns:
    sm = best_full.set_index(["平台","飯店名稱"])["超值分數"].to_dict()
    df_raw["超值分數"] = df_raw.apply(lambda r: sm.get((r["平台"],r["飯店名稱"]),np.nan), axis=1)

df = df_raw[df_raw["每晚價格(TWD)"]<=max_price].copy()
df = df[df["評分"].fillna(0)>=min_rating]
if filter_breakfast:   df = df[df["_breakfast_raw"]==True]
if filter_free_cancel: df = df[df["_free_cancel_raw"]==True]
asc = not (sort_by in ["評分","超值分數"])
if sort_by in df.columns: df = df.sort_values(sort_by, ascending=asc)
disp = df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")

# ─── 摘要指標 ──────────────────────────────────────────────────────────────────
st.markdown(f"### 📊 「{destination}」搜尋結果")
m1,m2,m3,m4,m5 = st.columns(5)
with m1: st.metric("搜尋到筆數", f"{len(df)} 筆")
with m2: st.metric("最低每晚", f"NT$ {df['每晚價格(TWD)'].min():,.0f}" if not df.empty else "N/A")
with m3: st.metric("平均每晚", f"NT$ {df['每晚價格(TWD)'].mean():,.0f}" if not df.empty else "N/A")
with m4:
    avg_r = df["評分"].dropna().mean()
    st.metric("平均評分", f"{avg_r:.1f}/10" if not np.isnan(avg_r) else "N/A")
with m5: st.metric("住宿天數", f"{nights} 晚")
st.markdown("---")

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5 = st.tabs(
    ["🏆 超值推薦","📋 完整列表","🔄 跨平台比較","📈 平台分析","📥 匯出資料"])

with tab1:
    st.markdown("#### 🏆 綜合超值排行 Top 5")
    st.caption("依「價格 55% + 評分 35% + 含早餐/免費取消加分 10%」計算")
    best = find_best_deals(df, top_n=5)
    if best.empty:
        st.info("篩選後無結果，請放寬條件。")
    else:
        icons = ["🥇","🥈","🥉","4️⃣","5️⃣"]
        for i, row in best.iterrows():
            ci2, info = st.columns([1,7])
            with ci2:
                st.markdown(f"<div style='font-size:2.5rem;text-align:center'>{icons[i-1]}</div>",
                            unsafe_allow_html=True)
            with info:
                color = PLATFORM_COLORS.get(row["平台"],"#888")
                bf = "🍳" if row["含早餐"]=="✅" else ""
                fc = "🔄" if row["免費取消"]=="✅" else ""
                link = row.get("訂房連結","#")
                score_pct = int(float(row.get("超值分數",0))*100)
                st.markdown(f"""<div class="deal-card">
                  <span class="deal-score">超值分 {score_pct}</span>
                  <div class="deal-name">{row['飯店名稱']} {bf}{fc}</div>
                  <div class="deal-platform">
                    <span class="platform-badge" style="background:{color}">{row['平台']}</span>
                    &nbsp;評分：{row['評分']} / 10
                  </div>
                  <div class="deal-price">NT$ {float(row['每晚價格(TWD)']):,.0f}
                    <span style='font-size:.85rem;color:#78716c'>/ 晚</span></div>
                  <a href="{link}" target="_blank" style="font-size:.8rem;color:#0ea5e9">🔗 前往訂房</a>
                </div>""", unsafe_allow_html=True)

with tab2:
    st.markdown(f"#### 📋 所有結果（共 {len(disp)} 筆）")
    cols = [c for c in ["平台","飯店名稱","每晚價格(TWD)","房型","含早餐","免費取消",
                         "評分","評論數","含稅"] if c in disp.columns]
    def _sp(v):
        c = PLATFORM_COLORS.get(v,"#888")
        return f"background-color:{c}15;color:{c};font-weight:600"
    st.dataframe(
        disp[cols].style.applymap(_sp, subset=["平台"])
            .format({"每晚價格(TWD)":"NT$ {:,.0f}","評分":"{:.1f}"}, na_rep="-")
            .bar(subset=["每晚價格(TWD)"], color="#bfdbfe", vmin=0),
        use_container_width=True, height=480)

with tab3:
    st.markdown("#### 🔄 各飯店跨平台最低價比較")
    pivot = pivot_price_table(df)
    if pivot.empty:
        st.info("資料不足。")
    else:
        pcols = [c for c in pivot.columns if c not in ("飯店名稱","最低價","最低價平台")]
        def _hl(row):
            styles = [""]*len(row)
            try:
                vals = row[pcols].dropna()
                if vals.empty: return styles
                mv = vals.min()
                for i,c in enumerate(row.index):
                    if c in pcols and row[c]==mv:
                        styles[i]="background-color:#d1fae5;color:#065f46;font-weight:700"
            except: pass
            return styles
        fmt = {c:"NT$ {:,.0f}" for c in pcols}; fmt["最低價"]="NT$ {:,.0f}"
        st.dataframe(pivot.style.apply(_hl,axis=1).format(fmt,na_rep="—"),
                     use_container_width=True, height=400)
        st.caption("🟢 綠色 = 最便宜平台；— = 無此飯店資料")
    st.markdown("#### 各平台平均每晚價格")
    ps = get_platform_stats(df)
    if not ps.empty: st.bar_chart(ps.set_index("平台")["平均每晚價格"], color="#3b82f6")

with tab4:
    st.markdown("#### 📈 各平台統計摘要")
    ps = get_platform_stats(df)
    if ps.empty: st.info("資料不足。")
    else:
        st.dataframe(ps.style.format(
            {"平均每晚價格":"NT$ {:,.0f}","最低價":"NT$ {:,.0f}","平均評分":"{:.2f}"}),
            use_container_width=True)
    st.markdown("#### 💲 各飯店跨平台價差分析")
    psum = get_price_summary(df)
    if not psum.empty:
        st.dataframe(psum.style.format({
            "最低價":"NT$ {:,.0f}","最高價":"NT$ {:,.0f}",
            "平均價":"NT$ {:,.0f}","價差":"NT$ {:,.0f}","可省(%)":"{:.1f}%"})
            .bar(subset=["可省(%)"], color="#fde68a"), use_container_width=True)

with tab5:
    st.markdown("#### 📥 匯出資料")
    csv_path = "/tmp/hotel_results.csv"
    export_to_csv(disp, csv_path)
    with open(csv_path,"rb") as f: csv_bytes = f.read()
    st.download_button("⬇️ 下載 CSV（Excel 直接開啟中文）", csv_bytes,
        f"訂房比價_{destination}_{ci_str}.csv", "text/csv", use_container_width=True)
    ebuf = io.BytesIO()
    with pd.ExcelWriter(ebuf, engine="openpyxl") as writer:
        disp.to_excel(writer, "完整列表", index=False)
        find_best_deals(df, top_n=10).to_excel(writer, "超值推薦", index=True)
        get_price_summary(df).to_excel(writer, "價格摘要", index=False)
        get_platform_stats(df).to_excel(writer, "平台統計", index=False)
    ebuf.seek(0)
    st.download_button("⬇️ 下載 Excel（含 4 個工作表）", ebuf.getvalue(),
        f"訂房比價_{destination}_{ci_str}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True)
    st.markdown("---")
    st.markdown("**資料預覽（前 20 筆）：**")
    st.dataframe(disp.head(20), use_container_width=True)
