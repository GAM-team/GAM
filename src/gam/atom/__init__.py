#
# Copyright (C) 2006 Google Inc.
#
# Licensed under the Apache License 2.0;



"""Contains classes representing Atom elements.

  Module objective: provide data classes for Atom constructs. These classes hide
  the XML-ness of Atom and provide a set of native Python classes to interact
  with.

  Conversions to and from XML should only be necessary when the Atom classes
  "touch the wire" and are sent over HTTP. For this reason this module
  provides  methods and functions to convert Atom classes to and from strings.

  For more information on the Atom data model, see RFC 4287
  (http://www.ietf.org/rfc/rfc4287.txt)

  AtomBase: A foundation class on which Atom classes are built. It
      handles the parsing of attributes and children which are common to all
      Atom classes. By default, the AtomBase class translates all XML child
      nodes into ExtensionElements.

  ExtensionElement: Atom allows Atom objects to contain XML which is not part
      of the Atom specification, these are called extension elements. If a
      classes parser encounters an unexpected XML construct, it is translated
      into an ExtensionElement instance. ExtensionElement is designed to fully
      capture the information in the XML. Child nodes in an XML extension are
      turned into ExtensionElements as well.
"""
from functools import wraps

# __author__ = 'api.jscudder (Jeffrey Scudder)'

import lxml.etree as ElementTree
import warnings

# XML namespaces which are often used in Atom entities.
ATOM_NAMESPACE = 'http://www.w3.org/2005/Atom'
ELEMENT_TEMPLATE = '{http://www.w3.org/2005/Atom}%s'
APP_NAMESPACE = 'http://purl.org/atom/app#'
APP_TEMPLATE = '{http://purl.org/atom/app#}%s'

# This encoding is used for converting strings before translating the XML
# into an object.
XML_STRING_ENCODING = 'utf-8'
# The desired string encoding for object members. set or monkey-patch to
# unicode if you want object members to be Python unicode strings, instead of
# encoded strings
MEMBER_STRING_ENCODING = str
#MEMBER_STRING_ENCODING = 'utf-8'
# MEMBER_STRING_ENCODING = unicode

# If True, all methods which are exclusive to v1 will raise a
# DeprecationWarning
ENABLE_V1_WARNINGS = False


def v1_deprecated(warning=None):
    """Shows a warning if ENABLE_V1_WARNINGS is True.

    Function decorator used to mark methods used in v1 classes which
    may be removed in future versions of the library.
    """
    warning = warning or ''

    # This closure is what is returned from the deprecated function.
    def mark_deprecated(f):
        # The deprecated_function wraps the actual call to f.
        @wraps(f)
        def optional_warn_function(*args, **kwargs):
            if ENABLE_V1_WARNINGS:
                warnings.warn(warning, DeprecationWarning, stacklevel=2)
            return f(*args, **kwargs)

        return optional_warn_function

    return mark_deprecated


def CreateClassFromXMLString(target_class, xml_string, string_encoding=None):
    """Creates an instance of the target class from the string contents.

    Args:
      target_class: class The class which will be instantiated and populated
          with the contents of the XML. This class must have a _tag and a
          _namespace class variable.
      xml_string: str A string which contains valid XML. The root element
          of the XML string should match the tag and namespace of the desired
          class.
      string_encoding: str The character encoding which the xml_string should
          be converted to before it is interpreted and translated into
          objects. The default is None in which case the string encoding
          is not changed.

    Returns:
      An instance of the target class with members assigned according to the
      contents of the XML - or None if the root XML tag and namespace did not
      match those of the target class.
    """
    encoding = string_encoding or XML_STRING_ENCODING
    if encoding and isinstance(xml_string, str):
        xml_string = xml_string.encode(encoding)
    tree = ElementTree.fromstring(xml_string)
    return _CreateClassFromElementTree(target_class, tree)


CreateClassFromXMLString = v1_deprecated(
    'Please use atom.core.parse with atom.data classes instead.')(
    CreateClassFromXMLString)


