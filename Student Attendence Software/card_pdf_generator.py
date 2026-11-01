"""
card_pdf_generator.py - Generate pixel-perfect standard CR80 PVC Student ID Cards.
Standard CR80 size: 54mm x 85.6mm (Portrait) or 85.6mm x 54mm (Landscape).
"""

import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

# Exact CR80 standard dimensions
CR80_WIDTH = 54.0 * mm
CR80_HEIGHT = 85.6 * mm

# Color palette (Clean Academic Navy & Crisp White)
COLOR_NAVY = HexColor("#1e40af")
COLOR_NAVY_DARK = HexColor("#0f172a")
COLOR_NAVY_LIGHT = HexColor("#eff6ff")
COLOR_BLUE_BORDER = HexColor("#bfdbfe")
COLOR_BORDER = HexColor("#cbd5e1")
COLOR_BG_GRAY = HexColor("#f8fafc")
COLOR_FOOTER_BG = HexColor("#f1f5f9")
COLOR_TEXT_MAIN = HexColor("#1e293b")
COLOR_TEXT_MUTED = HexColor("#64748b")
COLOR_GREEN = HexColor("#15803d")
COLOR_WHITE = HexColor("#ffffff")
COLOR_CUT_LINE = HexColor("#94a3b8")

def draw_portrait_pvc_card(c, x, y, student, school_name, academic_year, qr_path):
    """
    Draws a single vertical CR80 PVC card (54mm x 85.6mm) at coordinate (x, y).
    Corner radius: 3.18mm (standard CR80).
    """
    w = CR80_WIDTH
    h = CR80_HEIGHT
    radius = 3.18 * mm

    c.saveState()

    # 1. Card Base Background & Outer Border
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)

    # 2. Header Bar (Top 13mm)
    header_h = 13.0 * mm
    header_y = y + h - header_h
    c.setFillColor(COLOR_NAVY)
    c.setStrokeColor(COLOR_NAVY)
    # Clip top corners
    path = c.beginPath()
    path.roundRect(x, y, w, h, radius)
    c.clipPath(path, stroke=0)

    c.rect(x, header_y, w, header_h, fill=1, stroke=0)

    # Header Text
    c.setFillColor(COLOR_WHITE)
    text_w = c.stringWidth(school_name.upper(), "Helvetica-Bold", 7.5)
    max_w = w - 4.0 * mm

    if text_w <= max_w:
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(x + w / 2.0, header_y + 7.5 * mm, school_name.upper())
        c.setFillColor(COLOR_BLUE_BORDER)
        c.setFont("Helvetica-Bold", 5.0)
        c.drawCentredString(x + w / 2.0, header_y + 3.0 * mm, "OFFICIAL STUDENT ID BADGE")
    else:
        # Split into 2 clean balanced lines
        words = school_name.upper().split()
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        c.setFont("Helvetica-Bold", 6.8)
        c.drawCentredString(x + w / 2.0, header_y + 8.8 * mm, line1)
        c.drawCentredString(x + w / 2.0, header_y + 5.5 * mm, line2)
        c.setFillColor(COLOR_BLUE_BORDER)
        c.setFont("Helvetica-Bold", 4.5)
        c.drawCentredString(x + w / 2.0, header_y + 2.2 * mm, "OFFICIAL STUDENT ID BADGE")

    # 3. Avatar Circle (Initials)
    avatar_radius = 8.5 * mm
    avatar_center_x = x + w / 2.0
    avatar_center_y = header_y - 10.5 * mm

    c.setFillColor(COLOR_NAVY_LIGHT)
    c.setStrokeColor(COLOR_BLUE_BORDER)
    c.setLineWidth(1.2)
    c.circle(avatar_center_x, avatar_center_y, avatar_radius, fill=1, stroke=1)

    # Avatar Initial letter
    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 12.0)
    initial = (student.get('name') or 'S')[0].upper()
    c.drawCentredString(avatar_center_x, avatar_center_y - 4.0, initial)

    # 4. Student Name
    name_y = avatar_center_y - avatar_radius - 4.2 * mm
    c.setFillColor(COLOR_NAVY_DARK)
    c.setFont("Helvetica-Bold", 8.5)
    name = student.get('name', 'Student Name')
    if len(name) > 20:
        name = name[:18] + '...'
    c.drawCentredString(x + w / 2.0, name_y, name)

    # 5. Student ID Badge
    id_y = name_y - 4.5 * mm
    c.setFillColor(COLOR_NAVY_LIGHT)
    c.setStrokeColor(COLOR_BLUE_BORDER)
    c.setLineWidth(0.5)
    id_w = 26.0 * mm
    id_h = 3.6 * mm
    c.roundRect(x + (w - id_w) / 2.0, id_y - 0.5 * mm, id_w, id_h, 1.5 * mm, fill=1, stroke=1)

    c.setFillColor(COLOR_NAVY)
    c.setFont("Courier-Bold", 6.8)
    c.drawCentredString(x + w / 2.0, id_y + 0.3 * mm, student.get('student_id', 'STD-000'))

    # 6. Details Grid Box
    info_box_y = id_y - 9.5 * mm
    info_box_w = w - 8.0 * mm
    info_box_h = 8.0 * mm
    info_box_x = x + 4.0 * mm

    c.setFillColor(COLOR_BG_GRAY)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(info_box_x, info_box_y, info_box_w, info_box_h, 1.5 * mm, fill=1, stroke=1)

    # 4 data points in 2 columns
    c.setFont("Helvetica-Bold", 4.5)
    c.setFillColor(COLOR_TEXT_MUTED)
    # Left column labels
    c.drawString(info_box_x + 2.0 * mm, info_box_y + 4.8 * mm, "CLASS")
    c.drawString(info_box_x + 2.0 * mm, info_box_y + 1.2 * mm, "SECTION")
    # Right column labels
    mid_x = info_box_x + info_box_w / 2.0
    c.drawString(mid_x + 1.5 * mm, info_box_y + 4.8 * mm, "YEAR")
    c.drawString(mid_x + 1.5 * mm, info_box_y + 1.2 * mm, "STATUS")

    # Values
    c.setFont("Helvetica-Bold", 5.2)
    c.setFillColor(COLOR_TEXT_MAIN)
    s_class = student.get('student_class', '')
    if len(s_class) > 8:
        s_class = s_class[:7] + '.'
    c.drawString(info_box_x + 11.5 * mm, info_box_y + 4.8 * mm, s_class)
    c.drawString(info_box_x + 11.5 * mm, info_box_y + 1.2 * mm, student.get('section', 'A') or 'A')

    c.drawString(mid_x + 11.5 * mm, info_box_y + 4.8 * mm, academic_year.split('-')[0].strip())
    c.setFillColor(COLOR_GREEN)
    c.drawString(mid_x + 11.5 * mm, info_box_y + 1.2 * mm, student.get('account_status', 'Active'))

    # 7. QR Code (Crisp vector image)
    qr_size = 21.0 * mm
    qr_x = x + (w - qr_size) / 2.0
    qr_y = info_box_y - qr_size - 1.2 * mm

    # QR background container
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(qr_x - 1.0 * mm, qr_y - 0.5 * mm, qr_size + 2.0 * mm, qr_size + 1.5 * mm, 1.2 * mm, fill=1, stroke=1)

    if qr_path and os.path.exists(qr_path):
        c.drawImage(qr_path, qr_x, qr_y + 0.2 * mm, width=qr_size, height=qr_size, preserveAspectRatio=True)

    # 8. Footer Strip
    footer_h = 4.2 * mm
    c.setFillColor(COLOR_FOOTER_BG)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.4)
    c.rect(x, y, w, footer_h, fill=1, stroke=0)
    c.line(x, y + footer_h, x + w, y + footer_h)

    c.setFillColor(COLOR_TEXT_MUTED)
    c.setFont("Helvetica", 4.5)
    c.drawCentredString(x + w / 2.0, y + 1.3 * mm, "Scan daily at school entrance checkpoint.")

    c.restoreState()


