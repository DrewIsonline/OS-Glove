"""Core storage, awareness, and tutoring services for Ubuntu Glove."""

from .config import ConfigurationError, ModelRegistry, SettingsStore
from .notes_db import ContextNote, NotesDatabase, WindowFingerprint
from .screen_vision import AccessibilityInspector, AccessibilityUnavailableError, PrivacyBlockedError, StructuralContext
from .tutor_engine import ConfigError, LocalTutorEngine, RemoteLLMClient

__all__ = [
    "AccessibilityInspector",
    "AccessibilityUnavailableError",
    "ConfigError",
    "ConfigurationError",
    "ContextNote",
    "LocalTutorEngine",
    "ModelRegistry",
    "NotesDatabase",
    "PrivacyBlockedError",
    "RemoteLLMClient",
    "SettingsStore",
    "StructuralContext",
    "WindowFingerprint",
]
