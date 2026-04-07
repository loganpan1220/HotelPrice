"""
資料處理模組 — 將爬蟲結果彙整為 DataFrame，並進行分析
"""
import pandas as pd
import numpy as np
from scrapers.base_scraper import HotelResult


# 平台主題色設定
PLATFORM_COLORS = {
    "Booking.com": "#003580",
    "Agoda":       "#e5261d",
    "Trip.com":    "#1890ff",
    "Hotels.com":  "#d4111e",
}


def results_to_dataframe(results: list[HotelResult]) -> pd.DataFrame:
    """將 HotelResult 列表轉為 DataFrame"""
    if not results:
        return pd.DataFrame()
    rows = []
    for r in results:
        rows.append({
            "平台": r.platform,
            "飯店名稱": r.hotel_name,
            "每晚價格(TWD)": r.price,
            "房型": r.room_type,
            "含早餐": "✅" if r.breakfast else "❌",
            "免費取消": "✅" if r.free_cancel else "❌",
            "評分": r.rating if r.rating > 0 else np.nan,
            "評論數": r.review_count if r.review_count > 0 else np.nan,
            "含稅": "✅" if r.taxes_included else "❌",
            "訂房連結": r.url,
            # 原始值，供排序/計算用
            "_breakfast_raw": r.breakfast,
            "_free_cancel_raw": r.free_cancel,
            "_taxes_raw": r.taxes_included,
        })
    df = pd.DataFrame(rows)
    return df


def get_price_summary(df: pd.DataFrame) -> pd.DataFrame:
    """以飯店為單位，跨平台彙整最低/最高/平均價格"""
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby("飯店名稱")["每晚價格(TWD)"]
        .agg(
            最低價=lambda x: x.min(),
            最高價=lambda x: x.max(),
            平均價=lambda x: round(x.mean(), 0),
            平台數=lambda x: x.count(),
            價差=lambda x: x.max() - x.min(),
        )
        .reset_index()
        .sort_values("最低價")
    )
    # 計算可省金額百分比
    summary["可省(%)"] = (
        (summary["價差"] / summary["最高價"] * 100).round(1)
    )
    return summary


def get_platform_stats(df: pd.DataFrame) -> pd.DataFrame:
    """各平台統計：平均價、平均評分、飯店數量"""
    if df.empty:
        return pd.DataFrame()
    stats = (
        df.groupby("平台")
        .agg(
            飯店數=("飯店名稱", "count"),
            平均每晚價格=("每晚價格(TWD)", lambda x: round(x.mean(), 0)),
            最低價=("每晚價格(TWD)", "min"),
            平均評分=("評分", lambda x: round(x.dropna().mean(), 2) if not x.dropna().empty else np.nan),
        )
        .reset_index()
    )
    return stats


def find_best_deals(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """綜合評分：價格評分 + 評分加權，找出最超值選項"""
    if df.empty or "每晚價格(TWD)" not in df.columns:
        return pd.DataFrame()

    tmp = df.copy()
    tmp = tmp[tmp["每晚價格(TWD)"] > 0].copy()
    if tmp.empty:
        return pd.DataFrame()

    # 價格越低分數越高（反轉標準化）
    p_min, p_max = tmp["每晚價格(TWD)"].min(), tmp["每晚價格(TWD)"].max()
    if p_max == p_min:
        tmp["_price_score"] = 1.0
    else:
        tmp["_price_score"] = 1 - (tmp["每晚價格(TWD)"] - p_min) / (p_max - p_min)

    # 評分標準化
    r_vals = tmp["評分"].fillna(0)
    r_min, r_max = r_vals.min(), r_vals.max()
    if r_max == r_min:
        tmp["_rating_score"] = 0.5
    else:
        tmp["_rating_score"] = (r_vals - r_min) / (r_max - r_min)

    # 含早餐 / 免費取消加分
    tmp["_bonus"] = (
        tmp["_breakfast_raw"].astype(float) * 0.05 +
        tmp["_free_cancel_raw"].astype(float) * 0.05
    )

    # 綜合分數
    tmp["超值分數"] = (
        tmp["_price_score"] * 0.55 +
        tmp["_rating_score"] * 0.35 +
        tmp["_bonus"]
    ).round(3)

    result = (
        tmp[["平台", "飯店名稱", "每晚價格(TWD)", "評分", "含早餐", "免費取消", "超值分數", "訂房連結"]]
        .sort_values("超值分數", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )
    result.index += 1  # 從 1 開始
    return result


def pivot_price_table(df: pd.DataFrame) -> pd.DataFrame:
    """建立飯店 × 平台的價格樞紐表"""
    if df.empty:
        return pd.DataFrame()
    pivot = df.pivot_table(
        index="飯店名稱",
        columns="平台",
        values="每晚價格(TWD)",
        aggfunc="min",
    ).reset_index()
    # 加上最低價欄
    price_cols = [c for c in pivot.columns if c != "飯店名稱"]
    pivot["最低價"] = pivot[price_cols].min(axis=1)
    pivot["最低價平台"] = pivot[price_cols].idxmin(axis=1)
    pivot = pivot.sort_values("最低價")
    return pivot


def export_to_csv(df: pd.DataFrame, path: str = "hotel_results.csv") -> str:
    """匯出為 CSV（UTF-8 BOM，Excel 可直接開啟中文）"""
    df_export = df.drop(
        columns=[c for c in df.columns if c.startswith("_")], errors="ignore"
    )
    df_export.to_csv(path, index=False, encoding="utf-8-sig")
    return path
