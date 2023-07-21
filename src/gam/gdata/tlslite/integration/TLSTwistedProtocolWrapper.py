"""TLS Lite + Twisted."""

from twisted.protocols.policies import ProtocolWrapper, WrappingFactory
from twisted.python.failure import Failure

from AsyncStateMachine import AsyncStateMachine
from gdata.tlslite.TLSConnection import TLSConnection
from gdata.tlslite.errors import *

import socket
import errno


#The TLSConnection is created around a "fake socket" that
#plugs it into the underlying Twisted transport
class _FakeSocket:
    def __init__(self, wrapper):
        self.wrapper = wrapper
        self.data = ""

    def send(self, data):
        ProtocolWrapper.write(self.wrapper, data)
        return len(data)

    def recv(self, numBytes):
        if self.data == "":
            raise socket.error, (errno.EWOULDBLOCK, "")
        returnData = self.data[:numBytes]
        self.data = self.data[numBytes:]
        return returnData

class TLSTwistedProtocolWrapper(ProtocolWrapper, AsyncStateMachine):
    """This class can wrap Twisted protocols to add TLS support.

    Below is a complete example of using TLS Lite with a Twisted echo
    server.

    There are two server implementations below.  Echo is the original
    protocol, which is oblivious to TLS.  Echo1 subclasses Echo and
    negotiates TLS when the client connects.  Echo2 subclasses Echo and
    negotiates TLS when the client sends "STARTTLS"::

        from twisted.internet.protocol import Protocol, Factory
        from twisted.internet import reactor
        from twisted.protocols.policies import WrappingFactory
        from twisted.protocols.basic import LineReceiver
        from twisted.python import log
        from twisted.python.failure import Failure
        import sys
        from tlslite.api import *

        s = open("./serverX509Cert.pem").read()
        x509 = X509()
        x509.parse(s)
        certChain = X509CertChain([x509])

        s = open("./serverX509Key.pem").read()
        privateKey = parsePEMKey(s, private=True)

        verifierDB = VerifierDB("verifierDB")
        verifierDB.open()

        class Echo(LineReceiver):
            def connectionMade(self):
                self.transport.write("Welcome to the echo server!\\r\\n")

            def lineReceived(self, line):
                self.transport.write(line + "\\r\\n")

        class Echo1(Echo):
            def connectionMade(self):
                if not self.transport.tlsStarted:
                    self.transport.setServerHandshakeOp(certChain=certChain,
                                                        privateKey=privateKey,
                                                        verifierDB=verifierDB)
                else:
                    Echo.connectionMade(self)

            def connectionLost(self, reason):
                pass #Handle any TLS exceptions here

        class Echo2(Echo):
            def lineReceived(self, data):
                if data == "STARTTLS":
                    self.transport.setServerHandshakeOp(certChain=certChain,
                                                        privateKey=privateKey,
                                                        verifierDB=verifierDB)
                else:
                    Echo.lineReceived(self, data)

            def connectionLost(self, reason):
                pass #Handle any TLS exceptions here

        factory = Factory()
        factory.protocol = Echo1
        #factory.protocol = Echo2

        wrappingFactory = WrappingFactory(factory)
        wrappingFactory.protocol = TLSTwistedProtocolWrapper

        log.startLogging(sys.stdout)
        reactor.listenTCP(1079, wrappingFactory)
        reactor.run()

    This class works as follows:

    Data comes in and is given to the AsyncStateMachine for handling.
    AsyncStateMachine will forward events to this class, and we'll
    pass them on to the ProtocolHandler, which will proxy them to the
    wrapped protocol.  The wrapped protocol may then call back into
    this class, and these calls will be proxied into the
    AsyncStateMachine.

    The call graph looks like this:
     - self.dataReceived
       - AsyncStateMachine.inReadEvent
         - self.out(Connect|Close|Read)Event
           - ProtocolWrapper.(connectionMade|loseConnection|dataReceived)
             - self.(loseConnection|write|writeSequence)
               - AsyncStateMachine.(setCloseOp|setWriteOp)
    """

    #WARNING: IF YOU COPY-AND-PASTE THE ABOVE CODE, BE SURE TO REMOVE
    #THE EXTRA ESCAPING AROUND "\\r\\n"

    def __init__(self, factory, wrappedProtocol):
        ProtocolWrapper.__init__(self, factory, wrappedProtocol)
        AsyncStateMachine.__init__(self)
        self.fakeSocket = _FakeSocket(self)
        self.tlsConnection = TLSConnection(self.fakeSocket)
        self.tlsStarted = False
        self.connectionLostCalled = False

    def connectionMade(self):
        try:
            ProtocolWrapper.connectionMade(self)
        except TLSError, e:
            self.connectionLost(Failure(e))
            ProtocolWrapper.loseConnection(self)

    def dataReceived(self, data):
        try:
            if not self.tlsStarted:
                ProtocolWrapper.dataReceived(self, data)
            else:
                self.fakeSocket.data += data
                while self.fakeSocket.data:
                    AsyncStateMachine.inReadEvent(self)
        except TLSError, e:
            self.connectionLost(Failure(e))
            ProtocolWrapper.loseConnection(self)

    def connectionLost(self, reason):
        if not self.connectionLostCalled:
            ProtocolWrapper.connectionLost(self, reason)
            self.connectionLostCalled = True


    def outConnectEvent(self):
        ProtocolWrapper.connectionMade(self)

    def outCloseEvent(self):
        ProtocolWrapper.loseConnection(self)

    def outReadEvent(self, data):
        if data == "":
            ProtocolWrapper.loseConnection(self)
        else:
            ProtocolWrapper.dataReceived(self, data)


    def setServerHandshakeOp(self, **args):
        self.tlsStarted = True
        AsyncStateMachine.setServerHandshakeOp(self, **args)

    def loseConnection(self):
        if not self.tlsStarted:
            ProtocolWrapper.loseConnection(self)
        else:
            AsyncStateMachine.setCloseOp(self)

    def write(self, data):
        if not self.tlsStarted:
            ProtocolWrapper.write(self, data)
        else:
            #Because of the FakeSocket, write operations are guaranteed to
            #terminate immediately.
            AsyncStateMachine.setWriteOp(self, data)

    def writeSequence(self, seq):
        if not self.tlsStarted:
            ProtocolWrapper.writeSequence(self, seq)
        else:
            #Because of the FakeSocket, write operations are guaranteed to
            #terminate immediately.
            AsyncStateMachine.setWriteOp(self, "".join(seq))
