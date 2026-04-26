from gi.repository import Adw, Gtk

def show_about(parent):
    about = Adw.AboutWindow(
        application_name="Stacks",
        application_icon="dialog-information-symbolic",
        version="1.0-alpha",
        developer_name="workonfire",
        website="https://github.com/workonfire/Stacks",
        license_type=Gtk.License.MIT_X11,
    )
    about.set_transient_for(parent)
    about.set_modal(True)
    about.present()
