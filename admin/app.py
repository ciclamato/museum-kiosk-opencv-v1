"""
Museum Kiosk — Flask Web Admin Panel
Simple web interface for museum staff to manage kiosk content.
Upload videos, PDFs, and images. Edit titles and descriptions.
"""
import os
import sys
import json
import uuid
import shutil

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_from_directory, jsonify)
from werkzeug.utils import secure_filename

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

app = Flask(__name__,
            template_folder=os.path.join(os.path.dirname(__file__), "templates"),
            static_folder=os.path.join(os.path.dirname(__file__), "static"))
app.secret_key = config.ADMIN_SECRET_KEY

ALLOWED_EXTENSIONS = {
    "video": {"mp4", "avi", "mkv", "webm", "mov"},
    "pdf": {"pdf"},
    "image": {"jpg", "jpeg", "png", "gif", "webp", "bmp"},
}
ALL_EXTENSIONS = set()
for exts in ALLOWED_EXTENSIONS.values():
    ALL_EXTENSIONS |= exts


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALL_EXTENSIONS


def get_type_from_ext(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    for t, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return t
    return "image"


def load_manifest():
    if not os.path.exists(config.MANIFEST_PATH):
        return {"content": []}
    with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(data):
    os.makedirs(os.path.dirname(config.MANIFEST_PATH), exist_ok=True)
    with open(config.MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@app.route("/")
def index():
    data = load_manifest()
    return render_template("index.html", content=data.get("content", []))


@app.route("/add", methods=["GET", "POST"])
def add_content():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        content_type = request.form.get("type", "image")

        file = request.files.get("file")
        if not file or not file.filename:
            flash("No se seleccionó archivo", "error")
            return redirect(url_for("add_content"))

        if not allowed_file(file.filename):
            flash("Tipo de archivo no permitido", "error")
            return redirect(url_for("add_content"))

        if not title:
            flash("El título es requerido", "error")
            return redirect(url_for("add_content"))

        # Determine type from extension if auto
        if content_type == "auto":
            content_type = get_type_from_ext(file.filename)

        # Save file
        filename = secure_filename(file.filename)
        type_dir = {"video": "videos", "pdf": "pdfs", "image": "images"}
        subdir = type_dir.get(content_type, "images")
        target_dir = os.path.join(config.CONTENT_DIR, subdir)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)

        # Handle thumbnail
        thumb_rel = ""
        thumb_file = request.files.get("thumbnail")
        if thumb_file and thumb_file.filename:
            thumb_name = secure_filename(thumb_file.filename)
            thumb_dir = os.path.join(config.CONTENT_DIR, "thumbnails")
            os.makedirs(thumb_dir, exist_ok=True)
            thumb_path = os.path.join(thumb_dir, thumb_name)
            thumb_file.save(thumb_path)
            thumb_rel = f"thumbnails/{thumb_name}"
        else:
            # Auto-generate thumbnail
            thumb_rel = _auto_thumbnail(file_path, content_type)

        # Create manifest entry
        content_id = f"exhibit-{uuid.uuid4().hex[:8]}"
        entry = {
            "id": content_id,
            "title": title,
            "type": content_type,
            "file": f"{subdir}/{filename}",
            "thumbnail": thumb_rel,
            "description": description,
        }

        data = load_manifest()
        data["content"].append(entry)
        save_manifest(data)

        flash(f"Contenido agregado: {title}", "success")
        return redirect(url_for("index"))

    return render_template("add.html")


@app.route("/edit/<content_id>", methods=["GET", "POST"])
def edit_content(content_id):
    data = load_manifest()
    item = next((c for c in data["content"] if c["id"] == content_id), None)

    if item is None:
        flash("Contenido no encontrado", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        item["title"] = request.form.get("title", item["title"]).strip()
        item["description"] = request.form.get("description",
                                                 item["description"]).strip()
        save_manifest(data)
        flash("Contenido actualizado", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", item=item)


@app.route("/delete/<content_id>", methods=["POST"])
def delete_content(content_id):
    data = load_manifest()
    item = next((c for c in data["content"] if c["id"] == content_id), None)

    if item:
        # Optionally delete file
        file_path = os.path.join(config.CONTENT_DIR, item.get("file", ""))
        if os.path.exists(file_path):
            os.remove(file_path)

        thumb_path = os.path.join(config.CONTENT_DIR, item.get("thumbnail", ""))
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        data["content"] = [c for c in data["content"] if c["id"] != content_id]
        save_manifest(data)
        flash("Contenido eliminado", "success")
    else:
        flash("Contenido no encontrado", "error")

    return redirect(url_for("index"))


@app.route("/content-file/<path:filepath>")
def serve_content(filepath):
    """Serve content files for preview."""
    return send_from_directory(config.CONTENT_DIR, filepath)


def _auto_thumbnail(file_path, content_type):
    """Generate thumbnail automatically."""
    thumb_dir = os.path.join(config.CONTENT_DIR, "thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(file_path))[0]
    thumb_path = os.path.join(thumb_dir, f"{basename}.jpg")

    try:
        if content_type == "video":
            import cv2
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                scale = 300 / max(w, h)
                thumb = cv2.resize(frame, (int(w * scale), int(h * scale)))
                cv2.imwrite(thumb_path, thumb)
            cap.release()
            return f"thumbnails/{basename}.jpg"

        elif content_type == "pdf":
            import fitz
            doc = fitz.open(file_path)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(1, 1))
            pix.save(thumb_path)
            doc.close()
            return f"thumbnails/{basename}.jpg"

        elif content_type == "image":
            from PIL import Image
            img = Image.open(file_path)
            img.thumbnail((300, 300))
            img.save(thumb_path, "JPEG")
            return f"thumbnails/{basename}.jpg"

    except Exception:
        pass
    return ""


def run_admin():
    """Start the admin panel server."""
    print(f"\n  [INFO] Museo Kiosk -- Panel de Administracion")
    print(f"  [INFO] http://localhost:{config.ADMIN_PORT}")
    print(f"  ---------------------------------\n")
    app.run(host=config.ADMIN_HOST, port=config.ADMIN_PORT, debug=True)


if __name__ == "__main__":
    run_admin()
