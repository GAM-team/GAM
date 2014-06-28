#!/usr/bin/python

"""
    Data Models for books.service

    All classes can be instantiated from an xml string using their FromString
    class method.

    Notes:
        * Book.title displays the first dc:title because the returned XML
          repeats that datum as atom:title.
    There is an undocumented gbs:openAccess element that is not parsed.
"""

__author__ = "James Sams <sams.james@gmail.com>"
__copyright__ = "Apache License v2.0"

import atom
import gdata


BOOK_SEARCH_NAMESPACE   = 'http://schemas.google.com/books/2008'
DC_NAMESPACE            = 'http://purl.org/dc/terms' 
ANNOTATION_REL          = "http://schemas.google.com/books/2008/annotation"
INFO_REL                = "http://schemas.google.com/books/2008/info"
LABEL_SCHEME            = "http://schemas.google.com/books/2008/labels"
PREVIEW_REL             = "http://schemas.google.com/books/2008/preview"
THUMBNAIL_REL           = "http://schemas.google.com/books/2008/thumbnail"
FULL_VIEW               = "http://schemas.google.com/books/2008#view_all_pages"
PARTIAL_VIEW            = "http://schemas.google.com/books/2008#view_partial"
NO_VIEW                 = "http://schemas.google.com/books/2008#view_no_pages"
UNKNOWN_VIEW            = "http://schemas.google.com/books/2008#view_unknown"
EMBEDDABLE              = "http://schemas.google.com/books/2008#embeddable"
NOT_EMBEDDABLE          = "http://schemas.google.com/books/2008#not_embeddable"



class _AtomFromString(atom.AtomBase):

    #@classmethod
    def FromString(cls, s):
        return atom.CreateClassFromXMLString(cls, s)

    FromString = classmethod(FromString)


class Creator(_AtomFromString):
    """
    The <dc:creator> element identifies an author-or more generally, an entity
    responsible for creating the volume in question. Examples of a creator
    include a person, an organization, or a service. In the case of 
    anthologies, proceedings, or other edited works, this field may be used to 
    indicate editors or other entities responsible for collecting the volume's 
    contents.
    
    This element appears as a child of <entry>. If there are multiple authors or
    contributors to the book, there may be multiple <dc:creator> elements in the
    volume entry (one for each creator or contributor).
    """

    _tag = 'creator'
    _namespace = DC_NAMESPACE


class Date(_AtomFromString): #iso 8601 / W3CDTF profile
    """
    The <dc:date> element indicates the publication date of the specific volume
    in question. If the book is a reprint, this is the reprint date, not the 
    original publication date. The date is encoded according to the ISO-8601 
    standard (and more specifically, the W3CDTF profile).

    The <dc:date> element can appear only as a child of <entry>.
    
    Usually only the year or the year and the month are given.

    YYYY-MM-DDThh:mm:ssTZD  TZD = -hh:mm or +hh:mm
    """
    
    _tag = 'date'     
    _namespace = DC_NAMESPACE
   

class Description(_AtomFromString):
    """
    The <dc:description> element includes text that describes a book or book 
    result. In a search result feed, this may be a search result "snippet" that
    contains the words around the user's search term. For a single volume feed,
    this element may contain a synopsis of the book.

    The <dc:description> element can appear only as a child of <entry>
    """

    _tag = 'description'
    _namespace = DC_NAMESPACE


class Format(_AtomFromString):
    """
    The <dc:format> element describes the physical properties of the volume. 
    Currently, it indicates the number of pages in the book, but more 
    information may be added to this field in the future.

    This element can appear only as a child of <entry>.
    """

    _tag = 'format'
    _namespace = DC_NAMESPACE


