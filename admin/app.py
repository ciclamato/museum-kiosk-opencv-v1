"""
Museum Kiosk - Flask web admin panel.
Manage uploads, categories, order, and visibility for kiosk content.
"""
import json
import os
import sys
import uuid

from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from werkzeug.utils import secure_filename

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
)
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
    for item_type, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            return item_type
    return "image"


def _safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_item(item, index):
    normalized = dict(item)
    normalized["category"] = (normalized.get("category") or "General").strip() or "General"
    normalized["sort_order"] = max(1, _safe_int(normalized.get("sort_order"), index + 1))
    normalized["enabled"] = bool(normalized.get("enabled", True))
    normalized["description"] = normalized.get("description", "")
    normalized["thumbnail"] = normalized.get("thumbnail", "")
    return normalized


def normalize_manifest(data):
    content = data.get("content", []) if isinstance(data, dict) else []
    normalized = [normalize_item(item, index) for index, item in enumerate(content)]
    normalized.sort(key=lambda item: (
        item["category"].lower(),
        item["sort_order"],
        item.get("title", "").lower(),
    ))
    settings = data.get("settings", {}) if isinstance(data, dict) else {}
    if not isinstance(settings, dict):
        settings = {}
    settings["screensaver"] = settings.get("screensaver", "")
    settings["experience_mode"] = settings.get("experience_mode", "menu")
    return {"content": normalized, "settings": settings}


def load_manifest():
    if not os.path.exists(config.MANIFEST_PATH):
        return {"content": []}
    with open(config.MANIFEST_PATH, "r", encoding="utf-8") as handle:
        return normalize_manifest(json.load(handle))


def save_manifest(data):
    os.makedirs(os.path.dirname(config.MANIFEST_PATH), exist_ok=True)
    normalized = normalize_manifest(data)
    with open(config.MANIFEST_PATH, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, ensure_ascii=False)


def get_categories(content):
    categories = sorted({
        (item.get("category") or "General").strip() or "General"
        for item in content
    })
    return categories or ["General"]


def get_screensaver_options(content):
    options = []
    seen = set()

    for item in content:
        if item.get("type") != "video":
            continue
        filepath = item.get("file", "")
        if filepath in seen:
            continue
        seen.add(filepath)
        options.append({
            "value": filepath,
            "label": item.get("title") or os.path.basename(filepath),
        })

    video_dir = os.path.join(config.CONTENT_DIR, "videos")
    if os.path.isdir(video_dir):
        for name in sorted(os.listdir(video_dir)):
            if not name.lower().endswith((".mp4", ".m4v", ".mov", ".avi", ".webm", ".mkv")):
                continue
            rel = f"videos/{name}"
            if rel in seen:
                continue
            seen.add(rel)
            options.append({
                "value": rel,
                "label": name,
            })

    return options


def next_sort_order(content, category):
    category_items = [item for item in content if item.get("category") == category]
    if not category_items:
        return 1
    return max(item.get("sort_order", 0) for item in category_items) + 1


def reorder_category(content, category):
    category_items = sorted(
        [item for item in content if item.get("category") == category],
        key=lambda item: (item.get("sort_order", 0), item.get("title", "").lower()),
    )
    for index, item in enumerate(category_items, start=1):
        item["sort_order"] = index


@app.route("/")
def index():
    data = load_manifest()
    content = data.get("content", [])
    return render_template(
        "index.html",
        content=content,
        categories=get_categories(content),
        settings=data.get("settings", {}),
        screensaver_options=get_screensaver_options(content),
    )


@app.route("/settings", methods=["POST"])
def update_settings():
    data = load_manifest()
    selected = (request.form.get("screensaver") or "").strip()
    experience_mode = (request.form.get("experience_mode") or "menu").strip()
    valid_values = {option["value"] for option in get_screensaver_options(data.get("content", []))}

    if selected and selected not in valid_values:
        flash("El screensaver seleccionado no es valido", "error")
        return redirect(url_for("index"))

    if experience_mode not in {"menu", "perpetual"}:
        flash("El modo de experiencia no es valido", "error")
        return redirect(url_for("index"))

    data.setdefault("settings", {})
    data["settings"]["screensaver"] = selected
    data["settings"]["experience_mode"] = experience_mode
    save_manifest(data)
    flash("Configuracion del screensaver actualizada", "success")
    return redirect(url_for("index"))