def _CreateClassFromElementTree(target_class, tree, namespace=None, tag=None):
    """Instantiates the class and populates members according to the tree.

    Note: Only use this function with classes that have _namespace and _tag
    class members.

    Args:
      target_class: class The class which will be instantiated and populated
          with the contents of the XML.
      tree: ElementTree An element tree whose contents will be converted into
          members of the new target_class instance.
      namespace: str (optional) The namespace which the XML tree's root node must
          match. If omitted, the namespace defaults to the _namespace of the
          target class.
      tag: str (optional) The tag which the XML tree's root node must match. If
          omitted, the tag defaults to the _tag class member of the target
          class.

      Returns:
        An instance of the target class - or None if the tag and namespace of
        the XML tree's root node did not match the desired namespace and tag.
    """
    if namespace is None:
        namespace = target_class._namespace
    if tag is None:
        tag = target_class._tag
    if tree.tag == '{%s}%s' % (namespace, tag):
        target = target_class()
        target._HarvestElementTree(tree)
        return target
    else:
        return None


class ExtensionContainer(object):
    def __init__(self, extension_elements=None, extension_attributes=None,
                 text=None):
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}
        self.text = text

    __init__ = v1_deprecated(
        'Please use data model classes in atom.data instead.')(
        __init__)

    # Three methods to create an object from an ElementTree
    def _HarvestElementTree(self, tree):
        # Fill in the instance members from the contents of the XML tree.
        for child in tree:
            self._ConvertElementTreeToMember(child)
        for attribute, value in tree.attrib.items():
            self._ConvertElementAttributeToMember(attribute, value)
        # Encode the text string according to the desired encoding type. (UTF-8)
        if tree.text:
            if MEMBER_STRING_ENCODING is str:
                self.text = tree.text
            else:
                self.text = tree.text.encode(MEMBER_STRING_ENCODING)

    def _ConvertElementTreeToMember(self, child_tree, current_class=None):
        self.extension_elements.append(_ExtensionElementFromElementTree(
            child_tree))

    def _ConvertElementAttributeToMember(self, attribute, value):
        # Encode the attribute value's string with the desired type Default UTF-8
        if value:
            if MEMBER_STRING_ENCODING is str:
                self.extension_attributes[attribute] = value
            else:
                self.extension_attributes[attribute] = value.encode(
                    MEMBER_STRING_ENCODING)

    # One method to create an ElementTree from an object
    def _AddMembersToElementTree(self, tree):
        for child in self.extension_elements:
            child._BecomeChildElement(tree)
        for attribute, value in self.extension_attributes.items():
            if value:
                if isinstance(value, str) or MEMBER_STRING_ENCODING is str:
                    tree.attrib[attribute] = value
                else:
                    # Decode the value from the desired encoding (default UTF-8).
                    tree.attrib[attribute] = value.decode(MEMBER_STRING_ENCODING)
        if self.text:
            if isinstance(self.text, str) or MEMBER_STRING_ENCODING is str:
                tree.text = self.text
            else:
                tree.text = self.text.decode(MEMBER_STRING_ENCODING)

    def FindExtensions(self, tag=None, namespace=None):
        """Searches extension elements for child nodes with the desired name.

        Returns a list of extension elements within this object whose tag
        and/or namespace match those passed in. To find all extensions in
        a particular namespace, specify the namespace but not the tag name.
        If you specify only the tag, the result list may contain extension
        elements in multiple namespaces.

        Args:
          tag: str (optional) The desired tag
          namespace: str (optional) The desired namespace

        Returns:
          A list of elements whose tag and/or namespace match the parameters
          values
        """

        results = []

        if tag and namespace:
            for element in self.extension_elements:
                if element.tag == tag and element.namespace == namespace:
                    results.append(element)
        elif tag and not namespace:
            for element in self.extension_elements:
                if element.tag == tag:
                    results.append(element)
        elif namespace and not tag:
            for element in self.extension_elements:
                if element.namespace == namespace:
                    results.append(element)
        else:
            for element in self.extension_elements:
                results.append(element)

        return results


