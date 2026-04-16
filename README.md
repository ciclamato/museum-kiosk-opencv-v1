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
```bash
# Clone the repository
git clone <repository-url>
cd OPENCV

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Kiosk
```bash
# Fullscreen mode (default)
python main.py

# Windowed mode for development
python main.py --windowed --debug
```

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
