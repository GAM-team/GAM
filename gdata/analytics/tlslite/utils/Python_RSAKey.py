"""Pure-Python RSA implementation."""

from cryptomath import *
import xmltools
from ASN1Parser import ASN1Parser
from RSAKey import *

class Python_RSAKey(RSAKey):
    def __init__(self, n=0, e=0, d=0, p=0, q=0, dP=0, dQ=0, qInv=0):
        if (n and not e) or (e and not n):
            raise AssertionError()
        self.n = n
        self.e = e
        self.d = d
        self.p = p
        self.q = q
        self.dP = dP
        self.dQ = dQ
        self.qInv = qInv
        self.blinder = 0
        self.unblinder = 0

    def hasPrivateKey(self):
        return self.d != 0

    def hash(self):
        s = self.writeXMLPublicKey('\t\t')
        return hashAndBase64(s.strip())

    def _rawPrivateKeyOp(self, m):
        #Create blinding values, on the first pass:
        if not self.blinder:
            self.unblinder = getRandomNumber(2, self.n)
            self.blinder = powMod(invMod(self.unblinder, self.n), self.e,
                                  self.n)

        #Blind the input
        m = (m * self.blinder) % self.n

        #Perform the RSA operation
        c = self._rawPrivateKeyOpHelper(m)

        #Unblind the output
        c = (c * self.unblinder) % self.n

        #Update blinding values
        self.blinder = (self.blinder * self.blinder) % self.n
        self.unblinder = (self.unblinder * self.unblinder) % self.n

        #Return the output
        return c


    def _rawPrivateKeyOpHelper(self, m):
        #Non-CRT version
        #c = powMod(m, self.d, self.n)

        #CRT version  (~3x faster)
        s1 = powMod(m, self.dP, self.p)
        s2 = powMod(m, self.dQ, self.q)
        h = ((s1 - s2) * self.qInv) % self.p
        c = s2 + self.q * h
        return c

    def _rawPublicKeyOp(self, c):
        m = powMod(c, self.e, self.n)
        return m

    def acceptsPassword(self): return False

    def write(self, indent=''):
        if self.d:
            s = indent+'<privateKey xmlns="http://trevp.net/rsa">\n'
        else:
            s = indent+'<publicKey xmlns="http://trevp.net/rsa">\n'
        s += indent+'\t<n>%s</n>\n' % numberToBase64(self.n)
        s += indent+'\t<e>%s</e>\n' % numberToBase64(self.e)
        if self.d:
            s += indent+'\t<d>%s</d>\n' % numberToBase64(self.d)
            s += indent+'\t<p>%s</p>\n' % numberToBase64(self.p)
            s += indent+'\t<q>%s</q>\n' % numberToBase64(self.q)
            s += indent+'\t<dP>%s</dP>\n' % numberToBase64(self.dP)
            s += indent+'\t<dQ>%s</dQ>\n' % numberToBase64(self.dQ)
            s += indent+'\t<qInv>%s</qInv>\n' % numberToBase64(self.qInv)
            s += indent+'</privateKey>'
        else:
            s += indent+'</publicKey>'
        #Only add \n if part of a larger structure
        if indent != '':
            s += '\n'
        return s

    def writeXMLPublicKey(self, indent=''):
        return Python_RSAKey(self.n, self.e).write(indent)

    def generate(bits):
        key = Python_RSAKey()
        p = getRandomPrime(bits/2, False)
        q = getRandomPrime(bits/2, False)
        t = lcm(p-1, q-1)
        key.n = p * q
        key.e = 3L  #Needed to be long, for Java
        key.d = invMod(key.e, t)
        key.p = p
        key.q = q
        key.dP = key.d % (p-1)
        key.dQ = key.d % (q-1)
        key.qInv = invMod(q, p)
        return key
    generate = staticmethod(generate)

    def parsePEM(s, passwordCallback=None):
        """Parse a string containing a <privateKey> or <publicKey>, or
        PEM-encoded key."""

        start = s.find("-----BEGIN PRIVATE KEY-----")
        if start != -1:
            end = s.find("-----END PRIVATE KEY-----")
            if end == -1:
                raise SyntaxError("Missing PEM Postfix")
            s = s[start+len("-----BEGIN PRIVATE KEY -----") : end]
            bytes = base64ToBytes(s)
            return Python_RSAKey._parsePKCS8(bytes)
        else:
            start = s.find("-----BEGIN RSA PRIVATE KEY-----")
            if start != -1:
                end = s.find("-----END RSA PRIVATE KEY-----")
                if end == -1:
                    raise SyntaxError("Missing PEM Postfix")
                s = s[start+len("-----BEGIN RSA PRIVATE KEY -----") : end]
                bytes = base64ToBytes(s)
                return Python_RSAKey._parseSSLeay(bytes)
        raise SyntaxError("Missing PEM Prefix")
    parsePEM = staticmethod(parsePEM)

    def parseXML(s):
        element = xmltools.parseAndStripWhitespace(s)
        return Python_RSAKey._parseXML(element)
    parseXML = staticmethod(parseXML)

    def _parsePKCS8(bytes):
        p = ASN1Parser(bytes)

        version = p.getChild(0).value[0]
        if version != 0:
            raise SyntaxError("Unrecognized PKCS8 version")

        rsaOID = p.getChild(1).value
        if list(rsaOID) != [6, 9, 42, 134, 72, 134, 247, 13, 1, 1, 1, 5, 0]:
            raise SyntaxError("Unrecognized AlgorithmIdentifier")

        #Get the privateKey
        privateKeyP = p.getChild(2)

        #Adjust for OCTET STRING encapsulation
        privateKeyP = ASN1Parser(privateKeyP.value)

        return Python_RSAKey._parseASN1PrivateKey(privateKeyP)
    _parsePKCS8 = staticmethod(_parsePKCS8)

    def _parseSSLeay(bytes):
        privateKeyP = ASN1Parser(bytes)
        return Python_RSAKey._parseASN1PrivateKey(privateKeyP)
    _parseSSLeay = staticmethod(_parseSSLeay)

    def _parseASN1PrivateKey(privateKeyP):
        version = privateKeyP.getChild(0).value[0]
        if version != 0:
            raise SyntaxError("Unrecognized RSAPrivateKey version")
        n = bytesToNumber(privateKeyP.getChild(1).value)
        e = bytesToNumber(privateKeyP.getChild(2).value)
        d = bytesToNumber(privateKeyP.getChild(3).value)
        p = bytesToNumber(privateKeyP.getChild(4).value)
        q = bytesToNumber(privateKeyP.getChild(5).value)
        dP = bytesToNumber(privateKeyP.getChild(6).value)
        dQ = bytesToNumber(privateKeyP.getChild(7).value)
        qInv = bytesToNumber(privateKeyP.getChild(8).value)
        return Python_RSAKey(n, e, d, p, q, dP, dQ, qInv)
    _parseASN1PrivateKey = staticmethod(_parseASN1PrivateKey)

    def _parseXML(element):
        try:
            xmltools.checkName(element, "privateKey")
        except SyntaxError:
            xmltools.checkName(element, "publicKey")

        #Parse attributes
        xmltools.getReqAttribute(element, "xmlns", "http://trevp.net/rsa\Z")
        xmltools.checkNoMoreAttributes(element)

        #Parse public values (<n> and <e>)
        n = base64ToNumber(xmltools.getText(xmltools.getChild(element, 0, "n"), xmltools.base64RegEx))
        e = base64ToNumber(xmltools.getText(xmltools.getChild(element, 1, "e"), xmltools.base64RegEx))
        d = 0
        p = 0
        q = 0
        dP = 0
        dQ = 0
        qInv = 0
        #Parse private values, if present
        if element.childNodes.length>=3:
            d = base64ToNumber(xmltools.getText(xmltools.getChild(element, 2, "d"), xmltools.base64RegEx))
            p = base64ToNumber(xmltools.getText(xmltools.getChild(element, 3, "p"), xmltools.base64RegEx))
            q = base64ToNumber(xmltools.getText(xmltools.getChild(element, 4, "q"), xmltools.base64RegEx))
            dP = base64ToNumber(xmltools.getText(xmltools.getChild(element, 5, "dP"), xmltools.base64RegEx))
            dQ = base64ToNumber(xmltools.getText(xmltools.getChild(element, 6, "dQ"), xmltools.base64RegEx))
            qInv = base64ToNumber(xmltools.getText(xmltools.getLastChild(element, 7, "qInv"), xmltools.base64RegEx))
        return Python_RSAKey(n, e, d, p, q, dP, dQ, qInv)
    _parseXML = staticmethod(_parseXML)
