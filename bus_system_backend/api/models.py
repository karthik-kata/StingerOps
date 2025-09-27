from django.db import models

class BusStop(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    routes_serving = models.TextField(help_text="Comma-separated list of routes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Class(models.Model):
    name = models.CharField(max_length=200)
    course_code = models.CharField(max_length=20, blank=True, null=True)
    building = models.CharField(max_length=100, blank=True, null=True)
    room = models.CharField(max_length=50, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    days = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., MWF, TTh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_code} - {self.name}" if self.course_code else self.name

    class Meta:
        ordering = ['course_code', 'name']

class Bus(models.Model):
    bus_number = models.CharField(max_length=10, unique=True)
    capacity = models.IntegerField(default=50)
    current_latitude = models.FloatField(blank=True, null=True)
    current_longitude = models.FloatField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bus {self.bus_number}"

    class Meta:
        ordering = ['bus_number']

class Route(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    stops = models.ManyToManyField(BusStop, related_name='routes')
    buses = models.ManyToManyField(Bus, related_name='routes')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
