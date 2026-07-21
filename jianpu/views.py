# jianpu/views.py

import copy
import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import JianpuScore, default_cell, default_score_data


def make_cell(note="", lyric="", octave=0, duration="quarter", tie=""):
    return {
        "note": str(note or ""),
        "lyric": str(lyric or ""),
        "octave": int(octave or 0),
        "duration": str(duration or "quarter"),
        "tie": str(tie or ""),
    }


def normalize_cell(cell):
    """
    兼容旧数据：
    旧版 cell 可能是 "1"
    新版 cell 是 {"note": "1", "lyric": "", "octave": 0, "duration": "quarter"}
    """
    if isinstance(cell, dict):
        note = str(cell.get("note", "") or "")
        lyric = str(cell.get("lyric", "") or "")

        try:
            octave = int(cell.get("octave", 0) or 0)
        except (TypeError, ValueError):
            octave = 0

        duration = str(cell.get("duration", "quarter") or "quarter")
        tie = str(cell.get("tie", "") or "")
        if tie not in ["", "start", "middle", "end"]:
            tie = ""

        if octave not in [-1, 0, 1]:
            octave = 0

        if duration not in ["quarter", "eighth"]:
            duration = "quarter"

        return make_cell(
            note=note,
            lyric=lyric,
            octave=octave,
            duration=duration,
            tie=tie,
        )

    return make_cell(note=str(cell or ""))


def normalize_score_data(score_data):
    if not isinstance(score_data, list) or not score_data:
        return default_score_data()

    rows = []

    for row in score_data:
        if not isinstance(row, list):
            continue

        normalized_row = [normalize_cell(cell) for cell in row]

        if normalized_row:
            rows.append(normalized_row)

    if not rows:
        return default_score_data()

    return rows


def build_template_scores():
    return {
        "twinkle": {
            "title": "小星星",
            "key": "1=C",
            "time_signature": "4/4",
            "tempo": 90,
            "score_data": [
                [
                    make_cell("1", "一"),
                    make_cell("1", "闪"),
                    make_cell("5", "一"),
                    make_cell("5", "闪"),
                    make_cell("|"),
                    make_cell("6", "亮"),
                    make_cell("6", "晶"),
                    make_cell("5", "晶"),
                    make_cell("-"),
                    make_cell("|"),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                ],
                [
                    make_cell("4", "满"),
                    make_cell("4", "天"),
                    make_cell("3", "都"),
                    make_cell("3", "是"),
                    make_cell("|"),
                    make_cell("2", "小"),
                    make_cell("2", "星"),
                    make_cell("1", "星"),
                    make_cell("-"),
                    make_cell("|"),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                ],
            ],
        },
        "birthday": {
            "title": "生日快乐",
            "key": "1=C",
            "time_signature": "3/4",
            "tempo": 90,
            "score_data": [
                [
                    make_cell("5", "祝", octave=-1),
                    make_cell("5", "你", octave=-1),
                    make_cell("6", "生", octave=-1),
                    make_cell("5", "日", octave=-1),
                    make_cell("|"),
                    make_cell("1", "快"),
                    make_cell("7", "乐", octave=-1),
                    make_cell("-"),
                    make_cell("|"),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                ],
                [
                    make_cell("5", "祝", octave=-1),
                    make_cell("5", "你", octave=-1),
                    make_cell("6", "生", octave=-1),
                    make_cell("5", "日", octave=-1),
                    make_cell("|"),
                    make_cell("2", "快"),
                    make_cell("1", "乐"),
                    make_cell("-"),
                    make_cell("|"),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                ],
                [
                    make_cell("5", "祝", octave=-1),
                    make_cell("5", "你", octave=-1),
                    make_cell("5", "生"),
                    make_cell("3", "日"),
                    make_cell("|"),
                    make_cell("1", "快"),
                    make_cell("7", "乐", octave=-1),
                    make_cell("6", "呀", octave=-1),
                    make_cell("|"),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                ],
                [
                    make_cell("4", "祝"),
                    make_cell("4", "你"),
                    make_cell("3", "生"),
                    make_cell("1", "日"),
                    make_cell("|"),
                    make_cell("2", "快"),
                    make_cell("1", "乐"),
                    make_cell("-"),
                    make_cell("|"),
                    make_cell("", ""),
                    make_cell("", ""),
                    make_cell("", ""),
                ],
            ],
        },
    }

