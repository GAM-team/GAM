#!/usr/bin/python
#
# Copyright (C) 2008 Yu-Jie Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains extensions to Atom objects used with Google Webmaster Tools."""


__author__ = 'livibetter (Yu-Jie Lin)'


try:
  from xml.etree import cElementTree as ElementTree
except ImportError:
  try:
    import cElementTree as ElementTree
  except ImportError:
    try:
      from xml.etree import ElementTree
    except ImportError:
      from elementtree import ElementTree
import atom
import gdata


# XML namespaces which are often used in Google Webmaster Tools entities.
GWEBMASTERTOOLS_NAMESPACE = 'http://schemas.google.com/webmasters/tools/2007'
GWEBMASTERTOOLS_TEMPLATE = '{http://schemas.google.com/webmasters/tools/2007}%s'


class Indexed(atom.AtomBase):
  _tag = 'indexed'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def IndexedFromString(xml_string):
  return atom.CreateClassFromXMLString(Indexed, xml_string)


class Crawled(atom.Date):
  _tag = 'crawled'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def CrawledFromString(xml_string):
  return atom.CreateClassFromXMLString(Crawled, xml_string)


class GeoLocation(atom.AtomBase):
  _tag = 'geolocation'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def GeoLocationFromString(xml_string):
  return atom.CreateClassFromXMLString(GeoLocation, xml_string)


class PreferredDomain(atom.AtomBase):
  _tag = 'preferred-domain'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def PreferredDomainFromString(xml_string):
  return atom.CreateClassFromXMLString(PreferredDomain, xml_string)


class CrawlRate(atom.AtomBase):
  _tag = 'crawl-rate'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def CrawlRateFromString(xml_string):
  return atom.CreateClassFromXMLString(CrawlRate, xml_string)


class EnhancedImageSearch(atom.AtomBase):
  _tag = 'enhanced-image-search'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def EnhancedImageSearchFromString(xml_string):
  return atom.CreateClassFromXMLString(EnhancedImageSearch, xml_string)


class Verified(atom.AtomBase):
  _tag = 'verified'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def VerifiedFromString(xml_string):
  return atom.CreateClassFromXMLString(Verified, xml_string)


class VerificationMethodMeta(atom.AtomBase):
  _tag = 'meta'
  _namespace = atom.ATOM_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['name'] = 'name'
  _attributes['content'] = 'content'

  def __init__(self, text=None, name=None, content=None,
      extension_elements=None, extension_attributes=None):
    self.text = text
    self.name = name
    self.content = content
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def VerificationMethodMetaFromString(xml_string):
  return atom.CreateClassFromXMLString(VerificationMethodMeta, xml_string)


class VerificationMethod(atom.AtomBase):
  _tag = 'verification-method'
  _namespace = GWEBMASTERTOOLS_NAMESPACE
  _children = atom.Text._children.copy()
  _attributes = atom.Text._attributes.copy()
  _children['{%s}meta' % atom.ATOM_NAMESPACE] = (
    'meta', VerificationMethodMeta)
  _attributes['in-use'] = 'in_use'
  _attributes['type'] = 'type'

  def __init__(self, text=None, in_use=None, meta=None, type=None,
      extension_elements=None, extension_attributes=None):
    self.text = text
    self.in_use = in_use
    self.meta = meta
    self.type = type
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def VerificationMethodFromString(xml_string):
  return atom.CreateClassFromXMLString(VerificationMethod, xml_string)


class MarkupLanguage(atom.AtomBase):
  _tag = 'markup-language'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def MarkupLanguageFromString(xml_string):
  return atom.CreateClassFromXMLString(MarkupLanguage, xml_string)


class SitemapMobile(atom.AtomBase):
  _tag = 'sitemap-mobile'
  _namespace = GWEBMASTERTOOLS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _children['{%s}markup-language' % GWEBMASTERTOOLS_NAMESPACE] = (
      'markup_language', [MarkupLanguage])

  def __init__(self, markup_language=None,
      extension_elements=None, extension_attributes=None, text=None):

    self.markup_language = markup_language or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def SitemapMobileFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapMobile, xml_string)


