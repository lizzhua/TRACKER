"""
AVEDA 品牌情報系統 - Gemini LLM 客戶端
封裝 Google Gemini API 呼叫，統一處理重試與錯誤。
使用新版 google-genai SDK。
"""

import json
import logging
import time
from typing import Optional

from google import genai
from google.genai import types

import config

logger = logging.getLogger(__name__)

# 初始化 Gemini Client
_client = None


def _get_client():
    """延遲初始化 Gemini client（只建立一次）"""
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY 未設定，請檢查 .env 檔案")
        _client = genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info(f"Gemini client 已初始化，使用模型: {config.GEMINI_MODEL}")
    return _client


def call_llm(prompt: str, max_retries: int = 3) -> Optional[str]:
    """
    呼叫 Gemini API 並回傳文字結果。

    Args:
        prompt: 傳送給 LLM 的提示詞
        max_retries: 重試次數

    Returns:
        LLM 回應的文字內容；失敗時回傳 None
    """
    client = _get_client()

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("強制等待 10 秒以避免觸發 API 限制...")
            time.sleep(10)
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=config.GEMINI_TEMPERATURE,
                    max_output_tokens=config.GEMINI_MAX_OUTPUT_TOKENS,
                ),
            )
            text = response.text.strip()
            logger.debug(f"LLM 回應（前 200 字）: {text[:200]}")
            return text

        except Exception as e:
            logger.warning(f"LLM 呼叫失敗（第 {attempt}/{max_retries} 次）: {e}")
            if attempt < max_retries:
                wait = 2 ** attempt  # 指數退避: 2, 4, 8 秒
                logger.info(f"等待 {wait} 秒後重試...")
                time.sleep(wait)

    logger.error("LLM 呼叫已達最大重試次數，放棄")
    return None


def call_llm_json(prompt: str, max_retries: int = 3) -> Optional[dict]:
    """
    呼叫 Gemini API 並解析 JSON 回應。

    Args:
        prompt: 傳送給 LLM 的提示詞（應要求回傳 JSON）
        max_retries: 重試次數

    Returns:
        解析後的字典；失敗時回傳 None
    """
    text = call_llm(prompt, max_retries)
    if text is None:
        return None

    # 嘗試從回應中提取 JSON（LLM 有時會包裹在 ```json ... ``` 中）
    cleaned = text
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1]
    if "```" in cleaned:
        cleaned = cleaned.split("```", 1)[0]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失敗: {e}\n原始回應: {text[:300]}")
        return None

def call_llm_json_with_image(prompt: str, image) -> Optional[list]:
    """
    透過 Gemini Vision 處理圖片與 Prompt 組合，並解析出 JSON。
    """
    client = _get_client()

    for attempt in range(1, 4):
        try:
            logger.info("強制等待 10 秒以避免觸發 API 限制...")
            time.sleep(10)
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # 降低溫度以獲取穩定的 JSON 結構
                ),
            )
            text = response.text.strip()
            
            # 清理 JSON Markdown Block
            if "```json" in text:
                text = text.split("```json", 1)[1]
            if "```" in text:
                text = text.split("```", 1)[0]
            text = text.strip()
            
            return json.loads(text)

        except Exception as e:
            logger.warning(f"Vision LLM 分析失敗（第 {attempt}/3 次）: {e}")
            if attempt < 3:
                time.sleep(2 ** attempt)

    logger.error("Vision LLM 呼叫已達最高重試次數")
    return None

# ─── 測試入口 ─────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    result = call_llm("用一句話描述 AVEDA 這個品牌。")
    if result:
        print(f"LLM 回應: {result}")
    else:
        print("LLM 呼叫失敗，請確認 GEMINI_API_KEY 是否正確")
