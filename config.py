"""
aespa 情報系統 - 統一設定檔
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ───────────────────────────────────────────────
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
IMESSAGE_RECIPIENT = os.getenv("IMESSAGE_RECIPIENT", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")

# ─── 搜尋設定 ───────────────────────────────────────────────
# 中文關鍵字
KEYWORDS_ZH = [
    "aespa",
    "aespa 回歸",
    "aespa 演唱會",
    "Karina",
    "Winter",
    "Ningning",
    "Giselle"
]

# 英文關鍵字
KEYWORDS_EN = [
    "aespa comeback",
    "aespa tour",
    "aespa Supernova",
    "aespa Drama",
    "aespa members",
    "aespa live"
]

# Tavily 專用關鍵字（精簡版，減少 API 消耗）
KEYWORDS_TAVILY = [
    "aespa 最新評價",
    "aespa 演唱會",
    "aespa 專輯回歸"
]

# SerpAPI 搜尋參數
SEARCH_PARAMS_ZH = {
    "engine": "google",
    "gl": "tw",         # 地區：台灣
    "hl": "zh-TW",      # 語系：繁體中文
    "num": 10,           # 每次搜尋結果數
    "tbs": "qdr:d",     # 時間範圍：過去 24 小時
}

SEARCH_PARAMS_EN = {
    "engine": "google",
    "gl": "us",          # 地區：美國
    "hl": "en",          # 語系：英文
    "num": 10,
    "tbs": "qdr:d",
}

# ─── LLM 設定 ───────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_TEMPERATURE = 0.3          # 低溫度 → 更穩定的分析結果
GEMINI_MAX_OUTPUT_TOKENS = 2048

# ─── 路徑設定 ───────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
DB_PATH = os.path.join(DATA_DIR, "aespa_tracker.db")
LOG_DIR = os.path.join(BASE_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "aespa_tracker.log")
TEMPLATES_DIR = os.path.join(BASE_DIR, "reporter", "templates")

# 確保目錄存在
for d in [DATA_DIR, REPORTS_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)
