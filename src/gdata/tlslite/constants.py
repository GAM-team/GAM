"""Constants used in various places."""

class CertificateType:
    x509 = 0
    openpgp = 1
    cryptoID = 2

class HandshakeType:
    hello_request = 0
    client_hello = 1
    server_hello = 2
    certificate = 11
    server_key_exchange = 12
    certificate_request = 13
    server_hello_done = 14
    certificate_verify = 15
    client_key_exchange = 16
    finished = 20

class ContentType:
    change_cipher_spec = 20
    alert = 21
    handshake = 22
    application_data = 23
    all = (20,21,22,23)

class AlertLevel:
    warning = 1
    fatal = 2

class AlertDescription:
    """
    @cvar bad_record_mac: A TLS record failed to decrypt properly.

    If this occurs during a shared-key or SRP handshake it most likely
    indicates a bad password.  It may also indicate an implementation
    error, or some tampering with the data in transit.

    This alert will be signalled by the server if the SRP password is bad.  It
    may also be signalled by the server if the SRP username is unknown to the
    server, but it doesn't wish to reveal that fact.

    This alert will be signalled by the client if the shared-key username is
    bad.

    @cvar handshake_failure: A problem occurred while handshaking.

    This typically indicates a lack of common ciphersuites between client and
    server, or some other disagreement (about SRP parameters or key sizes,
    for example).

    @cvar protocol_version: The other party's SSL/TLS version was unacceptable.

    This indicates that the client and server couldn't agree on which version
    of SSL or TLS to use.

    @cvar user_canceled: The handshake is being cancelled for some reason.

    """

    close_notify = 0
    unexpected_message = 10
    bad_record_mac = 20
    decryption_failed = 21
    record_overflow = 22
    decompression_failure = 30
    handshake_failure = 40
    no_certificate = 41 #SSLv3
    bad_certificate = 42
    unsupported_certificate = 43
    certificate_revoked = 44
    certificate_expired = 45
    certificate_unknown = 46
    illegal_parameter = 47
    unknown_ca = 48
    access_denied = 49
    decode_error = 50
    decrypt_error = 51
    export_restriction = 60
    protocol_version = 70
    insufficient_security = 71
    internal_error = 80
    user_canceled = 90
    no_renegotiation = 100
    unknown_srp_username = 120
    missing_srp_username = 121
    untrusted_srp_parameters = 122

