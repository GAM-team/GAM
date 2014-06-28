#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
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


"""Contains the data classes of the Google Webmaster Tools Data API"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import atom.data
import gdata.data
import gdata.opensearch.data


WT_TEMPLATE = '{http://schemas.google.com/webmaster/tools/2007/}%s'


class CrawlIssueCrawlType(atom.core.XmlElement):
  """Type of crawl of the crawl issue"""
  _qname = WT_TEMPLATE % 'crawl-type'


class CrawlIssueDateDetected(atom.core.XmlElement):
  """Detection date for the issue"""
  _qname = WT_TEMPLATE % 'date-detected'


class CrawlIssueDetail(atom.core.XmlElement):
  """Detail of the crawl issue"""
  _qname = WT_TEMPLATE % 'detail'


class CrawlIssueIssueType(atom.core.XmlElement):
  """Type of crawl issue"""
  _qname = WT_TEMPLATE % 'issue-type'


class CrawlIssueLinkedFromUrl(atom.core.XmlElement):
  """Source URL that links to the issue URL"""
  _qname = WT_TEMPLATE % 'linked-from'


class CrawlIssueUrl(atom.core.XmlElement):
  """URL affected by the crawl issue"""
  _qname = WT_TEMPLATE % 'url'


class CrawlIssueEntry(gdata.data.GDEntry):
  """Describes a crawl issue entry"""
  date_detected = CrawlIssueDateDetected
  url = CrawlIssueUrl
  detail = CrawlIssueDetail
  issue_type = CrawlIssueIssueType
  crawl_type = CrawlIssueCrawlType
  linked_from = [CrawlIssueLinkedFromUrl]


class CrawlIssuesFeed(gdata.data.GDFeed):
  """Feed of crawl issues for a particular site"""
  entry = [CrawlIssueEntry]


class Indexed(atom.core.XmlElement):
  """Describes the indexing status of a site"""
  _qname = WT_TEMPLATE % 'indexed'


class Keyword(atom.core.XmlElement):
  """A keyword in a site or in a link to a site"""
  _qname = WT_TEMPLATE % 'keyword'
  source = 'source'


class KeywordEntry(gdata.data.GDEntry):
  """Describes a keyword entry"""


class KeywordsFeed(gdata.data.GDFeed):
  """Feed of keywords for a particular site"""
  entry = [KeywordEntry]
  keyword = [Keyword]


class LastCrawled(atom.core.XmlElement):
  """Describes the last crawled date of a site"""
  _qname = WT_TEMPLATE % 'last-crawled'


class MessageBody(atom.core.XmlElement):
  """Message body"""
  _qname = WT_TEMPLATE % 'body'


class MessageDate(atom.core.XmlElement):
  """Message date"""
  _qname = WT_TEMPLATE % 'date'


class MessageLanguage(atom.core.XmlElement):
  """Message language"""
  _qname = WT_TEMPLATE % 'language'


class MessageRead(atom.core.XmlElement):
  """Indicates if the message has already been read"""
  _qname = WT_TEMPLATE % 'read'


class MessageSubject(atom.core.XmlElement):
  """Message subject"""
  _qname = WT_TEMPLATE % 'subject'


class SiteId(atom.core.XmlElement):
  """Site URL"""
  _qname = WT_TEMPLATE % 'id'


class MessageEntry(gdata.data.GDEntry):
  """Describes a message entry"""
  wt_id = SiteId
  subject = MessageSubject
  date = MessageDate
  body = MessageBody
  language = MessageLanguage
  read = MessageRead


class MessagesFeed(gdata.data.GDFeed):
  """Describes a messages feed"""
  entry = [MessageEntry]


class SitemapEntry(gdata.data.GDEntry):
  """Describes a sitemap entry"""
  indexed = Indexed
  wt_id = SiteId


class SitemapMobileMarkupLanguage(atom.core.XmlElement):
  """Describes a markup language for URLs in this sitemap"""
  _qname = WT_TEMPLATE % 'sitemap-mobile-markup-language'


class SitemapMobile(atom.core.XmlElement):
  """Lists acceptable mobile markup languages for URLs in this sitemap"""
  _qname = WT_TEMPLATE % 'sitemap-mobile'
  sitemap_mobile_markup_language = [SitemapMobileMarkupLanguage]


class SitemapNewsPublicationLabel(atom.core.XmlElement):
  """Specifies the publication label for this sitemap"""
  _qname = WT_TEMPLATE % 'sitemap-news-publication-label'


class SitemapNews(atom.core.XmlElement):
  """Lists publication labels for this sitemap"""
  _qname = WT_TEMPLATE % 'sitemap-news'
  sitemap_news_publication_label = [SitemapNewsPublicationLabel]


class SitemapType(atom.core.XmlElement):
  """Indicates the type of sitemap. Not used for News or Mobile Sitemaps"""
  _qname = WT_TEMPLATE % 'sitemap-type'


class SitemapUrlCount(atom.core.XmlElement):
  """Indicates the number of URLs contained in the sitemap"""
  _qname = WT_TEMPLATE % 'sitemap-url-count'


class SitemapsFeed(gdata.data.GDFeed):
  """Describes a sitemaps feed"""
  entry = [SitemapEntry]


class VerificationMethod(atom.core.XmlElement):
  """Describes a verification method that may be used for a site"""
  _qname = WT_TEMPLATE % 'verification-method'
  in_use = 'in-use'
  type = 'type'


class Verified(atom.core.XmlElement):
  """Describes the verification status of a site"""
  _qname = WT_TEMPLATE % 'verified'


class SiteEntry(gdata.data.GDEntry):
  """Describes a site entry"""
  indexed = Indexed
  wt_id = SiteId
  verified = Verified
  last_crawled = LastCrawled
  verification_method = [VerificationMethod]


class SitesFeed(gdata.data.GDFeed):
  """Describes a sites feed"""
  entry = [SiteEntry]


