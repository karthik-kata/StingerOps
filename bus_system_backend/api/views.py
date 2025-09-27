from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import JsonResponse
import csv
import io
from .models import BusStop, Class, Bus, Route
from .serializers import (
    BusStopSerializer, 
    ClassSerializer, 
    BusSerializer, 
    RouteSerializer,
    CSVUploadSerializer,
    BusCountSerializer
)

class BusStopViewSet(viewsets.ModelViewSet):
    queryset = BusStop.objects.all()
    serializer_class = BusStopSerializer

class ClassViewSet(viewsets.ModelViewSet):
    queryset = Class.objects.all()
    serializer_class = ClassSerializer

class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

class CSVUploadViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def upload_csv(self, request):
        serializer = CSVUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            data_type = serializer.validated_data['data_type']
            
            try:
                # Read CSV file
                csv_data = file.read().decode('utf-8')
                csv_reader = csv.DictReader(io.StringIO(csv_data))
                
                created_objects = []
                
                if data_type == 'stops':
                    for row in csv_reader:
                        stop, created = BusStop.objects.get_or_create(
                            name=row.get('stop_name', ''),
                            defaults={
                                'latitude': float(row.get('stop_lat', 0)),
                                'longitude': float(row.get('stop_lon', 0)),
                                'routes_serving': row.get('routes_serving', '')
                            }
                        )
                        created_objects.append(stop)
                        
                elif data_type == 'classes':
                    for row in csv_reader:
                        class_obj, created = Class.objects.get_or_create(
                            name=row.get('name', ''),
                            defaults={
                                'course_code': row.get('course_code', ''),
                                'building': row.get('building', ''),
                                'room': row.get('room', ''),
                                'latitude': float(row.get('latitude', 0)) if row.get('latitude') else None,
                                'longitude': float(row.get('longitude', 0)) if row.get('longitude') else None,
                                'start_time': row.get('start_time', ''),
                                'end_time': row.get('end_time', ''),
                                'days': row.get('days', '')
                            }
                        )
                        created_objects.append(class_obj)
                
                return Response({
                    'message': f'Successfully uploaded {len(created_objects)} {data_type}',
                    'count': len(created_objects)
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'error': f'Error processing CSV: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BusCountViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def set_bus_count(self, request):
        serializer = BusCountSerializer(data=request.data)
        if serializer.is_valid():
            count = serializer.validated_data['count']
            
            # Get current bus count
            current_count = Bus.objects.count()
            
            if count > current_count:
                # Create new buses
                for i in range(current_count + 1, count + 1):
                    Bus.objects.create(
                        bus_number=f"BUS{i:03d}",
                        capacity=50
                    )
            elif count < current_count:
                # Deactivate excess buses
                excess_buses = Bus.objects.all()[count:]
                for bus in excess_buses:
                    bus.is_active = False
                    bus.save()
            
            return Response({
                'message': f'Bus count set to {count}',
                'count': count
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def get_bus_count(self, request):
        active_buses = Bus.objects.filter(is_active=True)
        return Response({
            'count': active_buses.count(),
            'buses': BusSerializer(active_buses, many=True).data
        })

def api_status(request):
    return JsonResponse({
        'status': 'active',
        'message': 'Bus System API is running'
    })