@app.route("/add", methods=["GET", "POST"])
def add_content():
    data = load_manifest()
    content = data.get("content", [])

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        content_type = request.form.get("type", "image")
        category = request.form.get("category", "").strip() or "General"
        sort_order = _safe_int(
            request.form.get("sort_order"),
            next_sort_order(content, category),
        )
        enabled = request.form.get("enabled") == "on"

        file = request.files.get("file")
        if not file or not file.filename:
            flash("No se selecciono archivo", "error")
            return redirect(url_for("add_content"))

        if not allowed_file(file.filename):
            flash("Tipo de archivo no permitido", "error")
            return redirect(url_for("add_content"))

        if not title:
            flash("El titulo es requerido", "error")
            return redirect(url_for("add_content"))

        if content_type == "auto":
            content_type = get_type_from_ext(file.filename)

        filename = secure_filename(file.filename)
        type_dir = {"video": "videos", "pdf": "pdfs", "image": "images"}
        subdir = type_dir.get(content_type, "images")
        target_dir = os.path.join(config.CONTENT_DIR, subdir)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)

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
            thumb_rel = _auto_thumbnail(file_path, content_type)

        entry = {
            "id": f"exhibit-{uuid.uuid4().hex[:8]}",
            "title": title,
            "type": content_type,
            "file": f"{subdir}/{filename}",
            "thumbnail": thumb_rel,
            "description": description,
            "category": category,
            "sort_order": max(1, sort_order),
            "enabled": enabled,
        }

        data["content"].append(entry)
        reorder_category(data["content"], category)
        save_manifest(data)

        flash(f"Contenido agregado: {title}", "success")
        return redirect(url_for("index"))

    return render_template(
        "add.html",
        categories=get_categories(content),
        suggested_order=next_sort_order(content, "General"),
    )


@app.route("/edit/<content_id>", methods=["GET", "POST"])
def edit_content(content_id):
    data = load_manifest()
    item = next((candidate for candidate in data["content"] if candidate["id"] == content_id), None)

    if item is None:
        flash("Contenido no encontrado", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        old_category = item.get("category", "General")
        item["title"] = request.form.get("title", item["title"]).strip()
        item["description"] = request.form.get("description", item["description"]).strip()
        item["category"] = request.form.get("category", old_category).strip() or "General"
        item["sort_order"] = max(1, _safe_int(
            request.form.get("sort_order"),
            item.get("sort_order", 1),
        ))
        item["enabled"] = request.form.get("enabled") == "on"

        reorder_category(data["content"], old_category)
        reorder_category(data["content"], item["category"])
        save_manifest(data)
        flash("Contenido actualizado", "success")
        return redirect(url_for("index"))

    return render_template(
        "edit.html",
        item=item,
        categories=get_categories(data["content"]),
    )


@app.route("/move/<content_id>/<direction>", methods=["POST"])
def move_content(content_id, direction):
    data = load_manifest()
    item = next((candidate for candidate in data["content"] if candidate["id"] == content_id), None)

    if item is None:
        flash("Contenido no encontrado", "error")
        return redirect(url_for("index"))

    category = item.get("category", "General")
    category_items = sorted(
        [candidate for candidate in data["content"] if candidate.get("category") == category],
        key=lambda candidate: (
            candidate.get("sort_order", 0),
            candidate.get("title", "").lower(),
        ),
    )
    current_index = next(
        (index for index, candidate in enumerate(category_items) if candidate["id"] == content_id),
        None,
    )

    if current_index is None:
        flash("No se pudo mover el contenido", "error")
        return redirect(url_for("index"))

    if direction == "up" and current_index > 0:
        other = category_items[current_index - 1]
    elif direction == "down" and current_index < len(category_items) - 1:
        other = category_items[current_index + 1]
    else:
        return redirect(url_for("index"))

    item["sort_order"], other["sort_order"] = other["sort_order"], item["sort_order"]
    reorder_category(data["content"], category)
    save_manifest(data)
    return redirect(url_for("index"))


@app.route("/delete/<content_id>", methods=["POST"])
def delete_content(content_id):
    data = load_manifest()
    item = next((candidate for candidate in data["content"] if candidate["id"] == content_id), None)

    if item:
        file_path = os.path.join(config.CONTENT_DIR, item.get("file", ""))
        if os.path.exists(file_path):
            os.remove(file_path)

        thumb_path = os.path.join(config.CONTENT_DIR, item.get("thumbnail", ""))
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

        category = item.get("category", "General")
        data["content"] = [candidate for candidate in data["content"] if candidate["id"] != content_id]
        reorder_category(data["content"], category)
        save_manifest(data)
        flash("Contenido eliminado", "success")
    else:
        flash("Contenido no encontrado", "error")

    return redirect(url_for("index"))


@app.route("/content-file/<path:filepath>")
def serve_content(filepath):
    return send_from_directory(config.CONTENT_DIR, filepath)


def _auto_thumbnail(file_path, content_type):
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
                height, width = frame.shape[:2]
                scale = 300 / max(width, height)
                thumb = cv2.resize(frame, (int(width * scale), int(height * scale)))
                cv2.imwrite(thumb_path, thumb)
            cap.release()
            return f"thumbnails/{basename}.jpg"

        if content_type == "pdf":
            import fitz

            doc = fitz.open(file_path)
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(1, 1))
            pix.save(thumb_path)
            doc.close()
            return f"thumbnails/{basename}.jpg"

        if content_type == "image":
            from PIL import Image

            img = Image.open(file_path)
            img.thumbnail((300, 300))
            img.save(thumb_path, "JPEG")
            return f"thumbnails/{basename}.jpg"
    except Exception:
        pass

    return ""


def run_admin():
    print("\n  [INFO] Museo Kiosk - Panel de Administracion")
    print(f"  [INFO] http://localhost:{config.ADMIN_PORT}")
    print("  ---------------------------------\n")
    app.run(host=config.ADMIN_HOST, port=config.ADMIN_PORT, debug=True)


if __name__ == "__main__":
    run_admin()
