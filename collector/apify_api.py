"""
AVEDA 品牌情報系統 - Apify 搜尋模組
透過 Apify 的 Google Search Scraper Actor 進行大規模網頁採集
"""

import logging
from typing import List

from apify_client import ApifyClient

import config
from collector.models import CollectedItem

logger = logging.getLogger(__name__)


def collect_apify() -> List[CollectedItem]:
    """
    呼叫 Apify 的 google-search-scraper 取得搜尋結果。
    具有極高的穩定度且不會被驗證碼阻擋。
    """
    if not config.APIFY_API_TOKEN:
        logger.warning("未設定 APIFY_API_TOKEN，將跳過 Apify 搜尋")
        return []

    client = ApifyClient(config.APIFY_API_TOKEN)
    items: List[CollectedItem] = []
    seen_urls = set()

    # 精簡版：1個中文主力 + 1個英文主力，每頁拿前 3 名
    target_queries = [config.KEYWORDS_TAVILY[0]]
    if config.KEYWORDS_EN:
        target_queries.append(config.KEYWORDS_EN[0])

    run_input = {
        "queries": "\n".join(target_queries),
        "maxPagesPerQuery": 1,
        "resultsPerPage": 3
    }

    try:
        logger.info("正在啟動 Apify Actor: [apify/google-search-scraper]...")
        
        # 呼叫並同步等待結果 (可能需數十秒)
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        # 從資料集中逐筆拉回資料
        for task in client.dataset(run["defaultDatasetId"]).iterate_items():
            query_term = task.get("searchQuery", {}).get("term", "AVEDA")
            organic_results = task.get("organicResults", [])
            
            for r in organic_results:
                url = r.get("url", "")
                
                # 排除重複網址
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                
                item = CollectedItem(
                    title=r.get("title", ""),
                    snippet=r.get("description", ""),
                    url=url,
                    source="Apify Google Search",
                    language="zh",
                    keyword=query_term,
                )
                items.append(item)
                logger.debug(f"Apify 發現: {item.title} ({item.url})")

    except Exception as e:
        logger.error(f"Apify 執行失敗: {e}")

    logger.info(f"Apify 網路爬取完成，共取得 {len(items)} 筆不重複結果")
    return items

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    res = collect_apify()
    print(f"取得 {len(res)} 筆")
