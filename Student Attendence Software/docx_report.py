import os
from io import BytesIO
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, hex_color):
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tc_pr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Set inner cell padding in twentieths of a point (dxa)."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tc_pr.append(tc_mar)

def create_daily_attendance_docx(records, selected_date, settings):
    """
    Generates a beautifully formatted MS Word (.docx) Daily Attendance Report.
    Returns BytesIO object containing the docx binary.
    """
    doc = Document()

    # Set page margins (0.75 in)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    school_name = settings.get('school_name', 'Govt Model School G.O.R Colony Hyderabad')
    motto = settings.get('school_motto', 'Smart Attendance Management System')
    academic_year = settings.get('academic_year', '2026-2027')

    # Title & Header
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run(school_name.upper())
    title_run.font.name = 'Calibri'
    title_run.font.size = Pt(20)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(30, 27, 75) # #1e1b4b

    subtitle_p = doc.add_paragraph()
    subtitle_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = subtitle_p.add_run(f"{motto} | Academic Year: {academic_year}")
    sub_run.font.name = 'Calibri'
    sub_run.font.size = Pt(10)
    sub_run.font.color.rgb = RGBColor(100, 116, 139) # slate-500

    doc.add_paragraph() # Spacer

    report_title_p = doc.add_paragraph()
    report_title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rt_run = report_title_p.add_run("DAILY STUDENT ATTENDANCE REPORT")
    rt_run.font.name = 'Calibri'
    rt_run.font.size = Pt(14)
    rt_run.font.bold = True
    rt_run.font.color.rgb = RGBColor(37, 99, 235) # blue-600

    # Summary Statistics Calculation
    total = len(records)
    present_cnt = sum(1 for r in records if r['attendance_status'] == 'Present')
    late_cnt = sum(1 for r in records if r['attendance_status'] == 'Late')
    absent_cnt = sum(1 for r in records if r['attendance_status'] == 'Absent')
    attended = present_cnt + late_cnt
    attendance_rate = round((attended / total * 100), 1) if total > 0 else 0.0

    # Stat summary boxes (using a 2-row table)
    stat_table = doc.add_table(rows=2, cols=5)
    stat_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["REPORT DATE", "TOTAL STUDENTS", "PRESENT", "LATE", "ATTENDANCE RATE"]
    values = [selected_date, str(total), str(present_cnt), str(late_cnt), f"{attendance_rate}%"]
    bg_colors = ["F1F5F9", "F1F5F9", "ECFDF5", "FEF3C7", "EEF2FF"]

    for col_idx in range(5):
        # Header cell
        cell_h = stat_table.cell(0, col_idx)
        set_cell_background(cell_h, "1E1B4B")
        set_cell_margins(cell_h, top=80, bottom=80, left=100, right=100)
        p = cell_h.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(headers[col_idx])
        r.font.name = 'Calibri'
        r.font.size = Pt(8.5)
        r.font.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

        # Value cell
        cell_v = stat_table.cell(1, col_idx)
        set_cell_background(cell_v, bg_colors[col_idx])
        set_cell_margins(cell_v, top=120, bottom=120, left=100, right=100)
        pv = cell_v.paragraphs[0]
        pv.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rv = pv.add_run(values[col_idx])
        rv.font.name = 'Calibri'
        rv.font.size = Pt(13)
        rv.font.bold = True
        rv.font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph() # Spacer

    # Section Heading
    tbl_heading_p = doc.add_paragraph()
    tbl_heading_p.add_run("Student Roster & Verification Log").font.bold = True

    # Main Attendance Table
    roster_table = doc.add_table(rows=1, cols=7)
    roster_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    col_widths = [Inches(0.4), Inches(1.1), Inches(1.8), Inches(0.9), Inches(0.9), Inches(1.0), Inches(1.0)]
    tbl_headers = ["#", "Student ID", "Full Name", "Class", "Status", "Time", "Scan Method"]

    hdr_cells = roster_table.rows[0].cells
    for i, title in enumerate(tbl_headers):
        hdr_cells[i].width = col_widths[i]
        set_cell_background(hdr_cells[i], "2563EB") # Royal Blue
        set_cell_margins(hdr_cells[i], top=90, bottom=90, left=100, right=100)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i in [0, 1, 3, 4, 5, 6] else WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(title)
        run.font.name = 'Calibri'
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)

    # Populate rows
    for idx, rec in enumerate(records, start=1):
        row_cells = roster_table.add_row().cells
        for i in range(7):
            row_cells[i].width = col_widths[i]
            set_cell_margins(row_cells[i], top=70, bottom=70, left=100, right=100)
            row_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        # Alternate row background
        row_bg = "FFFFFF" if idx % 2 != 0 else "F8FAFC"
        for c in row_cells:
            set_cell_background(c, row_bg)

        # 0: S.No
        p0 = row_cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.add_run(str(idx)).font.size = Pt(9)

        # 1: Student ID
        p1 = row_cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = p1.add_run(rec['student_id'])
        r1.font.size = Pt(9)
        r1.font.bold = True

        # 2: Name
        p2 = row_cells[2].paragraphs[0]
        r2 = p2.add_run(rec['name'])
        r2.font.size = Pt(9.5)

        # 3: Class & Section
        p3 = row_cells[3].paragraphs[0]
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sec = f"-{rec['section']}" if rec.get('section') else ""
        p3.add_run(f"{rec['student_class']}{sec}").font.size = Pt(9)

        # 4: Status (with color coding)
        p4 = row_cells[4].paragraphs[0]
        p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
        st = rec['attendance_status']
        r4 = p4.add_run(st)
        r4.font.size = Pt(9)
        r4.font.bold = True
        if st == 'Present':
            r4.font.color.rgb = RGBColor(16, 149, 93) # Emerald
        elif st == 'Late':
            r4.font.color.rgb = RGBColor(217, 119, 6) # Amber
        else:
            r4.font.color.rgb = RGBColor(225, 29, 72) # Rose

        # 5: Time
        p5 = row_cells[5].paragraphs[0]
        p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p5.add_run(rec.get('attendance_time', '-')).font.size = Pt(8.5)

        # 6: Scan Method
        p6 = row_cells[6].paragraphs[0]
        p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p6.add_run(rec.get('scan_method', '-')).font.size = Pt(8.5)

    doc.add_paragraph() # Spacer

    # Footer note & signature lines
    footer_p = doc.add_paragraph()
    footer_p.add_run(f"System Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Smart QR Code School Attendance System")
    footer_p.runs[0].font.size = Pt(8)
    footer_p.runs[0].font.color.rgb = RGBColor(148, 163, 184)

    sig_table = doc.add_table(rows=1, cols=2)
    sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    c0 = sig_table.cell(0, 0)
    c1 = sig_table.cell(0, 1)
    
    p_sig0 = c0.paragraphs[0]
    p_sig0.add_run("\n\n___________________________\nTeacher / Supervisor Signature").font.size = Pt(9)
    p_sig0.alignment = WD_ALIGN_PARAGRAPH.LEFT

    p_sig1 = c1.paragraphs[0]
    p_sig1.add_run("\n\n___________________________\nSchool Principal / Administrator").font.size = Pt(9)
    p_sig1.alignment = WD_ALIGN_PARAGRAPH.RIGHT

    # Save to BytesIO
    target_stream = BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    return target_stream