class Identifier(_AtomFromString):
    """
    The <dc:identifier> element provides an unambiguous reference to a 
    particular book.
    * Every <entry> contains at least one <dc:identifier> child.
    * The first identifier is always the unique string Book Search has assigned
      to the volume (such as s1gVAAAAYAAJ). This is the ID that appears in the 
      book's URL in the Book Search GUI, as well as in the URL of that book's 
      single item feed.
    * Many books contain additional <dc:identifier> elements. These provide 
      alternate, external identifiers to the volume. Such identifiers may 
      include the ISBNs, ISSNs, Library of Congress Control Numbers (LCCNs), 
      and OCLC numbers; they are prepended with a corresponding namespace 
      prefix (such as "ISBN:").
    * Any <dc:identifier> can be passed to the Dynamic Links, used to 
      instantiate an Embedded Viewer, or even used to construct static links to
      Book Search.
    The <dc:identifier> element can appear only as a child of <entry>.
    """

    _tag = 'identifier'
    _namespace = DC_NAMESPACE


class Publisher(_AtomFromString):
    """
    The <dc:publisher> element contains the name of the entity responsible for 
    producing and distributing the volume (usually the specific edition of this
    book). Examples of a publisher include a person, an organization, or a 
    service.

    This element can appear only as a child of <entry>. If there is more than 
    one publisher, multiple <dc:publisher> elements may appear.
    """

    _tag = 'publisher'
    _namespace = DC_NAMESPACE


class Subject(_AtomFromString):
    """
    The <dc:subject> element identifies the topic of the book. Usually this is 
    a Library of Congress Subject Heading (LCSH) or  Book Industry Standards 
    and Communications Subject Heading (BISAC).

    The <dc:subject> element can appear only as a child of <entry>. There may 
    be multiple <dc:subject> elements per entry.
    """

    _tag = 'subject'
    _namespace = DC_NAMESPACE


class Title(_AtomFromString):
    """
    The <dc:title> element contains the title of a book as it was published. If
    a book has a subtitle, it appears as a second <dc:title> element in the book
    result's <entry>.
    """

    _tag = 'title'
    _namespace = DC_NAMESPACE


class Viewability(_AtomFromString):
    """
    Google Book Search respects the user's local copyright restrictions. As a 
    result, previews or full views of some books are not available in all 
    locations. The <gbs:viewability> element indicates whether a book is fully 
    viewable, can be previewed, or only has "about the book" information. These
    three "viewability modes" are the same ones returned by the Dynamic Links 
    API.

    The <gbs:viewability> element can appear only as a child of <entry>.

    The value attribute will take the form of the following URIs to represent
    the relevant viewing capability:

    Full View: http://schemas.google.com/books/2008#view_all_pages
    Limited Preview: http://schemas.google.com/books/2008#view_partial
    Snippet View/No Preview: http://schemas.google.com/books/2008#view_no_pages
    Unknown view: http://schemas.google.com/books/2008#view_unknown
    """

    _tag = 'viewability'
    _namespace = BOOK_SEARCH_NAMESPACE
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['value'] = 'value'

    def __init__(self, value=None, text=None, 
                extension_elements=None, extension_attributes=None):
        self.value = value
        _AtomFromString.__init__(self, extension_elements=extension_elements,
                    extension_attributes=extension_attributes, text=text)


class Embeddability(_AtomFromString):
    """
    Many of the books found on Google Book Search can be embedded on third-party
    sites using the Embedded Viewer. The <gbs:embeddability> element indicates 
    whether a particular book result is available for embedding. By definition,
    a book that cannot be previewed on Book Search cannot be embedded on third-
    party sites.

    The <gbs:embeddability> element can appear only as a child of <entry>.

    The value attribute will take on one of the following URIs:
    embeddable: http://schemas.google.com/books/2008#embeddable
    not embeddable: http://schemas.google.com/books/2008#not_embeddable
    """

    _tag = 'embeddability'
    _namespace = BOOK_SEARCH_NAMESPACE
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['value'] = 'value'

    def __init__(self, value=None, text=None, extension_elements=None, 
                extension_attributes=None):
        self.value = value
        _AtomFromString.__init__(self, extension_elements=extension_elements,
                    extension_attributes=extension_attributes, text=text)


