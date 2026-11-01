/**
 * scanner.js - Bulletproof Webcam QR Scanner Logic
 * Real-time continuous camera decoding with image file upload fallback and manual entry.
 */

let html5QrCode = null;
let isCameraRunning = false;
let lastScannedCode = "";
let lastScannedTime = 0;

document.addEventListener('DOMContentLoaded', () => {
    initScanner();
    initFileUploadScanner();
    initManualEntry();
});

// ==================== WEBCAM SCANNER ====================

async function initScanner() {
    const readerElement = document.getElementById('reader');
    if (!readerElement) return;

    html5QrCode = new Html5Qrcode("reader");

    const statusEl = document.getElementById('scannerStatus');
    statusEl.innerHTML = '<span class="text-primary"><span class="spinner-border spinner-border-sm me-2"></span>Requesting camera access...</span>';

    // Start with default camera (front/user facing or first available)
    startCamera({ facingMode: "user" });

    // Populate camera list for switching
    try {
        const cameras = await Html5Qrcode.getCameras();
        const cameraSelect = document.getElementById('cameraSelect');

        if (cameras && cameras.length > 0) {
            cameraSelect.innerHTML = '';
            cameras.forEach((cam, index) => {
                const opt = document.createElement('option');
                opt.value = cam.id;
                opt.textContent = cam.label || `Camera ${index + 1}`;
                cameraSelect.appendChild(opt);
            });

            cameraSelect.addEventListener('change', (e) => {
                if (e.target.value) {
                    startCamera(e.target.value);
                }
            });
        } else {
            cameraSelect.innerHTML = '<option value="">Default Webcam</option>';
        }
    } catch (e) {
        console.log("Camera enumeration note:", e);
    }
}

async function startCamera(cameraConfig) {
    if (isCameraRunning && html5QrCode) {
        try {
            await html5QrCode.stop();
            isCameraRunning = false;
        } catch (e) {
            console.error("Stop camera error:", e);
        }
    }

    const statusEl = document.getElementById('scannerStatus');

    const scanConfig = {
        fps: 15,
        // Scan full frame for maximum detection sensitivity
        qrbox: (viewfinderWidth, viewfinderHeight) => {
            const edge = Math.min(viewfinderWidth, viewfinderHeight);
            return {
                width: Math.floor(edge * 0.85),
                height: Math.floor(edge * 0.85)
            };
        },
        aspectRatio: 1.0,
        experimentalFeatures: {
            useBarCodeDetectorIfSupported: true
        }
    };

    try {
        await html5QrCode.start(
            cameraConfig,
            scanConfig,
            onCodeScanned,
            onScanFrameError
        );

        isCameraRunning = true;
        statusEl.innerHTML = '<span class="text-success fw-semibold"><i class="bi bi-camera-video-fill me-1"></i> Camera is LIVE. Hold student QR badge to lens.</span>';

        // Update toggle button
        const toggleBtn = document.getElementById('toggleCameraBtn');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-stop-circle me-1"></i> Stop Camera';
            toggleBtn.className = 'btn btn-outline-danger btn-sm';
        }

    } catch (err) {
        console.error("Start camera failed:", err);
        isCameraRunning = false;
        statusEl.innerHTML = `
            <div class="text-danger small">
                <i class="bi bi-exclamation-triangle-fill me-1"></i> 
                <strong>Camera not started:</strong> ${err.message || err}.
                <br>Please make sure your browser has permission to access the webcam, or use the <strong>"Upload QR Image"</strong> or <strong>"Manual Entry"</strong> options below.
            </div>
        `;

        const toggleBtn = document.getElementById('toggleCameraBtn');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i> Start Camera';
            toggleBtn.className = 'btn btn-outline-primary btn-sm';
        }
    }
}

async function toggleCamera() {
    const toggleBtn = document.getElementById('toggleCameraBtn');
    if (isCameraRunning) {
        await html5QrCode.stop();
        isCameraRunning = false;
        document.getElementById('scannerStatus').innerHTML = '<span class="text-muted"><i class="bi bi-camera-video-off me-1"></i> Camera paused.</span>';
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="bi bi-play-circle me-1"></i> Start Camera';
            toggleBtn.className = 'btn btn-outline-primary btn-sm';
        }
    } else {
        const cameraSelect = document.getElementById('cameraSelect');
        const camId = cameraSelect && cameraSelect.value ? cameraSelect.value : { facingMode: "user" };
        startCamera(camId);
    }
}

function onScanFrameError(error) {
    // Frames without QR code are normal, do not spam console
}

// ==================== ON QR CODE DETECTED ====================

async function onCodeScanned(decodedText) {
    const now = Date.now();
    const cleanCode = decodedText.trim();

    // 4-second cooldown for the same code to prevent spamming
    if (cleanCode === lastScannedCode && (now - lastScannedTime < 4000)) {
        return;
    }

    lastScannedCode = cleanCode;
    lastScannedTime = now;

    console.log("QR Code Decoded:", cleanCode);

    // Send to Flask API
    await submitAttendance(cleanCode, 'QR Camera');
}

