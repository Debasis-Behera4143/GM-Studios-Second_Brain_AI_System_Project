# Second Brain Studio

A full-stack AI-powered note management and retrieval system with voice input, semantic search, and intelligent note resurfacing. Never lose a valuable thought again.

## Features

### 📝 Note Management
- **Text Notes**: Quickly save thoughts, ideas, and information
- **URL Ingestion**: Save and ingest content directly from URLs
- **File Uploads**: Support for PDF, images (with OCR), and other document formats
- **Voice Notes**: Record or upload audio to create voice-transcribed notes using OpenAI Whisper
- **Automatic Metadata**: System automatically tracks creation time, source type, and user identity

### 🎤 Voice Input (Dual Mode)
- **Browser Microphone Recording**: Record notes and queries directly in the browser without file upload
- **Audio File Upload**: Upload pre-recorded audio files in any format supported by Whisper
- **Voice-to-Text Conversion**: Automatic transcription using OpenAI Whisper model
- **Voice Queries**: Ask questions by voice - your audio is transcribed and used for semantic search

### 🔍 Intelligent Search & Retrieval
- **RAG (Retrieval-Augmented Generation)**: Semantic search powered by embeddings
- **Grounded Answers**: Use Google Gemini or other LLMs to answer questions based on your notes
- **Source Attribution**: See which notes contributed to each answer
- **Relevance Scoring**: View similarity percentages to understand match quality

### 🌊 Smart Resurfacing
- **Semantic Resurfacing**: Automatically resurface older notes that are semantically related to your recent notes
- **Spaced Repetition**: Based on 7-day recency metrics
- **Daily Suggestions**: Get up to 5 relevant suggestions from your past
- **One-Click Integration**: Click suggestions to remind yourself of past thoughts

### 🔐 User Management & Sessions
- **Secure Sessions**: Encrypted per-user sessions with 30-day TTL
- **Multi-User Support**: Isolated note storage per user
- **Authentication**: Session-based authentication with session tokens
- **No Manual Login**: Generate secure session on first access

### 🗄️ Technology Stack

**Backend:**
- FastAPI (async Python web framework)
- PostgreSQL (primary data store)
- ChromaDB (vector database for embeddings)
- OpenAI Whisper (speech-to-text)
- Google Generative AI (Gemini LLM)
- SQLAlchemy (ORM)
- 🐳 Docker & Docker Compose

**Frontend:**
- Next.js 14 (React framework)
- TypeScript
- Zustand (state management)
- Tailwind CSS (styling)
- Lucide Icons (UI components)
- Axios (HTTP client)

### 📋 API Endpoints

#### Session Management
- `POST /api/session` - Create a new secure session

#### Note Ingestion
- `POST /api/ingest` - Save a text note or URL
- `POST /api/ingest/file` - Upload and ingest a file (PDF, images, etc.)
- `POST /api/voice` - Upload an audio file to create a voice note

#### Queries & Search
- `POST /api/ask` - Ask a question (text-based RAG)
- `POST /api/query` - Semantic query on your notes
- `POST /api/voice/query` - Ask a question by voice

#### Suggestions
- `GET /api/resurface` - Get resurfacing suggestions from past notes

### 🚀 Getting Started

#### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- API Keys:
  - `GEMINI_API_KEY` (from Google AI Studio)
  - Optional: other LLM keys (GROQ, Fireworks, etc.)

#### Environment Setup

Create `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=postgresql+psycopg2://admin:password@localhost:5432/secondbrain
CHROMA_HOST=localhost
CHROMA_PORT=8000
ENABLE_RESURFACING_JOB=true
SECRET_KEY=your-secret-key-at-least-32-chars
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

#### Quick Start with Docker Compose

```bash
# Clone the repository
git clone <repo-url>
cd MT2

# Start all services (database, vector store, backend, frontend)
docker-compose up -d

