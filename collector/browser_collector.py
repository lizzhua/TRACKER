"""
aespa 情報系統 - 瀏覽器自動截圖模組
使用 Playwright 直接啟動無頭瀏覽器，前往 Threads 搜尋頁面並擷取完整長截圖。
"""

import logging
import os
import time
from playwright.sync_api import sync_playwright

import config

logger = logging.getLogger(__name__)


def take_screenshots() -> list[str]:
    """訪問 Threads，並進行視窗截圖"""
    screenshots = []

    # 搜尋目標 URL，我們針對「aespa」進行重點搜尋
    urls = [
        ("threads", "https://www.threads.net/search?q=aespa&serp_type=real_time")
    ]

    os.makedirs(os.path.join(config.DATA_DIR, "screenshots"), exist_ok=True)

    with sync_playwright() as p:
        logger.info("正在啟動 Playwright 無頭瀏覽器...")
        # 啟動 Chrome
        browser = p.chromium.launch(headless=True)
        # 設定更大的視窗大小以擷取更多資訊
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 3000} 
        )
        page = context.new_page()

        for name, url in urls:
            try:
                logger.info(f"正在造訪搜尋頁面: {url} ({name})")
                
                # 考慮到社群網站使用大量非同步請求，networkidle 常常會等不到
                # 改用 domcontentloaded 加上固定的幾秒等待時間
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)
                
                # 滾動幾次來觸發 lazy loading
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 1000)")
                    time.sleep(1)
                
                # 給予網頁幾秒鐘去渲染內容
                time.sleep(3)

                filepath = os.path.join(config.DATA_DIR, "screenshots", f"{name}.png")
                # 針對整個網頁進行長截圖
                page.screenshot(path=filepath, full_page=True)
                screenshots.append(filepath)
                logger.info(f"✅ 截圖已儲存: {filepath}")

            except Exception as e:
                logger.error(f"❌ 擷取 {name} ({url}) 時發生錯誤: {e}")

        browser.close()

    return screenshots


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    res = take_screenshots()
    print("截圖清單:", res)
