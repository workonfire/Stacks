import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
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
