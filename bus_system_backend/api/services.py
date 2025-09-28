"""
Business logic layer for the bus system API.
"""
import csv
import io
import os
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from .models import (
    BusStop, Course, ClassSession, Building, Bus, Route, 
    RouteStop, RouteAssignment
)


class CSVProcessingService:
    """Service for handling CSV file processing and validation."""
    
    @staticmethod
    def validate_csv_file(file) -> bool:
        """Validate that the uploaded file is a valid CSV."""
        if not file.name.endswith('.csv'):
            raise ValidationError("File must have a .csv extension")
        
        if file.size > 5 * 1024 * 1024:  # 5MB limit
            raise ValidationError("File size must be less than 5MB")
        
        return True
    
    @staticmethod
    def parse_csv_data(file, required_columns: List[str]) -> List[Dict]:
        """Parse CSV file and validate required columns."""
        try:
            file.seek(0)  # Reset file pointer
            csv_content = file.read().decode('utf-8-sig')  # Handle BOM
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Validate headers
            headers = csv_reader.fieldnames or []
            missing_columns = set(required_columns) - set(headers)
            if missing_columns:
                raise ValidationError(
                    f"Missing required columns: {', '.join(missing_columns)}"
                )
            
            data = list(csv_reader)
            if not data:
                raise ValidationError("CSV file is empty or contains no data rows")
            
            return data
            
        except UnicodeDecodeError:
            raise ValidationError("File encoding not supported. Please use UTF-8 encoding")
        except csv.Error as e:
            raise ValidationError(f"Invalid CSV format: {str(e)}")
    
    @classmethod
    def process_bus_stops_csv(cls, file) -> Tuple[int, List[str]]:
        """Process bus stops CSV file."""
        required_columns = ['name', 'latitude', 'longitude']
        optional_columns = ['code', 'description', 'capacity', 'has_shelter', 'building_code']
        
        data = cls.parse_csv_data(file, required_columns)
        
        created_count = 0
        errors = []
        
        with transaction.atomic():
            for i, row in enumerate(data, start=2):  # Start from row 2 (after header)
                try:
                    # Get building if specified
                    building = None
                    if row.get('building_code'):
                        try:
                            building = Building.objects.get(code=row['building_code'])
                        except Building.DoesNotExist:
                            errors.append(f"Row {i}: Building with code '{row['building_code']}' not found")
                            continue
                    
                    bus_stop, created = BusStop.objects.get_or_create(
                        name=row['name'].strip(),
                        defaults={
                            'code': row.get('code', '').strip() or None,
                            'description': row.get('description', '').strip(),
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'capacity': int(row.get('capacity', 20)),
                            'has_shelter': row.get('has_shelter', '').lower() in ['true', '1', 'yes'],
                            'building': building,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    
                except (ValueError, ValidationError) as e:
                    errors.append(f"Row {i}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {i}: Unexpected error - {str(e)}")
        
        return created_count, errors
    
    @classmethod
    def process_classes_csv(cls, file) -> Tuple[int, List[str]]:
        """Process class sessions CSV file."""
        required_columns = ['course_code', 'course_name', 'building_code', 'room', 
                          'start_time', 'end_time', 'days']
        
        data = cls.parse_csv_data(file, required_columns)
        
        created_count = 0
        errors = []
        
        with transaction.atomic():
            for i, row in enumerate(data, start=2):
                try:
                    # Get or create course
                    course, _ = Course.objects.get_or_create(
                        course_code=row['course_code'].strip(),
                        defaults={
                            'name': row['course_name'].strip(),
                            'department': row.get('department', '').strip()
                        }
                    )
                    
                    # Get building
                    try:
                        building = Building.objects.get(code=row['building_code'].strip())
                    except Building.DoesNotExist:
                        errors.append(f"Row {i}: Building '{row['building_code']}' not found")
                        continue
                    
                    # Parse days of week
                    days_str = row['days'].strip().upper()
                    days_list = list(days_str) if days_str else []
                    
                    class_session, created = ClassSession.objects.get_or_create(
                        course=course,
                        building=building,
                        room=row['room'].strip(),
                        start_time=row['start_time'].strip(),
                        end_time=row['end_time'].strip(),
                        defaults={
                            'instructor': row.get('instructor', '').strip(),
                            'days_of_week': days_list,
                            'capacity': int(row.get('capacity', 30)),
                            'enrollment': int(row.get('enrollment', 0)),
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                except (ValueError, ValidationError) as e:
                    errors.append(f"Row {i}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {i}: Unexpected error - {str(e)}")
        
        return created_count, errors
    
    @classmethod
    def process_buildings_csv(cls, file) -> Tuple[int, List[str]]:
        """Process buildings CSV file for Stinger optimization."""
        required_columns = ['building_name', 'demand', 'latitude', 'longitude']
        
        data = cls.parse_csv_data(file, required_columns)
        
        created_count = 0
        errors = []
        
        with transaction.atomic():
            for i, row in enumerate(data, start=2):
                try:
                    building, created = Building.objects.get_or_create(
                        name=row['building_name'].strip(),
                        defaults={
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                        }
                    )
                    
                    if created:
                        created_count += 1
                    
                except (ValueError, ValidationError) as e:
                    errors.append(f"Row {i}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {i}: Unexpected error - {str(e)}")
        
        return created_count, errors
    
    @classmethod
    def process_sources_csv(cls, file) -> Tuple[int, List[str]]:
        """Process sources CSV file for Stinger optimization."""
        required_columns = ['source_name', 'latitude', 'longitude', 'demand']
        
        data = cls.parse_csv_data(file, required_columns)
        
        created_count = 0
        errors = []
        
        with transaction.atomic():
            for i, row in enumerate(data, start=2):
                try:
                    # Import Source model here to avoid circular imports
                    from .models import Source
                    
                    source, created = Source.objects.get_or_create(
                        name=row['source_name'].strip(),
                        defaults={
                            'latitude': float(row['latitude']),
                            'longitude': float(row['longitude']),
                            'demand': int(row['demand']) if row['demand'].strip() else 100,
                            'source_type': 'other',  # Default type, could be enhanced
                            'capacity': int(row.get('capacity', '')) if row.get('capacity', '').strip() else None
                        }
                    )
                    
                    if created:
                        created_count += 1
                    
                except (ValueError, ValidationError) as e:
                    errors.append(f"Row {i}: {str(e)}")
                except Exception as e:
                    errors.append(f"Row {i}: Unexpected error - {str(e)}")
        
        return created_count, errors


class BusManagementService:
    """Service for managing bus operations."""
    
    @staticmethod
    def get_operational_buses() -> List[Bus]:
        """Get all operational buses."""
        return Bus.objects.filter(
            is_active=True,
            status='active'
        ).order_by('bus_number')
    
    @staticmethod
    def create_bus_fleet(count: int, start_number: int = 1) -> List[Bus]:
        """Create a fleet of buses with sequential numbers."""
        buses = []
        
        with transaction.atomic():
            for i in range(count):
                bus_number = f"BUS{start_number + i:03d}"
                
                bus, created = Bus.objects.get_or_create(
                    bus_number=bus_number,
                    defaults={
                        'capacity': 50,
                        'status': 'active',
                    }
                )
                buses.append(bus)
        
        return buses
    
    @staticmethod
    def set_bus_count(count: int) -> Dict:
        """Set the total number of active buses."""
        current_active = Bus.objects.filter(is_active=True).count()
        
        if count > current_active:
            # Create additional buses
            additional_needed = count - current_active
            last_number = Bus.objects.count()
            BusManagementService.create_bus_fleet(
                additional_needed, 
                start_number=last_number + 1
            )
            message = f"Created {additional_needed} new buses"
            
        elif count < current_active:
            # Deactivate excess buses
            excess_buses = Bus.objects.filter(is_active=True)[count:]
            deactivated = 0
            
            with transaction.atomic():
                for bus in excess_buses:
                    bus.is_active = False
                    bus.status = 'inactive'
                    bus.save()
                    deactivated += 1
            
            message = f"Deactivated {deactivated} buses"
        else:
            message = f"Bus count already at {count}"
        
        active_count = Bus.objects.filter(is_active=True).count()
        
        return {
            'message': message,
            'active_count': active_count,
            'total_count': Bus.objects.count()
        }


class RouteService:
    """Service for managing routes and schedules."""
    
    @staticmethod
    def create_route_with_stops(route_data: Dict, stops_data: List[Dict]) -> Route:
        """Create a route with ordered stops."""
        with transaction.atomic():
            route = Route.objects.create(**route_data)
            
            for i, stop_data in enumerate(stops_data):
                bus_stop = BusStop.objects.get(id=stop_data['bus_stop_id'])
                RouteStop.objects.create(
                    route=route,
                    bus_stop=bus_stop,
                    stop_order=i + 1,
                    arrival_time_offset=timedelta(minutes=stop_data.get('offset_minutes', 0))
                )
            
            return route
    
    @staticmethod
    def assign_bus_to_route(bus_id: str, route_id: str, 
                          assigned_date: datetime.date, 
                          start_time: datetime.time,
                          end_time: datetime.time) -> RouteAssignment:
        """Assign a bus to a route for a specific time period."""
        bus = Bus.objects.get(id=bus_id)
        route = Route.objects.get(id=route_id)
        
        assignment = RouteAssignment(
            bus=bus,
            route=route,
            assigned_date=assigned_date,
            start_time=start_time,
            end_time=end_time
        )
        
        # Validate will check for overlapping assignments
        assignment.full_clean()
        assignment.save()
        
        return assignment
    
    @staticmethod
    def get_route_schedule(route_id: str, date: Optional[datetime.date] = None) -> Dict:
        """Get the schedule for a route on a specific date."""
        if not date:
            date = timezone.now().date()
        
        route = Route.objects.get(id=route_id)
        assignments = RouteAssignment.objects.filter(
            route=route,
            assigned_date=date,
            is_active=True
        ).select_related('bus')
        
        stops = RouteStop.objects.filter(
            route=route,
            is_active=True
        ).select_related('bus_stop').order_by('stop_order')
        
        return {
            'route': route,
            'date': date,
            'assignments': assignments,
            'stops': stops,
            'operating_hours': {
                'start': route.operating_hours_start,
                'end': route.operating_hours_end
            }
        }


class AnalyticsService:
    """Service for providing analytics and insights."""
    
    @staticmethod
    def get_system_overview() -> Dict:
        """Get an overview of the entire bus system."""
        return {
            'total_buses': Bus.objects.count(),
            'active_buses': Bus.objects.filter(is_active=True, status='active').count(),
            'total_routes': Route.objects.filter(is_active=True).count(),
            'total_stops': BusStop.objects.filter(is_active=True).count(),
            'total_buildings': Building.objects.filter(is_active=True).count(),
            'total_courses': Course.objects.filter(is_active=True).count(),
            'total_class_sessions': ClassSession.objects.filter(is_active=True).count(),
        }
    
    @staticmethod
    def get_route_utilization(date: Optional[datetime.date] = None) -> List[Dict]:
        """Get route utilization data for a specific date."""
        if not date:
            date = timezone.now().date()
        
        routes = Route.objects.filter(is_active=True)
        utilization_data = []
        
        for route in routes:
            assignments = RouteAssignment.objects.filter(
                route=route,
                assigned_date=date,
                is_active=True
            )
            
            utilization_data.append({
                'route': route,
                'assigned_buses': assignments.count(),
                'stops_count': route.route_stops.filter(is_active=True).count(),
                'frequency_minutes': route.frequency_minutes,
                'operating_hours': (route.operating_hours_end.hour - route.operating_hours_start.hour)
            })
        
        return utilization_data


class DataValidationService:
    """Service for validating data integrity across the system."""
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """Validate geographic coordinates."""
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)
    
    @staticmethod
    def validate_time_range(start_time: datetime.time, end_time: datetime.time) -> bool:
        """Validate that end time is after start time."""
        return start_time < end_time
    
    @staticmethod
    def check_route_consistency() -> List[str]:
        """Check for inconsistencies in route data."""
        issues = []
        
        # Check routes without stops
        routes_without_stops = Route.objects.filter(
            is_active=True,
            route_stops__isnull=True
        ).distinct()
        
        for route in routes_without_stops:
            issues.append(f"Route {route.code} has no stops assigned")
        
        # Check routes without assignments
        today = timezone.now().date()
        routes_without_buses = Route.objects.filter(
            is_active=True,
            assignments__assigned_date=today,
            assignments__isnull=True
        ).distinct()
        
        for route in routes_without_buses:
            issues.append(f"Route {route.code} has no bus assignments for today")
        
        return issues
    
    @staticmethod
    def check_bus_availability() -> List[str]:
        """Check bus availability and conflicts."""
        issues = []
        today = timezone.now().date()
        
        # Check for overlapping assignments
        assignments = RouteAssignment.objects.filter(
            assigned_date=today,
            is_active=True
        ).select_related('bus', 'route')
        
        bus_schedules = {}
        for assignment in assignments:
            bus_id = assignment.bus.id
            
            if bus_id not in bus_schedules:
                bus_schedules[bus_id] = []
            
            bus_schedules[bus_id].append(assignment)
        
        for bus_id, schedule in bus_schedules.items():
            if len(schedule) > 1:
                # Check for time conflicts
                for i in range(len(schedule)):
                    for j in range(i + 1, len(schedule)):
                        assign1, assign2 = schedule[i], schedule[j]
                        if (assign1.start_time < assign2.end_time and 
                            assign1.end_time > assign2.start_time):
                            issues.append(
                                f"Bus {assign1.bus.bus_number} has overlapping assignments: "
                                f"{assign1.route.code} and {assign2.route.code}"
                            )
        
        return issues


class RouteOptimizationService:
    """Service for integrating Stinger route optimization with Django."""
    
    @staticmethod
    def get_stinger_path() -> str:
        """Get the path to the Stinger optimization directory."""
        # Assuming Stinger is in a sibling directory to the Django backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(base_dir, 'stinger')
    
    @staticmethod
    def prepare_optimization_data(buildings_data: List[Dict], stops_data: List[Dict], sources_data: List[Dict] = None) -> Tuple[str, str, str]:
        """Prepare CSV data for Stinger optimization and return file paths."""
        stinger_path = RouteOptimizationService.get_stinger_path()
        data_path = os.path.join(stinger_path, 'data')
        
        # Ensure data directory exists
        os.makedirs(data_path, exist_ok=True)
        
        # Prepare buildings.csv
        buildings_file = os.path.join(data_path, 'buildings.csv')
        with open(buildings_file, 'w', newline='', encoding='utf-8') as f:
            if buildings_data:
                writer = csv.DictWriter(f, fieldnames=['building_name', 'demand', 'latitude', 'longitude'])
                writer.writeheader()
                writer.writerows(buildings_data)
        
        # Prepare sources.csv
        sources_file = os.path.join(data_path, 'sources.csv')
        
        # Use provided sources_data or fall back to default GT sources
        if not sources_data or len(sources_data) == 0:
            sources_data = [
                {
                    'source_name': 'West Village Dorms (West Campus)',
                    'latitude': 33.779568,
                    'longitude': -84.404716,
                    'demand': 2052
                },
                {
                    'source_name': 'North Avenue Dorms (East Campus)',
                    'latitude': 33.77118,
                    'longitude': -84.390857,
                    'demand': 4256
                },
                {
                    'source_name': 'MARTA Midtown Station',
                    'latitude': 33.781262,
                    'longitude': -84.386494,
                    'demand': 500
                }
            ]
        
        with open(sources_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['source_name', 'latitude', 'longitude', 'demand'])
            writer.writeheader()
            for source in sources_data:
                # Handle both uploaded sources and default sources format
                source_row = {
                    'source_name': source.get('source_name') or source.get('name') or 'Unknown Source',
                    'latitude': source.get('latitude'),
                    'longitude': source.get('longitude'),
                    'demand': source.get('demand', 100)
                }
                writer.writerow(source_row)
        
        # Prepare stops.csv
        stops_file = os.path.join(data_path, 'stops.csv')
        with open(stops_file, 'w', newline='', encoding='utf-8') as f:
            if stops_data:
                writer = csv.DictWriter(f, fieldnames=['stop_name', 'stop_lat', 'stop_lon'])
                writer.writeheader()
                writer.writerows(stops_data)
        
        return buildings_file, sources_file, stops_file
    
    @staticmethod
    def run_stinger_optimization(
        buildings_data: List[Dict],
        stops_data: List[Dict],
        sources_data: List[Dict] = None,
        fleet_size: int = 12,
        target_lines: int = 12,
        k_transfers: int = 2,
        transfer_penalty: float = 5.0,
        speed_kmh: float = 30.0,
        algorithm: str = 'genetic'
    ) -> Dict:
        """Run Stinger optimization and return results."""
        try:
            # Prepare data files
            buildings_file, sources_file, stops_file = RouteOptimizationService.prepare_optimization_data(
                buildings_data, stops_data, sources_data
            )
            
            stinger_path = RouteOptimizationService.get_stinger_path()
            
            # Step 1: Run demand distribution
            demand_script = os.path.join(stinger_path, 'nearest_stops_demand.py')
            demand_result = subprocess.run(
                ['python3', demand_script],
                cwd=stinger_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if demand_result.returncode != 0:
                raise Exception(f"Demand distribution failed: {demand_result.stderr}")
            
            # Step 2: Run route optimization
            optimization_script = os.path.join(stinger_path, 'tlpf_ktransfers.py')
            optimization_cmd = [
                'python3', optimization_script,
                '--fleet', str(fleet_size),
                '--target-lines', str(target_lines),
                '--k-transfers', str(k_transfers),
                '--transfer-penalty', str(transfer_penalty),
                '--speed-kmh', str(speed_kmh),
                '--algorithm', algorithm
            ]
            
            optimization_result = subprocess.run(
                optimization_cmd,
                cwd=stinger_path,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if optimization_result.returncode != 0:
                raise Exception(f"Route optimization failed: {optimization_result.stderr}")
            
            # Parse optimization results
            parsed_results = RouteOptimizationService.parse_stinger_output(
                optimization_result.stdout
            )
            
            return {
                'success': True,
                'results': parsed_results,
                'demand_output': demand_result.stdout,
                'optimization_output': optimization_result.stdout,
                'parameters': {
                    'fleet_size': fleet_size,
                    'target_lines': target_lines,
                    'k_transfers': k_transfers,
                    'transfer_penalty': transfer_penalty,
                    'speed_kmh': speed_kmh,
                    'algorithm': algorithm
                }
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Optimization timed out. Please try with fewer routes or smaller dataset.")
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': None
            }
    
    @staticmethod
    def parse_stinger_output(output_text: str) -> Dict:
        """Parse Stinger algorithm output and extract route information."""
        try:
            lines = output_text.strip().split('\n')
            routes = []
            current_route = None
            parsing_routes = False
            parsing_details = False
            
            # Extract summary metrics
            metrics = {}
            for line in lines:
                if 'Total Cost:' in line:
                    metrics['total_cost'] = float(re.search(r'([\d.]+)', line).group(1))
                elif 'Demand Coverage:' in line:
                    metrics['demand_coverage'] = float(re.search(r'([\d.]+)%', line).group(1)) / 100
                elif 'Efficiency:' in line:
                    metrics['efficiency'] = float(re.search(r'([\d.]+)', line).group(1))
            
            # Parse route information
            for i, line in enumerate(lines):
                line = line.strip()
                
                if 'Final Selected Lines' in line:
                    parsing_routes = True
                    continue
                
                if 'Detailed Route Information' in line:
                    parsing_details = True
                    parsing_routes = False
                    continue
                
                if parsing_routes and line and not line.startswith('-') and not line.startswith('Service') and not line.startswith('Equal') and not line.startswith('Mean') and not line.startswith('Total'):
                    # Parse route summary line - match format: '1. F_6      |  2 stops | cycle=  2.1 min | demand=  2723 | efficiency=1324.13'
                    match = re.match(r'(\d+)\. (\w+)\s+\|\s+(\d+) stops\s+\|.*?cycle=\s*([\d.]+) min.*?demand=\s*([\d.]+).*?efficiency=([\d.]+)', line)
                    if match:
                        routes.append({
                            'route_number': int(match.group(1)),
                            'route_id': match.group(2),
                            'stops_count': int(match.group(3)),
                            'cycle_minutes': float(match.group(4)),
                            'demand_coverage': float(match.group(5)),
                            'efficiency': float(match.group(6)),
                            'stops': []
                        })
                
                if parsing_details and line.startswith('Route '):
                    # Extract route ID from detail section
                    route_match = re.match(r'Route (\d+): (\w+)', line)
                    if route_match:
                        route_num = int(route_match.group(1))
                        # Find corresponding route in our list
                        current_route = next((r for r in routes if r['route_number'] == route_num), None)
                
                if parsing_details and current_route and re.match(r'\s+\d+\. ', line):
                    # Parse stop information
                    stop_match = re.match(r'\s+(\d+)\. (.+?)\s+\(([\d.-]+), ([\d.-]+)\)', line)
                    if stop_match:
                        current_route['stops'].append({
                            'stop_order': int(stop_match.group(1)),
                            'stop_name': stop_match.group(2).strip(),
                            'latitude': float(stop_match.group(3)),
                            'longitude': float(stop_match.group(4))
                        })
            
            return {
                'metrics': metrics,
                'routes': routes,
                'total_routes': len(routes)
            }
            
        except Exception as e:
            return {
                'error': f"Failed to parse Stinger output: {str(e)}",
                'raw_output': output_text
            }
    
    @staticmethod
    def apply_optimized_routes(optimization_results: Dict) -> Dict:
        """Apply optimized routes to Django models."""
        if not optimization_results.get('success') or not optimization_results.get('results'):
            raise ValidationError("Invalid optimization results")
        
        results = optimization_results['results']
        routes_data = results.get('routes', [])
        
        created_routes = []
        errors = []
        
        with transaction.atomic():
            # Clear existing optimized routes (optional - you might want to keep them)
            # Route.objects.filter(route_type='campus', code__startswith='OPT_').delete()
            
            for route_data in routes_data:
                try:
                    # Create the route
                    route = Route.objects.create(
                        name=f"Optimized Route {route_data['route_number']}",
                        code=f"OPT_{route_data['route_id']}",
                        description=f"Stinger optimized route with {route_data['stops_count']} stops",
                        route_type='campus',
                        color=RouteOptimizationService._generate_route_color(route_data['route_number']),
                        frequency_minutes=max(5, int(route_data['cycle_minutes'] / 2)),  # Half cycle time as frequency
                    )
                    
                    # Add stops to the route
                    for stop_info in route_data['stops']:
                        try:
                            # Find or create bus stop
                            bus_stop, created = BusStop.objects.get_or_create(
                                name=stop_info['stop_name'],
                                defaults={
                                    'latitude': stop_info['latitude'],
                                    'longitude': stop_info['longitude'],
                                    'capacity': 20
                                }
                            )
                            
                            # Create route stop relationship
                            RouteStop.objects.create(
                                route=route,
                                bus_stop=bus_stop,
                                stop_order=stop_info['stop_order'],
                                arrival_time_offset=timedelta(
                                    minutes=stop_info['stop_order'] * route_data['cycle_minutes'] / route_data['stops_count']
                                )
                            )
                            
                        except Exception as stop_error:
                            errors.append(f"Error adding stop {stop_info['stop_name']} to route {route.code}: {str(stop_error)}")
                    
                    created_routes.append(route)
                    
                except Exception as route_error:
                    errors.append(f"Error creating route {route_data['route_id']}: {str(route_error)}")
        
        return {
            'created_routes': created_routes,
            'created_count': len(created_routes),
            'errors': errors,
            'success': len(created_routes) > 0
        }
    
    @staticmethod
    def _generate_route_color(route_number: int) -> str:
        """Generate a unique color for each route."""
        colors = [
            '#FF0000',  # Red
            '#00FF00',  # Green
            '#0000FF',  # Blue
            '#FFFF00',  # Yellow
            '#FF00FF',  # Magenta
            '#00FFFF',  # Cyan
            '#FFA500',  # Orange
            '#800080',  # Purple
            '#FFC0CB',  # Pink
            '#A52A2A',  # Brown
            '#808080',  # Gray
            '#000000',  # Black
        ]
        return colors[(route_number - 1) % len(colors)]
