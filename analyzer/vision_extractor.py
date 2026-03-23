"""
aespa 情報系統 - 視覺情緒與活動分析
將 Playwright 獲取的長截圖送給 Gemini 2.0 Flash，直接一條龍抽取：貼文摘要、情緒、與活動資訊！
"""

import json
import logging
from PIL import Image
from typing import List

from analyzer.llm_client import call_llm_json_with_image

logger = logging.getLogger(__name__)

# 設計一個非常嚴謹的 JSON 分析 Prompt 用於圖片
VISION_PROMPT = """你是一位品牌輿情分析專家與數據擷取工程師。這是一張社群平台（Threads）搜尋「aespa」的結果截圖。
請分析圖中的發文標題、內文摘要、發文時間、讚數與留言數等元素，將這些貼文轉換成純粹的 JSON 格式清單回傳。

請回傳此 JSON 格式的陣列：
[
  {
    "title": "貼文的標題或第一句",
    "snippet": "貼文的詳細內容摘要",
    "source": "Threads",
    "url": "依照來源填入預設網址，如 https://www.threads.net/search?q=aespa",
    "language": "zh",
    "keyword": "aespa",
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