class SitemapMobileMarkupLanguage(atom.AtomBase):
  _tag = 'sitemap-mobile-markup-language'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def SitemapMobileMarkupLanguageFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapMobileMarkupLanguage, xml_string)


class PublicationLabel(atom.AtomBase):
  _tag = 'publication-label'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def PublicationLabelFromString(xml_string):
  return atom.CreateClassFromXMLString(PublicationLabel, xml_string)


class SitemapNews(atom.AtomBase):
  _tag = 'sitemap-news'
  _namespace = GWEBMASTERTOOLS_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _attributes = atom.AtomBase._attributes.copy()
  _children['{%s}publication-label' % GWEBMASTERTOOLS_NAMESPACE] = (
      'publication_label', [PublicationLabel])

  def __init__(self, publication_label=None,
    extension_elements=None, extension_attributes=None, text=None):

    self.publication_label = publication_label or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def SitemapNewsFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapNews, xml_string)


class SitemapNewsPublicationLabel(atom.AtomBase):
  _tag = 'sitemap-news-publication-label'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def SitemapNewsPublicationLabelFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapNewsPublicationLabel, xml_string)


class SitemapLastDownloaded(atom.Date):
  _tag = 'sitemap-last-downloaded'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def SitemapLastDownloadedFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapLastDownloaded, xml_string)


class SitemapType(atom.AtomBase):
  _tag = 'sitemap-type'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def SitemapTypeFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapType, xml_string)


class SitemapStatus(atom.AtomBase):
  _tag = 'sitemap-status'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def SitemapStatusFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapStatus, xml_string)


class SitemapUrlCount(atom.AtomBase):
  _tag = 'sitemap-url-count'
  _namespace = GWEBMASTERTOOLS_NAMESPACE


def SitemapUrlCountFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapUrlCount, xml_string)


class LinkFinder(atom.LinkFinder):
  """An "interface" providing methods to find link elements

  SitesEntry elements often contain multiple links which differ in the rel 
  attribute or content type. Often, developers are interested in a specific
  type of link so this class provides methods to find specific classes of links.

  This class is used as a mixin in SitesEntry.
  """

  def GetSelfLink(self):
    """Find the first link with rel set to 'self'

    Returns:
      An atom.Link or none if none of the links had rel equal to 'self'
    """

    for a_link in self.link:
      if a_link.rel == 'self':
        return a_link
    return None

  def GetEditLink(self):
    for a_link in self.link:
      if a_link.rel == 'edit':
        return a_link
    return None

  def GetPostLink(self):
    """Get a link containing the POST target URL.
    
    The POST target URL is used to insert new entries.

    Returns:
      A link object with a rel matching the POST type.
    """
    for a_link in self.link:
      if a_link.rel == 'http://schemas.google.com/g/2005#post':
        return a_link
    return None

  def GetFeedLink(self):
    for a_link in self.link:
      if a_link.rel == 'http://schemas.google.com/g/2005#feed':
        return a_link
    return None


