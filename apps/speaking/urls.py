# apps/speaking/urls.py

from django.shortcuts import redirect
from django.urls import path

from . import views


def speaking_home(request):
    return redirect("speaking_topic_list")


urlpatterns = [
    path("", speaking_home, name="speaking_home"),

    path("review/", views.review_table, name="speaking_review_table"),
    path("topics/", views.topic_list, name="speaking_topic_list"),
    path("topics/create/", views.topic_create, name="speaking_topic_create"),
    path("topics/<int:topic_id>/", views.topic_detail, name="speaking_topic_detail"),
    path("topics/<int:topic_id>/questions/create/", views.question_create, name="speaking_question_create"),

    path("questions/<int:question_id>/", views.question_detail, name="speaking_question_detail"),
    path(
        "questions/<int:question_id>/answers/create/",
        views.create_answer,
        name="speaking_answer_create",
    ),
]
