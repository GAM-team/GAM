"""Class representing an X.509 certificate."""

from utils.ASN1Parser import ASN1Parser
from utils.cryptomath import *
from utils.keyfactory import _createPublicRSAKey


class X509:
    """This class represents an X.509 certificate.

    @type bytes: L{array.array} of unsigned bytes
    @ivar bytes: The DER-encoded ASN.1 certificate

    @type publicKey: L{tlslite.utils.RSAKey.RSAKey}
    @ivar publicKey: The subject public key from the certificate.
    """

    def __init__(self):
        self.bytes = createByteArraySequence([])
        self.publicKey = None

    def parse(self, s):
        """Parse a PEM-encoded X.509 certificate.

        @type s: str
        @param s: A PEM-encoded X.509 certificate (i.e. a base64-encoded
        certificate wrapped with "-----BEGIN CERTIFICATE-----" and
        "-----END CERTIFICATE-----" tags).
        """

        start = s.find("-----BEGIN CERTIFICATE-----")
        end = s.find("-----END CERTIFICATE-----")
        if start == -1:
            raise SyntaxError("Missing PEM prefix")
        if end == -1:
            raise SyntaxError("Missing PEM postfix")
        s = s[start+len("-----BEGIN CERTIFICATE-----") : end]

        bytes = base64ToBytes(s)
        self.parseBinary(bytes)
        return self

    def parseBinary(self, bytes):
        """Parse a DER-encoded X.509 certificate.

        @type bytes: str or L{array.array} of unsigned bytes
        @param bytes: A DER-encoded X.509 certificate.
        """

        if isinstance(bytes, type("")):
            bytes = stringToBytes(bytes)

        self.bytes = bytes
        p = ASN1Parser(bytes)

        #Get the tbsCertificate
        tbsCertificateP = p.getChild(0)

        #Is the optional version field present?
        #This determines which index the key is at.
        if tbsCertificateP.value[0]==0xA0:
            subjectPublicKeyInfoIndex = 6
        else:
            subjectPublicKeyInfoIndex = 5

        #Get the subjectPublicKeyInfo
        subjectPublicKeyInfoP = tbsCertificateP.getChild(\
                                    subjectPublicKeyInfoIndex)

        #Get the algorithm
        algorithmP = subjectPublicKeyInfoP.getChild(0)
        rsaOID = algorithmP.value
        if list(rsaOID) != [6, 9, 42, 134, 72, 134, 247, 13, 1, 1, 1, 5, 0]:
            raise SyntaxError("Unrecognized AlgorithmIdentifier")

        #Get the subjectPublicKey
        subjectPublicKeyP = subjectPublicKeyInfoP.getChild(1)

        #Adjust for BIT STRING encapsulation
        if (subjectPublicKeyP.value[0] !=0):
            raise SyntaxError()
        subjectPublicKeyP = ASN1Parser(subjectPublicKeyP.value[1:])

        #Get the modulus and exponent
        modulusP = subjectPublicKeyP.getChild(0)
        publicExponentP = subjectPublicKeyP.getChild(1)

        #Decode them into numbers
        n = bytesToNumber(modulusP.value)
        e = bytesToNumber(publicExponentP.value)

        #Create a public key instance
        self.publicKey = _createPublicRSAKey(n, e)

    def getFingerprint(self):
        """Get the hex-encoded fingerprint of this certificate.

        @rtype: str
        @return: A hex-encoded fingerprint.
        """
        return sha.sha(self.bytes).hexdigest()

    def getCommonName(self):
        """Get the Subject's Common Name from the certificate.

        The cryptlib_py module must be installed in order to use this
        function.

        @rtype: str or None
        @return: The CN component of the certificate's subject DN, if
        present.
        """
        import cryptlib_py
        import array
        c = cryptlib_py.cryptImportCert(self.bytes, cryptlib_py.CRYPT_UNUSED)
        name = cryptlib_py.CRYPT_CERTINFO_COMMONNAME
        try:
            try:
                length = cryptlib_py.cryptGetAttributeString(c, name, None)
                returnVal = array.array('B', [0] * length)
                cryptlib_py.cryptGetAttributeString(c, name, returnVal)
                returnVal = returnVal.tostring()
            except cryptlib_py.CryptException, e:
                if e[0] == cryptlib_py.CRYPT_ERROR_NOTFOUND:
                    returnVal = None
            return returnVal
        finally:
            cryptlib_py.cryptDestroyCert(c)

    def writeBytes(self):
        return self.bytes