class AtomBase(ExtensionContainer):
    _children = {}
    _attributes = {}

    def __init__(self, extension_elements=None, extension_attributes=None,
                 text=None):
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}
        self.text = text

    __init__ = v1_deprecated(
        'Please use data model classes in atom.data instead.')(
        __init__)

    def _ConvertElementTreeToMember(self, child_tree):
        # Find the element's tag in this class's list of child members
        if child_tree.tag in self.__class__._children:
            member_name = self.__class__._children[child_tree.tag][0]
            member_class = self.__class__._children[child_tree.tag][1]
            # If the class member is supposed to contain a list, make sure the
            # matching member is set to a list, then append the new member
            # instance to the list.
            if isinstance(member_class, list):
                if getattr(self, member_name) is None:
                    setattr(self, member_name, [])
                getattr(self, member_name).append(_CreateClassFromElementTree(
                    member_class[0], child_tree))
            else:
                setattr(self, member_name,
                        _CreateClassFromElementTree(member_class, child_tree))
        else:
            ExtensionContainer._ConvertElementTreeToMember(self, child_tree)

    def _ConvertElementAttributeToMember(self, attribute, value):
        # Find the attribute in this class's list of attributes.
        if attribute in self.__class__._attributes:
            # Find the member of this class which corresponds to the XML attribute
            # (lookup in current_class._attributes) and set this member to the
            # desired value (using self.__dict__).
            if value:
                # Encode the string to capture non-ascii characters (default UTF-8)
                if MEMBER_STRING_ENCODING is str:
                    setattr(self, self.__class__._attributes[attribute], value)
                else:
                    setattr(self, self.__class__._attributes[attribute],
                            value.encode(MEMBER_STRING_ENCODING))
        else:
            ExtensionContainer._ConvertElementAttributeToMember(
                self, attribute, value)

    # Three methods to create an ElementTree from an object
    def _AddMembersToElementTree(self, tree):
        # Convert the members of this class which are XML child nodes.
        # This uses the class's _children dictionary to find the members which
        # should become XML child nodes.
        member_node_names = [values[0] for tag, values in
                             self.__class__._children.items()]
        for member_name in member_node_names:
            member = getattr(self, member_name)
            if member is None:
                pass
            elif isinstance(member, list):
                for instance in member:
                    instance._BecomeChildElement(tree)
            else:
                member._BecomeChildElement(tree)
        # Convert the members of this class which are XML attributes.
        for xml_attribute, member_name in self.__class__._attributes.items():
            member = getattr(self, member_name)
            if member is not None:
                if isinstance(member, str) or MEMBER_STRING_ENCODING is str:
                    tree.attrib[xml_attribute] = member
                else:
                    tree.attrib[xml_attribute] = member.decode(MEMBER_STRING_ENCODING)
        # Lastly, call the ExtensionContainers's _AddMembersToElementTree to
        # convert any extension attributes.
        ExtensionContainer._AddMembersToElementTree(self, tree)

    def _BecomeChildElement(self, tree):
        """

        Note: Only for use with classes that have a _tag and _namespace class
        member. It is in AtomBase so that it can be inherited but it should
        not be called on instances of AtomBase.

        """
        new_child = ElementTree.Element('tag__')
        tree.append(new_child)
        new_child.tag = '{%s}%s' % (self.__class__._namespace,
                                    self.__class__._tag)
        self._AddMembersToElementTree(new_child)

    def _ToElementTree(self):
        """

        Note, this method is designed to be used only with classes that have a
        _tag and _namespace. It is placed in AtomBase for inheritance but should
        not be called on this class.

        """
        new_tree = ElementTree.Element('{%s}%s' % (self.__class__._namespace,
                                                   self.__class__._tag))
        self._AddMembersToElementTree(new_tree)
        return new_tree

    def ToString(self, string_encoding=str):
        """Converts the Atom object to a string containing XML."""
        return ElementTree.tostring(self._ToElementTree(), encoding=string_encoding)

    def __str__(self):
        return self.ToString()


class Name(AtomBase):
    """The atom:name element"""

    _tag = 'name'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Name

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def NameFromString(xml_string):
    return CreateClassFromXMLString(Name, xml_string)


class Email(AtomBase):
    """The atom:email element"""

    _tag = 'email'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Email

        Args:
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
          text: str The text data in the this element
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def EmailFromString(xml_string):
    return CreateClassFromXMLString(Email, xml_string)


class Uri(AtomBase):
    """The atom:uri element"""

    _tag = 'uri'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Uri

        Args:
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
          text: str The text data in the this element
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def UriFromString(xml_string):
    return CreateClassFromXMLString(Uri, xml_string)


