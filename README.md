# 🏆 QuizMaster Pro - Advanced Quiz App with Score Tracking

A comprehensive, full-stack quiz and performance tracking application built with **Flask**, **SQLite**, **Tailwind CSS**, and **Chart.js**.

---

## 🌟 Key Features

1. **User Authentication & Role Management**:
   - Secure registration, login, and password hashing (`werkzeug.security`).
   - Role-based authorization (`user` vs `admin`).
   - 1-Click instant demo logins for fast testing.

2. **Multi-Category & Difficulty Selection**:
   - 6 Disciplines: *Computer Science & Code*, *Science & Physics*, *Mathematics & Logic*, *World History & Geography*, *Pop Culture & Trivia*, and *Business & Finance*.
   - 3 Difficulty Tiers: **Easy** (10 pts, 30s), **Medium** (20 pts, 25s), and **Hard** (30 pts, 20s).
   - "Mixed All-Rounder" mode and "Weak Subject Recovery" drills.

3. **Interactive Timed Quiz Arena**:
   - Per-question real-time countdown timer with color shifting (Green ➔ Amber ➔ Red) and audio cues.
   - Question Palette / Navigator drawer: jump to any question, view answered, pending, and flagged status.
   - Code snippet syntax box support.
   - Keyboard shortcuts: `1-4` or `A-D` for options, `F` to flag, `Arrows` / `Enter` to navigate.
   - Synthesized audio cues via Web Audio API (with instant mute toggle).

4. **Automated Marks & Score Calculation**:
   - Automatic percentage scoring with letter grades (**S, A, B, C, D, F**).
   - Difficulty multipliers (1x, 1.5x, 2x) + speed bonus for fast correct answers.
   - Detailed question-by-question review showing selected option vs correct answer with explanations.

5. **Daily Quiz Streak Tracking**:
   - Real-time streak tracking engine calculating consecutive days of quiz completion.
   - 7-Day interactive calendar widget with visual completion status dots.
   - Streak badges and peak streak records saved per user.

6. **Weak Subject Diagnostic Engine**:
   - Aggregates user accuracy across all categories.
   - Automatically identifies and flags categories with accuracy < 60% as "Weak Subjects".
   - 1-Click **"Launch Weak Subject Recovery Quiz"** dynamically pulls drill questions from weakest areas.

7. **Performance Reports & Analytics**:
   - Score Progression Over Time (Chart.js Line Chart).
   - Category Mastery & Accuracy Radar / Bar Chart.
   - Detailed Subject Diagnostic Matrix table.

8. **Global & Category Leaderboards**:
   - Podium presentation for Gold 🥇, Silver 🥈, and Bronze 🥉.
   - Filter by Category and Timeframe.
   - Current user's standing banner with rank gap.

9. **Administrator Control Portal**:
   - Full Question Bank CRUD: add, edit, delete questions with categories, difficulty, time limits, and explanations.
   - User Management: promote to admin, demote, reset statistics, or delete accounts.
   - Platform health metrics and category popularity counters.

---

## 🚀 How to Run in VS Code

1. Open this folder in VS Code (`C:\Users\user\OneDrive\Desktop\quiz_master_pro`).
2. Open a terminal in VS Code (`Ctrl + ~` or Terminal ➔ New Terminal).
3. Run the application:
   ```powershell
   python run.py
   ```
4. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🔑 Demo Credentials

| Role | Username | Password |
|---|---|---|
| **Administrator** | `admin` | `admin123` |
| **Student (Alex)** | `student1` | `quiz123` |
| **Developer (Sarah)** | `sarah_dev` | `quiz123` |
