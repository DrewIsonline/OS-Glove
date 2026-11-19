"""GTK4 command palette backed only by the local curated command dataset."""

from __future__ import annotations

from collections.abc import Callable

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from core.tutor_engine import LocalTutorEngine, SafeCommand


class CommandPalette:
    """Searches curated commands and stages the chosen command without executing it."""

    def __init__(
        self,
        application: Gtk.Application,
        engine: LocalTutorEngine,
        *,
        on_selected: Callable[[SafeCommand], None] | None = None,
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        self.engine = engine
        self.on_selected = on_selected
        self.on_closed = on_closed
        self.window = Gtk.ApplicationWindow(application=application)
        self.window.set_title("Ubuntu Glove Commands")
        self.window.set_default_size(680, 500)
        self.window.set_modal(False)
        self.window.connect("close-request", self._close_request)
        self._build()
        self._populate()

    def _build(self) -> None:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        outer.set_margin_top(18)
        outer.set_margin_bottom(18)
        outer.set_margin_start(18)
        outer.set_margin_end(18)
        self.window.set_child(outer)

        title = Gtk.Label(label="Command palette")
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        outer.append(title)
        explanation = Gtk.Label(label="Commands are staged in the clipboard; Ubuntu Glove never executes them automatically.")
        explanation.set_halign(Gtk.Align.START)
        explanation.set_wrap(True)
        outer.append(explanation)

        filters = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.search = Gtk.SearchEntry()
        self.search.set_hexpand(True)
        self.search.set_placeholder_text("e.g. check hardware temps, unzip a tar file")
        self.search.connect("search-changed", lambda *_: self._populate())
        self.search.connect("activate", self._choose_first)
        filters.append(self.search)
        self.category_model = Gtk.StringList.new(["All", *self.engine.categories])
        self.category = Gtk.DropDown.new(self.category_model, None)
        self.category.connect("notify::selected", lambda *_: self._populate())
        filters.append(self.category)
        outer.append(filters)

        self.result_count = Gtk.Label()
        self.result_count.set_halign(Gtk.Align.START)
        outer.append(self.result_count)
        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        self.rows = Gtk.ListBox()
        self.rows.set_selection_mode(Gtk.SelectionMode.NONE)
        scroller.set_child(self.rows)
        outer.append(scroller)

    def present(self) -> None:
        self.window.present()
        self.search.grab_focus()

    def _selected_category(self) -> str | None:
        item = self.category.get_selected_item()
        value = item.get_string() if item else "All"
        return None if value == "All" else value

    def _matches(self) -> list[SafeCommand]:
        return self.engine.search_commands(self.search.get_text(), self._selected_category())

    def _populate(self) -> None:
        child = self.rows.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.rows.remove(child)
            child = next_child
        matches = self._matches()
        self.result_count.set_text(f"{len(matches)} matching curated command{'s' if len(matches) != 1 else ''}")
        for command in matches:
            button = Gtk.Button()
            button.set_hexpand(True)
            button.set_halign(Gtk.Align.FILL)
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            content.set_margin_top(8)
            content.set_margin_bottom(8)
            content.set_margin_start(8)
            content.set_margin_end(8)
            description = Gtk.Label(label=command.description)
            description.set_halign(Gtk.Align.START)
            description.set_wrap(True)
            command_text = Gtk.Label(label=command.command)
            command_text.set_halign(Gtk.Align.START)
            command_text.add_css_class("monospace")
            category = Gtk.Label(label=command.category)
            category.set_halign(Gtk.Align.START)
            category.add_css_class("caption")
            content.append(description)
            content.append(command_text)
            content.append(category)
            button.set_child(content)
            button.connect("clicked", self._select, command)
            self.rows.append(button)
        if not matches:
            empty = Gtk.Label(label="No curated command matches. Try different wording or add a record to data/viable_commands.json.")
            empty.set_wrap(True)
            empty.set_margin_top(18)
            self.rows.append(empty)

    def _choose_first(self, *_args: object) -> None:
        matches = self._matches()
        if matches:
            self._select(None, matches[0])

    def _select(self, _button: Gtk.Button | None, command: SafeCommand) -> None:
        display = Gdk.Display.get_default()
        if display:
            display.get_clipboard().set(command.command)
        if self.on_selected:
            self.on_selected(command)
        self.window.close()

    def _close_request(self, *_args: object) -> bool:
        if self.on_closed:
            self.on_closed()
        return False
