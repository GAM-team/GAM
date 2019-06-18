#!/usr/bin/env python3

from xml.etree import ElementTree as ET
import requests
from html.parser import HTMLParser
import string
import sys
import json
import dateutil.parser

class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        global next_data_is_oem, next_data_is_td
        if tag == 'h2' and attrs == [('class', 'zippy')]:
            next_data_is_oem = True
        elif tag == 'td':
            next_data_is_td = True

    def handle_data(self, data):
        global oem, next_data_is_oem, next_data_is_td, data_is_date, model, printable, output_rows
        if next_data_is_oem:
            oem = ''.join(filter(lambda x: x in printable, data))
            next_data_is_oem = False
        elif next_data_is_td:
            if data_is_date:
                if model.lower().startswith(oem.lower()):
                    fullname = model.lower()
                else:
                    fullname = '%s %s' % (oem, model)
                    fullname = fullname.lower()
                date = dateutil.parser.parse(data).replace(day=1).strftime('%Y-%m-%dT00:00:00.000Z')
                output_rows[fullname] = date
                if fullname in exceptions:
                    for value in exceptions[fullname]:
                        output_rows[value] = date
                data_is_date = False
            else:
                model = ''.join(filter(lambda x: x in printable, data))
                data_is_date = True
            next_data_is_td = False

global oem, next_data_is_oem, next_data_is_td, data_is_date, model, printable, exceptions, output_rows
output_rows = {}
printable = set(string.printable)
exceptions = {
        # 'AUE OEM MODEL': ['API MODEL 1', ...]
        'acer c7 chromebook': ['acer c7 chromebook (c710)'],
        'acer chromebook 11 (c720, c720p)': ['acer c720 chromebook', 'acer c740 chromebook'],
        'acer chromebook 11 (cb3-111, c730, c730e)': ['chromebook 11 (c730 / cb3-111)'],
        'acer chromebook 11 (cb3-131, c735)': ['chromebook 11 (c735)'],
        'acer chromebook 15 (cb515-1h,cb515-1ht)': ['chromebook 15 (cb515 - 1ht / 1h)'],
        'acer chromebook 13(cb5-311, c810)': ['acer chromebook 13 (cb5-311)'],
        'acer chromebook 15 (cb5-571, c910)': ['acer chromebook 15 (c910 / cb5-571)'],
        'acer chromebook 311 (c721, c733, c733u, c733t)': ['acer chromebook 311', 'chromebook 311 (c721)'],
        'acer chromebook 315 (cb315-2h)': ['acer chromebook 315'],
        'acer chromebook spin 311 (r721t)': ['acer chromebook 311'],
        'acer chromebook spin 511 (r752t, r752tn)': ['acer chromebook spin 511'],
        'acer chromebox cxi2 / cxv2': ['acer chromebox cxi2'],
        'asus chromebook c200': ['asus chromebook c200ma'],
        'asus chromebook c201pa': ['asus chromebook c201pa'],
        'asus chromebook c204': ['asus chromebook c204'],
        'asus chromebook c300': ['asus chromebook c300ma'],
        'asus chromebook flip c213': ['asus chromebook c213na'],
        'asus chromebox 2 (cn62)': ['asus chromebox cn62'],
        'asus chromebox 3 (cn65)': ['asus chromebox 3'],
        'asus chromebox (cn60)': ['asus chromebox cn60'],
        'ctl chromebook nl7 / nl7t-360 / nl7tw-360': ['ctl chromebook nl7'],
        'ctl chromebook tablet tx1 for education': ['ctl chromebook tab tx1'],
        'ctl nl61 chromebook': ['mecer v2 chromebook'],
        'google cr-48': ['cr-48'],
        'haier chromebook 11e': ['chromebook pcm-116e', 'lumos education chromebook'],
        'haier chromebook 11': ['true idc chromebook 11', 'xolo chromebook'],
        'hisense chromebook 11': ['epik 11.6" chromebook  elb1101', 'mecer chromebook', 'videonet chromebook bl10'],
        'hp chromebook 11 g1': ['hp chromebook 11 1100-1199 / hp chromebook 11 g1'],
        'hp chromebook 11 g2': ['hp chromebook 11 2000-2099 / hp chromebook 11 g2'],
        'hp chromebook 11 g3': ['hp chromebook 11 2100-2199 / hp chromebook 11 g3'],
        'hp chromebook 11 g4/g4 ee': ['hp chromebook 11 2200-2299 / hp chromebook 11 g4/g4 ee'],
        'hp chromebook 11 g5': ['hp chromebook 11 g5 / hp chromebook 11-vxxx'],
        'hp chromebook 14a g5': ['hp chromebook 14 db0000-db0999'],
        'hp chromebook 14 g3': ['hp chromebook 14 x000-x999 / hp chromebook 14 g3'],
        'hp chromebook 14 g4': ['hp chromebook 14 ak000-099 / hp chromebook 14 g4'],
        'hp chromebook 14 g5': ['hp chromebook 14 / hp chromebook 14 g5'],
        'hp chromebox g1': ['hp chromebox cb1-(000-099) / hp chromebox g1/ hp chromebox for meetings'],
        'lenovo ideapad c330 chromebook': ['lenovo chromebook c330'],
        'lenovo ideapad s330 chromebook': ['lenovo chromebook s330'],
        'lenovo n21 chromebook': ['asi chromebook', 'crambo chromebook', 'jp sa couto chromebook', 'rgs education chromebook', 'true idc chromebook', 'videonet chromebook', 'consumer chromebook'],
        'lenovo thinkpad 11e 3rd gen chromebook': ['thinkpad 11e chromebook 3rd gen (yoga/clamshell)'],
        'lenovo thinkpad 11e 4th gen chromebook': ['lenovo thinkpad 11e chromebook (4th gen)/lenovo thinkpad yoga 11e chromebook (4th gen)'],
        'lenovo thinkpad 13': ['thinkpad 13 chromebook'],
        'poin2 chromebook 14': ['poin2 chromebook 11c'],
        'prowise chromebook eduline': ['viglen chromebook 11c'],
        'prowise chromebook entryline': ['prowise 11.6\" entry line chromebook'],
        'prowise chromebook proline': ['prowise proline chromebook'],
        'samsung chromebook - xe303': ['samsung chromebook'],
        }
next_data_is_oem = False
next_data_is_td = False
data_is_date = False
auepage = requests.get('https://support.google.com/chrome/a/answer/6220366?hl=en')
parser = MyHTMLParser()
parser.feed(auepage.content.decode('utf-8'))
print(json.dumps(output_rows, indent=2, sort_keys=True))
