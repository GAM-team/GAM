"""Class representing an X.509 certificate chain."""

from utils import cryptomath

class X509CertChain:
    """This class represents a chain of X.509 certificates.

    @type x509List: list
    @ivar x509List: A list of L{tlslite.X509.X509} instances,
    starting with the end-entity certificate and with every
    subsequent certificate certifying the previous.
    """

    def __init__(self, x509List=None):
        """Create a new X509CertChain.

        @type x509List: list
        @param x509List: A list of L{tlslite.X509.X509} instances,
        starting with the end-entity certificate and with every
        subsequent certificate certifying the previous.
        """
        if x509List:
            self.x509List = x509List
        else:
            self.x509List = []

    def getNumCerts(self):
        """Get the number of certificates in this chain.

        @rtype: int
        """
        return len(self.x509List)

    def getEndEntityPublicKey(self):
        """Get the public key from the end-entity certificate.

        @rtype: L{tlslite.utils.RSAKey.RSAKey}
        """
        if self.getNumCerts() == 0:
            raise AssertionError()
        return self.x509List[0].publicKey

    def getFingerprint(self):
        """Get the hex-encoded fingerprint of the end-entity certificate.

        @rtype: str
        @return: A hex-encoded fingerprint.
        """
        if self.getNumCerts() == 0:
            raise AssertionError()
        return self.x509List[0].getFingerprint()

    def getCommonName(self):
        """Get the Subject's Common Name from the end-entity certificate.

        The cryptlib_py module must be installed in order to use this
        function.

        @rtype: str or None
        @return: The CN component of the certificate's subject DN, if
        present.
        """
        if self.getNumCerts() == 0:
            raise AssertionError()
        return self.x509List[0].getCommonName()

    def validate(self, x509TrustList):
        """Check the validity of the certificate chain.

        This checks that every certificate in the chain validates with
        the subsequent one, until some certificate validates with (or
        is identical to) one of the passed-in root certificates.

        The cryptlib_py module must be installed in order to use this
        function.

        @type x509TrustList: list of L{tlslite.X509.X509}
        @param x509TrustList: A list of trusted root certificates.  The
        certificate chain must extend to one of these certificates to
        be considered valid.
        """

        import cryptlib_py
        c1 = None
        c2 = None
        lastC = None
        rootC = None

        try:
            rootFingerprints = [c.getFingerprint() for c in x509TrustList]

            #Check that every certificate in the chain validates with the
            #next one
            for cert1, cert2 in zip(self.x509List, self.x509List[1:]):

                #If we come upon a root certificate, we're done.
                if cert1.getFingerprint() in rootFingerprints:
                    return True

                c1 = cryptlib_py.cryptImportCert(cert1.writeBytes(),
                                                 cryptlib_py.CRYPT_UNUSED)
                c2 = cryptlib_py.cryptImportCert(cert2.writeBytes(),
                                                 cryptlib_py.CRYPT_UNUSED)
                try:
                    cryptlib_py.cryptCheckCert(c1, c2)
                except:
                    return False
                cryptlib_py.cryptDestroyCert(c1)
                c1 = None
                cryptlib_py.cryptDestroyCert(c2)
                c2 = None

            #If the last certificate is one of the root certificates, we're
            #done.
            if self.x509List[-1].getFingerprint() in rootFingerprints:
                return True

            #Otherwise, find a root certificate that the last certificate
            #chains to, and validate them.
            lastC = cryptlib_py.cryptImportCert(self.x509List[-1].writeBytes(),
                                                cryptlib_py.CRYPT_UNUSED)
            for rootCert in x509TrustList:
                rootC = cryptlib_py.cryptImportCert(rootCert.writeBytes(),
                                                    cryptlib_py.CRYPT_UNUSED)
                if self._checkChaining(lastC, rootC):
                    try:
                        cryptlib_py.cryptCheckCert(lastC, rootC)
                        return True
                    except:
                        return False
            return False
        finally:
            if not (c1 is None):
                cryptlib_py.cryptDestroyCert(c1)
            if not (c2 is None):
                cryptlib_py.cryptDestroyCert(c2)
            if not (lastC is None):
                cryptlib_py.cryptDestroyCert(lastC)
            if not (rootC is None):
                cryptlib_py.cryptDestroyCert(rootC)



    def _checkChaining(self, lastC, rootC):
        import cryptlib_py
        import array
        def compareNames(name):
            try:
                length = cryptlib_py.cryptGetAttributeString(lastC, name, None)
                lastName = array.array('B', [0] * length)
                cryptlib_py.cryptGetAttributeString(lastC, name, lastName)
                lastName = lastName.tostring()
            except cryptlib_py.CryptException, e:
                if e[0] == cryptlib_py.CRYPT_ERROR_NOTFOUND:
                    lastName = None
            try:
                length = cryptlib_py.cryptGetAttributeString(rootC, name, None)
                rootName = array.array('B', [0] * length)
                cryptlib_py.cryptGetAttributeString(rootC, name, rootName)
                rootName = rootName.tostring()
            except cryptlib_py.CryptException, e:
                if e[0] == cryptlib_py.CRYPT_ERROR_NOTFOUND:
                    rootName = None

            return lastName == rootName

        cryptlib_py.cryptSetAttribute(lastC,
                                      cryptlib_py.CRYPT_CERTINFO_ISSUERNAME,
                                      cryptlib_py.CRYPT_UNUSED)

        if not compareNames(cryptlib_py.CRYPT_CERTINFO_COUNTRYNAME):
            return False
        if not compareNames(cryptlib_py.CRYPT_CERTINFO_LOCALITYNAME):
            return False
        if not compareNames(cryptlib_py.CRYPT_CERTINFO_ORGANIZATIONNAME):
            return False
        if not compareNames(cryptlib_py.CRYPT_CERTINFO_ORGANIZATIONALUNITNAME):
            return False
        if not compareNames(cryptlib_py.CRYPT_CERTINFO_COMMONNAME):
            return False
        return True