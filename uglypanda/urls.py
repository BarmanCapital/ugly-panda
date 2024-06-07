"""
URL configuration for uglypanda project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
import re
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path("panda/", include("tgbot.urls")),
]

if not settings.DEBUG:
    # url_static = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    prefix = settings.STATIC_URL
    kwargs = {"document_root": settings.STATIC_ROOT}
    url_static = [re_path(r"^%s(?P<path>.*)$" % re.escape(prefix.lstrip("/")), serve, kwargs=kwargs), ]
    urlpatterns += url_static

