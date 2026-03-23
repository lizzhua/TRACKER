#!/bin/bash
# 切換到專案主要目錄
cd /Users/ziling/antigravity

# 確認 venv 存在並使用他執行 (或者手動指定路徑也可以)
# 使用絕對路徑以確保 cronjob/launchd 模式穩健
PYTHON_BIN="/Users/ziling/antigravity/venv/bin/python3"

echo "=====================================" >> logs/cron.log
echo "📅 開始執行每日排程: $(date)" >> logs/cron.log

# 抓取專案內設的 venv python 執行主程式
$PYTHON_BIN main.py >> logs/cron.log 2>&1

echo "✅ 每日排程執行完畢: $(date)" >> logs/cron.log
echo "=====================================" >> logs/cron.log
