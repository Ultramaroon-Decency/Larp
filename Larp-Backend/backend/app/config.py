"""Configuration module for the application.

This module re-exports ``Settings`` and ``get_settings`` from
``app.settings`` so that all existing imports continue to work
without modification:

    from app.config import get_settings          # ✅ still works
    from app.config import Settings              # ✅ still works
    from app.config import EnvironmentType       # ✅ new

**Why separate config.py and settings.py?**

- ``settings.py`` is the *implementation* — the full ``Settings`` class
  with validators, enums, computed properties, and the ``get_settings()``
  factory.  This file can grow as new environment variables are added.

- ``config.py`` is the *public API* — a stable, thin re-export.  Every
  module in the project imports from here.  By keeping this file small,
  we avoid circular-import risks and make it trivial to swap the
  implementation (e.g. for integration tests that need custom settings).
"""

from app.settings import EnvironmentType, Settings, get_settings

__all__ = ["EnvironmentType", "Settings", "get_settings"]
