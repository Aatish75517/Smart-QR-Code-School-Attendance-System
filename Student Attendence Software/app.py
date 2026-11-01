"""
app.py - Main Flask Application for Smart QR Code School Attendance System 
 
"""

import os
import csv
import io
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response, send_file

# Database aur QR code helper functions import karna
from database import (
    init_db, get_db, check_admin, update_admin_password,
    get_all_students, get_student, add_student, update_student, delete_student, get_classes,
    mark_attendance, get_daily_attendance, get_dashboard_stats, get_recent_scans
)
from qr_generator import generate_qr
from docx_report import create_daily_attendance_docx
from card_pdf_generator import generate_single_card_pdf, generate_bulk_cards_pdf

app = Flask(__name__)
app.secret_key = "school_attendance_secret_key_123"

# Database tables initialize karna agar pehle se na hon
init_db()

# School Settings (School name aur current year)
SCHOOL_NAME = "Govt Model School G.O.R Colony Hyderabad"
ACADEMIC_YEAR = "2026 - 2027"

# Tamam templates ko globally school info provide karna
@app.context_processor
def global_variables():
    return {
        'school_name': SCHOOL_NAME,
        'academic_year': ACADEMIC_YEAR,
        'is_logged_in': 'admin' in session,
        'today_date': date.today().isoformat()
    }

# AUTHENTICATION (LOGIN / LOGOUT)

@app.route('/')
def home():
    """Agar login hai to dashboard bhejo, warna login page par."""
    if 'admin' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if 'admin' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        admin = check_admin(username, password)
        if admin:
            session['admin'] = admin['username']
            session['admin_name'] = admin['full_name']
            flash(f"Welcome, {admin['full_name']}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password. Default is: admin / admin123", "danger")

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin session khatam karke logout karta hai."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ==================== ADMIN DASHBOARD ====================

@app.route('/dashboard')
def dashboard():
    """Admin Dashboard: Total, Present, Absent counts aur recent scans dikhata hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    stats = get_dashboard_stats()
    recent = get_recent_scans()
    classes = get_classes()
    return render_template('dashboard.html', stats=stats, recent_scans=recent, classes=classes)

# ==================== STUDENT MANAGEMENT ====================

@app.route('/students')
def students_list():
    """Students ki list dikhata hai (Search aur Class filter ke sath)."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    class_filter = request.args.get('class', 'All')
    status_filter = request.args.get('status', 'All')
    search = request.args.get('q', '').strip()

    students = get_all_students(class_filter, status_filter, search)
    classes = get_classes()
    return render_template('students.html', students=students, classes=classes, current_class=class_filter, current_status=status_filter, search_query=search)

