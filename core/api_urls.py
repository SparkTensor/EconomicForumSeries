from django.urls import path
from . import api_views

urlpatterns = [
    path('events/', api_views.EventListAPIView.as_view(), name='api-event-list'),
    path('events/<int:pk>/', api_views.EventDetailAPIView.as_view(), name='api-event-detail'),
]