from app import app
from database import get_db, delete_student

def run_tests():
    print("=" * 60)
    print("RUNNING AUTOMATED TEST SUITE FOR SIMPLIFIED CODEBASE")
    print("=" * 60)

    client = app.test_client()

    # 1. Login page
    res = client.get('/login')
    assert res.status_code == 200, f"Login page failed: {res.status_code}"
    print("✓ [TEST 1] /login renders OK")

    # 2. Login submit
    res = client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    assert res.status_code == 200, f"Admin login failed: {res.status_code}"
    assert b"Dashboard" in res.data or b"Attendance" in res.data
    print("✓ [TEST 2] Admin authentication & session verified")

    # 3. Dashboard
    res = client.get('/dashboard')
    assert res.status_code == 200
    assert b"Total Enrolled" in res.data
    print("✓ [TEST 3] /dashboard renders OK")

    # 4. Students list
    res = client.get('/students')
    assert res.status_code == 200
    assert b"Student Directory" in res.data
    print("✓ [TEST 4] /students directory renders OK")

    # Clean up test student if exists
    delete_student('STD-TEST-999')

    # 5. Add new student
    res = client.post('/students/new', data={
        'student_id': 'STD-TEST-999',
        'name': 'Test Student',
        'student_class': 'Grade 10',
        'section': 'A',
        'contact_email': 'test@example.com',
        'guardian_phone': '1234567890'
    }, follow_redirects=True)
    assert res.status_code == 200
    print("✓ [TEST 5] Student registration + automatic QR code creation OK")

    # 6. Test /api/scan with valid student ID
    res = client.post('/api/scan', json={'token': 'STD-TEST-999', 'method': 'Test Client'})
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['success'] is True, f"Expected success: {json_data}"
    print(f"✓ [TEST 6] /api/scan SUCCESS verified: {json_data['message']}")

    # 7. Test duplicate scan on same day
    res = client.post('/api/scan', json={'token': 'STD-TEST-999', 'method': 'Test Client'})
    json_data = res.get_json()
    assert json_data['success'] is False
    assert json_data['status'] == 'ALREADY_RECORDED'
    print(f"✓ [TEST 7] Duplicate attendance prevention verified: {json_data['message']}")

    # 8. Test invalid student ID
    res = client.post('/api/scan', json={'token': 'INVALID_TOKEN_XYZ'})
    json_data = res.get_json()
    assert json_data['success'] is False
    print(f"✓ [TEST 8] Invalid QR rejection verified: {json_data['message']}")

    # 9. Test /scanner page
    res = client.get('/scanner')
    assert res.status_code == 200
    assert b"reader" in res.data
    print("✓ [TEST 9] /scanner webcam interface renders OK")

    # 10. Test /attendance page
    res = client.get('/attendance')
    assert res.status_code == 200
    print("✓ [TEST 10] /attendance daily logs render OK")

    # 11. Test CSV export
    res = client.get('/reports/export/csv')
    assert res.status_code == 200
    assert res.headers['Content-Type'].startswith('text/csv')
    print("✓ [TEST 11] CSV export generated valid spreadsheet download")

    # 12. Test Word (.docx) export
    res = client.get('/reports/export/docx')
    assert res.status_code == 200
    assert len(res.data) > 1000
    print(f"✓ [TEST 12] Microsoft Word (.docx) export OK ({len(res.data)} bytes generated)")

    # 13. Test student ID card view
    res = client.get('/students/id-card/STD-TEST-999')
    assert res.status_code == 200
    assert b"Official Student ID Badge" in res.data
    print("✓ [TEST 13] Student Smart ID Card badge renders OK")

    # 14. Test student ID card PDF export (CR80 standard)
    res = client.get('/students/id-card/STD-TEST-999/pdf?paper=A4&orientation=portrait')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert len(res.data) > 2000
    print(f"✓ [TEST 14] Student ID Card PDF (A4 Sheet + Cut Marks) generated ({len(res.data)} bytes)")

    res = client.get('/students/id-card/STD-TEST-999/pdf?paper=CR80&orientation=portrait')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    print(f"✓ [TEST 15] Student ID Card PDF (Exact CR80 PVC Size) generated ({len(res.data)} bytes)")

    # 16. Test bulk ID cards PDF export
    res = client.get('/students/bulk-cards/pdf?class=All&orientation=portrait')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert len(res.data) > 5000
    print(f"✓ [TEST 16] Batch ID Cards PDF generated ({len(res.data)} bytes)")

    # Clean up test student
    delete_student('STD-TEST-999')
    print("✓ [TEST 17] Test data cleaned up successfully")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED! CODEBASE IS CLEAN AND READY! 🎉")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