@app.route('/students/new', methods=['GET', 'POST'])
def student_add():
    """Naya student register karta hai aur automatic QR code generate karta hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        student_class = request.form.get('student_class', '').strip()
        section = request.form.get('section', 'A').strip()
        email = request.form.get('contact_email', '').strip()
        phone = request.form.get('guardian_phone', '').strip()

        if not student_id or not name or not student_class:
            flash("Student ID, Name, and Class are required.", "danger")
            return render_template('student_form.html', student=None, is_edit=False)

        success, msg = add_student(student_id, name, student_class, section, email, phone)
        if success:
            # Automatic QR code image generation
            generate_qr(student_id.upper())
            flash(f"Student '{name}' added successfully! QR Code generated.", "success")
            return redirect(url_for('student_id_card', student_id=student_id.upper()))
        else:
            flash(msg, "danger")

    return render_template('student_form.html', student=None, is_edit=False)

@app.route('/students/edit/<student_id>', methods=['GET', 'POST'])
def student_edit(student_id):
    """Student ka record edit/update karta hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    student = get_student(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('students_list'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        student_class = request.form.get('student_class', '').strip()
        section = request.form.get('section', 'A').strip()
        email = request.form.get('contact_email', '').strip()
        phone = request.form.get('guardian_phone', '').strip()
        status = request.form.get('account_status', 'Active').strip()

        update_student(student_id, name, student_class, section, email, phone, status)
        flash("Student record updated successfully.", "success")
        return redirect(url_for('students_list'))

    return render_template('student_form.html', student=student, is_edit=True)

@app.route('/students/delete/<student_id>', methods=['POST'])
def student_delete(student_id):
    """Student ko delete karta hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    delete_student(student_id)
    # Delete QR file if exists
    qr_file = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes', f"{student_id}.png")
    if os.path.exists(qr_file):
        try:
            os.remove(qr_file)
        except Exception:
            pass

    flash("Student removed from database.", "info")
    return redirect(url_for('students_list'))

@app.route('/students/id-card/<student_id>')
def student_id_card(student_id):
    """Student ka printable Smart ID Card badge dikhata hai."""
    student = get_student(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('students_list'))

    # Agar QR code file mojood na ho to bana lo
    qr_file = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes', f"{student_id}.png")
    if not os.path.exists(qr_file):
        generate_qr(student_id)

    qr_url = f"/static/qrcodes/{student_id}.png"
    return render_template('student_id_card.html', student=student, qr_url=qr_url)

@app.route('/students/id-card/<student_id>/pdf')
def student_id_card_pdf(student_id):
    """Student ka standard CR80 PVC ID card PDF download karta hai (A4 Sheet ya Direct PVC Card)."""
    student = get_student(student_id)
    if not student:
        flash("Student not found.", "danger")
        return redirect(url_for('students_list'))

    orientation = request.args.get('orientation', 'portrait').lower()
    if orientation not in ['portrait', 'landscape']:
        orientation = 'portrait'

    paper = request.args.get('paper', 'A4').upper()
    if paper not in ['A4', 'CR80']:
        paper = 'A4'

    qr_file = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes', f"{student_id}.png")
    if not os.path.exists(qr_file):
        generate_qr(student_id)

    pdf_stream = generate_single_card_pdf(
        student=dict(student),
        school_name=SCHOOL_NAME,
        academic_year=ACADEMIC_YEAR,
        qr_path=qr_file,
        orientation=orientation,
        paper_size=paper
    )

    suffix = "PVC_Exact" if paper == 'CR80' else "A4_Print"
    filename = f"{student_id}_ID_Card_{orientation}_{suffix}.pdf"

    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.route('/students/bulk-cards')
def bulk_id_cards():
    """Tamam students ke ID cards ek sath print karne ka page."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    class_filter = request.args.get('class', 'All')
    students = get_all_students(class_filter=class_filter, status_filter='Active')
    classes = get_classes()

    # Tamam students ke QR code check karo
    for s in students:
        qr_file = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes', f"{s['student_id']}.png")
        if not os.path.exists(qr_file):
            generate_qr(s['student_id'])

    return render_template('bulk_id_cards.html', students=students, classes=classes, current_class=class_filter)

@app.route('/students/bulk-cards/pdf')
def bulk_id_cards_pdf():
    """Tamam students ke standard CR80 PVC ID cards ka batch A4 PDF download karta hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    class_filter = request.args.get('class', 'All')
    orientation = request.args.get('orientation', 'portrait').lower()
    if orientation not in ['portrait', 'landscape']:
        orientation = 'portrait'

    students = [dict(s) for s in get_all_students(class_filter=class_filter, status_filter='Active')]
    qr_dir = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes')

    for s in students:
        qr_file = os.path.join(qr_dir, f"{s['student_id']}.png")
        if not os.path.exists(qr_file):
            generate_qr(s['student_id'])

    pdf_stream = generate_bulk_cards_pdf(
        students=students,
        school_name=SCHOOL_NAME,
        academic_year=ACADEMIC_YEAR,
        qr_dir=qr_dir,
        orientation=orientation
    )

    clean_class = class_filter.replace(' ', '_')
    filename = f"Batch_Student_ID_Cards_{clean_class}_{orientation}.pdf"

    return send_file(
        pdf_stream,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

# ==================== ATTENDANCE SCANNER & API ====================

@app.route('/scanner')
def scanner():
    """Webcam QR Code Scanner ka interface."""
    recent = get_recent_scans()
    stats = get_dashboard_stats()
    return render_template('scanner.html', recent_scans=recent, stats=stats)

@app.route('/api/scan', methods=['POST'])
def api_scan():
    """
    QR code scan hone par yeh API call hoti hai.
    JSON Request: {"token": "STD-2026-101", "method": "QR Camera"}
    Attendance mark karta hai aur JSON response return karta hai.
    """
    data = request.get_json(silent=True) or {}
    token = data.get('token', '').strip()
    method = data.get('method', 'QR Camera').strip()

    if not token:
        return jsonify({'success': False, 'status': 'EMPTY', 'message': 'No QR code data received.'}), 400

    # database.py ka mark_attendance function call karo
    success, message, student_data, record_data = mark_attendance(token, scan_method=method)

    status_code = "SUCCESS" if success else ("ALREADY_RECORDED" if "Already marked" in message else "ERROR")

    return jsonify({
        'success': success,
        'status': status_code,
        'message': message,
        'student': student_data,
        'record': record_data
    })

# ==================== ATTENDANCE RECORDS & REPORTS ====================

@app.route('/attendance')
def attendance_list():
    """Daily attendance list date picker ke sath."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    selected_date = request.args.get('date', date.today().isoformat())
    class_filter = request.args.get('class', 'All')
    status_filter = request.args.get('status', 'All')
    search = request.args.get('q', '').strip()

    records = get_daily_attendance(selected_date, class_filter, status_filter, search)
    classes = get_classes()

    # Summary counts
    total = len(records)
    present_cnt = sum(1 for r in records if r['attendance_status'] == 'Present')
    late_cnt = sum(1 for r in records if r['attendance_status'] == 'Late')
    absent_cnt = sum(1 for r in records if r['attendance_status'] == 'Absent')
    rate = round(((present_cnt + late_cnt) / total * 100), 1) if total > 0 else 0.0

    date_stats = {'total': total, 'present': present_cnt, 'late': late_cnt, 'absent': absent_cnt, 'rate': rate}

    return render_template('attendance.html', records=records, selected_date=selected_date, classes=classes, current_class=class_filter, current_status=status_filter, search_query=search, date_stats=date_stats)

@app.route('/attendance/manual-mark', methods=['POST'])
def manual_mark():
    """Teacher/Admin manual attendance mark kar sakte hain."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    student_id = request.form.get('student_id', '').strip()
    status = request.form.get('status', 'Present').strip()
    custom_date = request.form.get('date', date.today().isoformat()).strip()

    conn = get_db()
    now_time = datetime.now().strftime('%H:%M:%S')

    try:
        conn.execute('''
            INSERT INTO attendance (student_id, attendance_date, attendance_time, attendance_status, scan_method)
            VALUES (?, ?, ?, ?, 'Manual Entry')
            ON CONFLICT(student_id, attendance_date) DO UPDATE SET
                attendance_status = excluded.attendance_status,
                attendance_time = excluded.attendance_time,
                scan_method = 'Manual Entry'
        ''', (student_id.upper(), custom_date, now_time, status))
        conn.commit()
        conn.close()
        flash(f"Attendance for {student_id.upper()} saved as '{status}'.", "success")
    except Exception as e:
        conn.close()
        flash(f"Error: {e}", "danger")

    return redirect(request.referrer or url_for('attendance_list'))

@app.route('/reports/export/csv')
def export_csv():
    """Attendance data CSV spreadsheet me export karta hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    selected_date = request.args.get('date', date.today().isoformat())
    records = get_daily_attendance(selected_date)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["#", "Student ID", "Student Name", "Class", "Section", "Date", "Status", "Time", "Scan Method"])

    for idx, r in enumerate(records, start=1):
        writer.writerow([idx, r['student_id'], r['name'], r['student_class'], r.get('section', ''), selected_date, r['attendance_status'], r.get('attendance_time', ''), r.get('scan_method', '')])

    output.seek(0)
    filename = f"Attendance_{selected_date}.csv"
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@app.route('/reports/export/docx')
def export_docx():
    """Attendance report MS Word (.docx) document me export karta hai."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    selected_date = request.args.get('date', date.today().isoformat())
    records = get_daily_attendance(selected_date)
    settings_dict = {'school_name': SCHOOL_NAME, 'academic_year': ACADEMIC_YEAR}

    doc_stream = create_daily_attendance_docx(records, selected_date, settings_dict)
    filename = f"Attendance_Report_{selected_date}.docx"

    return send_file(
        doc_stream,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=filename
    )

# ==================== SETTINGS ====================

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    """School settings aur admin password change page."""
    if 'admin' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        new_pwd = request.form.get('new_password', '').strip()
        confirm_pwd = request.form.get('confirm_password', '').strip()

        if new_pwd != confirm_pwd:
            flash("Passwords do not match.", "danger")
        elif len(new_pwd) < 4:
            flash("Password must be at least 4 characters.", "danger")
        else:
            update_admin_password(new_pwd)
            flash("Admin password updated successfully!", "success")

    return render_template('settings.html')

if __name__ == '__main__':
    print("=" * 60)
    print("  SMART QR CODE SCHOOL ATTENDANCE SYSTEM")
    print("  Server URL: http://127.0.0.1:5000")
    print("  Admin Login: admin / admin123")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