class Person(AtomBase):
    """A foundation class from which atom:author and atom:contributor extend.

    A person contains information like name, email address, and web page URI for
    an author or contributor to an Atom feed.
    """

    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _children['{%s}name' % (ATOM_NAMESPACE)] = ('name', Name)
    _children['{%s}email' % (ATOM_NAMESPACE)] = ('email', Email)
    _children['{%s}uri' % (ATOM_NAMESPACE)] = ('uri', Uri)

    def __init__(self, name=None, email=None, uri=None,
                 extension_elements=None, extension_attributes=None, text=None):
        """Foundation from which author and contributor are derived.

        The constructor is provided for illustrative purposes, you should not
        need to instantiate a Person.

        Args:
          name: Name The person's name
          email: Email The person's email address
          uri: Uri The URI of the person's webpage
          extension_elements: list A list of ExtensionElement instances which are
              children of this element.
          extension_attributes: dict A dictionary of strings which are the values
              for additional XML attributes of this element.
          text: String The text contents of the element. This is the contents
              of the Entry's XML text node. (Example: <foo>This is the text</foo>)
        """

        self.name = name
        self.email = email
        self.uri = uri
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}
        self.text = text


class Author(Person):
    """The atom:author element

    An author is a required element in Feed.
    """

    _tag = 'author'
    _namespace = ATOM_NAMESPACE
    _children = Person._children.copy()
    _attributes = Person._attributes.copy()

    # _children = {}
    # _attributes = {}

    def __init__(self, name=None, email=None, uri=None,
                 extension_elements=None, extension_attributes=None, text=None):
        """Constructor for Author

        Args:
          name: Name
          email: Email
          uri: Uri
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
          text: str The text data in the this element
        """

        self.name = name
        self.email = email
        self.uri = uri
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}
        self.text = text


def AuthorFromString(xml_string):
    return CreateClassFromXMLString(Author, xml_string)


class Contributor(Person):
    """The atom:contributor element"""

    _tag = 'contributor'
    _namespace = ATOM_NAMESPACE
    _children = Person._children.copy()
    _attributes = Person._attributes.copy()

    def __init__(self, name=None, email=None, uri=None,
                 extension_elements=None, extension_attributes=None, text=None):
        """Constructor for Contributor

        Args:
          name: Name
          email: Email
          uri: Uri
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
          text: str The text data in the this element
        """

        self.name = name
        self.email = email
        self.uri = uri
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}
        self.text = text


def ContributorFromString(xml_string):
    return CreateClassFromXMLString(Contributor, xml_string)


