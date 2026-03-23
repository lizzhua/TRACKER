"""
AVEDA 品牌情報系統 - 網頁內文爬蟲
擷取搜尋結果的完整頁面內文，供 LLM 做更深入分析。
"""

import logging
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from collector.models import CollectedItem

logger = logging.getLogger(__name__)

# 模擬瀏覽器 User-Agent，避免被阻擋
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

# 請求逾時（秒）
TIMEOUT = 15


def scrape_content(url: str) -> Optional[str]:
    """
    擷取指定 URL 的主要文字內容。

    Args:
        url: 目標網頁 URL

    Returns:
        提取的純文字內容；失敗時回傳 None
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding  # 自動偵測編碼
    except requests.RequestException as e:
        logger.warning(f"無法擷取頁面 [{url}]: {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # 移除不需要的元素
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 嘗試取得 <article> 或 <main>，否則取整個 <body>
    content_tag = soup.find("article") or soup.find("main") or soup.find("body")
    if content_tag is None:
        return None

    text = content_tag.get_text(separator="\n", strip=True)

    # 基本清理：移除過多的空行
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)

    # 限制長度，避免超大文本送入 LLM
    max_chars = 5000
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n...(已截斷)"

    logger.debug(f"擷取完成 [{url}]: {len(cleaned)} 字")
    return cleaned


def enrich_items(items: List[CollectedItem]) -> List[CollectedItem]:
    """
    批次擷取 CollectedItem 的完整內文，填入 full_text 欄位。
    單一頁面失敗不中斷整體流程。

    Args:
        items: 搜集階段取得的項目列表

    Returns:
        已補充內文的項目列表（原地修改）
    """
    logger.info(f"開始擷取 {len(items)} 個頁面的內文...")
    success = 0

    for item in items:
        text = scrape_content(item.url)
        if text:
            item.full_text = text
            success += 1

    logger.info(f"內文擷取完成：成功 {success}/{len(items)} 筆")
    return items


# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    test_url = "https://www.aveda.com.tw/"
    print(f"測試擷取：{test_url}")
    content = scrape_content(test_url)
    if content:
        print(f"\n取得 {len(content)} 字：")
        print(content[:500])
    else:
        print("擷取失敗")
