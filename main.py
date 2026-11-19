"""Ubuntu Glove application daemon and command-line entry point."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

try:
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

    HAVE_GTK = True
except (ImportError, ValueError):
    Adw = None  # type: ignore[assignment,misc]
    Gio = None  # type: ignore[assignment,misc]
    GLib = None  # type: ignore[assignment,misc]
    Gtk = None  # type: ignore[assignment,misc]
    HAVE_GTK = False

from core.config import ConfigurationError, ModelRegistry, SettingsStore
from core.notes_db import NotesDatabase, WindowFingerprint
from core.screen_vision import AccessibilityInspector, AccessibilityUnavailableError, PrivacyBlockedError, StructuralContext
from core.tutor_engine import ConfigError, LLMRequestError, LocalTutorEngine, RemoteLLMClient



APP_ID = "io.drewis.ubuntu_glove"


def project_data_dir() -> Path:
    """Find bundled source data in source-tree and Debian-installed locations."""
    source_data = Path(__file__).resolve().parent / "data"
    installed_data = Path("/usr/share/ubuntu-glove/data")
    configured_data = os.environ.get("UBUNTU_GLOVE_DATA_DIR")
    for candidate in (Path(configured_data) if configured_data else None, source_data, installed_data):
        if candidate and (candidate / "viable_commands.json").is_file() and (candidate / "onboarding_rules.json").is_file() and (candidate / "models.lock.json").is_file():
            return candidate
    return source_data


def load_engine(data_dir: Path) -> LocalTutorEngine:
    return LocalTutorEngine(data_dir / "viable_commands.json", data_dir / "onboarding_rules.json")


def load_registry(data_dir: Path) -> ModelRegistry:
    return ModelRegistry(data_dir / "models.lock.json")


BaseApplication = Adw.Application if (HAVE_GTK and Adw is not None) else object  # type: ignore[misc]


class GloveApplication(BaseApplication):
    """Single-process GTK4 overlay daemon; all potentially blocking work leaves the UI thread."""

    def __init__(
        self,
        engine: LocalTutorEngine,
        store: SettingsStore,
        registry: ModelRegistry,
        *,
        launch_indicator: bool,
    ) -> None:
        if not HAVE_GTK or Adw is None:
            raise RuntimeError("GTK4 and Libadwaita are required to instantiate GloveApplication")
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.engine = engine
        self.store = store
        self.registry = registry
        self.launch_indicator = launch_indicator
        self.notes = NotesDatabase()
        self.inspector = AccessibilityInspector()
        self.overlay: Any | None = None
        self.spotlight: Any | None = None
        self.palette: Any | None = None
        self.indicator_process: subprocess.Popen[bytes] | None = None
        self._watch_started = False
        self._last_context_signature = ""
        self._mode_timer: int | None = None

    def do_activate(self) -> None:
        if self.store.mode() == "off":
            self.quit()
            return
        if self.overlay is None:
            from ui.avatar_overlay import AvatarOverlay, SpotlightOverlay

            screen_read_on = self.store.read().get("privacy", {}).get("screen_read_enabled", False)
            self.overlay = AvatarOverlay(
                self,
                on_question=self._on_question,
                on_note=self._on_note,
                on_screen_read=self._on_screen_read,
                on_palette=self._open_palette,
                screen_read_enabled=screen_read_on,
            )
            self.spotlight = SpotlightOverlay(self)
        self.overlay.set_mode(self.store.mode())
        self.overlay.present()
        if not self._watch_started:
            self.inspector.start(self._on_structural_change)
            self._watch_started = True
        if self._mode_timer is None:
            self._mode_timer = GLib.timeout_add_seconds(1, self._sync_mode)
        if self.launch_indicator and self.indicator_process is None:
            self._launch_indicator()
        context = self.inspector.current_context()
        if context.app_id:
            self._handle_context_change(context)

    def do_shutdown(self) -> None:
        self.inspector.stop()
        if self.indicator_process and self.indicator_process.poll() is None:
            self.indicator_process.terminate()
        super().do_shutdown()

    def _launch_indicator(self) -> None:
        environment = os.environ.copy()
        source_root = str(Path(__file__).resolve().parent)
        environment["PYTHONPATH"] = source_root + os.pathsep + environment.get("PYTHONPATH", "")
        try:
            self.indicator_process = subprocess.Popen(
                [sys.executable, "-m", "ui.tray_indicator"],
                cwd=source_root,
                env=environment,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError:
            self.indicator_process = None

    def _sync_mode(self) -> bool:
        mode = self.store.mode()
        if mode == "off":
            if self.overlay:
                self.overlay.set_mode("off")
            self.quit()
            return False
        if self.overlay:
            self.overlay.set_mode(mode)
        return True

    def _on_structural_change(self, context: StructuralContext) -> None:
        GLib.idle_add(self._handle_context_change, context)

    def _handle_context_change(self, context: StructuralContext) -> bool:
        if self.store.mode() != "active" or not self.overlay or not context.app_id:
            return False
        signature = f"{context.app_id}\x00{context.window_title}"
        if signature == self._last_context_signature:
            return False
        self._last_context_signature = signature
        notes = self.notes.matching_notes(context.app_id, context.window_title, limit=1)
        if notes:
            note = notes[0]
            self.notes.mark_shown(note.id)
            self.overlay.show_message(f"**Note for this window**\n\n{note.body}", reveal=True)
            return False
        tips = self.engine.matching_tips(context.app_id, context.window_title, limit=1)
        if tips:
            self.overlay.show_message(tips[0].tip_text, reveal=True)
            if context.bounds.width and context.bounds.height and self.spotlight:
                # Spotlight highlights the focused control only when accessible coordinates are available.
                self.spotlight.show_target(
                    context.bounds.x, context.bounds.y, context.bounds.width, context.bounds.height
                )
                GLib.timeout_add(3200, self._clear_spotlight)
        return False

    def _clear_spotlight(self) -> bool:
        if self.spotlight:
            self.spotlight.clear()
        return False

    def _on_question(self, question: str) -> None:
        context = self.inspector.current_context()
        local_answer = self.engine.resolve(question, context.app_id, context.window_title)
        if local_answer:
            self._show(local_answer)
            return
        self._show("Checking your configured assistant…")
        self._run_async_answer(question, context)

    def _on_note(self, note_text: str) -> None:
        context = self.inspector.current_context()
        fingerprint = WindowFingerprint.from_window(context.app_id, context.window_title)
        try:
            note = self.notes.save_note(fingerprint, note_text, context=context.to_dict())
        except (ValueError, OSError) as error:
            self._show(f"Could not save the local note: {error}")
            return
        self._show(f"Saved a pinned local note for **{note.fingerprint.app_id}** / **{context.window_title}**.")

    def _on_screen_read(self) -> None:
        if not self.store.screen_read_enabled():
            self._show("Screen reading is disabled. Enable it only after a reviewed local model gateway is configured and tested.")
            return
        self._show("Capturing this screen through the desktop portal…")
        worker = threading.Thread(target=self._read_screen_worker, name="ubuntu-glove-screen-read", daemon=True)
        worker.start()

    def _read_screen_worker(self) -> None:
        frame: Path | None = None
        try:
            frame = self.inspector.capture_to_private_file(capture_state=self._set_recording)
            context = self.inspector.current_context(require_available=True)
            client = RemoteLLMClient(self.store, self.registry)
            answer = asyncio.run(
                client.answer(
                    "Describe the visible screen and give the next safe action. State uncertainty where relevant.",
                    structural_context=context.to_dict(),
                    image_path=frame,
                )
            )
        except (AccessibilityUnavailableError, PrivacyBlockedError, LLMRequestError, OSError, RuntimeError) as error:
            self._show(f"Screen read did not complete: {error}")
        else:
            self._show(answer)
        finally:
            if frame:
                try:
                    frame.unlink(missing_ok=True)
                except OSError:
                    frame = None

    def _run_async_answer(self, question: str, context: StructuralContext) -> None:
        def worker() -> None:
            try:
                client = RemoteLLMClient(self.store, self.registry)
                answer = asyncio.run(client.answer(question, structural_context=context.to_dict()))
            except LLMRequestError as error:
                self._show(f"No local rule matched. {error}")
            else:
                self._show(answer)

        threading.Thread(target=worker, name="ubuntu-glove-llm", daemon=True).start()

    def _open_palette(self) -> None:
        if self.palette is not None:
            self.palette.present()
            return

        from ui.command_dropdown import CommandPalette

        def selected(command: Any) -> None:
            self._show(f"Staged in the clipboard:\n\n`{command.command}`\n\nPaste it into the terminal and review it before running.")

        def closed() -> None:
            self.palette = None

        self.palette = CommandPalette(self, self.engine, on_selected=selected, on_closed=closed)
        self.palette.present()

    def _set_recording(self, active: bool) -> None:
        if self.overlay and GLib:
            GLib.idle_add(self.overlay.set_recording, active)

    def _show(self, text: str) -> None:
        if self.overlay and GLib:
            GLib.idle_add(self.overlay.show_message, text)


def run_palette(engine: LocalTutorEngine, *, print_command: bool) -> int:
    """Open a focused palette process for terminal integration and return only the selected command."""
    if not HAVE_GTK or Gtk is None:
        print("ubuntu-glove: GTK4 is required to run the command palette.", file=sys.stderr)
        return 1
    from ui.command_dropdown import CommandPalette

    application = Gtk.Application(application_id=f"{APP_ID}.palette")

    def activate(app: Gtk.Application) -> None:
        def selected(command: Any) -> None:
            if print_command:
                print(command.command, flush=True)
            app.quit()

        palette = CommandPalette(app, engine, on_selected=selected, on_closed=app.quit)
        palette.present()

    application.connect("activate", activate)
    return application.run([sys.argv[0]])


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ubuntu Glove desktop assistant overlay")
    parser.add_argument("--command-palette", action="store_true", help="open the curated command palette")
    parser.add_argument("--print-command", action="store_true", help="print selected palette command to stdout")
    parser.add_argument("--note", help="save a context-bound note for the currently active window")
    parser.add_argument("--read-screen", action="store_true", help="perform one privacy-gated visual inspection")
    parser.add_argument("--mode", choices=("active", "quiet", "off"), help="persist a daemon mode and exit")
    parser.add_argument("--activate", action="store_true", help="set Active mode and open the overlay")
    parser.add_argument("--check-data", action="store_true", help="validate JSON datasets and the reviewed model-route lock")
    parser.add_argument("--configure-local-gateway", nargs=2, metavar=("ENDPOINT", "ROUTE_ID"), help="configure a reviewed loopback OpenAI-compatible model gateway")
    parser.add_argument("--screen-read", choices=("on", "off"), help="explicitly enable or disable local screen reading")
    parser.add_argument("--show-config", action="store_true", help="show safe configuration status without secrets")
    parser.add_argument("--data-dir", type=Path, help="override bundled data directory")
    parser.add_argument("--config-dir", type=Path, help="override XDG configuration parent directory")
    parser.add_argument("--no-tray", action="store_true", help="do not spawn the separate top-bar indicator")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv if argv is not None else sys.argv[1:])
    data_dir = args.data_dir or project_data_dir()
    try:
        engine = load_engine(data_dir)
        registry = load_registry(data_dir)
    except (ConfigError, ConfigurationError) as error:
        print(f"ubuntu-glove: configuration error: {error}", file=sys.stderr)
        return 2
    if args.check_data:
        print(json.dumps({"commands": len(engine.commands), "categories": engine.categories, "onboarding_rules": len(engine.onboarding_rules), "model_routes": len(registry._routes)}, indent=2))
        return 0
    store = SettingsStore(args.config_dir)
    try:
        if args.configure_local_gateway:
            endpoint, route_id = args.configure_local_gateway
            store.configure_local_gateway(endpoint, route_id, registry)
            print("Configured a reviewed local loopback model gateway.")
            return 0
        if args.screen_read:
            store.set_screen_read_enabled(args.screen_read == "on")
            print(f"Screen reading is now {'enabled' if args.screen_read == 'on' else 'disabled'}.")
            return 0
        if args.show_config:
            current = store.read()
            print(json.dumps({"mode": current["mode"], "screen_read_enabled": current["privacy"]["screen_read_enabled"], "local_gateway_configured": "llm" in current}, indent=2))
            return 0
        if args.mode:
            store.set_mode(args.mode)
            return 0
        if args.activate:
            store.set_mode("active")
        if args.command_palette or args.print_command:
            return run_palette(engine, print_command=args.print_command)
        if not HAVE_GTK or Adw is None:
            print(
                "ubuntu-glove: GTK4 and Libadwaita are required to run the desktop overlay. "
                "Install them using 'bash scripts/install_stack.sh --install-deps'.",
                file=sys.stderr,
            )
            return 1
        app = GloveApplication(engine, store, registry, launch_indicator=not args.no_tray)
        if args.note:
            # The normal app activation creates the overlay; the note is then associated with current AT-SPI context.
            def create_note_after_activate() -> bool:
                app._on_note(args.note)
                app.quit()
                return False

            app.connect("activate", lambda *_: GLib.idle_add(create_note_after_activate))
        if args.read_screen:
            app.connect("activate", lambda *_: GLib.idle_add(lambda: (app._on_screen_read(), False)[1]))
        return app.run([sys.argv[0]])
    except ConfigurationError as error:
        print(f"ubuntu-glove: configuration error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
