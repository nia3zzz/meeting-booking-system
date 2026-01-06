from rest_framework import serializers


class TimeSlotSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    from_time = serializers.TimeField()
    to_time = serializers.TimeField()
    timezone = serializers.CharField(max_length=65, default="UTC")
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
