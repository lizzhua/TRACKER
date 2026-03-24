"""
aespa 情報系統 - iMessage 通知模組
透過 macOS AppleScript 發送 iMessage 推播通知。
"""

import logging
import subprocess
from typing import Optional

import config
from collector.models import DailyReport

logger = logging.getLogger(__name__)


def send_imessage(recipient: str, message: str) -> bool:
    """
    透過 macOS Messages.app 發送 iMessage。

    Args:
        recipient: 收件者電話號碼或 Apple ID（如 +886912345678）
        message: 訊息內容

    Returns:
        True 表示發送成功，False 表示失敗
    """
    # 將訊息中的特殊字元跳脫，避免 AppleScript 注入
    escaped_msg = message.replace("\\", "\\\\").replace('"', '\\"')
    escaped_recipient = recipient.replace("\\", "\\\\").replace('"', '\\"')

    applescript = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{escaped_recipient}" of targetService
        send "{escaped_msg}" to targetBuddy
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            logger.info(f"iMessage 發送成功 → {recipient}")
            return True
        else:
            logger.error(f"iMessage 發送失敗: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("iMessage 發送逾時 (30s)")
        return False
    except Exception as e:
        logger.error(f"iMessage 發送異常: {e}")
        return False


def format_daily_summary(report: DailyReport) -> str:
    """
    將 DailyReport 格式化為適合 iMessage 的文字摘要。

    Args:
        report: DailyReport 物件

    Returns:
        格式化的文字摘要
    """
    total = max(report.total_items, 1)
    pos_pct = round(report.positive_count / total * 100)
    neg_pct = round(report.negative_count / total * 100)

    lines = [
        f"🌌 aespa 每日情報 — {report.date}",
        f"",
        f"💿 分析 {report.total_items} 筆輿情：",
        f"  🦋 正面 {report.positive_count} 筆 ({pos_pct}%)",
        f"  👾 負面 {report.negative_count} 筆 ({neg_pct}%)",
        f"  🪐 中立 {report.neutral_count} 筆",
    ]

    # 負面預警
    if report.negative_count > 0:
        lines.append(f"")
        lines.append(f"⚠️ 偵測到 {report.negative_count} 筆負面輿情，請關注！")

    # Top 產品
    if report.top_products:
        lines.append(f"")
        lines.append(f"🚀 熱門關鍵字：")
        for kw in report.top_products[:3]:
            lines.append(f"  • {kw['keyword']} ({kw['count']}次)")

    # 活動通知
    if report.events:
        lines.append(f"")
        lines.append(f"⚡ 偵測到 {len(report.events)} 個活動/事件：")
        for event in report.events[:3]:
            # 防呆：確保文字不是 None
            title = event.get('event_title') or '未命名活動'
            desc = event.get('event_description') or event.get('event_detail') or ''
            
            lines.append(f"🔸 {title}")
            if desc:
                lines.append(f"   {desc[:40]}...")

    return "\n".join(lines)


def notify(report: DailyReport, recipient: Optional[str] = None) -> bool:
    """
    發送每日摘要通知。

    Args:
        report: DailyReport 物件
        recipient: 收件者（預設使用 config 設定）

    Returns:
        是否成功發送
    """
    target = recipient or config.IMESSAGE_RECIPIENT
    if not target:
        logger.error("未設定 IMESSAGE_RECIPIENT，無法發送通知")
        return False

    message = format_daily_summary(report)
    logger.info(f"準備發送每日摘要至 {target}...")
    logger.debug(f"訊息內容:\n{message}")

    return send_imessage(target, message)


# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # 模擬測試報告
    test_report = DailyReport(
        date="2026-03-18",
        total_items=15,
        positive_count=8,
        negative_count=3,
        neutral_count=4,
        top_products=[
            {"keyword": "Gemini 模型", "count": 5},
            {"keyword": "Gemini API", "count": 3},
            {"keyword": "aespa", "count": 2},
        ],
        events=[
            {"event_type": "promotion", "event_detail": "Gemini全館 85 折", "event_date": "2026-05-01"},
        ],
        items=[],
    )

    # 先印出摘要預覽
    summary = format_daily_summary(test_report)
    print("===== 訊息預覽 =====")
    print(summary)
    print("===================")

    # 嘗試發送（需要設定 .env 中的 IMESSAGE_RECIPIENT）
    # notify(test_report)
