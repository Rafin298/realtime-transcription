import asyncio
import json
import os
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from vosk import Model, KaldiRecognizer

# Path to your Vosk model
MODEL_PATH = os.path.join("models", "vosk-small")

# Load Vosk model once (synchronous)
model = Model(MODEL_PATH)

# class TranscribeConsumer(AsyncJsonWebsocketConsumer):
class TranscribeConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer that receives audio blobs (binary) from browser,
    pipes them to ffmpeg stdin which outputs raw PCM to stdout,
    reads PCM stdout and feeds it to Vosk recognizer, and sends transcripts back.
    """

    async def connect(self):
        await self.accept()
        self.ffmpeg_proc = None
        self.vosk_task = None
        self.recognizer = None
        # Start ffmpeg subprocess and reader task
        await self.start_ffmpeg_and_vosk()
        await self.send_json({"type": "success", "message": "connected"})

    async def disconnect(self, close_code):
        # cleanup
        if self.vosk_task:
            self.vosk_task.cancel()
        if self.ffmpeg_proc:
            try:
                self.ffmpeg_proc.stdin.close()
            except Exception:
                pass
            try:
                await asyncio.wait_for(self.ffmpeg_proc.wait(), timeout=1.0)
            except Exception:
                self.ffmpeg_proc.kill()

    async def receive(self, text_data=None, bytes_data=None):
        """
        Browser sends audio blobs as binary frames (bytes_data).
        We'll write them directly to ffmpeg stdin.
        """
        if bytes_data is None:
            # ignoring non-binary frames (you can implement control frames here)
            return

        if self.ffmpeg_proc and self.ffmpeg_proc.stdin:
            try:
                # write bytes to ffmpeg stdin
                self.ffmpeg_proc.stdin.write(bytes_data)
                await self.ffmpeg_proc.stdin.drain()
            except Exception:
                # if ffmpeg stdin closed, ignore or send error
                await self.send_json({"type": "error", "message": "ffmpeg stdin closed"})
        else:
            await self.send_json({"type": "error", "message": "ffmpeg not running"})

    async def start_ffmpeg_and_vosk(self):
        """
        Launch ffmpeg with stdin pipe (accepting webm/opus) and stdout raw PCM.
        Then spawn a reader task that reads ffmpeg stdout and feeds it
        to the Vosk recognizer.
        """

        # ffmpeg command:
        # -i - : read input from stdin
        # -f s16le -acodec pcm_s16le -ar 16000 -ac 1 - : write raw PCM to stdout
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

        # create subprocess with stdin/stdout as pipes
        self.ffmpeg_proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Create Vosk recognizer
        # sample rate is 16000 (matches ffmpeg output)
        self.recognizer = KaldiRecognizer(model, 16000.0)
        self.recognizer.SetWords(True)

        # create background task to read ffmpeg stdout and process with Vosk
        self.vosk_task = asyncio.create_task(self._read_ffmpeg_and_transcribe())

    async def _read_ffmpeg_and_transcribe(self):
        """
        Continuously read raw PCM bytes from ffmpeg stdout, feed to Vosk,
        and send partial/final results back to client.
        """
        try:
            while True:
                # read chunk size: must be an even number representing PCM frames
                data = await self.ffmpeg_proc.stdout.read(4096)
                if not data:
                    # ffmpeg ended or closed stdout: finalize
                    break

                # Feed to Vosk recognizer
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        # final result chunk
                        await self.send_json({"type": "final", "text": text})
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    # partial may contain {"partial":"..."}
                    await self.send_json({"type": "partial", "partial": partial.get("partial", "")})
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            # send error to client
            try:
                await self.send_json({"type": "error", "message": str(exc)})
            except Exception:
                pass