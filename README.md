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
| Migrations | Alembic |
| Document Parsing | PyPDF2, pytesseract, Pillow |

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
│   │   ├── nodes.py               # All 7 LangGraph node functions
│   │   ├── prompts.py             # LLM prompt templates
│   │   ├── state.py               # ComplaintAgentState TypedDict
│   │   └── complaint_agent.py     # LangGraph graph definition
│   │
│   ├── core/
│   │   └── config.py              # Pydantic settings — loads from .env
│   │
│   ├── routers/
│   │   ├── complaints.py          # CRUD endpoints for complaints
│   │   └── analysis.py            # AI analysis trigger endpoint
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
    │   │   ├── AICopilot/
    │   │   │   └── AICopilotPanel.jsx
    │   │   ├── ComplaintForm.jsx  # Main form + chat interface
    │   │   ├── ComplaintList.jsx  # Filterable complaint table
    │   │   └── Layout/
    │   │       ├── Header.jsx     # Top navigation bar
    │   │       ├── Layout.jsx     # Page layout wrapper
    │   │       └── Sidebar.jsx    # Sidebar navigation
    │   │
    │   ├── pages/
    │   │   ├── Dashboard.jsx          # KPI overview + recent complaints
    │   │   ├── DashboardPage.jsx      # Dashboard page wrapper
    │   │   ├── ComplaintFormPage.jsx  # Log/edit complaint page
    │   │   └── ComplaintsListPage.jsx # Complaints list page
    │   │
    │   ├── services/
    │   │   └── api.js             # Axios instance + interceptors
    │   │
    │   ├── store/
    │   │   ├── store.js           # Redux store configuration
    │   │   ├── index.js           # Store exports
    │   │   ├── complaintsSlice.js # Main complaint state + thunks
    │   │   ├── complaintSlice.js  # Single complaint state
    │   │   └── complaintsListSlice.js # Complaint list state
    │   │
    │   ├── styles/
    │   │   └── globals.css        # Global styles
    │   │
    │   ├── App.jsx                # Root component + routes
    │   ├── main.jsx               # React entry point + Redux Provider
    │   └── index.css              # Tailwind CSS imports + Inter font
    │
    ├── index.html                 # HTML entry point
    ├── vite.config.js             # Vite build configuration
    ├── tailwind.config.js         # Tailwind configuration
    ├── postcss.config.js          # PostCSS configuration
    └── package.json               # Node dependencies
```

---

## AI Pipeline

The LangGraph agent runs a 7-node directed graph. All 7 tasks are performed in a **single OpenAI API call** to avoid rate limits and minimize latency. Each node then reads its slice of the result from shared state.

```
User Input (text / PDF / email)
            ↓
    ┌── Node 1: EXTRACT ──────────────────────────────────┐
    │   Single OpenAI gpt-4o-mini call                    │
    │   Extracts: product, batch, customer, description   │
    │   Also performs: classification, completeness,      │
    │   root cause, CAPA, summary, duplicate detection    │
    │   Stores full result in _full_analysis state key    │
    └─────────────────────────────────────────────────────┘
            ↓
    Node 2: CLASSIFY        reads _full_analysis → risk_level, category
            ↓
    Node 3: COMPLETENESS    reads _full_analysis → is_complete, missing_fields
            ↓
    Node 4: ROOT CAUSE      reads _full_analysis → root_cause_analysis, probable_causes
            ↓
    Node 5: CAPA            reads _full_analysis → capa_actions (corrective + preventive)
            ↓
    Node 6: SUMMARIZE       reads _full_analysis → ai_summary
            ↓
    Node 7: DUPLICATES      reads _full_analysis → duplicate_score, similar_ids
            ↓
           END
```

**Risk Classification** follows ICH Q10, FDA 21 CFR Part 211 standards:

| Risk Level | Definition |
|-----------|-----------|
| `critical` | Patient safety risk, potential recall, regulatory reportable |
| `major` | Confirmed quality defect, packaging failure, spec deviation |
| `minor` | Cosmetic defect, administrative error, no quality impact |
| `unknown` | Not yet assessed |

---

## Backend Overview

The backend provides REST APIs for:

- Creating and managing customer complaints
- Uploading complaint documents (PDF, email, text)
- Extracting complaint information using AI
- Classifying complaint risk and category per ICH Q10
- Checking complaint completeness per FDA 21 CFR 211.198
- Generating root cause analysis using 5-Why methodology
- Generating CAPA recommendations (corrective + preventive)
- Generating complaint executive summaries
- Detecting similar or duplicate complaints
- Returning complaint data and AI analysis to the frontend

### Database Tables

| Table | Purpose |
|-------|---------|
| `complaints` | Core complaint record — all structured fields |
| `analysis_results` | Everything the AI agent produced (1-to-1 with complaints) |
| `capa_actions` | Individual CAPA action items (many per complaint) |
| `attachments` | Uploaded file metadata + extracted text |

---

## Frontend Overview

The frontend is a React 18 single-page application with a three-column layout:

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

### Key Components

| Component | Purpose |
|-----------|---------|
| `ComplaintForm.jsx` | Three-column layout, chat interface, auto-fill logic |
| `AICopilot.jsx` | Displays risk assessment, root cause, CAPA actions |
| `ComplaintList.jsx` | Filterable table of all complaints with risk badges |
| `Dashboard.jsx` | KPI cards — total, critical, major, AI analyzed counts |

### Chat Workflow

1. User types complaint text in the right chat panel and presses Enter
2. Message appears as a blue bubble (right-aligned)
3. AI responds with "Analyzing..." loading bubble
4. Backend runs LangGraph agent — single OpenAI call
5. Form fields auto-fill from AI extraction (product, batch, customer)
6. AI Copilot panel populates with risk assessment, root cause, CAPA
7. Chat shows completion message with risk level and summary

### Redux State

All complaint state is managed in Redux Toolkit:

| Selector | State |
|----------|-------|
| `selectComplaints` | List of all complaints |
| `selectSelectedComplaint` | Currently viewed complaint + analysis |
| `selectAnalyzing` | True while LangGraph agent runs |
| `selectFormLoading` | True while saving complaint |
| `selectListLoading` | True while fetching list |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/complaints/` | Create a new complaint |
| `POST` | `/complaints/upload` | Upload PDF or email file |
| `GET` | `/complaints/` | List all complaints (with filters) |
| `GET` | `/complaints/{id}` | Get complaint + full AI analysis |
| `PATCH` | `/complaints/{id}` | Update complaint fields |
| `DELETE` | `/complaints/{id}` | Delete a complaint |
| `POST` | `/analysis/analyze` | Trigger LangGraph AI agent |
| `GET` | `/analysis/{id}` | Get analysis result for a complaint |
| `GET` | `/` | Health check |
| `GET` | `/docs` | Swagger UI — interactive API docs |

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

### 3. Set up Backend

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

### 4. Run Backend

```bash
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### 5. Set up Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

### 6. Run Frontend

```bash
npm run dev
```

App available at: `http://localhost:3000`

---

## Environment Variables

### Backend `.env`

```env
# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Database
DATABASE_URL=mysql+pymysql://pharmauser:pharmapass@localhost:3306/pharmadb

# App
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## Sample Test Complaint

Paste this into the chat input to test the full AI pipeline:

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
root cause analysis, 4 CAPA actions, executive summary.

---

*AIVOA.AI — AI Product Engineer Assignment*