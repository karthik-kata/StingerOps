from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
import logging
from typing import Dict, Any

from .models import (
    Building, BusStop, Course, ClassSession, Bus, Route, 
    RouteStop, RouteAssignment, Source
)
from .serializers import (
    BuildingSerializer, BusStopSerializer, SourceSerializer, CourseSerializer,
    ClassSessionSerializer, BusSerializer, RouteSerializer,
    RouteStopSerializer, RouteAssignmentSerializer,
    CSVUploadSerializer, BusCountSerializer, SystemOverviewSerializer,
    ErrorResponseSerializer, SuccessResponseSerializer,
    RouteOptimizationRequestSerializer, RouteOptimizationResultSerializer,
    ApplyOptimizedRoutesSerializer
)
from .services import (
    CSVProcessingService, BusManagementService, RouteService,
    AnalyticsService, DataValidationService, RouteOptimizationService
)


logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list views."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class BaseAPIView(APIView):
    """Base API view with common error handling."""
    
    def handle_exception(self, exc):
        """Handle exceptions with proper error responses."""
        logger.error(f"API Error in {self.__class__.__name__}: {str(exc)}", exc_info=True)
        
        if isinstance(exc, DjangoValidationError):
            return Response({
                'error': 'Validation Error',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
                'timestamp': timezone.now()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return super().handle_exception(exc)
    
    def create_success_response(self, message: str, data: Dict[Any, Any] = None) -> Response:
        """Create standardized success response."""
        response_data = {
            'message': message,
            'timestamp': timezone.now()
        }
        if data:
            response_data['data'] = data
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def create_error_response(self, error: str, details: Dict = None, 
                            status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
        """Create standardized error response."""
        response_data = {
            'error': error,
            'timestamp': timezone.now()
        }
        if details:
            response_data['details'] = details
        
        return Response(response_data, status=status_code)


# Building Views

class BuildingListView(generics.ListCreateAPIView):
    """List all buildings or create a new building."""
    queryset = Building.objects.filter(is_active=True)
    serializer_class = BuildingSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['code', 'is_active']
    search_fields = ['name', 'code', 'address']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['code', 'name']
    
    def post(self, request, *args, **kwargs):
        """Handle both JSON building creation and CSV upload."""
        # Check if this is a CSV upload
        if 'file' in request.FILES:
            return self.upload_csv(request)
        else:
            # Handle regular building creation
            return super().post(request, *args, **kwargs)
    
    def upload_csv(self, request):
        """Handle CSV file upload for buildings."""
        serializer = CSVUploadSerializer(data={'file': request.FILES['file'], 'data_type': 'buildings'})
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid upload data',
                'details': serializer.errors,
                'timestamp': timezone.now()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        
        try:
            CSVProcessingService.validate_csv_file(file)
            created_count, errors = CSVProcessingService.process_buildings_csv(file)
            
            response_data = {
                'created_count': created_count,
                'errors': errors,
                'success_rate': f"{((created_count / (created_count + len(errors))) * 100):.1f}%" if (created_count + len(errors)) > 0 else "0%"
            }
            
            if errors:
                return Response({
                    'message': f'Processed CSV with {len(errors)} errors. Created {created_count} buildings.',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_206_PARTIAL_CONTENT)
            else:
                return Response({
                    'message': f'Successfully created {created_count} buildings',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Buildings CSV processing error: {str(e)}", exc_info=True)
            return Response({
                'error': 'CSV processing failed',
                'details': {'detail': str(e)},
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BuildingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a building."""
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()


# Bus Stop Views

class BusStopListView(generics.ListCreateAPIView):
    """List all bus stops or create a new bus stop."""
    queryset = BusStop.objects.filter(is_active=True).select_related('building')
    serializer_class = BusStopSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['building', 'has_shelter', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'capacity', 'created_at']
    ordering = ['code', 'name']
    
    def post(self, request, *args, **kwargs):
        """Handle both JSON bus stop creation and CSV upload."""
        # Check if this is a CSV upload
        if 'file' in request.FILES:
            return self.upload_csv(request)
        else:
            # Handle regular bus stop creation
            return super().post(request, *args, **kwargs)
    
    def upload_csv(self, request):
        """Handle CSV file upload for bus stops."""
        serializer = CSVUploadSerializer(data={'file': request.FILES['file'], 'data_type': 'stops'})
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid upload data',
                'details': serializer.errors,
                'timestamp': timezone.now()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        
        try:
            CSVProcessingService.validate_csv_file(file)
            created_count, errors = CSVProcessingService.process_bus_stops_csv(file)
            
            response_data = {
                'created_count': created_count,
                'errors': errors,
                'success_rate': f"{((created_count / (created_count + len(errors))) * 100):.1f}%" if (created_count + len(errors)) > 0 else "0%"
            }
            
            if errors:
                return Response({
                    'message': f'Processed CSV with {len(errors)} errors. Created {created_count} bus stops.',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_206_PARTIAL_CONTENT)
            else:
                return Response({
                    'message': f'Successfully created {created_count} bus stops',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Bus stops CSV processing error: {str(e)}", exc_info=True)
            return Response({
                'error': 'CSV processing failed',
                'details': {'detail': str(e)},
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BusStopDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a bus stop."""
    queryset = BusStop.objects.select_related('building')
    serializer_class = BusStopSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()


# Source Views

class SourceListView(generics.ListCreateAPIView):
    """List all sources or create a new source."""
    queryset = Source.objects.filter(is_active=True)
    serializer_class = SourceSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['source_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'demand', 'capacity', 'created_at']
    ordering = ['name']
    
    def post(self, request, *args, **kwargs):
        """Handle both JSON source creation and CSV upload."""
        # Check if this is a CSV upload
        if 'file' in request.FILES:
            return self.upload_csv(request)
        else:
            # Handle regular source creation
            return super().post(request, *args, **kwargs)
    
    def upload_csv(self, request):
        """Handle CSV file upload for sources."""
        serializer = CSVUploadSerializer(data={'file': request.FILES['file'], 'data_type': 'sources'})
        
        if not serializer.is_valid():
            return Response({
                'error': 'Invalid upload data',
                'details': serializer.errors,
                'timestamp': timezone.now()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = serializer.validated_data['file']
        
        try:
            CSVProcessingService.validate_csv_file(file)
            created_count, errors = CSVProcessingService.process_sources_csv(file)
            
            response_data = {
                'created_count': created_count,
                'errors': errors,
                'success_rate': f"{((created_count / (created_count + len(errors))) * 100):.1f}%" if (created_count + len(errors)) > 0 else "0%"
            }
            
            if errors:
                return Response({
                    'message': f'Processed CSV with {len(errors)} errors. Created {created_count} sources.',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_206_PARTIAL_CONTENT)
            else:
                return Response({
                    'message': f'Successfully created {created_count} sources',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Sources CSV processing error: {str(e)}", exc_info=True)
            return Response({
                'error': 'CSV processing failed',
                'details': {'detail': str(e)},
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SourceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a source."""
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()


# Course Views

class CourseListView(generics.ListCreateAPIView):
    """List all courses or create a new course."""
    queryset = Course.objects.filter(is_active=True)
    serializer_class = CourseSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['department', 'credits', 'is_active']
    search_fields = ['name', 'course_code', 'department']
    ordering_fields = ['course_code', 'name', 'credits', 'created_at']
    ordering = ['course_code']


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a course."""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()


# Class Session Views

class ClassSessionListView(generics.ListCreateAPIView):
    """List all class sessions or create a new class session."""
    queryset = ClassSession.objects.filter(is_active=True).select_related(
        'course', 'building'
    )
    serializer_class = ClassSessionSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['course', 'building', 'is_active']
    search_fields = ['course__name', 'course__course_code', 'instructor', 'room']
    ordering_fields = ['start_time', 'course__course_code', 'created_at']
    ordering = ['course__course_code', 'start_time']


class ClassSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a class session."""
    queryset = ClassSession.objects.select_related('course', 'building')
    serializer_class = ClassSessionSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()


# Bus Views

class BusListView(generics.ListCreateAPIView):
    """List all buses or create a new bus."""
    queryset = Bus.objects.filter(is_active=True)
    serializer_class = BusSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_active']
    search_fields = ['bus_number', 'license_plate']
    ordering_fields = ['bus_number', 'capacity', 'status', 'created_at']
    ordering = ['bus_number']


class BusDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a bus."""
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.status = 'inactive'
        instance.save()


# Route Views

class RouteListView(generics.ListCreateAPIView):
    """List all routes or create a new route."""
    queryset = Route.objects.filter(is_active=True).prefetch_related(
        'route_stops__bus_stop'
    )
    serializer_class = RouteSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['route_type', 'is_active']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['code', 'name', 'frequency_minutes', 'created_at']
    ordering = ['code']


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a route."""
    queryset = Route.objects.prefetch_related('route_stops__bus_stop')
    serializer_class = RouteSerializer
    
    def perform_destroy(self, instance):
        """Soft delete by setting is_active to False."""
        instance.is_active = False
        instance.save()


# CSV Upload View

class CSVUploadView(BaseAPIView):
    """Handle CSV file uploads for bus stops and class sessions."""
    
    def post(self, request, *args, **kwargs):
        """Upload and process CSV file."""
        serializer = CSVUploadSerializer(data=request.data)
        
        if not serializer.is_valid():
            return self.create_error_response(
                "Invalid upload data",
                serializer.errors
            )
        
        file = serializer.validated_data['file']
        data_type = serializer.validated_data['data_type']
        
        try:
            # Validate file
            CSVProcessingService.validate_csv_file(file)
            
            # Process based on data type
            if data_type == 'stops':
                created_count, errors = CSVProcessingService.process_bus_stops_csv(file)
                data_name = 'bus stops'
            elif data_type == 'classes':
                created_count, errors = CSVProcessingService.process_classes_csv(file)
                data_name = 'class sessions'
            elif data_type == 'buildings':
                created_count, errors = CSVProcessingService.process_buildings_csv(file)
                data_name = 'buildings'
            elif data_type == 'sources':
                created_count, errors = CSVProcessingService.process_sources_csv(file)
                data_name = 'sources'
            else:
                return self.create_error_response(
                    "Invalid data type",
                    {"data_type": "Must be 'stops', 'classes', 'buildings', or 'sources'"}
                )
            
            response_data = {
                'created_count': created_count,
                'errors': errors,
                'success_rate': f"{((created_count / (created_count + len(errors))) * 100):.1f}%" if (created_count + len(errors)) > 0 else "0%"
            }
            
            if errors:
                return Response({
                    'message': f'Processed CSV with {len(errors)} errors. Created {created_count} {data_name}.',
                    'data': response_data,
                    'timestamp': timezone.now()
                }, status=status.HTTP_206_PARTIAL_CONTENT)
            else:
                return self.create_success_response(
                    f'Successfully created {created_count} {data_name}',
                    response_data
                )
        
        except Exception as e:
            logger.error(f"CSV processing error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "CSV processing failed",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Bus Management Views

class BusCountView(BaseAPIView):
    """Manage bus fleet count."""
    
    def get(self, request, *args, **kwargs):
        """Get current bus count and details."""
        try:
            operational_buses = BusManagementService.get_operational_buses()
            
            return self.create_success_response(
                "Bus count retrieved successfully",
                {
                    'active_count': len(operational_buses),
                    'total_count': Bus.objects.count(),
                    'operational_buses': BusSerializer(operational_buses, many=True).data
                }
            )
        
        except Exception as e:
            return self.create_error_response(
                "Failed to retrieve bus count",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, *args, **kwargs):
        """Set the total number of active buses."""
        serializer = BusCountSerializer(data=request.data)
        
        if not serializer.is_valid():
            return self.create_error_response(
                "Invalid bus count data",
                serializer.errors
            )
        
        count = serializer.validated_data['count']
        
        try:
            result = BusManagementService.set_bus_count(count)
            return self.create_success_response(result['message'], result)
            
        except Exception as e:
            logger.error(f"Bus count update error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "Failed to update bus count",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Analytics Views

class SystemOverviewView(BaseAPIView):
    """Provide system-wide analytics and overview."""
    
    def get(self, request, *args, **kwargs):
        """Get system overview statistics."""
        try:
            overview_data = AnalyticsService.get_system_overview()
            return self.create_success_response(
                "System overview retrieved successfully",
                overview_data
            )
            
        except Exception as e:
            logger.error(f"System overview error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "Failed to retrieve system overview",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RouteUtilizationView(BaseAPIView):
    """Provide route utilization analytics."""
    
    def get(self, request, *args, **kwargs):
        """Get route utilization data for a specific date."""
        try:
            date_param = request.query_params.get('date')
            date = None
            
            if date_param:
                from datetime import datetime
                try:
                    date = datetime.strptime(date_param, '%Y-%m-%d').date()
                except ValueError:
                    return self.create_error_response(
                        "Invalid date format",
                        {"detail": "Date must be in YYYY-MM-DD format"}
                    )
            
            utilization_data = AnalyticsService.get_route_utilization(date)
            
            return self.create_success_response(
                f"Route utilization data retrieved for {date or 'today'}",
                {
                    'date': date or timezone.now().date(),
                    'routes': utilization_data
                }
            )
            
        except Exception as e:
            logger.error(f"Route utilization error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "Failed to retrieve route utilization data",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# System Health Views

class SystemHealthView(BaseAPIView):
    """Check system health and data consistency."""
    
    def get(self, request, *args, **kwargs):
        """Perform system health check."""
        try:
            route_issues = DataValidationService.check_route_consistency()
            bus_issues = DataValidationService.check_bus_availability()
            
            all_issues = route_issues + bus_issues
            is_healthy = len(all_issues) == 0
            
            return Response({
                'status': 'healthy' if is_healthy else 'warning',
                'message': 'System health check completed',
                'issues_found': len(all_issues),
                'issues': all_issues,
                'timestamp': timezone.now()
            }, status=status.HTTP_200_OK if is_healthy else status.HTTP_206_PARTIAL_CONTENT)
            
        except Exception as e:
            logger.error(f"System health check error: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': 'System health check failed',
                'error': str(e),
                'timestamp': timezone.now()
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def api_status(request):
    """Simple API status endpoint."""
    return JsonResponse({
        'status': 'active',
        'message': 'Bus System API is running',
        'version': '2.0.0',
        'timestamp': timezone.now().isoformat()
    })


# Route Optimization Views

class RouteOptimizationView(BaseAPIView):
    """Handle route optimization requests."""
    
    def post(self, request, *args, **kwargs):
        """Run route optimization using Stinger algorithm."""
        serializer = RouteOptimizationRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return self.create_error_response(
                "Invalid optimization request",
                serializer.errors
            )
        
        try:
            # Extract parameters
            params = serializer.validated_data
            use_existing = params.get('use_existing_data', True)
            
            # Prepare data
            if use_existing:
                # Get data from database
                buildings_data = []
                for building in Building.objects.filter(is_active=True):
                    # Skip buildings that were previously stored as sources (legacy support)
                    if not building.name.startswith('SOURCE: '):
                        buildings_data.append({
                            'building_name': building.name,
                            'demand': 100,  # Default demand, could be enhanced with actual demand data
                            'latitude': float(building.latitude) if building.latitude else 0,
                            'longitude': float(building.longitude) if building.longitude else 0
                        })
                
                # Get sources from Source model
                sources_data = []
                for source in Source.objects.filter(is_active=True):
                    sources_data.append({
                        'source_name': source.name,
                        'latitude': float(source.latitude),
                        'longitude': float(source.longitude),
                        'demand': source.demand
                    })
                
                stops_data = []
                for stop in BusStop.objects.filter(is_active=True):
                    stops_data.append({
                        'stop_name': stop.name,
                        'stop_lat': float(stop.latitude),
                        'stop_lon': float(stop.longitude)
                    })
            else:
                # Use provided data
                buildings_data = params.get('buildings_data', [])
                stops_data = params.get('stops_data', [])
                sources_data = params.get('sources_data', [])
            
            # Validate we have data - we need at least buildings and stops for optimization
            if not buildings_data or not stops_data:
                return self.create_error_response(
                    "Insufficient data for optimization",
                    {"detail": "Please upload both buildings and stops data. Sources are optional and will use defaults if not provided."}
                )
            
            # Run optimization
            optimization_result = RouteOptimizationService.run_stinger_optimization(
                buildings_data=buildings_data,
                stops_data=stops_data,
                sources_data=sources_data,
                fleet_size=params.get('fleet_size', 12),
                target_lines=params.get('target_lines', 12),
                k_transfers=params.get('k_transfers', 2),
                transfer_penalty=params.get('transfer_penalty', 5.0),
                speed_kmh=params.get('speed_kmh', 30.0),
                algorithm=params.get('algorithm', 'genetic')
            )
            
            if optimization_result.get('success'):
                # Store results temporarily (you might want to implement a proper cache/database storage)
                import uuid
                optimization_id = uuid.uuid4()
                
                # Add metadata to results
                optimization_result['optimization_id'] = optimization_id
                optimization_result['created_at'] = timezone.now()
                
                # TODO: Store results in cache or database for later retrieval
                # For now, return directly
                
                result_serializer = RouteOptimizationResultSerializer(data=optimization_result)
                if result_serializer.is_valid():
                    return self.create_success_response(
                        f"Route optimization completed successfully. Generated {len(optimization_result['results']['routes'])} optimized routes.",
                        result_serializer.validated_data
                    )
                else:
                    return self.create_error_response(
                        "Failed to serialize optimization results",
                        result_serializer.errors
                    )
            else:
                return self.create_error_response(
                    "Route optimization failed",
                    {"detail": optimization_result.get('error', 'Unknown error occurred')},
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Route optimization error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "Route optimization failed",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ApplyOptimizedRoutesView(BaseAPIView):
    """Apply optimized routes to the system."""
    
    def post(self, request, *args, **kwargs):
        """Apply optimization results to create routes in the database."""
        serializer = ApplyOptimizedRoutesSerializer(data=request.data)
        
        if not serializer.is_valid():
            return self.create_error_response(
                "Invalid apply routes request",
                serializer.errors
            )
        
        try:
            optimization_id = serializer.validated_data['optimization_id']
            clear_existing = serializer.validated_data.get('clear_existing', False)
            
            # TODO: Retrieve optimization results from cache/database using optimization_id
            # For now, this is a placeholder - in a real implementation, you'd store and retrieve results
            
            return self.create_error_response(
                "Apply routes not yet implemented",
                {"detail": "This endpoint requires optimization results storage implementation"},
                status.HTTP_501_NOT_IMPLEMENTED
            )
            
        except Exception as e:
            logger.error(f"Apply routes error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "Failed to apply optimized routes",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OptimizationTestView(BaseAPIView):
    """Test route optimization with sample data."""
    
    def post(self, request, *args, **kwargs):
        """Run optimization test with existing Stinger sample data."""
        try:
            # Use default Georgia Tech data for testing
            buildings_data = [
                {'building_name': '760 SPRING STREET', 'demand': 30, 'latitude': 33.77780591, 'longitude': -84.38983261},
                {'building_name': 'CLOUGH UNDERGRADUATE LEARNING COMMONS', 'demand': 758, 'latitude': 33.77543753, 'longitude': -84.39390424},
                {'building_name': 'COLLEGE OF COMPUTING', 'demand': 421, 'latitude': 33.77755663, 'longitude': -84.39758288},
                {'building_name': 'HOWEY PHYSICS BUILDING', 'demand': 991, 'latitude': 33.77769409, 'longitude': -84.39847445},
                {'building_name': 'SCHELLER COLLEGE OF BUSINESS', 'demand': 1232, 'latitude': 33.77665282, 'longitude': -84.38724716},
            ]
            
            stops_data = [
                {'stop_name': 'Klaus Building EB', 'stop_lat': 33.777097, 'stop_lon': -84.395484},
                {'stop_name': 'Clough Commons', 'stop_lat': 33.775274, 'stop_lon': -84.396138},
                {'stop_name': 'College of Business', 'stop_lat': 33.77677, 'stop_lon': -84.387753},
                {'stop_name': 'MARTA Midtown Station', 'stop_lat': 33.78082162, 'stop_lon': -84.38640592},
                {'stop_name': 'Student Center', 'stop_lat': 33.77342787, 'stop_lon': -84.39917304},
            ]
            
            sources_data = [
                {'source_name': 'West Village Dorms', 'latitude': 33.779568, 'longitude': -84.404716, 'demand': 2052},
                {'source_name': 'North Avenue Dorms', 'latitude': 33.77118, 'longitude': -84.390857, 'demand': 4256},
                {'source_name': 'MARTA Midtown Station', 'latitude': 33.781262, 'longitude': -84.386494, 'demand': 500},
            ]
            
            # Run optimization with test data
            optimization_result = RouteOptimizationService.run_stinger_optimization(
                buildings_data=buildings_data,
                stops_data=stops_data,
                sources_data=sources_data,
                fleet_size=5,
                target_lines=3,
                k_transfers=2,
                algorithm='genetic'
            )
            
            if optimization_result.get('success'):
                return self.create_success_response(
                    "Optimization test completed successfully",
                    optimization_result
                )
            else:
                return self.create_error_response(
                    "Optimization test failed",
                    {"detail": optimization_result.get('error', 'Unknown error')}
                )
                
        except Exception as e:
            logger.error(f"Optimization test error: {str(e)}", exc_info=True)
            return self.create_error_response(
                "Optimization test failed",
                {"detail": str(e)},
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
