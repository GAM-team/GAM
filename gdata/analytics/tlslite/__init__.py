"""
TLS Lite is a free python library that implements SSL v3, TLS v1, and
TLS v1.1.  TLS Lite supports non-traditional authentication methods
such as SRP, shared keys, and cryptoIDs, in addition to X.509
certificates.  TLS Lite is pure python, however it can access OpenSSL,
cryptlib, pycrypto, and GMPY for faster crypto operations.  TLS Lite
integrates with httplib, xmlrpclib, poplib, imaplib, smtplib,
SocketServer, asyncore, and Twisted.

To use, do::

    from tlslite.api import *

Then use the L{tlslite.TLSConnection.TLSConnection} class with a socket,
or use one of the integration classes in L{tlslite.integration}.

@version: 0.3.8
"""
__version__ = "0.3.8"

__all__ = ["api",
           "BaseDB",
           "Checker",
           "constants",
           "errors",
           "FileObject",
           "HandshakeSettings",
           "mathtls",
           "messages",
           "Session",
           "SessionCache",
           "SharedKeyDB",
           "TLSConnection",
           "TLSRecordLayer",
           "VerifierDB",
           "X509",
           "X509CertChain",
           "integration",
           "utils"]
