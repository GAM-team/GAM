# -*- coding: utf-8 -*-
#
# Copyright (c) 2007 Benoit Chesneau <benoitc@metavers.net>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


"""Contains extensions to Atom objects used by Google Codesearch"""

__author__ = 'Benoit Chesneau'


import atom
import gdata


CODESEARCH_NAMESPACE='http://schemas.google.com/codesearch/2006'
CODESEARCH_TEMPLATE='{http://shema.google.com/codesearch/2006}%s'


class Match(atom.AtomBase):
    """ The Google Codesearch match element """
    _tag = 'match'
    _namespace = CODESEARCH_NAMESPACE
    _children = atom.AtomBase._children.copy()
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['lineNumber'] = 'line_number'
    _attributes['type'] = 'type'

    def __init__(self, line_number=None, type=None, extension_elements=None,
            extension_attributes=None, text=None):
        self.text = text
        self.type = type
        self.line_number = line_number 
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


class File(atom.AtomBase):
    """ The Google Codesearch file element"""
    _tag = 'file'
    _namespace = CODESEARCH_NAMESPACE
    _children = atom.AtomBase._children.copy()
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['name'] = 'name'

    def __init__(self, name=None, extension_elements=None,
            extension_attributes=None, text=None):
        self.text = text
        self.name = name
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


class Package(atom.AtomBase):
    """ The Google Codesearch package element"""
    _tag = 'package'
    _namespace = CODESEARCH_NAMESPACE
    _children = atom.AtomBase._children.copy()
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['name'] = 'name'
    _attributes['uri'] = 'uri'

    def __init__(self, name=None, uri=None, extension_elements=None,
            extension_attributes=None, text=None):
        self.text = text
        self.name = name
        self.uri = uri
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


class CodesearchEntry(gdata.GDataEntry):
    """ Google codesearch atom entry"""
    _tag = gdata.GDataEntry._tag
    _namespace = gdata.GDataEntry._namespace
    _children = gdata.GDataEntry._children.copy()
    _attributes = gdata.GDataEntry._attributes.copy()
    
    _children['{%s}file' % CODESEARCH_NAMESPACE] = ('file', File)
    _children['{%s}package' % CODESEARCH_NAMESPACE] = ('package', Package)
    _children['{%s}match' % CODESEARCH_NAMESPACE] = ('match', [Match])
    
    def __init__(self, author=None, category=None, content=None,
            atom_id=None, link=None, published=None, 
            title=None, updated=None, 
            match=None, 
            extension_elements=None, extension_attributes=None, text=None):
        
        gdata.GDataEntry.__init__(self, author=author, category=category, 
                content=content, atom_id=atom_id, link=link, 
                published=published, title=title, 
                updated=updated, text=None)

        self.match = match or []


def CodesearchEntryFromString(xml_string):
    """Converts an XML string into a CodesearchEntry object.

    Args:
        xml_string: string The XML describing a Codesearch feed entry.

    Returns:
        A CodesearchEntry object corresponding to the given XML.
    """
    return atom.CreateClassFromXMLString(CodesearchEntry, xml_string)


class CodesearchFeed(gdata.GDataFeed):
    """feed containing list of Google codesearch Items"""
    _tag = gdata.GDataFeed._tag
    _namespace = gdata.GDataFeed._namespace
    _children = gdata.GDataFeed._children.copy()
    _attributes = gdata.GDataFeed._attributes.copy()
    _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [CodesearchEntry])

    
def CodesearchFeedFromString(xml_string):
    """Converts an XML string into a CodesearchFeed object.
    Args:
    xml_string: string The XML describing a Codesearch feed.
    Returns:
    A CodeseartchFeed object corresponding to the given XML.
    """
    return atom.CreateClassFromXMLString(CodesearchFeed, xml_string)
