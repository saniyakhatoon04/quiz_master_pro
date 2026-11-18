import os
import json
from datetime import datetime, date
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import models

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()

# Ensure database is initialized
models.init_db()

# ----------------- Authentication Decorators -----------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access restricted to administrators only.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    current_user = None
    if 'user_id' in session:
        current_user = models.get_user_by_id(session['user_id'])
    return dict(current_user=current_user)

# ----------------- Public Routes -----------------

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    categories = models.get_categories()
    leaderboard = models.get_leaderboard(limit=5)
    return render_template('index.html', categories=categories, leaderboard=leaderboard)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        user = models.authenticate_user(username_or_email, password)

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome back, {user['full_name']}!", 'success')

            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('admin_dashboard' if user['role'] == 'admin' else 'dashboard'))
        else:
            flash('Invalid username/email or password.', 'danger')

    return render_template('login.html')

@app.route('/demo-login/<role>')
def demo_login(role):
    """Convenient 1-click login for testing demo profiles."""
    if role == 'admin':
        user = models.authenticate_user('admin', 'admin123')
    else:
        user = models.authenticate_user('student1', 'quiz123')

    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        flash(f"Logged in as demo {role.capitalize()}: {user['full_name']}", 'success')
        return redirect(url_for('admin_dashboard' if user['role'] == 'admin' else 'dashboard'))
    else:
        flash('Demo account could not be found. Please check database seeder.', 'danger')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        full_name = request.form.get('full_name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        avatar = request.form.get('avatar', 'avatar1.png')

        if not username or not email or not full_name or not password:
            flash('All fields are required.', 'warning')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'warning')
            return render_template('register.html')

        user = models.create_user(username, email, password, full_name, role='user', avatar=avatar)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            flash('Registration successful! Welcome to QuizMaster Pro.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username or email already exists. Please pick another one.', 'danger')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ----------------- Dashboard & User Arena -----------------

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = models.get_user_by_id(user_id)
    categories = models.get_categories()
    recent_attempts = models.get_user_attempts(user_id, limit=6)
    weak_categories = models.get_weak_categories(user_id)
    streak_calendar = models.get_streak_calendar(user_id, days=7)
    leaderboard_preview = models.get_leaderboard(limit=5)

    # Calculate average accuracy
    total_quizzes = user['quizzes_taken'] or 0
    avg_accuracy = 0
    if recent_attempts:
        avg_accuracy = round(sum(att['percentage'] for att in recent_attempts) / len(recent_attempts), 1)

    # Identify primary weak subject
    primary_weak_subject = None
    for wc in weak_categories:
        if wc['status'] == 'Weak':
            primary_weak_subject = wc
            break

    return render_template(
        'dashboard.html',
        user=user,
        categories=categories,
        recent_attempts=recent_attempts,
        weak_categories=weak_categories,
        primary_weak_subject=primary_weak_subject,
        streak_calendar=streak_calendar,
        leaderboard_preview=leaderboard_preview,
        avg_accuracy=avg_accuracy,
        total_quizzes=total_quizzes
    )

# ----------------- Interactive Quiz Engine -----------------

@app.route('/quiz')
@login_required
def quiz():
    category_id = request.args.get('category', 'all')
    difficulty = request.args.get('difficulty', 'all')
    mode = request.args.get('mode', 'standard')
    limit = int(request.args.get('limit', 10))

    cat_name = "All Categories"
    if category_id and category_id != 'all':
        cat = models.get_category_by_id(category_id)
        if cat:
            cat_name = cat['name']

    return render_template(
        'quiz.html',
        category_id=category_id,
        category_name=cat_name,
        difficulty=difficulty,
        mode=mode,
        limit=limit
    )

@app.route('/quiz/weak-recovery')
@login_required
def quiz_weak_recovery():
    """Generates targeted practice quiz for weakest categories."""
    return render_template(
        'quiz.html',
        category_id='weak',
        category_name='Weak Subject Recovery',
        difficulty='all',
        mode='weak_recovery',
        limit=10
    )

