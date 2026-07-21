from django.urls import path
from . import views

urlpatterns = [
    path("", views.phrase_list, name="phrase_list"),
    path("add/", views.phrase_create, name="phrase_create"),
    path("translate/", views.phrase_translate_api, name="phrase_translate_api"),
    path("<int:pk>/", views.phrase_detail, name="phrase_detail"),
    path("<int:pk>/edit/", views.phrase_update, name="phrase_update"),
    path("<int:pk>/delete/", views.phrase_delete, name="phrase_delete"),
]
