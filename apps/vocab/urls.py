from django.urls import path
from . import views

urlpatterns = [
    path("", views.word_list, name="word_list"),
    path("add/", views.word_create, name="word_create"),
    path("<int:pk>/", views.word_detail, name="word_detail"),
    path("<int:pk>/edit/", views.word_update, name="word_update"),
    path("<int:pk>/delete/", views.word_delete, name="word_delete"),
]
