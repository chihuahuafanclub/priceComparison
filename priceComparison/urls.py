from django.contrib import admin
from django.urls import path
from backend.views import get_data

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/search/", get_data, name="get_data" ),
]
