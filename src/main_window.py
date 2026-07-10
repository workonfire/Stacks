import gi
import logging
from typing import Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from stackslib.game import Game, Player
from main_view import MainView, SingleplayerSetupView
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
        self.start_game(
            cards=7,
            players=2,
            card_stacking=True,
            vs_computer=False,
        )

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
        if self.navigation_view.get_visible_page_tag() == "game":
            self.navigation_view.pop_to_tag("main")
            self.game = None
            self.human_player = None
        else:
            self.navigation_view.pop()

    def on_visible_page_changed(self, navigation_view, _param):
        if not hasattr(self, "back_btn"):
            return
        self.back_btn.set_visible(navigation_view.get_visible_page_tag() != "main")

    def on_info_clicked(self, button):
        show_about(self)
