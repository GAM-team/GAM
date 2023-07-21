#!/usr/bin/env python
#
#    Copyright (C) 2008 Google Inc.
#
#   Licensed under the Apache License 2.0;
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


# This module is used for version 2 of the Google Data APIs.


# __author__ = 'j.s@google.com (Jeff Scudder)'

import inspect

import lxml.etree as ElementTree

try:
    from xml.dom.minidom import parseString as xmlString
except ImportError:
    xmlString = None

STRING_ENCODING = 'utf-8'


class XmlElement(object):
    """Represents an element node in an XML document.

    The text member is a UTF-8 encoded str or unicode.
    """
    _qname = None
    _other_elements = None
    _other_attributes = None
    # The rule set contains mappings for XML qnames to child members and the
    # appropriate member classes.
    _rule_set = None
    _members = None
    text = None

    def __init__(self, text=None, *args, **kwargs):
        if ('_members' not in self.__class__.__dict__
            or self.__class__._members is None):
            self.__class__._members = tuple(self.__class__._list_xml_members())
        for member_name, member_type in self.__class__._members:
            if member_name in kwargs:
                setattr(self, member_name, kwargs[member_name])
            else:
                if isinstance(member_type, list):
                    setattr(self, member_name, [])
                else:
                    setattr(self, member_name, None)
        self._other_elements = []
        self._other_attributes = {}
        if text is not None:
            self.text = text

    def _list_xml_members(cls):
        """Generator listing all members which are XML elements or attributes.

        The following members would be considered XML members:
        foo = 'abc' - indicates an XML attribute with the qname abc
        foo = SomeElement - indicates an XML child element
        foo = [AnElement] - indicates a repeating XML child element, each instance
            will be stored in a list in this member
        foo = ('att1', '{http://example.com/namespace}att2') - indicates an XML
            attribute which has different parsing rules in different versions of
            the protocol. Version 1 of the XML parsing rules will look for an
            attribute with the qname 'att1' but verion 2 of the parsing rules will
            look for a namespaced attribute with the local name of 'att2' and an
            XML namespace of 'http://example.com/namespace'.
        """
        members = []
        for pair in inspect.getmembers(cls):
            if not pair[0].startswith('_') and pair[0] != 'text':
                member_type = pair[1]
                if (isinstance(member_type, tuple) or isinstance(member_type, list)
                    or isinstance(member_type, str)
                    or (inspect.isclass(member_type)
                        and issubclass(member_type, XmlElement))):
                    members.append(pair)
        return members

    _list_xml_members = classmethod(_list_xml_members)

    def _get_rules(cls, version):
        """Initializes the _rule_set for the class which is used when parsing XML.

        This method is used internally for parsing and generating XML for an
        XmlElement. It is not recommended that you call this method directly.

        Returns:
          A tuple containing the XML parsing rules for the appropriate version.

          The tuple looks like:
          (qname, {sub_element_qname: (member_name, member_class, repeating), ..},
           {attribute_qname: member_name})

          To give a couple of concrete example, the atom.data.Control _get_rules
          with version of 2 will return:
          ('{http://www.w3.org/2007/app}control',
           {'{http://www.w3.org/2007/app}draft': ('draft',
                                                  <class 'atom.data.Draft'>,
                                                  False)},
           {})
          Calling _get_rules with version 1 on gdata.data.FeedLink will produce:
          ('{http://schemas.google.com/g/2005}feedLink',
           {'{http://www.w3.org/2005/Atom}feed': ('feed',
                                                  <class 'gdata.data.GDFeed'>,
                                                  False)},
           {'href': 'href', 'readOnly': 'read_only', 'countHint': 'count_hint',
            'rel': 'rel'})
        """
        # Initialize the _rule_set to make sure there is a slot available to store
        # the parsing rules for this version of the XML schema.
        # Look for rule set in the class __dict__ proxy so that only the
        # _rule_set for this class will be found. By using the dict proxy
        # we avoid finding rule_sets defined in superclasses.
        # The four lines below provide support for any number of versions, but it
        # runs a bit slower then hard coding slots for two versions, so I'm using
        # the below two lines.
        # if '_rule_set' not in cls.__dict__ or cls._rule_set is None:
        #  cls._rule_set = []
        # while len(cls.__dict__['_rule_set']) < version:
        #  cls._rule_set.append(None)
        # If there is no rule set cache in the class, provide slots for two XML
        # versions. If and when there is a version 3, this list will need to be
        # expanded.
        if '_rule_set' not in cls.__dict__ or cls._rule_set is None:
            cls._rule_set = [None, None]
        # If a version higher than 2 is requested, fall back to version 2 because
        # 2 is currently the highest supported version.
        if version > 2:
            return cls._get_rules(2)
        # Check the dict proxy for the rule set to avoid finding any rule sets
        # which belong to the superclass. We only want rule sets for this class.
        if cls._rule_set[version - 1] is None:
            # The rule set for each version consists of the qname for this element
            # ('{namespace}tag'), a dictionary (elements) for looking up the
            # corresponding class member when given a child element's qname, and a
            # dictionary (attributes) for looking up the corresponding class member
            # when given an XML attribute's qname.
            elements = {}
            attributes = {}
            if ('_members' not in cls.__dict__ or cls._members is None):
                cls._members = tuple(cls._list_xml_members())
            for member_name, target in cls._members:
                if isinstance(target, list):
                    # This member points to a repeating element.
                    elements[_get_qname(target[0], version)] = (member_name, target[0],
                                                                True)
                elif isinstance(target, tuple):
                    # This member points to a versioned XML attribute.
                    if version <= len(target):
                        attributes[target[version - 1]] = member_name
                    else:
                        attributes[target[-1]] = member_name
                elif isinstance(target, str):
                    # This member points to an XML attribute.
                    attributes[target] = member_name
                elif issubclass(target, XmlElement):
                    # This member points to a single occurance element.
                    elements[_get_qname(target, version)] = (member_name, target, False)
            version_rules = (_get_qname(cls, version), elements, attributes)
            cls._rule_set[version - 1] = version_rules
            return version_rules
        else:
            return cls._rule_set[version - 1]

    _get_rules = classmethod(_get_rules)

    def get_elements(self, tag=None, namespace=None, version=1):
        """Find all sub elements which match the tag and namespace.

        To find all elements in this object, call get_elements with the tag and
        namespace both set to None (the default). This method searches through
        the object's members and the elements stored in _other_elements which
        did not match any of the XML parsing rules for this class.

        Args:
          tag: str
          namespace: str
          version: int Specifies the version of the XML rules to be used when
                   searching for matching elements.

        Returns:
          A list of the matching XmlElements.
        """
        matches = []
        ignored1, elements, ignored2 = self.__class__._get_rules(version)
        if elements:
            for qname, element_def in elements.items():
                member = getattr(self, element_def[0])
                if member:
                    if _qname_matches(tag, namespace, qname):
                        if element_def[2]:
                            # If this is a repeating element, copy all instances into the
                            # result list.
                            matches.extend(member)
                        else:
                            matches.append(member)
        for element in self._other_elements:
            if _qname_matches(tag, namespace, element._qname):
                matches.append(element)
        return matches

    GetElements = get_elements
    # FindExtensions and FindChildren are provided for backwards compatibility
    # to the atom.AtomBase class.
    # However, FindExtensions may return more results than the v1 atom.AtomBase
    # method does, because get_elements searches both the expected children
    # and the unexpected "other elements". The old AtomBase.FindExtensions
    # method searched only "other elements" AKA extension_elements.
    FindExtensions = get_elements
    FindChildren = get_elements

    def get_attributes(self, tag=None, namespace=None, version=1):
        """Find all attributes which match the tag and namespace.

        To find all attributes in this object, call get_attributes with the tag
        and namespace both set to None (the default). This method searches
        through the object's members and the attributes stored in
        _other_attributes which did not fit any of the XML parsing rules for this
        class.

        Args:
          tag: str
          namespace: str
          version: int Specifies the version of the XML rules to be used when
                   searching for matching attributes.

        Returns:
          A list of XmlAttribute objects for the matching attributes.
        """
        matches = []
        ignored1, ignored2, attributes = self.__class__._get_rules(version)
        if attributes:
            for qname, attribute_def in attributes.items():
                if isinstance(attribute_def, (list, tuple)):
                    attribute_def = attribute_def[0]
                member = getattr(self, attribute_def)
                # TODO: ensure this hasn't broken existing behavior.
                # member = getattr(self, attribute_def[0])
                if member:
                    if _qname_matches(tag, namespace, qname):
                        matches.append(XmlAttribute(qname, member))
        for qname, value in self._other_attributes.items():
            if _qname_matches(tag, namespace, qname):
                matches.append(XmlAttribute(qname, value))
        return matches

    GetAttributes = get_attributes

    def _harvest_tree(self, tree, version=1):
        """Populates object members from the data in the tree Element."""
        qname, elements, attributes = self.__class__._get_rules(version)
        for element in tree:
            if elements and element.tag in elements:
                definition = elements[element.tag]
                # If this is a repeating element, make sure the member is set to a
                # list.
                if definition[2]:
                    if getattr(self, definition[0]) is None:
                        setattr(self, definition[0], [])
                    getattr(self, definition[0]).append(_xml_element_from_tree(element,
                                                                               definition[1], version))
                else:
                    setattr(self, definition[0], _xml_element_from_tree(element,
                                                                        definition[1], version))
            else:
                self._other_elements.append(_xml_element_from_tree(element, XmlElement,
                                                                   version))
        for attrib, value in tree.attrib.items():
            if attributes and attrib in attributes:
                setattr(self, attributes[attrib], value)
            else:
                self._other_attributes[attrib] = value
        if tree.text:
            self.text = tree.text

    def _to_tree(self, version=1):
        new_tree = ElementTree.Element(_get_qname(self, version))
        self._attach_members(new_tree, version)
        return new_tree

    def _attach_members(self, tree, version=1):
        """Convert members to XML elements/attributes and add them to the tree.

        Args:
          tree: An ElementTree.Element which will be modified. The members of
                this object will be added as child elements or attributes
                according to the rules described in _expected_elements and
                _expected_attributes. The elements and attributes stored in
                other_attributes and other_elements are also added a children
                of this tree.
          version: int Ingnored in this method but used by VersionedElement.
          encoding: str (optional)
        """
        qname, elements, attributes = self.__class__._get_rules(version)
        encoding = STRING_ENCODING
        # Add the expected elements and attributes to the tree.
        if elements:
            for tag, element_def in elements.items():
                member = getattr(self, element_def[0])
                # If this is a repeating element and there are members in the list.
                if member and element_def[2]:
                    for instance in member:
                        instance._become_child(tree, version)
                elif member:
                    member._become_child(tree, version)
        if attributes:
            for attribute_tag, member_name in attributes.items():
                value = getattr(self, member_name)
                if value:
                    tree.attrib[attribute_tag] = value
        # Add the unexpected (other) elements and attributes to the tree.
        for element in self._other_elements:
            element._become_child(tree, version)
        for key, value in self._other_attributes.items():
            # I'm not sure if unicode can be used in the attribute name, so for now
            # we assume the encoding is correct for the attribute name.
            if not isinstance(value, str):
                value = value.decode(encoding)
            tree.attrib[key] = value
        if self.text:
            if isinstance(self.text, str):
                tree.text = self.text
            else:
                tree.text = self.text.decode(encoding)

    def to_string(self, version=1, encoding=None, pretty_print=None):
        """Converts this object to XML."""

        tree_string = ElementTree.tostring(self._to_tree(version))

        if pretty_print and xmlString is not None:
            return xmlString(tree_string).toprettyxml()

        return tree_string

    ToString = to_string

    def __str__(self):
        return self.to_string()

    def _become_child(self, tree, version=1):
        """Adds a child element to tree with the XML data in self."""
        new_child = ElementTree.Element(_get_qname(self, version))
        tree.append(new_child)
        new_child.tag = _get_qname(self, version)
        self._attach_members(new_child, version)

    def __get_extension_elements(self):
        return self._other_elements

    def __set_extension_elements(self, elements):
        self._other_elements = elements

    extension_elements = property(__get_extension_elements,
                                  __set_extension_elements,
                                  """Provides backwards compatibility for v1 atom.AtomBase classes.""")

    def __get_extension_attributes(self):
        return self._other_attributes

    def __set_extension_attributes(self, attributes):
        self._other_attributes = attributes

    extension_attributes = property(__get_extension_attributes,
                                    __set_extension_attributes,
                                    """Provides backwards compatibility for v1 atom.AtomBase classes.""")

    def _get_tag(self, version=1):
        qname = _get_qname(self, version)
        if qname:
            return qname[qname.find('}') + 1:]
        return None

    def _get_namespace(self, version=1):
        qname = _get_qname(self, version)
        if qname.startswith('{'):
            return qname[1:qname.find('}')]
        else:
            return None

    def _set_tag(self, tag):
        if isinstance(self._qname, tuple):
            self._qname = self._qname.copy()
            if self._qname[0].startswith('{'):
                self._qname[0] = '{%s}%s' % (self._get_namespace(1), tag)
            else:
                self._qname[0] = tag
        else:
            if self._qname is not None and self._qname.startswith('{'):
                self._qname = '{%s}%s' % (self._get_namespace(), tag)
            else:
                self._qname = tag

    def _set_namespace(self, namespace):
        tag = self._get_tag(1)
        if tag is None:
            tag = ''
        if isinstance(self._qname, tuple):
            self._qname = self._qname.copy()
            if namespace:
                self._qname[0] = '{%s}%s' % (namespace, tag)
            else:
                self._qname[0] = tag
        else:
            if namespace:
                self._qname = '{%s}%s' % (namespace, tag)
            else:
                self._qname = tag

    tag = property(_get_tag, _set_tag,
                   """Provides backwards compatibility for v1 atom.AtomBase classes.""")

    namespace = property(_get_namespace, _set_namespace,
                         """Provides backwards compatibility for v1 atom.AtomBase classes.""")

    # Provided for backwards compatibility to atom.ExtensionElement
    children = extension_elements
    attributes = extension_attributes


