"""
database.py - Database Management for School Attendance System
Yeh file SQLite database banati hai aur data save/read karne ke aasan functions provide karti hai.
"""

import sqlite3
from datetime import datetime, date

DB_NAME = "attendance.db"

def get_db():
    """Database se connect karta hai aur rows ko dictionary jesa access deta hai."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Database tables create karta hai (Students, Attendance, Admins)."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        student_class TEXT NOT NULL,
        section TEXT DEFAULT 'A',
        contact_email TEXT,
        guardian_phone TEXT,
        account_status TEXT DEFAULT 'Active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Attendance Table
    # UNIQUE(student_id, attendance_date) 
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        attendance_date TEXT NOT NULL,
        attendance_time TEXT NOT NULL,
        attendance_status TEXT NOT NULL,
        scan_method TEXT DEFAULT 'QR Camera',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, attendance_date)
    )
    ''')

    # 3. Admins Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL
    )
    ''')

    # Default Admin insert karna (admin / admin123)
    cursor.execute('''
        INSERT OR IGNORE INTO admins (id, username, password, full_name)
        VALUES (1, 'admin', 'admin123', 'School Administrator')
    ''')

    conn.commit()
    conn.close()

# ==================== ADMIN LOGIN ====================

def check_admin(username, password):
    """Admin ka username aur password check karta hai."""
    conn = get_db()
    admin = conn.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password)).fetchone()
    conn.close()
    return admin

def update_admin_password(new_password):
    """Admin ka password update karta hai."""
    conn = get_db()
    conn.execute("UPDATE admins SET password = ? WHERE id = 1", (new_password,))
    conn.commit()
    conn.close()
    return True

# ==================== STUDENT FUNCTIONS ====================

def get_all_students(class_filter=None, status_filter=None, search=None):
    """Tamam students ki list lata hai (search aur filter ke sath)."""
    conn = get_db()
    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if class_filter and class_filter != 'All':
        query += " AND student_class = ?"
        params.append(class_filter)

    if status_filter and status_filter != 'All':
        query += " AND account_status = ?"
        params.append(status_filter)

    if search:
        query += " AND (name LIKE ? OR student_id LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])

    query += " ORDER BY student_class ASC, name ASC"
    students = conn.execute(query, params).fetchall()
    conn.close()
    return students

def get_student(student_id):
    """Student ID ke zariye kisi student ka data lata hai."""
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (student_id.strip().upper(),)).fetchone()
    conn.close()
    return student

def add_student(student_id, name, student_class, section='A', contact_email='', guardian_phone=''):
    """Naya student database me add karta hai."""
    conn = get_db()
    try:
        conn.execute('''
            INSERT INTO students (student_id, name, student_class, section, contact_email, guardian_phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id.strip().upper(), name.strip(), student_class.strip(), section.strip().upper(), contact_email.strip(), guardian_phone.strip()))
        conn.commit()
        conn.close()
        return True, "Student registered successfully."
    except sqlite3.IntegrityError:
        conn.close()
        return False, f"Student ID '{student_id}' already exists."

def update_student(student_id, name, student_class, section, contact_email, guardian_phone, account_status):
    """Student ki details update karta hai."""
    conn = get_db()
    conn.execute('''
        UPDATE students
        SET name = ?, student_class = ?, section = ?, contact_email = ?, guardian_phone = ?, account_status = ?
        WHERE student_id = ?
    ''', (name.strip(), student_class.strip(), section.strip().upper(), contact_email.strip(), guardian_phone.strip(), account_status, student_id))
    conn.commit()
    conn.close()
    return True

def delete_student(student_id):
    """Student aur uski attendance delete karta hai."""
    conn = get_db()
    conn.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()
    return True

def get_classes():
    """Distinct classes ki list nikalta hai dropdown ke liye."""
    conn = get_db()
    rows = conn.execute("SELECT DISTINCT student_class FROM students ORDER BY student_class ASC").fetchall()
    conn.close()
    return [r['student_class'] for r in rows]

# ==================== ATTENDANCE FUNCTIONS ====================

def mark_attendance(student_id, scan_method='QR Camera'):
    """
    QR code scan hone par attendance lagata hai.
    1. Check karta hai student active hai ya nahi.
    2. Check karta hai aj pehle lag chuki hai ya nahi (Duplicate Check).
    3. Time 08:30 se zyada ho to 'Late' warna 'Present' mark karta hai.
    """
    conn = get_db()
    clean_id = student_id.strip().upper()

    # 1. Student dhundo
    student = conn.execute("SELECT * FROM students WHERE student_id = ?", (clean_id,)).fetchone()
    if not student:
        conn.close()
        return False, "Student not found in system.", None, None

    # 2. Check active status
    if student['account_status'] != 'Active':
        conn.close()
        return False, f"Student {student['name']} is Inactive/Deactivated.", dict(student), None

    today_date = date.today().isoformat()       # YYYY-MM-DD
    current_time = datetime.now().strftime('%H:%M:%S') # HH:MM:SS

    # 3. Duplicate attendance check
    existing = conn.execute('''
        SELECT * FROM attendance WHERE student_id = ? AND attendance_date = ?
    ''', (clean_id, today_date)).fetchone()

    if existing:
        conn.close()
        return False, f"Already marked present today at {existing['attendance_time']}.", dict(student), dict(existing)

    # 4. Check Late or Present (Cutoff time = 08:30 AM)
    current_time_short = datetime.now().strftime('%H:%M')
    status = 'Late' if current_time_short > '08:30' else 'Present'

    # 5. Insert attendance record
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO attendance (student_id, attendance_date, attendance_time, attendance_status, scan_method)
            VALUES (?, ?, ?, ?, ?)
        ''', (clean_id, today_date, current_time, status, scan_method))
        conn.commit()

        record = {
            'student_id': clean_id,
            'attendance_date': today_date,
            'attendance_time': current_time,
            'attendance_status': status,
            'scan_method': scan_method
        }
        conn.close()
        return True, f"Attendance marked successfully! ({status})", dict(student), record
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Attendance already recorded for today.", dict(student), None

def get_daily_attendance(selected_date=None, class_filter=None, status_filter=None, search=None):
    """Kisi specific date ki attendance list student details ke sath lata hai."""
    if not selected_date:
        selected_date = date.today().isoformat()

    conn = get_db()
    query = '''
        SELECT 
            s.student_id, s.name, s.student_class, s.section, s.account_status,
            a.attendance_time, a.attendance_status, a.scan_method
        FROM students s
        LEFT JOIN attendance a ON s.student_id = a.student_id AND a.attendance_date = ?
        WHERE s.account_status = 'Active'
    '''
    params = [selected_date]

    if class_filter and class_filter != 'All':
        query += " AND s.student_class = ?"
        params.append(class_filter)

    if search:
        query += " AND (s.name LIKE ? OR s.student_id LIKE ?)"
        term = f"%{search.strip()}%"
        params.extend([term, term])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    result = []
    for r in rows:
        item = dict(r)
        if not item['attendance_status']:
            item['attendance_status'] = 'Absent'
            item['attendance_time'] = '-'
            item['scan_method'] = '-'

        if status_filter and status_filter != 'All':
            if item['attendance_status'] != status_filter:
                continue

        result.append(item)

    result.sort(key=lambda x: (x['student_class'], x['name']))
    return result

def get_dashboard_stats():
    """Dashboard par dikhane ke liye Total, Present, Late, aur Absent count karta hai."""
    conn = get_db()
    today_date = date.today().isoformat()

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    active_students = conn.execute("SELECT COUNT(*) FROM students WHERE account_status = 'Active'").fetchone()[0]

    present_today = conn.execute('''
        SELECT COUNT(*) FROM attendance 
        WHERE attendance_date = ? AND attendance_status = 'Present'
    ''', (today_date,)).fetchone()[0]

    late_today = conn.execute('''
        SELECT COUNT(*) FROM attendance 
        WHERE attendance_date = ? AND attendance_status = 'Late'
    ''', (today_date,)).fetchone()[0]

    total_checked_in = present_today + late_today
    absent_today = max(0, active_students - total_checked_in)
    rate = round((total_checked_in / active_students * 100), 1) if active_students > 0 else 0.0

    conn.close()

    return {
        'total': total_students,
        'active': active_students,
        'present': present_today,
        'late': late_today,
        'absent': absent_today,
        'rate': rate,
        'today': today_date
    }

def get_recent_scans():
    """Aj ke latest scans list karta hai live stream ke liye."""
    conn = get_db()
    today_date = date.today().isoformat()
    rows = conn.execute('''
        SELECT a.attendance_time, a.attendance_status, a.scan_method, s.student_id, s.name, s.student_class, s.section
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        WHERE a.attendance_date = ?
        ORDER BY a.id DESC
        LIMIT 8
    ''', (today_date,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
