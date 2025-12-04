from rest_framework import generics
from .models import TranscriptionSession
from .serializers import SessionSerializer

class SessionListView(generics.ListAPIView):
    queryset = TranscriptionSession.objects.order_by("-id")
    serializer_class = SessionSerializer

class SessionDetailView(generics.RetrieveAPIView):
    queryset = TranscriptionSession.objects.all()
    serializer_class = SessionSerializer