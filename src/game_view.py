import gi

from uno.game import Card

gi.require_version('Gtk', '4.0')

from gi.repository import Gtk

class GameView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_margin_top(20)
        self.set_margin_bottom(20)
        self.set_margin_start(20)
        self.set_margin_end(20)

    def update_game_info(self, players, cards, card_stacking):
        for child in list(self):
            self.remove(child)

        title = Gtk.Label(label=f"Game started with {players} players and {cards} cards each.")
        title.add_css_class("title-2")
        self.append(title)

        card_stacking_label = Gtk.Label(label=f"Card stacking is {'enabled' if card_stacking else 'disabled'}.")
        self.append(card_stacking_label)

        card = Card.from_str('8 BLUE')
        test_label = Gtk.Label(label=card)
        self.append(test_label)
