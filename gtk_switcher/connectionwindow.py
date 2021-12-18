import time
from urllib.parse import urlparse, quote

import gi

from gtk_switcher.preferences import PreferencesWindow
from pyatem import locate

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject, Gio, GdkPixbuf

gi.require_version('Handy', '1')
from gi.repository import Handy


class ConnectionWindow:
    def __init__(self, parent, connection, application):
        builder = Gtk.Builder()
        builder.add_from_resource('/nl/brixit/switcher/ui/connection.glade')
        builder.connect_signals(Handler(builder, parent, application, connection))

        window = builder.get_object("preferences_window")

        window.set_transient_for(parent)
        window.set_modal(True)

        window.show_all()


class Item(GObject.GObject):
    text = GObject.property(type=str)

    def __init__(self, text):
        GObject.GObject.__init__(self)
        self.text = text


class Handler:
    def __init__(self, builder, parent, application, connection):
        self.builder = builder
        self.parent = parent
        self.application = application
        self.connection = connection
        self.window = builder.get_object('preferences_window')

        self.ipaddress = builder.get_object('ipaddress')
        self.username = builder.get_object('username')
        self.password = builder.get_object('password')
        self.device = builder.get_object('device')
        self.avahi_list = builder.get_object('avahi_list')

        self.connection_udp = builder.get_object('connection_udp')
        self.connection_usb = builder.get_object('connection_usb')
        self.connection_tcp = builder.get_object('connection_tcp')

        self.settings = Gio.Settings.new('nl.brixit.Switcher')
        self.settings.connect('changed::switcher-ip', self.on_switcher_ip_changed)

        self.on_switcher_ip_changed(self.settings, 'switcher-ip')
        locate.listen(self.on_discovered)

    def on_discovered(self, name, subtitle, proto, address):
        GLib.idle_add(self.on_discovered_ui, name, subtitle, proto, address)

    def on_discovered_ui(self, name, subtitle, proto, address):
        label = Gtk.Label(address[0])
        label.address = address
        label.proto = proto
        ar = Handy.ActionRow()
        ar.set_title(name)
        ar.set_subtitle(subtitle)
        ar.add(label)
        time.sleep(0.1)
        self.avahi_list.add(ar)
        time.sleep(0.1)
        self.avahi_list.show_all()

    def on_lost(self, address):
        print('lost', address)

    def on_avahi_activate(self, widget, row):
        label = list(row)[0]
        if label.proto == 'udp':
            self.connection_udp.set_active(True)
            self.ipaddress.set_text(str(label.address[0]))
        elif label.proto == 'tcp':
            self.connection_tcp.set_active(True)
            self.ipaddress.set_text(f'{label.address[0]}:{label.address[1]}')
        elif label.proto == 'usb':
            self.ipaddress.set_text('')
            self.connection_usb.set_active(True)

    def on_destroy(self, *args):
        locate.stop()

    def on_save_clicked(self, *args):
        if self.connection_udp.get_active():
            self.settings.set_string('switcher-ip', self.ipaddress.get_text())
        elif self.connection_usb.get_active():
            self.settings.set_string('switcher-ip', "0.0.0.0")
        else:
            url = 'tcp://'
            username = self.username.get_text()
            password = self.password.get_text()
            if username != "":
                url += f"{quote(username)}:{quote(password)}@"
            url += self.ipaddress.get_text()
            url += '/' + self.device.get_text()
            print("New connection url: " + str(url))
            self.settings.set_string('switcher-ip', url)
        self.window.close()

    def fix_widget_state(self):
        if self.connection_udp.get_active():
            self.ipaddress.set_sensitive(True)
            self.username.set_sensitive(False)
            self.password.set_sensitive(False)
            self.device.set_sensitive(False)
        elif self.connection_usb.get_active():
            self.ipaddress.set_sensitive(False)
            self.username.set_sensitive(False)
            self.password.set_sensitive(False)
            self.device.set_sensitive(False)
        else:
            self.ipaddress.set_sensitive(True)
            self.username.set_sensitive(True)
            self.password.set_sensitive(True)
            self.device.set_sensitive(True)

    def on_connection_change(self, *args):
        self.fix_widget_state()

    def on_switcher_ip_changed(self, settings, key, *args):
        if key == 'switcher-ip':
            value = self.settings.get_string('switcher-ip')
            if value.startswith('tcp://'):
                part = urlparse(value)
                address = part.hostname
                if part.port:
                    address += ':' + str(part.port)
                self.ipaddress.set_text(address)

                if part.username is None:
                    self.username.set_text("")
                else:
                    self.username.set_text(part.username)

                if part.password is None:
                    self.password.set_text("")
                else:
                    self.password.set_text(part.password)
                self.device.set_text(part.path[1:])

                self.connection_tcp.set_active(True)

            elif value == '0.0.0.0':
                self.connection_usb.set_active(True)
                self.ipaddress.set_text("")
            else:
                self.connection_udp.set_active(True)
                self.ipaddress.set_text(value)
            self.fix_widget_state()

    def on_preferences_clicked(self, *args):
        PreferencesWindow(self.parent, self.application, self.connection)
