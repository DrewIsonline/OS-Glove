"""AT-SPI structural inspection and privacy-gated, user-triggered screen capture."""

from __future__ import annotations

import os
import re
import select
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import unquote, urlparse


class AccessibilityUnavailableError(RuntimeError):
    """Raised when AT-SPI2 is not enabled or cannot be reached."""


class PrivacyBlockedError(PermissionError):
    """Raised when a focused credential field blocks a pixel capture."""


@dataclass(frozen=True)
class Bounds:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0


@dataclass(frozen=True)
class StructuralContext:
    """A small, serializable representation of the currently focused UI element."""

    app_id: str = ""
    window_title: str = ""
    focused_role: str = ""
    focused_name: str = ""
    bounds: Bounds = Bounds()
    is_password_field: bool = False
    accessibility_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bounds"] = asdict(self.bounds)
        return payload


class AccessibilityInspector:
    """Uses AT-SPI when available without adding a permanent pixel capture workload."""

    PASSWORD_TERMS = ("password", "passphrase", "credential", "secret", "pin", "security code")

    def __init__(self, poll_seconds: float = 0.75) -> None:
        self.poll_seconds = max(0.25, poll_seconds)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._on_change: Callable[[StructuralContext], None] | None = None
        self._last_context = StructuralContext()
        self._lock = threading.RLock()
        self._pyatspi: Any | None = None

    def available(self) -> bool:
        try:
            self._load_pyatspi()
            return True
        except AccessibilityUnavailableError:
            return False

    def start(self, on_change: Callable[[StructuralContext], None]) -> None:
        """Start a daemon polling thread; it never runs on GTK's UI thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._on_change = on_change
            self._thread = threading.Thread(target=self._watch_loop, name="ubuntu-glove-atspi", daemon=True)
            self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=timeout)

    def current_context(self, *, require_available: bool = False) -> StructuralContext:
        """Read the active application, window, and focused accessible object once."""
        try:
            atspi = self._load_pyatspi()
            desktop = atspi.Registry.getDesktop(0)
            active_app, active_window, focused = self._find_active(desktop, atspi)
            app_name = self._safe_name(active_app) or self._safe_attribute(active_app, "application-id")
            title = self._safe_name(active_window) or self._safe_name(active_app)
            role = self._safe_role(focused)
            name = self._safe_name(focused)
            sensitive = self._is_sensitive(focused, role, name)
            return StructuralContext(
                app_id=app_name or "unknown.application",
                window_title=title or "Untitled window",
                focused_role=role,
                focused_name=name,
                bounds=self._bounds(focused, atspi),
                is_password_field=sensitive,
                accessibility_available=True,
            )
        except AccessibilityUnavailableError:
            if require_available:
                raise
            return StructuralContext()
        except Exception as error:
            # Accessibility providers can disappear while windows close; retain a safe empty state.
            if require_available:
                raise AccessibilityUnavailableError("AT-SPI context is unavailable; screen capture is blocked.") from error
            return StructuralContext()

    def capture_to_private_file(self, *, capture_state: Callable[[bool], None] | None = None) -> Path:
        """Capture only with a working safety context into an app-private 0600 file."""
        context = self.current_context(require_available=True)
        if not context.accessibility_available:
            raise AccessibilityUnavailableError("AT-SPI context is unavailable; screen capture is blocked.")
        if context.is_password_field:
            raise PrivacyBlockedError("Screen capture blocked because a password or credential field is focused.")
        target = self._new_private_capture_path()
        if capture_state:
            capture_state(True)
        try:
            try:
                self._capture_via_portal(target)
            except RuntimeError:
                self._capture_via_native_tool(target)
            if not target.exists() or target.stat().st_size == 0:
                raise RuntimeError("Screenshot capture returned no image data.")
            os.chmod(target, 0o600)
            if stat.S_IMODE(target.stat().st_mode) != 0o600:
                raise PrivacyBlockedError("Screenshot file permissions could not be restricted; capture was blocked.")
            return target
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            if capture_state:
                capture_state(False)

    @staticmethod
    def _new_private_capture_path() -> Path:
        """Return an unused random path in a 0700 per-user runtime directory."""
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
        directory = Path(runtime_dir) / "ubuntu-glove" if runtime_dir else Path.home() / ".cache" / "ubuntu-glove" / "runtime"
        directory.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(directory, 0o700)
        except OSError as error:
            raise PrivacyBlockedError(f"Could not restrict private screenshot directory: {error}") from error
        if stat.S_IMODE(directory.stat().st_mode) != 0o700:
            raise PrivacyBlockedError("Private screenshot directory permissions are unsafe; capture was blocked.")
        descriptor, name = tempfile.mkstemp(prefix="screen-", suffix=".png", dir=directory)
        try:
            os.fchmod(descriptor, 0o600)
        finally:
            os.close(descriptor)
        target = Path(name)
        target.unlink(missing_ok=True)
        return target

    def _watch_loop(self) -> None:
        while not self._stop.wait(self.poll_seconds):
            context = self.current_context()
            with self._lock:
                changed = context != self._last_context
                self._last_context = context
                callback = self._on_change
            if changed and callback:
                try:
                    callback(context)
                except Exception:
                    # A consumer failure must not kill the accessibility watcher.
                    continue

    def _load_pyatspi(self) -> Any:
        if self._pyatspi is not None:
            return self._pyatspi
        try:
            import pyatspi  # type: ignore[import-not-found]
        except ImportError as error:
            raise AccessibilityUnavailableError("pyatspi is not installed") from error
        self._pyatspi = pyatspi
        return pyatspi

    def _find_active(self, desktop: Any, atspi: Any) -> tuple[Any | None, Any | None, Any | None]:
        active_app = active_window = focused = None
        for app in self._walk(desktop, limit=900):
            state = self._safe_state(app)
            if state and state.contains(atspi.STATE_ACTIVE):
                active_app = app
                break
        candidates = self._walk(active_app or desktop, limit=1200)
        for accessible in candidates:
            state = self._safe_state(accessible)
            if not state:
                continue
            if state.contains(atspi.STATE_ACTIVE):
                active_window = accessible
            if state.contains(atspi.STATE_FOCUSED):
                focused = accessible
                break
        return active_app, active_window, focused or active_window or active_app

    @staticmethod
    def _walk(root: Any, limit: int) -> Iterator[Any]:
        if root is None:
            return
        stack = [root]
        visited = 0
        while stack and visited < limit:
            current = stack.pop()
            visited += 1
            yield current
            try:
                count = current.childCount
                stack.extend(current[index] for index in range(count - 1, -1, -1))
            except Exception:
                continue

    @staticmethod
    def _safe_name(accessible: Any) -> str:
        try:
            return str(accessible.name or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _safe_role(accessible: Any) -> str:
        try:
            return str(accessible.getRoleName() or "").strip().casefold()
        except Exception:
            return ""

    @staticmethod
    def _safe_state(accessible: Any) -> Any | None:
        try:
            return accessible.getState()
        except Exception:
            return None

    @staticmethod
    def _safe_attribute(accessible: Any, key: str) -> str:
        try:
            attributes = dict(item.split(":", 1) for item in accessible.getAttributes() if ":" in item)
            return str(attributes.get(key, "")).strip()
        except Exception:
            return ""

    def _is_sensitive(self, accessible: Any, role: str, name: str) -> bool:
        terms = " ".join((role, name, self._safe_attribute(accessible, "placeholder-text"))).casefold()
        if any(term in terms for term in self.PASSWORD_TERMS):
            return True
        try:
            state = self._safe_state(accessible)
            atspi = self._load_pyatspi()
            return bool(state and state.contains(atspi.STATE_PROTECTED))
        except Exception:
            return False

    @staticmethod
    def _bounds(accessible: Any, atspi: Any) -> Bounds:
        try:
            extents = accessible.queryComponent().getExtents(atspi.DESKTOP_COORDS)
            return Bounds(int(extents.x), int(extents.y), int(extents.width), int(extents.height))
        except Exception:
            return Bounds()

    @staticmethod
    def _capture_via_portal(target: Path) -> None:
        """Request an XDG Screenshot portal capture and copy its URI to the volatile target."""
        command = [
            "gdbus", "call", "--session", "--dest", "org.freedesktop.portal.Desktop",
            "--object-path", "/org/freedesktop/portal/desktop",
            "--method", "org.freedesktop.portal.Screenshot.Screenshot", "", "{'interactive': <false>}",
        ]
        try:
            start = subprocess.run(command, check=True, text=True, capture_output=True, timeout=8)
        except (OSError, subprocess.SubprocessError) as error:
            raise RuntimeError(f"Screenshot portal is unavailable: {error}") from error
        match = re.search(r"objectpath ['\"]([^'\"]+)['\"]", start.stdout)
        if not match:
            raise RuntimeError("Screenshot portal returned no request handle")
        monitor = subprocess.Popen(
            ["gdbus", "monitor", "--session", "--dest", "org.freedesktop.portal.Desktop", "--object-path", match.group(1)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if monitor.stdout is None:
                    break
                readable, _, _ = select.select([monitor.stdout], [], [], max(0.1, deadline - time.monotonic()))
                if not readable:
                    continue
                line = monitor.stdout.readline()
                uri_match = re.search(r"'uri': <'([^']+)'>", line)
                if uri_match:
                    source = Path(unquote(urlparse(uri_match.group(1)).path))
                    if source.exists():
                        shutil.copyfile(source, target)
                        os.chmod(target, 0o600)
                        return
                if "Response" in line and "uint32 1" in line:
                    raise RuntimeError("Screenshot portal request was denied")
            raise RuntimeError("Screenshot portal timed out")
        finally:
            monitor.terminate()
            try:
                monitor.wait(timeout=1)
            except subprocess.TimeoutExpired:
                monitor.kill()

    @staticmethod
    def _capture_via_native_tool(target: Path) -> None:
        """Use GNOME's own screenshot utility only when the portal is not operational."""
        for command in (["gnome-screenshot", "-f", str(target)], ["grim", str(target)]):
            try:
                subprocess.run(command, check=True, timeout=20, capture_output=True)
                if target.exists() and target.stat().st_size:
                    os.chmod(target, 0o600)
                    return
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        raise RuntimeError("No usable screenshot portal, gnome-screenshot, or grim capture tool was found")
