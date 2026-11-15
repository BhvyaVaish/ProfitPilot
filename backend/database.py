"""
database.py — RETIRED.

ProfitPilot has migrated from Supabase/PostgreSQL to Firebase Firestore.
All database operations now go through firestore_db.py.

This file is kept only so that any stale import of `database` does not
crash the process. If you see this file being imported anywhere, that
module still needs to be updated to use firestore_db.
"""

USE_POSTGRES = False


def get_connection():
    raise RuntimeError(
        "database.get_connection() was called but this app now uses Firestore. "
        "Update the calling code to use firestore_db instead."
    )


def init_db():
    """No-op — Firestore needs no schema initialisation."""
    pass