def _get_qname(element, version):
    if isinstance(element._qname, tuple):
        if version <= len(element._qname):
            return element._qname[version - 1]
        else:
            return element._qname[-1]
    else:
        return element._qname


def _qname_matches(tag, namespace, qname):
    """Logic determines if a QName matches the desired local tag and namespace.

    This is used in XmlElement.get_elements and XmlElement.get_attributes to
    find matches in the element's members (among all expected-and-unexpected
    elements-and-attributes).

    Args:
      expected_tag: string
      expected_namespace: string
      qname: string in the form '{xml_namespace}localtag' or 'tag' if there is
             no namespace.

    Returns:
      boolean True if the member's tag and namespace fit the expected tag and
      namespace.
    """
    # If there is no expected namespace or tag, then everything will match.
    if qname is None:
        member_tag = None
        member_namespace = None
    else:
        if qname.startswith('{'):
            member_namespace = qname[1:qname.index('}')]
            member_tag = qname[qname.index('}') + 1:]
        else:
            member_namespace = None
            member_tag = qname
    return ((tag is None and namespace is None)
            # If there is a tag, but no namespace, see if the local tag matches.
            or (namespace is None and member_tag == tag)
            # There was no tag, but there was a namespace so see if the namespaces
            # match.
            or (tag is None and member_namespace == namespace)
            # There was no tag, and the desired elements have no namespace, so check
            # to see that the member's namespace is None.
            or (tag is None and namespace == ''
                and member_namespace is None)
            # The tag and the namespace both match.
            or (tag == member_tag
                and namespace == member_namespace)
            # The tag matches, and the expected namespace is the empty namespace,
            # check to make sure the member's namespace is None.
            or (tag == member_tag and namespace == ''
                and member_namespace is None))


