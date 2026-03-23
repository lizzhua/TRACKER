"""
aespa 情報系統 - SerpAPI 搜尋模組
透過 SerpAPI 對 Google Search 進行中文關鍵字搜尋 (已精簡)。
"""

import logging
from typing import List

from serpapi import GoogleSearch

import config
from collector.models import CollectedItem

logger = logging.getLogger(__name__)


def search_google(keyword: str, lang: str = "zh", num: int = 3) -> List[CollectedItem]:
    if not config.SERPAPI_KEY:
        logger.error("SERPAPI_KEY 未設定，請檢查 .env 檔案")
        return []

    params = config.SEARCH_PARAMS_ZH.copy()
    params["q"] = keyword
    params["num"] = num
    params["api_key"] = config.SERPAPI_KEY

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
    except Exception as e:
        logger.error(f"SerpAPI 搜尋失敗 [{keyword}]: {e}")
        return []

    items: List[CollectedItem] = []
    organic = results.get("organic_results", [])

    for r in organic:
        item = CollectedItem(
            title=r.get("title", ""),
            snippet=r.get("snippet", ""),
            url=r.get("link", ""),
            source="Google Search",
            language=lang,
            keyword=keyword,
            date=r.get("date", None),
        )
        items.append(item)
        logger.debug(f"搜尋結果: {item.title} ({item.url})")

    logger.info(f"[{lang.upper()}] 關鍵字「{keyword}」取得 {len(items)} 筆結果")
    return items


def collect_all() -> List[CollectedItem]:
    all_items: List[CollectedItem] = []
    seen_urls: set = set()

    # 為了省流，只抓中文前2大關鍵字
    for kw in config.KEYWORDS_ZH[:2]:
        results = search_google(kw, lang="zh", num=3)
        for item in results:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                all_items.append(item)

    logger.info(f"搜尋完成，共取得 {len(all_items)} 筆不重複結果")
    return all_items