// ==================== SUBMIT TO FLASK API ====================

async function submitAttendance(token, method) {
    const resultBox = document.getElementById('scanResult');
    resultBox.innerHTML = `
        <div class="p-3 bg-light rounded text-center text-muted">
            <span class="spinner-border spinner-border-sm me-2 text-primary"></span>
            Verifying <strong>${token}</strong> in database...
        </div>
    `;

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token, method: method })
        });

        const data = await response.json();

        if (data.success) {
            playBeep('success');
            const std = data.student || {};
            const rec = data.record || {};

            resultBox.innerHTML = `
                <div class="scan-alert scan-alert-success shadow-sm">
                    <i class="bi bi-check-circle-fill fs-2 text-success"></i>
                    <div>
                        <div class="fw-bold fs-6">${data.message}</div>
                        <div class="small text-secondary">
                            <strong>${std.name}</strong> (<span class="font-monospace text-primary">${std.student_id}</span>) &bull; 
                            Class: <strong>${std.student_class} (${std.section || 'A'})</strong> &bull; 
                            Time: <strong>${rec.attendance_time}</strong>
                        </div>
                    </div>
                </div>
            `;
            prependToLiveTable(std, rec);

        } else if (data.status === 'ALREADY_RECORDED') {
            playBeep('warning');
            const std = data.student || {};

            resultBox.innerHTML = `
                <div class="scan-alert scan-alert-warning shadow-sm">
                    <i class="bi bi-exclamation-triangle-fill fs-2 text-warning"></i>
                    <div>
                        <div class="fw-bold fs-6">Already Marked Today!</div>
                        <div class="small">${data.message}</div>
                        <div class="small text-muted mt-1">Student: <strong>${std.name}</strong> (${std.student_id})</div>
                    </div>
                </div>
            `;

        } else {
            playBeep('error');
            resultBox.innerHTML = `
                <div class="scan-alert scan-alert-error shadow-sm">
                    <i class="bi bi-x-circle-fill fs-2 text-danger"></i>
                    <div>
                        <div class="fw-bold fs-6">Attendance Not Recorded</div>
                        <div class="small">${data.message}</div>
                    </div>
                </div>
            `;
        }

    } catch (err) {
        console.error("API error:", err);
        playBeep('error');
        resultBox.innerHTML = `
            <div class="scan-alert scan-alert-error">
                <i class="bi bi-wifi-off fs-3 text-danger"></i>
                <div>
                    <div class="fw-bold">Connection Error</div>
                    <div class="small">Could not reach the server at /api/scan.</div>
                </div>
            </div>
        `;
    }
}

// ==================== FILE UPLOAD SCANNER FALLBACK ====================

function initFileUploadScanner() {
    const fileInput = document.getElementById('qrFileInput');
    if (!fileInput) return;

    fileInput.addEventListener('change', async (e) => {
        if (!e.target.files || e.target.files.length === 0) return;
        const file = e.target.files[0];

        const resultBox = document.getElementById('scanResult');
        resultBox.innerHTML = `
            <div class="p-3 bg-light rounded text-center text-muted">
                <span class="spinner-border spinner-border-sm me-2 text-primary"></span>
                Scanning uploaded image for QR code...
            </div>
        `;

        try {
            const fileScanner = new Html5Qrcode("reader");
            const decodedText = await fileScanner.scanFile(file, true);
            fileInput.value = '';
            await submitAttendance(decodedText, 'Image File');
        } catch (err) {
            console.error("File scan failed:", err);
            fileInput.value = '';
            playBeep('error');
            resultBox.innerHTML = `
                <div class="scan-alert scan-alert-error">
                    <i class="bi bi-file-earmark-x fs-2 text-danger"></i>
                    <div>
                        <div class="fw-bold">No QR Code Found in Image</div>
                        <div class="small">Please make sure the uploaded image clearly shows the student QR code badge.</div>
                    </div>
                </div>
            `;
        }
    });
}

// ==================== MANUAL ID ENTRY ====================

function initManualEntry() {
    const form = document.getElementById('manualScanForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('manualIdInput');
        const studentId = input.value.trim();
        if (studentId) {
            await submitAttendance(studentId, 'Manual Entry');
            input.value = '';
        }
    });
}

// ==================== LIVE ROSTER UPDATE ====================

function prependToLiveTable(std, rec) {
    const tableBody = document.getElementById('liveRecentScans');
    if (!tableBody) return;

    const noScans = document.getElementById('noScansRow');
    if (noScans) noScans.remove();

    const row = document.createElement('tr');
    const badgeClass = rec.attendance_status === 'Late' ? 'status-late' : 'status-present';

    row.innerHTML = `
        <td>
            <strong>${std.name}</strong>
            <div class="text-muted font-monospace" style="font-size: 11px;">${std.student_id}</div>
        </td>
        <td>${std.student_class} (${std.section || 'A'})</td>
        <td>${rec.attendance_time}</td>
        <td><span class="status-badge ${badgeClass}">${rec.attendance_status}</span></td>
    `;

    tableBody.prepend(row);
}
