import gi
import logging
from typing import Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from uno.game import Game, Player, Card, Turn, GameEventType
from main_view import MainView
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
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)

        self.main_view = MainView()
        self.main_view.new_game_btn.connect("clicked", self.on_new_game)
        self.stack.add_named(self.main_view, "main")

        self.game_view = GameView()
        self.stack.add_named(self.game_view, "game")

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

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(self.header_bar)
        toolbar_view.set_content(self.stack)

        self.set_content(toolbar_view)

    def on_new_game(self, button):
        cards = int(self.main_view.cards_spin.get_value())
        players = int(self.main_view.players_spin.get_value())
        card_stacking = self.main_view.card_stacking.get_active()
        vs_computer = self.main_view.is_vs_computer()

        # Inicjalizuj grę
        if vs_computer:
            p1 = Player(_("You"))
            p2 = Player(_("Computer"))
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

        # Aktualizuj widok gry
        self.game_view.setup_game(self.game, self.human_player, self.on_card_played, self.on_draw_card,
                                  self.on_color_selected)
        self.back_btn.set_visible(True)
        self.stack.set_visible_child_name("game")

    def on_card_played(self, card: Card, callback):
        """Callback gdy gracz zagrał kartę"""
        try:
            event = self.game.play(card, self.human_player)

            # Jeśli to karta wildcard, poproś o wybranie koloru
            if event.type == GameEventType.AWAIT_COLOR_INPUT:
                self.game_view.show_color_picker(callback)
            else:
                callback(None)

        except Exception as e:
            logging.error(_(f"Error while playing card: {e}"))
            self.game_view.show_error(str(e))

    def on_draw_card(self, callback):
        """Callback gdy gracz wylosuje kartę"""
        self.game.deal_card(self.human_player)
        callback()

    def on_color_selected(self, color, callback):
        """Callback gdy gracz wybrał kolor dla karty wildcard"""
        self.game.last_played_card.color = color
        callback()

    def on_back_clicked(self, button):
        self.stack.set_visible_child_name("main")
        self.back_btn.set_visible(False)
        self.game = None
        self.human_player = None

    def on_info_clicked(self, button):
        show_about(self)