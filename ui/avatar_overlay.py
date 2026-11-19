"""GTK4/Libadwaita floating assistant avatar and visual coaching spotlight."""

from __future__ import annotations

import cairo
import re
from dataclasses import dataclass
from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk, Pango  # noqa: E402

try:
    gi.require_version("Gtk4LayerShell", "1.0")
    from gi.repository import Gtk4LayerShell  # type: ignore # noqa: E402
except (ImportError, ValueError):
    Gtk4LayerShell = None  # type: ignore[assignment,misc]


OVERLAY_CSS = b"""
.avatar-shell { background: transparent; }
.avatar-button {
  min-width: 48px; min-height: 48px; border-radius: 28px; padding: 0;
  background: linear-gradient(135deg, #5e5ce6, #3584e4);
  color: white; box-shadow: 0 5px 18px rgba(0,0,0,.35);
}
.avatar-button:hover { opacity: 1; }
.avatar-idle { opacity: .40; }
.avatar-active { opacity: 1; }
.avatar-glyph { font-size: 21px; font-weight: 800; }
.glove-cloud {
  border-radius: 16px; padding: 12px; margin-bottom: 8px;
  background: alpha(@window_bg_color, .97); color: @window_fg_color;
  box-shadow: 0 5px 20px rgba(0,0,0,.35);
}
.cloud-title { font-weight: 800; font-size: 12px; opacity: .75; }
.recording-light { color: #33d17a; font-size: 16px; }
.cloud-actions button { min-height: 30px; }
"""


def markdown_to_pango(text: str) -> str:
    """Convert a deliberately small safe Markdown subset into escaped Pango markup."""
    escaped = GLib.markup_escape_text(text.strip())
    escaped = re.sub(r"^###?\s+(.+)$", r"<b>\1</b>", escaped, flags=re.MULTILINE)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"`(.+?)`", r"<tt>\1</tt>", escaped)
    return escaped.replace("\n", "\n")


@dataclass
class SpotlightTarget:
    x: int
    y: int
    width: int
    height: int


class SpotlightOverlay:
    """A pass-through fullscreen layer surface that visually focuses an accessibility target."""

    def __init__(self, application: Gtk.Application) -> None:
        self.window = Gtk.ApplicationWindow(application=application)
        self.window.add_css_class("avatar-shell")
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_can_target(False)
        self._target: SpotlightTarget | None = None
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_draw_func(self._draw)
        self.window.set_child(self.canvas)
        self._setup_layer_surface()

    def _setup_layer_surface(self) -> None:
        if Gtk4LayerShell is None:
            self.window.fullscreen()
            return
        Gtk4LayerShell.init_for_window(self.window)
        Gtk4LayerShell.set_layer(self.window, Gtk4LayerShell.Layer.OVERLAY)
        Gtk4LayerShell.set_exclusive_zone(self.window, 0)
        for edge in (Gtk4LayerShell.Edge.TOP, Gtk4LayerShell.Edge.RIGHT, Gtk4LayerShell.Edge.BOTTOM, Gtk4LayerShell.Edge.LEFT):
            Gtk4LayerShell.set_anchor(self.window, edge, True)
        try:
            Gtk4LayerShell.set_keyboard_mode(self.window, Gtk4LayerShell.KeyboardMode.NONE)
        except AttributeError:
            self.window.set_focusable(False)

    def show_target(self, x: int, y: int, width: int, height: int) -> None:
        self._target = SpotlightTarget(max(0, x), max(0, y), max(1, width), max(1, height))
        self.canvas.queue_draw()
        self.window.present()

    def clear(self) -> None:
        self._target = None
        self.window.set_visible(False)

    def _draw(self, _widget: Gtk.DrawingArea, context: object, width: int, height: int) -> None:
        # Cairo is intentionally used through GTK's draw callback to preserve compositor transparency.
        if self._target is None:
            return
        cr = context
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.62)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        target = self._target
        padding = 8
        cr.set_operator(cairo.Operator.CLEAR)
        cr.rectangle(target.x - padding, target.y - padding, target.width + padding * 2, target.height + padding * 2)
        cr.fill()
        cr.set_operator(cairo.Operator.OVER)
        cr.set_source_rgba(0.2, 0.9, 0.5, 0.96)
        cr.set_line_width(3)
        cr.rectangle(target.x - padding, target.y - padding, target.width + padding * 2, target.height + padding * 2)
        cr.stroke()


