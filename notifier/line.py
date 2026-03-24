"""
aespa 情報系統 - LINE Messaging API 通知模組
取代已廢棄之 LINE Notify，透過 LINE 官方帳號發送推播通知。
"""

import logging
import requests
from typing import Optional

import config
from collector.models import DailyReport

logger = logging.getLogger(__name__)


def send_line_message(user_id: str, access_token: str, message: str) -> bool:
    """
    透過 LINE Messaging API 發送推播訊息 (Push Message)。

    Args:
        user_id: 接收者的 LINE User ID (U 開頭)
        access_token: LINE Channel Access Token
        message: 訊息文字

    Returns:
        True 表示發送成功，False 表示失敗
    """
    api_url = "https://api.line.me/v2/bot/message/push"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"LINE 發送成功 → User ID: {user_id}")
            return True
        else:
            logger.error(f"LINE 發送失敗: HTTP {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"LINE 連線異常: {e}")
        return False


def format_daily_summary(report: DailyReport) -> str:
    """
    將 DailyReport 格式化為適合 LINE 的純文字摘要。
    (LINE Messaging API 純文字不支援 Markdown)

    Args:
        report: DailyReport 物件

    Returns:
        格式化的文字摘要
    """
    total = max(report.total_items, 1)
    pos_pct = round(report.positive_count / total * 100)
    neg_pct = round(report.negative_count / total * 100)

    lines = [
        f"【🌌 aespa SYNK: 每日情報庫】",
        f"⏳ 日期：{report.date}",
        f"",
        f"💿 本日深度探勘 {report.total_items} 筆最新輿情：",
        f"  🦋 正向: {report.positive_count} 筆 ({pos_pct}%)",
        f"  👾 異常: {report.negative_count} 筆 ({neg_pct}%)",
        f"  🪐 中立: {report.neutral_count} 筆",
    ]

    # 負面預警
    if report.negative_count > 0:
        lines.append(f"")
        lines.append(f"⚠️ 系統異狀：偵測到 {report.negative_count} 筆黑粉攻擊或爭議，請提高警覺！")

    # Top 熱門關鍵字
    if report.top_products:
        lines.append(f"")
        lines.append(f"🌌 KWANGYA 熱議焦點 Top 3：")
        for kw in report.top_products[:3]:
            lines.append(f"  ✧ {kw['keyword']} ({kw['count']}次)")

    # 活動通知或動態
    if report.events:
        lines.append(f"")
        lines.append(f"🔮 最新系統情報預警：")
        lines.append(f"   攔截到 {len(report.events)} 個近期強烈動態：")
        for event in report.events[:3]:
            title = event.get('event_title') or '社群特別關注'
            desc = event.get('event_description') or event.get('event_detail') or ''
            
            lines.append(f" ✨ {title}")
            if desc:
                lines.append(f"   ✧ {desc[:40]}...")

    # 附上詳細報表網址
    lines.append(f"")
    lines.append(f"🕸️ 點擊下方網址，觀看完整動態圖表與儀表板：")
    lines.append(f"https://lizzhua.github.io/TRACKER/")

    return "\n".join(lines)


def notify(report: DailyReport, user_id: Optional[str] = None, token: Optional[str] = None) -> bool:
    """
    發送每日摘要通知至 LINE。

    Args:
        report: DailyReport 物件
        user_id: 指定 LINE User ID（覆寫 config）
        token: 指定 Channel Access Token（覆寫 config）

    Returns:
        是否成功發送
    """
    target_user_id = user_id or config.LINE_USER_ID
    target_token = token or config.LINE_CHANNEL_ACCESS_TOKEN
    
    if not target_user_id or not target_token:
        logger.error("未設定 LINE_USER_ID 或 LINE_CHANNEL_ACCESS_TOKEN，無法發送 LINE 通知")
        return False

    message = format_daily_summary(report)
    logger.info(f"準備發送每日摘要至 LINE (User ID: {target_user_id})...")

    return send_line_message(target_user_id, target_token, message)


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
        print("\n💠 LINE 發送成功！請查看您的手機 LINE。")
    else:
        print("\n💥 發送失敗，請確認 .env 中的 LINE_CHANNEL_ACCESS_TOKEN 和 LINE_USER_ID 是否正確填入 (請勿包含不當引號)。")
