import gi
import asyncio
import json
import threading
from typing import Any, Callable, Optional
from urllib.parse import urlparse

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from i18n import _


class MainView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        self.set_margin_top(48)
        self.set_margin_bottom(48)
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        icon = Gtk.Image.new_from_icon_name("pl.workonfire.Stacks")
        icon.set_pixel_size(128)
        self.append(icon)

        title_label = Gtk.Label(label=_("Welcome to Stacks!"))
        title_label.add_css_class("title-1")
        title_label.set_justify(Gtk.Justification.CENTER)
        self.append(title_label)

        buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        buttons_box.set_halign(Gtk.Align.CENTER)

        self.singleplayer_btn = Gtk.Button(label=_("Singleplayer"))
        self.singleplayer_btn.set_size_request(160, 52)
        self.singleplayer_btn.add_css_class("pill")
        self.singleplayer_btn.add_css_class("suggested-action")
        buttons_box.append(self.singleplayer_btn)

        self.multiplayer_btn = Gtk.Button(label=_("Multiplayer"))
        self.multiplayer_btn.set_size_request(160, 52)
        self.multiplayer_btn.add_css_class("pill")
        buttons_box.append(self.multiplayer_btn)

        self.append(buttons_box)


class SingleplayerSetupView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)

        title_label = Gtk.Label(label=_("Welcome to Stacks!"))
        title_label.add_css_class("title-1")
        self.append(title_label)

        subtitle_label = Gtk.Label(label=_("Configure your game settings"))
        subtitle_label.add_css_class("subtitle")
        self.append(subtitle_label)

        prefs_group = Adw.PreferencesGroup()
        prefs_group.set_title(_("Game Settings"))
        prefs_group.set_description(_("Configure how the game starts"))

        self.cards_spin = Adw.SpinRow()
        self.cards_spin.set_title(_("Starting cards"))
        self.cards_spin.set_subtitle(_("How many cards to give each player upon game launch"))
        self.cards_spin.set_adjustment(Gtk.Adjustment(value=7, lower=1, upper=20, step_increment=1))
        self.cards_spin.set_digits(0)
        prefs_group.add(self.cards_spin)

        self.card_stacking = Adw.SwitchRow()
        self.card_stacking.set_title(_("Card stacking"))
        self.card_stacking.set_subtitle(_("Automatically play similar cards"))
        self.card_stacking.set_active(True)
        prefs_group.add(self.card_stacking)

        self.append(prefs_group)

        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        buttons_box.set_halign(Gtk.Align.CENTER)
        buttons_box.set_margin_top(20)

        self.new_game_btn = Gtk.Button(label=_("Start New Game"))
        self.new_game_btn.set_size_request(150, 50)
        self.new_game_btn.add_css_class("pill")
        self.new_game_btn.add_css_class("suggested-action")
        buttons_box.append(self.new_game_btn)

        self.append(buttons_box)


