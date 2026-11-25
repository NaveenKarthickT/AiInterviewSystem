# AI-Driven Adaptive Interview Training & Intelligent Resume Recommendation System

## 📄 Overview

An end‑to‑end platform that helps engineering students prepare for real‑world interviews and polish their resumes.

- **Resume Analysis** – PDF/DOCX upload, structured parsing, skill extraction.
- **7‑Stage Adaptive Interview** – Intro → Skill verification → Technical → Problem‑solving → Project → Experience → Behavioral.
- **Dual‑Perspective Evaluation** – Independent technical‑knowledge and communication scores (no penalising for accent or grammar).
- **Voice Interaction** – Speech‑to‑text and text‑to‑speech powered interview flow.
- **Performance Reporting** – Radar charts, knowledge‑gap matrix, personalised learning plan.
- **Intelligent Resume Optimisation** – KEEP / MODIFY / VERIFY / REMOVE recommendations, candidate‑approved changes, ATS‑friendly PDF & DOCX export.
- **Job‑Role Recommendation** – Top‑3 engineering roles matched to verified skills.

## 🏗️ System Architecture

```
User (React SPA) <--REST API--> FastAPI Backend <--LangGraph--> AI Agents (ResumeParser, SkillAnalysis, InterviewPlanner, QuestionGenerator, KnowledgeEval, CommEval, Feedback, Optimizer, CareerRecommend)
```

- **Frontend** – React 18, Vite, Tailwind CSS, Recharts visualisations.
- **Backend** – Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic 2, LangGraph 1.2, LangChain 1.5.
- **Database** – SQLite for local dev (compatible with PostgreSQL/MySQL).
- **LLM Providers** – Configurable (Gemini, OpenAI, Groq, Ollama).
- **File handling** – PyMuPDF & python‑docx for PDF/DOCX extraction, speech‑service for STT/TTS.

## 🛠️ Tech Stack

| Layer | Tech |
|------|------|
| Frontend | React 18, Vite, Tailwind CSS, Recharts, Lucide icons |
| Backend | Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic 2, LangGraph, LangChain |
| AI | Gemini/OpenAI/Groq/Ollama APIs, LangChain agents |
| Docs | PyMuPDF, python‑docx |
| Auth | PyJWT, bcrypt |
| Speech | Native fallback + optional cloud TTS/STT |

## 📦 Prerequisites

- **Python 3.10+** (venv or conda)
- **Node.js ≥ 18** (npm or yarn)
- An LLM API key (Gemini is the default; configure others in `.env`)

## ⚙️ Installation & Setup

```bash
# Clone the repo
git clone <repo‑url>
cd "Interview System"

# Backend
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit with your keys

# Frontend
cd ../frontend
npm install
```

## 🚀 Running the Application

```bash
# Backend (development server)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (dev server)
cd ../frontend
npm run dev   # http://localhost:5173
```

Open the UI, register, upload a resume, and start an adaptive interview!

## 📚 API Documentation

- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## 📂 Project Structure
```
Interview System/
├─ backend/
│  ├─ app/
│  │  ├─ api/v1/            # routers (auth, resumes, interviews, …)
│  │  ├─ core/              # config, db, rate limiter, security middleware
│  │  ├─ models/            # SQLAlchemy ORM
│  │  ├─ agents/            # LangGraph nodes & graphs
│  │  ├─ services/          # document & speech helpers
│  │  └─ main.py
│  ├─ tests/                # unit & integration tests
│  └─ requirements.txt
├─ frontend/
│  ├─ src/                  # React components, pages, context, api wrappers
│  └─ vite.config.ts
├─ .env.example
└─ README.md
```

## ✨ Key Features
- **Modular AI agents** – each responsibility isolated (resume parsing, skill analysis, interview planning, etc.).
- **Adaptive difficulty** – interview engine raises or lowers question difficulty based on real‑time performance.
- **Independent scoring** – technical knowledge never penalised for communication issues and vice‑versa.
- **Candidate‑controlled resume edits** – no invented content; changes require explicit approval.
- **Export‑ready resumes** – ATS‑friendly single‑column PDF/DOCX generated after approval.
- **Job‑role matcher** – top‑3 engineering roles with fit percentages.

## 🔐 Security & Hardening (Implemented)
- Upload size caps (10 MB for resumes, 25 MB for audio).
- MIME/magic‑byte validation for PDF/DOCX.
- Filename sanitisation to prevent path traversal.
- Rate‑limiting middleware (60 req/min global, 10 req/min auth endpoints).
- Standard security headers (nosniff, deny, X‑XSS‑Protection, HSTS).

## 📄 License

MIT (placeholder – replace with your preferred license).
