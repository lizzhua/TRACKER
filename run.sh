#!/bin/bash
# 切換到專案主要目錄
cd /Users/ziling/antigravity

# 確認 venv 存在並使用他執行 (或者手動指定路徑也可以)
# 使用絕對路徑以確保 cronjob/launchd 模式穩健
PYTHON_BIN="/Users/ziling/antigravity/venv/bin/python3"
CURRENT_DATE=$(date +'%Y-%m-%d')

echo "=====================================" >> logs/cron.log
echo "📅 開始執行每日排程: $(date)" >> logs/cron.log

# 1. 抓取專案內設的 venv python 執行主程式
$PYTHON_BIN main.py >> logs/cron.log 2>&1

echo "✅ 每日情報排程執行完畢: $(date)" >> logs/cron.log

# 2. 自動更新至 GitHub
echo "☁️ 準備備份資料至 GitHub..." >> logs/cron.log

# 確認是否有檔案變更 (如新的 HTML 報表、抓取紀錄等)
if [[ -n $(git status -s) ]]; then
    git add .
    git commit -m "chore(auto): daily report sync ${CURRENT_DATE}" >> logs/cron.log 2>&1
    git push origin main >> logs/cron.log 2>&1
    echo "☁️ GitHub 已成功定時更新同步: $(date)" >> logs/cron.log
else
    echo "☁️ GitHub 工作區無變動，略過推送。" >> logs/cron.log
fi

echo "=====================================" >> logs/cron.log
