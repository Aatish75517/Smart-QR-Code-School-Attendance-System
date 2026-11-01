"""
scanner_opencv.py - Standalone Desktop Webcam Scanner using OpenCV
OpenCV library ke zariye camera se QR code scan karke attendance lagata hai.
"""

import cv2
import time
import requests

# Flask API ka URL jahan attendance bheji jati hai
API_URL = "http://127.0.0.1:5000/api/scan"

def start_scanner():
    print("=" * 50)
    print("  OPENCV QR CODE ATTENDANCE SCANNER")
    print("  Camera open ho raha hai... (Band karne ke liye 'q' dabayein)")
    print("=" * 50)

    # 1. Camera open karo (0 default webcam hai)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Camera open nahi ho saka. Webcam check karein.")
        return

    # 2. OpenCV ka built-in QR Code detector initialize karo
    detector = cv2.QRCodeDetector()

    last_scanned = ""
    last_time = 0
    feedback_text = "Show Student QR Badge to Camera"
    feedback_color = (255, 255, 255) # White

    while True:
        # Camera se frame read karo
        ret, frame = cap.read()
        if not ret:
            break

        # Mirror effect ke liye horizontally flip karo
        frame = cv2.flip(frame, 1)

        # 3. QR code detect aur decode karo
        data, bbox, _ = detector.detectAndDecode(frame)

        current_time = time.time()

        # Agar QR code mila aur wo pichle 4 seconds me scan nahi hua
        if data and (data != last_scanned or (current_time - last_time > 4)):
            last_scanned = data.strip()
            last_time = current_time

            print(f"[QR DETECTED] Student ID: {last_scanned}")

            # 4. Flask API ko request bhejo attendance mark karne ke liye
            try:
                response = requests.post(API_URL, json={'token': last_scanned, 'method': 'OpenCV Webcam'}, timeout=2)
                result = response.json()

                if result.get('success'):
                    std_name = result['student']['name']
                    feedback_text = f"SUCCESS: {std_name} Marked Present!"
                    feedback_color = (0, 255, 0) # Green (BGR)
                else:
                    feedback_text = result.get('message', 'Scan Failed')
                    feedback_color = (0, 165, 255) # Orange (BGR)

            except Exception as e:
                feedback_text = f"Server Error: Ensure Flask app is running"
                feedback_color = (0, 0, 255) # Red

            print(f" -> Result: {feedback_text}")

            # Detected QR code ke gird border draw karo
            if bbox is not None:
                pts = bbox.astype(int).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], True, feedback_color, 3)

        # Video frame ke upar status aur instructions likho
        cv2.rectangle(frame, (0, 0), (640, 50), (30, 30, 30), -1)
        cv2.putText(frame, feedback_text, (15, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, feedback_color, 2)
        cv2.putText(frame, "Press 'Q' to Exit", (15, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Window me display karo
        cv2.imshow("School Attendance - QR Scanner", frame)

        # 'q' dabane se window band ho jaye
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Camera release karo aur window band karo
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Scanner closed.")

if __name__ == '__main__':
    start_scanner()
