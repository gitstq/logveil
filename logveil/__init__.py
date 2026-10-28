"""LogVeil: redact logs for safe sharing, reversibly."""

from .redactor import Redactor, restore_text

__version__ = "1.0.0"
__all__ = ["Redactor", "restore_text", "__version__"]