class SitesEntry(atom.Entry, LinkFinder):
  """A Google Webmaster Tools meta Entry flavor of an Atom Entry """

  _tag = atom.Entry._tag
  _namespace = atom.Entry._namespace
  _children = atom.Entry._children.copy()
  _attributes = atom.Entry._attributes.copy()
  _children['{%s}entryLink' % gdata.GDATA_NAMESPACE] = (
      'entry_link', [gdata.EntryLink])
  _children['{%s}indexed' % GWEBMASTERTOOLS_NAMESPACE] = ('indexed', Indexed)
  _children['{%s}crawled' % GWEBMASTERTOOLS_NAMESPACE] = (
      'crawled', Crawled)
  _children['{%s}geolocation' % GWEBMASTERTOOLS_NAMESPACE] = (
      'geolocation', GeoLocation)
  _children['{%s}preferred-domain' % GWEBMASTERTOOLS_NAMESPACE] = (
      'preferred_domain', PreferredDomain)
  _children['{%s}crawl-rate' % GWEBMASTERTOOLS_NAMESPACE] = (
      'crawl_rate', CrawlRate)
  _children['{%s}enhanced-image-search' % GWEBMASTERTOOLS_NAMESPACE] = (
      'enhanced_image_search', EnhancedImageSearch)
  _children['{%s}verified' % GWEBMASTERTOOLS_NAMESPACE] = (
      'verified', Verified)
  _children['{%s}verification-method' % GWEBMASTERTOOLS_NAMESPACE] = (
      'verification_method', [VerificationMethod])
  
  def __GetId(self):
    return self.__id

  # This method was created to strip the unwanted whitespace from the id's 
  # text node.
  def __SetId(self, id):
    self.__id = id
    if id is not None and id.text is not None:
      self.__id.text = id.text.strip()

  id = property(__GetId, __SetId)

  def __init__(self, category=None, content=None,
      atom_id=None, link=None, title=None, updated=None,
      entry_link=None, indexed=None, crawled=None,
      geolocation=None, preferred_domain=None, crawl_rate=None,
      enhanced_image_search=None,
      verified=None, verification_method=None,
      extension_elements=None, extension_attributes=None, text=None):
    atom.Entry.__init__(self, category=category, 
                        content=content, atom_id=atom_id, link=link, 
                        title=title, updated=updated, text=text)

    self.entry_link = entry_link or []
    self.indexed = indexed
    self.crawled = crawled
    self.geolocation = geolocation
    self.preferred_domain = preferred_domain
    self.crawl_rate = crawl_rate
    self.enhanced_image_search = enhanced_image_search
    self.verified = verified
    self.verification_method = verification_method or []


def SitesEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(SitesEntry, xml_string)


class SitesFeed(atom.Feed, LinkFinder):
  """A Google Webmaster Tools meta Sites feed flavor of an Atom Feed"""

  _tag = atom.Feed._tag
  _namespace = atom.Feed._namespace
  _children = atom.Feed._children.copy()
  _attributes = atom.Feed._attributes.copy()
  _children['{%s}startIndex' % gdata.OPENSEARCH_NAMESPACE] = (
      'start_index', gdata.StartIndex)
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [SitesEntry])
  del _children['{%s}generator' % atom.ATOM_NAMESPACE]
  del _children['{%s}author' % atom.ATOM_NAMESPACE]
  del _children['{%s}contributor' % atom.ATOM_NAMESPACE]
  del _children['{%s}logo' % atom.ATOM_NAMESPACE]
  del _children['{%s}icon' % atom.ATOM_NAMESPACE]
  del _children['{%s}rights' % atom.ATOM_NAMESPACE]
  del _children['{%s}subtitle' % atom.ATOM_NAMESPACE]

  def __GetId(self):
    return self.__id

  def __SetId(self, id):
    self.__id = id
    if id is not None and id.text is not None:
      self.__id.text = id.text.strip()

  id = property(__GetId, __SetId)

  def __init__(self, start_index=None, atom_id=None, title=None, entry=None,
      category=None, link=None, updated=None,
      extension_elements=None, extension_attributes=None, text=None):
    """Constructor for Source
    
    Args:
      category: list (optional) A list of Category instances
      id: Id (optional) The entry's Id element
      link: list (optional) A list of Link instances
      title: Title (optional) the entry's title element
      updated: Updated (optional) the entry's updated element
      entry: list (optional) A list of the Entry instances contained in the 
          feed.
      text: String (optional) The text contents of the element. This is the 
          contents of the Entry's XML text node. 
          (Example: <foo>This is the text</foo>)
      extension_elements: list (optional) A list of ExtensionElement instances
          which are children of this element.
      extension_attributes: dict (optional) A dictionary of strings which are 
          the values for additional XML attributes of this element.
    """

    self.start_index = start_index
    self.category = category or []
    self.id = atom_id
    self.link = link or []
    self.title = title
    self.updated = updated
    self.entry = entry or []
    self.text = text
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def SitesFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SitesFeed, xml_string)


