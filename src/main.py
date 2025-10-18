import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from main_window import MainWindow

APP_ID = "pl.workonfire.Stacks"

class MyApplication(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_application_id(APP_ID)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        if not hasattr(self, 'win') or self.win is None:
            self.win = MainWindow(application=app)
        self.win.present()

def main():
    app = MyApplication()
    return app.run(sys.argv)

if __name__ == '__main__':
    main()
