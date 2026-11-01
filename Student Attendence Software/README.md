# Smart QR Code-Based School Attendance System

A web-based school attendance management system built with Python, Flask, SQLite, HTML, CSS, and JavaScript. It helps an administrator manage student records, generate student QR codes, record attendance, and prepare reports.

## Features

- Admin login and session-based access
- Dashboard with attendance statistics
- Add, view, search, update, and delete student records
- Generate QR codes for student IDs
- Scan QR codes using a browser camera
- Optional desktop webcam scanner using OpenCV
- Record and view daily attendance
- Export attendance reports to Microsoft Word and PDF
- Generate individual and bulk student ID cards
- SQLite database for local data storage
- Responsive interface with CSS and JavaScript

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language and application logic |
| Flask | Python web framework; handles routes, requests, sessions, and page rendering |
| SQLite | Stores student, administrator, settings, and attendance data |
| HTML5 | Defines the web pages and forms |
| CSS3 | Styles the interface, layout, and responsive design |
| JavaScript | Adds interactive features to the web interface |
| Bootstrap | Provides common interface styles and responsive layout components |
| Bootstrap Icons | Supplies icons used in the interface |
| Chart.js | Displays charts and attendance statistics where used |
| html5-qrcode | Reads QR codes through a supported browser camera |
| OpenCV | Provides the optional desktop webcam QR scanner |
| Microsoft Word / PDF | Report and student ID-card output formats |

## Python Libraries and Their Uses

The Python dependencies are listed in `requirements.txt`.

| Library / Package | Import name (if different) | Why it is used |
|---|---|---|
| `Flask` | `flask` | Runs the web application, handles URLs, forms, sessions, templates, and responses |
| `qrcode` | `qrcode` | Creates QR-code images for student IDs |
| `Pillow` | `PIL` | Image-processing library used by QR/image-related functionality |
| `opencv-python` | `cv2` | Opens a webcam and detects/decodes QR codes in the desktop scanner |
| `python-docx` | `docx` | Creates downloadable Microsoft Word attendance reports |
| `lxml` | `lxml` | XML processing support used by document-generation functionality |
| `numpy` | `numpy` | Numerical and array support, including computer-vision operations |
| `requests` | `requests` | Sends scanned QR-code data from the desktop scanner to the Flask API |
| `reportlab` | `reportlab` | Generates PDF documents, including student ID cards |

Python's built-in modules are also used; these do **not** need to be installed separately:

- `os` — file and folder paths
- `csv` — CSV report handling
- `io` — in-memory file data
- `datetime` — dates and times
- `sqlite3` — SQLite database access
- `time` — scanner timing
- Flask modules such as `session`, `request`, `render_template`, `redirect`, `url_for`, `flash`, `jsonify`, and `send_file`

The frontend also includes local vendor files under `static/vendor/`, such as Bootstrap, Bootstrap Icons, Chart.js, and `html5-qrcode`. These are JavaScript/CSS assets, not Python packages.

## Project Structure

```text
Student Attendence Software/
├── app.py                    # Main Flask application and web routes
├── database.py                # Database setup and database helper functions
├── qr_generator.py            # Creates student QR-code images
├── scanner_opencv.py          # Optional desktop webcam QR scanner
├── docx_report.py             # Creates Word attendance reports
├── card_pdf_generator.py      # Creates PDF student ID cards
├── sample_data.py             # Adds sample data (if needed)
├── test_app.py                # Automated application tests
├── requirements.txt            # Required Python packages
├── attendance.db               # SQLite database file
├── run.bat                     # Windows launch script
├── templates/                  # HTML templates
├── static/
│   ├── css/                    # Stylesheets
│   ├── js/                     # Frontend JavaScript
│   ├── img/                    # Images used by the interface
│   ├── qrcodes/                # Generated QR-code images
│   └── vendor/                 # Local frontend libraries
└── README.md                   # Project documentation
```

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer recommended
- A modern web browser
- A webcam for camera-based QR scanning
- Internet is not normally required to run the local app if the included frontend vendor files are used

## Installation and Setup (Windows)

1. Download or extract the project ZIP file.
2. Open Command Prompt or PowerShell in the project folder (the folder containing `app.py`).
3. (Recommended) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, you can use Command Prompt instead:

   ```bat
   .venv\Scripts\activate.bat
   ```

4. Install the required packages:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

5. Start the application:

   ```powershell
   python app.py
   ```

6. Open this address in your browser:

   `http://127.0.0.1:5000`

You can also try `run.bat` if it is configured for your local Python installation.

## QR Scanning

### Browser scanner

1. Start the Flask application.
2. Sign in and open the scanner page.
3. Allow camera permission in the browser when prompted.
4. Present a student's generated QR code to the camera.

Camera access generally works on `localhost` or a secure HTTPS site. If the browser camera does not start, check browser permissions and try `http://127.0.0.1:5000`.

### Optional desktop OpenCV scanner

Keep the Flask application running in one terminal. In a second terminal, run:

```powershell
python scanner_opencv.py
```

The desktop scanner sends scanned QR data to the local Flask API at `http://127.0.0.1:5000/api/scan`. Press `Q` in the scanner window to exit.

## Reports and ID Cards

The application includes code for generating attendance reports and student ID cards. Word reports use `python-docx`; PDF output uses `reportlab`. The available options depend on the relevant page and features enabled in the current project version.

## Database

The project uses SQLite, with its database file named `attendance.db`. SQLite is included with standard Python installations, so a separate database server is not required.

If you want to reset or recreate data, back up `attendance.db` first. Only run sample-data scripts when you intend to add or refresh demonstration records.

## Troubleshooting

- **`ModuleNotFoundError`**: Activate the intended Python environment and run `python -m pip install -r requirements.txt`.
- **Port 5000 is already in use**: Close the other process using that port or configure the Flask app to use another port.
- **Webcam not opening**: Close other applications using the camera and check operating-system camera permissions.
- **Browser scanner cannot access the camera**: Allow camera permission and use `localhost` or HTTPS.
- **PDF or Word export fails**: Confirm that `reportlab` and `python-docx` were installed successfully.

## Security Notes

- Change any default administrator credentials before using real student data.
- Do not publish a database containing real student records.
- For a public or production deployment, configure a strong secret key, secure session settings, and appropriate access controls.
- This project is intended as a school project/local application; review and strengthen its security before using it in a real school environment.

## Author

**Aatish Aakash**

## License

No license has been specified. Add a license file if you intend to allow others to reuse or distribute this project.
