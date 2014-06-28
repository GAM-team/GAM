#!/usr/bin/python

"""
    Extend gdata.service.GDataService to support authenticated CRUD ops on 
    Books API

    http://code.google.com/apis/books/docs/getting-started.html
    http://code.google.com/apis/books/docs/gdata/developers_guide_protocol.html

    TODO: (here and __init__)
        * search based on label, review, or other annotations (possible?)
        * edit (specifically, Put requests) seem to fail effect a change

    Problems With API:
        * Adding a book with a review to the library adds a note, not a review.
          This does not get included in the returned item. You see this by
          looking at My Library through the website.
        * Editing a review never edits a review (unless it is freshly added, but 
          see above). More generally,
        * a Put request with changed annotations (label/rating/review) does NOT
          change the data. Note: Put requests only work on the href from 
          GetEditLink (as per the spec). Do not try to PUT to the annotate or 
          library feeds, this will cause a 400 Invalid URI Bad Request response.
          Attempting to Post to one of the feeds with the updated annotations
          does not update them. See the following for (hopefully) a follow up:
          google.com/support/forum/p/booksearch-apis/thread?tid=27fd7f68de438fc8
        * Attempts to workaround the edit problem continue to fail. For example,
          removing the item, editing the data, readding the item, gives us only
          our originally added data (annotations). This occurs even if we
          completely shut python down, refetch the book from the public feed,
          and re-add it. There is some kind of persistence going on that I
          cannot change. This is likely due to the annotations being cached in
          the annotation feed and the inability to edit (see Put, above)
        * GetAnnotationLink has www.books.... as the server, but hitting www...
          results in a bad URI error.
        * Spec indicates there may be multiple labels, but there does not seem
          to be a way to get the server to accept multiple labels, nor does the
          web interface have an obvious way to have multiple labels. Multiple 
          labels are never returned.
"""

__author__ = "James Sams <sams.james@gmail.com>"
__copyright__ = "Apache License v2.0"

from shlex import split

import gdata.service
try:
    import books
except ImportError:
    import gdata.books as books


BOOK_SERVER       = "books.google.com"
GENERAL_FEED      = "/books/feeds/volumes"
ITEM_FEED         = "/books/feeds/volumes/"
LIBRARY_FEED      = "/books/feeds/users/%s/collections/library/volumes"
ANNOTATION_FEED   = "/books/feeds/users/%s/volumes"
PARTNER_FEED      = "/books/feeds/p/%s/volumes"
BOOK_SERVICE      = "print"
ACCOUNT_TYPE      = "HOSTED_OR_GOOGLE"