@app.route('/api/quiz/questions')
@login_required
def api_quiz_questions():
    category_id = request.args.get('category', 'all')
    difficulty = request.args.get('difficulty', 'all')
    mode = request.args.get('mode', 'standard')
    limit = int(request.args.get('limit', 10))

    if mode == 'weak_recovery' or category_id == 'weak':
        questions = models.get_weak_subject_questions(session['user_id'], limit=limit)
    else:
        questions = models.get_questions_for_quiz(category_id=category_id, difficulty=difficulty, limit=limit)

    # Secure: omit correct_option and explanation from client payload to prevent cheating
    sanitized = []
    for q in questions:
        sanitized.append({
            'id': q['id'],
            'category_name': q['category_name'],
            'difficulty': q['difficulty'],
            'question_text': q['question_text'],
            'code_snippet': q['code_snippet'],
            'option_a': q['option_a'],
            'option_b': q['option_b'],
            'option_c': q['option_c'],
            'option_d': q['option_d'],
            'points': q['points'],
            'time_limit_seconds': q['time_limit_seconds']
        })

    return jsonify({'success': True, 'questions': sanitized, 'count': len(sanitized)})

@app.route('/api/quiz/submit', methods=['POST'])
@login_required
def api_quiz_submit():
    data = request.get_json() or {}
    category_id = data.get('category_id')
    category_name = data.get('category_name', 'General')
    difficulty = data.get('difficulty', 'Mixed')
    user_answers = data.get('answers', [])
    time_taken_seconds = int(data.get('time_taken_seconds', 0))

    if not user_answers:
        return jsonify({'success': False, 'message': 'No answers submitted'}), 400

    result = models.submit_quiz_attempt(
        user_id=session['user_id'],
        category_id=category_id,
        category_name=category_name,
        difficulty=difficulty,
        user_answers=user_answers,
        time_taken_seconds=time_taken_seconds
    )

    return jsonify({
        'success': True,
        'attempt_id': result['attempt_id'],
        'redirect_url': url_for('quiz_result', attempt_id=result['attempt_id'])
    })

