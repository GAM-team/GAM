import uuid
from lxml import etree
import sys

# Hacky solution to create a Guid for all files
# so Wix is happy and Guid is stable every time.
# uuid5 is used for the Guid and the input is the
# source filename so the Guid will be the same
# every time as long as the source file name is
# the same.

rewrite_file = sys.argv[1]

with open(rewrite_file, 'rb') as f:
    input_xml = f.read()
root = etree.fromstring(input_xml)
for elem in root.getiterator():
    if 'Guid' in elem.attrib:
        source = elem.getchildren()[0].attrib['Source']
        stable_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, source))
        elem.attrib['Guid'] = stable_uuid
with open(rewrite_file, 'w') as f:
  f.write(etree.tostring(root).decode())
