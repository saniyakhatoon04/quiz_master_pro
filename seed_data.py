import sqlite3
import json
import random
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
from models import get_db, init_db

def seed_database():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # 1. Seed Categories
    categories = [
        ('Computer Science & Code', 'cs', 'Algorithms, Web Development, Python, and System Design', 'laptop-code', 'indigo'),
        ('Science & Physics', 'science', 'Astronomy, Quantum Physics, Chemistry, and Biology', 'atom', 'emerald'),
        ('Mathematics & Logic', 'math', 'Algebra, Probability, Number Theory, and Critical Puzzles', 'calculator', 'violet'),
        ('World History & Geography', 'history', 'Ancient Civilizations, Global Landmarks, and Historical Milestones', 'landmark', 'amber'),
        ('Pop Culture & Trivia', 'trivia', 'Cinematic Legends, Gaming Milestones, and Modern Culture', 'film', 'rose'),
        ('Business & Finance', 'finance', 'Stock Markets, Macroeconomics, Venture Capital, and FinTech', 'chart-line', 'blue'),
    ]

    for name, slug, desc, icon, color in categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, description, icon, color)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, slug, desc, icon, color))
    conn.commit()

    # Fetch Category ID mappings
    cursor.execute('SELECT id, slug FROM categories')
    cat_map = {row['slug']: row['id'] for row in cursor.fetchall()}

    # 2. Seed Default Demo Users
    demo_users = [
        ('admin', 'admin@quizmaster.com', 'admin123', 'Administrator Pro', 'admin', 'avatar_admin.png'),
        ('student1', 'alex.turner@school.edu', 'quiz123', 'Alex Turner', 'user', 'avatar1.png'),
        ('sarah_dev', 'sarah.connor@cyber.net', 'quiz123', 'Sarah Connor', 'user', 'avatar2.png'),
        ('marcus_math', 'marcus.aurelius@stoic.org', 'quiz123', 'Marcus Aurelius', 'user', 'avatar3.png'),
        ('elena_science', 'elena.rostova@lab.gov', 'quiz123', 'Elena Rostova', 'user', 'avatar4.png'),
        ('david_finance', 'david.g@hedgefund.io', 'quiz123', 'David Geller', 'user', 'avatar5.png'),
    ]

    for username, email, pwd, full_name, role, avatar in demo_users:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, avatar, total_score, xp, quizzes_taken, current_streak, longest_streak, last_quiz_date)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0, NULL)
            ''', (username, email, generate_password_hash(pwd), full_name, role, avatar))
    conn.commit()

    # 3. Comprehensive Questions Bank
    questions = [
        # --- Computer Science (CS) ---
        # Easy
        (cat_map['cs'], 'Easy', 'Which data structure follows the First-In, First-Out (FIFO) principle?',
         None, 'Stack', 'Queue', 'Binary Tree', 'Priority Heap', 'B',
         'A Queue follows FIFO (First-In, First-Out), where elements are added at the rear and removed from the front. Stacks follow LIFO.', 10, 30),

        (cat_map['cs'], 'Easy', 'In Python, what is the output of bool([])?',
         'print(bool([]))', 'True', 'False', 'None', 'TypeError', 'B',
         'In Python, empty collections (lists, tuples, dicts, sets, strings) evaluate to False in a boolean context.', 10, 30),

        (cat_map['cs'], 'Easy', 'What does HTTP status code 404 signify?',
         None, 'Internal Server Error', 'Unauthorized Access', 'Not Found', 'Bad Gateway', 'C',
         'HTTP 404 indicates that the server cannot find the requested resource.', 10, 30),

        (cat_map['cs'], 'Easy', 'Which SQL clause is used to filter records returned by a SELECT query?',
         'SELECT * FROM employees ___ salary > 50000;', 'GROUP BY', 'HAVING', 'WHERE', 'ORDER BY', 'C',
         'The WHERE clause filters rows before any grouping occurs.', 10, 30),

        # Medium
        (cat_map['cs'], 'Medium', 'What is the worst-case time complexity of QuickSort?',
         None, 'O(N log N)', 'O(N)', 'O(N^2)', 'O(log N)', 'C',
         'QuickSort has an average time complexity of O(N log N), but its worst-case complexity degrades to O(N^2) when poor pivots are chosen (e.g. already sorted array with first element as pivot).', 20, 25),

        (cat_map['cs'], 'Medium', 'In JavaScript, what will `typeof NaN` return?',
         'console.log(typeof NaN);', '"number"', '"nan"', '"undefined"', '"object"', 'A',
         'Despite meaning "Not-a-Number", ECMAScript specification classifies NaN as a numeric data type, so `typeof NaN` yields "number".', 20, 25),

        (cat_map['cs'], 'Medium', 'Which Git command creates and immediately switches to a new branch in modern Git?',
         None, 'git branch -new <name>', 'git checkout -b <name> or git switch -c <name>', 'git fork <name>', 'git merge --create <name>', 'B',
         '`git checkout -b <name>` (or `git switch -c <name>`) creates the branch and checks it out in a single step.', 20, 25),

        (cat_map['cs'], 'Medium', 'What problem does the ACID acronym address in relational database management systems?',
         None, 'Network routing protocols', 'Transaction reliability & integrity', 'UI rendering speeds', 'Data compression algorithms', 'B',
         'ACID stands for Atomicity, Consistency, Isolation, and Durability, guaranteeing that database transactions are processed reliably.', 20, 25),

        # Hard
        (cat_map['cs'], 'Hard', 'In Python, what does the Global Interpreter Lock (GIL) actually prevent?',
         None, 'Multiple Python processes from running simultaneously', 'Multiple native OS threads from executing Python bytecodes concurrently', 'I/O operations from being non-blocking', 'Memory leaks in circular reference garbage collection', 'B',
         'The GIL is a mutex that protects access to Python objects, preventing multiple native threads from executing Python bytecodes at the same time.', 30, 20),

        (cat_map['cs'], 'Hard', 'Which consensus algorithm does the Raft protocol use to resolve leader election and log replication?',
         None, 'Proof of Work with difficulty targets', 'Randomized election timers & RPC quorum voting', 'Byzantine Fault Tolerance with 3-phase commit', 'Gossip protocol without a single leader', 'B',
         'Raft uses randomized election timers to avoid split votes and requires an absolute majority (quorum) through RequestVote and AppendEntries RPCs.', 30, 20),

        (cat_map['cs'], 'Hard', 'In computational complexity theory, what would it imply if P = NP?',
         None, 'Every problem solvable in polynomial time cannot be verified in polynomial time', 'Every problem whose solution can be verified in polynomial time can also be solved in polynomial time', 'NP-hard problems have no deterministic solutions', 'Cryptography becomes unbreakable', 'B',
         'P = NP means that any algorithmic problem whose positive solution can be verified quickly (polynomial time) can also be discovered/computed in polynomial time.', 30, 20),

        # --- Science & Physics (Science) ---
        # Easy
        (cat_map['science'], 'Easy', 'What is the chemical formula for ordinary table salt?',
         None, 'H2O', 'NaCl', 'CO2', 'CaCO3', 'B',
         'Table salt consists of Sodium (Na) and Chlorine (Cl), forming Sodium Chloride (NaCl).', 10, 30),

        (cat_map['science'], 'Easy', 'Which planet in our solar system has the most prominent ring system?',
         None, 'Jupiter', 'Mars', 'Saturn', 'Neptune', 'C',
         'Saturn has the most extensive and visually prominent ring system, composed mostly of ice particles and rocky debris.', 10, 30),

        (cat_map['science'], 'Easy', 'What is the powerhouse organelle of eukaryotic cells responsible for producing ATP?',
         None, 'Ribosome', 'Mitochondria', 'Endoplasmic Reticulum', 'Golgi Apparatus', 'B',
         'Mitochondria generate most of the chemical energy needed to power the cell through cellular respiration, storing it as ATP.', 10, 30),

        # Medium
        (cat_map['science'], 'Medium', 'What is the speed of light in a vacuum (approximate standard value)?',
         None, '150,000 km/s', '300,000 km/s (3 x 10^8 m/s)', '1,080,000 km/s', '3,000,000 m/s', 'B',
         'The speed of light in vacuum is exactly 299,792,458 m/s, conventionally rounded to 300,000 km/s or 3 x 10^8 m/s.', 20, 25),

        (cat_map['science'], 'Medium', 'Which fundamental force of nature is responsible for holding atomic nuclei together against electromagnetic repulsion?',
         None, 'Gravitational Force', 'Electromagnetic Force', 'Strong Nuclear Force', 'Weak Nuclear Force', 'C',
         'The Strong Nuclear Force overcomes electrostatic repulsion between positively charged protons and binds quarks and nucleons together.', 20, 25),

        (cat_map['science'], 'Medium', 'What does the Doppler effect describe regarding wave emissions?',
         None, 'The absorption of photons by electrons', 'The change in frequency or wavelength of a wave in relation to an observer moving relative to the wave source', 'The quantum tunneling of particles across barriers', 'The total internal reflection of light in glass', 'B',
         'The Doppler effect is the perceived frequency shift when the wave source and observer are in relative motion (e.g. siren pitch changing as it passes).', 20, 25),

        # Hard
        (cat_map['science'], 'Hard', 'According to Heisenberg’s Uncertainty Principle, which pair of physical quantities cannot be simultaneously measured with arbitrary precision?',
         None, 'Mass and Charge', 'Position and Linear Momentum', 'Temperature and Entropy', 'Velocity and Acceleration', 'B',
         'Heisenbergs principle states that Δx * Δp >= ħ/2, meaning position and momentum cannot both be known with infinite precision at the same time.', 30, 20),

        (cat_map['science'], 'Hard', 'What is the cosmic microwave background (CMB) radiation considered to be evidence of?',
         None, 'Decaying dark matter in the Milky Way halo', 'Thermal remnant radiation from the Big Bang approximately 380,000 years after creation', 'Hawking radiation from supermassive black holes', 'Neutrino oscillations from distant quasars', 'B',
         'The CMB is faint relic radiation that cooled as the universe expanded, providing bedrock observational evidence supporting the Big Bang cosmological model.', 30, 20),

        # --- Mathematics & Logic (Math) ---
        # Easy
        (cat_map['math'], 'Easy', 'What is the value of 7 factorial (7!)?',
         '7! = 7 * 6 * 5 * 4 * 3 * 2 * 1', '720', '5040', '2520', '40320', 'B',
         '7! = 7 * 720 = 5,040.', 10, 30),

        (cat_map['math'], 'Easy', 'Which of the following is the only even prime number?',
         None, '0', '2', '4', '6', 'B',
         '2 is the only even prime number because any other even number greater than 2 is divisible by 2.', 10, 30),

        (cat_map['math'], 'Easy', 'What is the sum of interior angles in any standard triangle?',
         None, '90 degrees', '180 degrees', '270 degrees', '360 degrees', 'B',
         'In Euclidean geometry, the sum of the interior angles of any triangle is always 180 degrees.', 10, 30),

        # Medium
        (cat_map['math'], 'Medium', 'A standard fair six-sided die is rolled twice. What is the probability of rolling a sum of exactly 7?',
         None, '1/12', '1/6', '7/36', '5/36', 'B',
         'Possible pairings for sum 7: (1,6), (2,5), (3,4), (4,3), (5,2), (6,1) = 6 favorable outcomes out of 36 total. 6/36 = 1/6.', 20, 25),

        (cat_map['math'], 'Medium', 'If log_2(x) = 6, what is the value of x?',
         'log2(x) = 6', '12', '36', '64', '128', 'C',
         'By definition of logarithms, x = 2^6 = 64.', 20, 25),

        (cat_map['math'], 'Medium', 'In a right triangle with legs of lengths 9 and 12, what is the length of the hypotenuse?',
         'c = sqrt(a^2 + b^2)', '15', '16', '18', '21', 'A',
         'By Pythagorean theorem, c = sqrt(9^2 + 12^2) = sqrt(81 + 144) = sqrt(225) = 15 (a 3-4-5 scaled triangle).', 20, 25),

        # Hard
        (cat_map['math'], 'Hard', 'What is the derivative of f(x) = x * ln(x) with respect to x?',
         'f(x) = x * ln(x)', '1 / x', 'ln(x) + 1', 'x + ln(x)', 'ln(x) / x', 'B',
         'Using the Product Rule (u*v)\' = u\'v + uv\': d/dx[x]*ln(x) + x*d/dx[ln(x)] = 1*ln(x) + x*(1/x) = ln(x) + 1.', 30, 20),

        (cat_map['math'], 'Hard', 'How many edges does a complete graph with 8 vertices (K_8) contain?',
         'E = n*(n-1)/2', '24', '28', '32', '56', 'B',
         'For a complete graph K_n, the number of edges is n*(n-1)/2. For n=8: 8 * 7 / 2 = 28 edges.', 30, 20),

        # --- World History & Geography (History) ---
        # Easy
        (cat_map['history'], 'Easy', 'Which river is historically credited with sustaining the civilization of Ancient Egypt?',
         None, 'Tigris', 'Amazon', 'Nile', 'Euphrates', 'C',
         'The Nile River provided fertile silt and irrigation essential for Ancient Egyptian agricultural civilization.', 10, 30),

        (cat_map['history'], 'Easy', 'What is the capital city of Australia?',
         None, 'Sydney', 'Melbourne', 'Canberra', 'Brisbane', 'C',
         'Canberra was selected as the compromise capital of Australia between Sydney and Melbourne in 1908.', 10, 30),

        (cat_map['history'], 'Easy', 'In which year did the Apollo 11 mission land the first humans on the Moon?',
         None, '1961', '1965', '1969', '1972', 'C',
         'Neil Armstrong and Buzz Aldrin landed on the lunar surface on July 20, 1969.', 10, 30),

        # Medium
        (cat_map['history'], 'Medium', 'Which Treaty signed in 1919 formally ended the state of war between Germany and the Allied Powers in World War I?',
         None, 'Treaty of Westphalia', 'Treaty of Versailles', 'Treaty of Paris', 'Treaty of Ghent', 'B',
         'The Treaty of Versailles was signed on June 28, 1919, in the Hall of Mirrors at the Palace of Versailles.', 20, 25),

        (cat_map['history'], 'Medium', 'Which strait separates the continents of Asia and North America?',
         None, 'Strait of Gibraltar', 'Bering Strait', 'Strait of Malacca', 'Bosphorus Strait', 'B',
         'The Bering Strait connects the Bering Sea and the Arctic Ocean, separating Russia (Asia) from Alaska (North America).', 20, 25),

        # Hard
        (cat_map['history'], 'Hard', 'Who was the Byzantine Emperor who codified Roman law into the famous Corpus Juris Civilis?',
         None, 'Constantine the Great', 'Justinian I', 'Heraclius', 'Basil II', 'B',
         'Emperor Justinian I (reigned 527–565 CE) directed the monumental codification of Roman legal jurisprudence.', 30, 20),

        (cat_map['history'], 'Hard', 'The ancient city-state of Carthage was founded by settlers from which seafaring civilization?',
         None, 'Phoenicians', 'Minoans', 'Mycenaeans', 'Etruscans', 'A',
         'Carthage was established as a Phoenician trading post by settlers from Tyre (modern Lebanon) in the 9th century BCE.', 30, 20),

        # --- Pop Culture & Trivia (Trivia) ---
        # Easy
        (cat_map['trivia'], 'Easy', 'Who directed the iconic 1993 film "Jurassic Park"?',
         None, 'James Cameron', 'Steven Spielberg', 'George Lucas', 'Ridley Scott', 'B',
         'Steven Spielberg directed Jurassic Park, based on Michael Crichtons novel.', 10, 30),

        (cat_map['trivia'], 'Easy', 'Which company originally created the Mario video game franchise?',
         None, 'Sony', 'Sega', 'Nintendo', 'Capcom', 'C',
         'Mario was created by Shigeru Miyamoto for Nintendo, premiering in 1981 Donkey Kong.', 10, 30),

        # Medium
        (cat_map['trivia'], 'Medium', 'In the Marvel Cinematic Universe, what is the name of Thor’s enchanted hammer?',
         None, 'Stormbreaker', 'Mjolnir', 'Gungnir', 'Hofund', 'B',
         'Mjolnir is Thors mystical hammer forged from Uru metal in the heart of a dying star.', 20, 25),

        (cat_map['trivia'], 'Medium', 'Which artist painted the legendary 1889 post-impressionist masterpiece "The Starry Night"?',
         None, 'Claude Monet', 'Pablo Picasso', 'Vincent van Gogh', 'Salvador Dalí', 'C',
         'Vincent van Gogh painted The Starry Night while staying at the Saint-Paul-de-Mausole asylum in Saint-Rémy-de-Provence.', 20, 25),

        # Hard
        (cat_map['trivia'], 'Hard', 'What was the first feature-length computer-animated film ever released in cinemas?',
         None, 'A Bug’s Life (1998)', 'Toy Story (1995)', 'Shrek (2001)', 'Antz (1998)', 'B',
         'Pixar’s Toy Story, released in November 1995 and directed by John Lasseter, made cinema history as the first full-length CGI film.', 30, 20),

        # --- Business & Finance (Finance) ---
        # Easy
        (cat_map['finance'], 'Easy', 'What does the financial acronym "IPO" stand for?',
         None, 'Initial Public Offering', 'Internal Profit Optimization', 'International Portfolio Operation', 'Integrated Price Order', 'A',
         'An Initial Public Offering (IPO) is when an unlisted private company first sells shares of stock to the general public.', 10, 30),

        (cat_map['finance'], 'Easy', 'If inflation rate is positive, what happens to the purchasing power of money over time?',
         None, 'It increases', 'It decreases', 'It remains strictly identical', 'It doubles every decade', 'B',
         'Inflation measures rising prices across an economy, which erodes the purchasing power of each unit of currency.', 10, 30),

        # Medium
        (cat_map['finance'], 'Medium', 'What does the Rule of 72 calculate in financial planning?',
         'Years = 72 / Interest Rate (%)', 'The maximum loan-to-value ratio for mortgages', 'Approximate number of years needed to double an investment at a fixed annual return', 'The statutory tax deduction on capital gains', 'The optimal stock-to-bond allocation percentage', 'B',
         'The Rule of 72 is a handy mental shortcut: divide 72 by the annual rate of return to estimate how many years it will take for your money to double.', 20, 25),

        (cat_map['finance'], 'Medium', 'What is a "Bull Market" defined as in economic parlance?',
         None, 'A prolonged period of declining stock values', 'A financial market where prices are rising or expected to rise substantially', 'A market characterized by extreme currency hyperinflation', 'A regulated government commodities exchange', 'B',
         'A bull market describes market conditions characterized by rising asset prices and sustained investor optimism.', 20, 25),

        # Hard
        (cat_map['finance'], 'Hard', 'In corporate valuation, what does EBITDA stand for?',
         None, 'Equity Before Interest, Taxes, Depreciation, and Amortization', 'Earnings Before Interest, Taxes, Depreciation, and Amortization', 'Estimated Balance Including Tariffs, Dividends, and Assets', 'Enterprise Budget Incurred Through Debt and Accruals', 'B',
         'EBITDA measures a company\'s overall financial performance and core profitability before accounting adjustments and capital structure costs.', 30, 20),

        (cat_map['finance'], 'Hard', 'Which mathematical option pricing model earned its creators the 1997 Nobel Memorial Prize in Economic Sciences?',
         None, 'Monte Carlo Stochastic Model', 'Black-Scholes-Merton Model', 'Binomial Lattice Model', 'Gordon Growth Model', 'B',
         'Fischer Black, Myron Scholes, and Robert Merton developed the Black-Scholes formula for pricing derivative options contracts.', 30, 20),
    ]

    # Insert questions
    cursor.execute('DELETE FROM questions')
    for q in questions:
        cursor.execute('''
            INSERT INTO questions (category_id, difficulty, question_text, code_snippet, option_a, option_b, option_c, option_d, correct_option, explanation, points, time_limit_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', q)
    conn.commit()

    # 4. Seed realistic attempts & streak history for demo users so charts & leaderboards look incredible right away!
    users_list = [
        ('student1', 4, [cat_map['cs'], cat_map['science'], cat_map['math']]),
        ('sarah_dev', 6, [cat_map['cs'], cat_map['math'], cat_map['finance']]),
        ('marcus_math', 5, [cat_map['math'], cat_map['history'], cat_map['science']]),
        ('elena_science', 7, [cat_map['science'], cat_map['trivia'], cat_map['cs']]),
        ('david_finance', 5, [cat_map['finance'], cat_map['cs'], cat_map['history']]),
    ]

    # Clear old attempts
    cursor.execute('DELETE FROM quiz_attempts')
    cursor.execute('DELETE FROM streak_logs')

    today = date.today()

    for username, streak_count, preferred_cats in users_list:
        cursor.execute('SELECT id, full_name FROM users WHERE username = ?', (username,))
        user_row = cursor.fetchone()
        if not user_row:
            continue
        uid = user_row['id']

        user_total_score = 0
        user_total_xp = 0
        attempts_count = 0

        # Simulate quiz attempts over the last `streak_count` days
        for day_idx in range(streak_count - 1, -1, -1):
            quiz_day = today - timedelta(days=day_idx)
            quiz_day_str = quiz_day.isoformat()

            # Record streak log
            cursor.execute('''
                INSERT INTO streak_logs (user_id, activity_date, attempts_count)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, activity_date) DO UPDATE SET attempts_count = attempts_count + 1
            ''', (uid, quiz_day_str))

            # Pick 1-2 categories for this day
            chosen_cat_id = random.choice(preferred_cats)
            cursor.execute('SELECT name FROM categories WHERE id = ?', (chosen_cat_id,))
            cat_name = cursor.fetchone()['name']

            difficulty = random.choice(['Easy', 'Medium', 'Hard'])
            # Fetch 5 questions
            cursor.execute('''
                SELECT * FROM questions WHERE category_id = ? ORDER BY RANDOM() LIMIT 5
            ''', (chosen_cat_id,))
            qs = cursor.fetchall()
            if not qs:
                continue

            sim_results = []
            sim_correct = 0
            sim_points = 0
            time_spent = 0

            for q in qs:
                # 80% chance correct for realistic demo data, except in weak subjects
                is_correct = random.random() < 0.75
                chosen_opt = q['correct_option'] if is_correct else random.choice([o for o in ['A', 'B', 'C', 'D'] if o != q['correct_option']])
                q_time = random.randint(8, 22)
                time_spent += q_time
                base_pts = q['points']
                pts = (base_pts if is_correct else 0)
                if is_correct:
                    sim_correct += 1
                    sim_points += pts

                sim_results.append({
                    'question_id': q['id'],
                    'question_text': q['question_text'],
                    'code_snippet': q['code_snippet'],
                    'category_name': cat_name,
                    'difficulty': q['difficulty'],
                    'option_a': q['option_a'],
                    'option_b': q['option_b'],
                    'option_c': q['option_c'],
                    'option_d': q['option_d'],
                    'correct_option': q['correct_option'],
                    'user_selected': chosen_opt,
                    'is_correct': is_correct,
                    'points_awarded': pts,
                    'explanation': q['explanation'],
                    'time_spent': q_time
                })

            total_qs = len(sim_results)
            pct = round((sim_correct / total_qs * 100), 1) if total_qs else 0
            passed = 1 if pct >= 60 else 0

            created_time_str = f"{quiz_day_str} {random.randint(10, 20):02d}:{random.randint(10, 59):02d}:00"

            cursor.execute('''
                INSERT INTO quiz_attempts 
                (user_id, category_id, category_name, difficulty, score, total_questions, percentage, xp_earned, time_taken_seconds, passed, detailed_results, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uid, chosen_cat_id, cat_name, difficulty, sim_correct, total_qs, pct, sim_points, time_spent, passed, json.dumps(sim_results), created_time_str))

            user_total_score += sim_correct
            user_total_xp += sim_points
            attempts_count += 1

        cursor.execute('''
            UPDATE users 
            SET total_score = ?, xp = ?, quizzes_taken = ?, current_streak = ?, longest_streak = ?, last_quiz_date = ? 
            WHERE id = ?
        ''', (user_total_score, user_total_xp, attempts_count, streak_count, max(streak_count, streak_count + 2), today.isoformat(), uid))

    conn.commit()
    conn.close()
    print("Database initialized and successfully seeded with rich questions and realistic demo data!")

if __name__ == '__main__':
    seed_database()
