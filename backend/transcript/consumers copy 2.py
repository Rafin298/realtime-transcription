import asyncio
import json
import os
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from vosk import Model, KaldiRecognizer

MODEL_PATH = os.path.join("models", "vosk-small")
model = Model(MODEL_PATH)

class TranscribeConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await self.accept()
        self.ffmpeg_proc = None
        self.vosk_task = None
        self.recognizer = None

        await self.send_json({"type": "info", "message": "connected"})

    async def disconnect(self, close_code):
        await self.stop_pipeline()

    async def receive(self, text_data=None, bytes_data=None):
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

        # ---- HANDLE AUDIO BYTES ----
        if bytes_data is not None and self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.stdin.write(bytes_data)
                await self.ffmpeg_proc.stdin.drain()
            except:
                await self.send_json({
                    "type": "error",
                    "message": "ffmpeg stdin write failed"
                })

    # PIPELINE START/STOP
    async def start_pipeline(self):
        if self.ffmpeg_proc:  # already running
            return

        cmd = [
            "ffmpeg",
            "-loglevel", "quiet",
            "-i", "pipe:0",
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
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

        self.vosk_task = asyncio.create_task(self._read_ffmpeg())

    async def stop_pipeline(self):
        # stop reader task
        if self.vosk_task:
            self.vosk_task.cancel()
            self.vosk_task = None

        # stop ffmpeg
        if self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.stdin.close()
            except:
                pass

            try:
                await asyncio.wait_for(self.ffmpeg_proc.wait(), timeout=1.0)
            except:
                self.ffmpeg_proc.kill()

        self.ffmpeg_proc = None
        self.recognizer = None

    # READ PCM FROM FFMPEG + VOSK
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
                        await self.send_json({"type": "final", "text": text})
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    await self.send_json({
                        "type": "partial",
                        "partial": partial.get("partial", "")
                    })

        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self.send_json({"type": "error", "message": str(e)})
