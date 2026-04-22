#!/usr/bin/env python3
"""
Museum Kiosk — Ultra-Lightweight Video Kiosk
Perpetual video loop with hand gesture navigation.
Optimized for Raspberry Pi 4.

Usage:
    python main.py                    # Kiosk mode (fullscreen)
    python main.py --windowed         # Windowed mode for development
    python main.py --debug            # Debug mode
    python main.py --camera 1         # Use camera index 1
    python main.py --admin            # Run web admin panel

Keyboard Shortcuts:
    ESC   = Exit
    LEFT  = Previous video
    RIGHT = Next video
    D     = Toggle debug
    F     = Toggle fullscreen
"""
import argparse
import sys
import os
import traceback
import time


def run_kiosk(args):
    """Start the ultra-lightweight kiosk."""
    import config

    from ui.renderer import Renderer

    renderer = Renderer(
        camera_index=args.camera,
        fullscreen=not args.windowed,
        debug=args.debug,
    )

    max_restarts = 5
    restart_count = 0

    while restart_count < max_restarts:
        try:
            print(f"\n  [KIOSK] Museo Kiosk Lite — Iniciando...")
            print(f"  [KIOSK] Camara: {args.camera}")
            print(f"  [KIOSK] Modo: {'Ventana' if args.windowed else 'Pantalla completa'}")
            print(f"  [KIOSK] Debug: {'Si' if args.debug else 'No'}")
            print(f"  ---------------------------------\n")

            renderer.run()
            break

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
        description="Museum Kiosk Lite — Ultra-Lightweight Video Kiosk",
    )

    parser.add_argument("--windowed", "-w", action="store_true",
                        help="Run in windowed mode")
    parser.add_argument("--debug", "-d", action="store_true",
                        help="Enable debug mode")
    parser.add_argument("--camera", "-c", type=int, default=0,
                        help="Camera index (default: 0)")
    parser.add_argument("--admin", "-a", action="store_true",
                        help="Run the web admin panel")

    args = parser.parse_args()

    os.makedirs(os.path.join("content", "videos"), exist_ok=True)
    os.makedirs(os.path.join("content", "thumbnails"), exist_ok=True)

    if args.admin:
        run_admin(args)
    else:
        run_kiosk(args)


if __name__ == "__main__":
    main()
