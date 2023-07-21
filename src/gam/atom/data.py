#!/usr/bin/env python
#
# Copyright (C) 2009 Google Inc.
#
# Licensed under the Apache License 2.0;



# This module is used for version 2 of the Google Data APIs.


# __author__ = 'j.s@google.com (Jeff Scudder)'

import atom.core

XML_TEMPLATE = '{http://www.w3.org/XML/1998/namespace}%s'
ATOM_TEMPLATE = '{http://www.w3.org/2005/Atom}%s'
APP_TEMPLATE_V1 = '{http://purl.org/atom/app#}%s'
APP_TEMPLATE_V2 = '{http://www.w3.org/2007/app}%s'


class Name(atom.core.XmlElement):
    """The atom:name element."""
    _qname = ATOM_TEMPLATE % 'name'


class Email(atom.core.XmlElement):
    """The atom:email element."""
    _qname = ATOM_TEMPLATE % 'email'


class Uri(atom.core.XmlElement):
    """The atom:uri element."""
    _qname = ATOM_TEMPLATE % 'uri'


class Person(atom.core.XmlElement):
    """A foundation class which atom:author and atom:contributor extend.

    A person contains information like name, email address, and web page URI for
    an author or contributor to an Atom feed.
    """
    name = Name
    email = Email
    uri = Uri


class Author(Person):
    """The atom:author element.

    An author is a required element in Feed unless each Entry contains an Author.
    """
    _qname = ATOM_TEMPLATE % 'author'


class Contributor(Person):
    """The atom:contributor element."""
    _qname = ATOM_TEMPLATE % 'contributor'


class Link(atom.core.XmlElement):
    """The atom:link element."""
    _qname = ATOM_TEMPLATE % 'link'
    href = 'href'
    rel = 'rel'
    type = 'type'
    hreflang = 'hreflang'
    title = 'title'
    length = 'length'


class Generator(atom.core.XmlElement):
    """The atom:generator element."""
    _qname = ATOM_TEMPLATE % 'generator'
    uri = 'uri'
    version = 'version'


class Text(atom.core.XmlElement):
    """A foundation class from which atom:title, summary, etc. extend.

    This class should never be instantiated.
    """
    type = 'type'


class Title(Text):
    """The atom:title element."""
    _qname = ATOM_TEMPLATE % 'title'


class Subtitle(Text):
    """The atom:subtitle element."""
    _qname = ATOM_TEMPLATE % 'subtitle'


class Rights(Text):
    """The atom:rights element."""
    _qname = ATOM_TEMPLATE % 'rights'


class Summary(Text):
    """The atom:summary element."""
    _qname = ATOM_TEMPLATE % 'summary'


class Content(Text):
    """The atom:content element."""
    _qname = ATOM_TEMPLATE % 'content'
    src = 'src'


class Category(atom.core.XmlElement):
    """The atom:category element."""
    _qname = ATOM_TEMPLATE % 'category'
    term = 'term'
    scheme = 'scheme'
    label = 'label'


class Id(atom.core.XmlElement):
    """The atom:id element."""
    _qname = ATOM_TEMPLATE % 'id'


class Icon(atom.core.XmlElement):
    """The atom:icon element."""
    _qname = ATOM_TEMPLATE % 'icon'


class Logo(atom.core.XmlElement):
    """The atom:logo element."""
    _qname = ATOM_TEMPLATE % 'logo'


class Draft(atom.core.XmlElement):
    """The app:draft element which indicates if this entry should be public."""
    _qname = (APP_TEMPLATE_V1 % 'draft', APP_TEMPLATE_V2 % 'draft')


class Control(atom.core.XmlElement):
    """The app:control element indicating restrictions on publication.

    The APP control element may contain a draft element indicating whether or
    not this entry should be publicly available.
    """
    _qname = (APP_TEMPLATE_V1 % 'control', APP_TEMPLATE_V2 % 'control')
    draft = Draft


class Date(atom.core.XmlElement):
    """A parent class for atom:updated, published, etc."""