class Link(AtomBase):
    """The atom:link element"""

    _tag = 'link'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _attributes['rel'] = 'rel'
    _attributes['href'] = 'href'
    _attributes['type'] = 'type'
    _attributes['title'] = 'title'
    _attributes['length'] = 'length'
    _attributes['hreflang'] = 'hreflang'

    def __init__(self, href=None, rel=None, link_type=None, hreflang=None,
                 title=None, length=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Link

        Args:
          href: string The href attribute of the link
          rel: string
          type: string
          hreflang: string The language for the href
          title: string
          length: string The length of the href's destination
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
          text: str The text data in the this element
        """

        self.href = href
        self.rel = rel
        self.type = link_type
        self.hreflang = hreflang
        self.title = title
        self.length = length
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def LinkFromString(xml_string):
    return CreateClassFromXMLString(Link, xml_string)


class Generator(AtomBase):
    """The atom:generator element"""

    _tag = 'generator'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _attributes['uri'] = 'uri'
    _attributes['version'] = 'version'

    def __init__(self, uri=None, version=None, text=None,
                 extension_elements=None, extension_attributes=None):
        """Constructor for Generator

        Args:
          uri: string
          version: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.uri = uri
        self.version = version
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def GeneratorFromString(xml_string):
    return CreateClassFromXMLString(Generator, xml_string)


class Text(AtomBase):
    """A foundation class from which atom:title, summary, etc. extend.

    This class should never be instantiated.
    """

    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _attributes['type'] = 'type'

    def __init__(self, text_type=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Text

        Args:
          text_type: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.type = text_type
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


class Title(Text):
    """The atom:title element"""

    _tag = 'title'
    _namespace = ATOM_NAMESPACE
    _children = Text._children.copy()
    _attributes = Text._attributes.copy()

    def __init__(self, title_type=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Title

        Args:
          title_type: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.type = title_type
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def TitleFromString(xml_string):
    return CreateClassFromXMLString(Title, xml_string)


class Subtitle(Text):
    """The atom:subtitle element"""

    _tag = 'subtitle'
    _namespace = ATOM_NAMESPACE
    _children = Text._children.copy()
    _attributes = Text._attributes.copy()

    def __init__(self, subtitle_type=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Subtitle

        Args:
          subtitle_type: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.type = subtitle_type
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def SubtitleFromString(xml_string):
    return CreateClassFromXMLString(Subtitle, xml_string)


class Rights(Text):
    """The atom:rights element"""

    _tag = 'rights'
    _namespace = ATOM_NAMESPACE
    _children = Text._children.copy()
    _attributes = Text._attributes.copy()

    def __init__(self, rights_type=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Rights

        Args:
          rights_type: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.type = rights_type
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def RightsFromString(xml_string):
    return CreateClassFromXMLString(Rights, xml_string)


class Summary(Text):
    """The atom:summary element"""

    _tag = 'summary'
    _namespace = ATOM_NAMESPACE
    _children = Text._children.copy()
    _attributes = Text._attributes.copy()

    def __init__(self, summary_type=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Summary

        Args:
          summary_type: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.type = summary_type
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def SummaryFromString(xml_string):
    return CreateClassFromXMLString(Summary, xml_string)


class Content(Text):
    """The atom:content element"""

    _tag = 'content'
    _namespace = ATOM_NAMESPACE
    _children = Text._children.copy()
    _attributes = Text._attributes.copy()
    _attributes['src'] = 'src'

    def __init__(self, content_type=None, src=None, text=None,
                 extension_elements=None, extension_attributes=None):
        """Constructor for Content

        Args:
          content_type: string
          src: string
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.type = content_type
        self.src = src
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def ContentFromString(xml_string):
    return CreateClassFromXMLString(Content, xml_string)


class Category(AtomBase):
    """The atom:category element"""

    _tag = 'category'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _attributes['term'] = 'term'
    _attributes['scheme'] = 'scheme'
    _attributes['label'] = 'label'

    def __init__(self, term=None, scheme=None, label=None, text=None,
                 extension_elements=None, extension_attributes=None):
        """Constructor for Category

        Args:
          term: str
          scheme: str
          label: str
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.term = term
        self.scheme = scheme
        self.label = label
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def CategoryFromString(xml_string):
    return CreateClassFromXMLString(Category, xml_string)


class Id(AtomBase):
    """The atom:id element."""

    _tag = 'id'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Id

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def IdFromString(xml_string):
    return CreateClassFromXMLString(Id, xml_string)


class Icon(AtomBase):
    """The atom:icon element."""

    _tag = 'icon'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Icon

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def IconFromString(xml_string):
    return CreateClassFromXMLString(Icon, xml_string)


class Logo(AtomBase):
    """The atom:logo element."""

    _tag = 'logo'
    _namespace = ATOM_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Logo

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def LogoFromString(xml_string):
    return CreateClassFromXMLString(Logo, xml_string)


class Draft(AtomBase):
    """The app:draft element which indicates if this entry should be public."""

    _tag = 'draft'
    _namespace = APP_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for app:draft

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def DraftFromString(xml_string):
    return CreateClassFromXMLString(Draft, xml_string)


class Control(AtomBase):
    """The app:control element indicating restrictions on publication.

    The APP control element may contain a draft element indicating whether or
    not this entry should be publicly available.
    """

    _tag = 'control'
    _namespace = APP_NAMESPACE
    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _children['{%s}draft' % APP_NAMESPACE] = ('draft', Draft)

    def __init__(self, draft=None, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for app:control"""

        self.draft = draft
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def ControlFromString(xml_string):
    return CreateClassFromXMLString(Control, xml_string)


class Date(AtomBase):
    """A parent class for atom:updated, published, etc."""

    # TODO Add text to and from time conversion methods to allow users to set
    # the contents of a Date to a python DateTime object.

    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


class Updated(Date):
    """The atom:updated element."""

    _tag = 'updated'
    _namespace = ATOM_NAMESPACE
    _children = Date._children.copy()
    _attributes = Date._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Updated

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def UpdatedFromString(xml_string):
    return CreateClassFromXMLString(Updated, xml_string)


class Published(Date):
    """The atom:published element."""

    _tag = 'published'
    _namespace = ATOM_NAMESPACE
    _children = Date._children.copy()
    _attributes = Date._attributes.copy()

    def __init__(self, text=None, extension_elements=None,
                 extension_attributes=None):
        """Constructor for Published

        Args:
          text: str The text data in the this element
          extension_elements: list A  list of ExtensionElement instances
          extension_attributes: dict A dictionary of attribute value string pairs
        """

        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def PublishedFromString(xml_string):
    return CreateClassFromXMLString(Published, xml_string)


class LinkFinder(object):
    """An "interface" providing methods to find link elements

    Entry elements often contain multiple links which differ in the rel
    attribute or content type. Often, developers are interested in a specific
    type of link so this class provides methods to find specific classes of
    links.

    This class is used as a mixin in Atom entries and feeds.
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

    def GetEditMediaLink(self):
        for a_link in self.link:
            if a_link.rel == 'edit-media':
                return a_link
        return None

    def GetNextLink(self):
        for a_link in self.link:
            if a_link.rel == 'next':
                return a_link
        return None

    def GetLicenseLink(self):
        for a_link in self.link:
            if a_link.rel == 'license':
                return a_link
        return None

    def GetAlternateLink(self):
        for a_link in self.link:
            if a_link.rel == 'alternate':
                return a_link
        return None


class FeedEntryParent(AtomBase, LinkFinder):
    """A super class for atom:feed and entry, contains shared attributes"""

    _children = AtomBase._children.copy()
    _attributes = AtomBase._attributes.copy()
    _children['{%s}author' % ATOM_NAMESPACE] = ('author', [Author])
    _children['{%s}category' % ATOM_NAMESPACE] = ('category', [Category])
    _children['{%s}contributor' % ATOM_NAMESPACE] = ('contributor', [Contributor])
    _children['{%s}id' % ATOM_NAMESPACE] = ('id', Id)
    _children['{%s}link' % ATOM_NAMESPACE] = ('link', [Link])
    _children['{%s}rights' % ATOM_NAMESPACE] = ('rights', Rights)
    _children['{%s}title' % ATOM_NAMESPACE] = ('title', Title)
    _children['{%s}updated' % ATOM_NAMESPACE] = ('updated', Updated)

    def __init__(self, author=None, category=None, contributor=None,
                 atom_id=None, link=None, rights=None, title=None, updated=None,
                 text=None, extension_elements=None, extension_attributes=None):
        self.author = author or []
        self.category = category or []
        self.contributor = contributor or []
        self.id = atom_id
        self.link = link or []
        self.rights = rights
        self.title = title
        self.updated = updated
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


class Source(FeedEntryParent):
    """The atom:source element"""

    _tag = 'source'
    _namespace = ATOM_NAMESPACE
    _children = FeedEntryParent._children.copy()
    _attributes = FeedEntryParent._attributes.copy()
    _children['{%s}generator' % ATOM_NAMESPACE] = ('generator', Generator)
    _children['{%s}icon' % ATOM_NAMESPACE] = ('icon', Icon)
    _children['{%s}logo' % ATOM_NAMESPACE] = ('logo', Logo)
    _children['{%s}subtitle' % ATOM_NAMESPACE] = ('subtitle', Subtitle)

    def __init__(self, author=None, category=None, contributor=None,
                 generator=None, icon=None, atom_id=None, link=None, logo=None,
                 rights=None, subtitle=None, title=None, updated=None, text=None,
                 extension_elements=None, extension_attributes=None):
        """Constructor for Source

        Args:
          author: list (optional) A list of Author instances which belong to this
              class.
          category: list (optional) A list of Category instances
          contributor: list (optional) A list on Contributor instances
          generator: Generator (optional)
          icon: Icon (optional)
          id: Id (optional) The entry's Id element
          link: list (optional) A list of Link instances
          logo: Logo (optional)
          rights: Rights (optional) The entry's Rights element
          subtitle: Subtitle (optional) The entry's subtitle element
          title: Title (optional) the entry's title element
          updated: Updated (optional) the entry's updated element
          text: String (optional) The text contents of the element. This is the
              contents of the Entry's XML text node.
              (Example: <foo>This is the text</foo>)
          extension_elements: list (optional) A list of ExtensionElement instances
              which are children of this element.
          extension_attributes: dict (optional) A dictionary of strings which are
              the values for additional XML attributes of this element.
        """

        self.author = author or []
        self.category = category or []
        self.contributor = contributor or []
        self.generator = generator
        self.icon = icon
        self.id = atom_id
        self.link = link or []
        self.logo = logo
        self.rights = rights
        self.subtitle = subtitle
        self.title = title
        self.updated = updated
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}


def SourceFromString(xml_string):
    return CreateClassFromXMLString(Source, xml_string)


class Entry(FeedEntryParent):
    """The atom:entry element"""

    _tag = 'entry'
    _namespace = ATOM_NAMESPACE
    _children = FeedEntryParent._children.copy()
    _attributes = FeedEntryParent._attributes.copy()
    _children['{%s}content' % ATOM_NAMESPACE] = ('content', Content)
    _children['{%s}published' % ATOM_NAMESPACE] = ('published', Published)
    _children['{%s}source' % ATOM_NAMESPACE] = ('source', Source)
    _children['{%s}summary' % ATOM_NAMESPACE] = ('summary', Summary)
    _children['{%s}control' % APP_NAMESPACE] = ('control', Control)

    def __init__(self, author=None, category=None, content=None,
                 contributor=None, atom_id=None, link=None, published=None, rights=None,
                 source=None, summary=None, control=None, title=None, updated=None,
                 extension_elements=None, extension_attributes=None, text=None):
        """Constructor for atom:entry

        Args:
          author: list A list of Author instances which belong to this class.
          category: list A list of Category instances
          content: Content The entry's Content
          contributor: list A list on Contributor instances
          id: Id The entry's Id element
          link: list A list of Link instances
          published: Published The entry's Published element
          rights: Rights The entry's Rights element
          source: Source the entry's source element
          summary: Summary the entry's summary element
          title: Title the entry's title element
          updated: Updated the entry's updated element
          control: The entry's app:control element which can be used to mark an
              entry as a draft which should not be publicly viewable.
          text: String The text contents of the element. This is the contents
              of the Entry's XML text node. (Example: <foo>This is the text</foo>)
          extension_elements: list A list of ExtensionElement instances which are
              children of this element.
          extension_attributes: dict A dictionary of strings which are the values
              for additional XML attributes of this element.
        """

        self.author = author or []
        self.category = category or []
        self.content = content
        self.contributor = contributor or []
        self.id = atom_id
        self.link = link or []
        self.published = published
        self.rights = rights
        self.source = source
        self.summary = summary
        self.title = title
        self.updated = updated
        self.control = control
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}

    __init__ = v1_deprecated('Please use atom.data.Entry instead.')(__init__)


def EntryFromString(xml_string):
    return CreateClassFromXMLString(Entry, xml_string)


class Feed(Source):
    """The atom:feed element"""

    _tag = 'feed'
    _namespace = ATOM_NAMESPACE
    _children = Source._children.copy()
    _attributes = Source._attributes.copy()
    _children['{%s}entry' % ATOM_NAMESPACE] = ('entry', [Entry])

    def __init__(self, author=None, category=None, contributor=None,
                 generator=None, icon=None, atom_id=None, link=None, logo=None,
                 rights=None, subtitle=None, title=None, updated=None, entry=None,
                 text=None, extension_elements=None, extension_attributes=None):
        """Constructor for Source

        Args:
          author: list (optional) A list of Author instances which belong to this
              class.
          category: list (optional) A list of Category instances
          contributor: list (optional) A list on Contributor instances
          generator: Generator (optional)
          icon: Icon (optional)
          id: Id (optional) The entry's Id element
          link: list (optional) A list of Link instances
          logo: Logo (optional)
          rights: Rights (optional) The entry's Rights element
          subtitle: Subtitle (optional) The entry's subtitle element
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

        self.author = author or []
        self.category = category or []
        self.contributor = contributor or []
        self.generator = generator
        self.icon = icon
        self.id = atom_id
        self.link = link or []
        self.logo = logo
        self.rights = rights
        self.subtitle = subtitle
        self.title = title
        self.updated = updated
        self.entry = entry or []
        self.text = text
        self.extension_elements = extension_elements or []
        self.extension_attributes = extension_attributes or {}

    __init__ = v1_deprecated('Please use atom.data.Feed instead.')(__init__)


def FeedFromString(xml_string):
    return CreateClassFromXMLString(Feed, xml_string)


class ExtensionElement(object):
    """Represents extra XML elements contained in Atom classes."""

    def __init__(self, tag, namespace=None, attributes=None,
                 children=None, text=None):
        """Constructor for EtensionElement

        Args:
          namespace: string (optional) The XML namespace for this element.
          tag: string (optional) The tag (without the namespace qualifier) for
              this element. To reconstruct the full qualified name of the element,
              combine this tag with the namespace.
          attributes: dict (optinal) The attribute value string pairs for the XML
              attributes of this element.
          children: list (optional) A list of ExtensionElements which represent
              the XML child nodes of this element.
        """

        self.namespace = namespace
        self.tag = tag
        self.attributes = attributes or {}
        self.children = children or []
        self.text = text

    def ToString(self):
        element_tree = self._TransferToElementTree(ElementTree.Element('tag__'))
        return ElementTree.tostring(element_tree, encoding="UTF-8")

    def _TransferToElementTree(self, element_tree):
        if self.tag is None:
            return None

        if self.namespace is not None:
            element_tree.tag = '{%s}%s' % (self.namespace, self.tag)
        else:
            element_tree.tag = self.tag

        for key, value in self.attributes.items():
            element_tree.attrib[key] = value

        for child in self.children:
            child._BecomeChildElement(element_tree)

        element_tree.text = self.text

        return element_tree

    def _BecomeChildElement(self, element_tree):
        """Converts this object into an etree element and adds it as a child node.

        Adds self to the ElementTree. This method is required to avoid verbose XML
        which constantly redefines the namespace.

        Args:
          element_tree: ElementTree._Element The element to which this object's XML
              will be added.
        """
        new_element = ElementTree.Element('tag__')  # uh, uhm... empty tag name - sorry google, this is bogus? (c)https://github.com/lqc
        element_tree.append(new_element)
        self._TransferToElementTree(new_element)

    def FindChildren(self, tag=None, namespace=None):
        """Searches child nodes for objects with the desired tag/namespace.

        Returns a list of extension elements within this object whose tag
        and/or namespace match those passed in. To find all children in
        a particular namespace, specify the namespace but not the tag name.
        If you specify only the tag, the result list may contain extension
        elements in multiple namespaces.

        Args:
          tag: str (optional) The desired tag
          namespace: str (optional) The desired namespace

        Returns:
          A list of elements whose tag and/or namespace match the parameters
          values
        """

        results = []

        if tag and namespace:
            for element in self.children:
                if element.tag == tag and element.namespace == namespace:
                    results.append(element)
        elif tag and not namespace:
            for element in self.children:
                if element.tag == tag:
                    results.append(element)
        elif namespace and not tag:
            for element in self.children:
                if element.namespace == namespace:
                    results.append(element)
        else:
            for element in self.children:
                results.append(element)

        return results


def ExtensionElementFromString(xml_string):
    element_tree = ElementTree.fromstring(xml_string)
    return _ExtensionElementFromElementTree(element_tree)


def _ExtensionElementFromElementTree(element_tree):
    element_tag = element_tree.tag
    if '}' in element_tag:
        namespace = element_tag[1:element_tag.index('}')]
        tag = element_tag[element_tag.index('}') + 1:]
    else:
        namespace = None
        tag = element_tag
    extension = ExtensionElement(namespace=namespace, tag=tag)
    for key, value in element_tree.attrib.items():
        extension.attributes[key] = value
    for child in element_tree:
        extension.children.append(_ExtensionElementFromElementTree(child))
    extension.text = element_tree.text
    return extension


def deprecated(warning=None):
    """Decorator to raise warning each time the function is called.

    Args:
      warning: The warning message to be displayed as a string (optinoal).
    """
    warning = warning or ''

    # This closure is what is returned from the deprecated function.
    def mark_deprecated(f):
        # The deprecated_function wraps the actual call to f.
        @wraps(f)
        def deprecated_function(*args, **kwargs):
            warnings.warn(warning, DeprecationWarning, stacklevel=2)
            return f(*args, **kwargs)

        return deprecated_function

    return mark_deprecated
