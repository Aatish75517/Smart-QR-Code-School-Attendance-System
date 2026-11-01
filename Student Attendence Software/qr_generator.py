"""
qr_generator.py - Simple QR Code Generation using Python qrcode Library
Yeh file student ke Student ID ka QR code generate karke static/qrcodes/ folder me save karti hai.
"""

import os
import qrcode

QR_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'qrcodes')

def generate_qr(student_id):
    """
    Student ID ka QR code image banata hai aur PNG file save karta hai.
    Example: 'STD-2026-101' -> static/qrcodes/STD-2026-101.png
    """
    os.makedirs(QR_FOLDER, exist_ok=True)

    # QR code create karna (simple aur standard tareeqa)
    qr_img = qrcode.make(student_id)

    # File path
    file_name = f"{student_id}.png"
    file_path = os.path.join(QR_FOLDER, file_name)

    # Save image
    qr_img.save(file_path)

    # Return relative URL
    return f"/static/qrcodes/{file_name}"
