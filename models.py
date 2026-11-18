import sqlite3
import json
import os
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quiz_app.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            avatar TEXT DEFAULT 'avatar1.png',
            role TEXT DEFAULT 'user', -- 'user' or 'admin'
            total_score INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0,
            quizzes_taken INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_quiz_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Categories Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT DEFAULT 'folder',
            color TEXT DEFAULT 'indigo'
        )
    ''')

    # Questions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            difficulty TEXT NOT NULL, -- 'Easy', 'Medium', 'Hard'
            question_text TEXT NOT NULL,
            code_snippet TEXT,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL, -- 'A', 'B', 'C', 'D'
            explanation TEXT,
            points INTEGER DEFAULT 10,
            time_limit_seconds INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    ''')

    # Quiz Attempts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER,
            category_name TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            score INTEGER NOT NULL,
            total_questions INTEGER NOT NULL,
            percentage REAL NOT NULL,
            xp_earned INTEGER DEFAULT 0,
            time_taken_seconds INTEGER NOT NULL,
            passed INTEGER DEFAULT 0, -- 1 for True, 0 for False (threshold 60%)
            detailed_results TEXT NOT NULL, -- JSON string of questions, user answers, correct answers
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Streak Activity Log (tracks every day a user played a quiz)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS streak_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_date TEXT NOT NULL, -- YYYY-MM-DD
            attempts_count INTEGER DEFAULT 1,
            UNIQUE(user_id, activity_date),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

# ----------------- User Authentication & Management -----------------

def create_user(username, email, password, full_name, role='user', avatar='avatar1.png'):
    conn = get_db()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, role, avatar)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username.strip(), email.strip().lower(), password_hash, full_name.strip(), role, avatar))
        conn.commit()
        user_id = cursor.lastrowid
        return get_user_by_id(user_id)
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def authenticate_user(username_or_email, password):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM users 
        WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)
    ''', (username_or_email.strip(), username_or_email.strip()))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None

def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, email, full_name, role, avatar, total_score, xp, 
               quizzes_taken, current_streak, longest_streak, last_quiz_date, created_at 
        FROM users ORDER BY created_at DESC
    ''')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

def update_user_role(user_id, new_role):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def reset_user_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET total_score = 0, xp = 0, quizzes_taken = 0, 
            current_streak = 0, longest_streak = 0, last_quiz_date = NULL 
        WHERE id = ?
    ''', (user_id,))
    cursor.execute('DELETE FROM quiz_attempts WHERE user_id = ?', (user_id,))
    cursor.execute('DELETE FROM streak_logs WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ----------------- Streak Calculation Logic -----------------

def update_user_streak(user_id):
    """
    Computes daily quiz streak accurately:
    - If user took a quiz today already, streak remains active.
    - If user's last quiz was yesterday, current_streak increments by 1.
    - If user's last quiz was older than yesterday, streak resets to 1.
    - Updates longest_streak if current_streak exceeds it.
    """
    conn = get_db()
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()

    # Log daily activity
    cursor.execute('''
        INSERT INTO streak_logs (user_id, activity_date, attempts_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, activity_date) 
        DO UPDATE SET attempts_count = attempts_count + 1
    ''', (user_id, today_str))

    cursor.execute('SELECT current_streak, longest_streak, last_quiz_date FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return 0, 0

    current_streak = user['current_streak'] or 0
    longest_streak = user['longest_streak'] or 0
    last_quiz_date = user['last_quiz_date']

    if last_quiz_date == today_str:
        # Already played today, maintain streak
        streak_updated = current_streak
    elif last_quiz_date == yesterday_str:
        # Played yesterday, increment streak
        streak_updated = current_streak + 1
    else:
        # Played earlier than yesterday or first time, restart streak at 1
        streak_updated = 1

    longest_streak = max(longest_streak, streak_updated)

    cursor.execute('''
        UPDATE users 
        SET current_streak = ?, longest_streak = ?, last_quiz_date = ? 
        WHERE id = ?
    ''', (streak_updated, longest_streak, today_str, user_id))

    conn.commit()
    conn.close()
    return streak_updated, longest_streak

def get_streak_calendar(user_id, days=7):
    """Returns the last N days with whether the user completed a quiz on that day."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT activity_date, attempts_count FROM streak_logs 
        WHERE user_id = ? ORDER BY activity_date DESC LIMIT 30
    ''', (user_id,))
    logged_dates = {row['activity_date']: row['attempts_count'] for row in cursor.fetchall()}
    conn.close()

    result = []
    today = date.today()
    for i in range(days - 1, -1, -1):
        day_date = today - timedelta(days=i)
        date_str = day_date.isoformat()
        result.append({
            'date': date_str,
            'day_name': day_date.strftime('%a'),
            'day_num': day_date.strftime('%d'),
            'completed': date_str in logged_dates,
            'attempts': logged_dates.get(date_str, 0),
            'is_today': date_str == today.isoformat()
        })
    return result

