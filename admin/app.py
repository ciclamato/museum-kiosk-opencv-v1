"""
Museum Kiosk Lite — Flask Admin Panel
Video-only content management. Upload videos, set overlay text, reorder.
"""
import json
import os
import sys
import uuid

from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
app.secret_key = config.ADMIN_SECRET_KEY

ALLOWED_EXTENSIONS = {"mp4", "avi", "mkv", "webm", "mov", "m4v", "pdf"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_manifest():
    if not os.path.exists(config.MANIFEST_PATH):
        return {"content": []}
    with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Normalize
    content = data.get("content", [])
    for i, item in enumerate(content):
        item.setdefault("sort_order", i + 1)
        item.setdefault("enabled", True)
        item.setdefault("overlay_text", "")
        item.setdefault("title", "")
        if item.get("file", "").lower().endswith(".pdf"):
            item.setdefault("type", "pdf")
        else:
            item.setdefault("type", "video")
    content.sort(key=lambda x: (x.get("sort_order", 0), x.get("title", "")))
    return {"content": content}


def save_manifest(data):
    os.makedirs(os.path.dirname(config.MANIFEST_PATH), exist_ok=True)
    with open(config.MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _auto_thumbnail(video_path):
    """Extract first frame as thumbnail."""
    thumb_dir = os.path.join(config.CONTENT_DIR, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(video_path))[0]
    thumb_path = os.path.join(thumb_dir, f"{basename}.jpg")

    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        if ret:
            h, w = frame.shape[:2]
            scale = 300 / max(w, h)
            thumb = cv2.resize(frame, (int(w * scale), int(h * scale)))
            cv2.imwrite(thumb_path, thumb)
        cap.release()
        return f"thumbnails/{basename}.jpg"
    except Exception:
        return ""


@app.route("/")
def index():
    data = load_manifest()
    return render_template("index.html", content=data.get("content", []))


@app.route("/add", methods=["GET", "POST"])
def add_content():
    if request.method == "POST":
        data = load_manifest()
        content = data.get("content", [])

        title = request.form.get("title", "").strip()
        overlay_text = request.form.get("overlay_text", "").strip()
        enabled = request.form.get("enabled") == "on"

        file = request.files.get("file")
        if not file or not file.filename:
            flash("No se seleccionó archivo", "error")
            return redirect(url_for("add_content"))

        if not allowed_file(file.filename):
            flash("Solo se permiten archivos de video (mp4, avi, mkv) o PDF", "error")
            return redirect(url_for("add_content"))

        if not title:
            title = os.path.splitext(file.filename)[0]

        filename = secure_filename(file.filename)
        is_pdf = filename.lower().endswith(".pdf")
        subfolder = "pdfs" if is_pdf else "videos"
        target_dir = os.path.join(config.CONTENT_DIR, subfolder)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)

        thumb_rel = ""
        if not is_pdf:
            thumb_rel = _auto_thumbnail(file_path)

        sort_order = max([item.get("sort_order", 0) for item in content], default=0) + 1

        entry = {
            "id": f"item-{uuid.uuid4().hex[:8]}",
            "title": title,
            "type": "pdf" if is_pdf else "video",
            "file": f"{subfolder}/{filename}",
            "thumbnail": thumb_rel,
            "overlay_text": overlay_text,
            "sort_order": sort_order,
            "enabled": enabled,
        }

        content.append(entry)
        data["content"] = content
        save_manifest(data)

        flash(f"Video agregado: {title}", "success")
        return redirect(url_for("index"))

    return render_template("add.html")


@app.route("/edit/<content_id>", methods=["GET", "POST"])
def edit_content(content_id):
    data = load_manifest()
    item = next((c for c in data["content"] if c["id"] == content_id), None)

    if item is None:
        flash("Video no encontrado", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        item["title"] = request.form.get("title", item["title"]).strip()
        item["overlay_text"] = request.form.get("overlay_text", "").strip()
        item["enabled"] = request.form.get("enabled") == "on"
        save_manifest(data)
        flash("Video actualizado", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", item=item)


@app.route("/move/<content_id>/<direction>", methods=["POST"])
def move_content(content_id, direction):
    data = load_manifest()
    content = data.get("content", [])

    idx = next((i for i, c in enumerate(content) if c["id"] == content_id), None)
    if idx is None:
        flash("Video no encontrado", "error")
        return redirect(url_for("index"))

    if direction == "up" and idx > 0:
        content[idx], content[idx - 1] = content[idx - 1], content[idx]
    elif direction == "down" and idx < len(content) - 1:
        content[idx], content[idx + 1] = content[idx + 1], content[idx]

    # Renumber
    for i, item in enumerate(content):
        item["sort_order"] = i + 1

    data["content"] = content
    save_manifest(data)
    return redirect(url_for("index"))


@app.route("/toggle/<content_id>", methods=["POST"])
def toggle_content(content_id):
    data = load_manifest()
    item = next((c for c in data["content"] if c["id"] == content_id), None)
    if item:
        item["enabled"] = not item.get("enabled", True)
        save_manifest(data)
    return redirect(url_for("index"))


@app.route("/delete/<content_id>", methods=["POST"])
def delete_content(content_id):
    data = load_manifest()
    item = next((c for c in data["content"] if c["id"] == content_id), None)

    if item:
        file_path = os.path.join(config.CONTENT_DIR, item.get("file", ""))
        if os.path.exists(file_path):
            os.remove(file_path)

        thumb_path = os.path.join(config.CONTENT_DIR, item.get("thumbnail", ""))
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        data["content"] = [c for c in data["content"] if c["id"] != content_id]
        # Renumber
        for i, c in enumerate(data["content"]):
            c["sort_order"] = i + 1
        save_manifest(data)
        flash("Video eliminado", "success")
    else:
        flash("Video no encontrado", "error")

    return redirect(url_for("index"))


@app.route("/content-file/<path:filepath>")
def serve_content(filepath):
    return send_from_directory(config.CONTENT_DIR, filepath)


def run_admin():
    print("\n  [ADMIN] Museo Kiosk Lite — Panel de Administración")
    print(f"  [ADMIN] http://localhost:{config.ADMIN_PORT}")
    print("  ---------------------------------\n")
    app.run(host=config.ADMIN_HOST, port=config.ADMIN_PORT, debug=True)


if __name__ == "__main__":
    run_admin()
