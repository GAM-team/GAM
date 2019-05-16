from xml.etree import ElementTree as ET
import requests
from html.parser import HTMLParser
import string
import dateutil.parser

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global next_data_is_oem, next_data_is_td
        if tag == 'h2' and attrs == [('class', 'zippy')]:
            next_data_is_oem = True
        elif tag == 'td':
            next_data_is_td = True

    def handle_data(self, data):
        global oem, next_data_is_oem, next_data_is_td, data_is_date, model, printable
        if next_data_is_oem:
            oem = ''.join(filter(lambda x: x in printable, data))
            next_data_is_oem = False
        elif next_data_is_td:
            if data_is_date:
                if model.lower().startswith(oem.lower()):
                    fullname = model
                else:
                    fullname = '%s %s' % (oem, model)
                date = dateutil.parser.parse(data).replace(day=1).strftime('%Y-%m-%dT00:00:00.000Z')
                print('  "%s": "%s",' % (fullname, date))
                if fullname in exceptions:
                    for value in exceptions[fullname]:
                        print('  "%s": "%s",' % (value, date))
                data_is_date = False
            else:
                model = ''.join(filter(lambda x: x in printable, data)).replace('"', '\\"')
                data_is_date = True
            next_data_is_td = False

global oem, next_data_is_oem, next_data_is_td, data_is_date, model, printable, exceptions
printable = set(string.printable)
exceptions = {
        # 'AUE "OEM MODEL': ['API MODEL 1', ...]
        'Acer Chromebook 11 (C720, C720P)': ['Acer C720 Chromebook', 'Acer C740 Chromebook'],
        'Acer Chromebook 315 (CB315-2H)': ['Acer Chromebook 315'],
        'CTL Chromebook NL7 / NL7T-360 / NL7TW-360': ['CTL Chromebook NL7'],
        'Lenovo ThinkPad 11e 3rd Gen Chromebook': ['ThinkPad 11e Chromebook 3rd Gen (Yoga/Clamshell)'],
        'Samsung Chromebook - XE303': ['Samsung Chromebook'],
        'HP Chromebook 11 G1': ['HP Chromebook 11 1100-1199 / HP Chromebook 11 G1'],
        'HP Chromebook 14 G4': ['HP Chromebook 14 ak000-099 / HP Chromebook 14 G4'],
        'HP Chromebook 14 G5': ['HP Chromebook 14 / HP Chromebook 14 G5'],
        }
next_data_is_oem = False
next_data_is_td = False
data_is_date = False
auepage = requests.get('https://support.google.com/chrome/a/answer/6220366?hl=en')
print('cros_aue = {')
parser = MyHTMLParser()
parser.feed(auepage.content.decode('utf-8'))
print('}')
