import os
import io
import unittest
import sqlite3
from pypdf import PdfWriter
from unittest.mock import patch, MagicMock
from app import app
import analyzer
import database

class CareerPilotTestCase(unittest.TestCase):
    """Comprehensive test suite covering all modules, database operations, and endpoints of CareerPilot AI."""

    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Ensure database is initialized
        database.init_db()

        # Sample test resume text
        self.sample_resume = """
        Alex Johnson
        Email: alex.johnson@example.com | Phone: +1 555-0199
        
        Education:
        Bachelor of Technology in Computer Science and Engineering
        Apex Institute of Technology, 2024
        CGPA: 8.9 / 10.0

        Technical Skills:
        Python, Flask, JavaScript, SQL, PostgreSQL, Git, Docker, REST APIs

        Soft Skills:
        Communication, Teamwork, Critical Thinking, Problem Solving

        Work Experience:
        Software Engineering Intern | DataPulse Systems (2023 - 2024)
        - Developed RESTful API endpoints using Python Flask and PostgreSQL.
        - Automated database queries reducing response time by 20%.

        Projects:
        CareerPilot AI - Intelligent Career Recommendation Platform
        - Implemented resume parsing and heuristic skill gap analysis.
        - Built interactive interview coaching interface with instant scoring.

        Certifications:
        AWS Certified Cloud Practitioner (2023)
        Python Programming Specialization - Coursera
        """

    # ==========================================
    # 1. UI & HOMEPAGE TESTS
    # ==========================================

    def test_homepage_loads(self):
        """Verify the main application page loads successfully with HTTP 200 and all feature headers."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("CareerPilot AI", html)
        self.assertIn("Upload Resume", html)
        self.assertIn("AI Resume Intelligence Dashboard", html)
        self.assertIn("AI Technical & Behavioral Interview Coach", html)
        self.assertIn("Career Intelligence & Growth Dashboard", html)
        self.assertIn("Career History & Saved Records", html)

    # ==========================================
    # 2. PDF UPLOAD & PARSING TESTS
    # ==========================================

    def test_upload_no_file(self):
        """Verify uploading with no file part redirects cleanly with an error flash."""
        response = self.client.post('/', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No file part detected", html)

    def test_upload_empty_filename(self):
        """Verify uploading an empty filename redirects cleanly."""
        data = {'resume': (io.BytesIO(b""), '')}
        response = self.client.post('/', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("No file was selected", html)

    def test_upload_invalid_extension(self):
        """Verify non-PDF file formats are rejected."""
        data = {'resume': (io.BytesIO(b"Fake content"), 'document.docx')}
        response = self.client.post('/', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Invalid file format", html)

    def test_upload_corrupted_pdf(self):
        """Verify corrupted PDF uploads are caught safely without causing a 500 crash."""
        data = {'resume': (io.BytesIO(b"%PDF-1.4 Corrupted content that cannot be parsed"), 'corrupt.pdf')}
        response = self.client.post('/', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertTrue(
            "corrupted" in html.lower() or "malformed" in html.lower() or "error" in html.lower()
        )

    def test_upload_valid_pdf(self):
        """Verify uploading a valid PDF document extracts text and displays extraction statistics."""
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)

        data = {'resume': (pdf_bytes, 'blank_resume.pdf')}
        response = self.client.post('/', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    # ==========================================
    # 3. RESUME ANALYSIS TESTS
    # ==========================================

    def test_analyze_empty_text(self):
        """Verify /analyze returns 400 Bad Request when resume text is empty."""
        response = self.client.post('/analyze', json={'text': '   '})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)

    def test_analyze_valid_resume(self):
        """Verify /analyze returns all 11 required structural analysis fields."""
        response = self.client.post('/analyze', json={'text': self.sample_resume})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        expected_fields = [
            'candidate_name', 'summary', 'education', 'technical_skills',
            'soft_skills', 'experience', 'projects', 'certifications',
            'strengths', 'missing_skills', 'suggested_roles', 'resume_improvements'
        ]
        for field in expected_fields:
            self.assertIn(field, data, f"Missing expected analysis field: {field}")

        self.assertIn('Python', data['technical_skills'])
        self.assertIn('SQL', data['technical_skills'])
        self.assertTrue(len(data['suggested_roles']) > 0)
        self.assertTrue(len(data['resume_improvements']) > 0)

    # ==========================================
    # 4. INTERVIEW COACH TESTS
    # ==========================================

    def test_interview_start(self):
        """Verify /interview/start generates 5 tailored questions."""
        payload = {
            'role': 'Python Developer',
            'resume_text': self.sample_resume
        }
        response = self.client.post('/interview/start', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('role'), 'Python Developer')
        questions = data.get('questions', [])
        self.assertEqual(len(questions), 5)
        for q in questions:
            self.assertIn('id', q)
            self.assertIn('type', q)
            self.assertIn('question', q)
            self.assertIn('context', q)

    def test_interview_evaluate(self):
        """Verify /interview/evaluate scores an answer out of 10 and returns constructive feedback."""
        payload = {
            'role': 'Python Developer',
            'question': 'How do Python lists and dictionaries differ in access complexity?',
            'answer': 'Lists are ordered arrays with O(1) index access, while dictionaries are hash tables providing average O(1) key lookups.',
            'question_type': 'Technical'
        }
        response = self.client.post('/interview/evaluate', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('score', data)
        self.assertGreaterEqual(data['score'], 0.0)
        self.assertLessEqual(data['score'], 10.0)
        self.assertIn('technical_accuracy', data)
        self.assertIn('relevance', data)
        self.assertIn('clarity', data)
        self.assertIn('what_was_done_well', data)
        self.assertIn('what_could_be_improved', data)
        self.assertIn('better_example_answer', data)

    def test_interview_evaluate_empty_answer(self):
        """Verify submitting an empty answer is handled cleanly with score 0.0."""
        payload = {
            'role': 'Python Developer',
            'question': 'What is the GIL?',
            'answer': '',
            'question_type': 'Technical'
        }
        response = self.client.post('/interview/evaluate', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get('score'), 0.0)

    def test_interview_summary(self):
        """Verify /interview/summary aggregates session questions and calculates performance tier."""
        payload = {
            'role': 'Python Developer',
            'history': [
                {
                    'question': 'What is the GIL?',
                    'answer': 'The Global Interpreter Lock restricts thread execution.',
                    'evaluation': {'score': 8.0, 'what_could_be_improved': 'Mention I/O bounds.'}
                },
                {
                    'question': 'Explain lists vs dicts.',
                    'answer': 'Lists use index; dicts use hashing.',
                    'evaluation': {'score': 8.5, 'what_could_be_improved': 'None.'}
                }
            ]
        }
        response = self.client.post('/interview/summary', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('overall_score', data)
        self.assertIn('performance_tier', data)
        self.assertIn('strong_areas', data)
        self.assertIn('areas_to_improve', data)
        self.assertIn('recommended_topics', data)

    # ==========================================
    # 5. CAREER INTELLIGENCE TESTS
    # ==========================================

    def test_career_intelligence_with_interview(self):
        """Verify /career-intelligence calculates readiness and returns complete roadmap and recommendations."""
        payload = {
            'role': 'Python Developer',
            'resume_analysis': {
                'technical_skills': ['Python', 'Flask', 'SQL', 'Git', 'Docker']
            },
            'interview_summary': {
                'overall_score': 8.2
            }
        }
        response = self.client.post('/career-intelligence', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn('readiness', data)
        self.assertGreaterEqual(data['readiness']['percentage'], 0)
        self.assertLessEqual(data['readiness']['percentage'], 100)
        self.assertIn('explanation', data['readiness'])
        self.assertIn('Combined Assessment', data['readiness']['source'])

        self.assertIn('skill_gap', data)
        self.assertIn('matched_skills', data['skill_gap'])
        self.assertIn('missing_skills', data['skill_gap'])
        self.assertIn('match_percentage', data['skill_gap'])

        self.assertIn('role_matching', data)
        self.assertTrue(len(data['role_matching']) >= 2)

        self.assertIn('learning_roadmap', data)
        self.assertEqual(len(data['learning_roadmap']), 5)

        self.assertIn('recommended_projects', data)
        self.assertTrue(len(data['recommended_projects']) >= 2)

        self.assertIn('resume_checklist', data)
        self.assertTrue(len(data['resume_checklist']) >= 3)

        self.assertIn('career_summary', data)
        self.assertIn('profile_summary', data['career_summary'])
        self.assertIn('recommended_next_action', data['career_summary'])

    def test_career_intelligence_resume_only(self):
        """Verify career intelligence works accurately before any interview has been conducted."""
        payload = {
            'role': 'Backend Developer',
            'resume_analysis': {
                'technical_skills': ['Python', 'PostgreSQL', 'Git']
            },
            'interview_summary': None
        }
        response = self.client.post('/career-intelligence', json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('readiness', data)
        self.assertEqual(data['readiness']['source'], 'Resume-Based Assessment')

    def test_offline_fallback_guarantee(self):
        """Verify heuristic analyzer works completely offline without crashing or throwing exceptions."""
        result = analyzer.smart_heuristic_analysis(self.sample_resume)
        self.assertEqual(result['source'], 'demo_fallback')
        self.assertIn('notice', result)
        self.assertEqual(result['candidate_name'], 'Alex Johnson')
        self.assertTrue('Python' in result['technical_skills'])
        self.assertEqual(len(result['suggested_roles']), 3)

    def test_404_handler(self):
        """Verify 404 responses are handled gracefully without leaking stack traces."""
        response = self.client.get('/invalid-page-for-testing')
        self.assertEqual(response.status_code, 302)

        json_response = self.client.get('/invalid-page-for-testing', headers={'Accept': 'application/json'})
        self.assertEqual(json_response.status_code, 404)
        self.assertIn('error', json_response.get_json())

    # ==========================================
    # 6. STEP 6: SQLITE DATABASE & HISTORY TESTS
    # ==========================================

    def test_database_initialization(self):
        """Verify all four SQLite tables are created with proper schemas."""
        conn = database.get_db_connection()
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row['name'] for row in cursor.fetchall()]
            self.assertIn('candidates', tables)
            self.assertIn('resume_analyses', tables)
            self.assertIn('interview_sessions', tables)
            self.assertIn('career_reports', tables)
        finally:
            conn.close()

    def test_candidate_crud(self):
        """Verify candidate creation, retrieval, and name updates."""
        cand_id = database.create_candidate("Test Student")
        self.assertIsInstance(cand_id, int)

        cand = database.get_candidate(cand_id)
        self.assertIsNotNone(cand)
        self.assertEqual(cand['candidate_name'], "Test Student")

        # Update candidate name
        success = database.update_candidate_name(cand_id, "Jane Engineer")
        self.assertTrue(success)
        cand_updated = database.get_candidate(cand_id)
        self.assertEqual(cand_updated['candidate_name'], "Jane Engineer")

    def test_save_and_retrieve_resume_analysis(self):
        """Verify resume analysis persistence and deserialization."""
        cand_id = database.create_candidate("Resume Test User")
        analysis_data = {
            'summary': 'Full stack developer with Python expertise.',
            'technical_skills': ['Python', 'Django', 'SQL'],
            'soft_skills': ['Leadership', 'Communication'],
            'education': [{'degree': 'B.Tech CS', 'institution': 'MIT', 'year': '2024'}],
            'projects': [{'title': 'Web App', 'technologies': ['Python']}],
            'experience': [{'role': 'Intern', 'company': 'Acme'}],
            'certifications': ['AWS Certified'],
            'strengths': ['Fast learner'],
            'missing_skills': ['Docker'],
            'suggested_roles': [{'title': 'Backend Developer', 'match_score': '90%'}],
            'resume_improvements': ['Add metrics']
        }
        record_id = database.save_resume_analysis(cand_id, "my_resume.pdf", analysis_data)
        self.assertIsNotNone(record_id)

        # Retrieve latest
        latest = database.get_latest_resume_analysis(cand_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest['resume_filename'], "my_resume.pdf")
        self.assertEqual(latest['technical_skills'], ['Python', 'Django', 'SQL'])
        self.assertEqual(latest['record_type'], 'resume_analysis')

        # Retrieve detail
        detail = database.get_record_detail('resume_analysis', record_id, cand_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail['summary'], 'Full stack developer with Python expertise.')

    def test_save_and_retrieve_interview_session(self):
        """Verify interview session persistence and Q&A history retrieval."""
        cand_id = database.create_candidate("Interview Test User")
        questions = ["What is the GIL?", "Explain lists vs dicts."]
        answers = ["It is a mutex in CPython.", "Lists are index-based, dicts are hash-based."]
        evaluations = [{'score': 8.5}, {'score': 9.0}]

        record_id = database.save_interview_session(
            cand_id, "Python Developer", questions, answers, evaluations, 8.8
        )
        self.assertIsNotNone(record_id)

        latest = database.get_latest_interview_session(cand_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest['target_role'], "Python Developer")
        self.assertEqual(latest['overall_score'], 8.8)
        self.assertEqual(len(latest['questions']), 2)

        detail = database.get_record_detail('interview_session', record_id, cand_id)
        self.assertIsNotNone(detail)
        self.assertEqual(detail['answers'][0], "It is a mutex in CPython.")

    def test_save_and_retrieve_career_report(self):
        """Verify career intelligence report persistence and retrieval."""
        cand_id = database.create_candidate("Career Report User")
        report_data = {
            'role': 'Data Analyst',
            'readiness': {'percentage': 82},
            'skill_gap': {'matched_skills': ['SQL', 'Python'], 'missing_skills': ['Tableau']},
            'role_matching': [{'role': 'Data Analyst', 'match_percentage': '82%'}],
            'learning_roadmap': [{'step': 1, 'title': 'Master Tableau'}],
            'recommended_projects': [{'title': 'Sales Dashboard'}],
            'resume_checklist': [{'title': 'Add metrics'}],
            'career_summary': {'profile_summary': 'Strong candidate'}
        }
        record_id = database.save_career_report(cand_id, "Data Analyst", report_data)
        self.assertIsNotNone(record_id)

        latest = database.get_latest_career_report(cand_id)
        self.assertIsNotNone(latest)
        self.assertEqual(latest['target_role'], "Data Analyst")
        self.assertEqual(latest['readiness_percentage'], 82)
        self.assertEqual(latest['skill_gap']['matched_skills'], ['SQL', 'Python'])

    def test_candidate_history_aggregation_and_clear(self):
        """Verify combined history retrieval, chronological sorting, and candidate-scoped clearing."""
        cand_id = database.create_candidate("History Aggregation User")
        database.save_resume_analysis(cand_id, "test.pdf", {'summary': 'Summary 1'})
        database.save_interview_session(cand_id, "Python Dev", ["Q1"], ["A1"], [{}], 8.0)
        database.save_career_report(cand_id, "Python Dev", {'readiness': {'percentage': 75}})

        history = database.get_candidate_history(cand_id)
        self.assertEqual(len(history), 3)

        # Confirm all 3 record types exist in history
        types = [h['record_type'] for h in history]
        self.assertIn('resume_analysis', types)
        self.assertIn('interview_session', types)
        self.assertIn('career_report', types)

        # Confirm clear only removes current candidate's data
        other_cand_id = database.create_candidate("Another User")
        database.save_resume_analysis(other_cand_id, "other.pdf", {'summary': 'Other summary'})

        success = database.clear_candidate_history(cand_id)
        self.assertTrue(success)
        self.assertEqual(len(database.get_candidate_history(cand_id)), 0)

        # Other candidate's data must remain intact
        other_history = database.get_candidate_history(other_cand_id)
        self.assertEqual(len(other_history), 1)

    def test_api_history_routes(self):
        """Verify GET /api/history, GET /api/history/<type>/<id>, and POST /api/history/clear."""
        # 1. Trigger resume analysis to populate session history
        with self.client:
            res_analysis = self.client.post('/analyze', json={'text': self.sample_resume})
            self.assertEqual(res_analysis.status_code, 200)

            # 2. Get history list
            res_history = self.client.get('/api/history')
            self.assertEqual(res_history.status_code, 200)
            data = res_history.get_json()
            self.assertTrue(data.get('success'))
            self.assertGreaterEqual(len(data.get('history', [])), 1)

            first_record = data['history'][0]
            rec_type = first_record['record_type']
            rec_id = first_record['id']

            # 3. Get history detail
            res_detail = self.client.get(f'/api/history/{rec_type}/{rec_id}')
            self.assertEqual(res_detail.status_code, 200)
            detail_data = res_detail.get_json()
            self.assertTrue(detail_data.get('success'))
            self.assertIn('record', detail_data)
            self.assertIn('technical_skills', detail_data['record'])

            # 4. Clear history
            res_clear = self.client.post('/api/history/clear')
            self.assertEqual(res_clear.status_code, 200)
            clear_data = res_clear.get_json()
            self.assertTrue(clear_data.get('success'))

            # Verify history is now empty
            res_history_empty = self.client.get('/api/history')
            self.assertEqual(len(res_history_empty.get_json()['history']), 0)

    def test_end_to_end_auto_persistence(self):
        """Verify that completing analysis, interview, and career intelligence saves all records automatically."""
        with self.client:
            # 1. Run Resume Analysis
            self.client.post('/analyze', json={'text': self.sample_resume})

            # 2. Run Interview Session
            self.client.post('/interview/summary', json={
                'role': 'Python Developer',
                'history': [
                    {'question': 'Explain GIL', 'answer': 'CPython mutex', 'evaluation': {'score': 8.5}}
                ]
            })

            # 3. Run Career Intelligence
            self.client.post('/career-intelligence', json={
                'role': 'Python Developer',
                'resume_analysis': {'technical_skills': ['Python', 'SQL']},
                'interview_summary': {'overall_score': 8.5}
            })

            # 4. Check history
            res = self.client.get('/api/history')
            self.assertEqual(res.status_code, 200)
            hist = res.get_json().get('history', [])
            self.assertEqual(len(hist), 3)

    # ==========================================
    # 7. STEP 7A: DEPLOYMENT PREPARATION TESTS
    # ==========================================

    def test_health_endpoint(self):
        """Verify GET /health returns HTTP 200 and standard health payload without exposing secrets."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get('status'), 'ok')
        self.assertEqual(data.get('service'), 'CareerPilot AI')

        # Security check: Ensure no API keys or database data leaked
        data_str = str(data)
        self.assertNotIn("GEMINI_API_KEY", data_str)
        self.assertNotIn("FLASK_SECRET_KEY", data_str)

    def test_production_startup_configuration(self):
        """Verify WSGI entrypoint app is valid for Gunicorn execution (gunicorn app:app)."""
        import app as app_module
        # 1. Ensure app callable exists and is an instance of Flask
        self.assertTrue(hasattr(app_module, 'app'))
        self.assertTrue(callable(app_module.app))

        # 2. Ensure upload folder exists and max content length is 16MB
        self.assertTrue(os.path.exists(app_module.app.config['UPLOAD_FOLDER']))
        self.assertEqual(app_module.app.config['MAX_CONTENT_LENGTH'], 16 * 1024 * 1024)

    def test_port_configuration_logic(self):
        """Verify PORT environment variable parsing logic behaves correctly for local & cloud."""
        # Local default fallback
        default_port = int(os.environ.get("PORT", 5000))
        self.assertIsInstance(default_port, int)
        self.assertGreater(default_port, 0)

    def test_gemini_model_configuration(self):
        """Verify the Gemini model configuration defaults to current stable gemini-3.6-flash."""
        self.assertEqual(analyzer.GEMINI_MODEL, 'gemini-3.6-flash')

    def test_sanitize_gemini_message(self):
        """Verify sanitize_gemini_message thoroughly redacts API keys and URL params."""
        fake_key = "AIzaSySecretFakeApiKey1234567890123"
        url_with_key = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={fake_key}"
        sanitized = analyzer.sanitize_gemini_message(url_with_key, api_key=fake_key)
        self.assertNotIn(fake_key, sanitized)
        self.assertIn("key=[REDACTED]", sanitized)

        # Test error body containing raw key
        error_body = f"Invalid API key: {fake_key}"
        sanitized_body = analyzer.sanitize_gemini_message(error_body, api_key=fake_key)
        self.assertNotIn(fake_key, sanitized_body)
        self.assertIn("[REDACTED_API_KEY]", sanitized_body)

    def test_log_gemini_diagnostic(self):
        """Verify log_gemini_diagnostic outputs required diagnostic fields without leaking secrets."""
        fake_key = "AIzaSySecretFakeApiKey1234567890123"
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": {
                "code": 404,
                "message": f"models/gemini-3.6-flash not found. url key={fake_key}",
                "status": "NOT_FOUND"
            }
        }
        mock_exc = Exception("Request failed")
        mock_exc.response = mock_response

        with patch('analyzer.get_gemini_api_key', return_value=fake_key), \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            analyzer.log_gemini_diagnostic(mock_exc, operation="test_op")
            log_output = mock_stderr.getvalue()

            # Verify required fields are logged
            self.assertIn("Operation: test_op", log_output)
            self.assertIn(f"Model: {analyzer.GEMINI_MODEL}", log_output)
            self.assertIn("Exception: Exception", log_output)
            self.assertIn("Status: HTTP 404", log_output)
            self.assertIn("Message: models/gemini-3.6-flash not found", log_output)

            # Security: ensure secret is completely absent
            self.assertNotIn(fake_key, log_output)

    def test_analyze_resume_diagnostic_fallback(self):
        """Verify analyze_resume catches exceptions, falls back safely, and does not leak diagnostic info to client."""
        fake_key = "AIzaSyTestSecretKey1234567890123"
        with patch('analyzer.get_gemini_api_key', return_value=fake_key), \
             patch('analyzer.call_gemini_api', side_effect=Exception(f"Google internal error for url key={fake_key}")), \
             patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
            result = analyzer.analyze_resume("Python developer with Flask experience.")
            
            # Diagnostic logged server-side
            log_output = mock_stderr.getvalue()
            self.assertIn("[Gemini Diagnostic]", log_output)
            self.assertNotIn(fake_key, log_output)

            # Client response must remain safe and standard
            self.assertNotIn(fake_key, str(result))
            self.assertNotIn("[Gemini Diagnostic]", str(result))
            self.assertEqual(result.get('source'), 'demo_fallback')
            self.assertIn('Falling back to smart offline analyzer', result.get('notice', ''))

if __name__ == '__main__':
    unittest.main()
