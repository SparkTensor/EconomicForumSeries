from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    """
    Serializer for the Event model, optimized for API consumption.
    """
    # Use our custom property to always get a valid image URL
    featured_image = serializers.URLField(source='featured_image_url', read_only=True)
    
    # Show the human-readable version of the event type
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    # Also include the event status
    event_status = serializers.CharField(read_only=True)
    
    # Add a field for the detail page URL on your own site
    event_detail_url = serializers.SerializerMethodField()

    class Meta:
        model = Event
        # Define the fields you want to expose in your API
        fields = [
            'id',
            'name',
            'description',
            'start_datetime',
            'end_datetime',
            'event_type',
            'event_type_display',
            'physical_location',
            'online_link',
            'featured_image', # This will now use the URL from our property
            'event_status',
            'event_detail_url',
        ]
        
    def get_event_detail_url(self, obj):
        # This creates a full, absolute URL to the event detail page
        # which is very useful for API consumers.
        request = self.context.get('request')
        return request.build_absolute_uri(obj.get_absolute_url()) # We'll add this method to the model next