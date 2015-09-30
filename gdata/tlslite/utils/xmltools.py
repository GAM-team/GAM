"""Helper functions for XML.

This module has misc. helper functions for working with XML DOM nodes."""

from compat import *
import os
import re

if os.name == "java":
    # Only for Jython
    from javax.xml.parsers import *
    import java

    builder = DocumentBuilderFactory.newInstance().newDocumentBuilder()

    def parseDocument(s):
        stream = java.io.ByteArrayInputStream(java.lang.String(s).getBytes())
        return builder.parse(stream)
else:
    from xml.dom import minidom
    from xml.sax import saxutils

    def parseDocument(s):
        return minidom.parseString(s)

def parseAndStripWhitespace(s):
    try:
        element = parseDocument(s).documentElement
    except BaseException, e:
        raise SyntaxError(str(e))
    stripWhitespace(element)
    return element

#Goes through a DOM tree and removes whitespace besides child elements,
#as long as this whitespace is correctly tab-ified
def stripWhitespace(element, tab=0):
    element.normalize()

    lastSpacer = "\n" + ("\t"*tab)
    spacer = lastSpacer + "\t"

    #Zero children aren't allowed (i.e. <empty/>)
    #This makes writing output simpler, and matches Canonical XML
    if element.childNodes.length==0: #DON'T DO len(element.childNodes) - doesn't work in Jython
        raise SyntaxError("Empty XML elements not allowed")

    #If there's a single child, it must be text context
    if element.childNodes.length==1:
        if element.firstChild.nodeType == element.firstChild.TEXT_NODE:
            #If it's an empty element, remove
            if element.firstChild.data == lastSpacer:
                element.removeChild(element.firstChild)
            return
        #If not text content, give an error
        elif element.firstChild.nodeType == element.firstChild.ELEMENT_NODE:
            raise SyntaxError("Bad whitespace under '%s'" % element.tagName)
        else:
            raise SyntaxError("Unexpected node type in XML document")

    #Otherwise there's multiple child element
    child = element.firstChild
    while child:
        if child.nodeType == child.ELEMENT_NODE:
            stripWhitespace(child, tab+1)
            child = child.nextSibling
        elif child.nodeType == child.TEXT_NODE:
            if child == element.lastChild:
                if child.data != lastSpacer:
                    raise SyntaxError("Bad whitespace under '%s'" % element.tagName)
            elif child.data != spacer:
                raise SyntaxError("Bad whitespace under '%s'" % element.tagName)
            next = child.nextSibling
            element.removeChild(child)
            child = next
        else:
            raise SyntaxError("Unexpected node type in XML document")


def checkName(element, name):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Missing element: '%s'" % name)

    if name == None:
        return

    if element.tagName != name:
        raise SyntaxError("Wrong element name: should be '%s', is '%s'" % (name, element.tagName))

def getChild(element, index, name=None):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Wrong node type in getChild()")

    child = element.childNodes.item(index)
    if child == None:
        raise SyntaxError("Missing child: '%s'" % name)
    checkName(child, name)
    return child

def getChildIter(element, index):
    class ChildIter:
        def __init__(self, element, index):
            self.element = element
            self.index = index

        def next(self):
            if self.index < len(self.element.childNodes):
                retVal = self.element.childNodes.item(self.index)
                self.index += 1
            else:
                retVal = None
            return retVal

        def checkEnd(self):
            if self.index != len(self.element.childNodes):
                raise SyntaxError("Too many elements under: '%s'" % self.element.tagName)
    return ChildIter(element, index)

def getChildOrNone(element, index):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Wrong node type in getChild()")
    child = element.childNodes.item(index)
    return child

def getLastChild(element, index, name=None):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Wrong node type in getLastChild()")

    child = element.childNodes.item(index)
    if child == None:
        raise SyntaxError("Missing child: '%s'" % name)
    if child != element.lastChild:
        raise SyntaxError("Too many elements under: '%s'" % element.tagName)
    checkName(child, name)
    return child

#Regular expressions for syntax-checking attribute and element content
nsRegEx = "http://trevp.net/cryptoID\Z"
cryptoIDRegEx = "([a-km-z3-9]{5}\.){3}[a-km-z3-9]{5}\Z"
urlRegEx = "http(s)?://.{1,100}\Z"
sha1Base64RegEx = "[A-Za-z0-9+/]{27}=\Z"
base64RegEx = "[A-Za-z0-9+/]+={0,4}\Z"
certsListRegEx = "(0)?(1)?(2)?(3)?(4)?(5)?(6)?(7)?(8)?(9)?\Z"
keyRegEx = "[A-Z]\Z"
keysListRegEx = "(A)?(B)?(C)?(D)?(E)?(F)?(G)?(H)?(I)?(J)?(K)?(L)?(M)?(N)?(O)?(P)?(Q)?(R)?(S)?(T)?(U)?(V)?(W)?(X)?(Y)?(Z)?\Z"
dateTimeRegEx = "\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ\Z"
shortStringRegEx = ".{1,100}\Z"
exprRegEx = "[a-zA-Z0-9 ,()]{1,200}\Z"
notAfterDeltaRegEx = "0|([1-9][0-9]{0,8})\Z" #A number from 0 to (1 billion)-1
booleanRegEx = "(true)|(false)"

def getReqAttribute(element, attrName, regEx=""):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Wrong node type in getReqAttribute()")

    value = element.getAttribute(attrName)
    if not value:
        raise SyntaxError("Missing Attribute: " + attrName)
    if not re.match(regEx, value):
        raise SyntaxError("Bad Attribute Value for '%s': '%s' " % (attrName, value))
    element.removeAttribute(attrName)
    return str(value) #de-unicode it; this is needed for bsddb, for example

def getAttribute(element, attrName, regEx=""):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Wrong node type in getAttribute()")

    value = element.getAttribute(attrName)
    if value:
        if not re.match(regEx, value):
            raise SyntaxError("Bad Attribute Value for '%s': '%s' " % (attrName, value))
        element.removeAttribute(attrName)
        return str(value) #de-unicode it; this is needed for bsddb, for example

def checkNoMoreAttributes(element):
    if element.nodeType != element.ELEMENT_NODE:
        raise SyntaxError("Wrong node type in checkNoMoreAttributes()")

    if element.attributes.length!=0:
        raise SyntaxError("Extra attributes on '%s'" % element.tagName)

def getText(element, regEx=""):
    textNode = element.firstChild
    if textNode == None:
        raise SyntaxError("Empty element '%s'" % element.tagName)
    if textNode.nodeType != textNode.TEXT_NODE:
        raise SyntaxError("Non-text node: '%s'" % element.tagName)
    if not re.match(regEx, textNode.data):
        raise SyntaxError("Bad Text Value for '%s': '%s' " % (element.tagName, textNode.data))
    return str(textNode.data) #de-unicode it; this is needed for bsddb, for example

#Function for adding tabs to a string
def indent(s, steps, ch="\t"):
    tabs = ch*steps
    if s[-1] != "\n":
        s = tabs + s.replace("\n", "\n"+tabs)
    else:
        s = tabs + s.replace("\n", "\n"+tabs)
        s = s[ : -len(tabs)]
    return s

def escape(s):
    return saxutils.escape(s)
