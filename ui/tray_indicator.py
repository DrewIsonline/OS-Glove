"""GTK3/Ayatana indicator process kept separate from the GTK4 overlay process."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3, Gtk  # noqa: E402
except (ImportError, ValueError):
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3, Gtk  # type: ignore # noqa: E402

from core.config import ConfigurationError, SettingsStore


class IndicatorApplication:
    """Native status indicator that shares a small atomically-written mode file with the daemon."""

    def __init__(self, store: SettingsStore) -> None:
        self.store = store
        self.indicator = AppIndicator3.Indicator.new(
            "ubuntu-glove", "dialog-information-symbolic", AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.menu = Gtk.Menu()
        self.radios: dict[str, Gtk.RadioMenuItem] = {}
        self._building = False
        self._build_menu()
        self.indicator.set_menu(self.menu)
        self._last_mode = ""
        self._sync_from_store()
        Gtk.timeout_add(1000, self._poll)

    def _build_menu(self) -> None:
        title = Gtk.MenuItem.new_with_label("Ubuntu Glove")
        title.set_sensitive(False)
        self.menu.append(title)
        group: Gtk.RadioMenuItem | None = None
        labels = (("active", "Active Mode"), ("quiet", "Quiet Mode"), ("off", "Turned Off"))
        for mode, label in labels:
            item = Gtk.RadioMenuItem.new_with_label_from_widget(group, label)
            item.connect("toggled", self._on_mode_toggled, mode)
            self.menu.append(item)
            self.radios[mode] = item
            group = item
        self.menu.append(Gtk.SeparatorMenuItem())
        palette = Gtk.MenuItem.new_with_label("Open command palette")
        palette.connect("activate", self._open_palette)
        self.menu.append(palette)
        quit_item = Gtk.MenuItem.new_with_label("Quit indicator")
        quit_item.connect("activate", lambda *_: Gtk.main_quit())
        self.menu.append(quit_item)
        self.menu.show_all()

    def _on_mode_toggled(self, item: Gtk.RadioMenuItem, mode: str) -> None:
        if self._building or not item.get_active():
            return
        self.store.set_mode(mode)
        self._last_mode = mode
        if mode == "off":
            self._systemctl("stop")
        elif mode == "active":
            self._systemctl("start")

    def _systemctl(self, action: str) -> None:
        try:
            subprocess.run(["systemctl", "--user", action, "ubuntu-glove.service"], timeout=8, check=False)
        except FileNotFoundError:
            return

    def _open_palette(self, *_args: object) -> None:
        executable = os.environ.get("UBUNTU_GLOVE_EXECUTABLE", "ubuntu-glove")
        subprocess.Popen([executable, "--command-palette"], start_new_session=True)

    def _poll(self) -> bool:
        self._sync_from_store()
        return True

    def _sync_from_store(self) -> None:
        try:
            mode = self.store.mode()
        except ConfigurationError:
            mode = "off"
        if mode == self._last_mode:
            return
        self._building = True
        try:
            self.radios[mode].set_active(True)
            self.indicator.set_icon_full(
                "dialog-information-symbolic" if mode != "off" else "process-stop-symbolic",
                f"Ubuntu Glove: {mode.title()} mode",
            )
            self._last_mode = mode
        finally:
            self._building = False


def main() -> int:
    parser = argparse.ArgumentParser(description="Ubuntu Glove top-bar indicator")
    parser.add_argument("--config-dir", type=Path, help="Override the Ubuntu Glove configuration directory")
    arguments = parser.parse_args()
    IndicatorApplication(SettingsStore(arguments.config_dir))
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
