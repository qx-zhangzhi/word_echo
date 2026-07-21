# -*- coding: utf-8 -*-
from __future__ import annotations

"""
phrase_ai.py

功能：
- 调用 LLM 翻译英文好句
- 返回中文翻译

支持：
- OpenAI 兼容接口（base_url）
"""

import logging
import os

from openai import OpenAI


logger = logging.getLogger(__name__)


# ======================
# Config
# ======================

MODEL_BASE_URL = os.getenv(
    "LLM_BASE_URL",
    "http://10.199.30.166:8001/v1",
)

MODEL_API_KEY = os.getenv(
    "LLM_API_KEY",
    "",
)

MODEL_NAME = os.getenv(
    "LLM_MODEL",
    "llama-3.1-8b",
)

TIMEOUT = 60


# ======================
# Core
# ======================

def _build_prompt(english_text: str) -> str:
    return f"""
你是一个专业英语学习助手。请把下面这句英文翻译成自然、准确、适合英语学习者理解的中文。

要求：
1. 只返回中文翻译
2. 不要解释
3. 不要加 markdown
4. 不要加引号
5. 保持原句意思准确

英文句子:
{english_text}
"""


def translate_phrase_with_ai(english_text: str) -> str:
    """
    调用 LLM 将英文句子翻译为中文
    """
    text = (english_text or "").strip()
    if not text:
        return ""

    client = OpenAI(
        api_key=MODEL_API_KEY,
        base_url=MODEL_BASE_URL,
    )

    prompt = _build_prompt(text)

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一个专业的英汉翻译助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            timeout=TIMEOUT,
        )

        content = resp.choices[0].message.content or ""
        return content.strip()

    except Exception as e:
        logger.error(f"[PHRASE AI ERROR] text={text[:100]} err={e}")
        return ""
