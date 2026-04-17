"""
Museum Kiosk — Translations (Spanish-first, English support)
"""

STRINGS = {
    "es": {
        # Home screen
        "home_title": "Museo",
        "home_subtitle": "Explora la coleccion",
        "no_content": "No hay contenido disponible",
        "show_hand": "Presencia detectada",

        # Gestures
        "gesture_point": "Señalar",
        "gesture_open_palm": "Libre",
        "gesture_fist": "Atrás",
        "gesture_swipe_left": "Siguiente",
        "gesture_swipe_right": "Anterior",
        "gesture_pinch": "Seleccionar",
        "gesture_none": "Sin gesto",

        # Content viewer
        "page": "Página",
        "of": "de",
        "playing": "Reproduciendo",
        "paused": "Pausado",
        "back_hint": "Puño cerrado para volver",
        "swipe_hint": "Desliza para navegar",
        "pinch_hint": "Pellizca para seleccionar",

        # Screensaver
        "screensaver_title": "Museo",
        "screensaver_subtitle": "",
        "screensaver_hint": "",
        "screensaver_presence": "",

        # HUD
        "fps": "FPS",
        "language": "Idioma",
        "switch_lang": "Cambiar a English",

        # Admin
        "admin_title": "Panel de Administración — Museo Kiosk",
        "add_content": "Agregar Contenido",
        "edit_content": "Editar Contenido",
        "delete_content": "Eliminar",
        "save": "Guardar",
        "cancel": "Cancelar",
        "title": "Título",
        "description": "Descripción",
        "type": "Tipo",
        "file": "Archivo",
        "thumbnail": "Miniatura",
        "upload": "Subir",
        "content_list": "Contenido del Museo",
    },
    "en": {
        # Home screen
        "home_title": "Museum",
        "home_subtitle": "Explore the collection",
        "no_content": "No content available",
        "show_hand": "Presence detected",

        # Gestures
        "gesture_point": "Point",
        "gesture_open_palm": "Free",
        "gesture_fist": "Back",
        "gesture_swipe_left": "Next",
        "gesture_swipe_right": "Previous",
        "gesture_pinch": "Select",
        "gesture_none": "No gesture",

        # Content viewer
        "page": "Page",
        "of": "of",
        "playing": "Playing",
        "paused": "Paused",
        "back_hint": "Closed fist to go back",
        "swipe_hint": "Swipe to navigate",
        "pinch_hint": "Pinch to select",

        # Screensaver
        "screensaver_title": "Museum",
        "screensaver_subtitle": "",
        "screensaver_hint": "",
        "screensaver_presence": "",

        # HUD
        "fps": "FPS",
        "language": "Language",
        "switch_lang": "Cambiar a Español",

        # Admin
        "admin_title": "Admin Panel — Museum Kiosk",
        "add_content": "Add Content",
        "edit_content": "Edit Content",
        "delete_content": "Delete",
        "save": "Save",
        "cancel": "Cancel",
        "title": "Title",
        "description": "Description",
        "type": "Type",
        "file": "File",
        "thumbnail": "Thumbnail",
        "upload": "Upload",
        "content_list": "Museum Content",
    },
}


class I18n:
    """Simple internationalization helper."""

    def __init__(self, default_lang="es"):
        self.lang = default_lang

    def t(self, key):
        """Get translated string for current language."""
        return STRINGS.get(self.lang, STRINGS["es"]).get(key, key)

    def toggle_language(self):
        """Switch between Spanish and English."""
        self.lang = "en" if self.lang == "es" else "es"
        return self.lang

    def set_language(self, lang):
        """Set language explicitly."""
        if lang in STRINGS:
            self.lang = lang


# Global instance
i18n = I18n()
