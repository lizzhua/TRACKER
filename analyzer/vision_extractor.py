"""
AVEDA 品牌情報系統 - 視覺情緒與活動分析
將 Playwright 獲取的長截圖送給 Gemini 2.0 Flash，直接一條龍抽取：貼文摘要、情緒、與活動資訊！
"""

import json
import logging
from PIL import Image
from typing import List

from analyzer.llm_client import call_llm_json_with_image

logger = logging.getLogger(__name__)

# 設計一個非常嚴謹的 JSON 分析 Prompt 用於圖片
VISION_PROMPT = """你是一位品牌輿情分析專家與數據擷取工程師。這是一張社群平台（如 Dcard 或 Threads）搜尋「AVEDA（或肯夢）」的結果截圖。
你的任務是從截圖中辨識出「所有提及 AVEDA 的各篇貼文」，並將每篇貼文的分析結果整理出一個完整的 JSON 陣列 (Array of objects)。

請確保完全遵守以下的 JSON 結構，必須回傳純 JSON 陣列，不要有 markdown codeblock，直接從 [ 開始：
[
  {
    "title": "該篇貼文標題",
    "snippet": "該篇貼文內容重點摘要（如果有內文）",
    "source": "若截圖是從 Dcard 來的就填 Dcard，Threads 來的填 Threads",
    "url": "依照來源填入預設網址，如 https://www.dcard.tw/search?query=AVEDA 或是 https://www.threads.net/search?q=AVEDA",
    "language": "zh",
    "keyword": "AVEDA",
    "sentiment": "positive 或是 negative 或是 neutral",
    "confidence": 0.9,
    "reason": "評分理由（20字內）",
    "has_event": true 或 false (這篇貼文有無提到新品上市、促銷、折扣、快閃店等任何活動?),
    "event_type": "new_product 或 promotion 或 pop_up 或 collaboration 或 other",
    "event_detail": "如果有活動，這裡填寫活動細節，沒有則填空字串"
  }
]

注意：
1. 每一篇不同的貼文，就是陣列裡的一個獨立物件。
2. 情緒一定要是 positive/negative/neutral 其中之一。
3. event_type 必須從選項中挑選，如果沒有，填 "other"。
"""

def extract_from_image(image_path: str) -> List[dict]:
    """
    將圖片推送到 Gemini 進行結構化擷取
    """
    logger.info(f"正在傳送圖片給 LLM 分析: {image_path}")
    
    try:
        img = Image.open(image_path)
    except Exception as e:
        logger.error(f"無法開啟圖片檔案 {image_path}: {e}")
        return []

    result = call_llm_json_with_image(VISION_PROMPT, img)
    
    if isinstance(result, list):
        logger.info(f"✅ 在圖片中辨識到 {len(result)} 篇貼文資料")
        return result
    else:
        logger.warning(f"⚠️ 回傳格式不如預期，預計為 list，但得到: {type(result)}")
        return []
