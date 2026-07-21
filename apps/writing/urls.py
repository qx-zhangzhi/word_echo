from django.urls import path
from . import views

urlpatterns = [
    path("", views.writing_list, name="writing_list"),
    path("add/", views.writing_create, name="writing_create"),
    path("<int:pk>/", views.writing_detail, name="writing_detail"),
    path("<int:pk>/edit/", views.writing_update, name="writing_update"),
    path("<int:pk>/delete/", views.writing_delete, name="writing_delete"),
]
