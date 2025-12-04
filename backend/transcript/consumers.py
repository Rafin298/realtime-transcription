import asyncio
import json
import os
import time

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from vosk import Model, KaldiRecognizer
from datetime import datetime
from transcript.models import TranscriptionSession

# ------------------------------
# Load Vosk Model
# ------------------------------
MODEL_PATH = os.path.join("models", "vosk-small")
model = Model(MODEL_PATH)


class TranscribeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Runtime vars
        self.session_obj = None  # <-- CREATE ONLY WHEN PIPELINE STARTS
        self.ffmpeg_proc = None
        self.vosk_task = None
        self.recognizer = None
        self.final_accumulated = ""
        self.start_time = None
        self.session_saved = False

        await self.send_json({"type": "info", "message": "connected"})

    async def disconnect(self, close_code):
        await self.stop_pipeline()

    # -------------------------
    # RECEIVE - commands + audio
    # -------------------------
    async def receive(self, text_data=None, bytes_data=None):

        # ---- JSON COMMANDS ----
        if text_data is not None:
            try:
                msg = json.loads(text_data)
            except:
                return

            cmd = msg.get("command")

            if cmd == "start":
                await self.start_pipeline()
                await self.send_json({"type": "info", "message": "pipeline started"})
                return

            if cmd == "stop":
                await self.stop_pipeline()
                await self.send_json({"type": "info", "message": "pipeline stopped"})
                return

        # ---- AUDIO BYTES ----
        if bytes_data is not None and self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.stdin.write(bytes_data)
                await self.ffmpeg_proc.stdin.drain()
            except:
                await self.send_json(
                    {"type": "error", "message": "ffmpeg stdin write failed"}
                )

    # -------------------------
    # START PIPELINE
    # -------------------------
    async def start_pipeline(self):
        if self.ffmpeg_proc:
            return  # already running

        # Create a NEW DB session for each start
        self.session_obj = await database_sync_to_async(
            TranscriptionSession.objects.create
        )(user_agent="Vosk")

        self.session_saved = False
        self.start_time = time.time()
        self.final_accumulated = ""

        cmd = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-i",
            "pipe:0",
            "-f",
            "s16le",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            "pipe:1",
        ]

        self.ffmpeg_proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self.recognizer = KaldiRecognizer(model, 16000.0)
        self.recognizer.SetWords(True)

        # Start background Vosk processor
        self.vosk_task = asyncio.create_task(self._read_ffmpeg())

    # -------------------------
    # STOP PIPELINE  + SAVE DB
    # -------------------------
    async def stop_pipeline(self):
        # stop background vosk task
        if self.vosk_task:
            self.vosk_task.cancel()
            self.vosk_task = None

        # close ffmpeg
        if self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.stdin.close()
            except:
                pass

            try:
                await asyncio.wait_for(self.ffmpeg_proc.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                self.ffmpeg_proc.kill()

            self.ffmpeg_proc = None

        # -------- SAVE SESSION TO DATABASE (ONLY ONCE) ----------
        if self.session_obj and not self.session_saved:  
            self.session_saved = True  
            duration = (time.time() - self.start_time) if self.start_time else 0
            final_text = self.final_accumulated.strip()

            await database_sync_to_async(self._save_session)(
                final_text,
                duration,
            )

        self.recognizer = None

    # Sync helper (executed via database_sync_to_async)
    def _save_session(self, text, duration):
        self.session_obj.final_transcript = text
        self.session_obj.word_count = len(text.split()) if text else 0
        self.session_obj.duration_seconds = duration
        self.session_obj.ended_at = datetime.now()
        self.session_obj.save()

    # -------------------------
    # READ PCM STREAM → VOSK
    # -------------------------
    async def _read_ffmpeg(self):
        try:
            while True:
                data = await self.ffmpeg_proc.stdout.read(4096)
                if not data:
                    break

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")

                    if text:
                        if self.final_accumulated:
                            self.final_accumulated += " " + text
                        else:
                            self.final_accumulated = text
                        
                        await self.send_json({"type": "final", "text": text})

                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    await self.send_json(
                        {"type": "partial", "partial": partial.get("partial", "")}
                    )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self.send_json({"type": "error", "message": str(e)})