@app.route('/quiz/result/<int:attempt_id>')
@login_required
def quiz_result(attempt_id):
    attempt = models.get_quiz_attempt(attempt_id)
    if not attempt or (attempt['user_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash('Quiz attempt record not found or access denied.', 'warning')
        return redirect(url_for('dashboard'))

    # Calculate grade letter
    pct = attempt['percentage']
    if pct >= 90:
        grade = 'S'
        badge_color = 'purple'
    elif pct >= 80:
        grade = 'A'
        badge_color = 'emerald'
    elif pct >= 70:
        grade = 'B'
        badge_color = 'blue'
    elif pct >= 60:
        grade = 'C'
        badge_color = 'amber'
    elif pct >= 50:
        grade = 'D'
        badge_color = 'orange'
    else:
        grade = 'F'
        badge_color = 'rose'

    user = models.get_user_by_id(session['user_id'])
    weak_categories = models.get_weak_categories(session['user_id'])

    return render_template(
        'result.html',
        attempt=attempt,
        grade=grade,
        badge_color=badge_color,
        user=user,
        weak_categories=weak_categories
    )

# ----------------- History & Analytics -----------------

@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    attempts = models.get_user_attempts(user_id, limit=100)
    categories = models.get_categories()
    return render_template('history.html', attempts=attempts, categories=categories)

@app.route('/analytics')
@login_required
def analytics():
    user_id = session['user_id']
    perf_data = models.get_user_performance_analytics(user_id)
    return render_template('analytics.html', data=perf_data)

@app.route('/api/analytics')
@login_required
def api_analytics():
    user_id = session['user_id']
    perf_data = models.get_user_performance_analytics(user_id)
    return jsonify({'success': True, 'data': perf_data})

# ----------------- Leaderboard -----------------

@app.route('/leaderboard')
def leaderboard():
    category_id = request.args.get('category', 'all')
    categories = models.get_categories()
    rankings = models.get_leaderboard(category_id=category_id, limit=25)

    # Find current user rank if logged in
    current_user_rank = None
    if 'user_id' in session:
        for idx, r in enumerate(rankings, 1):
            if r['id'] == session['user_id']:
                current_user_rank = r
                break

    return render_template(
        'leaderboard.html',
        categories=categories,
        rankings=rankings,
        selected_category=category_id,
        current_user_rank=current_user_rank
    )

# ----------------- Admin Management Portal -----------------

@app.route('/admin')
@admin_required
def admin_dashboard():
    stats = models.get_admin_dashboard_stats()
    recent_users = models.get_all_users()[:8]
    categories = models.get_categories()
    return render_template('admin_dashboard.html', stats=stats, recent_users=recent_users, categories=categories)

@app.route('/admin/questions')
@admin_required
def admin_questions():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category')
    difficulty = request.args.get('difficulty')
    questions = models.get_all_questions(search=search, category_id=category_id, difficulty=difficulty)
    categories = models.get_categories()
    return render_template('admin_questions.html', questions=questions, categories=categories, search=search, selected_category=category_id, selected_difficulty=difficulty)

@app.route('/api/admin/questions/add', methods=['POST'])
@admin_required
def api_admin_add_question():
    try:
        data = request.form
        category_id = int(data.get('category_id'))
        difficulty = data.get('difficulty')
        question_text = data.get('question_text', '').strip()
        code_snippet = data.get('code_snippet', '').strip() or None
        option_a = data.get('option_a', '').strip()
        option_b = data.get('option_b', '').strip()
        option_c = data.get('option_c', '').strip()
        option_d = data.get('option_d', '').strip()
        correct_option = data.get('correct_option', '').strip().upper()
        explanation = data.get('explanation', '').strip()
        points = int(data.get('points', 10))
        time_limit_seconds = int(data.get('time_limit_seconds', 30))

        if not question_text or not option_a or not option_b or not correct_option:
            flash('Please fill in all required question fields.', 'warning')
            return redirect(url_for('admin_questions'))

        qid = models.add_question(
            category_id, difficulty, question_text, code_snippet,
            option_a, option_b, option_c, option_d, correct_option,
            explanation, points, time_limit_seconds
        )
        flash('Question added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding question: {str(e)}', 'danger')

    return redirect(url_for('admin_questions'))

@app.route('/api/admin/questions/<int:qid>/edit', methods=['POST'])
@admin_required
def api_admin_edit_question(qid):
    try:
        data = request.form
        category_id = int(data.get('category_id'))
        difficulty = data.get('difficulty')
        question_text = data.get('question_text', '').strip()
        code_snippet = data.get('code_snippet', '').strip() or None
        option_a = data.get('option_a', '').strip()
        option_b = data.get('option_b', '').strip()
        option_c = data.get('option_c', '').strip()
        option_d = data.get('option_d', '').strip()
        correct_option = data.get('correct_option', '').strip().upper()
        explanation = data.get('explanation', '').strip()
        points = int(data.get('points', 10))
        time_limit_seconds = int(data.get('time_limit_seconds', 30))

        models.update_question(
            qid, category_id, difficulty, question_text, code_snippet,
            option_a, option_b, option_c, option_d, correct_option,
            explanation, points, time_limit_seconds
        )
        flash('Question updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating question: {str(e)}', 'danger')

    return redirect(url_for('admin_questions'))

@app.route('/api/admin/questions/<int:qid>/delete', methods=['POST'])
@admin_required
def api_admin_delete_question(qid):
    models.delete_question(qid)
    flash('Question deleted successfully.', 'info')
    return redirect(url_for('admin_questions'))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = models.get_all_users()
    return render_template('admin_users.html', users=users)

@app.route('/api/admin/users/<int:uid>/role', methods=['POST'])
@admin_required
def api_admin_change_user_role(uid):
    new_role = request.form.get('role', 'user')
    models.update_user_role(uid, new_role)
    flash(f'User role updated to {new_role}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/api/admin/users/<int:uid>/reset', methods=['POST'])
@admin_required
def api_admin_reset_user(uid):
    models.reset_user_stats(uid)
    flash('User statistics have been reset.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/api/admin/users/<int:uid>/delete', methods=['POST'])
@admin_required
def api_admin_delete_user(uid):
    if uid == session['user_id']:
        flash('You cannot delete your own active administrator account.', 'danger')
    else:
        models.delete_user(uid)
        flash('User account deleted successfully.', 'info')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 QuizMaster Pro is starting at http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
