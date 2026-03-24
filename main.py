#!/usr/bin/env python3
"""
aespa 情報系統 - 主流程入口 (混合引擎版)
支援: 
1. Browser Agent (Playwright + Gemini Vision) 擷取社群(Dcard/Threads)
2. Tavily AI Search (Tavily API + Gemini Text LLM) 搜尋新聞輿情
"""

import argparse
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from collector.models import CollectedItem, SentimentResult, EventResult
from analyzer.sentiment import analyze_sentiments
from analyzer.event_extractor import extract_events
from reporter.generator import build_daily_report, generate_html
from notifier.telegram import notify
import json

def load_seen_urls():
    path = os.path.join(config.DATA_DIR, "seen_urls.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except:
            pass
    return set()

def save_seen_urls(seen: set):
    path = os.path.join(config.DATA_DIR, "seen_urls.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, indent=2, ensure_ascii=False)

def setup_logging():
    os.makedirs(config.LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

def main(dry_run: bool = False):
    logger = logging.getLogger("main")
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info("🌿 aespa 情報系統 - 混合引擎版啟動")
    logger.info(f"   日期: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   Dry run: {dry_run}")
    logger.info("=" * 60)

    try:
        items, sentiments, events = [], [], []
        seen_urls = load_seen_urls()
        
        def filter_new_items(source_items):
            new_items = []
            for it in source_items:
                # 排除截圖搜尋網址，因為搜尋頁面每天都在變，不要去重
                if "search?" in it.url:
                    new_items.append(it)
                elif it.url not in seen_urls:
                    seen_urls.add(it.url)
                    new_items.append(it)
                else:
                    logger.debug(f"   ⏭️ 略過已處理過的網址: {it.url}")
            return new_items

        # ── 引擎 A: Browser Agent ──────────────────────────
        logger.info("📸 [引擎A] 啟動 Browser Agent 進行社群長截圖...")
        from collector.browser_collector import take_screenshots
        screenshots = take_screenshots()

        if screenshots:
            logger.info("🧠 [引擎A] LLM Vision 判讀並結構化截圖內容...")
            from analyzer.vision_extractor import extract_from_image
            
            for img_path in screenshots:
                raw_results = extract_from_image(img_path)
                for r in raw_results:
                    url = r.get("url", "https://gemini.google.com")
                    
                    item = CollectedItem(
                        title=r.get("title", "無標題"),
                        snippet=r.get("snippet", ""),
                        url=url,
                        source=r.get("source", "Unknown"),
                        language=r.get("language", "zh"),
                        keyword=r.get("keyword", "aespa")
                    )
                    
                    try:
                        conf = float(r.get("confidence", 0.5))
                    except:
                        conf = 0.5

                    sent = SentimentResult(
                        sentiment=r.get("sentiment", "neutral"),
                        confidence=conf,
                        reason=r.get("reason", ""),
                        source_url=url
                    )
                    
                    evt = EventResult(
                        has_event=bool(r.get("has_event", False)),
                        event_type=r.get("event_type"),
                        event_detail=r.get("event_detail"),
                        source_url=url
                    )
                    
                    items.append(item)
                    sentiments.append(sent)
                    events.append(evt)
            logger.info(f"   ✅ [引擎A] 成功辨識出 {len(screenshots)} 張截圖內的資訊")

        # ── 引擎 B: Tavily 搜尋 ────────────────────────────
        logger.info("🌐 [引擎B] 啟動 Tavily AI 搜尋網路輿情...")
        from collector.tavily_api import collect_tavily
        tavily_items = collect_tavily()

        if tavily_items:
            tavily_items = filter_new_items(tavily_items)
            
            if tavily_items:
                logger.info(f"   取得 {len(tavily_items)} 筆全新結果，進入 LLM 分析...")
                from analyzer.sentiment import analyze_sentiments
                from analyzer.event_extractor import extract_events
                
                tavily_sentiments = analyze_sentiments(tavily_items)
                tavily_events = extract_events(tavily_items)
                
                items.extend(tavily_items)
                sentiments.extend(tavily_sentiments)
                events.extend(tavily_events)
                logger.info(f"   ✅ [引擎B] 完成 {len(tavily_items)} 筆資訊處理")

        # ── 引擎 C: SerpAPI (傳統 Google 搜尋) ───────────────
        if config.SERPAPI_KEY:
            logger.info("📡 [引擎C] 啟動 SerpAPI 進行 Google 傳統分析...")
            from collector.search_api import collect_all
            from collector.scraper import enrich_items
            
            serp_items = collect_all()
            if serp_items:
                serp_items = filter_new_items(serp_items)
                
                if serp_items:
                    logger.info("   📄 [引擎C] 正在擷取搜尋結果網頁內文...")
                    serp_items = enrich_items(serp_items)
                    
                    logger.info(f"   🧠 [引擎C] LLM 正在處理網頁內文...")
                    serp_sentiments = analyze_sentiments(serp_items)
                    serp_events = extract_events(serp_items)
                    
                    items.extend(serp_items)
                    sentiments.extend(serp_sentiments)
                    events.extend(serp_events)
                    logger.info(f"   ✅ [引擎C] 完成 {len(serp_items)} 筆資訊處理")

        # ── 引擎 D: Apify (自動化 Google 採集) ───────────────
        if config.APIFY_API_TOKEN:
            logger.info("🤖 [引擎D] 啟動 Apify 雲端無頭 Google 採集...")
            from collector.apify_api import collect_apify
            
            apify_items = collect_apify()
            if apify_items:
                apify_items = filter_new_items(apify_items)
                
                if apify_items:
                    logger.info("   📄 [引擎D] Apify 擷取了搜尋結果清單...")
                    # Apify 抓到的是標題與摘要，這通常足以讓 LLM 分析（類似 Tavily）
                    # 為了避免超出 Gemini RPM 限制，我們一樣分批餵給分析器
                    
                    logger.info(f"   🧠 [引擎D] LLM 正在處理 {len(apify_items)} 筆網頁摘要...")
                    apify_sentiments = analyze_sentiments(apify_items)
                    apify_events = extract_events(apify_items)
                    
                    items.extend(apify_items)
                    sentiments.extend(apify_sentiments)
                    events.extend(apify_events)
                    logger.info(f"   ✅ [引擎D] 完成 {len(apify_items)} 筆資訊處理")

        # ── 驗證結果 ───────────────────────────────────────
        if not items:
            logger.warning("⚠️ 兩個引擎皆未發現任何相關討論，流程結束")
            return

        # ── Phase 3: 報告 ──────────────────────────────────
        logger.info("📊 準備生成 Dashboard 報告...")
        report = build_daily_report(items, sentiments, events)
        report_path = generate_html(report)
        logger.info(f"   報告已生成: {report_path}")

        # ── Phase 4: 通知 ──────────────────────────────────
        if dry_run:
            logger.info("📱 [Dry Run] 跳過 LINE 通知")
            from notifier.line import format_daily_summary
            summary = format_daily_summary(report)
            logger.info(f"   訊息預覽:\n{summary}")
        else:
            logger.info("📱 發送 LINE 通知...")
            success = notify(report)
            if success:
                logger.info("   ✅ LINE 通知發送成功")
            else:
                logger.error("   ❌ LINE 通知發送失敗")

        # ── Phase 5: 備份 (Vault Backup) ──────────────────────
        logger.info("💾 準備建立每日 Markdown 備份...")
        vault_path = "/Users/ziling/aespa vault"
        os.makedirs(vault_path, exist_ok=True)
        backup_file = os.path.join(vault_path, "歡迎.md")
        
        try:
            md_content = f"# ✨ aespa KWANGYA情報中心\n\n"
            md_content += f"> 🕒 自動備份日期：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md_content += f"## 📊 數據摘要 ({report.date})\n"
            md_content += f"- 🔍 總探索筆數：{report.total_items}\n"
            md_content += f"- 🟢 正面評價：{report.positive_count}\n"
            md_content += f"- 🔴 負面評價：{report.negative_count}\n"
            md_content += f"- ⚪ 中立評價：{report.neutral_count}\n\n"
            
            if report.top_products:
                md_content += f"## 🔥 社群熱門關鍵字\n"
                for kw in report.top_products[:5]:
                    md_content += f"- **{kw['keyword']}** ({kw['count']} 次)\n"
                md_content += "\n"
                
            if report.events:
                md_content += f"## 🎉 近期動態 / 社群話題\n"
                for ev in report.events:
                    title = ev.get('event_title') or '社群動態'
                    desc = ev.get('event_description') or ev.get('event_detail') or ''
                    date_info = ev.get('event_date') or ''
                    
                    md_content += f"### 🔸 {title}\n"
                    if date_info:
                        md_content += f"**時間：** {date_info}\n"
                    md_content += f"{desc}\n\n"
                    
            md_content += f"---\n*自動報表路徑：`{report_path}`*\n"

            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(md_content)
            logger.info(f"   ✅ 已成功更新 Markdown 備份至: {backup_file}")
        except Exception as e:
            logger.error(f"   ❌ Markdown 備份失敗: {e}")

        # ── 完成 ──────────────────────────────────────────
        save_seen_urls(seen_urls)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info(f"✅ 全部流程完成！耗時 {elapsed:.1f} 秒")
        logger.info(f"   分析總計: {len(items)} 篇貼文/文章")
        logger.info(f"   正面: {report.positive_count} | 負面: {report.negative_count} | 中立: {report.neutral_count}")
        logger.info(f"   報告路徑: {report_path}")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"❌ 執行過程發生錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="aespa 情報系統 - 混合引擎")
    parser.add_argument("--dry-run", action="store_true", help="不發送 iMessage 通知，僅預覽訊息")
    args = parser.parse_args()
    
    setup_logging()
    main(dry_run=args.dry_run)
