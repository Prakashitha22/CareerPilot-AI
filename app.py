import os
import uuid
from flask import Flask, render_template, request, redirect, flash, jsonify, session
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import analyzer
import database

# Load environment variables from .env if present
load_dotenv()

app = Flask(__name__)
# Secret key for session management and flash messaging
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "careerpilot-ai-platform-secret-key")

# Automatically initialize SQLite database tables on startup
database.init_db()

def get_current_candidate_id():
    """
    Retrieve candidate ID from the current anonymous user session,
    or create a new candidate record in SQLite if not yet initialized.
    """
    candidate_id = session.get('candidate_id')
    if candidate_id:
        try:
            cand = database.get_candidate(candidate_id)
            if cand:
                return candidate_id
        except Exception:
            pass
    try:
        new_id = database.create_candidate(candidate_name="Candidate")
        session['candidate_id'] = new_id
        return new_id
    except Exception:
        return None

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB maximum upload limit

def allowed_file(filename):
    """Verify that file has an allowed extension (.pdf)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """
    Extract plain text from a given PDF file path using pypdf.
    Returns a tuple: (text, error_message).
    On success: (extracted_text, None)
    On error: (None, user_friendly_error_message)
    """
    if not os.path.exists(pdf_path):
        return None, "The uploaded file could not be found on the server."

    try:
        reader = PdfReader(pdf_path)

        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                return None, "The uploaded PDF is password-protected. Please upload an unprotected PDF resume."

        extracted_pages = []
        for index, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())

        full_text = "\n\n".join(extracted_pages).strip()
        return full_text, None

    except (PdfReadError, FileNotDecryptedError):
        return None, "The uploaded file is corrupted, malformed, or not a valid PDF document."
    except Exception:
        return None, "An unexpected error occurred while parsing the PDF document."

# ==========================================
# ERROR HANDLERS (CLEAN & USER-FRIENDLY)
# ==========================================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle files exceeding maximum upload limit (16MB)."""
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({"error": "The uploaded file exceeds the 16MB maximum size limit. Please upload a smaller PDF."}), 413
    flash("The uploaded file exceeds the 16MB maximum size limit. Please upload a smaller PDF.", "error")
    return redirect('/')

@app.errorhandler(404)
def page_not_found(error):
    """Handle non-existent routes gracefully."""
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({"error": "The requested resource was not found."}), 404
    flash("The requested page was not found. Redirected to CareerPilot AI home.", "warning")
    return redirect('/')

@app.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors without leaking backend stack traces."""
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({"error": "An internal server error occurred. Please try again."}), 500
    flash("An unexpected server error occurred. Please try again.", "error")
    return redirect('/')

# ==========================================
# STEP 1 & 2 ROUTES: RESUME UPLOAD & ANALYSIS
# ==========================================

@app.route('/', methods=['GET', 'POST'])
def index():
    extracted_text = None
    filename = None
    stats = None
    analysis = None

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash("No file part detected in the request.", "error")
            return redirect(request.url)

        file = request.files['resume']

        if file.filename == '':
            flash("No file was selected. Please choose a PDF resume to upload.", "error")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file format. Only PDF documents (.pdf) are supported.", "error")
            return redirect(request.url)

        try:
            safe_name = secure_filename(file.filename)
            if not safe_name or not safe_name.lower().endswith('.pdf'):
                safe_name = f"resume_{uuid.uuid4().hex[:8]}.pdf"

            saved_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

            # Security: Ensure saved path is strictly within UPLOAD_FOLDER (path traversal check)
            real_upload_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
            real_saved_path = os.path.abspath(saved_path)
            if not real_saved_path.startswith(real_upload_dir):
                flash("Invalid upload file destination.", "error")
                return redirect(request.url)

            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(saved_path)

            text, error = extract_text_from_pdf(saved_path)
            filename = safe_name

            if error:
                flash(error, "error")
            elif not text:
                flash("Uploaded PDF seems to be empty or contains scanned images without selectable text.", "warning")
            else:
                extracted_text = text
                words = len(extracted_text.split())
                chars = len(extracted_text)
                stats = {
                    "word_count": words,
                    "char_count": chars
                }
                flash("Resume text extracted successfully! Click 'Analyze Resume' below to generate AI insights.", "success")
        except Exception:
            flash("An unexpected error occurred while processing the uploaded file. Please try again.", "error")

    return render_template('index.html', extracted_text=extracted_text, filename=filename, stats=stats, analysis=analysis)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Endpoint to analyze extracted resume text via AJAX or form submission."""
    try:
        # 1. Handle JSON / AJAX request
        if request.is_json:
            data = request.get_json(silent=True) or {}
            resume_text = data.get('text', '').strip()
            if not resume_text:
                return jsonify({'error': 'Resume text is missing or empty. Please upload a resume first.'}), 400

            analysis_result = analyzer.analyze_resume(resume_text)
            if 'error' not in analysis_result:
                try:
                    cand_id = get_current_candidate_id()
                    if cand_id:
                        cand_name = analysis_result.get('candidate_name')
                        if cand_name and cand_name.lower() != 'candidate':
                            database.update_candidate_name(cand_id, cand_name)
                        filename_to_save = data.get('filename', 'resume.pdf')
                        database.save_resume_analysis(cand_id, filename_to_save, analysis_result)
                except Exception:
                    pass
            return jsonify(analysis_result)

        # 2. Handle standard HTML form submission
        resume_text = request.form.get('resume_text', '').strip()
        filename = request.form.get('filename', 'resume.pdf')

        if not resume_text:
            flash("No resume text available for analysis. Please upload your resume first.", "error")
            return redirect('/')

        words = len(resume_text.split())
        chars = len(resume_text)
        stats = {
            "word_count": words,
            "char_count": chars
        }

        analysis_result = analyzer.analyze_resume(resume_text)
        if 'error' in analysis_result:
            flash(analysis_result['error'], "error")
        else:
            try:
                cand_id = get_current_candidate_id()
                if cand_id:
                    cand_name = analysis_result.get('candidate_name')
                    if cand_name and cand_name.lower() != 'candidate':
                        database.update_candidate_name(cand_id, cand_name)
                    database.save_resume_analysis(cand_id, filename, analysis_result)
            except Exception:
                pass
            flash("AI Resume Analysis completed successfully!", "success")

        return render_template(
            'index.html',
            extracted_text=resume_text,
            filename=filename,
            stats=stats,
            analysis=analysis_result
        )
    except Exception:
        if request.is_json:
            return jsonify({'error': 'An unexpected error occurred during resume analysis.'}), 500
        flash("An unexpected error occurred during resume analysis.", "error")
        return redirect('/')

