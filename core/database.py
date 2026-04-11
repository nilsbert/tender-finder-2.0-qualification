try:
    from backend.shared.database import db, DuplicateKeywordError
except ImportError:
    from shared.database import db, DuplicateKeywordError

# Ensure qualification routes can import 'db' directly
__all__ = ['db', 'DuplicateKeywordError']