class SitemapsEntry(atom.Entry, LinkFinder):
  """A Google Webmaster Tools meta Sitemaps Entry flavor of an Atom Entry """

  _tag = atom.Entry._tag
  _namespace = atom.Entry._namespace
  _children = atom.Entry._children.copy()
  _attributes = atom.Entry._attributes.copy()
  _children['{%s}sitemap-type' % GWEBMASTERTOOLS_NAMESPACE] = (
      'sitemap_type', SitemapType)
  _children['{%s}sitemap-status' % GWEBMASTERTOOLS_NAMESPACE] = (
      'sitemap_status', SitemapStatus)
  _children['{%s}sitemap-last-downloaded' % GWEBMASTERTOOLS_NAMESPACE] = (
      'sitemap_last_downloaded', SitemapLastDownloaded)
  _children['{%s}sitemap-url-count' % GWEBMASTERTOOLS_NAMESPACE] = (
      'sitemap_url_count', SitemapUrlCount)
  _children['{%s}sitemap-mobile-markup-language' % GWEBMASTERTOOLS_NAMESPACE] \
      = ('sitemap_mobile_markup_language', SitemapMobileMarkupLanguage)
  _children['{%s}sitemap-news-publication-label' % GWEBMASTERTOOLS_NAMESPACE] \
      = ('sitemap_news_publication_label', SitemapNewsPublicationLabel)
  
  def __GetId(self):
    return self.__id

  # This method was created to strip the unwanted whitespace from the id's 
  # text node.
  def __SetId(self, id):
    self.__id = id
    if id is not None and id.text is not None:
      self.__id.text = id.text.strip()

  id = property(__GetId, __SetId)

  def __init__(self, category=None, content=None,
      atom_id=None, link=None, title=None, updated=None,
      sitemap_type=None, sitemap_status=None, sitemap_last_downloaded=None,
      sitemap_url_count=None, sitemap_mobile_markup_language=None,
      sitemap_news_publication_label=None,
      extension_elements=None, extension_attributes=None, text=None):
    atom.Entry.__init__(self, category=category, 
                        content=content, atom_id=atom_id, link=link, 
                        title=title, updated=updated, text=text)

    self.sitemap_type = sitemap_type
    self.sitemap_status = sitemap_status
    self.sitemap_last_downloaded = sitemap_last_downloaded
    self.sitemap_url_count = sitemap_url_count
    self.sitemap_mobile_markup_language = sitemap_mobile_markup_language
    self.sitemap_news_publication_label = sitemap_news_publication_label


def SitemapsEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapsEntry, xml_string)


class SitemapsFeed(atom.Feed, LinkFinder):
  """A Google Webmaster Tools meta Sitemaps feed flavor of an Atom Feed"""

  _tag = atom.Feed._tag
  _namespace = atom.Feed._namespace
  _children = atom.Feed._children.copy()
  _attributes = atom.Feed._attributes.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [SitemapsEntry])
  _children['{%s}sitemap-mobile' % GWEBMASTERTOOLS_NAMESPACE] = (
      'sitemap_mobile', SitemapMobile)
  _children['{%s}sitemap-news' % GWEBMASTERTOOLS_NAMESPACE] = (
      'sitemap_news', SitemapNews)
  del _children['{%s}generator' % atom.ATOM_NAMESPACE]
  del _children['{%s}author' % atom.ATOM_NAMESPACE]
  del _children['{%s}contributor' % atom.ATOM_NAMESPACE]
  del _children['{%s}logo' % atom.ATOM_NAMESPACE]
  del _children['{%s}icon' % atom.ATOM_NAMESPACE]
  del _children['{%s}rights' % atom.ATOM_NAMESPACE]
  del _children['{%s}subtitle' % atom.ATOM_NAMESPACE]

  def __GetId(self):
    return self.__id

  def __SetId(self, id):
    self.__id = id
    if id is not None and id.text is not None:
      self.__id.text = id.text.strip()

  id = property(__GetId, __SetId)

  def __init__(self, category=None, content=None,
      atom_id=None, link=None, title=None, updated=None,
      entry=None, sitemap_mobile=None, sitemap_news=None,
      extension_elements=None, extension_attributes=None, text=None):

    self.category = category or []
    self.id = atom_id
    self.link = link or []
    self.title = title
    self.updated = updated
    self.entry = entry or []
    self.text = text
    self.sitemap_mobile = sitemap_mobile
    self.sitemap_news = sitemap_news
    self.extension_elements = extension_elements or []
    self.extension_attributes = extension_attributes or {}


def SitemapsFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(SitemapsFeed, xml_string)
