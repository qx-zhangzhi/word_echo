import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SynonymItemInput:
    word: str
    usage_context: str = ""
    fixed_sentence: str = ""
    comparison_note: str = ""


def parse_synonym_words(raw_text: str) -> list[str]:
    if not raw_text:
        return []

    parts = re.split(r"[,，;；、\n\r]+", raw_text)
    results = []
    seen = set()

    for item in parts:
        item = re.sub(r"^\s*(?:[-*•]+|\d+[.)、])\s*", "", item).strip()
        if not item:
            continue
        if len(item) > 100:
            item = item[:100].rstrip()
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(item)

    return results


def parse_synonym_item_lines(raw_text: str) -> list[SynonymItemInput]:
    if not raw_text:
        return []

    if "|" not in raw_text and re.search(r"[,，;；、]", raw_text):
        return [SynonymItemInput(word=word) for word in parse_synonym_words(raw_text)]

    results = []
    seen = set()
    for raw_line in re.split(r"[\n\r]+", raw_text):
        line = re.sub(r"^\s*(?:[-*•]+|\d+[.)、])\s*", "", raw_line).strip()
        if not line:
            continue

        pieces = [part.strip() for part in re.split(r"\s*\|\s*", line, maxsplit=3)]
        if len(pieces) == 1:
            word, usage_context, fixed_sentence, comparison_note = pieces[0], "", "", ""
        elif len(pieces) == 2:
            word, usage_context, fixed_sentence, comparison_note = pieces[0], pieces[1], "", ""
        elif len(pieces) == 3:
            word, usage_context, fixed_sentence, comparison_note = pieces[0], pieces[1], pieces[2], ""
        else:
            word, usage_context, fixed_sentence, comparison_note = pieces

        if not word:
            continue
        word = word[:100].rstrip()
        lowered = word.casefold()
        if lowered in seen:
            continue
        seen.add(lowered)
        results.append(SynonymItemInput(
            word=word,
            usage_context=usage_context[:100].rstrip(),
            fixed_sentence=fixed_sentence,
            comparison_note=comparison_note,
        ))

    if results:
        return results

    return [SynonymItemInput(word=word) for word in parse_synonym_words(raw_text)]
