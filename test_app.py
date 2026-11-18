import json
from app import app
import models

def test_full_application():
    print("Beginning comprehensive test suite for QuizMaster Pro...")
    client = app.test_client()

    # 1. Test Home page
    res = client.get('/')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    print("  [PASS] GET / (Landing page renders)")

    # 2. Test Login page
    res = client.get('/login')
    assert res.status_code == 200
    print("  [PASS] GET /login (Login page renders)")

    # 3. Test Demo Student Login
    res = client.get('/demo-login/user', follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard" in res.data or b"Quiz" in res.data
    print("  [PASS] GET /demo-login/user (Student session created & redirected to Dashboard)")

    # 4. Test Quiz Questions API
    res = client.get('/api/quiz/questions?limit=5')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['success'] is True
    assert len(data['questions']) == 5
    # Verify answers are NOT leaked to client
    for q in data['questions']:
        assert 'correct_option' not in q
        assert 'explanation' not in q
    print("  [PASS] GET /api/quiz/questions (5 questions returned, client-safe sanitization verified)")

    # 5. Test Quiz Submission Engine
    submit_payload = {
        'category_id': 1,
        'category_name': 'Computer Science & Code',
        'difficulty': 'Medium',
        'answers': [
            {'question_id': data['questions'][0]['id'], 'selected_option': 'B', 'time_spent': 10},
            {'question_id': data['questions'][1]['id'], 'selected_option': 'A', 'time_spent': 8},
            {'question_id': data['questions'][2]['id'], 'selected_option': 'C', 'time_spent': 12},
            {'question_id': data['questions'][3]['id'], 'selected_option': 'D', 'time_spent': 15},
            {'question_id': data['questions'][4]['id'], 'selected_option': 'B', 'time_spent': 9}
        ],
        'time_taken_seconds': 54
    }

    res = client.post('/api/quiz/submit', json=submit_payload)
    assert res.status_code == 200
    sub_data = json.loads(res.data)
    assert sub_data['success'] is True
    attempt_id = sub_data['attempt_id']
    print(f"  [PASS] POST /api/quiz/submit (Assessment calculated, attempt #{attempt_id} created)")

    # 6. Test Result Review Page
    res = client.get(f'/quiz/result/{attempt_id}')
    assert res.status_code == 200
    assert b"Score" in res.data or b"Grade" in res.data
    print("  [PASS] GET /quiz/result/<id> (Scorecard & question review rendered)")

    # 7. Test Performance Analytics
    res = client.get('/api/analytics')
    assert res.status_code == 200
    adata = json.loads(res.data)
    assert adata['success'] is True
    assert 'weak_categories' in adata['data']
    print(f"  [PASS] GET /api/analytics (Found {len(adata['data']['weak_categories'])} category diagnostics)")

    # 8. Test Leaderboard
    res = client.get('/leaderboard')
    assert res.status_code == 200
    print("  [PASS] GET /leaderboard (Rankings page renders)")

    # 9. Test History
    res = client.get('/history')
    assert res.status_code == 200
    print("  [PASS] GET /history (Past attempts history renders)")

    # 10. Test Admin Login & Admin Dashboard Access
    res = client.get('/demo-login/admin', follow_redirects=True)
    assert res.status_code == 200
    res = client.get('/admin')
    assert res.status_code == 200
    assert b"Operations" in res.data or b"System" in res.data
    print("  [PASS] GET /admin (Admin protected route accessed successfully)")

    # 11. Test Admin Question Management
    res = client.get('/admin/questions')
    assert res.status_code == 200
    print("  [PASS] GET /admin/questions (Admin questions CRUD view renders)")

    # 12. Test Admin User Management
    res = client.get('/admin/users')
    assert res.status_code == 200
    print("  [PASS] GET /admin/users (Admin users view renders)")

    print("\n" + "=" * 50)
    print("🎉 ALL 12 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == '__main__':
    test_full_application()
