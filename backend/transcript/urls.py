from django.urls import path
from . import views
from . import consumers
from channels.routing import URLRouter
from django.urls import re_path

from .views import SessionListView, SessionDetailView

urlpatterns = [
    path("sessions/", SessionListView.as_view(), name="session-list"),
    path("sessions/<int:pk>/", SessionDetailView.as_view()),
]

# For ASGI websocket routing (imported by asgi.py)
websocket_urlpatterns = [
    re_path(r"ws/transcribe/?$", consumers.TranscribeConsumer.as_asgi()),
]