# Backend will be available at: http://localhost:8080
# Frontend will be available at: http://localhost:3001
# ChromaDB UI at: http://localhost:8000
```

#### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### 💡 Usage Guide

#### Saving Notes
1. **Text Note**: Type in the save panel and click "Save"
2. **URL**: Paste any URL (starts with http:// or https://) in the save panel
3. **File**: Click "Upload and Ingest" to upload PDFs, images, or documents
4. **Voice Note**: Record directly using the microphone button or upload an audio file

#### Asking Questions
1. Type your question in the chat input box
2. Click Send or press Enter
3. The system searches your notes and provides an answer with sources
4. Alternative: Use the 🎤 button to ask by voice

#### Getting Resurfacing Suggestions
1. Check the "Resurfacing" panel on the sidebar
2. Click "Refresh" to get new suggestions
3. Suggestions are based on semantic similarity to recent notes
4. Each suggestion shows a snippet of the old note

### 🎙️ Voice Features in Detail

#### Browser Microphone Recording
- Click the 🎤 button next to the text input
- Allow microphone access when prompted
- Speak your query or note
- Recording time: Unlimited
- Automatic upload and transcription upon completion

#### Audio File Upload
- Click the 🎤 button in save or query sections
- Select a pre-recorded audio file
- Supported formats: .wav, .mp3, .m4a, .ogg, .flac, etc.
- File is transcribed using OpenAI Whisper

#### Voice-First Workflow
```
1. Record thought via microphone
   ↓
2. Automatic transcription
   ↓
3. Note saved (or answer generated)
   ↓
4. Continue with other notes/questions
```

### 🔧 Configuration & Customization

#### LLM Provider Options
The backend supports multiple LLM providers:

```python
# Google Gemini (default)
GEMINI_API_KEY=xxxx
GEMINI_MODEL=gemini-2.5-flash

# Groq (optional)
GROQ_API_KEY=xxxx
GROQ_MODEL=llama-3.1-8b-instant

# Fireworks (optional)
FIREWORKS_API_KEY=xxxx
FIREWORKS_MODEL=accounts/fireworks/models/llama-v3p1-8b-instruct
```

#### Database & Vector Store
- **PostgreSQL**: Stores all notes, metadata, and user sessions
- **ChromaDB**: Vector database for embeddings, enables semantic search

#### Feature Flags
- `ENABLE_RESURFACING_JOB`: Enable/disable automatic resurfacing suggestions
- `ALLOW_GENERAL_ANSWER_WITHOUT_NOTES`: Allow non-grounded answers

### 📊 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                     │
│     UI Components, State Management, API Client          │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST
                   ↓
┌─────────────────────────────────────────────────────────┐
│               Backend API (FastAPI)                      │
│  ├─ /api/ingest      - Note ingestion                   │
│  ├─ /api/ask         - RAG queries                      │
│  ├─ /api/voice       - Voice transcription              │
│  └─ /api/resurface   - Suggestion engine                │
└──────┬────────────────────────────────────────┬─────────┘
       │                                        │
       ↓                                        ↓
┌─────────────────────┐              ┌──────────────────────┐
│   PostgreSQL DB     │              │    ChromaDB Vector   │
│   - Notes           │              │    - Embeddings      │
│   - Users           │              │    - Similarity      │
│   - Sessions        │              │    - Retrieval       │
└─────────────────────┘              └──────────────────────┘
```

### 🐛 Troubleshooting

**Voice transcription not working:**
- Ensure Whisper is installed: `pip install openai-whisper`
- Check `is_voice_available()` returns True in backend logs
- Verify audio file format is supported

**Notes not showing up in search:**
- Ensure ChromaDB is running: `docker ps | grep chromadb`
- Check embeddings are being created for new notes
- Try refreshing the page

**Backend connection issues:**
- Verify `NEXT_PUBLIC_API_URL` in frontend environment
- Check CORS settings in backend `.env`
- Ensure backend is running: `http://localhost:8080/health`

**Permission denied on voice:**
- Browser needs https or localhost for microphone access
- Check browser permissions for microphone
- Try a different browser if it persists

### 🚧 Future Enhancements
- [ ] Real-time collaborative notes (WebSocket)
- [ ] Advanced filtering by date, source, tags
- [ ] Custom LLM fine-tuning on user's notes
- [ ] Mobile app (React Native)
- [ ] Export notes (PDF, markdown, etc.)
- [ ] Note versioning and history
- [ ] Real-time transcription in frontend
- [ ] Multi-language support

### 📝 License
[Your License Here]

### 🤝 Contributing
Contributions welcome! Please submit PRs with:
- Tests for new features
- Updated documentation
- Clear commit messages

### 📞 Support
For issues or questions, please open a GitHub issue or contact the maintainers.

---

**Built with ❤️ by Your Team**
