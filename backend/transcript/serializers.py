from rest_framework import serializers
from .models import TranscriptionSession

class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptionSession
        fields = "__all__"