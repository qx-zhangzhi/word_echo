import re
from difflib import SequenceMatcher


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_keywords(raw_keywords: str) -> list[str]:
    if not raw_keywords:
        return []

    raw_keywords = raw_keywords.replace("\n", ",")
    items = [x.strip() for x in raw_keywords.split(",") if x.strip()]

    seen = set()
    results = []
    for item in items:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(item)

    return results


def calc_similarity_score(reference: str, transcript: str) -> float:
    ref = normalize_text(reference)
    hyp = normalize_text(transcript)

    if not ref or not hyp:
        return 0.0

    return round(SequenceMatcher(None, ref, hyp).ratio() * 100, 1)


def calc_length_score(reference: str, transcript: str) -> float:
    ref_words = normalize_text(reference).split()
    hyp_words = normalize_text(transcript).split()

    if not ref_words or not hyp_words:
        return 0.0

    ref_len = len(ref_words)
    hyp_len = len(hyp_words)

    ratio = min(hyp_len / ref_len, 1.0)
    return round(ratio * 100, 1)


def calc_keywords_score(raw_keywords: str, transcript: str) -> tuple[float, list[str], list[str]]:
    keywords = parse_keywords(raw_keywords)
    hyp = normalize_text(transcript)

    if not keywords:
        return 100.0, [], []

    hit = []
    missed = []

    for kw in keywords:
        normalized_kw = normalize_text(kw)
        if normalized_kw and normalized_kw in hyp:
            hit.append(kw)
        else:
            missed.append(kw)

    score = round(len(hit) * 100.0 / len(keywords), 1)
    return score, hit, missed


def build_feedback(
    similarity_score: float,
    length_score: float,
    keyword_score: float,
    hit_keywords: list[str],
    missed_keywords: list[str],
) -> str:
    parts = []

    parts.append(f"内容相似度：{similarity_score}")
    parts.append(f"长度覆盖率：{length_score}")
    parts.append(f"关键词命中率：{keyword_score}")

    if hit_keywords:
        parts.append("已命中关键词：" + ", ".join(hit_keywords))

    if missed_keywords:
        parts.append("未命中关键词：" + ", ".join(missed_keywords))

    if similarity_score >= 80:
        parts.append("整体回答与参考答案较接近。")
    elif similarity_score >= 60:
        parts.append("整体回答基本贴题，但表达还可以更完整。")
    else:
        parts.append("回答与参考答案差距较大，建议多听多跟读。")

    return "\n".join(parts)


def score_attempt(reference_answer: str, raw_keywords: str, transcript: str) -> dict:
    similarity_score = calc_similarity_score(reference_answer, transcript)
    length_score = calc_length_score(reference_answer, transcript)
    keyword_score, hit_keywords, missed_keywords = calc_keywords_score(raw_keywords, transcript)

    overall = round(
        similarity_score * 0.5 +
        keyword_score * 0.3 +
        length_score * 0.2,
        1,
    )

    feedback = build_feedback(
        similarity_score=similarity_score,
        length_score=length_score,
        keyword_score=keyword_score,
        hit_keywords=hit_keywords,
        missed_keywords=missed_keywords,
    )

    return {
        "score_overall": overall,
        "score_similarity": similarity_score,
        "score_keywords": keyword_score,
        "score_length": length_score,
        "feedback": feedback,
    }
