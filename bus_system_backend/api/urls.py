from django.urls import path
from . import views

urlpatterns = [
    # System endpoints
    path('status/', views.api_status, name='api-status'),
    path('overview/', views.SystemOverviewView.as_view(), name='system-overview'),
    path('health/', views.SystemHealthView.as_view(), name='system-health'),
    
    # Building endpoints
    path('buildings/', views.BuildingListView.as_view(), name='building-list'),
    path('buildings/<uuid:pk>/', views.BuildingDetailView.as_view(), name='building-detail'),
    
    # Bus Stop endpoints
    path('bus-stops/', views.BusStopListView.as_view(), name='busstop-list'),
    path('bus-stops/<uuid:pk>/', views.BusStopDetailView.as_view(), name='busstop-detail'),
    
    # Source endpoints
    path('sources/', views.SourceListView.as_view(), name='source-list'),
    path('sources/<uuid:pk>/', views.SourceDetailView.as_view(), name='source-detail'),
    
    # Course endpoints
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<uuid:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    
    # Class Session endpoints
    path('classes/', views.ClassSessionListView.as_view(), name='classsession-list'),
    path('classes/<uuid:pk>/', views.ClassSessionDetailView.as_view(), name='classsession-detail'),
    
    # Bus endpoints
    path('buses/', views.BusListView.as_view(), name='bus-list'),
    path('buses/<uuid:pk>/', views.BusDetailView.as_view(), name='bus-detail'),
    
    # Route endpoints
    path('routes/', views.RouteListView.as_view(), name='route-list'),
    path('routes/<uuid:pk>/', views.RouteDetailView.as_view(), name='route-detail'),
    
    # CSV Upload endpoint
    path('csv-upload/', views.CSVUploadView.as_view(), name='csv-upload'),
    
    # Bus Management endpoints
    path('bus-count/', views.BusCountView.as_view(), name='bus-count'),
    
    # Analytics endpoints
    path('analytics/routes/', views.RouteUtilizationView.as_view(), name='route-utilization'),
    
    # Route Optimization endpoints
    path('optimize-routes/', views.RouteOptimizationView.as_view(), name='optimize-routes'),
    path('apply-routes/', views.ApplyOptimizedRoutesView.as_view(), name='apply-routes'),
    path('optimization/test/', views.OptimizationTestView.as_view(), name='optimization-test'),
]
