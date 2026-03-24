"""
aespa 情報系統 - Telegram 通知模組
透過 Telegram Bot API 發送推播通知，支援 Markdown 格式。
"""

import logging
import requests
from typing import Optional

import config
from collector.models import DailyReport

logger = logging.getLogger(__name__)


def send_telegram(chat_id: str, bot_token: str, message: str) -> bool:
    """
    透過 Telegram API 發送訊息。

    Args:
        chat_id: 接收者的 Chat ID
        bot_token: Telegram Bot Token
        message: 訊息內容（支援 HTML 或 MarkdownV2）

    Returns:
        True 表示發送成功，False 表示失敗
    """
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(api_url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Telegram 發送成功 → Chat ID: {chat_id}")
            return True
        else:
            logger.error(f"Telegram 發送失敗: HTTP {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram 連線異常: {e}")
        return False


def format_daily_summary(report: DailyReport) -> str:
    """
    將 DailyReport 格式化為適合 Telegram 的 HTML 摘要。

    Args:
        report: DailyReport 物件

    Returns:
        格式化的文字摘要
    """
    total = max(report.total_items, 1)
    pos_pct = round(report.positive_count / total * 100)
    neg_pct = round(report.negative_count / total * 100)

    # 運用 HTML 標籤讓主旨更明顯 (<b> 粗體, <i> 斜體 等)
    lines = [
        f"<b>🌌 aespa SYNK: 每日情報庫 — {report.date}</b>",
        f"",
        f"💿 <b>深度探勘 {report.total_items} 筆最新輿情：</b>",
        f"  🦋 <b>正向</b> {report.positive_count} 筆 (<i>{pos_pct}%</i>)",
        f"  👾 <b>異常</b> {report.negative_count} 筆 (<i>{neg_pct}%</i>)",
        f"  🪐 <b>中立</b> {report.neutral_count} 筆",
    ]

    # 負面預警
    if report.negative_count > 0:
        lines.append(f"")
        lines.append(f"⚠️ <b>系統異狀：偵測到 {report.negative_count} 筆黑粉攻擊或爭議，請提高警覺！</b>")

    # Top 熱門關鍵字
    if report.top_products:
        lines.append(f"")
        lines.append(f"🚀 <b>KWANGYA 熱議焦點 Top 3：</b>")
        for kw in report.top_products[:3]:
            lines.append(f"  • {kw['keyword']} ({kw['count']}次)")

    # 活動通知或動態
    if report.events:
        lines.append(f"")
        lines.append(f"⚡ <b>最新系統情報預警：</b>")
        lines.append(f"   攔截到 {len(report.events)} 個近期強烈動態：")
        for event in report.events[:3]:
            title = event.get('event_title') or '社群特別關注'
            desc = event.get('event_description') or event.get('event_detail') or ''
            
            lines.append(f" ✨ <b>{title}</b>")
            if desc:
                lines.append(f"   <i>{desc[:60]}...</i>")

    # 附上詳細報表網址
    lines.append(f"")
    lines.append(f"🕸️ <b>點擊下方網址，觀看完整動態圖表與儀表板：</b>")
    lines.append(f"https://lizzhua.github.io/TRACKER/")

    return "\n".join(lines)


def notify(report: DailyReport, chat_id: Optional[str] = None, token: Optional[str] = None) -> bool:
    """
    發送每日摘要通知至 Telegram。

    Args:
        report: DailyReport 物件
        chat_id: 指定 Chat ID（覆寫 config）
        token: 指定 Bot Token（覆寫 config）

    Returns:
        是否成功發送
    """
    target_chat_id = chat_id or config.TELEGRAM_CHAT_ID
    target_token = token or config.TELEGRAM_BOT_TOKEN
    
    if not target_chat_id or not target_token:
        logger.error("未設定 TELEGRAM_CHAT_ID 或 TELEGRAM_BOT_TOKEN，無法發送 Telegram 通知")
        return False

    message = format_daily_summary(report)
    logger.info(f"準備發送每日摘要至 Telegram (Chat ID: {target_chat_id})...")

    return send_telegram(target_chat_id, target_token, message)


# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_report = DailyReport(
        date="2026-03-23",
        total_items=19,
        positive_count=7,
        negative_count=6,
        neutral_count=6,
        top_products=[
            {"keyword": "aespa", "count": 12},
            {"keyword": "Karina", "count": 4},
            {"keyword": "Winter", "count": 2},
        ],
        events=[
            {"event_type": "concert", "event_title": "aespa 台北演唱會搶票預熱", "event_detail": "aespa 即將來台開唱，各大社群論壇如 Threads 開始熱烈討論搶票攻略與應援準備！", "event_date": "2026-03-23"},
        ],
        items=[],
    )

    print("發送測試訊息中...")
    success = notify(test_report)
    if success:
        print("\n💠 Telegram 發送成功！請查看您的手機 Telegram。")
    else:
        print("\n💥 發送失敗，請確認 .env 中的 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 是否正確。")