# ----------------- Category & Question Operations -----------------

def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.*, COUNT(q.id) as question_count 
        FROM categories c 
        LEFT JOIN questions q ON c.id = q.category_id 
        GROUP BY c.id ORDER BY c.name ASC
    ''')
    cats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cats

def get_category_by_id(cat_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories WHERE id = ?', (cat_id,))
    cat = cursor.fetchone()
    conn.close()
    return dict(cat) if cat else None

def add_category(name, slug, description, icon='folder', color='indigo'):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO categories (name, slug, description, icon, color)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, slug, description, icon, color))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_questions_for_quiz(category_id=None, difficulty=None, limit=10):
    """Fetches random questions filtered by category and/or difficulty."""
    conn = get_db()
    cursor = conn.cursor()
    query = '''
        SELECT q.*, c.name as category_name 
        FROM questions q 
        JOIN categories c ON q.category_id = c.id 
        WHERE 1=1
    '''
    params = []
    if category_id and category_id != 'all':
        query += ' AND q.category_id = ?'
        params.append(category_id)
    if difficulty and difficulty != 'all':
        query += ' AND LOWER(q.difficulty) = LOWER(?)'
        params.append(difficulty)

    query += ' ORDER BY RANDOM() LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questions

def get_weak_subject_questions(user_id, limit=10):
    """Generates a targeted quiz targeting user's weakest categories based on previous accuracy."""
    weak_cats = get_weak_categories(user_id)
    conn = get_db()
    cursor = conn.cursor()

    if weak_cats:
        # Collect questions from weak categories
        cat_ids = [wc['category_id'] for wc in weak_cats if wc['accuracy'] < 70]
        if not cat_ids:
            cat_ids = [weak_cats[0]['category_id']] # pick lowest

        placeholders = ','.join(['?'] * len(cat_ids))
        cursor.execute(f'''
            SELECT q.*, c.name as category_name 
            FROM questions q 
            JOIN categories c ON q.category_id = c.id 
            WHERE q.category_id IN ({placeholders})
            ORDER BY RANDOM() LIMIT ?
        ''', (*cat_ids, limit))
        questions = [dict(row) for row in cursor.fetchall()]
    else:
        # Fallback to random questions if not enough history
        cursor.execute('''
            SELECT q.*, c.name as category_name 
            FROM questions q 
            JOIN categories c ON q.category_id = c.id 
            ORDER BY RANDOM() LIMIT ?
        ''', (limit,))
        questions = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return questions

def get_all_questions(search='', category_id=None, difficulty=None):
    conn = get_db()
    cursor = conn.cursor()
    query = '''
        SELECT q.*, c.name as category_name 
        FROM questions q 
        JOIN categories c ON q.category_id = c.id 
        WHERE 1=1
    '''
    params = []
    if search:
        query += ' AND (q.question_text LIKE ? OR q.explanation LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    if category_id:
        query += ' AND q.category_id = ?'
        params.append(category_id)
    if difficulty:
        query += ' AND LOWER(q.difficulty) = LOWER(?)'
        params.append(difficulty)

    query += ' ORDER BY q.id DESC'
    cursor.execute(query, params)
    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return questions

def get_question_by_id(question_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT q.*, c.name as category_name 
        FROM questions q 
        JOIN categories c ON q.category_id = c.id 
        WHERE q.id = ?
    ''', (question_id,))
    q = cursor.fetchone()
    conn.close()
    return dict(q) if q else None

