from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import TranscriptionSession
from datetime import datetime, timedelta

class TranscriptionSessionAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create a sample session
        self.session = TranscriptionSession.objects.create(
            final_transcript="hello world",
            word_count=2,
            duration_seconds=10.5,
            ended_at=datetime.now(),
        )

    def test_get_all_sessions(self):
        url = reverse("session-list") 
        response = self.client.get("/api/sessions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertIn("final_transcript", response.data[0])

    def test_get_single_session(self):
        url = f"/api/sessions/{self.session.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["final_transcript"], "hello world")
        self.assertEqual(response.data["word_count"], 2)