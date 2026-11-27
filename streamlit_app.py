import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="東京の天気（過去1週間〜今後1週間）", layout="wide")
st.title("🌤️ 東京の天気（過去7日間・今後7日間）")

# Open-Meteo APIから東京の天気データを取得（過去7日＋未来7日）
# 東京の緯度: 35.6762, 経度: 139.6503
URL = "https://api.open-meteo.com/v1/forecast"
PARAMS = {
    "latitude": 35.6762,
    "longitude": 139.6503,
    "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
    "timezone": "Asia/Tokyo",
    "past_days": 7,
    "forecast_days": 7,
}

# WMO天気コードの簡易日本語変換
WEATHER_MAP = {
    0: "☀️ 快晴",
    1: "🌤️ 晴れ",
    2: "⛅ 一部曇り",
    3: "☁️ 曇り",
    45: "🌫️ 霧",
    48: "🌫️ 霧氷",
    51: "🌦️ 霧雨（弱）",
    53: "🌦️ 霧雨（中）",
    55: "🌦️ 霧雨（強）",
    61: "☔ 雨（弱）",
    63: "☔ 雨（中）",
    65: "☔ 雨（強）",
    71: "❄️ 雪（弱）",
    73: "❄️ 雪（中）",
    75: "❄️ 雪（強）",
    80: "🌦️ にわか雨（弱）",
    81: "🌦️ にわか雨（中）",
    82: "⛈️ にわか雨（強）",
    95: "⚡ 雷雨",
}

@st.cache_data(ttl=3600)  # 1時間キャッシュしてAPI負荷を軽減
def get_weather_data():
    res = requests.get(URL, params=PARAMS, timeout=10)
    res.raise_for_status()
    return res.json()

try:
    data = get_weather_data()
    daily = data["daily"]

    df = pd.DataFrame({
        "日付": pd.to_datetime(daily["time"]).strftime("%Y-%m-%d (%a)"),
        "天気": [WEATHER_MAP.get(code, f"その他({code})") for code in daily["weather_code"]],
        "最高気温 (℃)": daily["temperature_2m_max"],
        "最低気温 (℃)": daily["temperature_2m_min"],
        "降水量 (mm)": daily["precipitation_sum"],
    })

    # 区分（過去・今日・予報）を追加
    today_str = pd.Timestamp.now(tz="Asia/Tokyo").strftime("%Y-%m-%d")
    raw_dates = daily["time"]
    df.insert(1, "区分", [
        "📍 今日" if d == today_str else ("⏪ 過去" if d < today_str else "⏩ 予報")
        for d in raw_dates
    ])

    # 気温の推移グラフ
    st.subheader("📈 最高・最低気温の推移")
    chart_df = df.set_index("日付")[["最高気温 (℃)", "最低気温 (℃)"]]
    st.line_chart(chart_df, color=["#FF4B4B", "#1C83E1"])

    # 一覧テーブル
    st.subheader("📅 日別データ一覧")
    st.dataframe(df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"データの取得に失敗しました: {e}")
