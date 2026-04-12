# 🧠 Second Brain AI System (MVP)

A personal knowledge management system with **AI-powered retrieval (RAG)**.
Save notes and query them conversationally using a local LLM.

---

# 🚀 Features

- ✅ Add notes (text input)
- ✅ Store notes in database
- ✅ Automatic embeddings generation
- ✅ Semantic search using vector database
- ✅ AI-powered question answering (RAG)
- ✅ Local LLM (no API cost)
- ✅ Simple frontend UI

---

# 🏗️ Tech Stack

## 💻 Frontend

- React (Vite)
- Axios (API calls)

## ⚙️ Backend

- FastAPI (Python)
- Uvicorn (ASGI server)

## 🗄️ Database

- SQLite (for MVP)

## 🧠 AI / ML

- Sentence Transformers (`all-MiniLM-L6-v2`) → embeddings
- ChromaDB → vector database
- Ollama → local LLM runtime
- Mistral model (`mistral:latest`)

## 🔌 Other Tools

- SQLAlchemy → ORM
- Pydantic → request validation

---

# 📁 Project Structure

```
second-brain/
│
├── backend/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── embeddings.py
│   ├── rag.py
│   ├── llm.py
│   └── requirements.txt
│
├── frontend/
│   └── frontend/
│           └──(React app)
│
└── README.md
```

---

# ⚙️ Setup Instructions

---

## 1️⃣ Clone Project

```
git clone <your-repo-url>
cd second-brain
```

---

## 2️⃣ Backend Setup

### 📦 Install dependencies

```
cd backend
pip install -r requirements.txt
```

If no `requirements.txt`, install manually:

```
pip install fastapi uvicorn sqlalchemy
pip install sentence-transformers chromadb
pip install requests
```

---

### ▶️ Run Backend

```
uvicorn main:app --reload
```

Backend runs on:

```
http://localhost:8000
```

API Docs:

```
http://localhost:8000/docs
```

---

## 3️⃣ Ollama Setup (Local AI)

### 📥 Install Ollama

Download from:
https://ollama.com/download

---

### 📦 Pull model

```
ollama pull mistral
```

---

### ▶️ Run Ollama

```
ollama serve
```

Runs on:

```
http://localhost:11434
```

---

## 4️⃣ Frontend Setup

```
cd frontend
npm install
npm run dev
```

Frontend runs on:

```
http://localhost:5173
```

---

# 🔗 How It Works

```
Frontend (5173)
   ↓
Backend (8000)
   ↓
Vector DB + Embeddings
   ↓
Ollama (11434)
   ↓
Response → Frontend
```

---

# 🧪 Usage

### ➤ Add Notes

- Enter text in UI
- Click "Save Note"

---

### ➤ Ask Questions

- Ask anything related to saved notes
- AI responds using your data

Example:

```
What do I know about machine learning?
```

---

# ⚠️ Common Issues & Fixes

## ❌ CORS Error

**Fix:** Ensure CORS middleware is added in `main.py`

---

## ❌ Backend not reachable

Check:

```
http://localhost:8000/docs
```

---

## ❌ Ollama not responding

Run:

```
ollama serve
```

---

## ❌ Slow responses

- Local model → slower than APIs
- Use smaller model (`phi3`) if needed

---

# 🔥 Future Improvements

- Browser extension (1-click capture)
- Voice input (Whisper)
- Auto-tagging (spaCy)
- Chat history memory
- Proactive note resurfacing
- Knowledge graph (Neo4j)

---

# 🧠 Key Concept

This system uses **RAG (Retrieval-Augmented Generation)**:

1. Store notes → convert to embeddings
2. Query → find similar notes
3. Send context → LLM
4. Generate answer

---

# 🚀 Status

✅ MVP Complete
🔄 Ready for enhancements

---

# 👨‍💻 Author

Built as a **Second Brain AI System** project.

---

# ⭐ Tip

This is not just a project — it's a **foundation for a real AI product**.

---
