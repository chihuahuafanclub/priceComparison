from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from backend.views import get_data

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html')),
    path('api/search/', get_data, name='get_data' ),
]
