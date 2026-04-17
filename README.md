# Museum Kiosk — Gesture-Controlled Content Viewer

A touchless, gesture-controlled interactive interface designed for museum exhibits. Users can browse videos, PDFs, and images using hand gestures, without physical contact with the screen.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)

## ✨ Features

- **Touchless Interaction**: Navigate content using intuitive hand gestures (Open Palm to select, Fist to go back, Swipe to browse).
- **Multi-Format Support**: Play videos, view high-quality PDFs, and browse images.
- **Museum-Ready**: Automatic screensaver mode, multilingual support (ES/EN), and high-performance rendering.
- **Modern UI**: Tokyo Night inspired aesthetic with smooth animations and "phantom trail" hand tracking.
- **Admin Panel**: Web-based interface to manage content and monitor kiosk status.

## 🛠️ Technology Stack

- **Computer Vision**: [OpenCV](https://opencv.org/) & [MediaPipe](https://mediapipe.dev/) for hand tracking and gesture recognition.
- **Graphics & UI**: [Pygame](https://www.pygame.org/) for the kiosk interface.
- **PDF Processing**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) for high-fidelity document rendering.
- **Management Panel**: [Flask](https://flask.palletsprojects.com/) for the web-based administration dashboard.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.8 or higher.
- A webcam or similar video input device.

### 2. Installation

#### Windows
The easiest way to install and run the project on Windows is by using the included batch scripts.

```bash
# Double-click install_requirements.bat
```

#### Linux / Raspberry Pi OS
On Raspberry Pi OS and other Debian-based systems, the project uses a local virtual environment in `./.venv`.

```bash
sudo apt update
sudo apt install -y python3-venv python3-full
chmod +x launcher.sh run_kiosk.sh run_admin.sh install_requirements.sh
./install_requirements.sh
```

### 3. Running the Kiosk

#### Windows
- **`launcher.bat`**: Recommended (all-in-one menu).
- **`run_kiosk.bat`**: Launch the main kiosk instantly.
- **`run_admin.bat`**: Open the web management panel.

#### Linux / Raspberry Pi OS
- **`./launcher.sh`**: Recommended (all-in-one menu).
- **`./run_kiosk.sh`**: Launch the main kiosk instantly.
- **`./run_admin.sh`**: Open the web management panel.

## 🖐️ Hand Gestures

| Gesture | Action | Description |
| :--- | :--- | :--- |
| **Open Palm** | Select / Click | Hold open palm over an item to select it. |
| **Fist** | Back / Close | Close hand into a fist to go back or close a viewer. |
| **Swipe Left/Right** | Navigate | Move hand quickly horizontally to scroll or change pages. |
| **Pinch** | Zoom | *Coming soon: Zoom functionality for images/PDFs.* |

## ⚙️ Configuration

Tunable parameters such as sensitivity, colors, and camera settings can be adjusted in `config.py`.

## 📦 Content Management

The kiosk follows a data-driven approach. Content is defined in `content/manifest.json`.

### manifest.json Structure
```json
{
  "content": [
    {
      "id": "unique-id",
      "title": "Display Title",
      "type": "video|pdf|image",
      "file": "relative/path/to/file",
      "thumbnail": "relative/path/to/thumbnail",
      "description": "Short description"
    }
  ]
}
```

You can manage this manually or use the built-in **Admin Panel** (`python main.py --admin`).

## 📂 Project Structure

- `core/`: Vision and gesture processing logic.
- `ui/`: Pygame rendering, screensaver, and overlay components.
- `admin/`: Flask web application for content management.
- `content/`: PDFs, videos, and images (automatically managed via admin panel).
- `assets/`: Fonts and static UI elements.

## 📄 License
This project is licensed under the MIT License.
