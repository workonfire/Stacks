import gi
import logging
from typing import Callable, Optional

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib
from uno.game import Game, Player, Card, Turn, GameEventType
from uno.enums import CardColor
from i18n import _


class CardButton(Gtk.Button):

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
        self.parent_window: Optional[Gtk.Window] = None
        self.computer_thinking = False

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.content_box)
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        self.append(scroll)

    def setup_game(self, game: Game, human_player: Player):
        self.game = game
        self.human_player = human_player
        self.parent_window = self.get_root()

        self.update_game()

        if self.game.turn != self.human_player and self.game.turn.is_computer:
            GLib.timeout_add(1000, self.computer_play_turn)

    def update_game(self):
        for child in list(self.content_box):
            self.content_box.remove(child)

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        info_box.set_halign(Gtk.Align.CENTER)

        current_player_label = Gtk.Label()
        current_player_label.set_markup(_("<b>Player:</b> {name}").format(name=self.game.turn.name))
        info_box.append(current_player_label)

        cards_left_label = Gtk.Label()
        cards_left_label.set_markup(_("<b>Cards on table:</b> {count}").format(count=len(self.game.stack)))
        info_box.append(cards_left_label)

        self.content_box.append(info_box)

        last_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        last_card_label = Gtk.Label()
        last_card_label.set_markup(_("<b>Last card:</b>"))
        last_card_box.append(last_card_label)

        last_card = self.game.last_played_card
        last_card_display = Gtk.Label(
            label="{card_type}\n{color}".format(
                card_type=last_card.card_type.name.replace('CARD_', ''),
                color=last_card.color.name if last_card.color else _("WILDCARD"),
            )
        )
        last_card_display.set_justify(Gtk.Justification.CENTER)
        last_card_display.add_css_class(f"card-{last_card.color.name.lower() if last_card.color else 'gray'}")
        last_card_display.set_size_request(100, 140)
        last_card_box.append(last_card_display)

        last_card_box.set_halign(Gtk.Align.CENTER)
        self.content_box.append(last_card_box)

        players_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        players_box.set_halign(Gtk.Align.CENTER)

        for player in self.game.players:
            player_card = self._create_player_card(player)
            players_box.append(player_card)

        self.content_box.append(players_box)

        hand_label = Gtk.Label()
        hand_label.set_markup(_("<b>Your cards:</b>"))
        self.content_box.append(hand_label)

        hand_box = Gtk.FlowBox()
        hand_box.set_halign(Gtk.Align.CENTER)
        hand_box.set_homogeneous(False)
        hand_box.set_column_spacing(8)
        hand_box.set_row_spacing(8)

        for card in self.human_player.hand:
            is_playable = card.playable(self.game.last_played_card)
            card_btn = CardButton(card, lambda widget, c=card: self._on_card_clicked(c))
            if not is_playable or self.computer_thinking or self.game.turn != self.human_player:
                card_btn.set_sensitive(False)
            hand_box.append(card_btn)

        self.content_box.append(hand_box)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(12)

        if self.computer_thinking:
            thinking_label = Gtk.Label(label=_("Thinking..."))
            thinking_label.add_css_class("title-3")
            action_box.append(thinking_label)
        elif self.game.turn == self.human_player:
            draw_btn = Gtk.Button(label=_("Draw a card"))
            draw_btn.add_css_class("suggested-action")
            draw_btn.set_sensitive(not self.computer_thinking)
            draw_btn.connect("clicked", lambda w: self._on_draw_card())
            action_box.append(draw_btn)
        else:
            info_label = Gtk.Label(label=_("Waiting for move: {name}").format(name=self.game.turn.name))
            info_label.add_css_class("title-3")
            action_box.append(info_label)

        self.content_box.append(action_box)

    def _create_player_card(self, player: Player) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_halign(Gtk.Align.CENTER)

        name_label = Gtk.Label()
        name_label.set_markup(f"<b>{player.name}</b>")
        box.append(name_label)

        cards_count_label = Gtk.Label(label=_("Cards: {count}").format(count=len(player.hand)))
        box.append(cards_count_label)

        if player == self.game.turn:
            box.add_css_class("player-active")

        return box

    def _check_winner(self) -> bool:
        winner = self.game.get_winner()
        if winner:
            logging.debug(f"[WIN] {winner.name} won the game!")
            self.game.win(winner)
            self.update_game()
            self.show_winner(winner)
            return True
        return False

    def _after_human_move(self):
        if self._check_winner():
            return
        self.update_game()
        if self.game.turn != self.human_player and self.game.turn.is_computer:
            GLib.timeout_add(500, self.computer_play_turn)

    def _on_card_clicked(self, card: Card):
        try:
            event = self.game.play(card, self.human_player)
        except Exception as e:
            logging.error(_("Error while playing card: {error}").format(error=e))
            self.show_error(str(e))
            return

        if event.type == GameEventType.AWAIT_COLOR_INPUT:
            self.show_color_picker()
        else:
            self._after_human_move()

    def _on_draw_card(self):
        self.game.deal_card(self.human_player)
        self._after_human_move()

    def computer_play_turn(self) -> bool:
        self.computer_thinking = True
        self.update_game()

        GLib.timeout_add(500, self._execute_computer_move)
        return False

    def _execute_computer_move(self) -> bool:
        try:
            turn = Turn(self.game)
            playable_cards = turn.playable_cards
            logging.debug(f"[COMPUTER] {self.game.turn.name} has {len(playable_cards)} playable card(s): {[repr(c) for c in playable_cards]}")

            if playable_cards:
                card_to_play = playable_cards[0]
                event = self.game.play(card_to_play, self.game.turn)
            else:
                logging.debug(f"[COMPUTER] {self.game.turn.name} has no playable cards, drawing")
                self.game.deal_card(self.game.turn)

        except Exception as e:
            logging.error(_("Error during computer move: {error}").format(error=e))

        self.computer_thinking = False
        if self._check_winner():
            return False
        self.update_game()


        if self.game.turn != self.human_player and self.game.turn.is_computer:
            GLib.timeout_add(500, self.computer_play_turn)

        return False

    def show_color_picker(self):
        dialog = Adw.MessageDialog()
        dialog.set_heading(_("Choose color"))
        dialog.set_body(_("You played a wildcard. Which color do you choose?"))

        for i, color_label in enumerate([_("Blue"), _("Red"), _("Green"), _("Yellow")]):
            dialog.add_response(str(i), color_label)

        if self.parent_window:
            dialog.set_transient_for(self.parent_window)
        dialog.connect("response", self._on_color_picked)
        dialog.present()

    def _on_color_picked(self, _dialog, response: str):
        colors = [CardColor.BLUE, CardColor.RED, CardColor.GREEN, CardColor.YELLOW]
        color = colors[int(response)]
        logging.debug(f"[COLOR] Player chose color: {color.name}")
        self.game.last_played_card.color = color
        self._after_human_move()

    def show_winner(self, winner: Player):
        dialog = Adw.MessageDialog()
        dialog.set_heading(_("Game over!"))
        dialog.set_body(_("{name} won the game!").format(name=winner.name))
        dialog.add_response("ok", _("OK"))
        if self.parent_window:
            dialog.set_transient_for(self.parent_window)
        dialog.present()

    def show_error(self, message: str):
        dialog = Adw.MessageDialog()
        dialog.set_heading(_("Error"))
        dialog.set_body(message)
        dialog.add_response("ok", _("OK"))
        if self.parent_window:
            dialog.set_transient_for(self.parent_window)
        dialog.present()