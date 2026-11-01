"""
sample_data.py - Database Seeder Script
Yeh script database create karti hai aur 15 sample students insert karke unke QR codes generate karti hai.
"""

import os
import random
from datetime import date, timedelta
from database import init_db, get_db, add_student
from qr_generator import generate_qr

SAMPLE_STUDENTS = [
    ("STD-2026-101", "Alex Morgan", "Grade 10", "A", "alex.morgan@school.edu", "+1 (555) 234-5678"),
    ("STD-2026-102", "Sophia Patel", "Grade 10", "A", "sophia.patel@school.edu", "+1 (555) 345-6789"),
    ("STD-2026-103", "Ethan Walker", "Grade 10", "B", "ethan.walker@school.edu", "+1 (555) 456-7890"),
    ("STD-2026-104", "Olivia Zhang", "Grade 10", "B", "olivia.zhang@school.edu", "+1 (555) 567-8901"),
    ("STD-2026-105", "Liam Henderson", "Grade 11", "A", "liam.h@school.edu", "+1 (555) 678-9012"),
    ("STD-2026-106", "Emma Watson", "Grade 11", "A", "emma.w@school.edu", "+1 (555) 789-0123"),
    ("STD-2026-107", "Noah Campbell", "Grade 11", "B", "noah.c@school.edu", "+1 (555) 890-1234"),
    ("STD-2026-108", "Ava Martinez", "Grade 11", "B", "ava.m@school.edu", "+1 (555) 901-2345"),
    ("STD-2026-109", "Lucas Dubois", "Grade 12", "Science", "lucas.d@school.edu", "+1 (555) 012-3456"),
    ("STD-2026-110", "Mia Tanaka", "Grade 12", "Science", "mia.t@school.edu", "+1 (555) 123-4567"),
    ("STD-2026-111", "Benjamin Clark", "Grade 12", "Arts", "ben.clark@school.edu", "+1 (555) 234-5679"),
    ("STD-2026-112", "Chloe Rivera", "Grade 12", "Arts", "chloe.r@school.edu", "+1 (555) 345-6780"),
    ("STD-2026-113", "Daniel Kim", "Grade 9", "A", "daniel.kim@school.edu", "+1 (555) 456-7891"),
    ("STD-2026-114", "Isabella Rossi", "Grade 9", "A", "isabella.r@school.edu", "+1 (555) 567-8902"),
    ("STD-2026-115", "James Anderson", "Grade 9", "B", "james.a@school.edu", "+1 (555) 678-9013"),
]

def seed_database():
    print("Database initialize ho raha hai...")
    init_db()

    conn = get_db()
    existing_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]

    if existing_count == 0:
        print("Sample students add kiye ja rahe hain aur QR codes ban rahe hain...")
        for sid, name, s_class, sec, email, phone in SAMPLE_STUDENTS:
            success, msg = add_student(sid, name, s_class, sec, email, phone)
            if success:
                qr_path = generate_qr(sid)
                print(f"  + Added: {name} ({sid}) -> QR: {qr_path}")

    # Aj ke sample attendance records
    today_str = date.today().isoformat()
    students = conn.execute("SELECT student_id FROM students").fetchall()

    for idx, s in enumerate(students[:8]): # First 8 students marked present
        sid = s['student_id']
        time_str = f"08:{15 + idx:02d}:30"
        status = 'Present' if (15 + idx) <= 30 else 'Late'
        try:
            conn.execute('''
                INSERT OR IGNORE INTO attendance (student_id, attendance_date, attendance_time, attendance_status, scan_method)
                VALUES (?, ?, ?, ?, 'QR Camera')
            ''', (sid, today_str, time_str, status))
        except Exception:
            pass

    conn.commit()
    conn.close()
    print("Sample data successfully loaded!")

if __name__ == '__main__':
    seed_database()
