import sys
import os
import seed_data
from app import app

if __name__ == '__main__':
    # Ensure database is seeded with rich questions
    seed_data.seed_database()

    port = 5000
    print("\n" + "=" * 65)
    print("🏆  QUIZMASTER PRO - ADVANCED QUIZ APP WITH SCORE TRACKING")
    print("=" * 65)
    print(f"👉 Local Web URL:       http://127.0.0.1:{port}")
    print("\n🔑 Demo Logins (1-Click or Manual):")
    print("   • Administrator:     Username: admin    | Password: admin123")
    print("   • Student Player:    Username: student1 | Password: quiz123")
    print("=" * 65 + "\n")

    app.run(host='127.0.0.1', port=port, debug=True)
