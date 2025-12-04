# Real-Time Microphone Transcription (CPU-Only)

A real-time, CPU-only speech-to-text transcription system. Users can record audio from their browser, which is streamed to the backend for live transcription using Vosk. The system stores transcription sessions with metadata, transcript, word count, and performance metrics.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation & Execution](#installation--execution)
- [API Usage](#api-usage)
- [Architecture & Design](#architecture--design)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Limitations](#limitations)
- [Future Improvements](#future-improvements)

## ✨ Features

- ✅ **Live partial transcription** display in browser
- ✅ **Final transcript** with word count
- ✅ **Session persistence** (metadata + performance metrics)
- ✅ **WebSocket-based** audio streaming
- ✅ **CPU-only** speech recognition (no GPU required)
- ✅ **RESTful API** for retrieving transcription history
- ✅ **Docker support** for easy deployment

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.10 + Django + Django Channels (WebSocket) |
| **Database** | SQLite |
| **Speech Recognition** | Vosk (open-source, CPU-only) |
| **Frontend** | Next.js 16 |
| **API** | Django REST Framework |
| **Containerization** | Docker + Docker Compose |
| **Audio Processing** | FFmpeg |

## 🚀 Installation & Execution

### Prerequisites

- Docker & Docker Compose installed
- (Optional) Node.js 18+ and Python 3.10+ for local development

### 1. Clone Repository

```bash
git clone https://github.com/Rafin298/realtime-transcription.git
cd real-time-transcription
```

### 2. Build & Run Docker

```bash
docker-compose up --build
```

This will start:
- **Backend (Django + Daphne)** → `http://localhost:8000`
- **Frontend (Next.js)** → `http://localhost:3000`
- **PostgreSQL Database** → `localhost:5432`

> **Note:** First build may take 3-5 minutes while downloading the Vosk model (~240MB).

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## 🎯 Frontend Usage

1. Navigate to `http://localhost:3000`
2. Click **"Start Recording"** → speak into your microphone
3. Watch **partial transcription** update in real-time
4. Click **"Stop Recording"** → final transcript is saved with word count
5. View your transcription history via the API endpoints

## 📡 API Usage

### Get All Sessions

**Endpoint:** `GET /api/sessions/`

```bash
curl http://localhost:8000/api/sessions/
```

**Response Example:**

```json
[
    {
        "id": 2,
        "started_at": "2025-12-04T09:57:38.554678Z",
        "ended_at": "2025-12-04T09:57:48.022234Z",
        "final_transcript": "hello do you know what is his name",
        "word_count": 8,
        "duration_seconds": 4.674075603485107,
        "user_agent": ""
    },
    {
        "id": 1,
        "started_at": "2025-12-04T09:54:31.070613Z",
        "ended_at": "2025-12-04T09:57:04.718727Z",
        "final_transcript": "hello do you know what is my name",
        "word_count": 8,
        "duration_seconds": 5.20743989944458,
        "user_agent": ""
    }
]
```

### Get Single Session

**Endpoint:** `GET /api/sessions/<id>/`

```bash
curl http://localhost:8000/api/sessions/1/
```

**Response Example:**

```json
{
    "id": 1,
    "started_at": "2025-12-04T09:57:38.554678Z",
    "ended_at": "2025-12-04T09:57:48.022234Z",
    "final_transcript": "hello do you know what is his name",
    "word_count": 8,
    "duration_seconds": 4.674075603485107,
    "user_agent": ""
}
```

### Testing with Postman

Import the following into Postman:

**Collection:**
- `GET` `http://localhost:8000/api/sessions/`
- `GET` `http://localhost:8000/api/sessions/1/`

## 🏗 Architecture & Design

### System Architecture

```
┌─────────────┐         WebSocket          ┌──────────────┐
│   Browser   │ ─────────────────────────> │   Django     │
│   (Next.js) │ <───────────────────────── │   Channels   │
└─────────────┘         JSON Messages       └──────────────┘
      │                                            │
      │                                            ▼
      │                                     ┌──────────────┐
      │                                     │    FFmpeg    │
      │                                     │  (PCM 16kHz) │
      │                                     └──────────────┘
      │                                            │
      │                                            ▼
      │                                     ┌──────────────┐
      │                                     │     Vosk     │
      │                                     │ (Speech API) │
      │                                     └──────────────┘
      │                                            │
      │                                            ▼
      │                                     ┌──────────────┐
      └────────── REST API ───────────────> │    SQLite    │
                                            └──────────────┘
```

### WebSocket Flow

1. **Client connects** to `/ws/transcribe/`
2. Client sends `{"command": "start"}` to begin recording
3. **Audio chunks** (WebM/Opus) are streamed as binary data
4. **Backend converts** audio to PCM using FFmpeg pipeline
5. **Vosk processes** PCM and returns:
   - **Partial results**: Intermediate transcription during speech
   - **Final results**: Completed utterance when speaker pauses
6. Client sends `{"command": "stop"}` to end recording
7. **Session is finalized** and saved to database with metrics

### Design Highlights

✅ **AsyncJsonWebsocketConsumer** ensures non-blocking audio streaming and transcription

✅ **Database writes** wrapped with `database_sync_to_async` to avoid blocking the event loop

✅ **Partial and final transcriptions** sent in real-time to the frontend

✅ **FFmpeg pipeline** converts WebM/Opus to PCM on-the-fly (no file storage)

✅ **Automatic metric calculation** for word count and duration

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Vosk Small Model** | Balance between accuracy and CPU performance. Can upgrade to larger models. |
| **FFmpeg Pipeline** | Real-time audio conversion without disk I/O overhead. |
| **Django Channels** | Native WebSocket support with Django integration. |
| **Session-based Storage** | Each recording creates unique session for multi-user support. |
| **Single Table Design** | Simple schema suitable for application scale with computed metrics. |

## 🗄 Database Schema

### TranscriptionSession Model

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | Integer | Primary key | Auto-increment |
| `started_at` | DateTime | Session start timestamp | Auto-set, Indexed |
| `ended_at` | DateTime | Session end timestamp | Nullable |
| `final_transcript` | Text | Complete transcribed text | - |
| `word_count` | Integer | Number of words in transcript | Default: 0 |
| `duration_seconds` | Float | Recording duration in seconds | Nullable |
| `user_agent` | String(20) | Model name |

## 🧪 Testing

### Run Minimal Automated Tests

```bash
docker-compose exec backend python manage.py test
```

### Test Coverage

The test suite includes:
1. **API Tests**
   - GET `/api/sessions/` - List all sessions
   - GET `/api/sessions/<id>/` - Retrieve specific session


## ⚠️ Notable Limitations

| Limitation | Impact |
|------------|--------|
| **CPU-only processing** | May be slower for long audio streams; limited concurrent users |
| **Single language model** | Currently supports only English (Vosk small-en-us) |
| **WebSocket scaling** | May not scale beyond a few concurrent users without Redis |
| **No authentication** | Sessions are not associated with specific users |
| **No audio playback** | Cannot replay recorded audio (only transcript stored) |
| **Browser compatibility** | Requires browsers with WebSocket and MediaRecorder API support |

## 🚀 Suggested Future Improvements

### Performance & Scalability

- [ ] Add **Redis channel layer** for horizontal scaling across multiple servers
- [ ] Implement **queue-based processing** (Celery) for high-load scenarios
- [ ] Add **caching layer** (Redis) for frequent API calls
- [ ] Support **GPU acceleration** option for faster transcription

### Features

- [ ] **Multi-language support** with automatic language detection
- [ ] **Audio file upload** for batch processing
- [ ] **Export transcripts** as PDF/DOCX/SRT formats
- [ ] **Search functionality** across all transcripts
- [ ] **Speaker diarization** (identify different speakers)
- [ ] **Timestamp markers** in transcript
- [ ] **Edit transcript** interface for corrections

### Security & Authentication

- [ ] **User authentication** (JWT/OAuth)
- [ ] **Session ownership** (users can only access their own sessions)
- [ ] **Rate limiting** on WebSocket connections
- [ ] **HTTPS/WSS** for production deployment
- [ ] **Input sanitization** for all user inputs

### User Experience

- [ ] **Real-time waveform visualization**
- [ ] **Playback with synchronized highlighting**
- [ ] **Keyboard shortcuts** for recording controls
- [ ] **Mobile app** version
- [ ] **Dark mode** support

### Development & Operations

- [ ] **CI/CD pipeline** (GitHub Actions)
- [ ] **Monitoring & logging** (Prometheus, Grafana)
- [ ] **API documentation** (Swagger/OpenAPI)
- [ ] **Load testing** results and benchmarks

## 📁 Project Structure

```
real-time-transcription/
├── backend/
│   ├── transcriptions/
│   │   ├── models.py           # Database models
│   │   ├── consumers.py        # WebSocket consumer
│   │   ├── views.py            # REST API views
│   │   ├── serializers.py      # DRF serializers
│   │   ├── urls.py             # URL routing
│   │   └── tests.py            # Unit tests
│   ├── config/
│   │   ├── settings.py         # Django settings
│   │   ├── asgi.py             # ASGI configuration
│   │   └── urls.py             # Main URL config
│   ├── models/
│   │   └── vosk-small/         # Vosk speech model (auto-downloaded)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── app/
│   │   └── page.tsx            # Main transcription page
│   ├── package.json
│   ├── next.config.js
│   └── Dockerfile
├── docker-compose.yml
├── download_model.sh           # Model download script
├── .env.example
├── .gitignore
└── README.md
```

## 📧 Support

For issues or questions:
- Create an issue in the repository
- Contact: [rafinkhan298@gmail.com]

---

*Built with ❤️ using open-source technologies*
