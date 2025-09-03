from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/websites/', views.WebsiteAPIView.as_view(), name='website_api'),
    path('api/monitoring/', views.MonitoringAPIView.as_view(), name='monitoring_api'),
    path('api/load-websites/', views.LoadWebsitesAPIView.as_view(), name='load_websites_api'),
    path('website/<int:website_id>/', views.website_detail, name='website_detail'),
]
