#!/usr/bin/env python3
"""
Museum Kiosk — Main Entry Point
Gesture-controlled touchless content viewer for museum kiosks.
Powered by OpenCV, MediaPipe, and Pygame.

Usage:
    python main.py                    # Normal kiosk mode (fullscreen)
    python main.py --windowed         # Windowed mode for development
    python main.py --debug            # Debug mode (shows FPS, mouse cursor)
    python main.py --camera 1         # Use camera index 1
    python main.py --admin            # Run web admin panel instead of kiosk
    python main.py --lang en          # Start in English

Keyboard Shortcuts (dev mode):
    ESC   = Exit / Back
    L     = Toggle language (ES/EN)
    D     = Toggle debug mode
    F     = Toggle fullscreen
    C     = Cycle camera index
"""
import argparse
import sys
import os
import traceback
import time


def run_kiosk(args):
    """Start the kiosk application."""
    import config

    # Apply CLI overrides
    if args.lang:
        config.DEFAULT_LANGUAGE = args.lang

    # Set language
    from translations import i18n
    i18n.set_language(config.DEFAULT_LANGUAGE)

    from ui.renderer import Renderer

    renderer = Renderer(
        camera_index=args.camera,
        fullscreen=not args.windowed,
        debug=args.debug,
    )

    # Auto-restart loop for kiosk resilience
    max_restarts = 5
    restart_count = 0

    while restart_count < max_restarts:
        try:
            print(f"\n  [INFO] Museo Kiosk -- Iniciando...")
            print(f"  [INFO] Camara: {args.camera}")
            print(f"  [INFO] Idioma: {config.DEFAULT_LANGUAGE.upper()}")
            print(f"  [INFO] Modo: {'Ventana' if args.windowed else 'Pantalla completa'}")
            print(f"  [INFO] Debug: {'Si' if args.debug else 'No'}")
            print(f"  ---------------------------------\n")

            renderer.run()
            break  # Clean exit

        except KeyboardInterrupt:
            print("\n[INFO] Kiosk detenido por el usuario.")
            break

        except Exception as e:
            restart_count += 1
            print(f"\n[ERROR] Crash #{restart_count}: {e}")
            traceback.print_exc()

            if restart_count < max_restarts:
                wait = min(5 * restart_count, 15)
                print(f"[INFO] Reiniciando en {wait}s...")
                time.sleep(wait)
                # Re-create renderer for clean state
                renderer = Renderer(
                    camera_index=args.camera,
                    fullscreen=not args.windowed,
                    debug=args.debug,
                )
            else:
                print("[FATAL] Demasiados reinicios. Deteniendo.")
                sys.exit(1)


def run_admin(args):
    """Start the web admin panel."""
    from admin.app import run_admin as _run_admin
    _run_admin()


def main():
    parser = argparse.ArgumentParser(
        description="Museum Kiosk — Gesture-Controlled Content Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--windowed", "-w", action="store_true",
                        help="Run in windowed mode (default: fullscreen)")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="Enable debug mode (FPS counter, mouse visible)")
    parser.add_argument("--camera", "-c", type=int, default=0,
                        help="Camera index (default: 0)")
    parser.add_argument("--admin", "-a", action="store_true",
                        help="Run the web admin panel instead of the kiosk")
    parser.add_argument("--lang", "-l", type=str, default=None,
                        choices=["es", "en"],
                        help="Interface language (default: es)")

    args = parser.parse_args()

    # Ensure content directories exist
    for subdir in ["videos", "pdfs", "images", "thumbnails"]:
        os.makedirs(os.path.join("content", subdir), exist_ok=True)

    if args.admin:
        run_admin(args)
    else:
        run_kiosk(args)


if __name__ == "__main__":
    main()
