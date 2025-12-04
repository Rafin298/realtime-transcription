from django.db import models

class TranscriptionSession(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    final_transcript = models.TextField(blank=True, default="")
    word_count = models.IntegerField(default=0)
    duration_seconds = models.FloatField(default=0.0)

    # optional metadata
    user_agent = models.CharField(max_length=255, blank=True, default="")
    
    def __str__(self):
        return f"Session {self.id}"