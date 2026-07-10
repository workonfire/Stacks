import gi
import logging
import asyncio
import threading
from typing import Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from stackslib.game import Game, Player
from main_view import MainView, SingleplayerSetupView, MultiplayerRoomView
from game_view import GameView
from about_dialog import show_about
from i18n import _

logging.basicConfig(level=logging.DEBUG)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(900, 700)
        self.set_title("Stacks")
        self.game: Optional[Game] = None
        self.human_player: Optional[Player] = None
        self.setup_ui()

    def setup_ui(self):
        self.navigation_view = Adw.NavigationView()

        self.main_view = MainView()
        self.main_view.singleplayer_btn.connect("clicked", self.on_singleplayer_clicked)
        self.main_view.multiplayer_btn.connect("clicked", self.on_multiplayer_clicked)
        self.main_page = Adw.NavigationPage.new(self.main_view, _("Stacks"))
        self.main_page.set_tag("main")
        self.navigation_view.add(self.main_page)

        self.singleplayer_setup_view = SingleplayerSetupView()
        self.singleplayer_setup_view.new_game_btn.connect("clicked", self.on_new_game_clicked)
        self.singleplayer_setup_page = Adw.NavigationPage.new(self.singleplayer_setup_view, _("Singleplayer"))
        self.singleplayer_setup_page.set_tag("singleplayer_setup")

        self.game_view = GameView()
        self.game_page = Adw.NavigationPage.new(self.game_view, _("Game"))
        self.game_page.set_tag("game")
        self.multiplayer_room_view: Optional[MultiplayerRoomView] = None
        self.current_page_tag = "main"

        self.back_btn = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("go-previous-symbolic")
        self.back_btn.set_child(icon)
        self.back_btn.set_valign(Gtk.Align.CENTER)
        self.back_btn.set_tooltip_text(_("Back to Menu"))
        self.back_btn.connect("clicked", self.on_back_clicked)
        self.back_btn.set_visible(False)

        info_btn = Gtk.Button(icon_name="dialog-information-symbolic")
        info_btn.set_valign(Gtk.Align.CENTER)
        info_btn.set_tooltip_text(_("About"))
        info_btn.connect("clicked", self.on_info_clicked)

        self.header_bar = Adw.HeaderBar()
        self.header_bar.pack_start(self.back_btn)
        self.header_bar.pack_end(info_btn)
        self.navigation_view.connect("notify::visible-page", self.on_visible_page_changed)

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(self.header_bar)
        toolbar_view.set_content(self.navigation_view)

        self.set_content(toolbar_view)

    def on_singleplayer_clicked(self, button):
        self.navigation_view.push(self.singleplayer_setup_page)

    def on_multiplayer_clicked(self, button):
        dialog = Adw.MessageDialog()
        dialog.set_heading(_("Connect to Multiplayer"))
        dialog.set_body(_("Enter the multiplayer server and room details."))

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)

        self.multiplayer_server_entry = Gtk.Entry()
        self.multiplayer_server_entry.set_text("ws://127.0.0.1:8765")
        self.multiplayer_server_entry.set_placeholder_text(_("Server address"))
        content_box.append(self._create_entry_box(_("Server address"), self.multiplayer_server_entry))

        self.multiplayer_name_entry = Gtk.Entry()
        self.multiplayer_name_entry.set_placeholder_text(_("Player name"))
        content_box.append(self._create_entry_box(_("Player name"), self.multiplayer_name_entry))

        self.multiplayer_room_entry = Gtk.Entry()
        self.multiplayer_room_entry.set_text("main")
        self.multiplayer_room_entry.set_placeholder_text(_("Room name"))
        content_box.append(self._create_entry_box(_("Room name"), self.multiplayer_room_entry))

        dialog.set_extra_child(content_box)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("connect", _("Connect"))
        dialog.set_response_appearance("connect", Adw.ResponseAppearance.SUGGESTED)
        if self:
            dialog.set_transient_for(self)
        dialog.connect("response", self.on_multiplayer_dialog_response)
        dialog.present()

    def on_new_game_clicked(self, button):
        self.start_game(
            cards=int(self.singleplayer_setup_view.cards_spin.get_value()),
            players=2,
            card_stacking=self.singleplayer_setup_view.card_stacking.get_active(),
            vs_computer=True,
        )

    def start_game(self, cards: int, players: int, card_stacking: bool, vs_computer: bool):
        logging.debug(f"[GAME] New game started: {players} player(s), {cards} starting cards, stacking={card_stacking}, vs_computer={vs_computer}")

        if vs_computer:
            p1 = Player(_("You"))
            p2 = Player(_("Computer"))
            p2.is_computer = True
            player_list = [p1, p2]
        else:
            player_list = [Player(f"Player {i + 1}" if i > 0 else "You") for i in range(players)] # TODO

        self.human_player = player_list[0]

        rules = {
            'starting_cards': cards,
            'card_stacking': card_stacking,
            'cheats': False
        }

        self.game = Game(player_list, rules)

        self.game_view.setup_game(self.game, self.human_player)
        self.navigation_view.push(self.game_page)

    def on_back_clicked(self, button):
        visible_tag = self.navigation_view.get_visible_page_tag()
        if visible_tag == "game":
            self.navigation_view.pop_to_tag("main")
            self.game = None
            self.human_player = None
        elif visible_tag == "multiplayer_room":
            self.disconnect_multiplayer_room()
            self.navigation_view.pop()
        else:
            self.navigation_view.pop()

    def on_visible_page_changed(self, navigation_view, _param):
        if not hasattr(self, "back_btn"):
            return
        previous_page_tag = self.current_page_tag
        visible_page_tag = navigation_view.get_visible_page_tag()
        if previous_page_tag == "multiplayer_room" and visible_page_tag != "multiplayer_room":
            self.disconnect_multiplayer_room()
        self.current_page_tag = visible_page_tag
        self.back_btn.set_visible(visible_page_tag != "main")

    def on_info_clicked(self, button):
        show_about(self)

    def on_multiplayer_dialog_response(self, _dialog, response: str):
        if response != "connect":
            return

        server_uri = self.multiplayer_server_entry.get_text().strip()
        player_name = self.multiplayer_name_entry.get_text().strip().lower()
        room_name = self.multiplayer_room_entry.get_text().strip() or "main"

        if not server_uri:
            self.show_error(_("Server address is required."))
            return
        if not player_name:
            self.show_error(_("Player name is required."))
            return

        self.connect_to_multiplayer_room(server_uri, player_name, room_name)

    def connect_to_multiplayer_room(self, server_uri: str, player_name: str, room_name: str):
        thread = threading.Thread(
            target=self._run_multiplayer_preflight,
            args=(server_uri, player_name, room_name),
            daemon=True,
        )
        thread.start()

    def _run_multiplayer_preflight(self, server_uri: str, player_name: str, room_name: str):
        try:
            asyncio.run(self._check_multiplayer_server(server_uri))
        except Exception as error:
            GLib.idle_add(
                self.show_error,
                _("Connection error: {message}").format(message=error),
            )
            return

        GLib.idle_add(
            self.open_multiplayer_room,
            server_uri,
            player_name,
            room_name,
        )

    @staticmethod
    async def _check_multiplayer_server(server_uri: str):
        import websockets

        async with websockets.connect(server_uri):
            pass

    def open_multiplayer_room(self, server_uri: str, player_name: str, room_name: str):
        self.multiplayer_room_view = MultiplayerRoomView(
            server_uri,
            player_name,
            room_name,
            on_connection_error=self.show_error,
        )
        multiplayer_room_page = Adw.NavigationPage.new(self.multiplayer_room_view, _("Multiplayer"))
        multiplayer_room_page.set_tag("multiplayer_room")
        self.navigation_view.push(multiplayer_room_page)
        self.multiplayer_room_view.connect_to_server()
        return False

    def disconnect_multiplayer_room(self):
        if self.multiplayer_room_view is not None:
            self.multiplayer_room_view.disconnect()
            self.multiplayer_room_view = None

    def show_error(self, message: str):
        dialog = Adw.MessageDialog()
        dialog.set_heading(_("Error"))
        dialog.set_body(message)
        dialog.add_response("ok", _("OK"))
        dialog.set_transient_for(self)
        dialog.present()
        return False

    @staticmethod
    def _create_entry_box(label: str, entry: Gtk.Entry) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        label_widget = Gtk.Label(label=label)
        label_widget.set_halign(Gtk.Align.START)
        box.append(label_widget)
        box.append(entry)
        return box