def draw_landscape_pvc_card(c, x, y, student, school_name, academic_year, qr_path):
    """
    Draws a single horizontal CR80 PVC card (85.6mm x 54mm) at coordinate (x, y).
    """
    w = CR80_HEIGHT  # 85.6mm
    h = CR80_WIDTH   # 54.0mm
    radius = 3.18 * mm

    c.saveState()

    # 1. Base Card
    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.6)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)

    # Clip for rounded header
    path = c.beginPath()
    path.roundRect(x, y, w, h, radius)
    c.clipPath(path, stroke=0)

    # 2. Header Bar
    header_h = 9.5 * mm
    header_y = y + h - header_h
    c.setFillColor(COLOR_NAVY)
    c.rect(x, header_y, w, header_h, fill=1, stroke=0)

    c.setFillColor(COLOR_WHITE)
    name_str = school_name.upper()
    font_sz = 8.0 if len(name_str) <= 28 else 6.8
    c.setFont("Helvetica-Bold", font_sz)
    c.drawString(x + 5.0 * mm, header_y + 4.8 * mm, name_str)

    c.setFillColor(COLOR_BLUE_BORDER)
    c.setFont("Helvetica-Bold", 5.2)
    c.drawString(x + 5.0 * mm, header_y + 1.8 * mm, "OFFICIAL STUDENT IDENTITY CARD")

    c.drawRightString(x + w - 5.0 * mm, header_y + 3.0 * mm, f"SESSION: {academic_year}")

    # 3. Left Section: Avatar + Name + Info
    avatar_radius = 8.0 * mm
    avatar_center_x = x + 12.0 * mm
    avatar_center_y = header_y - 11.0 * mm

    c.setFillColor(COLOR_NAVY_LIGHT)
    c.setStrokeColor(COLOR_BLUE_BORDER)
    c.setLineWidth(1.0)
    c.circle(avatar_center_x, avatar_center_y, avatar_radius, fill=1, stroke=1)

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 11.0)
    initial = (student.get('name') or 'S')[0].upper()
    c.drawCentredString(avatar_center_x, avatar_center_y - 3.8, initial)

    # Student Name beside avatar
    info_left_x = avatar_center_x + avatar_radius + 4.0 * mm
    c.setFillColor(COLOR_NAVY_DARK)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(info_left_x, avatar_center_y + 2.0 * mm, student.get('name', 'Student Name'))

    # Student ID Badge
    id_w = 26.0 * mm
    id_h = 3.8 * mm
    c.setFillColor(COLOR_NAVY_LIGHT)
    c.setStrokeColor(COLOR_BLUE_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(info_left_x, avatar_center_y - 3.2 * mm, id_w, id_h, 1.5 * mm, fill=1, stroke=1)
    c.setFillColor(COLOR_NAVY)
    c.setFont("Courier-Bold", 7.0)
    c.drawString(info_left_x + 2.0 * mm, avatar_center_y - 1.8 * mm, student.get('student_id', 'STD-000'))

    # Details Grid below avatar
    grid_y = avatar_center_y - avatar_radius - 7.5 * mm
    grid_w = 52.0 * mm
    grid_h = 8.5 * mm
    grid_x = x + 5.0 * mm

    c.setFillColor(COLOR_BG_GRAY)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(grid_x, grid_y, grid_w, grid_h, 1.5 * mm, fill=1, stroke=1)

    c.setFont("Helvetica-Bold", 4.8)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(grid_x + 2.0 * mm, grid_y + 5.0 * mm, "CLASS:")
    c.drawString(grid_x + 2.0 * mm, grid_y + 1.5 * mm, "SECTION:")
    c.drawString(grid_x + 27.0 * mm, grid_y + 5.0 * mm, "GUARDIAN:")
    c.drawString(grid_x + 27.0 * mm, grid_y + 1.5 * mm, "STATUS:")

    c.setFont("Helvetica-Bold", 5.2)
    c.setFillColor(COLOR_TEXT_MAIN)
    c.drawString(grid_x + 10.0 * mm, grid_y + 5.0 * mm, student.get('student_class', ''))
    c.drawString(grid_x + 10.0 * mm, grid_y + 1.5 * mm, student.get('section', 'A') or 'A')

    phone = student.get('guardian_phone', '') or 'N/A'
    if len(phone) > 11:
        phone = phone[:11]
    c.drawString(grid_x + 37.0 * mm, grid_y + 5.0 * mm, phone)
    c.setFillColor(COLOR_GREEN)
    c.drawString(grid_x + 37.0 * mm, grid_y + 1.5 * mm, student.get('account_status', 'Active'))

    # 4. Right Section: QR Code
    qr_size = 24.0 * mm
    qr_x = x + w - qr_size - 6.0 * mm
    qr_y = y + 7.5 * mm

    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.roundRect(qr_x - 1.0 * mm, qr_y - 0.5 * mm, qr_size + 2.0 * mm, qr_size + 1.5 * mm, 1.5 * mm, fill=1, stroke=1)

    if qr_path and os.path.exists(qr_path):
        c.drawImage(qr_path, qr_x, qr_y + 0.3 * mm, width=qr_size, height=qr_size, preserveAspectRatio=True)

    # 5. Footer Strip
    footer_h = 4.0 * mm
    c.setFillColor(COLOR_FOOTER_BG)
    c.rect(x, y, w, footer_h, fill=1, stroke=0)
    c.setStrokeColor(COLOR_BORDER)
    c.line(x, y + footer_h, x + w, y + footer_h)

    c.setFillColor(COLOR_TEXT_MUTED)
    c.setFont("Helvetica", 4.5)
    c.drawString(x + 5.0 * mm, y + 1.2 * mm, f"Property of {school_name} • Non-transferable")
    c.drawRightString(x + w - 5.0 * mm, y + 1.2 * mm, "Scan for Attendance Checkpoint")

    c.restoreState()


def draw_cut_guidelines(c, x, y, width, height, label="Standard CR80 PVC Size (54mm × 85.6mm)"):
    """
    Draws neat dashed cut lines around the card with scissors markers.
    """
    c.saveState()
    c.setStrokeColor(COLOR_CUT_LINE)
    c.setLineWidth(0.6)
    c.setDash([2.0 * mm, 2.0 * mm], 0)

    # Dotted rectangle slightly outside the card
    offset = 1.0 * mm
    c.rect(x - offset, y - offset, width + 2 * offset, height + 2 * offset, fill=0, stroke=1)

    # Small scissor / cut text
    c.setFont("Helvetica", 5.5)
    c.setFillColor(COLOR_TEXT_MUTED)
    c.drawString(x - offset, y - offset - 3.2 * mm, f"[ CUT LINE ] {label}")
    c.restoreState()


def generate_single_card_pdf(student, school_name, academic_year, qr_path, orientation='portrait', paper_size='A4'):
    """
    Generates a PDF stream for a single student ID card.
    paper_size can be 'A4' (print-ready with cut marks) or 'CR80' (exact card size for PVC printer).
    """
    buf = io.BytesIO()

    if paper_size == 'CR80':
        # Exact PVC card canvas size
        if orientation == 'landscape':
            page_w, page_h = CR80_HEIGHT, CR80_WIDTH
            c = canvas.Canvas(buf, pagesize=(page_w, page_h))
            draw_landscape_pvc_card(c, 0, 0, student, school_name, academic_year, qr_path)
        else:
            page_w, page_h = CR80_WIDTH, CR80_HEIGHT
            c = canvas.Canvas(buf, pagesize=(page_w, page_h))
            draw_portrait_pvc_card(c, 0, 0, student, school_name, academic_year, qr_path)
        c.showPage()
        c.save()
    else:
        # Standard A4 Sheet (210mm x 297mm)
        page_w, page_h = A4
        c = canvas.Canvas(buf, pagesize=A4)

        # Header instructions on A4 page
        c.setFillColor(COLOR_NAVY)
        c.setFont("Helvetica-Bold", 14.0)
        c.drawString(20.0 * mm, page_h - 22.0 * mm, f"{school_name} - Official Student ID Card")

        c.setFillColor(COLOR_TEXT_MUTED)
        c.setFont("Helvetica", 9.0)
        c.drawString(20.0 * mm, page_h - 28.0 * mm, "Print Guidelines: Print at 100% scale (Do not scale / 'Actual Size').")
        c.drawString(20.0 * mm, page_h - 33.0 * mm, "Cut along the dashed border to fit any standard CR80 PVC card holder or badge pouch.")

        # Separator line
        c.setStrokeColor(COLOR_BORDER)
        c.setLineWidth(0.8)
        c.line(20.0 * mm, page_h - 36.0 * mm, page_w - 20.0 * mm, page_h - 36.0 * mm)

        # Center the card on the page
        if orientation == 'landscape':
            card_w = CR80_HEIGHT
            card_h = CR80_WIDTH
            card_x = (page_w - card_w) / 2.0
            card_y = page_h - 45.0 * mm - card_h
            draw_cut_guidelines(c, card_x, card_y, card_w, card_h, "CR80 PVC Size: 85.6mm × 54mm")
            draw_landscape_pvc_card(c, card_x, card_y, student, school_name, academic_year, qr_path)
        else:
            card_w = CR80_WIDTH
            card_h = CR80_HEIGHT
            card_x = (page_w - card_w) / 2.0
            card_y = page_h - 45.0 * mm - card_h
            draw_cut_guidelines(c, card_x, card_y, card_w, card_h, "CR80 PVC Size: 54mm × 85.6mm")
            draw_portrait_pvc_card(c, card_x, card_y, student, school_name, academic_year, qr_path)

        # Card Back / Reverse side preview below it for double-sided print!
        back_y = card_y - card_h - 15.0 * mm
        if back_y > 20.0 * mm:
            draw_card_back(c, card_x, back_y, card_w, card_h, school_name, academic_year, orientation)
            draw_cut_guidelines(c, card_x, back_y, card_w, card_h, "CARD BACK (Optional Double-Sided Print)")

        c.showPage()
        c.save()

    buf.seek(0)
    return buf


def draw_card_back(c, x, y, width, height, school_name, academic_year, orientation):
    """Draws an authentic school card back with terms and emergency contacts."""
    c.saveState()
    radius = 3.18 * mm

    c.setFillColor(COLOR_WHITE)
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.6)
    c.roundRect(x, y, width, height, radius, fill=1, stroke=1)

    c.setFillColor(COLOR_NAVY)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(x + width / 2.0, y + height - 8.0 * mm, "STUDENT CARD RULES & CONDITIONS")

    c.setFillColor(COLOR_TEXT_MUTED)
    c.setFont("Helvetica", 5.5)
    lines = [
        "1. This card must be worn or carried at all times on school premises.",
        "2. Required for daily electronic QR attendance marking.",
        "3. Non-transferable. Loss must be reported to the office immediately.",
        "4. If found, please return to the school administration office."
    ]
    cur_y = y + height - 13.0 * mm
    for line in lines:
        c.drawString(x + 4.0 * mm, cur_y, line)
        cur_y -= 4.0 * mm

    # Principal Signature Box
    sig_w = 28.0 * mm
    sig_x = x + width - sig_w - 4.0 * mm
    c.setStrokeColor(COLOR_BORDER)
    c.setLineWidth(0.5)
    c.line(sig_x, y + 8.0 * mm, sig_x + sig_w, y + 8.0 * mm)

    c.setFillColor(COLOR_TEXT_MUTED)
    c.setFont("Helvetica-Bold", 5.2)
    c.drawCentredString(sig_x + sig_w / 2.0, y + 5.0 * mm, "Authorized Signature")

    c.restoreState()