class AvatarOverlay:
    """Small layer-shell surface with a draggable avatar and expandable assistance cloud."""

    def __init__(
        self,
        application: Gtk.Application,
        *,
        on_question: Callable[[str], None],
        on_note: Callable[[str], None],
        on_screen_read: Callable[[], None],
        on_palette: Callable[[], None],
        screen_read_enabled: bool = False,
    ) -> None:
        self._on_question = on_question
        self._on_note = on_note
        self._on_screen_read = on_screen_read
        self._on_palette = on_palette
        self._x = 20
        self._y = 84
        self._drag_start = (self._x, self._y)

        self.window = Gtk.ApplicationWindow(application=application)
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_default_size(356, -1)
        self.window.add_css_class("avatar-shell")
        self._install_css()
        self._setup_layer_surface()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.set_halign(Gtk.Align.START)
        self.window.set_child(root)

        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.revealer.set_transition_duration(180)
        root.append(self.revealer)
        self.cloud = self._build_cloud(screen_read_enabled)
        self.revealer.set_child(self.cloud)

        self.avatar = Gtk.Button(label="U")
        self.avatar.add_css_class("avatar-button")
        self.avatar.add_css_class("avatar-idle")
        self.avatar.set_tooltip_text("Ubuntu Glove — click for help")
        avatar_label = self.avatar.get_child()
        if avatar_label:
            avatar_label.add_css_class("avatar-glyph")
        self.avatar.connect("clicked", self._toggle_cloud)
        drag = Gtk.GestureDrag()
        drag.connect("drag-begin", self._drag_begin)
        drag.connect("drag-update", self._drag_update)
        self.avatar.add_controller(drag)
        root.append(self.avatar)

    def _install_css(self) -> None:
        provider = Gtk.CssProvider()
        provider.load_from_data(OVERLAY_CSS)
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _setup_layer_surface(self) -> None:
        if Gtk4LayerShell is None:
            self.window.set_title("Ubuntu Glove")
            return
        Gtk4LayerShell.init_for_window(self.window)
        Gtk4LayerShell.set_layer(self.window, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_exclusive_zone(self.window, 0)
        Gtk4LayerShell.set_anchor(self.window, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self.window, Gtk4LayerShell.Edge.LEFT, True)
        self._apply_position()
        try:
            Gtk4LayerShell.set_keyboard_mode(self.window, Gtk4LayerShell.KeyboardMode.ON_DEMAND)
        except AttributeError:
            self.window.set_focusable(True)

    def _build_cloud(self, screen_read_enabled: bool) -> Gtk.Widget:
        cloud = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cloud.add_css_class("glove-cloud")
        heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        title = Gtk.Label(label="Ubuntu Glove")
        title.set_halign(Gtk.Align.START)
        title.add_css_class("cloud-title")
        heading.append(title)
        self.recording_indicator = Gtk.Label(label="●")
        self.recording_indicator.add_css_class("recording-light")
        self.recording_indicator.set_tooltip_text("Pixel capture is active")
        self.recording_indicator.set_visible(False)
        heading.append(self.recording_indicator)
        cloud.append(heading)

        self.message = Gtk.Label()
        self.message.set_use_markup(True)
        self.message.set_wrap(True)
        self.message.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.message.set_xalign(0)
        self.message.set_selectable(True)
        self.message.set_markup("Ask a question, save a local note for this window, or stage a reviewed command.")
        cloud.append(self.message)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Ask about this screen or write a note…")
        self.entry.connect("activate", self._submit_question)
        cloud.append(self.entry)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        actions.add_css_class("cloud-actions")
        ask = Gtk.Button(label="Ask")
        ask.connect("clicked", self._submit_question)
        note = Gtk.Button(label="Save note")
        note.connect("clicked", self._save_note)
        screen = Gtk.Button(label="Read screen")
        screen.set_sensitive(screen_read_enabled)
        screen.set_tooltip_text(
            "Disabled until explicitly enabled for a reviewed local model gateway."
            if not screen_read_enabled
            else "Capture through the desktop portal."
        )
        screen.connect("clicked", lambda *_: self._on_screen_read())
        palette = Gtk.Button(label="Commands")
        palette.connect("clicked", lambda *_: self._on_palette())
        for button in (ask, note, screen, palette):
            actions.append(button)
        cloud.append(actions)
        return cloud

    def present(self) -> None:
        self.window.present()

    def set_mode(self, mode: str) -> None:
        active = mode == "active"
        self.avatar.remove_css_class("avatar-idle")
        self.avatar.remove_css_class("avatar-active")
        self.avatar.add_css_class("avatar-active" if active else "avatar-idle")
        if mode == "quiet":
            self.revealer.set_reveal_child(False)
        elif mode == "off":
            self.window.set_visible(False)
        else:
            self.window.set_visible(True)

    def show_message(self, text: str, *, reveal: bool = True) -> None:
        self.message.set_markup(markdown_to_pango(text))
        if reveal:
            self.revealer.set_reveal_child(True)
            self.entry.grab_focus()

    def set_recording(self, active: bool) -> None:
        GLib.idle_add(self.recording_indicator.set_visible, active)

    def _toggle_cloud(self, *_args: object) -> None:
        self.revealer.set_reveal_child(not self.revealer.get_reveal_child())
        if self.revealer.get_reveal_child():
            self.entry.grab_focus()

    def _submit_question(self, *_args: object) -> None:
        question = self.entry.get_text().strip()
        if question:
            self.entry.set_text("")
            self._on_question(question)

    def _save_note(self, *_args: object) -> None:
        note = self.entry.get_text().strip()
        if note:
            self.entry.set_text("")
            self._on_note(note)
        else:
            self.show_message("Write the note in the input field, then select **Save note**.")

    def _drag_begin(self, _gesture: Gtk.GestureDrag, _start_x: float, _start_y: float) -> None:
        self._drag_start = (self._x, self._y)

    def _drag_update(self, _gesture: Gtk.GestureDrag, offset_x: float, offset_y: float) -> None:
        self._x = max(0, self._drag_start[0] + int(offset_x))
        self._y = max(0, self._drag_start[1] + int(offset_y))
        self._apply_position()

    def _apply_position(self) -> None:
        if Gtk4LayerShell is not None:
            Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.LEFT, self._x)
            Gtk4LayerShell.set_margin(self.window, Gtk4LayerShell.Edge.TOP, self._y)