# ==========================================
# STEP 9 ROUTES: JOB DESCRIPTION MATCHER
# ==========================================

@app.route('/job-match', methods=['POST'])
def job_match():
    """
    Compare an analyzed resume against a provided job description.
    Returns structured compatibility evaluation, matching/missing skills,
    tailored resume improvements, interview questions, and a 5-step preparation plan.
    """
    try:
        data = request.get_json(silent=True) or (request.form if request.form else {})
        if not isinstance(data, dict):
            data = {}

        job_description = data.get('job_description', '').strip()
        resume_analysis = data.get('resume_analysis', None)

        # 1. Validate resume analysis is provided and non-empty
        if not resume_analysis or not isinstance(resume_analysis, dict) or not resume_analysis.get('technical_skills'):
            return jsonify({
                'error': 'No analyzed resume found. Please upload and analyze your resume first.'
            }), 400

        # 2. Validate job description presence
        if not job_description:
            return jsonify({
                'error': 'Job description is empty. Please paste a job description to analyze.'
            }), 400

        # 3. Validate job description length (minimum 20 chars, max 25,000 chars)
        if len(job_description) < 20:
            return jsonify({
                'error': 'Job description is too short. Please paste a more detailed job posting (minimum 20 characters).'
            }), 400

        if len(job_description) > 25000:
            return jsonify({
                'error': 'Job description is excessively long (exceeds 25,000 characters). Please provide a concise job description.'
            }), 400

        # 4. Perform job description matching
        match_result = analyzer.analyze_job_description(
            resume_analysis=resume_analysis,
            job_description=job_description
        )

        if 'error' in match_result:
            return jsonify({'error': match_result['error']}), 400

        return jsonify(match_result), 200

    except Exception:
        return jsonify({
            'error': 'An unexpected error occurred while analyzing the job match. Please try again.'
        }), 500

# ==========================================
# STEP 3 ROUTES: AI INTERVIEW COACH
# ==========================================

@app.route('/interview/start', methods=['POST'])
def interview_start():
    """Start an interview session by generating 5 tailored questions."""
    try:
        data = request.get_json(silent=True) or (request.form if request.form else {})
        if not isinstance(data, dict):
            data = {}
        role = data.get('role', 'Software Engineer').strip()
        resume_text = data.get('resume_text', '').strip()

        if not role:
            role = 'Software Engineer'

        questions = analyzer.generate_interview_questions(role, resume_text)
        return jsonify({
            'success': True,
            'role': role,
            'questions': questions
        })
    except Exception:
        return jsonify({'success': False, 'error': 'Failed to generate interview questions. Please try again.'}), 500

@app.route('/interview/evaluate', methods=['POST'])
def interview_evaluate():
    """Evaluate a single question response."""
    try:
        data = request.get_json(silent=True) or (request.form if request.form else {})
        if not isinstance(data, dict):
            data = {}
        role = data.get('role', 'Software Engineer').strip()
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        question_type = data.get('question_type', 'Technical').strip()

        evaluation = analyzer.evaluate_interview_answer(role, question, answer, question_type)
        return jsonify(evaluation)
    except Exception:
        return jsonify({'error': 'Failed to evaluate interview answer. Please try again.'}), 500

