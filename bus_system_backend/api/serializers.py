from rest_framework import serializers
from .models import BusStop, Class, Bus, Route

class BusStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
        fields = '__all__'

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = '__all__'

class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = '__all__'

class RouteSerializer(serializers.ModelSerializer):
    stops = BusStopSerializer(many=True, read_only=True)
    buses = BusSerializer(many=True, read_only=True)
    
    class Meta:
        model = Route
        fields = '__all__'

class CSVUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    data_type = serializers.ChoiceField(choices=['classes', 'stops', 'general'])
    
class BusCountSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=20)