class Review(_AtomFromString):
    """
    When present, the <gbs:review> element contains a user-generated review for
    a given book. This element currently appears only in the user library and 
    user annotation feeds, as a child of <entry>.

    type: text, html, xhtml
    xml:lang: id of the language, a guess, (always two letters?)
    """

    _tag = 'review'
    _namespace = BOOK_SEARCH_NAMESPACE
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['type'] = 'type'
    _attributes['{http://www.w3.org/XML/1998/namespace}lang'] = 'lang'
    
    def __init__(self, type=None, lang=None, text=None, 
                extension_elements=None, extension_attributes=None):
        self.type = type
        self.lang = lang
        _AtomFromString.__init__(self, extension_elements=extension_elements,
                    extension_attributes=extension_attributes, text=text)


class Rating(_AtomFromString):
    """All attributes must take an integral string between 1 and 5.
    The min, max, and average attributes represent 'community' ratings. The
    value attribute is the user's (of the feed from which the item is fetched,
    not necessarily the authenticated user) rating of the book.
    """

    _tag = 'rating'
    _namespace = gdata.GDATA_NAMESPACE
    _attributes = atom.AtomBase._attributes.copy()
    _attributes['min'] = 'min'
    _attributes['max'] = 'max'
    _attributes['average'] = 'average'
    _attributes['value'] = 'value'

    def __init__(self, min=None, max=None, average=None, value=None, text=None,
                extension_elements=None, extension_attributes=None):
        self.min = min 
        self.max = max 
        self.average = average
        self.value = value
        _AtomFromString.__init__(self, extension_elements=extension_elements,
                    extension_attributes=extension_attributes, text=text)