def add_question(category_id, difficulty, question_text, code_snippet,
                 option_a, option_b, option_c, option_d, correct_option,
                 explanation, points=10, time_limit_seconds=30):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO questions 
        (category_id, difficulty, question_text, code_snippet, option_a, option_b, option_c, option_d, correct_option, explanation, points, time_limit_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (category_id, difficulty, question_text, code_snippet, option_a, option_b, option_c, option_d, correct_option.upper(), explanation, points, time_limit_seconds))
    conn.commit()
    qid = cursor.lastrowid
    conn.close()
    return qid

def update_question(question_id, category_id, difficulty, question_text, code_snippet,
                    option_a, option_b, option_c, option_d, correct_option,
                    explanation, points, time_limit_seconds):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE questions 
        SET category_id = ?, difficulty = ?, question_text = ?, code_snippet = ?,
            option_a = ?, option_b = ?, option_c = ?, option_d = ?, correct_option = ?,
            explanation = ?, points = ?, time_limit_seconds = ?
        WHERE id = ?
    ''', (category_id, difficulty, question_text, code_snippet, option_a, option_b, option_c, option_d, correct_option.upper(), explanation, points, time_limit_seconds, question_id))
    conn.commit()
    conn.close()

def delete_question(question_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
    conn.commit()
    conn.close()

# ----------------- Quiz Submission & Scoring Engine -----------------

def submit_quiz_attempt(user_id, category_id, category_name, difficulty, user_answers, time_taken_seconds):
    """
    Evaluates quiz submissions automatically:
    - Calculates score, percentage, earned points/XP with difficulty multiplier.
    - Generates detailed explanation report for correct vs wrong answers.
    - Updates user profile: total_score, xp, quizzes_taken, daily streak.
    - Stores attempt in database.
    """
    conn = get_db()
    cursor = conn.cursor()

    total_questions = len(user_answers)
    correct_count = 0
    total_points_earned = 0
    detailed_results = []

    # Difficulty multiplier
    multiplier = {'Easy': 1, 'Medium': 1.5, 'Hard': 2}.get(difficulty, 1)

    for item in user_answers:
        qid = item.get('question_id')
        chosen_option = (item.get('selected_option') or '').upper().strip()
        time_spent_q = item.get('time_spent', 0)

        cursor.execute('''
            SELECT q.*, c.name as cat_name 
            FROM questions q 
            JOIN categories c ON q.category_id = c.id 
            WHERE q.id = ?
        ''', (qid,))
        q = cursor.fetchone()

        if q:
            is_correct = (chosen_option == q['correct_option'])
            base_points = q['points'] or 10

            if is_correct:
                correct_count += 1
                # Fast answer bonus if answered in < 50% of time limit
                time_bonus = 5 if (time_spent_q > 0 and time_spent_q <= (q['time_limit_seconds'] / 2)) else 0
                q_points = int(base_points * multiplier) + time_bonus
                total_points_earned += q_points
            else:
                q_points = 0

            detailed_results.append({
                'question_id': q['id'],
                'question_text': q['question_text'],
                'code_snippet': q['code_snippet'],
                'category_name': q['cat_name'],
                'difficulty': q['difficulty'],
                'option_a': q['option_a'],
                'option_b': q['option_b'],
                'option_c': q['option_c'],
                'option_d': q['option_d'],
                'correct_option': q['correct_option'],
                'user_selected': chosen_option,
                'is_correct': is_correct,
                'points_awarded': q_points,
                'explanation': q['explanation'],
                'time_spent': time_spent_q
            })

    percentage = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0
    passed = 1 if percentage >= 60.0 else 0

    # Insert into quiz_attempts
    cursor.execute('''
        INSERT INTO quiz_attempts 
        (user_id, category_id, category_name, difficulty, score, total_questions, percentage, xp_earned, time_taken_seconds, passed, detailed_results)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        category_id if category_id and category_id != 'all' else None,
        category_name,
        difficulty,
        correct_count,
        total_questions,
        percentage,
        total_points_earned,
        time_taken_seconds,
        passed,
        json.dumps(detailed_results)
    ))
    attempt_id = cursor.lastrowid

    # Update user summary stats
    cursor.execute('''
        UPDATE users 
        SET total_score = total_score + ?,
            xp = xp + ?,
            quizzes_taken = quizzes_taken + 1
        WHERE id = ?
    ''', (correct_count, total_points_earned, user_id))

    conn.commit()
    conn.close()

    # Update streak
    current_streak, longest_streak = update_user_streak(user_id)

    return {
        'attempt_id': attempt_id,
        'score': correct_count,
        'total_questions': total_questions,
        'percentage': percentage,
        'xp_earned': total_points_earned,
        'time_taken_seconds': time_taken_seconds,
        'passed': bool(passed),
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'detailed_results': detailed_results
    }