def score_list(request):
    scores = JianpuScore.objects.all()

    for score in scores:
        score.key_display = get_key_display(score.key)

    return render(
        request,
        "jianpu/score_list.html",
        {
            "scores": scores,
        },
    )


def create_score(request):
    score = JianpuScore.objects.create(
        title="未命名歌曲",
        key="1=C",
        time_signature="4/4",
        tempo=90,
        score_data=default_score_data(),
    )
    return redirect("jianpu:score_editor", score_id=score.id)


def create_score_from_template(request, template_key):
    templates = build_template_scores()
    template = templates.get(template_key)

    if not template:
        return redirect("jianpu:score_list")

    score = JianpuScore.objects.create(
        title=template["title"],
        key=template["key"],
        time_signature=template["time_signature"],
        tempo=template["tempo"],
        score_data=copy.deepcopy(template["score_data"]),
    )

    return redirect("jianpu:score_editor", score_id=score.id)

@ensure_csrf_cookie
def score_editor(request, score_id):
    score = get_object_or_404(JianpuScore, id=score_id)
    score_data = normalize_score_data(score.score_data)

    return render(
        request,
        "jianpu/score_editor.html",
        {
            "score": score,
            "score_data_json": json.dumps(score_data, ensure_ascii=False),
        },
    )

def score_print(request, score_id):
    score = get_object_or_404(JianpuScore, id=score_id)
    score_data = normalize_score_data(score.score_data)

    return render(
        request,
        "jianpu/score_print.html",
        {
            "score": score,
            "score_data": score_data,
            "key_display": get_key_display(score.key),
        },
    )


@require_POST
def save_score(request, score_id):
    try:
        score = get_object_or_404(JianpuScore, id=score_id)

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "ok": False,
                    "message": "数据格式错误",
                },
                status=400,
            )

        title = str(payload.get("title", "")).strip() or "未命名歌曲"
        key = str(payload.get("key", "")).strip() or "1=C"
        time_signature = str(payload.get("time_signature", "")).strip() or "4/4"

        try:
            tempo = int(payload.get("tempo", 90))
        except (TypeError, ValueError):
            tempo = 90

        score_data = normalize_score_data(payload.get("score_data"))

        score.title = title
        score.key = key
        score.time_signature = time_signature
        score.tempo = tempo
        score.score_data = score_data
        score.save()

        return JsonResponse(
            {
                "ok": True,
                "message": "已保存",
            }
        )

    except Exception as e:
        import traceback

        traceback.print_exc()

        return JsonResponse(
            {
                "ok": False,
                "message": f"后端保存失败：{type(e).__name__}: {e}",
            },
            status=500,
        )

@require_POST
def delete_score(request, score_id):
    score = get_object_or_404(JianpuScore, id=score_id)
    score.delete()

    return JsonResponse(
        {
            "ok": True,
            "message": "已删除",
        }
    )

def get_key_display(key):
    key_display_map = {
        "1=C": "1=C",
        "1=#C": "1=#C / bD",
        "1=bD": "1=#C / bD",
        "1=D": "1=D",
        "1=#D": "1=#D / bE",
        "1=bE": "1=#D / bE",
        "1=E": "1=E",
        "1=F": "1=F",
        "1=#F": "1=#F / bG",
        "1=bG": "1=#F / bG",
        "1=G": "1=G",
        "1=#G": "1=#G / bA",
        "1=bA": "1=#G / bA",
        "1=A": "1=A",
        "1=#A": "1=#A / bB",
        "1=bB": "1=#A / bB",
        "1=B": "1=B",
    }

    return key_display_map.get(key, key or "1=C")
