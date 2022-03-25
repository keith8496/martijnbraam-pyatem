import platform
from gi.repository import Gtk, GObject, Gio, GLib
import xml.etree.ElementTree as ET
import os

_PERFORM_MANUAL_TRANSLATION = platform.system() == "Windows" and not os.environ['LANGUAGE'].startswith("en")

class TemplateLocale(Gtk.Template):

    def __call__(self, cls):
        if not _PERFORM_MANUAL_TRANSLATION:
            return super(TemplateLocale, self).__call__(cls)

        element = Gio.resources_lookup_data(self.resource_path, Gio.ResourceLookupFlags.NONE) \
            .get_data().decode('utf-8')
        tree = ET.fromstring(element)
        for node in tree.iter():
            context = ''
            if 'context' in node.attrib:
                context = node.attrib['context'] + "\x04"
            if 'translatable' in node.attrib:
                node.text = _(context + node.text)
        as_str = ET.tostring(tree, encoding='unicode', method='xml')
        self.string = as_str
        return super(TemplateLocale, self).__call__(cls)