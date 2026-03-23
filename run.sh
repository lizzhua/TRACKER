#!/bin/bash

# 補上 Mac launchd 預設遺失的環境變數路徑 (確保能找到 Homebrew 甚至 Conda 的 python3)
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# 切換到專案主要目錄
cd /Users/ziling/antigravity

echo "=====================================" >> logs/cron.log
echo "📅 開始執行每日排程: $(date)" >> logs/cron.log

# 抓取系統最高優先權的 python3 執行主程式
python3 main.py >> logs/cron.log 2>&1

echo "✅ 每日排程執行完畢: $(date)" >> logs/cron.log
echo "=====================================" >> logs/cron.log
