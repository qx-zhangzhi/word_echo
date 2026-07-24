from django.urls import path
from . import views

urlpatterns = [
    path("", views.synonym_list, name="synonym_list"),
    path("add/", views.synonym_create, name="synonym_create"),
    path("ai/generate/", views.synonym_ai_generate, name="synonym_ai_generate"),
    path("review/", views.synonym_review_list, name="synonym_review_list"),
    path("<int:pk>/", views.synonym_detail, name="synonym_detail"),
    path("<int:pk>/edit/", views.synonym_update, name="synonym_update"),
    path("<int:pk>/review/", views.synonym_review, name="synonym_review"),
    path("<int:pk>/exam/", views.synonym_exam, name="synonym_exam"),
    path("<int:pk>/delete/", views.synonym_delete, name="synonym_delete"),
]
