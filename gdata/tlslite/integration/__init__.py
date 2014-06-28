"""Classes for integrating TLS Lite with other packages."""

__all__ = ["AsyncStateMachine",
           "HTTPTLSConnection",
           "POP3_TLS",
           "IMAP4_TLS",
           "SMTP_TLS",
           "XMLRPCTransport",
           "TLSSocketServerMixIn",
           "TLSAsyncDispatcherMixIn",
           "TLSTwistedProtocolWrapper"]

try:
    import twisted
    del twisted
except ImportError:
   del __all__[__all__.index("TLSTwistedProtocolWrapper")]
