# apps/primary_dictation/urls.py

from django.shortcuts import redirect
from django.urls import path

from . import views


def primary_dictation_home(request):
    return redirect("primary_word_set_list")


urlpatterns = [
    path("", primary_dictation_home, name="primary_dictation_home"),
    path("sets/", views.word_set_list, name="primary_word_set_list"),
    path("sets/<int:set_id>/", views.word_set_detail, name="primary_word_set_detail"),
    path("sets/<int:set_id>/start/", views.dictation_start, name="primary_dictation_start"),
    path("sessions/<int:session_id>/", views.dictation_session, name="primary_dictation_session"),
    path("sessions/<int:session_id>/submit/", views.dictation_submit, name="primary_dictation_submit"),
    path("sessions/<int:session_id>/result/", views.dictation_result, name="primary_dictation_result"),
]
