# -*- coding: utf-8 -*-
from __future__ import annotations

"""
vocab_ai.py

功能：
- 调用 LLM 补全单词信息
- 返回结构化 JSON

支持：
- OpenAI 兼容接口（base_url）
"""

import json
import logging
import os
from typing import Any, Dict

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

def _build_prompt(word: str) -> str:
    return f"""
你是一个专业英语词典助手。请根据给定单词，返回 JSON，不要输出任何解释、markdown、代码块。

单词: {word}

返回字段：
{{
  "phonetic": "音标",
  "meaning_cn": "中文释义",
  "part_of_speech": "词性",
  "example_sentence": "英文例句,必须英文回答, 符合雅思7分",
  "note": "简短记忆提示",
  "difficulty": 3
}}

要求：
1. 必须返回合法 JSON
2. difficulty 范围 1-5
3. example_sentence 简单自然（适合初中水平）
4. 所有字段必须存在
"""


def _parse_json(content: str) -> Dict[str, Any]:
    content = content.strip()

    # 去掉 ```json ``` 包裹（很多模型会加）
    if content.startswith("```"):
        content = content.strip("`")
        if "json" in content:
            content = content.replace("json", "", 1).strip()

    try:
        return json.loads(content)
    except Exception as e:
        logger.warning(f"[LLM JSON parse error] content={content[:200]} err={e}")
        return {}


def call_llm_fill_word(word: str) -> Dict[str, Any]:
    """
    调用 LLM 返回结构化词典信息
    """
    client = OpenAI(
        api_key=MODEL_API_KEY,
        base_url=MODEL_BASE_URL,
    )

    prompt = _build_prompt(word)

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你必须只返回合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            timeout=TIMEOUT,
        )

        content = resp.choices[0].message.content or ""

        return _parse_json(content)

    except Exception as e:
        logger.error(f"[LLM ERROR] word={word} err={e}")
        return {}
