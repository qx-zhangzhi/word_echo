# -*- coding: utf-8 -*-
from __future__ import annotations

"""
word_builder.py

功能：
- 构建单词默认数据
- 调用 LLM 自动补全
"""

import logging
from typing import Dict, Any

from .vocab_ai import call_llm_fill_word


logger = logging.getLogger(__name__)


# ======================
# Core
# ======================

def build_word_defaults(raw_word: str, use_ai: bool = True) -> Dict[str, Any]:
    """
    构建单词默认信息（支持 AI 自动补全）
    """

    word = (raw_word or "").strip().lower()

    base = {
        "word": word,
        "tts_text": word,
        "phonetic": "",
        "meaning_cn": "",
        "part_of_speech": "",
        "example_sentence": "",
        "note": "",
        "difficulty": 3,
        "is_active": True,
        "source_type": "manual",
    }

    if not word:
        return base

    if not use_ai:
        return base

    try:
        ai_data = call_llm_fill_word(word)

        if not isinstance(ai_data, dict):
            return base

        base.update({
            "phonetic": ai_data.get("phonetic", ""),
            "meaning_cn": ai_data.get("meaning_cn", ""),
            "part_of_speech": ai_data.get("part_of_speech", ""),
            "example_sentence": ai_data.get("example_sentence", ""),
            "note": ai_data.get("note", ""),
            "difficulty": _safe_int(ai_data.get("difficulty"), default=3),
            "source_type": "ai",
        })

    except Exception as e:
        logger.error(f"[build_word_defaults] word={word} err={e}")

    return base


# ======================
# Utils
# ======================

def _safe_int(value: Any, default: int = 3) -> int:
    try:
        v = int(value)
        return max(1, min(5, v))
    except Exception:
        return default
