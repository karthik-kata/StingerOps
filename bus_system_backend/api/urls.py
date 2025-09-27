from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'bus-stops', views.BusStopViewSet)
router.register(r'classes', views.ClassViewSet)
router.register(r'buses', views.BusViewSet)
router.register(r'routes', views.RouteViewSet)
router.register(r'csv-upload', views.CSVUploadViewSet, basename='csv-upload')
router.register(r'bus-count', views.BusCountViewSet, basename='bus-count')

urlpatterns = [
    path('', include(router.urls)),
    path('status/', views.api_status, name='api-status'),
]
