"""Exception classes.
@sort: TLSError, TLSAbruptCloseError, TLSAlert, TLSLocalAlert, TLSRemoteAlert,
TLSAuthenticationError, TLSNoAuthenticationError, TLSAuthenticationTypeError,
TLSFingerprintError, TLSAuthorizationError, TLSValidationError, TLSFaultError
"""

from constants import AlertDescription, AlertLevel

class TLSError(Exception):
    """Base class for all TLS Lite exceptions."""
    pass

class TLSAbruptCloseError(TLSError):
    """The socket was closed without a proper TLS shutdown.

    The TLS specification mandates that an alert of some sort
    must be sent before the underlying socket is closed.  If the socket
    is closed without this, it could signify that an attacker is trying
    to truncate the connection.  It could also signify a misbehaving
    TLS implementation, or a random network failure.
    """
    pass

class TLSAlert(TLSError):
    """A TLS alert has been signalled."""
    pass

    _descriptionStr = {\
        AlertDescription.close_notify: "close_notify",\
        AlertDescription.unexpected_message: "unexpected_message",\
        AlertDescription.bad_record_mac: "bad_record_mac",\
        AlertDescription.decryption_failed: "decryption_failed",\
        AlertDescription.record_overflow: "record_overflow",\
        AlertDescription.decompression_failure: "decompression_failure",\
        AlertDescription.handshake_failure: "handshake_failure",\
        AlertDescription.no_certificate: "no certificate",\
        AlertDescription.bad_certificate: "bad_certificate",\
        AlertDescription.unsupported_certificate: "unsupported_certificate",\
        AlertDescription.certificate_revoked: "certificate_revoked",\
        AlertDescription.certificate_expired: "certificate_expired",\
        AlertDescription.certificate_unknown: "certificate_unknown",\
        AlertDescription.illegal_parameter: "illegal_parameter",\
        AlertDescription.unknown_ca: "unknown_ca",\
        AlertDescription.access_denied: "access_denied",\
        AlertDescription.decode_error: "decode_error",\
        AlertDescription.decrypt_error: "decrypt_error",\
        AlertDescription.export_restriction: "export_restriction",\
        AlertDescription.protocol_version: "protocol_version",\
        AlertDescription.insufficient_security: "insufficient_security",\
        AlertDescription.internal_error: "internal_error",\
        AlertDescription.user_canceled: "user_canceled",\
        AlertDescription.no_renegotiation: "no_renegotiation",\
        AlertDescription.unknown_srp_username: "unknown_srp_username",\
        AlertDescription.missing_srp_username: "missing_srp_username"}

class TLSLocalAlert(TLSAlert):
    """A TLS alert has been signalled by the local implementation.

    @type description: int
    @ivar description: Set to one of the constants in
    L{tlslite.constants.AlertDescription}

    @type level: int
    @ivar level: Set to one of the constants in
    L{tlslite.constants.AlertLevel}

    @type message: str
    @ivar message: Description of what went wrong.
    """
    def __init__(self, alert, message=None):
        self.description = alert.description
        self.level = alert.level
        self.message = message

    def __str__(self):
        alertStr = TLSAlert._descriptionStr.get(self.description)
        if alertStr == None:
            alertStr = str(self.description)
        if self.message:
            return alertStr + ": " + self.message
        else:
            return alertStr

class TLSRemoteAlert(TLSAlert):
    """A TLS alert has been signalled by the remote implementation.

    @type description: int
    @ivar description: Set to one of the constants in
    L{tlslite.constants.AlertDescription}

    @type level: int
    @ivar level: Set to one of the constants in
    L{tlslite.constants.AlertLevel}
    """
    def __init__(self, alert):
        self.description = alert.description
        self.level = alert.level

    def __str__(self):
        alertStr = TLSAlert._descriptionStr.get(self.description)
        if alertStr == None:
            alertStr = str(self.description)
        return alertStr

class TLSAuthenticationError(TLSError):
    """The handshake succeeded, but the other party's authentication
    was inadequate.

    This exception will only be raised when a
    L{tlslite.Checker.Checker} has been passed to a handshake function.
    The Checker will be invoked once the handshake completes, and if
    the Checker objects to how the other party authenticated, a
    subclass of this exception will be raised.
    """
    pass

class TLSNoAuthenticationError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    certificate chain, but this did not occur."""
    pass

class TLSAuthenticationTypeError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    different type of certificate chain."""
    pass

class TLSFingerprintError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    certificate chain that matches a different fingerprint."""
    pass

class TLSAuthorizationError(TLSAuthenticationError):
    """The Checker was expecting the other party to authenticate with a
    certificate chain that has a different authorization."""
    pass

class TLSValidationError(TLSAuthenticationError):
    """The Checker has determined that the other party's certificate
    chain is invalid."""
    pass

class TLSFaultError(TLSError):
    """The other party responded incorrectly to an induced fault.

    This exception will only occur during fault testing, when a
    TLSConnection's fault variable is set to induce some sort of
    faulty behavior, and the other party doesn't respond appropriately.
    """
    pass
