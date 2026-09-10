from django.urls import path

from . import views


urlpatterns = [
    path("", views.entry_list, name="cambridge_vocab_list"),
    path("import/", views.entry_import, name="cambridge_vocab_import"),
    path("new/", views.entry_create, name="cambridge_vocab_create"),
    path("<int:pk>/", views.entry_detail, name="cambridge_vocab_detail"),
    path("<int:pk>/edit/", views.entry_update, name="cambridge_vocab_update"),
    path("<int:pk>/delete/", views.entry_delete, name="cambridge_vocab_delete"),
    path("<int:pk>/toggle-learned/", views.entry_toggle_learned, name="cambridge_vocab_toggle_learned"),
]
