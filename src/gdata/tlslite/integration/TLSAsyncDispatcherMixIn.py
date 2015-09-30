"""TLS Lite + asyncore."""


import asyncore
from gdata.tlslite.TLSConnection import TLSConnection
from AsyncStateMachine import AsyncStateMachine


class TLSAsyncDispatcherMixIn(AsyncStateMachine):
    """This class can be "mixed in" with an
    L{asyncore.dispatcher} to add TLS support.

    This class essentially sits between the dispatcher and the select
    loop, intercepting events and only calling the dispatcher when
    applicable.

    In the case of handle_read(), a read operation will be activated,
    and when it completes, the bytes will be placed in a buffer where
    the dispatcher can retrieve them by calling recv(), and the
    dispatcher's handle_read() will be called.

    In the case of handle_write(), the dispatcher's handle_write() will
    be called, and when it calls send(), a write operation will be
    activated.

    To use this class, you must combine it with an asyncore.dispatcher,
    and pass in a handshake operation with setServerHandshakeOp().

    Below is an example of using this class with medusa.  This class is
    mixed in with http_channel to create http_tls_channel.  Note:
     1. the mix-in is listed first in the inheritance list

     2. the input buffer size must be at least 16K, otherwise the
       dispatcher might not read all the bytes from the TLS layer,
       leaving some bytes in limbo.

     3. IE seems to have a problem receiving a whole HTTP response in a
     single TLS record, so HTML pages containing '\\r\\n\\r\\n' won't
     be displayed on IE.

    Add the following text into 'start_medusa.py', in the 'HTTP Server'
    section::

        from tlslite.api import *
        s = open("./serverX509Cert.pem").read()
        x509 = X509()
        x509.parse(s)
        certChain = X509CertChain([x509])

        s = open("./serverX509Key.pem").read()
        privateKey = parsePEMKey(s, private=True)

        class http_tls_channel(TLSAsyncDispatcherMixIn,
                               http_server.http_channel):
            ac_in_buffer_size = 16384

            def __init__ (self, server, conn, addr):
                http_server.http_channel.__init__(self, server, conn, addr)
                TLSAsyncDispatcherMixIn.__init__(self, conn)
                self.tlsConnection.ignoreAbruptClose = True
                self.setServerHandshakeOp(certChain=certChain,
                                          privateKey=privateKey)

        hs.channel_class = http_tls_channel

    If the TLS layer raises an exception, the exception will be caught
    in asyncore.dispatcher, which will call close() on this class.  The
    TLS layer always closes the TLS connection before raising an
    exception, so the close operation will complete right away, causing
    asyncore.dispatcher.close() to be called, which closes the socket
    and removes this instance from the asyncore loop.

    """


    def __init__(self, sock=None):
        AsyncStateMachine.__init__(self)

        if sock:
            self.tlsConnection = TLSConnection(sock)

        #Calculate the sibling I'm being mixed in with.
        #This is necessary since we override functions
        #like readable(), handle_read(), etc., but we
        #also want to call the sibling's versions.
        for cl in self.__class__.__bases__:
            if cl != TLSAsyncDispatcherMixIn and cl != AsyncStateMachine:
                self.siblingClass = cl
                break
        else:
            raise AssertionError()

    def readable(self):
        result = self.wantsReadEvent()
        if result != None:
            return result
        return self.siblingClass.readable(self)

    def writable(self):
        result = self.wantsWriteEvent()
        if result != None:
            return result
        return self.siblingClass.writable(self)

    def handle_read(self):
        self.inReadEvent()

    def handle_write(self):
        self.inWriteEvent()

    def outConnectEvent(self):
        self.siblingClass.handle_connect(self)

    def outCloseEvent(self):
        asyncore.dispatcher.close(self)

    def outReadEvent(self, readBuffer):
        self.readBuffer = readBuffer
        self.siblingClass.handle_read(self)

    def outWriteEvent(self):
        self.siblingClass.handle_write(self)

    def recv(self, bufferSize=16384):
        if bufferSize < 16384 or self.readBuffer == None:
            raise AssertionError()
        returnValue = self.readBuffer
        self.readBuffer = None
        return returnValue

    def send(self, writeBuffer):
        self.setWriteOp(writeBuffer)
        return len(writeBuffer)

    def close(self):
        if hasattr(self, "tlsConnection"):
            self.setCloseOp()
        else:
            asyncore.dispatcher.close(self)