class CipherSuite:
    TLS_SRP_SHA_WITH_3DES_EDE_CBC_SHA  = 0x0050
    TLS_SRP_SHA_WITH_AES_128_CBC_SHA = 0x0053
    TLS_SRP_SHA_WITH_AES_256_CBC_SHA = 0x0056

    TLS_SRP_SHA_RSA_WITH_3DES_EDE_CBC_SHA = 0x0051
    TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA = 0x0054
    TLS_SRP_SHA_RSA_WITH_AES_256_CBC_SHA = 0x0057

    TLS_RSA_WITH_3DES_EDE_CBC_SHA = 0x000A
    TLS_RSA_WITH_AES_128_CBC_SHA = 0x002F
    TLS_RSA_WITH_AES_256_CBC_SHA = 0x0035
    TLS_RSA_WITH_RC4_128_SHA = 0x0005

    srpSuites = []
    srpSuites.append(TLS_SRP_SHA_WITH_3DES_EDE_CBC_SHA)
    srpSuites.append(TLS_SRP_SHA_WITH_AES_128_CBC_SHA)
    srpSuites.append(TLS_SRP_SHA_WITH_AES_256_CBC_SHA)
    def getSrpSuites(ciphers):
        suites = []
        for cipher in ciphers:
            if cipher == "aes128":
                suites.append(CipherSuite.TLS_SRP_SHA_WITH_AES_128_CBC_SHA)
            elif cipher == "aes256":
                suites.append(CipherSuite.TLS_SRP_SHA_WITH_AES_256_CBC_SHA)
            elif cipher == "3des":
                suites.append(CipherSuite.TLS_SRP_SHA_WITH_3DES_EDE_CBC_SHA)
        return suites
    getSrpSuites = staticmethod(getSrpSuites)

    srpRsaSuites = []
    srpRsaSuites.append(TLS_SRP_SHA_RSA_WITH_3DES_EDE_CBC_SHA)
    srpRsaSuites.append(TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA)
    srpRsaSuites.append(TLS_SRP_SHA_RSA_WITH_AES_256_CBC_SHA)
    def getSrpRsaSuites(ciphers):
        suites = []
        for cipher in ciphers:
            if cipher == "aes128":
                suites.append(CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA)
            elif cipher == "aes256":
                suites.append(CipherSuite.TLS_SRP_SHA_RSA_WITH_AES_256_CBC_SHA)
            elif cipher == "3des":
                suites.append(CipherSuite.TLS_SRP_SHA_RSA_WITH_3DES_EDE_CBC_SHA)
        return suites
    getSrpRsaSuites = staticmethod(getSrpRsaSuites)

    rsaSuites = []
    rsaSuites.append(TLS_RSA_WITH_3DES_EDE_CBC_SHA)
    rsaSuites.append(TLS_RSA_WITH_AES_128_CBC_SHA)
    rsaSuites.append(TLS_RSA_WITH_AES_256_CBC_SHA)
    rsaSuites.append(TLS_RSA_WITH_RC4_128_SHA)
    def getRsaSuites(ciphers):
        suites = []
        for cipher in ciphers:
            if cipher == "aes128":
                suites.append(CipherSuite.TLS_RSA_WITH_AES_128_CBC_SHA)
            elif cipher == "aes256":
                suites.append(CipherSuite.TLS_RSA_WITH_AES_256_CBC_SHA)
            elif cipher == "rc4":
                suites.append(CipherSuite.TLS_RSA_WITH_RC4_128_SHA)
            elif cipher == "3des":
                suites.append(CipherSuite.TLS_RSA_WITH_3DES_EDE_CBC_SHA)
        return suites
    getRsaSuites = staticmethod(getRsaSuites)

    tripleDESSuites = []
    tripleDESSuites.append(TLS_SRP_SHA_WITH_3DES_EDE_CBC_SHA)
    tripleDESSuites.append(TLS_SRP_SHA_RSA_WITH_3DES_EDE_CBC_SHA)
    tripleDESSuites.append(TLS_RSA_WITH_3DES_EDE_CBC_SHA)

    aes128Suites = []
    aes128Suites.append(TLS_SRP_SHA_WITH_AES_128_CBC_SHA)
    aes128Suites.append(TLS_SRP_SHA_RSA_WITH_AES_128_CBC_SHA)
    aes128Suites.append(TLS_RSA_WITH_AES_128_CBC_SHA)

    aes256Suites = []
    aes256Suites.append(TLS_SRP_SHA_WITH_AES_256_CBC_SHA)
    aes256Suites.append(TLS_SRP_SHA_RSA_WITH_AES_256_CBC_SHA)
    aes256Suites.append(TLS_RSA_WITH_AES_256_CBC_SHA)

    rc4Suites = []
    rc4Suites.append(TLS_RSA_WITH_RC4_128_SHA)


class Fault:
    badUsername = 101
    badPassword = 102
    badA = 103
    clientSrpFaults = range(101,104)

    badVerifyMessage = 601
    clientCertFaults = range(601,602)

    badPremasterPadding = 501
    shortPremasterSecret = 502
    clientNoAuthFaults = range(501,503)

    badIdentifier = 401
    badSharedKey = 402
    clientSharedKeyFaults = range(401,403)

    badB = 201
    serverFaults = range(201,202)

    badFinished = 300
    badMAC = 301
    badPadding = 302
    genericFaults = range(300,303)

    faultAlerts = {\
        badUsername: (AlertDescription.unknown_srp_username, \
                      AlertDescription.bad_record_mac),\
        badPassword: (AlertDescription.bad_record_mac,),\
        badA: (AlertDescription.illegal_parameter,),\
        badIdentifier: (AlertDescription.handshake_failure,),\
        badSharedKey: (AlertDescription.bad_record_mac,),\
        badPremasterPadding: (AlertDescription.bad_record_mac,),\
        shortPremasterSecret: (AlertDescription.bad_record_mac,),\
        badVerifyMessage: (AlertDescription.decrypt_error,),\
        badFinished: (AlertDescription.decrypt_error,),\
        badMAC: (AlertDescription.bad_record_mac,),\
        badPadding: (AlertDescription.bad_record_mac,)
        }

    faultNames = {\
        badUsername: "bad username",\
        badPassword: "bad password",\
        badA: "bad A",\
        badIdentifier: "bad identifier",\
        badSharedKey: "bad sharedkey",\
        badPremasterPadding: "bad premaster padding",\
        shortPremasterSecret: "short premaster secret",\
        badVerifyMessage: "bad verify message",\
        badFinished: "bad finished message",\
        badMAC: "bad MAC",\
        badPadding: "bad padding"
        }
