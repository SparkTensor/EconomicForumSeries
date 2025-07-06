from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.utils import timezone

from .models import Event
from .serializers import EventSerializer


class EventListAPIView(generics.ListAPIView):
    """
    API endpoint that provides a list of ALL active events in the database.
    This is a read-only endpoint.
    """
    # This queryset now fetches all active events, ordered by the most recent first.
    queryset = Event.objects.filter(is_active=True).order_by('-start_datetime')
    serializer_class = EventSerializer
    permission_classes = [AllowAny]


class EventDetailAPIView(generics.RetrieveAPIView):
    """
    API endpoint that provides the details of a SINGLE event by its ID.
    This is a read-only endpoint.
    """
    queryset = Event.objects.filter(is_active=True)
    serializer_class = EventSerializer
    permission_classes = [AllowAny]