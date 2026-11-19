"""Thread-safe, local SQLite persistence for context-bound notes."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


class NotesDatabaseError(RuntimeError):
    """Raised when a note cannot be safely stored or retrieved."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class WindowFingerprint:
    """Stable identifiers used to associate a note with a visible window."""

    app_id: str
    title_regex: str

    def __post_init__(self) -> None:
        if not self.app_id.strip():
            raise ValueError("app_id cannot be empty")
        if not self.title_regex.strip():
            raise ValueError("title_regex cannot be empty")
        try:
            re.compile(self.title_regex, re.IGNORECASE)
        except re.error as error:
            raise ValueError(f"invalid window title regular expression: {error}") from error

    def matches(self, app_id: str, title: str) -> bool:
        """Return true only when the application identity and title both match."""
        app_matches = self.app_id.casefold() == (app_id or "").casefold()
        title_matches = bool(re.search(self.title_regex, title or "", re.IGNORECASE))
        return app_matches and title_matches

    @classmethod
    def from_window(cls, app_id: str, title: str) -> "WindowFingerprint":
        """Create an exact-title fingerprint while safely escaping metacharacters."""
        normalized_app = (app_id or "unknown.application").strip()
        normalized_title = (title or "Untitled window").strip()
        return cls(normalized_app, rf"^{re.escape(normalized_title)}$")


@dataclass(frozen=True)
class ContextNote:
    """A note and the window fingerprint it belongs to."""

    id: int
    fingerprint: WindowFingerprint
    body: str
    pinned: bool
    context: dict[str, Any]
    created_at: str
    updated_at: str
    last_shown_at: str | None


class NotesDatabase:
    """SQLite data layer stored under XDG local data without network access."""

    def __init__(self, database_path: Path | str | None = None) -> None:
        data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
        default = data_home / "ubuntu-glove" / "context_notes.db"
        self.path = Path(database_path or default).expanduser()
        self._lock = threading.RLock()
        self.initialize()

    def _restrict_paths(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
            if self.path.exists():
                os.chmod(self.path, 0o600)
        except OSError:
            # The package runs on Linux; this makes local non-POSIX development possible without weakening Linux behavior.
            pass

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self._restrict_paths()
        connection = sqlite3.connect(self.path, timeout=8, isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            self._restrict_paths()
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA busy_timeout = 8000")
            yield connection
        except sqlite3.Error as error:
            raise NotesDatabaseError(str(error)) from error
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create or upgrade the compact local schema atomically."""
        with self._lock, self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS context_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_id TEXT NOT NULL,
                    title_regex TEXT NOT NULL,
                    body TEXT NOT NULL CHECK(length(trim(body)) > 0),
                    pinned INTEGER NOT NULL DEFAULT 1 CHECK(pinned IN (0, 1)),
                    context_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_shown_at TEXT,
                    UNIQUE(app_id, title_regex)
                );
                CREATE INDEX IF NOT EXISTS idx_context_notes_match
                    ON context_notes(app_id, pinned, updated_at DESC);
                """
            )

    def save_note(
        self,
        fingerprint: WindowFingerprint,
        body: str,
        *,
        pinned: bool = True,
        context: dict[str, Any] | None = None,
    ) -> ContextNote:
        """Insert or replace a note for an exact fingerprint."""
        cleaned_body = body.strip()
        if not cleaned_body:
            raise ValueError("note body cannot be empty")
        serialized_context = json.dumps(context or {}, ensure_ascii=False, sort_keys=True)
        now = _utc_now()
        with self._lock, self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO context_notes
                    (app_id, title_regex, body, pinned, context_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(app_id, title_regex) DO UPDATE SET
                    body = excluded.body,
                    pinned = excluded.pinned,
                    context_json = excluded.context_json,
                    updated_at = excluded.updated_at
                """,
                (
                    fingerprint.app_id,
                    fingerprint.title_regex,
                    cleaned_body,
                    int(pinned),
                    serialized_context,
                    now,
                    now,
                ),
            )
            row = connection.execute(
                """SELECT * FROM context_notes
                   WHERE app_id = ? AND title_regex = ?""",
                (fingerprint.app_id, fingerprint.title_regex),
            ).fetchone()
            connection.execute("COMMIT")
        return self._row_to_note(row)

    def matching_notes(self, app_id: str, title: str, *, limit: int = 5) -> list[ContextNote]:
        """Return pinned notes that match the active window, newest first."""
        if limit < 1:
            return []
        with self._lock, self._connection() as connection:
            rows = connection.execute(
                """SELECT * FROM context_notes
                   WHERE app_id = ? AND pinned = 1
                   ORDER BY updated_at DESC LIMIT ?""",
                (app_id or "", limit * 4),
            ).fetchall()
        matches = [self._row_to_note(row) for row in rows]
        return [note for note in matches if note.fingerprint.matches(app_id, title)][:limit]

    def mark_shown(self, note_id: int) -> None:
        """Record a display event without changing the note content."""
        with self._lock, self._connection() as connection:
            connection.execute(
                "UPDATE context_notes SET last_shown_at = ? WHERE id = ?",
                (_utc_now(), note_id),
            )

    def set_pinned(self, note_id: int, pinned: bool) -> bool:
        """Pin or unpin a note, returning whether a record was updated."""
        with self._lock, self._connection() as connection:
            result = connection.execute(
                "UPDATE context_notes SET pinned = ?, updated_at = ? WHERE id = ?",
                (int(pinned), _utc_now(), note_id),
            )
        return result.rowcount == 1

    def delete_note(self, note_id: int) -> bool:
        """Delete one note by numeric identifier."""
        with self._lock, self._connection() as connection:
            result = connection.execute("DELETE FROM context_notes WHERE id = ?", (note_id,))
        return result.rowcount == 1

    @staticmethod
    def _row_to_note(row: sqlite3.Row) -> ContextNote:
        try:
            context = json.loads(row["context_json"])
        except (TypeError, json.JSONDecodeError):
            context = {}
        return ContextNote(
            id=int(row["id"]),
            fingerprint=WindowFingerprint(str(row["app_id"]), str(row["title_regex"])),
            body=str(row["body"]),
            pinned=bool(row["pinned"]),
            context=context if isinstance(context, dict) else {},
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
            last_shown_at=str(row["last_shown_at"]) if row["last_shown_at"] else None,
        )
