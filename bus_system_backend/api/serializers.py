from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import (
    Building, BusStop, Course, ClassSession, Bus, Route, 
    RouteStop, RouteAssignment, Source
)


class BuildingSerializer(serializers.ModelSerializer):
    """Serializer for Building model with proper validation."""
    
    class Meta:
        model = Building
        fields = [
            'id', 'name', 'code', 'address', 'latitude', 'longitude',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate building data."""
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Both coordinates must be provided together or both omitted
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )
        
        return data
    
    def validate_code(self, value):
        """Validate building code format."""
        if value and not value.isalnum():
            raise serializers.ValidationError(
                "Building code must contain only alphanumeric characters."
            )
        return value.upper() if value else None


class BusStopSerializer(serializers.ModelSerializer):
    """Serializer for BusStop model with nested building information."""
    building = BuildingSerializer(read_only=True)
    building_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = BusStop
        fields = [
            'id', 'name', 'code', 'description', 'latitude', 'longitude',
            'capacity', 'has_shelter', 'accessibility_features', 'building',
            'building_id', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_code(self, value):
        """Validate bus stop code format."""
        if value and not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "Bus stop code must contain only alphanumeric characters, hyphens, and underscores."
            )
        return value.upper() if value else None
    
    def validate_capacity(self, value):
        """Validate bus stop capacity."""
        if value < 1 or value > 200:
            raise serializers.ValidationError(
                "Capacity must be between 1 and 200."
            )
        return value
    
    def create(self, validated_data):
        building_id = validated_data.pop('building_id', None)
        if building_id:
            try:
                building = Building.objects.get(id=building_id)
                validated_data['building'] = building
            except Building.DoesNotExist:
                raise serializers.ValidationError(
                    f"Building with ID {building_id} does not exist."
                )
        
        return super().create(validated_data)


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source model with validation."""
    
    class Meta:
        model = Source
        fields = [
            'id', 'name', 'source_type', 'description', 'latitude', 'longitude',
            'demand', 'capacity', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate source name."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Source name must be at least 2 characters long."
            )
        return value.strip()
    
    def validate_demand(self, value):
        """Validate demand value."""
        if value < 1 or value > 10000:
            raise serializers.ValidationError(
                "Demand must be between 1 and 10000."
            )
        return value
    
    def validate_capacity(self, value):
        """Validate capacity value."""
        if value is not None and value < 1:
            raise serializers.ValidationError(
                "Capacity must be a positive integer."
            )
        return value


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""
    
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'course_code', 'credits', 'department',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_course_code(self, value):
        """Validate course code format."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Course code must be at least 2 characters long."
            )
        return value.strip().upper()
    
    def validate_credits(self, value):
        """Validate course credits."""
        if value < 1 or value > 6:
            raise serializers.ValidationError(
                "Credits must be between 1 and 6."
            )
        return value


class ClassSessionSerializer(serializers.ModelSerializer):
    """Serializer for ClassSession model with nested course and building."""
    course = CourseSerializer(read_only=True)
    course_id = serializers.UUIDField(write_only=True)
    building = BuildingSerializer(read_only=True)
    building_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = ClassSession
        fields = [
            'id', 'course', 'course_id', 'building', 'building_id', 'room',
            'instructor', 'start_time', 'end_time', 'days_of_week',
            'capacity', 'enrollment', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_days_of_week(self, value):
        """Validate days of week format."""
        valid_days = ['M', 'T', 'W', 'R', 'F', 'S', 'U']
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Days of week must be a list of day codes."
            )
        
        for day in value:
            if day not in valid_days:
                raise serializers.ValidationError(
                    f"Invalid day code: {day}. Valid codes are: {', '.join(valid_days)}"
                )
        
        return value
    
    def validate(self, data):
        """Validate class session data."""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                "End time must be after start time."
            )
        
        enrollment = data.get('enrollment', 0)
        capacity = data.get('capacity', 30)
        
        if enrollment > capacity:
            raise serializers.ValidationError(
                "Enrollment cannot exceed capacity."
            )
        
        return data


class BusSerializer(serializers.ModelSerializer):
    """Serializer for Bus model with operational status."""
    is_operational = serializers.ReadOnlyField()
    
    class Meta:
        model = Bus
        fields = [
            'id', 'bus_number', 'license_plate', 'capacity',
            'current_latitude', 'current_longitude', 'status',
            'last_maintenance', 'accessibility_features',
            'is_operational', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_bus_number(self, value):
        """Validate bus number format."""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Bus number must be at least 3 characters long."
            )
        return value.strip().upper()
    
    def validate_license_plate(self, value):
        """Validate license plate format."""
        if value and len(value.strip()) < 5:
            raise serializers.ValidationError(
                "License plate must be at least 5 characters long."
            )
        return value.strip().upper() if value else None
    
    def validate_capacity(self, value):
        """Validate bus capacity."""
        if value < 10 or value > 100:
            raise serializers.ValidationError(
                "Bus capacity must be between 10 and 100."
            )
        return value
    
    def validate(self, data):
        """Validate bus location data."""
        latitude = data.get('current_latitude')
        longitude = data.get('current_longitude')
        
        # Both coordinates must be provided together or both omitted
        if (latitude is None) != (longitude is None):
            raise serializers.ValidationError(
                "Both latitude and longitude must be provided together."
            )
        
        return data


class RouteStopSerializer(serializers.ModelSerializer):
    """Serializer for RouteStop through model."""
    bus_stop = BusStopSerializer(read_only=True)
    bus_stop_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = RouteStop
        fields = [
            'id', 'bus_stop', 'bus_stop_id', 'stop_order', 
            'arrival_time_offset', 'is_active'
        ]
        read_only_fields = ['id']
    
    def validate_stop_order(self, value):
        """Validate stop order."""
        if value < 1:
            raise serializers.ValidationError(
                "Stop order must be a positive integer."
            )
        return value


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model with nested stops."""
    route_stops = RouteStopSerializer(many=True, read_only=True)
    stops_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'name', 'code', 'description', 'route_type', 'color',
            'frequency_minutes', 'operating_hours_start', 'operating_hours_end',
            'operating_days', 'route_stops', 'stops_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_stops_count(self, obj):
        """Get the number of active stops for this route."""
        return obj.route_stops.filter(is_active=True).count()
    
    def validate_code(self, value):
        """Validate route code format."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Route code must be at least 2 characters long."
            )
        return value.strip().upper()
    
    def validate_color(self, value):
        """Validate hex color code."""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError(
                "Color must be a valid hex code (e.g., #FF0000)."
            )
        
        try:
            int(value[1:], 16)  # Validate hex digits
        except ValueError:
            raise serializers.ValidationError(
                "Color must be a valid hex code (e.g., #FF0000)."
            )
        
        return value.upper()
    
    def validate_frequency_minutes(self, value):
        """Validate route frequency."""
        if value < 5 or value > 60:
            raise serializers.ValidationError(
                "Frequency must be between 5 and 60 minutes."
            )
        return value
    
    def validate_operating_days(self, value):
        """Validate operating days format."""
        valid_days = ['M', 'T', 'W', 'R', 'F', 'S', 'U']
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "Operating days must be a list of day codes."
            )
        
        for day in value:
            if day not in valid_days:
                raise serializers.ValidationError(
                    f"Invalid day code: {day}. Valid codes are: {', '.join(valid_days)}"
                )
        
        return value
    
    def validate(self, data):
        """Validate route operating hours."""
        start_time = data.get('operating_hours_start')
        end_time = data.get('operating_hours_end')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                "Operating end time must be after start time."
            )
        
        return data


class RouteAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for RouteAssignment model."""
    route = RouteSerializer(read_only=True)
    route_id = serializers.UUIDField(write_only=True)
    bus = BusSerializer(read_only=True)
    bus_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = RouteAssignment
        fields = [
            'id', 'route', 'route_id', 'bus', 'bus_id',
            'assigned_date', 'start_time', 'end_time',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate route assignment."""
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise serializers.ValidationError(
                "End time must be after start time."
            )
        
        # Check for overlapping assignments (handled in model's clean method)
        return data


# API Request/Response Serializers

class CSVUploadSerializer(serializers.Serializer):
    """Serializer for CSV file upload."""
    file = serializers.FileField(
        help_text="CSV file to upload (max 5MB)"
    )
    data_type = serializers.ChoiceField(
        choices=[
            ('stops', 'Bus Stops'), 
            ('classes', 'Class Sessions'),
            ('buildings', 'Buildings (for optimization)'),
            ('sources', 'Sources (for optimization)')
        ],
        help_text="Type of data in the CSV file"
    )
    
    def validate_file(self, value):
        """Validate uploaded file."""
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError(
                "File must have a .csv extension."
            )
        
        if value.size > 5 * 1024 * 1024:  # 5MB
            raise serializers.ValidationError(
                "File size must be less than 5MB."
            )
        
        return value


class BusCountSerializer(serializers.Serializer):
    """Serializer for setting bus count."""
    count = serializers.IntegerField(
        min_value=1, max_value=50,
        help_text="Number of active buses (1-50)"
    )


class SystemOverviewSerializer(serializers.Serializer):
    """Serializer for system overview response."""
    total_buses = serializers.IntegerField()
    active_buses = serializers.IntegerField()
    total_routes = serializers.IntegerField()
    total_stops = serializers.IntegerField()
    total_buildings = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_class_sessions = serializers.IntegerField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""
    error = serializers.CharField()
    details = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField()


class SuccessResponseSerializer(serializers.Serializer):
    """Serializer for success responses."""
    message = serializers.CharField()
    data = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField()


# Route Optimization Serializers

class RouteOptimizationRequestSerializer(serializers.Serializer):
    """Serializer for route optimization request."""
    fleet_size = serializers.IntegerField(
        default=12, min_value=1, max_value=50,
        help_text="Number of available buses"
    )
    target_lines = serializers.IntegerField(
        default=12, min_value=1, max_value=20,
        help_text="Maximum number of routes to generate"
    )
    k_transfers = serializers.IntegerField(
        default=2, min_value=0, max_value=5,
        help_text="Maximum number of transfers allowed"
    )
    transfer_penalty = serializers.FloatField(
        default=5.0, min_value=0.0, max_value=30.0,
        help_text="Time penalty for transfers in minutes"
    )
    speed_kmh = serializers.FloatField(
        default=30.0, min_value=10.0, max_value=80.0,
        help_text="Average bus speed in km/h"
    )
    algorithm = serializers.ChoiceField(
        choices=[('genetic', 'Demand-driven'), ('greedy', 'Iterative'), ('both', 'Both')],
        default='genetic',
        help_text="Optimization algorithm to use"
    )
    use_existing_data = serializers.BooleanField(
        default=True,
        help_text="Use existing buildings and stops data from database"
    )
    buildings_data = serializers.ListField(
        child=serializers.DictField(),
        required=False, allow_empty=True,
        help_text="Custom buildings data (if not using existing data)"
    )
    stops_data = serializers.ListField(
        child=serializers.DictField(),
        required=False, allow_empty=True,
        help_text="Custom stops data (if not using existing data)"
    )


class OptimizedRouteStopSerializer(serializers.Serializer):
    """Serializer for optimized route stop information."""
    stop_order = serializers.IntegerField()
    stop_name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class OptimizedRouteSerializer(serializers.Serializer):
    """Serializer for optimized route information."""
    route_number = serializers.IntegerField()
    route_id = serializers.CharField()
    stops_count = serializers.IntegerField()
    cycle_minutes = serializers.FloatField()
    demand_coverage = serializers.FloatField()
    efficiency = serializers.FloatField()
    stops = OptimizedRouteStopSerializer(many=True)


class OptimizationMetricsSerializer(serializers.Serializer):
    """Serializer for optimization metrics."""
    total_cost = serializers.FloatField(required=False)
    demand_coverage = serializers.FloatField(required=False)
    efficiency = serializers.FloatField(required=False)


class RouteOptimizationResultSerializer(serializers.Serializer):
    """Serializer for route optimization results."""
    success = serializers.BooleanField()
    metrics = OptimizationMetricsSerializer(required=False)
    routes = OptimizedRouteSerializer(many=True, required=False)
    total_routes = serializers.IntegerField(required=False)
    parameters = serializers.DictField(required=False)
    error = serializers.CharField(required=False)
    optimization_id = serializers.UUIDField(required=False)
    created_at = serializers.DateTimeField(required=False)


class ApplyOptimizedRoutesSerializer(serializers.Serializer):
    """Serializer for applying optimized routes to the system."""
    optimization_id = serializers.UUIDField(
        help_text="ID of the optimization results to apply"
    )
    clear_existing = serializers.BooleanField(
        default=False,
        help_text="Whether to clear existing optimized routes before applying new ones"
    )
