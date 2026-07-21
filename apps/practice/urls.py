from django.urls import path
from . import views

urlpatterns = [
    path("", views.practice_setup, name="practice_setup"),
    path("run/", views.practice_run, name="practice_run"),
    path("submit/", views.practice_submit, name="practice_submit"),
    path("result/<int:session_id>/", views.practice_result, name="practice_result"),
    path("wrong-words/", views.wrong_word_list, name="wrong_word_list"),
]