def generate_bulk_cards_pdf(students, school_name, academic_year, qr_dir, orientation='portrait'):
    """
    Generates an A4 batch PDF sheet with multiple CR80 PVC cards per page.
    Portrait: 8 cards per A4 page (2 columns x 4 rows).
    Landscape: 8 cards per A4 page (2 columns x 4 rows).
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    page_w, page_h = A4

    margin_x = 14.0 * mm
    margin_top = 18.0 * mm

    if orientation == 'landscape':
        card_w = CR80_HEIGHT  # 85.6mm
        card_h = CR80_WIDTH   # 54.0mm
        cols = 2
        rows = 4
        gap_x = 10.0 * mm
        gap_y = 7.0 * mm
    else:
        card_w = CR80_WIDTH   # 54.0mm
        card_h = CR80_HEIGHT  # 85.6mm
        cols = 3
        rows = 3
        gap_x = 8.0 * mm
        gap_y = 6.0 * mm

    cards_per_page = cols * rows

    for idx, student in enumerate(students):
        page_idx = idx % cards_per_page
        if idx > 0 and page_idx == 0:
            c.showPage()

        # Page header
        if page_idx == 0:
            c.saveState()
            c.setFillColor(COLOR_NAVY)
            c.setFont("Helvetica-Bold", 10.0)
            page_num = (idx // cards_per_page) + 1
            total_pages = ((len(students) - 1) // cards_per_page) + 1
            c.drawString(margin_x, page_h - 12.0 * mm, f"{school_name} - Student ID Badges (Page {page_num} of {total_pages})")
            c.setFillColor(COLOR_TEXT_MUTED)
            c.setFont("Helvetica", 7.0)
            c.drawRightString(page_w - margin_x, page_h - 12.0 * mm, "Standard CR80 PVC Size (Cut along lines)")
            c.restoreState()

        col = page_idx % cols
        row = page_idx // cols

        card_x = margin_x + col * (card_w + gap_x)
        card_y = page_h - margin_top - (row + 1) * card_h - row * gap_y

        qr_path = os.path.join(qr_dir, f"{student.get('student_id')}.png")

        # Draw cut guidelines
        draw_cut_guidelines(c, card_x, card_y, card_w, card_h, f"{student.get('student_id')}")

        # Draw card
        if orientation == 'landscape':
            draw_landscape_pvc_card(c, card_x, card_y, student, school_name, academic_year, qr_path)
        else:
            draw_portrait_pvc_card(c, card_x, card_y, student, school_name, academic_year, qr_path)

    c.showPage()
    c.save()

    buf.seek(0)
    return buf