class BookService(gdata.service.GDataService):

    def __init__(self, email=None, password=None, source=None,
                server=BOOK_SERVER, account_type=ACCOUNT_TYPE,
                exception_handlers=tuple(), **kwargs):
        """source should be of form 'ProgramCompany - ProgramName - Version'"""

        gdata.service.GDataService.__init__(self, email=email, 
                    password=password, service=BOOK_SERVICE, source=source,
                    server=server, **kwargs) 
        self.exception_handlers = exception_handlers

    def search(self, q, start_index="1", max_results="10", 
                min_viewability="none", feed=GENERAL_FEED,
                converter=books.BookFeed.FromString):
        """
        Query the Public search feed. q is either a search string or a
        gdata.service.Query instance with a query set.
        
        min_viewability must be "none", "partial", or "full".
        
        If you change the feed to a single item feed, note that you will 
        probably need to change the converter to be Book.FromString
        """

        if not isinstance(q, gdata.service.Query):
            q = gdata.service.Query(text_query=q)
        if feed:
            q.feed = feed
        q['start-index'] = start_index
        q['max-results'] = max_results
        q['min-viewability'] = min_viewability
        return self.Get(uri=q.ToUri(),converter=converter)
    
    def search_by_keyword(self, q='', feed=GENERAL_FEED, start_index="1",
                max_results="10", min_viewability="none", **kwargs):
        """
            Query the Public Search Feed by keyword. Non-keyword strings can be
            set in q. This is quite fragile. Is there a function somewhere in
            the Google library that will parse a query the same way that Google
            does?

            Legal Identifiers are listed below and correspond to their meaning
            at http://books.google.com/advanced_book_search:
                all_words 
                exact_phrase 
                at_least_one 
                without_words 
                title
                author
                publisher
                subject
                isbn
                lccn
                oclc
                seemingly unsupported:
                publication_date: a sequence of two, two tuples:
                    ((min_month,min_year),(max_month,max_year))
                    where month is one/two digit month, year is 4 digit, eg:
                    (('1','2000'),('10','2003')). Lower bound is inclusive,
                    upper bound is exclusive
        """

        for k, v in kwargs.items():
            if not v:
                continue
            k = k.lower()
            if k == 'all_words':
                q = "%s %s" % (q, v)
            elif k == 'exact_phrase':
                q = '%s "%s"' % (q, v.strip('"'))
            elif k == 'at_least_one':
                q = '%s %s' % (q, ' '.join(['OR "%s"' % x for x in split(v)]))
            elif k == 'without_words':
                q = '%s %s' % (q, ' '.join(['-"%s"' % x for x in split(v)]))
            elif k in ('author','title', 'publisher'):
                q = '%s %s' % (q, ' '.join(['in%s:"%s"'%(k,x) for x in split(v)]))
            elif k == 'subject':
                q = '%s %s' % (q, ' '.join(['%s:"%s"' % (k,x) for x in split(v)]))
            elif k == 'isbn':
                q = '%s ISBN%s' % (q, v)
            elif k == 'issn':
                q = '%s ISSN%s' % (q,v)
            elif k == 'oclc':
                q = '%s OCLC%s' % (q,v)
            else:
                raise ValueError("Unsupported search keyword")
        return self.search(q.strip(),start_index=start_index, feed=feed, 
                            max_results=max_results, 
                            min_viewability=min_viewability)
    
    def search_library(self, q, id='me', **kwargs):
        """Like search, but in a library feed. Default is the authenticated
        user's feed. Change by setting id."""

        if 'feed' in kwargs:
            raise ValueError("kwarg 'feed' conflicts with library_id")
        feed = LIBRARY_FEED % id
        return self.search(q, feed=feed, **kwargs)
   
    def search_library_by_keyword(self, id='me', **kwargs):
        """Hybrid of search_by_keyword and search_library
        """

        if 'feed' in kwargs:
            raise ValueError("kwarg 'feed' conflicts with library_id")
        feed = LIBRARY_FEED % id
        return self.search_by_keyword(feed=feed,**kwargs)
    
    def search_annotations(self, q, id='me', **kwargs): 
        """Like search, but in an annotation feed. Default is the authenticated
        user's feed. Change by setting id."""

        if 'feed' in kwargs:
            raise ValueError("kwarg 'feed' conflicts with library_id")
        feed = ANNOTATION_FEED % id
        return self.search(q, feed=feed, **kwargs)
    
    def search_annotations_by_keyword(self, id='me', **kwargs):
        """Hybrid of search_by_keyword and search_annotations
        """

        if 'feed' in kwargs:
            raise ValueError("kwarg 'feed' conflicts with library_id")
        feed = ANNOTATION_FEED % id
        return self.search_by_keyword(feed=feed,**kwargs)
    
    def add_item_to_library(self, item):
        """Add the item, either an XML string or books.Book instance, to the 
        user's library feed"""

        feed = LIBRARY_FEED % 'me'
        return self.Post(data=item, uri=feed, converter=books.Book.FromString)
    
    def remove_item_from_library(self, item):
        """
        Remove the item, a books.Book instance, from the authenticated user's 
        library feed. Using an item retrieved from a public search will fail.
        """

        return self.Delete(item.GetEditLink().href)
    
    def add_annotation(self, item):
        """
        Add the item, either an XML string or books.Book instance, to the 
        user's annotation feed.
        """
        # do not use GetAnnotationLink, results in 400 Bad URI due to www
        return self.Post(data=item, uri=ANNOTATION_FEED % 'me', 
                        converter=books.Book.FromString)
    
    def edit_annotation(self, item):
        """
        Send an edited item, a books.Book instance, to the user's annotation 
        feed. Note that whereas extra annotations in add_annotations, minus 
        ratings which are immutable once set, are simply added to the item in 
        the annotation feed, if an annotation has been removed from the item, 
        sending an edit request will remove that annotation. This should not 
        happen with add_annotation.
        """

        return self.Put(data=item, uri=item.GetEditLink().href,
                    converter=books.Book.FromString) 
    
    def get_by_google_id(self, id):
        return self.Get(ITEM_FEED + id, converter=books.Book.FromString)
    
    def get_library(self, id='me',feed=LIBRARY_FEED, start_index="1", 
                max_results="100", min_viewability="none",
                converter=books.BookFeed.FromString):
        """
        Return a generator object that will return gbook.Book instances until
        the search feed no longer returns an item from the GetNextLink method.
        Thus max_results is not the maximum number of items that will be
        returned, but rather the number of items per page of searches. This has
        been set high to reduce the required number of network requests.
        """

        q = gdata.service.Query()
        q.feed = feed % id
        q['start-index'] = start_index
        q['max-results'] = max_results
        q['min-viewability'] = min_viewability
        x = self.Get(uri=q.ToUri(), converter=converter)
        while 1:
            for entry in x.entry:
                yield entry
            else:
                l = x.GetNextLink()
                if l: # hope the server preserves our preferences
                    x = self.Get(uri=l.href, converter=converter)
                else:
                    break

    def get_annotations(self, id='me', start_index="1", max_results="100",
                min_viewability="none", converter=books.BookFeed.FromString):
        """
        Like get_library, but for the annotation feed
        """

        return self.get_library(id=id, feed=ANNOTATION_FEED,
                    max_results=max_results, min_viewability = min_viewability,
                    converter=converter)