class MultiplayerRoomView(Gtk.Box):
    def __init__(
        self,
        server_uri: str,
        player_name: str,
        room_name: str,
        on_connection_error: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)

        self.server_uri = server_uri
        self.player_name = player_name.lower()
        self.room_name = room_name or "main"
        self.websocket: Any | None = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.on_connection_error = on_connection_error
        self.active = True

        title_label = Gtk.Label(label=f"{self.player_name}@{self.room_name}")
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.START)
        self.append(title_label)

        parsed_server = self._parse_server(self.server_uri)
        server_text = f"{parsed_server[0]}:{parsed_server[1]}" if parsed_server[1] else parsed_server[0]
        server_label = Gtk.Label(label=server_text)
        server_label.add_css_class("subtitle")
        server_label.set_halign(Gtk.Align.START)
        self.append(server_label)

        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        content_box.set_vexpand(True)

        players_group = Adw.PreferencesGroup()
        players_group.set_title(_("Players"))
        players_group.set_size_request(220, -1)

        self.players_list = Gtk.ListBox()
        self.players_list.add_css_class("boxed-list")
        players_group.add(self.players_list)
        content_box.append(players_group)

        chat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        chat_box.set_hexpand(True)
        chat_box.set_vexpand(True)

        chat_label = Gtk.Label(label=_("Chat"))
        chat_label.add_css_class("title-3")
        chat_label.set_halign(Gtk.Align.START)
        chat_box.append(chat_label)

        chat_scroll = Gtk.ScrolledWindow()
        chat_scroll.set_hexpand(True)
        chat_scroll.set_vexpand(True)

        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_view.set_cursor_visible(False)
        self.chat_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        chat_scroll.set_child(self.chat_view)
        chat_box.append(chat_scroll)

        chat_input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.chat_entry = Gtk.Entry()
        self.chat_entry.set_placeholder_text(_("Message"))
        self.chat_entry.set_hexpand(True)
        self.chat_entry.connect("activate", self.on_send_chat)
        chat_input_box.append(self.chat_entry)

        send_btn = Gtk.Button(label=_("Send"))
        send_btn.connect("clicked", self.on_send_chat)
        chat_input_box.append(send_btn)
        chat_box.append(chat_input_box)

        content_box.append(chat_box)
        self.append(content_box)

        actions_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        actions_box.set_halign(Gtk.Align.END)

        self.status_label = Gtk.Label(label=_("Connecting..."))
        self.status_label.set_hexpand(True)
        self.status_label.set_halign(Gtk.Align.START)
        actions_box.append(self.status_label)

        self.start_game_btn = Gtk.Button(label=_("Start Game"))
        self.start_game_btn.add_css_class("suggested-action")
        self.start_game_btn.connect("clicked", self.on_start_game)
        actions_box.append(self.start_game_btn)

        self.append(actions_box)

    def connect_to_server(self):
        self._append_chat(_("Connecting to {server}...").format(server=self.server_uri))
        thread = threading.Thread(target=self._run_network_client, daemon=True)
        thread.start()

    def disconnect(self):
        self.active = False
        if self.loop is not None and self.websocket is not None:
            asyncio.run_coroutine_threadsafe(self._disconnect_async(), self.loop)

    def on_start_game(self, _button):
        self._send({"action": "start"})

    def on_send_chat(self, _widget):
        text = self.chat_entry.get_text().strip()
        if not text:
            return
        self.chat_entry.set_text("")
        self._send({"action": "chat", "message": text})

    def _run_network_client(self):
        asyncio.run(self._network_client())

    async def _network_client(self):
        try:
            import websockets

            self.loop = asyncio.get_running_loop()
            async with websockets.connect(self.server_uri) as websocket:
                self.websocket = websocket
                await self._send_async({
                    "action": "join",
                    "name": self.player_name,
                    "room": self.room_name,
                })
                GLib.idle_add(self._set_connected, True)

                async for raw_message in websocket:
                    if not self.active:
                        break
                    GLib.idle_add(self._handle_message, raw_message)
        except Exception as error:
            GLib.idle_add(self._show_connection_error, str(error))
        finally:
            self.websocket = None
            self.loop = None
            GLib.idle_add(self._set_connected, False)

    async def _disconnect_async(self):
        if self.websocket is None:
            return
        try:
            await self._send_async({"action": "leave"})
            await self.websocket.close()
        except Exception:
            pass

    def _send(self, message: dict[str, Any]):
        if self.loop is None or self.websocket is None:
            self._append_chat(_("Not connected."))
            return
        asyncio.run_coroutine_threadsafe(self._send_async(message), self.loop)

    async def _send_async(self, message: dict[str, Any]):
        if self.websocket is not None:
            await self.websocket.send(json.dumps(message))

    def _handle_message(self, raw_message: str):
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            self._append_chat(_("Server sent invalid data."))
            return False

        message_type = message.get("type")
        if message_type == "lobby":
            self._update_players(message.get("players", []))
        elif message_type == "state":
            state = message.get("state", {})
            self._update_players(state.get("players", []), state.get("turn"))
            self._append_chat(_("Game started."))
        elif message_type == "chat":
            self._append_chat("{player}: {message}".format(
                player=message.get("player", ""),
                message=message.get("message", ""),
            ))
        elif message_type in ("info", "error"):
            self._append_chat(str(message.get("message", "")))
        return False

    def _update_players(self, players: list[dict[str, Any]], current_turn: str | None = None):
        rows = []
        row = self.players_list.get_first_child()
        while row is not None:
            rows.append(row)
            row = row.get_next_sibling()

        for row in rows:
            self.players_list.remove(row)

        if not players:
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=_("No players"), xalign=0))
            self.players_list.append(row)
            return

        for player in players:
            name = str(player.get("name", ""))
            cards = player.get("cards")
            label = name if cards is None else f"{name} ({cards})"
            if current_turn == name:
                label = f"> {label}"
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=label, xalign=0))
            self.players_list.append(row)

    def _append_chat(self, message: str):
        buffer = self.chat_view.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, f"{message}\n")
        return False

    def _set_connected(self, connected: bool):
        self.status_label.set_text(_("Connected") if connected else _("Disconnected"))
        return False

    def _show_connection_error(self, message: str):
        error_message = _("Connection error: {message}").format(message=message)
        self._append_chat(error_message)
        if self.on_connection_error is not None:
            self.on_connection_error(error_message)
        return False

    @staticmethod
    def _parse_server(server_uri: str) -> tuple[str, str]:
        parsed = urlparse(server_uri)
        if parsed.hostname is None:
            return server_uri, ""
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "wss" else 80
        return parsed.hostname, str(port)