class Updated(Date):
    """The atom:updated element."""
    _qname = ATOM_TEMPLATE % 'updated'


class Published(Date):
    """The atom:published element."""
    _qname = ATOM_TEMPLATE % 'published'


class LinkFinder(object):
    """An "interface" providing methods to find link elements

    Entry elements often contain multiple links which differ in the rel
    attribute or content type. Often, developers are interested in a specific
    type of link so this class provides methods to find specific classes of
    links.

    This class is used as a mixin in Atom entries and feeds.
    """

    def find_url(self, rel):
        """Returns the URL (as a string) in a link with the desired rel value."""
        for link in self.link:
            if link.rel == rel and link.href:
                return link.href
        return None

    FindUrl = find_url

    def get_link(self, rel):
        """Returns a link object which has the desired rel value.

        If you are interested in the URL instead of the link object,
        consider using find_url instead.
        """
        for link in self.link:
            if link.rel == rel and link.href:
                return link
        return None

    GetLink = get_link

    def find_self_link(self):
        """Find the first link with rel set to 'self'

        Returns:
          A str containing the link's href or None if none of the links had rel
          equal to 'self'
        """
        return self.find_url('self')

    FindSelfLink = find_self_link

    def get_self_link(self):
        return self.get_link('self')

    GetSelfLink = get_self_link

    def find_edit_link(self):
        return self.find_url('edit')

    FindEditLink = find_edit_link

    def get_edit_link(self):
        return self.get_link('edit')

    GetEditLink = get_edit_link

    def find_edit_media_link(self):
        link = self.find_url('edit-media')
        # Search for media-edit as well since Picasa API used media-edit instead.
        if link is None:
            return self.find_url('media-edit')
        return link

    FindEditMediaLink = find_edit_media_link

    def get_edit_media_link(self):
        link = self.get_link('edit-media')
        if link is None:
            return self.get_link('media-edit')
        return link

    GetEditMediaLink = get_edit_media_link

    def find_next_link(self):
        return self.find_url('next')

    FindNextLink = find_next_link

    def get_next_link(self):
        return self.get_link('next')

    GetNextLink = get_next_link

    def find_license_link(self):
        return self.find_url('license')

    FindLicenseLink = find_license_link

    def get_license_link(self):
        return self.get_link('license')

    GetLicenseLink = get_license_link

    def find_alternate_link(self):
        return self.find_url('alternate')

    FindAlternateLink = find_alternate_link

    def get_alternate_link(self):
        return self.get_link('alternate')

    GetAlternateLink = get_alternate_link


class FeedEntryParent(atom.core.XmlElement, LinkFinder):
    """A super class for atom:feed and entry, contains shared attributes"""
    author = [Author]
    category = [Category]
    contributor = [Contributor]
    id = Id
    link = [Link]
    rights = Rights
    title = Title
    updated = Updated

    def __init__(self, atom_id=None, text=None, *args, **kwargs):
        if atom_id is not None:
            self.id = atom_id
        atom.core.XmlElement.__init__(self, text=text, *args, **kwargs)


class Source(FeedEntryParent):
    """The atom:source element."""
    _qname = ATOM_TEMPLATE % 'source'
    generator = Generator
    icon = Icon
    logo = Logo
    subtitle = Subtitle


class Entry(FeedEntryParent):
    """The atom:entry element."""
    _qname = ATOM_TEMPLATE % 'entry'
    content = Content
    published = Published
    source = Source
    summary = Summary
    control = Control


class Feed(Source):
    """The atom:feed element which contains entries."""
    _qname = ATOM_TEMPLATE % 'feed'
    entry = [Entry]


class ExtensionElement(atom.core.XmlElement):
    """Provided for backwards compatibility to the v1 atom.ExtensionElement."""

    def __init__(self, tag=None, namespace=None, attributes=None,
                 children=None, text=None, *args, **kwargs):
        if namespace:
            self._qname = '{%s}%s' % (namespace, tag)
        else:
            self._qname = tag
        self.children = children or []
        self.attributes = attributes or {}
        self.text = text

    _BecomeChildElement = atom.core.XmlElement._become_child
