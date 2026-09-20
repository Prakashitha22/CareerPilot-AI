# Walkthrough: CareerPilot AI — Step 7A (Deployment Preparation)

CareerPilot AI has successfully completed **Step 7A: Deployment Preparation**. The application is now fully prepared for deployment to cloud web hosting services (such as **Render**, **Railway**, or containerized environments) without modifying the local development experience or replacing the SQLite database.

---

## 1. Summary of Changes Made in Step 7A

### A. Production WSGI Server & Dependencies (`requirements.txt`)
- Added production-grade WSGI server dependency:
  ```text
  gunicorn>=21.2.0
  ```
- Kept the runtime dependencies minimal, clean, and beginner-friendly:
  - `Flask>=3.0.0`
  - `pypdf>=4.0.0`
  - `requests>=2.31.0`
  - `python-dotenv>=1.0.0`
  - `gunicorn>=21.2.0`

### B. Python Runtime Specification (`.python-version`)
- Created `.python-version` specifying `3.11.9`.
- Ensures cloud build packs (such as Render or Railway) pin to a stable, compatible LTS Python runtime.

### C. Dynamic Port & Startup Configuration (`app.py`)
- **Dynamic `$PORT` Binding**: Cloud platforms dynamically assign a port via the `PORT` environment variable. `app.py` now detects `PORT`:
  - In cloud environments (`PORT` set): Binds to `0.0.0.0:$PORT` with debug disabled by default.
  - In local development (`PORT` not set): Defaults to `127.0.0.1:5000` with debug enabled.
- **Production WSGI Entrypoint**: The top-level `app` Flask instance is exposed directly for Gunicorn:
  ```bash
  gunicorn app:app
  ```
- **Local Development Preservation**: The standard local run command remains completely intact:
  ```bash
  py app.py
  ```
- **Upload Directory Resilience**: Ensured `UPLOAD_FOLDER` is dynamically recreated on demand if wiped during ephemeral disk restarts or file cleanups.

### D. Production Health Check Route (`GET /health`)
- Added a lightweight monitoring endpoint at `/health`:
  ```json
  {
    "status": "ok",
    "service": "CareerPilot AI"
  }
  ```
- Returns HTTP 200 for cloud load balancers and uptime pingers.
- Strictly isolated: does NOT leak database contents, API keys, or internal session details.

### E. Security & Secret Isolation
- `GEMINI_API_KEY` is loaded strictly on the server side via `os.environ`.
- Zero client exposure in templates, JavaScript, or CSS.
- `.env`, `careerpilot.db`, and `uploads/` remain safely git-ignored.

### F. SQLite Cloud Limitations Documented
- Clearly documented in `README.md` that free-tier cloud platforms (e.g., Render free tier) use **ephemeral filesystems**.
- Explains that local SQLite files reset on instance spin-down or redeploy, setting the stage for future database migrations (Step 7B / Step 8).

---

## 2. Automated Test Verification Results

The automated test suite in `tests/test_app.py` was expanded from 24 to **27 unit tests** covering the new deployment configurations:
1. `test_health_endpoint`: Proves `GET /health` returns HTTP 200 with `status: ok` and leaks no credentials.
2. `test_production_startup_configuration`: Validates the `app` WSGI callable, upload directory creation, and 16MB max upload limit.
3. `test_port_configuration_logic`: Validates dynamic `$PORT` environment variable parsing.

### Test Execution Output
```
test_404_handler (test_app.CareerPilotTestCase.test_404_handler) ... ok
test_analyze_empty_text (test_app.CareerPilotTestCase.test_analyze_empty_text) ... ok
test_analyze_valid_resume (test_app.CareerPilotTestCase.test_analyze_valid_resume) ... ok
test_api_history_routes (test_app.CareerPilotTestCase.test_api_history_routes) ... ok
test_candidate_crud (test_app.CareerPilotTestCase.test_candidate_crud) ... ok
test_candidate_history_aggregation_and_clear (test_app.CareerPilotTestCase.test_candidate_history_aggregation_and_clear) ... ok
test_career_intelligence_resume_only (test_app.CareerPilotTestCase.test_career_intelligence_resume_only) ... ok
test_career_intelligence_with_interview (test_app.CareerPilotTestCase.test_career_intelligence_with_interview) ... ok
test_database_initialization (test_app.CareerPilotTestCase.test_database_initialization) ... ok
test_end_to_end_auto_persistence (test_app.CareerPilotTestCase.test_end_to_end_auto_persistence) ... ok
test_health_endpoint (test_app.CareerPilotTestCase.test_health_endpoint) ... ok
test_homepage_loads (test_app.CareerPilotTestCase.test_homepage_loads) ... ok
test_interview_evaluate (test_app.CareerPilotTestCase.test_interview_evaluate) ... ok
test_interview_evaluate_empty_answer (test_app.CareerPilotTestCase.test_interview_evaluate_empty_answer) ... ok
test_interview_start (test_app.CareerPilotTestCase.test_interview_start) ... ok
test_interview_summary (test_app.CareerPilotTestCase.test_interview_summary) ... ok
test_offline_fallback_guarantee (test_app.CareerPilotTestCase.test_offline_fallback_guarantee) ... ok
test_port_configuration_logic (test_app.CareerPilotTestCase.test_port_configuration_logic) ... ok
test_production_startup_configuration (test_app.CareerPilotTestCase.test_production_startup_configuration) ... ok
test_save_and_retrieve_career_report (test_app.CareerPilotTestCase.test_save_and_retrieve_career_report) ... ok
test_save_and_retrieve_interview_session (test_app.CareerPilotTestCase.test_save_and_retrieve_interview_session) ... ok
test_save_and_retrieve_resume_analysis (test_app.CareerPilotTestCase.test_save_and_retrieve_resume_analysis) ... ok
test_upload_corrupted_pdf (test_app.CareerPilotTestCase.test_upload_corrupted_pdf) ... ok
test_upload_empty_filename (test_app.CareerPilotTestCase.test_upload_empty_filename) ... ok
test_upload_invalid_extension (test_app.CareerPilotTestCase.test_upload_invalid_extension) ... ok
test_upload_no_file (test_app.CareerPilotTestCase.test_upload_no_file) ... ok
test_upload_valid_pdf (test_app.CareerPilotTestCase.test_upload_valid_pdf) ... ok
test_gemini_model_configuration (test_app.CareerPilotTestCase.test_gemini_model_configuration) ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.734s

OK (100% Pass Rate)
```

---

## 3. Gemini 2.5 Flash Model Update

- Upgraded Generative AI backend model from deprecated `gemini-2.0-flash` to current stable `gemini-2.5-flash`.
- Added configurable `GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash').strip()` in [`analyzer.py`](file:///c:/Users/hp/OneDrive/Desktop/CareerPilot-AI/analyzer.py).
- Preserved all `GEMINI_API_KEY` handling, structured JSON outputs, error handling, and smart heuristic offline fallback guarantees.
- Updated UI badges in [`templates/index.html`](file:///c:/Users/hp/OneDrive/Desktop/CareerPilot-AI/templates/index.html) and documentation in [`README.md`](file:///c:/Users/hp/OneDrive/Desktop/CareerPilot-AI/README.md).
- Added `test_gemini_model_configuration` to automated test suite (28/28 tests passing).

---

## 4. How to Run the Application

### Local Development (Windows)
```powershell
py app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

### Production Command (Cloud / Linux)
```bash
gunicorn app:app
```
Or with custom binding:
```bash
gunicorn --bind 0.0.0.0:$PORT --workers 2 app:app
```

### Running the Test Suite
```powershell
py -m unittest discover -s tests -v
```
