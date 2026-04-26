import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gdk', '4.0')

from gi.repository import Gtk, Adw, Gdk
from main_window import MainWindow

APP_ID = "pl.workonfire.Stacks"


class StacksApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.win = None
        self.set_application_id(APP_ID)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.load_css()
        self.load_icons()

        if not hasattr(self, 'win') or self.win is None:
            self.win = MainWindow(application=app)
        self.win.present()

    @staticmethod
    def load_icons():
        display = Gdk.Display.get_default()
        icon_theme = Gtk.IconTheme.get_for_display(display)
        icon_theme.add_search_path("icons")

    @staticmethod
    def load_css():
        css_provider = Gtk.CssProvider()
        try:
            css_provider.load_from_path("style.css")
            display = Gdk.Display.get_default()
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"An error occurred during CSS loading: {e}")


def main():
    app = StacksApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    main()