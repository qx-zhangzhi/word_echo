from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.conf import settings
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

from .services import parse_synonym_item_lines

logger = logging.getLogger(__name__)


class SynonymAIError(RuntimeError):
    """A user-safe error raised when synonym generation cannot complete."""


def _parse_json(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        data = json.loads(text)
    except (TypeError, json.JSONDecodeError) as exc:
        raise SynonymAIError("AI 返回的内容格式不正确，请重试。") from exc
    if not isinstance(data, dict):
        raise SynonymAIError("AI 返回的内容格式不正确，请重试。")
    return data


def generate_synonym_data(headword: str, known_words: str = "") -> dict[str, Any]:
    word = (headword or "").strip()
    if not word:
        raise SynonymAIError("请先输入核心词。")
    if len(word) > 100:
        raise SynonymAIError("核心词不能超过 100 个字符。")
    api_key = settings.SYNONYM_AI_API_KEY
    if not api_key:
        raise SynonymAIError("尚未配置同义词 AI API，请设置 SYNONYM_AI_API_KEY。")

    known_items = parse_synonym_item_lines(known_words)
    known_text = "\n".join(item.word for item in known_items) or "无"

    prompt = f"""你是 IELTS 7.5 写作词汇辨析老师。请围绕主题 {word!r} 整理一组高频替换词/词组，风格要像“钱类词汇辨析”：按来源、语境、正式程度区分，不能只给普通同义词。
用户已知道这些词组，请保留它们并补充到总数 8 到 24 个：
{known_text}

只返回合法 JSON，不要输出 Markdown 或解释，格式如下：
{{
  "meaning_cn": "这个主题的中文说明",
  "items": [
    {{
      "word": "英文词或词组",
      "usage_context": "分类/语境，例如 个人收入 / Task 2、公司经营 / Task 1、政府税收",
      "fixed_sentence": "包含该词或词组的自然 IELTS 英文固定例句",
      "comparison_note": "中文说明：核心区别、正式程度、常见搭配、易混点"
    }}
  ],
  "usage_note": "用中文写 IELTS 建议、最容易混淆的几组、升级表达，适合直接显示在页面里",
  "practice_sentence": "一个适合主动替换练习的英文句子，句中用 ____ 标出替换位置"
}}
items 必须包含用户已知道的词组；补充项要常用、可写进 IELTS Task 1/Task 2；每个词必须有固定句子和明确区别；不要提供反义词；不确定时宁缺毋滥。"""
    request_data: dict[str, Any] = {
        "model": settings.SYNONYM_AI_MODEL,
        "messages": [
            {"role": "system", "content": "你必须只返回合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "timeout": settings.SYNONYM_AI_TIMEOUT,
    }
    temperature = str(getattr(settings, "SYNONYM_AI_TEMPERATURE", "")).strip()
    if temperature:
        request_data["temperature"] = float(temperature)

    try:
        response = OpenAI(api_key=api_key, base_url=settings.SYNONYM_AI_BASE_URL).chat.completions.create(
            **request_data
        )
        data = _parse_json(response.choices[0].message.content or "")
    except SynonymAIError:
        raise
    except AuthenticationError as exc:
        logger.exception("Synonym AI authentication failed")
        raise SynonymAIError("同义词 AI API Key 无效或已过期，请检查 SYNONYM_AI_API_KEY。") from exc
    except PermissionDeniedError as exc:
        logger.exception("Synonym AI permission denied")
        raise SynonymAIError("当前 API Key 没有访问同义词 AI 模型的权限。") from exc
    except NotFoundError as exc:
        logger.exception("Synonym AI model not found: %s", settings.SYNONYM_AI_MODEL)
        raise SynonymAIError(f"同义词 AI 模型不可用：{settings.SYNONYM_AI_MODEL}。请检查 SYNONYM_AI_MODEL。") from exc
    except BadRequestError as exc:
        logger.exception("Synonym AI request was rejected for %r", word)
        raise SynonymAIError("同义词 AI 请求参数不被模型支持，请检查模型和 temperature 配置。") from exc
    except RateLimitError as exc:
        logger.exception("Synonym AI rate limited")
        raise SynonymAIError("同义词 AI 请求过于频繁或额度不足，请稍后重试。") from exc
    except (APITimeoutError, APIConnectionError) as exc:
        logger.exception("Synonym AI request timed out or could not connect for %r", word)
        raise SynonymAIError("同义词 AI 连接超时，请稍后重试；必要时调大 SYNONYM_AI_TIMEOUT。") from exc
    except Exception as exc:
        logger.exception("Synonym AI request failed for %r", word)
        raise SynonymAIError("AI 服务暂时不可用，请稍后重试或手工填写。") from exc

    raw_items = data.get("items") or data.get("synonyms", [])
    item_lines = []
    if isinstance(raw_items, list):
        for item in raw_items:
            if isinstance(item, dict):
                item_word = str(item.get("word", "")).strip()
                if not item_word:
                    continue
                item_lines.append(" | ".join([
                    item_word,
                    str(item.get("usage_context", "")).strip(),
                    str(item.get("fixed_sentence", "")).strip(),
                    str(item.get("comparison_note", "")).strip(),
                ]).strip(" |"))
            else:
                item_lines.append(str(item))
    else:
        item_lines.append(str(raw_items or ""))

    items = parse_synonym_item_lines("\n".join(item_lines))
    merged = list(known_items)
    positions = {item.word.casefold(): index for index, item in enumerate(merged)}
    for item in items:
        lowered = item.word.casefold()
        if lowered in positions:
            current = merged[positions[lowered]]
            merged[positions[lowered]] = type(current)(
                word=current.word,
                usage_context=current.usage_context or item.usage_context,
                fixed_sentence=current.fixed_sentence or item.fixed_sentence,
                comparison_note=current.comparison_note or item.comparison_note,
            )
            continue
        positions[lowered] = len(merged)
        merged.append(item)
    if not merged:
        raise SynonymAIError("AI 未生成有效同义词，请重试或手工填写。")
    return {
        "meaning_cn": str(data.get("meaning_cn", ""))[:255].strip(),
        "synonym_words": "\n".join(
            " | ".join(part for part in [
                item.word,
                item.usage_context,
                item.fixed_sentence,
                item.comparison_note,
            ] if part)
            for item in merged
        ),
        "usage_note": str(data.get("usage_note", "")).strip(),
        "example_sentence": str(data.get("practice_sentence") or data.get("example_sentence", "")).strip(),
    }


def generate_synonym_exam(entry, items) -> dict[str, Any]:
    word = (entry.headword or "").strip()
    if not word:
        raise SynonymAIError("请先输入核心词。")
    api_key = settings.SYNONYM_AI_API_KEY
    if not api_key:
        raise SynonymAIError("尚未配置同义词 AI API，请设置 SYNONYM_AI_API_KEY。")

    item_lines = "\n".join(
        " | ".join(part for part in [
            item.word,
            item.usage_context,
            item.fixed_sentence,
            item.comparison_note or item.note,
        ] if part)
        for item in items
    )
    if not item_lines:
        raise SynonymAIError("这一组还没有可考试的词组，请先添加同义词。")

    prompt = f"""你是 IELTS 写作词汇教练。请基于下面这组同义词实时生成一道主动回忆题，目标是让学生真正掌握语境差异，而不是只背中文意思。
主题：{word}
中文释义：{entry.meaning_cn or "未填写"}
整体说明：{entry.usage_note or "未填写"}
同义词表：
{item_lines}

只返回合法 JSON，不要输出 Markdown，格式如下：
{{
  "question": "英文或中文题干，包含具体写作语境，要求学生填一个最合适的替换表达",
  "instruction": "一句中文作答要求",
  "acceptable_answers": ["必须来自同义词表中的一个或多个可接受英文答案"],
  "explanation": "中文说明：为什么这些答案合适，以及容易错用哪些词"
}}
acceptable_answers 必须完全使用同义词表里的英文词/词组；题目要能区分语境，不要泛泛问同义词。"""
    request_data: dict[str, Any] = {
        "model": settings.SYNONYM_AI_MODEL,
        "messages": [
            {"role": "system", "content": "你必须只返回合法 JSON。"},
            {"role": "user", "content": prompt},
        ],
        "timeout": settings.SYNONYM_AI_TIMEOUT,
    }
    temperature = str(getattr(settings, "SYNONYM_AI_TEMPERATURE", "")).strip()
    if temperature:
        request_data["temperature"] = float(temperature)

    try:
        response = OpenAI(api_key=api_key, base_url=settings.SYNONYM_AI_BASE_URL).chat.completions.create(
            **request_data
        )
        data = _parse_json(response.choices[0].message.content or "")
    except SynonymAIError:
        raise
    except AuthenticationError as exc:
        logger.exception("Synonym exam AI authentication failed")
        raise SynonymAIError("同义词 AI API Key 无效或已过期，请检查 SYNONYM_AI_API_KEY。") from exc
    except PermissionDeniedError as exc:
        logger.exception("Synonym exam AI permission denied")
        raise SynonymAIError("当前 API Key 没有访问同义词 AI 模型的权限。") from exc
    except NotFoundError as exc:
        logger.exception("Synonym exam AI model not found: %s", settings.SYNONYM_AI_MODEL)
        raise SynonymAIError(f"同义词 AI 模型不可用：{settings.SYNONYM_AI_MODEL}。请检查 SYNONYM_AI_MODEL。") from exc
    except BadRequestError as exc:
        logger.exception("Synonym exam AI request was rejected for %r", word)
        raise SynonymAIError("同义词 AI 请求参数不被模型支持，请检查模型和 temperature 配置。") from exc
    except RateLimitError as exc:
        logger.exception("Synonym exam AI rate limited")
        raise SynonymAIError("同义词 AI 请求过于频繁或额度不足，请稍后重试。") from exc
    except (APITimeoutError, APIConnectionError) as exc:
        logger.exception("Synonym exam AI request timed out or could not connect for %r", word)
        raise SynonymAIError("同义词 AI 连接超时，请稍后重试；必要时调大 SYNONYM_AI_TIMEOUT。") from exc
    except Exception as exc:
        logger.exception("Synonym exam AI request failed for %r", word)
        raise SynonymAIError("AI 服务暂时不可用，请稍后重试或手工填写。") from exc

    known = {item.word.casefold(): item.word for item in items}
    answers = []
    raw_answers = data.get("acceptable_answers", [])
    if isinstance(raw_answers, str):
        raw_answers = [raw_answers]
    if isinstance(raw_answers, list):
        for answer in raw_answers:
            lowered = str(answer).strip().casefold()
            if lowered in known and known[lowered] not in answers:
                answers.append(known[lowered])
    if not answers:
        answers = [items[0].word]

    return {
        "question": str(data.get("question", "")).strip() or f"请写出一个适合表达“{entry.meaning_cn or word}”的替换词组。",
        "instruction": str(data.get("instruction", "")).strip() or "写出一个最合适的英文词或词组。",
        "acceptable_answers": answers,
        "explanation": str(data.get("explanation", "")).strip() or "答案需要符合题目语境，并能自然写进 IELTS 句子。",
    }