class Book(_AtomFromString, gdata.GDataEntry):
    """
    Represents an <entry> from either a search, annotation, library, or single
    item feed. Note that dc_title attribute is the proper title of the volume,
    title is an atom element and may not represent the full title.
    """

    _tag = 'entry'
    _namespace = atom.ATOM_NAMESPACE
    _children = gdata.GDataEntry._children.copy()
    for i in (Creator, Identifier, Publisher, Subject,):
        _children['{%s}%s' % (i._namespace, i._tag)] = (i._tag, [i])
    for i in (Date, Description, Format, Viewability, Embeddability, 
                Review, Rating):  # Review, Rating maybe only in anno/lib entrys
        _children['{%s}%s' % (i._namespace, i._tag)] = (i._tag, i)
    # there is an atom title as well, should we clobber that?
    del(i)
    _children['{%s}%s' % (Title._namespace, Title._tag)] = ('dc_title', [Title])

    def to_dict(self):
        """Returns a dictionary of the book's available metadata. If the data
        cannot be discovered, it is not included as a key in the returned dict.
        The possible keys are: authors, embeddability, date, description, 
        format, identifiers, publishers, rating, review, subjects, title, and
        viewability.

        Notes:
          * Plural keys will be lists
          * Singular keys will be strings
          * Title, despite usually being a list, joins the title and subtitle
            with a space as a single string.
          * embeddability and viewability only return the portion of the URI 
            after #
          * identifiers is a list of tuples, where the first item of each tuple
            is the type of identifier and the second item is the identifying
            string. Note that while doing dict() on this tuple may be possible,
            some items may have multiple of the same identifier and converting
            to a dict may resulted in collisions/dropped data.
          * Rating returns only the user's rating. See Rating class for precise
            definition.
        """
        d = {}
        if self.GetAnnotationLink():
            d['annotation'] = self.GetAnnotationLink().href
        if self.creator:
            d['authors'] = [x.text for x in self.creator]
        if self.embeddability:
            d['embeddability'] = self.embeddability.value.split('#')[-1]
        if self.date:
            d['date'] = self.date.text
        if self.description:
            d['description'] = self.description.text
        if self.format:
            d['format'] = self.format.text
        if self.identifier:
            d['identifiers'] = [('google_id', self.identifier[0].text)]
            for x in self.identifier[1:]:
                l = x.text.split(':') # should we lower the case of the ids?
                d['identifiers'].append((l[0], ':'.join(l[1:])))
        if self.GetInfoLink():
            d['info'] = self.GetInfoLink().href
        if self.GetPreviewLink():
            d['preview'] = self.GetPreviewLink().href
        if self.publisher:
            d['publishers'] = [x.text for x in self.publisher]
        if self.rating:
            d['rating'] = self.rating.value
        if self.review:
            d['review'] = self.review.text
        if self.subject:
            d['subjects'] = [x.text for x in self.subject]
        if self.GetThumbnailLink():
            d['thumbnail'] = self.GetThumbnailLink().href
        if self.dc_title:
            d['title'] = ' '.join([x.text for x in self.dc_title])
        if self.viewability:
            d['viewability'] = self.viewability.value.split('#')[-1]
        return d

    def __init__(self, creator=None, date=None, 
                description=None, format=None, author=None, identifier=None, 
                publisher=None, subject=None, dc_title=None, viewability=None, 
                embeddability=None, review=None, rating=None, category=None, 
                content=None, contributor=None, atom_id=None, link=None,
                published=None, rights=None, source=None, summary=None, 
                title=None, control=None, updated=None, text=None, 
                extension_elements=None, extension_attributes=None):
        self.creator = creator
        self.date = date
        self.description = description
        self.format = format
        self.identifier = identifier
        self.publisher = publisher
        self.subject = subject
        self.dc_title = dc_title or []
        self.viewability = viewability
        self.embeddability = embeddability
        self.review = review
        self.rating = rating
        gdata.GDataEntry.__init__(self, author=author, category=category, 
                content=content, contributor=contributor, atom_id=atom_id,
                link=link, published=published, rights=rights, source=source,
                summary=summary, title=title, control=control, updated=updated, 
                text=text, extension_elements=extension_elements, 
                extension_attributes=extension_attributes)
    
    def GetThumbnailLink(self):
        """Returns the atom.Link object representing the thumbnail URI."""
        for i in self.link:
            if i.rel == THUMBNAIL_REL:
                return i
    
    def GetInfoLink(self):
        """
        Returns the atom.Link object representing the human-readable info URI.
        """
        for i in self.link:
            if i.rel == INFO_REL:
                return i
    
    def GetPreviewLink(self):
        """Returns the atom.Link object representing the preview URI."""
        for i in self.link:
            if i.rel == PREVIEW_REL:
                return i
    
    def GetAnnotationLink(self):
        """
        Returns the atom.Link object representing the Annotation URI.
        Note that the use of www.books in the href of this link seems to make
        this information useless. Using books.service.ANNOTATION_FEED and 
        BOOK_SERVER to construct your URI seems to work better.
        """
        for i in self.link:
            if i.rel == ANNOTATION_REL:
                return i
    
    def set_rating(self, value):
        """Set user's rating. Must be an integral string between 1 nad 5"""
        assert (value in ('1','2','3','4','5'))
        if not isinstance(self.rating, Rating):
            self.rating = Rating()
        self.rating.value = value
    
    def set_review(self, text, type='text', lang='en'):
        """Set user's review text"""
        self.review = Review(text=text, type=type, lang=lang)
    
    def get_label(self):
        """Get users label for the item as a string"""
        for i in self.category:
            if i.scheme == LABEL_SCHEME:
                return i.term
    
    def set_label(self, term):
        """Clear pre-existing label for the item and set term as the label."""
        self.remove_label()
        self.category.append(atom.Category(term=term, scheme=LABEL_SCHEME))
    
    def remove_label(self):
        """Clear the user's label for the item"""
        ln = len(self.category)
        for i, j in enumerate(self.category[::-1]):
            if j.scheme == LABEL_SCHEME:
                del(self.category[ln-1-i])

    def clean_annotations(self):
        """Clear all annotations from an item. Useful for taking an item from
        another user's library/annotation feed and adding it to the 
        authenticated user's library without adopting annotations."""
        self.remove_label()
        self.review = None
        self.rating = None

    
    def get_google_id(self):
        """Get Google's ID of the item."""
        return self.id.text.split('/')[-1]


class BookFeed(_AtomFromString, gdata.GDataFeed):
    """Represents a feed of entries from a search."""

    _tag = 'feed'
    _namespace = atom.ATOM_NAMESPACE
    _children = gdata.GDataFeed._children.copy()
    _children['{%s}%s' % (Book._namespace, Book._tag)] = (Book._tag, [Book])


if __name__ == '__main__':
    import doctest
    doctest.testfile('datamodels.txt')
