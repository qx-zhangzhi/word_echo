import html
import re


def parse_highlight_words(raw_text: str) -> list[str]:
    if not raw_text:
        return []

    raw_text = raw_text.replace("\n", ",")
    parts = [item.strip() for item in raw_text.split(",")]

    results = []
    seen = set()

    for item in parts:
        if not item:
            continue
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(item)

    return results


def highlight_text(content: str, items: list[str]) -> str:
    """
    在文章正文内部高亮词或句式。
    支持：
    - word
    - phrase
    - sentence pattern
    """
    if not content:
        return ""

    safe_text = html.escape(content)
    safe_text = safe_text.replace("\n", "<br>")

    valid_items = [x.strip() for x in items if x and x.strip()]
    valid_items.sort(key=len, reverse=True)

    placeholders = {}

    for idx, item in enumerate(valid_items):
        placeholder = f"__MARK_{idx}__"
        placeholders[placeholder] = f"<mark>{html.escape(item)}</mark>"

        pattern = re.compile(re.escape(html.escape(item)), re.IGNORECASE)
        safe_text = pattern.sub(placeholder, safe_text)

    for placeholder, marked in placeholders.items():
        safe_text = safe_text.replace(placeholder, marked)

    return safe_text