def parse(xml_string, target_class=None, version=1):
    """Parses the XML string according to the rules for the target_class.

    Args:
      xml_string: bytes
      target_class: XmlElement or a subclass. If None is specified, the
          XmlElement class is used.
      version: int (optional) The version of the schema which should be used when
          converting the XML into an object. The default is 1.
      encoding: str (optional) The character encoding of the bytes in the
          xml_string. Default is 'UTF-8'.
    """
    if target_class is None:
        target_class = XmlElement
    if not isinstance(xml_string, bytes):
        raise Exception("This function only accepts bytes")
    tree = ElementTree.fromstring(xml_string)
    return _xml_element_from_tree(tree, target_class, version)


Parse = parse
xml_element_from_string = parse
XmlElementFromString = xml_element_from_string


def _xml_element_from_tree(tree, target_class, version=1):
    if target_class._qname is None:
        instance = target_class()
        instance._qname = tree.tag
        instance._harvest_tree(tree, version)
        return instance
    # TODO handle the namespace-only case
    # Namespace only will be used with Google Spreadsheets rows and
    # Google Base item attributes.
    elif tree.tag == _get_qname(target_class, version):
        instance = target_class()
        instance._harvest_tree(tree, version)
        return instance
    return None


class XmlAttribute(object):
    def __init__(self, qname, value):
        self._qname = qname
        self.value = value
