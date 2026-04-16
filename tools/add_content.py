"""
Museum Kiosk — CLI Content Manager
Adds, lists, and removes content entries from manifest.json.
Auto-generates thumbnails for videos and PDFs.

Usage:
    python tools/add_content.py add --title "Title" --type video --file videos/my_video.mp4
    python tools/add_content.py list
    python tools/add_content.py remove --id exhibit-001
"""
import argparse
import json
import os
import sys
import uuid

# Add parent dir to path so we can import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_manifest():
    """Load the content manifest."""
    if not os.path.exists(config.MANIFEST_PATH):
        return {"content": []}
    with open(config.MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(data):
    """Save the content manifest."""
    os.makedirs(os.path.dirname(config.MANIFEST_PATH), exist_ok=True)
    with open(config.MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_thumbnail(file_path, content_type, thumb_dir):
    """Auto-generate thumbnail from content file."""
    os.makedirs(thumb_dir, exist_ok=True)
    basename = os.path.splitext(os.path.basename(file_path))[0]
    thumb_path = os.path.join(thumb_dir, f"{basename}.jpg")

    try:
        if content_type == "video":
            import cv2
            cap = cv2.VideoCapture(file_path)
            ret, frame = cap.read()
            if ret:
                # Resize to thumbnail
                h, w = frame.shape[:2]
                scale = 300 / max(w, h)
                new_w, new_h = int(w * scale), int(h * scale)
                thumb = cv2.resize(frame, (new_w, new_h))
                cv2.imwrite(thumb_path, thumb)
                cap.release()
                return os.path.relpath(thumb_path, config.CONTENT_DIR)
            cap.release()

        elif content_type == "pdf":
            try:
                import fitz
                doc = fitz.open(file_path)
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
                pix.save(thumb_path)
                doc.close()
                return os.path.relpath(thumb_path, config.CONTENT_DIR)
            except ImportError:
                print("[WARN] PyMuPDF not installed — cannot generate PDF thumbnail")

        elif content_type == "image":
            from PIL import Image
            img = Image.open(file_path)
            img.thumbnail((300, 300))
            img.save(thumb_path, "JPEG")
            return os.path.relpath(thumb_path, config.CONTENT_DIR)

    except Exception as e:
        print(f"[WARN] Could not generate thumbnail: {e}")

    return ""


def cmd_add(args):
    """Add new content to the manifest."""
    # Validate file
    file_path = os.path.join(config.CONTENT_DIR, args.file)
    if not os.path.exists(file_path):
        print(f"[ERROR] File not found: {file_path}")
        print(f"        Place your file in: {config.CONTENT_DIR}")
        sys.exit(1)

    valid_types = ("video", "pdf", "image")
    if args.type not in valid_types:
        print(f"[ERROR] Type must be one of: {valid_types}")
        sys.exit(1)

    # Generate ID
    content_id = f"exhibit-{uuid.uuid4().hex[:8]}"

    # Auto-generate thumbnail
    thumb_dir = os.path.join(config.CONTENT_DIR, "thumbnails")
    thumbnail = generate_thumbnail(file_path, args.type, thumb_dir)

    # Use manual thumbnail if provided
    if args.thumbnail:
        thumbnail = args.thumbnail

    # Create entry
    entry = {
        "id": content_id,
        "title": args.title,
        "type": args.type,
        "file": args.file,
        "thumbnail": thumbnail,
        "description": args.description or "",
    }

    # Add to manifest
    data = load_manifest()
    data["content"].append(entry)
    save_manifest(data)

    print(f"[OK] Added: {args.title} ({args.type})")
    print(f"     ID: {content_id}")
    print(f"     File: {args.file}")
    if thumbnail:
        print(f"     Thumbnail: {thumbnail}")


def cmd_list(args):
    """List all content in the manifest."""
    data = load_manifest()
    entries = data.get("content", [])

    if not entries:
        print("[INFO] No content registered.")
        return

    print(f"\n{'ID':<20} {'Type':<8} {'Title':<30} {'File'}")
    print("─" * 80)
    for item in entries:
        print(f"{item['id']:<20} {item['type']:<8} {item['title']:<30} {item.get('file', 'N/A')}")
    print(f"\nTotal: {len(entries)} items")


def cmd_remove(args):
    """Remove content by ID."""
    data = load_manifest()
    original_len = len(data["content"])
    data["content"] = [c for c in data["content"] if c["id"] != args.id]

    if len(data["content"]) == original_len:
        print(f"[ERROR] Content ID not found: {args.id}")
        sys.exit(1)

    save_manifest(data)
    print(f"[OK] Removed content: {args.id}")


def main():
    parser = argparse.ArgumentParser(description="Museum Kiosk Content Manager")
    subparsers = parser.add_subparsers(dest="command")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add new content")
    add_parser.add_argument("--title", required=True, help="Display title")
    add_parser.add_argument("--type", required=True, choices=["video", "pdf", "image"],
                            help="Content type")
    add_parser.add_argument("--file", required=True,
                            help="File path relative to content/ directory")
    add_parser.add_argument("--description", default="",
                            help="Short description")
    add_parser.add_argument("--thumbnail", default="",
                            help="Thumbnail path relative to content/ directory")

    # List command
    subparsers.add_parser("list", help="List all content")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove content by ID")
    remove_parser.add_argument("--id", required=True, help="Content ID to remove")

    args = parser.parse_args()

    if args.command == "add":
        cmd_add(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "remove":
        cmd_remove(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