@app.route('/interview/summary', methods=['POST'])
def interview_summary():
    """Generate final interview report from session history."""
    try:
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            data = {}
        role = data.get('role', 'Software Engineer').strip()
        history = data.get('history', [])

        summary = analyzer.generate_interview_summary(role, history)
        try:
            cand_id = get_current_candidate_id()
            if cand_id and history:
                questions = [h.get('question', '') for h in history]
                answers = [h.get('answer', '') for h in history]
                evaluations = [h.get('evaluation', {}) for h in history]
                database.save_interview_session(
                    candidate_id=cand_id,
                    target_role=role,
                    questions=questions,
                    answers=answers,
                    evaluations=evaluations,
                    overall_score=summary.get('overall_score', 0.0)
                )
        except Exception:
            pass
        return jsonify(summary)
    except Exception:
        return jsonify({'error': 'Failed to generate interview summary. Please try again.'}), 500

# ==========================================
# STEP 4 ROUTES: CAREER INTELLIGENCE DASHBOARD
# ==========================================

@app.route('/career-intelligence', methods=['POST'])
def career_intelligence():
    """Endpoint to generate full career readiness and intelligence data."""
    try:
        data = request.get_json(silent=True) or (request.form if request.form else {})
        if not isinstance(data, dict):
            data = {}
        role = data.get('role', 'Python Developer').strip()
        resume_analysis = data.get('resume_analysis', {})
        interview_summary = data.get('interview_summary', None)

        intelligence_result = analyzer.generate_career_intelligence(
            role=role,
            resume_analysis=resume_analysis,
            interview_summary=interview_summary
        )
        try:
            cand_id = get_current_candidate_id()
            if cand_id:
                database.save_career_report(
                    candidate_id=cand_id,
                    target_role=role,
                    report_data=intelligence_result
                )
        except Exception:
            pass
        return jsonify(intelligence_result)
    except Exception:
        return jsonify({'error': 'Failed to generate career intelligence. Please try again.'}), 500

# ==========================================
# STEP 6 ROUTES: SQLITE CAREER HISTORY
# ==========================================

@app.route('/history')
def history_page():
    """Direct route linking to Career History section."""
    return redirect('/#careerHistorySection')

@app.route('/api/history', methods=['GET'])
def api_history():
    """Return chronological career activity records for current anonymous session candidate."""
    try:
        cand_id = get_current_candidate_id()
        records = database.get_candidate_history(cand_id) if cand_id else []
        candidate_info = database.get_candidate(cand_id) if cand_id else None
        return jsonify({
            'success': True,
            'candidate': candidate_info,
            'history': records,
            'count': len(records)
        })
    except Exception:
        return jsonify({'success': False, 'history': [], 'error': 'Could not retrieve career history.'}), 500

@app.route('/api/history/<record_type>/<int:record_id>', methods=['GET'])
def api_history_detail(record_type, record_id):
    """Return structured, human-readable details for a specific history record."""
    try:
        cand_id = get_current_candidate_id()
        detail = database.get_record_detail(record_type, record_id, candidate_id=cand_id)
        if not detail:
            return jsonify({'success': False, 'error': 'Record not found.'}), 404
        return jsonify({'success': True, 'record': detail})
    except Exception:
        return jsonify({'success': False, 'error': 'Failed to load record details.'}), 500

@app.route('/api/history/clear', methods=['POST'])
def api_history_clear():
    """Safely clear only the current session candidate's saved history records."""
    try:
        cand_id = get_current_candidate_id()
        if cand_id:
            database.clear_candidate_history(cand_id)
        return jsonify({'success': True, 'message': 'Career history cleared successfully.'})
    except Exception:
        return jsonify({'success': False, 'error': 'Failed to clear career history.'}), 500

# ==========================================
# PRODUCTION HEALTH CHECK
# ==========================================

@app.route('/health', methods=['GET'])
def health():
    """
    Production health check endpoint for cloud load balancers and monitoring services.
    Returns lightweight service status without exposing internal secrets or database contents.
    """
    return jsonify({
        "status": "ok",
        "service": "CareerPilot AI"
    }), 200

if __name__ == '__main__':
    # Support dynamic PORT environment variable provided by cloud hosts (e.g. Render, Railway)
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0" if "PORT" in os.environ else "127.0.0.1"
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1") if "PORT" in os.environ else True

    print(f"CareerPilot AI is running on {host}:{port}!")
    if host == "127.0.0.1":
        print(f"Open your browser and navigate to: http://127.0.0.1:{port}")
    app.run(host=host, port=port, debug=debug_mode)
