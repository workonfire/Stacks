import gi
import logging
from typing import Callable, Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from uno.game import Game, Player, Card, Turn, GameEventType
from uno.enums import CardColor


class CardButton(Gtk.Button):
    """Przycisk reprezentujący kartę"""

    def __init__(self, card: Card, on_clicked: Callable):
        super().__init__()
        self.card = card
        self.set_size_request(80, 120)

        label = Gtk.Label(label=str(card.card_type.name.replace('CARD_', '')))
        label.set_wrap(True)
        label.set_justify(Gtk.Justification.CENTER)
        self.set_child(label)

        color_name = card.color.name.lower() if card.color else "gray"
        css_class = f"card-{color_name}"
        self.add_css_class(css_class)
        self.add_css_class("card-button")

        self.connect("clicked", on_clicked)


class GameView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(12)
        self.set_margin_bottom(12)
        self.set_margin_start(12)
        self.set_margin_end(12)

        self.game: Optional[Game] = None
        self.human_player: Optional[Player] = None
        self.on_card_played: Optional[Callable] = None
        self.on_draw_card: Optional[Callable] = None
        self.on_color_selected: Optional[Callable] = None
        self.parent_window: Optional[Gtk.Window] = None
        self.computer_thinking = False

        # Wewnętrzny box do zawartości
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.content_box)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        self.append(scroll)

    def setup_game(self, game: Game, human_player: Player, on_card_played: Callable,
                   on_draw_card: Callable, on_color_selected: Callable):
        """Inicjalizuje widok gry"""
        self.game = game
        self.human_player = human_player
        self.on_card_played = on_card_played
        self.on_draw_card = on_draw_card
        self.on_color_selected = on_color_selected
        self.parent_window = self.get_root()

        self.update_game()

        # Jeśli komputer zaczyna, niech czeka
        if self.game.turn != self.human_player and self.game.turn.is_computer:
            GLib.timeout_add(1000, self.computer_play_turn)

    def update_game(self):
        """Aktualizuje widok gry"""
        # Wyczyść poprzednią zawartość
        for child in list(self.content_box):
            self.content_box.remove(child)

        # Informacja o stanie gry
        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        info_box.set_halign(Gtk.Align.CENTER)

        current_player_label = Gtk.Label()
        current_player_label.set_markup(f"<b>Gracz:</b> {self.game.turn.name}")
        info_box.append(current_player_label)

        cards_left_label = Gtk.Label()
        cards_left_label.set_markup(f"<b>Karty na stole:</b> {len(self.game.stack)}")
        info_box.append(cards_left_label)

        self.content_box.append(info_box)

        # Ostatnia grana karta
        last_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        last_card_label = Gtk.Label()
        last_card_label.set_markup("<b>Ostatnia karta:</b>")
        last_card_box.append(last_card_label)

        last_card = self.game.last_played_card
        last_card_display = Gtk.Label(
            label=f"{last_card.card_type.name.replace('CARD_', '')}\n{last_card.color.name if last_card.color else 'WILDCARD'}"
        )
        last_card_display.set_justify(Gtk.Justification.CENTER)
        last_card_display.add_css_class(f"card-{last_card.color.name.lower() if last_card.color else 'gray'}")
        last_card_display.set_size_request(100, 140)
        last_card_box.append(last_card_display)

        last_card_box.set_halign(Gtk.Align.CENTER)
        self.content_box.append(last_card_box)

        # Gracze i ich karty
        players_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        players_box.set_halign(Gtk.Align.CENTER)

        for player in self.game.players:
            player_card = self._create_player_card(player)
            players_box.append(player_card)

        self.content_box.append(players_box)

        # Ręka gracza
        hand_label = Gtk.Label()
        hand_label.set_markup("<b>Twoje karty:</b>")
        self.content_box.append(hand_label)

        hand_box = Gtk.FlowBox()
        hand_box.set_halign(Gtk.Align.CENTER)
        hand_box.set_homogeneous(False)
        hand_box.set_column_spacing(8)
        hand_box.set_row_spacing(8)

        turn = Turn(self.game)
        for card in self.human_player.hand:
            is_playable = card.playable(self.game.last_played_card)
            card_btn = CardButton(card, lambda widget, c=card: self._on_card_clicked(c))
            if not is_playable or self.computer_thinking or self.game.turn != self.human_player:
                card_btn.set_sensitive(False)
            hand_box.append(card_btn)

        self.content_box.append(hand_box)

        # Przyciski akcji
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(12)

        if self.computer_thinking:
            thinking_label = Gtk.Label(label="Thinking...")
            thinking_label.add_css_class("title-3")
            action_box.append(thinking_label)
        elif self.game.turn == self.human_player:
            draw_btn = Gtk.Button(label="Wylosuj kartę")
            draw_btn.add_css_class("suggested-action")
            draw_btn.set_sensitive(not self.computer_thinking)
            draw_btn.connect("clicked", lambda w: self._on_draw_card())
            action_box.append(draw_btn)
        else:
            info_label = Gtk.Label(label=f"Czeka na ruch: {self.game.turn.name}")
            info_label.add_css_class("title-3")
            action_box.append(info_label)

        self.content_box.append(action_box)

    def _create_player_card(self, player: Player) -> Gtk.Box:
        """Tworzy kartę gracza"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_halign(Gtk.Align.CENTER)

        name_label = Gtk.Label()
        name_label.set_markup(f"<b>{player.name}</b>")
        box.append(name_label)

        cards_count_label = Gtk.Label(label=f"Karty: {len(player.hand)}")
        box.append(cards_count_label)

        if player == self.game.turn:
            box.add_css_class("player-active")

        return box

    def _on_card_clicked(self, card: Card):
        """Obsługa kliknięcia na kartę"""

        def callback(color=None):
            self.update_game()
            # Jeśli teraz kolej komputera, czekaj i graj
            if self.game.turn != self.human_player and self.game.turn.is_computer:
                GLib.timeout_add(500, self.computer_play_turn)

        self.on_card_played(card, callback)

    def _on_draw_card(self):
        """Obsługa wylosowania karty"""

        def callback():
            self.update_game()
            # Jeśli teraz kolej komputera, czekaj i graj
            if self.game.turn != self.human_player and self.game.turn.is_computer:
                GLib.timeout_add(500, self.computer_play_turn)

        self.on_draw_card(callback)

    def computer_play_turn(self) -> bool:
        """Obsługa tury komputera"""
        self.computer_thinking = True
        self.update_game()

        # Symuluj myślenie przez 500ms
        GLib.timeout_add(500, self._execute_computer_move)
        return False

    def _execute_computer_move(self) -> bool:
        """Wykonaj ruch komputera"""
        try:
            turn = Turn(self.game)
            playable_cards = turn.playable_cards

            if playable_cards:
                card_to_play = playable_cards[0]
                event = self.game.play(card_to_play, self.game.turn)

                # Obsłuż wildcard
                if event.type == GameEventType.AWAIT_COLOR_INPUT:
                    color = turn.most_reasonable_color
                    self.game.last_played_card.color = color
            else:
                self.game.deal_card(self.game.turn)

        except Exception as e:
            logging.error(f"Błąd przy ruchu komputera: {e}")

        self.computer_thinking = False
        self.update_game()

        # Jeśli teraz znowu kolej komputera, czekaj i graj
        if self.game.turn != self.human_player and self.game.turn.is_computer:
            GLib.timeout_add(500, self.computer_play_turn)

        return False

    def show_color_picker(self, callback: Callable):
        """Pokazuje dialog wyboru koloru"""
        dialog = Adw.MessageDialog()
        dialog.set_heading("Wybierz kolor")
        dialog.set_body("Wybrałeś kartę wildcard. Jaki kolor wybrałeś?")

        colors = ['BLUE', 'RED', 'GREEN', 'YELLOW']
        for i, color in enumerate(colors):
            dialog.add_response(str(i), color)

        if self.parent_window:
            dialog.set_transient_for(self.parent_window)
        dialog.connect("response", lambda d, response: self._on_color_picked(response, callback))
        dialog.present()

    def _on_color_picked(self, response: str, callback: Callable):
        """Obsługa wyboru koloru"""
        colors = [CardColor.BLUE, CardColor.RED, CardColor.GREEN, CardColor.YELLOW]
        color = colors[int(response)]
        self.on_color_selected(color, callback)

    def show_error(self, message: str):
        """Pokazuje dialog z błędem"""
        dialog = Adw.MessageDialog()
        dialog.set_heading("Błąd")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        if self.parent_window:
            dialog.set_transient_for(self.parent_window)
        dialog.present()