import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from i18n import _

class MainView(Gtk.Box):
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

        mode_group = Adw.PreferencesGroup()
        mode_group.set_title(_("Game Mode"))
        mode_group.set_description(_("Choose who you want to play with"))

        self.game_mode = Adw.ComboRow()
        self.game_mode.set_title(_("Game Mode"))
        self.game_mode.set_model(Gtk.StringList.new([_("Player vs Player"), _("Player vs Computer")]))
        self.game_mode.set_selected(0)
        mode_group.add(self.game_mode)

        self.append(mode_group)

        prefs_group = Adw.PreferencesGroup()
        prefs_group.set_title(_("Game Settings"))
        prefs_group.set_description(_("Configure how the game starts"))

        self.cards_spin = Adw.SpinRow()
        self.cards_spin.set_title(_("Starting cards"))
        self.cards_spin.set_subtitle(_("How many cards to give each player upon game launch"))
        self.cards_spin.set_adjustment(Gtk.Adjustment(value=7, lower=1, upper=20, step_increment=1))
        self.cards_spin.set_digits(0)
        prefs_group.add(self.cards_spin)

        self.players_spin = Adw.SpinRow()
        self.players_spin.set_title(_("Number of players"))
        self.players_spin.set_subtitle(_("How many players will participate"))
        self.players_spin.set_adjustment(Gtk.Adjustment(value=2, lower=2, upper=8, step_increment=1))
        self.players_spin.set_digits(0)
        prefs_group.add(self.players_spin)

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

        self.settings_btn = Gtk.Button(label=_("Settings"))
        self.settings_btn.set_size_request(100, 50)
        self.settings_btn.add_css_class("pill")
        buttons_box.append(self.settings_btn)

        self.append(buttons_box)

    def is_vs_computer(self) -> bool:
        return self.game_mode.get_selected() == 1