def get_quiz_attempt(attempt_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM quiz_attempts WHERE id = ?', (attempt_id,))
    attempt = cursor.fetchone()
    conn.close()
    if attempt:
        d = dict(attempt)
        try:
            d['detailed_results'] = json.loads(d['detailed_results'])
        except Exception:
            d['detailed_results'] = []
        return d
    return None

def get_user_attempts(user_id, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM quiz_attempts 
        WHERE user_id = ? 
        ORDER BY created_at DESC LIMIT ?
    ''', (user_id, limit))
    attempts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    for att in attempts:
        try:
            att['detailed_results'] = json.loads(att['detailed_results'])
        except Exception:
            att['detailed_results'] = []
    return attempts

# ----------------- Weak Subjects & Analytics Engine -----------------

def get_weak_categories(user_id):
    """
    Computes accuracy percentage per category for the given user.
    Flags categories as:
    - 'Weak' (accuracy < 60%)
    - 'Average' (60% <= accuracy < 80%)
    - 'Mastered' (accuracy >= 80%)
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT detailed_results FROM quiz_attempts WHERE user_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    cat_stats = {} # cat_name: {'correct': 0, 'total': 0, 'category_id': id}

    for row in rows:
        try:
            results = json.loads(row['detailed_results'])
            for q in results:
                cat_name = q.get('category_name', 'General')
                if cat_name not in cat_stats:
                    cat_stats[cat_name] = {'correct': 0, 'total': 0, 'category_id': None}
                cat_stats[cat_name]['total'] += 1
                if q.get('is_correct'):
                    cat_stats[cat_name]['correct'] += 1
        except Exception:
            continue

    # Enrich with category IDs from DB
    cats = get_categories()
    cat_map = {c['name']: c['id'] for c in cats}

    output = []
    for cat_name, stats in cat_stats.items():
        total = stats['total']
        correct = stats['correct']
        accuracy = round((correct / total * 100), 1) if total > 0 else 0
        status = 'Weak' if accuracy < 60 else ('Average' if accuracy < 80 else 'Mastered')
        color = 'red' if status == 'Weak' else ('amber' if status == 'Average' else 'emerald')
        output.append({
            'category_name': cat_name,
            'category_id': cat_map.get(cat_name),
            'correct': correct,
            'total': total,
            'accuracy': accuracy,
            'status': status,
            'color': color
        })

    # Sort ascending by accuracy so weakest is first
    output.sort(key=lambda x: (x['accuracy'], -x['total']))
    return output

def get_user_performance_analytics(user_id):
    """Aggregates all performance metrics for visualization and reporting."""
    user = get_user_by_id(user_id)
    if not user:
        return None

    conn = get_db()
    cursor = conn.cursor()

    # Attempts over time (recent 15)
    cursor.execute('''
        SELECT id, category_name, difficulty, percentage, score, total_questions, xp_earned, time_taken_seconds, created_at 
        FROM quiz_attempts 
        WHERE user_id = ? 
        ORDER BY created_at ASC LIMIT 20
    ''', (user_id,))
    history_trend = [dict(row) for row in cursor.fetchall()]

    # Difficulty performance
    cursor.execute('''
        SELECT difficulty, 
               COUNT(*) as count, 
               AVG(percentage) as avg_percentage,
               SUM(score) as total_correct,
               SUM(total_questions) as total_qs
        FROM quiz_attempts 
        WHERE user_id = ? 
        GROUP BY difficulty
    ''', (user_id,))
    difficulty_stats = [dict(row) for row in cursor.fetchall()]

    # Overall platform stats
    cursor.execute('''
        SELECT COUNT(*) as total_attempts, 
               AVG(percentage) as avg_score,
               SUM(time_taken_seconds) as total_time
        FROM quiz_attempts WHERE user_id = ?
    ''', (user_id,))
    overall = cursor.fetchone()
    conn.close()

    weak_categories = get_weak_categories(user_id)
    streak_calendar = get_streak_calendar(user_id, days=7)

    # Calculate Grade
    avg_score = round(overall['avg_score'] or 0, 1)
    if avg_score >= 90:
        grade = 'S'
    elif avg_score >= 80:
        grade = 'A'
    elif avg_score >= 70:
        grade = 'B'
    elif avg_score >= 60:
        grade = 'C'
    elif avg_score >= 50:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'user': user,
        'total_quizzes': overall['total_attempts'] or 0,
        'avg_score': avg_score,
        'grade': grade,
        'total_time_seconds': overall['total_time'] or 0,
        'history_trend': history_trend,
        'difficulty_stats': difficulty_stats,
        'weak_categories': weak_categories,
        'streak_calendar': streak_calendar
    }

# ----------------- Leaderboard Engine -----------------

def get_leaderboard(category_id=None, timeframe='all', limit=20):
    """
    Fetches leaderboard rankings.
    Rankings calculated by total XP and accuracy.
    Supports filtering by category.
    """
    conn = get_db()
    cursor = conn.cursor()

    if category_id and category_id != 'all':
        # Rank by score in this specific category
        cursor.execute('''
            SELECT u.id, u.username, u.full_name, u.avatar, u.current_streak,
                   COUNT(a.id) as quizzes_taken,
                   SUM(a.xp_earned) as total_xp,
                   AVG(a.percentage) as avg_accuracy,
                   SUM(a.score) as total_correct
            FROM users u
            JOIN quiz_attempts a ON u.id = a.user_id
            WHERE a.category_id = ?
            GROUP BY u.id
            ORDER BY total_xp DESC, avg_accuracy DESC
            LIMIT ?
        ''', (category_id, limit))
    else:
        # Global leaderboard
        cursor.execute('''
            SELECT id, username, full_name, avatar, xp as total_xp, total_score as total_correct,
                   quizzes_taken, current_streak, longest_streak
            FROM users 
            WHERE quizzes_taken > 0
            ORDER BY xp DESC, total_score DESC
            LIMIT ?
        ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    leaderboard = []
    for rank, row in enumerate(rows, 1):
        item = dict(row)
        item['rank'] = rank
        # Calculate accuracy
        if 'avg_accuracy' not in item or item['avg_accuracy'] is None:
            # compute from quizzes
            pass
        leaderboard.append(item)

    return leaderboard

# ----------------- Admin Statistics -----------------

def get_admin_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM questions')
    total_questions = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM quiz_attempts')
    total_quizzes = cursor.fetchone()[0]

    cursor.execute('SELECT AVG(percentage) FROM quiz_attempts')
    avg_platform_score = round(cursor.fetchone()[0] or 0, 1)

    cursor.execute('''
        SELECT category_name, COUNT(*) as count 
        FROM quiz_attempts 
        GROUP BY category_name 
        ORDER BY count DESC LIMIT 1
    ''')
    top_cat = cursor.fetchone()
    most_popular_category = top_cat['category_name'] if top_cat else 'None'

    cursor.execute('''
        SELECT c.name, COUNT(q.id) as question_count 
        FROM categories c 
        LEFT JOIN questions q ON c.id = q.category_id 
        GROUP BY c.id
    ''')
    questions_by_category = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        'total_users': total_users,
        'total_questions': total_questions,
        'total_quizzes': total_quizzes,
        'avg_platform_score': avg_platform_score,
        'most_popular_category': most_popular_category,
        'questions_by_category': questions_by_category
    }
