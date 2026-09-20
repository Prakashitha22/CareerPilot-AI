# CareerPilot AI — AI Resume & Interview Coach

An intelligent, web-based career acceleration and interview preparation platform built with **Python**, **Flask**, **SQLite**, and **Google Gemini Generative AI**. 

CareerPilot AI bridges the gap between static resume screening and technical interview performance. It provides automated resume text extraction, structured AI candidate analysis, an interactive 5-question technical and behavioral mock interview coach with real-time scoring, an executive career intelligence dashboard with personalized 5-step learning roadmaps, and a **persistent SQLite career history database** that preserves student progress across sessions.

Designed and engineered as a comprehensive academic college software project, the platform features a **dual-engine architecture** that seamlessly toggles between live Google Gemini 2.5 Flash REST APIs and high-precision offline heuristic fallback engines, ensuring 100% operational reliability during offline presentations, evaluations, and demonstrations.

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Project Objectives](#project-objectives)
3. [Key Features](#key-features)
4. [System Architecture & Workflow](#system-architecture--workflow)
5. [Database Architecture & Schema](#database-architecture--schema)
6. [Technology Stack](#technology-stack)
7. [Project Structure](#project-structure)
8. [Prerequisites & Installation](#prerequisites--installation)
9. [Configuration & Environment Variables](#configuration--environment-variables)
10. [Running the Application](#running-the-application)
11. [Deployment Preparation](#deployment-preparation)
12. [End-to-End User Guide](#end-to-end-user-guide)
13. [Dual-Engine & Offline Fallback Architecture](#dual-engine--offline-fallback-architecture)
14. [Automated Testing Suite](#automated-testing-suite)
15. [Security & Robustness Practices](#security--robustness-practices)
16. [Future Scope & Enhancements](#future-scope--enhancements)

---

## Problem Statement

Entering today's competitive technology job market presents several steep hurdles for college graduates and early-career developers:
- **Opaque Applicant Tracking Systems (ATS)**: Candidates receive automated rejection emails without understanding which critical skills, keywords, or quantifiable achievements were missing from their resumes.
- **Disconnected Interview Preparation**: Traditional interview prep tools are generic and detached from a candidate's actual resume experience, failing to simulate real-world contextual technical questioning.
- **Lack of Actionable Roadmaps**: Candidates rarely receive structured, chronological steps showing how to close technical gaps and transition from their current profile to their desired job role.
- **Session Data Loss**: Most web prototypes lose all candidate scans, interview scores, and improvement suggestions as soon as the browser tab is refreshed or closed.
- **Fragility in Demonstration**: Many AI-driven prototypes fail completely during live presentations when network connectivity drops or third-party cloud API rate limits are exceeded.

CareerPilot AI solves these problems through an integrated, reliable, and beginner-friendly web application with persistent local storage.

---

## Project Objectives

1. **Automate Resume Ingestion**: Safely accept PDF documents up to 16MB, parse multi-page layout text, and validate integrity without server-side crashes.
2. **Deliver Comprehensive Candidate Intelligence**: Extract 11 distinct dimensions of candidate data (education, technical skills, soft skills, projects, experience, strengths, gaps, suggested roles, and targeted resume improvements).
3. **Simulate Real-World Technical Interviews**: Dynamically generate role-specific questions across technical fundamentals, system architecture, resume projects, troubleshooting, and behavioral scenarios.
4. **Provide Objective, Multi-Dimensional Feedback**: Score responses out of 10.0 with granular feedback on technical accuracy, relevance, clarity, positive points, areas for improvement, and exemplary 10/10 model answers.
5. **Synthesize Career Intelligence**: Calculate an overall career readiness score (weighting resume alignment and live interview performance), perform multi-role matching, and generate an actionable 5-step learning timeline.
6. **Persist Complete Career Records**: Store all resume analyses, interview transcripts, and career reports in a local SQLite database (`careerpilot.db`) using clean parameterized queries and anonymous sessions.
7. **Guarantee Zero-Downtime Reliability**: Incorporate a robust offline heuristic fallback that delivers deterministic, realistic results even without an internet connection or Gemini API key.

---

## Key Features

### 1. Resume PDF Upload & Text Extraction
- **Drag-and-drop & Click-to-Upload** interface supporting PDF documents up to 16MB.
- **Multi-page plain text parsing** powered by `pypdf`.
- Path traversal protection, file format validation, and safe UUID fallback naming.
- Real-time word and character extraction metrics.

### 2. AI Resume Intelligence Dashboard
- **Structured 11-Field Extraction**:
  - Full candidate name and executive profile summary
  - Education history (degree, institution, graduation year, CGPA/honors)
  - Technical skills categorized by language, database, framework, and cloud tools
  - Soft skills and interpersonal attributes
  - Work and internship experience summaries
  - Project portfolio analysis
  - Professional certifications
  - Key technical and leadership strengths
  - Missing and complementary high-demand skills
  - Top 3 suggested job roles with match percentages
  - Actionable resume improvement recommendations
- **1-Click Launchers**: Instantly click any suggested job role to launch tailored mock interviews or calibrate career intelligence.

### 3. Interactive AI Interview Coach
- **Pre-Configured & Custom Roles**: Choose from industry roles (*Python Developer, Software Engineer, Backend Developer, Frontend Developer, Data Analyst, Data Scientist, Machine Learning Engineer*) or enter custom specialized titles.
- **5-Question Structured Interview Cycle**:
  1. Technical Fundamentals
  2. In-Depth System / Architecture
  3. Resume & Project Experience
  4. Real-World Debugging & Problem Solving
  5. Behavioral Collaboration (STAR Framework)
- **Real-Time AI Response Evaluation**:
  - Numerical score out of 10.0
  - Technical accuracy, relevance, and clarity ratings
  - Specific positive highlights and constructive critique
  - Comprehensive model answers illustrating 10/10 responses
- **Session Performance Report**: Aggregates average scores, determines hiring tiers (*Solid Hire, Strong Hire, Developing*), highlights strong areas, identifies gaps, and preserves the full Q&A transcript.

### 4. Career Intelligence & Growth Dashboard
- **Dynamic Career Readiness Score**: Combines resume alignment (50%) and live interview performance (50%).
- **Skill Gap Analysis**: Visual progress bar comparing current candidate skills against expected industry competencies.
- **Multi-Role Suitability Matching**: Explores suitability percentages and skill overlaps across adjacent career tracks.
- **Personalized 5-Step Learning Roadmap**: Phased chronological timeline (Weeks 1 to 8+) guiding students from core gap closure to portfolio capstones and job application readiness.
- **Portfolio Project Recommendations**: 3 domain-specific capstone project concepts detailing target architecture and skills practiced.
- **Resume Checklist**: Practical guidelines for quantifiable metrics, ATS keyword positioning, and link hygiene.
- **Executive Career Summary**: High-level synthesis of market positioning and immediate next action.

### 5. SQLite Database & Persistent Career History
- **Automatic Initialization**: `careerpilot.db` is created automatically on application launch without manual setup scripts.
- **Relational Tables**: Tracks `candidates`, `resume_analyses`, `interview_sessions`, and `career_reports` with foreign-key integrity and cascade deletion.
- **Zero Raw JSON Exposed**: Complete historical sessions can be viewed through interactive human-readable modals and card feeds.
- **Lightweight Anonymous Sessions**: Uses Flask's signed cookie sessions to associate records with the current student without requiring complex login passwords.
- **Safe Candidate-Scoped Clearing**: Allows users to reset their own session history with confirmation without wiping the entire database.

---

## System Architecture & Workflow

```
+-----------------------------------------------------------------------------------+
|                                  USER BROWSER                                     |
|   - PDF Resume Upload & Text View        - 11-Field Resume Intelligence           |
|   - 5-Question Interview Simulation      - Career Readiness Gauge & 5-Step Map    |
|   - Career History Feed (Filter/View)    - Record Inspection Modals               |
+-----------------------------------------------------------------------------------+
                                          |
                      HTTP POST / GET (Multipart & JSON APIs)
                                          v
+-----------------------------------------------------------------------------------+
|                              FLASK BACKEND (app.py)                               |
|   - Endpoints: /, /analyze, /interview/*, /career-intelligence, /api/history/*    |
|   - Anonymous Session Manager: get_current_candidate_id()                         |
|   - Security: Path Traversal Check, 16MB Limit, HTTP Error Handlers (413, 404, 500) |
+-----------------------------------------------------------------------------------+
             /                                               \
            /                                                 \
           v                                                   v
+------------------------------------+       +------------------------------------+
|  INTELLIGENCE ENGINE (analyzer.py) |       |     DATABASE LAYER (database.py)   |
|                                    |       |                                    |
|   [Google Gemini 2.5 Flash]        |       |   [SQLite Engine: careerpilot.db]  |
|   - Structured JSON output         |       |   - Parameterized SQL queries      |
|   - Low temperature (0.2)          |       |   - Tables:                        |
|                                    |       |     • candidates                   |
|   [Smart Offline Heuristic Engine] |       |     • resume_analyses              |
|   - 50+ tech regex keywords        |       |     • interview_sessions           |
|   - Curated role question banks    |       |     • career_reports               |
|   - Heuristic STAR answer scoring  |       |   - Fast indexes on candidate_id   |
+------------------------------------+       +------------------------------------+
```

---

## Database Architecture & Schema

CareerPilot AI uses Python's built-in `sqlite3` module. No external database servers or complex ORMs are required.

### 1. `candidates` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique candidate identifier |
| `candidate_name` | TEXT | NOT NULL DEFAULT 'Candidate' | Extracted or default candidate name |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |
| `updated_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last activity timestamp |

### 2. `resume_analyses` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Analysis record ID |
| `candidate_id` | INTEGER | NOT NULL, FK -> candidates(id) | Associated candidate ID |
| `resume_filename` | TEXT | DEFAULT 'resume.pdf' | Uploaded PDF filename |
| `summary` | TEXT | | Executive profile summary |
| `education` | TEXT | JSON Encoded | Array of degrees, institutions, and years |
| `technical_skills` | TEXT | JSON Encoded | Array of detected technical skills |
| `soft_skills` | TEXT | JSON Encoded | Array of detected soft skills |
| `experience` | TEXT | JSON Encoded | Array of work/internship experience items |
| `projects` | TEXT | JSON Encoded | Array of project items |
| `certifications` | TEXT | JSON Encoded | Array of certification strings |
| `strengths` | TEXT | JSON Encoded | Array of candidate strengths |
| `missing_skills` | TEXT | JSON Encoded | Array of skill gap recommendations |
| `suggested_roles` | TEXT | JSON Encoded | Array of matched roles with percentages |
| `resume_improvements`| TEXT | JSON Encoded | Array of actionable improvement tips |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |

### 3. `interview_sessions` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Interview session ID |
| `candidate_id` | INTEGER | NOT NULL, FK -> candidates(id) | Associated candidate ID |
| `target_role` | TEXT | NOT NULL | Target job role |
| `questions` | TEXT | JSON Encoded | Array of question prompts |
| `answers` | TEXT | JSON Encoded | Array of candidate responses |
| `evaluations` | TEXT | JSON Encoded | Array of scoring objects and model answers |
| `overall_score` | REAL | DEFAULT 0.0 | Average score (0.0 to 10.0) |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Completion timestamp |

### 4. `career_reports` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Career report ID |
| `candidate_id` | INTEGER | NOT NULL, FK -> candidates(id) | Associated candidate ID |
| `target_role` | TEXT | NOT NULL | Target job role |
| `readiness_percentage` | INTEGER | DEFAULT 0 | Overall career readiness score |
| `skill_gap` | TEXT | JSON Encoded | Matched vs. missing competencies |
| `role_matching` | TEXT | JSON Encoded | Multi-role suitability percentages |
| `learning_roadmap` | TEXT | JSON Encoded | 5-step sequential learning plan |
| `recommended_projects` | TEXT | JSON Encoded | Capstone portfolio project concepts |
| `resume_checklist` | TEXT | JSON Encoded | Actionable resume enhancement tips |
| `career_summary` | TEXT | JSON Encoded | Final synthesis statement and next action |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Calibration timestamp |

---

## Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Backend Framework** | **Python 3.10+ / Flask 3.0+** | Lightweight WSGI web application framework managing routing, requests, and JSON APIs. |
| **Database Engine** | **SQLite 3 (Built-in `sqlite3`)** | Serverless, zero-configuration relational database storing candidates and session records in `careerpilot.db`. |
| **PDF Extraction Engine** | **pypdf 4.0+** | Pure-Python PDF extraction library handling multi-page parsing, metadata, and corruption exceptions. |
| **Generative AI** | **Google Gemini 2.5 Flash REST API** | Cloud-based generative AI utilizing structured JSON generation schema for natural language reasoning. |
| **Fallback Intelligence** | **Native Heuristic Rule Engine** | Python pattern matching, regex tokenizers, curated question databases, and scoring algorithms. |
| **Configuration** | **python-dotenv** | Secure management of environment variables and sensitive credentials. |
| **Frontend UI** | **HTML5, CSS3, Modern Vanilla JavaScript** | Responsive, accessible interface featuring custom CSS variables, flexbox/grid, and zero external JS dependencies. |
| **Testing** | **Python unittest** | Automated regression and unit test suite covering file upload handling, all API endpoints, and fallback logic. |

---

## Project Structure

```
CareerPilot-AI/
│
├── app.py                      # Core Flask application, route definitions, and security handlers
├── analyzer.py                 # Resume parsing, Gemini API integrations, interview & career logic
├── database.py                 # SQLite database initialization, schemas, and parameterized queries
├── careerpilot.db              # Local SQLite database file (auto-generated, excluded in .gitignore)
├── requirements.txt            # Python dependencies (Flask, pypdf, requests, python-dotenv)
├── .env                        # Local environment configuration (API keys, secret keys - gitignored)
├── .env.example                # Example environment template for new team members
├── .gitignore                  # Git exclusions (.env, uploads/, __pycache__/, *.db)
├── README.md                   # Comprehensive academic project documentation
│
├── templates/
│   └── index.html              # Unified Single Page Application template (Steps 1 to 6)
│
├── static/
│   └── style.css               # Modern, clean CSS design system with responsive layouts
│
├── tests/
│   └── test_app.py             # 24 automated unit tests covering all routes, uploads, DB, and analyzers
│
└── uploads/                    # Server-side temporary storage for uploaded PDF resumes (auto-created)
```

---

## Prerequisites & Installation

### 1. Prerequisites
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Python**: Python 3.10 or higher installed. (On Windows, ensure the Python launcher `py` or `python` is added to your PATH).

### 2. Clone or Navigate to Project
```bash
cd c:\Users\hp\OneDrive\Desktop\CareerPilot-AI
```

### 3. (Optional but Recommended) Create a Virtual Environment
```bash
# Windows
py -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
# Windows
py -m pip install -r requirements.txt

# macOS / Linux
pip install -r requirements.txt
```

---

## Configuration & Environment Variables

Create a `.env` file in the root project directory:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Edit `.env`:

```ini
# Flask Configuration
FLASK_SECRET_KEY=your_secure_random_session_secret_key_here

# Google Gemini API Key (Optional)
# Get a free key at: https://aistudio.google.com/
# If left empty, CareerPilot AI operates automatically in offline demo mode.
GEMINI_API_KEY=your_google_gemini_api_key_here
```

---

## Running the Application

Start the Flask development server:

```bash
# Windows
py app.py

# macOS / Linux
python3 app.py
```

You will see:
```
CareerPilot AI (Academic Software Project) is running!
Open your browser and navigate to: http://127.0.0.1:5000
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

Open your browser and navigate to:  
**`http://127.0.0.1:5000`**

---

## Deployment Preparation

CareerPilot AI is configured for smooth deployment to production cloud hosting platforms (such as **Render**, **Railway**, or containerized PaaS environments).

### 1. Local Development vs. Production Execution

- **Local Development Command** (runs local Flask dev server on `127.0.0.1:5000` with hot reloading):
  ```bash
  # Windows
  py app.py

  # macOS / Linux
  python3 app.py
  ```

- **Production WSGI Command** (uses production-grade multi-worker Gunicorn server):
  ```bash
  gunicorn app:app
  ```
  Or specifying port binding and worker threads:
  ```bash
  gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
  ```

### 2. Cloud Environment Variables
Configure the following variables in your hosting provider's dashboard:

| Variable | Required | Default | Description |
|---|---|---|---|
| `PORT` | Auto-provided | `5000` | Automatically assigned by cloud platforms (e.g. Render). `app.py` listens dynamically on this port. |
| `FLASK_SECRET_KEY` | Recommended | Built-in fallback | Cryptographic secret used by Flask to sign session cookies. In production, set to a strong random string. |
| `GEMINI_API_KEY` | Optional | Empty | Your Google Gemini API key. If omitted, the application runs in offline heuristic fallback mode without crashing. |
| `FLASK_DEBUG` | Optional | `false` | Disable debug mode in production to avoid leaking internal traces. |

### 3. API Key Security (Server-Side Only)
- The `GEMINI_API_KEY` is loaded exclusively on the backend through `os.environ`.
- **Zero Client Exposure**: The API key is never rendered in HTML templates, transmitted in JavaScript AJAX calls, stored in CSS, or included in client-side code.
- **Git Protection**: `.env` and `careerpilot.db` are explicitly listed in `.gitignore` to prevent secret leakage to public Git repositories.
- **Sanitized Notices**: Error handlers scrub third-party API exception strings to ensure URLs containing query parameters (`?key=...`) are never displayed to end users.

### 4. Current SQLite Limitation for Cloud Deployment
> [!IMPORTANT]
> **Understanding Ephemeral Storage on PaaS Cloud Providers**:
> - CareerPilot AI currently uses a lightweight local SQLite database (`careerpilot.db`).
> - On cloud application platforms like Render (free tier), Railway, or Heroku, the server instances use **ephemeral (stateless) filesystems**.
> - When a free cloud service spins down due to inactivity, restarts, or receives a new code deployment, the local disk is reset. Consequently, local SQLite database records will reset to an empty state unless a paid persistent volume mount is configured.
> - While SQLite is ideal for local testing, college project grading, and offline demonstrations, production multi-user cloud persistence will be addressed in future milestones by migrating to a managed cloud database (such as PostgreSQL).

### 5. Production Health Check Endpoint
- **URL**: `GET /health`
- **Response**:
  ```json
  {
    "status": "ok",
    "service": "CareerPilot AI"
  }
  ```
- Designed for cloud uptime monitors and load balancer health probes without exposing database state or sensitive configuration.

---

## End-to-End User Guide

### Step 1: Upload & Extract Resume
1. Drag and drop your PDF resume into the **Upload Resume** card or click to browse.
2. Click **Extract Resume Text**.
3. The extracted plain text appears in the preview panel with word and character metrics.

### Step 2: Generate AI Resume Intelligence
1. Click the **Analyze Resume** button.
2. The dashboard displays:
   - Candidate profile overview and professional summary.
   - Categorized technical and soft skills.
   - Detected experience, projects, education, and certifications.
   - Distinct strengths and missing skill recommendations.
   - Suggested job roles with match percentages and justification.
   - Actionable resume improvement tips.
3. This analysis is **automatically saved to your local SQLite database**.

### Step 3: Practice with the AI Interview Coach
1. Select your target job role or type a custom role.
2. Click **Start Interview**.
3. Answer 5 structured questions (Technical Fundamentals, Architecture, Project Experience, Debugging, and Behavioral STAR).
4. Review instant scoring (out of 10.0), positive highlights, constructive suggestions, and expandable **10/10 Model Answers**.
5. Upon completion, review the **Interview Performance Report** detailing your hiring tier and full transcript.
6. The entire session is **automatically saved to your local SQLite database**.

### Step 4: Explore Career Intelligence & Growth Roadmap
1. Navigate to the **Career Intelligence Dashboard**.
2. Review your **Career Readiness Score** (50% resume alignment + 50% interview score).
3. Inspect your **Skill Gap Analysis** and adjacent **Role Matching** tracks.
4. Follow the **5-Step Personalized Learning Roadmap** (Weeks 1 to 8+).
5. Explore **Portfolio Project Recommendations** and the **Resume Checklist**.
6. The calibrated report is **automatically saved to your local SQLite database**.

### Step 5 & 6: Career History & Saved Records
1. Click **📚 Career History** in the navigation bar to jump directly to saved activities.
2. Use filter pills to filter between **All Activities**, **Resume Analyses**, **Mock Interviews**, and **Career Reports**.
3. Click **👁️ View Record** on any card to view detailed historical information in a readable format.
4. Click **🗑️ Clear History** if you wish to safely wipe your session records with confirmation.

---

## Dual-Engine & Offline Fallback Architecture

| Condition | Primary Mode (Gemini 2.5 Flash) | Fallback Mode (Smart Heuristic Engine) |
|---|---|---|
| **Trigger** | `GEMINI_API_KEY` present and API reachable | `GEMINI_API_KEY` missing, invalid, or API rate-limited |
| **Resume Analysis** | High-level generative synthesis across 11 fields | Regex tokenizer scanning 50+ tech stacks and academic patterns |
| **Interview Questions** | Contextual questions generated from resume text | Curated question banks for top roles + synthesized custom prompts |
| **Evaluation & Scoring** | Multi-attribute generative rubric (0.0 to 10.0) | Heuristic scoring based on depth, keywords, clarity, and model answers |
| **Persistence** | Automatically saved to `careerpilot.db` | Automatically saved to `careerpilot.db` |
| **User Experience** | Instant response with live AI badge | Instant response with clear offline demo badge; zero user crashes |

---

## Automated Testing Suite

The project includes an automated test suite located in `tests/test_app.py` using Python's standard `unittest` library.

### Running the Tests
```bash
# Windows
py -m unittest discover -s tests -v

# macOS / Linux
python3 -m unittest discover -s tests -v
```

### Test Coverage Breakdown (28 Automated Tests)
- `test_homepage_loads`: Confirms HTTP 200 and validates presence of all 5 UI sections.
- `test_upload_no_file`: Verifies missing file payload is handled with a clean flash redirect.
- `test_upload_empty_filename`: Verifies empty file submissions are rejected.
- `test_upload_invalid_extension`: Ensures non-PDF files (.docx, .png) are rejected.
- `test_upload_corrupted_pdf`: Proves corrupted/malformed binary uploads are safely caught without 500 crashes.
- `test_upload_valid_pdf`: Confirms valid PDF extraction and text preview generation.
- `test_analyze_empty_text`: Confirms `/analyze` returns HTTP 400 Bad Request on empty payloads.
- `test_analyze_valid_resume`: Verifies all 11 structural analysis fields are generated.
- `test_interview_start`: Confirms 5 tailored questions are generated with proper IDs and contexts.
- `test_interview_evaluate`: Validates score generation (0–10) and feedback attributes.
- `test_interview_evaluate_empty_answer`: Confirms empty answers receive score 0.0 without server errors.
- `test_interview_summary`: Confirms session aggregation and performance tier assignment.
- `test_career_intelligence_with_interview`: Validates combined 50/50 readiness calculation and roadmap output.
- `test_career_intelligence_resume_only`: Verifies graceful fallback to resume-only readiness when interview has not yet been taken.
- `test_offline_fallback_guarantee`: Ensures offline heuristic engine functions without throwing exceptions.
- `test_404_handler`: Verifies graceful error redirection for web users and clean JSON for API clients.
- `test_database_initialization`: Verifies all 4 SQLite tables are created on startup.
- `test_candidate_crud`: Verifies candidate creation, retrieval, and name updates.
- `test_save_and_retrieve_resume_analysis`: Validates resume persistence and JSON field deserialization.
- `test_save_and_retrieve_interview_session`: Validates interview persistence and Q&A history retrieval.
- `test_save_and_retrieve_career_report`: Validates career report persistence and readiness storage.
- `test_candidate_history_aggregation_and_clear`: Confirms combined chronological history and candidate-scoped clearing.
- `test_api_history_routes`: Tests `/api/history`, `/api/history/<type>/<id>`, and `/api/history/clear`.
- `test_end_to_end_auto_persistence`: Confirms that completing analysis, interview, and career intelligence automatically creates database records.
- `test_health_endpoint`: Validates production `GET /health` endpoint returns HTTP 200 without exposing secrets.
- `test_production_startup_configuration`: Confirms the `app` WSGI callable is valid for Gunicorn execution (`gunicorn app:app`).
- `test_port_configuration_logic`: Validates dynamic `$PORT` environment variable binding for cloud providers.
- `test_gemini_model_configuration`: Verifies the Gemini model configuration defaults to current stable `gemini-2.5-flash`.

---

## Security & Robustness Practices

1. **SQL Injection Protection**: All SQLite queries in `database.py` use parameterized queries (`?`). User inputs are never directly concatenated into SQL strings.
2. **Path Traversal Protection**: Uploaded file destinations are sanitized using `secure_filename()` and validated against directory traversal attacks via `os.path.abspath()` checks.
3. **File Size Enforcement**: Requests exceeding the 16MB limit are intercepted via Flask's `@app.errorhandler(413)`.
4. **No Credential Leakage**: API keys and backend stack traces are strictly confined to the server; exception handlers return sanitized, user-friendly error notices.
5. **Database Error Resilience**: Database write failures are caught in non-blocking try-except blocks, ensuring that transient database issues never crash user requests or break offline fallbacks.

---

## Future Scope & Enhancements

For prospective development and final-year academic expansion:
- **Voice & Speech-to-Text Coaching**: Browser Web Speech API integration to enable verbal mock interviews with speech-to-text transcription.
- **Exportable PDF Career Reports**: Generation of downloadable PDF career audit reports summarizing candidate readiness and improvement plans.
- **Multi-Candidate Profile Switcher**: Adding optional profile switching for campus lab computers.
- **LinkedIn & GitHub Integration**: Automated profile synchronization to complement resume data.

---

## Academic Project Information

- **Project Title**: CareerPilot AI — AI Resume & Interview Coach
- **Primary Domain**: Artificial Intelligence, Relational Databases & Web Development
- **Framework & Storage**: Python / Flask / SQLite / RESTful Web Services
- **Designation**: B.Tech / Academic Software Engineering Project
