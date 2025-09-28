from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid


class BaseModel(models.Model):
    """Abstract base model with common fields and functionality."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class Building(BaseModel):
    """Building model for campus locations."""
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))],
        blank=True, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))],
        blank=True, null=True
    )
    
    def clean(self):
        """Validate that both latitude and longitude are provided together."""
        if (self.latitude is None) != (self.longitude is None):
            raise ValidationError('Both latitude and longitude must be provided together.')
    
    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name
    
    class Meta:
        ordering = ['code', 'name']
        verbose_name = 'Building'
        verbose_name_plural = 'Buildings'


class BusStop(BaseModel):
    """Bus stop model with proper validation and relationships."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))]
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))]
    )
    building = models.ForeignKey(
        Building, on_delete=models.SET_NULL, 
        null=True, blank=True, related_name='bus_stops'
    )
    capacity = models.PositiveIntegerField(
        default=20, 
        validators=[MinValueValidator(1), MaxValueValidator(200)]
    )
    has_shelter = models.BooleanField(default=False)
    accessibility_features = models.JSONField(default=list, blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}" if self.code else self.name
    
    class Meta:
        ordering = ['code', 'name']
        unique_together = [['latitude', 'longitude']]
        verbose_name = 'Bus Stop'
        verbose_name_plural = 'Bus Stops'


class Course(BaseModel):
    """Course model for academic classes."""
    DAYS_CHOICES = [
        ('M', 'Monday'),
        ('T', 'Tuesday'), 
        ('W', 'Wednesday'),
        ('R', 'Thursday'),
        ('F', 'Friday'),
        ('S', 'Saturday'),
        ('U', 'Sunday'),
    ]
    
    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=20, unique=True)
    credits = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(6)]
    )
    department = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"{self.course_code} - {self.name}"
    
    class Meta:
        ordering = ['course_code']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'


class ClassSession(BaseModel):
    """Individual class session for scheduling."""
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='sessions'
    )
    building = models.ForeignKey(
        Building, on_delete=models.CASCADE, related_name='class_sessions'
    )
    room = models.CharField(max_length=50)
    instructor = models.CharField(max_length=200, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    days_of_week = models.JSONField(
        default=list,
        help_text="List of day codes: M, T, W, R, F, S, U"
    )
    capacity = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(500)]
    )
    enrollment = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    def clean(self):
        """Validate class session data."""
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        
        if self.enrollment > self.capacity:
            raise ValidationError('Enrollment cannot exceed capacity.')
    
    def __str__(self):
        return f"{self.course.course_code} - {self.building.code} {self.room}"
    
    class Meta:
        ordering = ['course__course_code', 'start_time']
        unique_together = [['building', 'room', 'start_time', 'end_time']]
        verbose_name = 'Class Session'
        verbose_name_plural = 'Class Sessions'


class Bus(BaseModel):
    """Bus model with proper validation."""
    BUS_STATUS_CHOICES = [
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('inactive', 'Inactive'),
        ('out_of_service', 'Out of Service'),
    ]
    
    bus_number = models.CharField(max_length=10, unique=True)
    license_plate = models.CharField(max_length=20, unique=True, blank=True, null=True)
    capacity = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(10), MaxValueValidator(100)]
    )
    current_latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))],
        blank=True, null=True
    )
    current_longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))],
        blank=True, null=True
    )
    status = models.CharField(
        max_length=20, choices=BUS_STATUS_CHOICES, default='active'
    )
    last_maintenance = models.DateField(blank=True, null=True)
    accessibility_features = models.JSONField(default=list, blank=True)
    
    def clean(self):
        """Validate bus location data."""
        if (self.current_latitude is None) != (self.current_longitude is None):
            raise ValidationError('Both latitude and longitude must be provided together.')
    
    @property
    def is_operational(self):
        """Check if bus is operational."""
        return self.status == 'active' and self.is_active
    
    def __str__(self):
        return f"Bus {self.bus_number}"
    
    class Meta:
        ordering = ['bus_number']
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'


