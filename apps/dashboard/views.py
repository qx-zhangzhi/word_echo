from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from apps.practice.models import PracticeRecord
from apps.vocab.models import Word


@login_required
def home(request):
    words = Word.objects.filter(user=request.user)
    records = PracticeRecord.objects.filter(user=request.user)

    total_words = words.count()
    forgotten_words = words.filter(is_forgotten=True).count()
    total_practices = records.count()
    correct_practices = records.filter(is_correct=True).count()

    accuracy = 0
    if total_practices:
        accuracy = round(correct_practices * 100.0 / total_practices, 1)

    top_wrong_words = words.order_by("-wrong_count")[:10]

    context = {
        "total_words": total_words,
        "forgotten_words": forgotten_words,
        "total_practices": total_practices,
        "accuracy": accuracy,
        "top_wrong_words": top_wrong_words,
    }
    return render(request, "dashboard/home.html", context)
