from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("reading/signals/", views.reading_signals, name="reading_signals"),
]
