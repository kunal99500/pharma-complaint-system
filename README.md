# AIVOA Pharma — AI Customer Complaint Management System

> AI-powered customer complaint management system for pharmaceutical quality management.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [AI Pipeline](#ai-pipeline)
- [Backend Overview](#backend-overview)
- [Frontend Overview](#frontend-overview)
- [API Endpoints](#api-endpoints)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)

---

## Overview

A full-stack AI-powered Quality Management System (QMS) for pharmaceutical manufacturers to log, analyze, and manage customer complaints. The system uses a LangGraph AI agent with OpenAI to automatically extract complaint information, classify risk levels per ICH Q10 and FDA 21 CFR Part 211, perform root cause analysis, generate CAPA recommendations, and detect duplicate complaints — all from a single complaint text or uploaded document.

Analysis runs as a **background task** — the API returns immediately and the frontend polls for results, keeping the system responsive even during long LLM processing.

---

## Tech Stack

### Backend
| Layer | Technology |
|-------|-----------|
| Framework | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | MySQL + PyMySQL |
| AI Agent | LangGraph |
| LLM | OpenAI API (gpt-4o-mini) |
| Validation | Pydantic |
| Document Parsing | PyPDF2 |

### Frontend
| Layer | Technology |
|-------|-----------|
| Framework | React 18 |
| State Management | Redux Toolkit |
| Routing | React Router v6 |
| HTTP Client | Axios |
| Styling | Tailwind CSS |
| Font | Google Inter |
| Icons | Lucide React |
| Notifications | React Hot Toast |
| Build Tool | Vite |

---

## Project Structure

```text
pharma-complaint-system/
│
├── backend/
│   ├── agents/
│   │   ├── nodes.py               # 4 LangGraph nodes — each makes a real LLM call
│   │   ├── prompts.py             # 4 focused prompt templates (one per node)
│   │   ├── state.py               # ComplaintAgentState TypedDict + success flags
│   │   └── complaint_agent.py     # LangGraph graph definition + runner
│   │
│   ├── core/
│   │   └── config.py              # Pydantic settings — loads from .env
│   │
│   ├── routers/
│   │   ├── complaints.py          # CRUD endpoints — pagination + filtering
│   │   └── analysis.py            # AI analysis — background task + status polling
│   │
│   ├── models.py                  # SQLAlchemy ORM models (4 tables)
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── database.py                # DB connection + session factory
│   ├── main.py                    # FastAPI app entry point + CORS
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment variable template
│   └── uploads/                   # Uploaded complaint files (gitignored)
│
└── frontend/
    ├── src/
    │   ├── api/
    │   │   └── complaintApi.js    # API function definitions
    │   │
    │   ├── components/
    │   │   ├── AICopilot.jsx      # AI results panel (risk, CAPA, root cause)
    │   │   ├── ComplaintForm.jsx  # Main form + chat interface
    │   │   ├── ComplaintList.jsx  # Filterable complaint table
    │   │   └── Layout/
    │   │       ├── Header.jsx
    │   │       ├── Layout.jsx
    │   │       └── Sidebar.jsx
    │   │
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── ComplaintFormPage.jsx
    │   │   └── ComplaintsListPage.jsx
    │   │
    │   ├── store/
    │   │   ├── store.js
    │   │   ├── complaintsSlice.js
    │   │   ├── complaintSlice.js
    │   │   └── complaintsListSlice.js
    │   │
    │   ├── App.jsx
    │   └── main.jsx
    │
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── package.json
```

---

## AI Pipeline

The LangGraph agent runs **4 nodes**, each making its own focused OpenAI API call. Every node receives the output of the previous node as structured input — so each step builds on real, grounded data rather than re-parsing raw text.

```
User Input (text / PDF / email)
            ↓
    ┌── Node 1: EXTRACT ──────────────────────────────────┐
    │   Focused prompt — extraction only                  │
    │   Input:  raw complaint text                        │
    │   Output: structured JSON of all complaint fields   │
    │           customer, product, batch, dates, etc.     │
    │           Sets extraction_success flag              │
    └─────────────────────────────────────────────────────┘
            ↓ (passes extracted JSON as input)
    ┌── Node 2: CLASSIFY + ROOT CAUSE ────────────────────┐
    │   Focused prompt — classification only              │
    │   Input:  extracted fields from Node 1              │
    │   Output: risk_level, complaint_category,           │
    │           classification_reasoning,                 │
    │           regulatory_reference,                     │
    │           is_complete, missing_fields,              │
    │           root_cause_analysis, probable_causes      │
    │           Sets classification_success flag          │
    └─────────────────────────────────────────────────────┘
            ↓ (passes classification + root cause as input)
    ┌── Node 3: CAPA + SUMMARY ───────────────────────────┐
    │   Focused prompt — CAPA generation only             │
    │   Input:  classification + root cause from Node 2   │
    │   Output: corrective and preventive CAPA actions,   │
    │           professional ai_summary for quality record│
    │           Sets capa_success flag                    │
    └─────────────────────────────────────────────────────┘
            ↓ (passes extracted fields as input)
    ┌── Node 4: DUPLICATE DETECTION ──────────────────────┐
    │   Focused prompt — comparison only                  │
    │   Input:  extracted fields + all existing complaints│
    │   Output: duplicate_score (0.0–1.0),                │
    │           similar_complaint_ids                     │
    └─────────────────────────────────────────────────────┘
            ↓
           END
```

### Why 4 separate LLM calls?

| Single mega-prompt | 4 focused prompts |
|-------------------|------------------|
| One prompt doing 7 tasks at once | Each prompt does exactly one task |
| LLM attention split across all tasks | Full LLM attention on each task |
| One failure crashes everything | Node failures are isolated — partial results saved |
| Cannot use extraction output to ground classification | Classification receives clean structured JSON as input |
| Harder to debug and improve | Each prompt can be tuned independently |

### Retry Logic

Every node retries up to 3 times with exponential backoff (1s → 2s → 4s) before failing. If a node fails, downstream nodes skip gracefully using success flags — partial results are always saved rather than discarded.

### Analysis Status

| Status | Meaning |
|--------|---------|
| `pending` | Complaint created, analysis not yet triggered |
| `processing` | Background task running — LangGraph pipeline in progress |
| `completed` | All 4 nodes succeeded |
| `partial` | Extraction succeeded but classification or CAPA failed |
| `failed` | Extraction failed — no structured data could be recovered |

### Risk Classification

Follows ICH Q10 and FDA 21 CFR Part 211 standards:

| Risk Level | Definition |
|-----------|-----------|
| `critical` | Patient safety risk, potential recall, regulatory reportable |
| `major` | Confirmed quality defect, packaging failure, spec deviation |
| `minor` | Cosmetic defect, administrative error, no quality impact |
| `unknown` | Insufficient information to assess |

---

## Backend Overview

### Analysis Flow

Analysis is non-blocking. The flow is:

```
POST /analysis/analyze
    → returns immediately with analysis_status: "processing"
    → background task starts LangGraph pipeline
    → pipeline runs 4 LLM calls sequentially
    → results saved to database
    → analysis_status updated to "completed" / "partial" / "failed"

GET /analysis/{complaint_id}
    → frontend polls this endpoint
    → returns current status + results when ready
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `complaints` | Core complaint record — all structured fields + analysis_status |
| `analysis_results` | Everything the AI agent produced (1-to-1 with complaints) |
| `capa_actions` | Individual CAPA action items (many per complaint) |
| `attachments` | Uploaded file metadata + extracted text |

### List Endpoint Filters

`GET /complaints` supports:

| Parameter | Type | Description |
|-----------|------|-------------|
| `status` | enum | Filter by complaint status |
| `risk_level` | enum | Filter by risk level |
| `category` | enum | Filter by complaint category |
| `ai_processed` | bool | Filter by whether AI has analyzed |
| `skip` | int | Pagination offset (default 0) |
| `limit` | int | Page size (default 50, max 200) |

---

## Frontend Overview

Three-column layout:

```
┌─────────────────────────────────────────────────────────┐
│              Top Navbar — AIVOA | Dashboard | Complaints │
├──────────────┬──────────────────────────┬───────────────┤
│              │                          │               │
│  AI COPILOT  │    COMPLAINT FORM        │  CHAT INPUT   │
│   (300px)    │    (center, flex)        │   (320px)     │
│              │                          │               │
│  Risk badge  │  Customer Information    │  Chat bubbles │
│  Summary     │  Product Information     │  User message │
│  Root cause  │  Complaint Details       │  AI response  │
│  CAPA cards  │  (collapsible sections)  │  File upload  │
│              │                          │               │
└──────────────┴──────────────────────────┴───────────────┘
```

### Chat + Polling Workflow

1. User types complaint text in the right chat panel
2. Frontend calls `POST /complaints` to create the complaint
3. Frontend calls `POST /analysis/analyze` — returns immediately
4. Frontend begins polling `GET /analysis/{id}` every 3 seconds
5. While polling: form shows loading state, copilot shows spinner
6. When `analysis_status === "completed"`:
   - Form fields auto-fill from extracted data
   - AI Copilot panel populates with risk, root cause, CAPA
   - Chat shows completion message with summary

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/complaints` | Create a new complaint |
| `POST` | `/complaints/upload` | Upload PDF, TXT, or EML file |
| `GET` | `/complaints` | List complaints — supports filtering + pagination |
| `GET` | `/complaints/{id}` | Get single complaint + full analysis |
| `PATCH` | `/complaints/{id}` | Update complaint fields |
| `DELETE` | `/complaints/{id}` | Delete a complaint |
| `POST` | `/analysis/analyze` | Trigger AI pipeline (returns immediately) |
| `GET` | `/analysis/{id}` | Poll for analysis status and results |
| `GET` | `/` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/kunal99500/pharma-complaint-system
cd pharma_complaint_system
```

### 2. Set up MySQL database

```sql
CREATE DATABASE pharmadb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'pharmauser'@'localhost' IDENTIFIED BY 'pharmapass';
GRANT ALL PRIVILEGES ON pharmadb.* TO 'pharmauser'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Set up backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your values
```

### 4. Run backend

```bash
uvicorn main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

### 5. Set up and run frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

App: `http://localhost:3000`

---

## Environment Variables

### Backend `.env`

```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

DATABASE_URL=mysql+pymysql://pharmauser:pharmapass@localhost:3306/pharmadb

SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## Sample Test Complaint

Paste this into the chat input to test the full pipeline:

```
From: dr.priya.sharma@citymedical.in
Subject: URGENT - Amoxicillin 500mg Capsules - Batch AMX-2025-003412

We received 500 bottles of Amoxicillin Trihydrate 500mg Capsules on August 5, 2025.
Batch: AMX-2025-003412, Manufacturing Date: March 2025, Expiry: March 2028.

Approximately 35-40 bottles show significant discoloration — brownish-yellow
instead of standard white. 5 bottles have visible powder clumping when shaken.
All 500 bottles quarantined. No product dispensed to patients.

Dr. Priya Sharma, Chief Pharmacist
City Medical Center, Mumbai, India
Phone: +91 22 4567 8901
```

**Expected output:** MAJOR risk, Product Quality category, auto-filled form fields,
root cause analysis, CAPA actions, executive summary.

---

*AIVOA.AI — AI Product Engineer Assignment*