class Route(BaseModel):
    """Bus route model with proper relationships."""
    ROUTE_TYPE_CHOICES = [
        ('campus', 'Campus Route'),
        ('express', 'Express Route'),
        ('night', 'Night Route'),
        ('weekend', 'Weekend Route'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True, null=True)
    route_type = models.CharField(
        max_length=20, choices=ROUTE_TYPE_CHOICES, default='campus'
    )
    color = models.CharField(
        max_length=7, default='#FF0000',
        help_text="Hex color code for route display"
    )
    frequency_minutes = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Frequency in minutes"
    )
    operating_hours_start = models.TimeField(default='06:00')
    operating_hours_end = models.TimeField(default='22:00')
    operating_days = models.JSONField(
        default=list,
        help_text="List of operating day codes: M, T, W, R, F, S, U"
    )
    
    def clean(self):
        """Validate route operating hours."""
        if self.operating_hours_start >= self.operating_hours_end:
            raise ValidationError('End time must be after start time.')
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['code']
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'


class RouteStop(BaseModel):
    """Through model for Route-BusStop relationship with ordering."""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_stops')
    bus_stop = models.ForeignKey(BusStop, on_delete=models.CASCADE, related_name='route_stops')
    stop_order = models.PositiveIntegerField()
    arrival_time_offset = models.DurationField(
        help_text="Time offset from route start (e.g., 5 minutes)"
    )
    
    class Meta:
        ordering = ['route', 'stop_order']
        unique_together = [['route', 'bus_stop'], ['route', 'stop_order']]
        verbose_name = 'Route Stop'
        verbose_name_plural = 'Route Stops'
    
    def __str__(self):
        return f"{self.route.code} - Stop {self.stop_order}: {self.bus_stop.name}"


class RouteAssignment(BaseModel):
    """Assignment of buses to routes."""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='assignments')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='assignments')
    assigned_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def clean(self):
        """Validate route assignment."""
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time.')
        
        # Check for overlapping assignments for the same bus
        overlapping = RouteAssignment.objects.filter(
            bus=self.bus,
            assigned_date=self.assigned_date,
            is_active=True
        ).exclude(pk=self.pk)
        
        for assignment in overlapping:
            if (self.start_time < assignment.end_time and 
                self.end_time > assignment.start_time):
                raise ValidationError(
                    f'Bus {self.bus.bus_number} has overlapping assignment '
                    f'on {assignment.route.code} route.'
                )
    
    class Meta:
        ordering = ['assigned_date', 'start_time']
        unique_together = [['route', 'bus', 'assigned_date', 'start_time']]
        verbose_name = 'Route Assignment'
        verbose_name_plural = 'Route Assignments'
    
    def __str__(self):
        return f"{self.bus.bus_number} -> {self.route.code} on {self.assigned_date}"


class Source(BaseModel):
    """Source locations for route optimization (e.g., dorms, parking lots)."""
    SOURCE_TYPE_CHOICES = [
        ('dormitory', 'Dormitory'),
        ('parking', 'Parking Facility'), 
        ('transit', 'Transit Station'),
        ('residence', 'Residential Area'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200, unique=True)
    source_type = models.CharField(
        max_length=20, choices=SOURCE_TYPE_CHOICES, default='other'
    )
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-90')), MaxValueValidator(Decimal('90'))]
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6,
        validators=[MinValueValidator(Decimal('-180')), MaxValueValidator(Decimal('180'))]
    )
    demand = models.PositiveIntegerField(
        default=100,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text="Estimated daily passenger demand from this source"
    )
    capacity = models.PositiveIntegerField(
        blank=True, null=True,
        validators=[MinValueValidator(1)],
        help_text="Maximum capacity (e.g., parking spaces, dorm residents)"
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        unique_together = [['latitude', 'longitude']]
        verbose_name = 'Source'
        verbose_name_plural = 'Sources'
