"""
URL configuration for word_echo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("jianpu/", include("jianpu.urls")),
    path("", include("apps.dashboard.urls")),
    path("words/", include("apps.vocab.urls")),
    path("practice/", include("apps.practice.urls")),
    path("writing/", include("apps.writing.urls")),
    path("synonyms/", include("apps.synonyms.urls")),
    path("phrases/", include("apps.phrases.urls")),
    path("speaking/", include("apps.speaking.urls")),
    path("primary-dictation/", include("apps.primary_dictation.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
