# jianpu/urls.py

from django.urls import path

from . import views

app_name = "jianpu"

urlpatterns = [
    path("", views.score_list, name="score_list"),
    path("new/", views.create_score, name="create_score"),
    path(
        "new/template/<str:template_key>/",
        views.create_score_from_template,
        name="create_score_from_template",
    ),
    path("<int:score_id>/", views.score_editor, name="score_editor"),
    path("<int:score_id>/print/", views.score_print, name="score_print"),
    path("<int:score_id>/save/", views.save_score, name="save_score"),
    path("<int:score_id>/delete/", views.delete_score, name="delete_score"),
]
