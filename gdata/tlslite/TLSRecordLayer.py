"""Helper class for TLSConnection."""
from __future__ import generators

from utils.compat import *
from utils.cryptomath import *
from utils.cipherfactory import createAES, createRC4, createTripleDES
from utils.codec import *
from errors import *
from messages import *
from mathtls import *
from constants import *
from utils.cryptomath import getRandomBytes
from utils import hmac
from FileObject import FileObject
import sha
import md5
import socket
import errno
import traceback

class _ConnectionState:
    def __init__(self):
        self.macContext = None
        self.encContext = None
        self.seqnum = 0

    def getSeqNumStr(self):
        w = Writer(8)
        w.add(self.seqnum, 8)
        seqnumStr = bytesToString(w.bytes)
        self.seqnum += 1
        return seqnumStr


class TLSRecordLayer:
    """
    This class handles data transmission for a TLS connection.

    Its only subclass is L{tlslite.TLSConnection.TLSConnection}.  We've
    separated the code in this class from TLSConnection to make things
    more readable.


    @type sock: socket.socket
    @ivar sock: The underlying socket object.

    @type session: L{tlslite.Session.Session}
    @ivar session: The session corresponding to this connection.

    Due to TLS session resumption, multiple connections can correspond
    to the same underlying session.

    @type version: tuple
    @ivar version: The TLS version being used for this connection.

    (3,0) means SSL 3.0, and (3,1) means TLS 1.0.

    @type closed: bool
    @ivar closed: If this connection is closed.

    @type resumed: bool
    @ivar resumed: If this connection is based on a resumed session.

    @type allegedSharedKeyUsername: str or None
    @ivar allegedSharedKeyUsername:  This is set to the shared-key
    username asserted by the client, whether the handshake succeeded or
    not.  If the handshake fails, this can be inspected to
    determine if a guessing attack is in progress against a particular
    user account.

    @type allegedSrpUsername: str or None
    @ivar allegedSrpUsername:  This is set to the SRP username
    asserted by the client, whether the handshake succeeded or not.
    If the handshake fails, this can be inspected to determine
    if a guessing attack is in progress against a particular user
    account.

    @type closeSocket: bool
    @ivar closeSocket: If the socket should be closed when the
    connection is closed (writable).

    If you set this to True, TLS Lite will assume the responsibility of
    closing the socket when the TLS Connection is shutdown (either
    through an error or through the user calling close()).  The default
    is False.

    @type ignoreAbruptClose: bool
    @ivar ignoreAbruptClose: If an abrupt close of the socket should
    raise an error (writable).

    If you set this to True, TLS Lite will not raise a
    L{tlslite.errors.TLSAbruptCloseError} exception if the underlying
    socket is unexpectedly closed.  Such an unexpected closure could be
    caused by an attacker.  However, it also occurs with some incorrect
    TLS implementations.

    You should set this to True only if you're not worried about an
    attacker truncating the connection, and only if necessary to avoid
    spurious errors.  The default is False.

    @sort: __init__, read, readAsync, write, writeAsync, close, closeAsync,
    getCipherImplementation, getCipherName
    """

    def __init__(self, sock):
        self.sock = sock

        #My session object (Session instance; read-only)
        self.session = None

        #Am I a client or server?
        self._client = None

        #Buffers for processing messages
        self._handshakeBuffer = []
        self._readBuffer = ""

        #Handshake digests
        self._handshake_md5 = md5.md5()
        self._handshake_sha = sha.sha()

        #TLS Protocol Version
        self.version = (0,0) #read-only
        self._versionCheck = False #Once we choose a version, this is True

        #Current and Pending connection states
        self._writeState = _ConnectionState()
        self._readState = _ConnectionState()
        self._pendingWriteState = _ConnectionState()
        self._pendingReadState = _ConnectionState()

        #Is the connection open?
        self.closed = True #read-only
        self._refCount = 0 #Used to trigger closure

        #Is this a resumed (or shared-key) session?
        self.resumed = False #read-only

        #What username did the client claim in his handshake?
        self.allegedSharedKeyUsername = None
        self.allegedSrpUsername = None

        #On a call to close(), do we close the socket? (writeable)
        self.closeSocket = False

        #If the socket is abruptly closed, do we ignore it
        #and pretend the connection was shut down properly? (writeable)
        self.ignoreAbruptClose = False

        #Fault we will induce, for testing purposes
        self.fault = None

    #*********************************************************
    # Public Functions START
    #*********************************************************

    def read(self, max=None, min=1):
        """Read some data from the TLS connection.

        This function will block until at least 'min' bytes are
        available (or the connection is closed).

        If an exception is raised, the connection will have been
        automatically closed.

        @type max: int
        @param max: The maximum number of bytes to return.

        @type min: int
        @param min: The minimum number of bytes to return

        @rtype: str
        @return: A string of no more than 'max' bytes, and no fewer
        than 'min' (unless the connection has been closed, in which
        case fewer than 'min' bytes may be returned).

        @raise socket.error: If a socket error occurs.
        @raise tlslite.errors.TLSAbruptCloseError: If the socket is closed
        without a preceding alert.
        @raise tlslite.errors.TLSAlert: If a TLS alert is signalled.
        """
        for result in self.readAsync(max, min):
            pass
        return result

    def readAsync(self, max=None, min=1):
        """Start a read operation on the TLS connection.

        This function returns a generator which behaves similarly to
        read().  Successive invocations of the generator will return 0
        if it is waiting to read from the socket, 1 if it is waiting
        to write to the socket, or a string if the read operation has
        completed.

        @rtype: iterable
        @return: A generator; see above for details.
        """
        try:
            while len(self._readBuffer)<min and not self.closed:
                try:
                    for result in self._getMsg(ContentType.application_data):
                        if result in (0,1):
                            yield result
                    applicationData = result
                    self._readBuffer += bytesToString(applicationData.write())
                except TLSRemoteAlert, alert:
                    if alert.description != AlertDescription.close_notify:
                        raise
                except TLSAbruptCloseError:
                    if not self.ignoreAbruptClose:
                        raise
                    else:
                        self._shutdown(True)

            if max == None:
                max = len(self._readBuffer)

            returnStr = self._readBuffer[:max]
            self._readBuffer = self._readBuffer[max:]
            yield returnStr
        except:
            self._shutdown(False)
            raise

    def write(self, s):
        """Write some data to the TLS connection.

        This function will block until all the data has been sent.

        If an exception is raised, the connection will have been
        automatically closed.

        @type s: str
        @param s: The data to transmit to the other party.

        @raise socket.error: If a socket error occurs.
        """
        for result in self.writeAsync(s):
            pass

    def writeAsync(self, s):
        """Start a write operation on the TLS connection.

        This function returns a generator which behaves similarly to
        write().  Successive invocations of the generator will return
        1 if it is waiting to write to the socket, or will raise
        StopIteration if the write operation has completed.

        @rtype: iterable
        @return: A generator; see above for details.
        """
        try:
            if self.closed:
                raise ValueError()

            index = 0
            blockSize = 16384
            skipEmptyFrag = False
            while 1:
                startIndex = index * blockSize
                endIndex = startIndex + blockSize
                if startIndex >= len(s):
                    break
                if endIndex > len(s):
                    endIndex = len(s)
                block = stringToBytes(s[startIndex : endIndex])
                applicationData = ApplicationData().create(block)
                for result in self._sendMsg(applicationData, skipEmptyFrag):
                    yield result
                skipEmptyFrag = True #only send an empy fragment on 1st message
                index += 1
        except:
            self._shutdown(False)
            raise

    def close(self):
        """Close the TLS connection.

        This function will block until it has exchanged close_notify
        alerts with the other party.  After doing so, it will shut down the
        TLS connection.  Further attempts to read through this connection
        will return "".  Further attempts to write through this connection
        will raise ValueError.

        If makefile() has been called on this connection, the connection
        will be not be closed until the connection object and all file
        objects have been closed.

        Even if an exception is raised, the connection will have been
        closed.

        @raise socket.error: If a socket error occurs.
        @raise tlslite.errors.TLSAbruptCloseError: If the socket is closed
        without a preceding alert.
        @raise tlslite.errors.TLSAlert: If a TLS alert is signalled.
        """
        if not self.closed:
            for result in self._decrefAsync():
                pass

    def closeAsync(self):
        """Start a close operation on the TLS connection.

        This function returns a generator which behaves similarly to
        close().  Successive invocations of the generator will return 0
        if it is waiting to read from the socket, 1 if it is waiting
        to write to the socket, or will raise StopIteration if the
        close operation has completed.

        @rtype: iterable
        @return: A generator; see above for details.
        """
        if not self.closed:
            for result in self._decrefAsync():
                yield result

    def _decrefAsync(self):
        self._refCount -= 1
        if self._refCount == 0 and not self.closed:
            try:
                for result in self._sendMsg(Alert().create(\
                        AlertDescription.close_notify, AlertLevel.warning)):
                    yield result
                alert = None
                while not alert:
                    for result in self._getMsg((ContentType.alert, \
                                              ContentType.application_data)):
                        if result in (0,1):
                            yield result
                    if result.contentType == ContentType.alert:
                        alert = result
                if alert.description == AlertDescription.close_notify:
                    self._shutdown(True)
                else:
                    raise TLSRemoteAlert(alert)
            except (socket.error, TLSAbruptCloseError):
                #If the other side closes the socket, that's okay
                self._shutdown(True)
            except:
                self._shutdown(False)
                raise

    def getCipherName(self):
        """Get the name of the cipher used with this connection.

        @rtype: str
        @return: The name of the cipher used with this connection.
        Either 'aes128', 'aes256', 'rc4', or '3des'.
        """
        if not self._writeState.encContext:
            return None
        return self._writeState.encContext.name

    def getCipherImplementation(self):
        """Get the name of the cipher implementation used with
        this connection.

        @rtype: str
        @return: The name of the cipher implementation used with
        this connection.  Either 'python', 'cryptlib', 'openssl',
        or 'pycrypto'.
        """
        if not self._writeState.encContext:
            return None
        return self._writeState.encContext.implementation



    #Emulate a socket, somewhat -
    def send(self, s):
        """Send data to the TLS connection (socket emulation).

        @raise socket.error: If a socket error occurs.
        """
        self.write(s)
        return len(s)

    def sendall(self, s):
        """Send data to the TLS connection (socket emulation).

        @raise socket.error: If a socket error occurs.
        """
        self.write(s)

    def recv(self, bufsize):
        """Get some data from the TLS connection (socket emulation).

        @raise socket.error: If a socket error occurs.
        @raise tlslite.errors.TLSAbruptCloseError: If the socket is closed
        without a preceding alert.
        @raise tlslite.errors.TLSAlert: If a TLS alert is signalled.
        """
        return self.read(bufsize)

    def makefile(self, mode='r', bufsize=-1):
        """Create a file object for the TLS connection (socket emulation).

        @rtype: L{tlslite.FileObject.FileObject}
        """
        self._refCount += 1
        return FileObject(self, mode, bufsize)

    def getsockname(self):
        """Return the socket's own address (socket emulation)."""
        return self.sock.getsockname()

    def getpeername(self):
        """Return the remote address to which the socket is connected
        (socket emulation)."""
        return self.sock.getpeername()

    def settimeout(self, value):
        """Set a timeout on blocking socket operations (socket emulation)."""
        return self.sock.settimeout(value)

    def gettimeout(self):
        """Return the timeout associated with socket operations (socket
        emulation)."""
        return self.sock.gettimeout()

    def setsockopt(self, level, optname, value):
        """Set the value of the given socket option (socket emulation)."""
        return self.sock.setsockopt(level, optname, value)


     #*********************************************************
     # Public Functions END
     #*********************************************************

    def _shutdown(self, resumable):
        self._writeState = _ConnectionState()
        self._readState = _ConnectionState()
        #Don't do this: self._readBuffer = ""
        self.version = (0,0)
        self._versionCheck = False
        self.closed = True
        if self.closeSocket:
            self.sock.close()

        #Even if resumable is False, we'll never toggle this on
        if not resumable and self.session:
            self.session.resumable = False


    def _sendError(self, alertDescription, errorStr=None):
        alert = Alert().create(alertDescription, AlertLevel.fatal)
        for result in self._sendMsg(alert):
            yield result
        self._shutdown(False)
        raise TLSLocalAlert(alert, errorStr)

    def _sendMsgs(self, msgs):
        skipEmptyFrag = False
        for msg in msgs:
            for result in self._sendMsg(msg, skipEmptyFrag):
                yield result
            skipEmptyFrag = True

    def _sendMsg(self, msg, skipEmptyFrag=False):
        bytes = msg.write()
        contentType = msg.contentType

        #Whenever we're connected and asked to send a message,
        #we first send an empty Application Data message.  This prevents
        #an attacker from launching a chosen-plaintext attack based on
        #knowing the next IV.
        if not self.closed and not skipEmptyFrag and self.version == (3,1):
            if self._writeState.encContext:
                if self._writeState.encContext.isBlockCipher:
                    for result in self._sendMsg(ApplicationData(),
                                               skipEmptyFrag=True):
                        yield result

        #Update handshake hashes
        if contentType == ContentType.handshake:
            bytesStr = bytesToString(bytes)
            self._handshake_md5.update(bytesStr)
            self._handshake_sha.update(bytesStr)

        #Calculate MAC
        if self._writeState.macContext:
            seqnumStr = self._writeState.getSeqNumStr()
            bytesStr = bytesToString(bytes)
            mac = self._writeState.macContext.copy()
            mac.update(seqnumStr)
            mac.update(chr(contentType))
            if self.version == (3,0):
                mac.update( chr( int(len(bytes)/256) ) )
                mac.update( chr( int(len(bytes)%256) ) )
            elif self.version in ((3,1), (3,2)):
                mac.update(chr(self.version[0]))
                mac.update(chr(self.version[1]))
                mac.update( chr( int(len(bytes)/256) ) )
                mac.update( chr( int(len(bytes)%256) ) )
            else:
                raise AssertionError()
            mac.update(bytesStr)
            macString = mac.digest()
            macBytes = stringToBytes(macString)
            if self.fault == Fault.badMAC:
                macBytes[0] = (macBytes[0]+1) % 256

        #Encrypt for Block or Stream Cipher
        if self._writeState.encContext:
            #Add padding and encrypt (for Block Cipher):
            if self._writeState.encContext.isBlockCipher:

                #Add TLS 1.1 fixed block
                if self.version == (3,2):
                    bytes = self.fixedIVBlock + bytes

                #Add padding: bytes = bytes + (macBytes + paddingBytes)
                currentLength = len(bytes) + len(macBytes) + 1
                blockLength = self._writeState.encContext.block_size
                paddingLength = blockLength-(currentLength % blockLength)

                paddingBytes = createByteArraySequence([paddingLength] * \
                                                       (paddingLength+1))
                if self.fault == Fault.badPadding:
                    paddingBytes[0] = (paddingBytes[0]+1) % 256
                endBytes = concatArrays(macBytes, paddingBytes)
                bytes = concatArrays(bytes, endBytes)
                #Encrypt
                plaintext = stringToBytes(bytes)
                ciphertext = self._writeState.encContext.encrypt(plaintext)
                bytes = stringToBytes(ciphertext)

            #Encrypt (for Stream Cipher)
            else:
                bytes = concatArrays(bytes, macBytes)
                plaintext = bytesToString(bytes)
                ciphertext = self._writeState.encContext.encrypt(plaintext)
                bytes = stringToBytes(ciphertext)

        #Add record header and send
        r = RecordHeader3().create(self.version, contentType, len(bytes))
        s = bytesToString(concatArrays(r.write(), bytes))
        while 1:
            try:
                bytesSent = self.sock.send(s) #Might raise socket.error
            except socket.error, why:
                if why[0] == errno.EWOULDBLOCK:
                    yield 1
                    continue
                else:
                    raise
            if bytesSent == len(s):
                return
            s = s[bytesSent:]
            yield 1


    def _getMsg(self, expectedType, secondaryType=None, constructorType=None):
        try:
            if not isinstance(expectedType, tuple):
                expectedType = (expectedType,)

            #Spin in a loop, until we've got a non-empty record of a type we
            #expect.  The loop will be repeated if:
            #  - we receive a renegotiation attempt; we send no_renegotiation,
            #    then try again
            #  - we receive an empty application-data fragment; we try again
            while 1:
                for result in self._getNextRecord():
                    if result in (0,1):
                        yield result
                recordHeader, p = result

                #If this is an empty application-data fragment, try again
                if recordHeader.type == ContentType.application_data:
                    if p.index == len(p.bytes):
                        continue

                #If we received an unexpected record type...
                if recordHeader.type not in expectedType:

                    #If we received an alert...
                    if recordHeader.type == ContentType.alert:
                        alert = Alert().parse(p)

                        #We either received a fatal error, a warning, or a
                        #close_notify.  In any case, we're going to close the
                        #connection.  In the latter two cases we respond with
                        #a close_notify, but ignore any socket errors, since
                        #the other side might have already closed the socket.
                        if alert.level == AlertLevel.warning or \
                           alert.description == AlertDescription.close_notify:

                            #If the sendMsg() call fails because the socket has
                            #already been closed, we will be forgiving and not
                            #report the error nor invalidate the "resumability"
                            #of the session.
                            try:
                                alertMsg = Alert()
                                alertMsg.create(AlertDescription.close_notify,
                                                AlertLevel.warning)
                                for result in self._sendMsg(alertMsg):
                                    yield result
                            except socket.error:
                                pass

                            if alert.description == \
                                   AlertDescription.close_notify:
                                self._shutdown(True)
                            elif alert.level == AlertLevel.warning:
                                self._shutdown(False)

                        else: #Fatal alert:
                            self._shutdown(False)

                        #Raise the alert as an exception
                        raise TLSRemoteAlert(alert)

                    #If we received a renegotiation attempt...
                    if recordHeader.type == ContentType.handshake:
                        subType = p.get(1)
                        reneg = False
                        if self._client:
                            if subType == HandshakeType.hello_request:
                                reneg = True
                        else:
                            if subType == HandshakeType.client_hello:
                                reneg = True
                        #Send no_renegotiation, then try again
                        if reneg:
                            alertMsg = Alert()
                            alertMsg.create(AlertDescription.no_renegotiation,
                                            AlertLevel.warning)
                            for result in self._sendMsg(alertMsg):
                                yield result
                            continue

                    #Otherwise: this is an unexpected record, but neither an
                    #alert nor renegotiation
                    for result in self._sendError(\
                            AlertDescription.unexpected_message,
                            "received type=%d" % recordHeader.type):
                        yield result

                break

            #Parse based on content_type
            if recordHeader.type == ContentType.change_cipher_spec:
                yield ChangeCipherSpec().parse(p)
            elif recordHeader.type == ContentType.alert:
                yield Alert().parse(p)
            elif recordHeader.type == ContentType.application_data:
                yield ApplicationData().parse(p)
            elif recordHeader.type == ContentType.handshake:
                #Convert secondaryType to tuple, if it isn't already
                if not isinstance(secondaryType, tuple):
                    secondaryType = (secondaryType,)

                #If it's a handshake message, check handshake header
                if recordHeader.ssl2:
                    subType = p.get(1)
                    if subType != HandshakeType.client_hello:
                        for result in self._sendError(\
                                AlertDescription.unexpected_message,
                                "Can only handle SSLv2 ClientHello messages"):
                            yield result
                    if HandshakeType.client_hello not in secondaryType:
                        for result in self._sendError(\
                                AlertDescription.unexpected_message):
                            yield result
                    subType = HandshakeType.client_hello
                else:
                    subType = p.get(1)
                    if subType not in secondaryType:
                        for result in self._sendError(\
                                AlertDescription.unexpected_message,
                                "Expecting %s, got %s" % (str(secondaryType), subType)):
                            yield result

                #Update handshake hashes
                sToHash = bytesToString(p.bytes)
                self._handshake_md5.update(sToHash)
                self._handshake_sha.update(sToHash)

                #Parse based on handshake type
                if subType == HandshakeType.client_hello:
                    yield ClientHello(recordHeader.ssl2).parse(p)
                elif subType == HandshakeType.server_hello:
                    yield ServerHello().parse(p)
                elif subType == HandshakeType.certificate:
                    yield Certificate(constructorType).parse(p)
                elif subType == HandshakeType.certificate_request:
                    yield CertificateRequest().parse(p)
                elif subType == HandshakeType.certificate_verify:
                    yield CertificateVerify().parse(p)
                elif subType == HandshakeType.server_key_exchange:
                    yield ServerKeyExchange(constructorType).parse(p)
                elif subType == HandshakeType.server_hello_done:
                    yield ServerHelloDone().parse(p)
                elif subType == HandshakeType.client_key_exchange:
                    yield ClientKeyExchange(constructorType, \
                                            self.version).parse(p)
                elif subType == HandshakeType.finished:
                    yield Finished(self.version).parse(p)
                else:
                    raise AssertionError()

        #If an exception was raised by a Parser or Message instance:
        except SyntaxError, e:
            for result in self._sendError(AlertDescription.decode_error,
                                         formatExceptionTrace(e)):
                yield result


    #Returns next record or next handshake message
    def _getNextRecord(self):

        #If there's a handshake message waiting, return it
        if self._handshakeBuffer:
            recordHeader, bytes = self._handshakeBuffer[0]
            self._handshakeBuffer = self._handshakeBuffer[1:]
            yield (recordHeader, Parser(bytes))
            return

        #Otherwise...
        #Read the next record header
        bytes = createByteArraySequence([])
        recordHeaderLength = 1
        ssl2 = False
        while 1:
            try:
                s = self.sock.recv(recordHeaderLength-len(bytes))
            except socket.error, why:
                if why[0] == errno.EWOULDBLOCK:
                    yield 0
                    continue
                else:
                    raise

            #If the connection was abruptly closed, raise an error
            if len(s)==0:
                raise TLSAbruptCloseError()

            bytes += stringToBytes(s)
            if len(bytes)==1:
                if bytes[0] in ContentType.all:
                    ssl2 = False
                    recordHeaderLength = 5
                elif bytes[0] == 128:
                    ssl2 = True
                    recordHeaderLength = 2
                else:
                    raise SyntaxError()
            if len(bytes) == recordHeaderLength:
                break

        #Parse the record header
        if ssl2:
            r = RecordHeader2().parse(Parser(bytes))
        else:
            r = RecordHeader3().parse(Parser(bytes))

        #Check the record header fields
        if r.length > 18432:
            for result in self._sendError(AlertDescription.record_overflow):
                yield result

        #Read the record contents
        bytes = createByteArraySequence([])
        while 1:
            try:
                s = self.sock.recv(r.length - len(bytes))
            except socket.error, why:
                if why[0] == errno.EWOULDBLOCK:
                    yield 0
                    continue
                else:
                    raise

            #If the connection is closed, raise a socket error
            if len(s)==0:
                    raise TLSAbruptCloseError()

            bytes += stringToBytes(s)
            if len(bytes) == r.length:
                break

        #Check the record header fields (2)
        #We do this after reading the contents from the socket, so that
        #if there's an error, we at least don't leave extra bytes in the
        #socket..
        #
        # THIS CHECK HAS NO SECURITY RELEVANCE (?), BUT COULD HURT INTEROP.
        # SO WE LEAVE IT OUT FOR NOW.
        #
        #if self._versionCheck and r.version != self.version:
        #    for result in self._sendError(AlertDescription.protocol_version,
        #            "Version in header field: %s, should be %s" % (str(r.version),
        #                                                       str(self.version))):
        #        yield result

        #Decrypt the record
        for result in self._decryptRecord(r.type, bytes):
            if result in (0,1):
                yield result
            else:
                break
        bytes = result
        p = Parser(bytes)

        #If it doesn't contain handshake messages, we can just return it
        if r.type != ContentType.handshake:
            yield (r, p)
        #If it's an SSLv2 ClientHello, we can return it as well
        elif r.ssl2:
            yield (r, p)
        else:
            #Otherwise, we loop through and add the handshake messages to the
            #handshake buffer
            while 1:
                if p.index == len(bytes): #If we're at the end
                    if not self._handshakeBuffer:
                        for result in self._sendError(\
                                AlertDescription.decode_error, \
                                "Received empty handshake record"):
                            yield result
                    break
                #There needs to be at least 4 bytes to get a header
                if p.index+4 > len(bytes):
                    for result in self._sendError(\
                            AlertDescription.decode_error,
                            "A record has a partial handshake message (1)"):
                        yield result
                p.get(1) # skip handshake type
                msgLength = p.get(3)
                if p.index+msgLength > len(bytes):
                    for result in self._sendError(\
                            AlertDescription.decode_error,
                            "A record has a partial handshake message (2)"):
                        yield result

                handshakePair = (r, bytes[p.index-4 : p.index+msgLength])
                self._handshakeBuffer.append(handshakePair)
                p.index += msgLength

            #We've moved at least one handshake message into the
            #handshakeBuffer, return the first one
            recordHeader, bytes = self._handshakeBuffer[0]
            self._handshakeBuffer = self._handshakeBuffer[1:]
            yield (recordHeader, Parser(bytes))


    def _decryptRecord(self, recordType, bytes):
        if self._readState.encContext:

            #Decrypt if it's a block cipher
            if self._readState.encContext.isBlockCipher:
                blockLength = self._readState.encContext.block_size
                if len(bytes) % blockLength != 0:
                    for result in self._sendError(\
                            AlertDescription.decryption_failed,
                            "Encrypted data not a multiple of blocksize"):
                        yield result
                ciphertext = bytesToString(bytes)
                plaintext = self._readState.encContext.decrypt(ciphertext)
                if self.version == (3,2): #For TLS 1.1, remove explicit IV
                    plaintext = plaintext[self._readState.encContext.block_size : ]
                bytes = stringToBytes(plaintext)

                #Check padding
                paddingGood = True
                paddingLength = bytes[-1]
                if (paddingLength+1) > len(bytes):
                    paddingGood=False
                    totalPaddingLength = 0
                else:
                    if self.version == (3,0):
                        totalPaddingLength = paddingLength+1
                    elif self.version in ((3,1), (3,2)):
                        totalPaddingLength = paddingLength+1
                        paddingBytes = bytes[-totalPaddingLength:-1]
                        for byte in paddingBytes:
                            if byte != paddingLength:
                                paddingGood = False
                                totalPaddingLength = 0
                    else:
                        raise AssertionError()

            #Decrypt if it's a stream cipher
            else:
                paddingGood = True
                ciphertext = bytesToString(bytes)
                plaintext = self._readState.encContext.decrypt(ciphertext)
                bytes = stringToBytes(plaintext)
                totalPaddingLength = 0

            #Check MAC
            macGood = True
            macLength = self._readState.macContext.digest_size
            endLength = macLength + totalPaddingLength
            if endLength > len(bytes):
                macGood = False
            else:
                #Read MAC
                startIndex = len(bytes) - endLength
                endIndex = startIndex + macLength
                checkBytes = bytes[startIndex : endIndex]

                #Calculate MAC
                seqnumStr = self._readState.getSeqNumStr()
                bytes = bytes[:-endLength]
                bytesStr = bytesToString(bytes)
                mac = self._readState.macContext.copy()
                mac.update(seqnumStr)
                mac.update(chr(recordType))
                if self.version == (3,0):
                    mac.update( chr( int(len(bytes)/256) ) )
                    mac.update( chr( int(len(bytes)%256) ) )
                elif self.version in ((3,1), (3,2)):
                    mac.update(chr(self.version[0]))
                    mac.update(chr(self.version[1]))
                    mac.update( chr( int(len(bytes)/256) ) )
                    mac.update( chr( int(len(bytes)%256) ) )
                else:
                    raise AssertionError()
                mac.update(bytesStr)
                macString = mac.digest()
                macBytes = stringToBytes(macString)

                #Compare MACs
                if macBytes != checkBytes:
                    macGood = False

            if not (paddingGood and macGood):
                for result in self._sendError(AlertDescription.bad_record_mac,
                                          "MAC failure (or padding failure)"):
                    yield result

        yield bytes

    def _handshakeStart(self, client):
        self._client = client
        self._handshake_md5 = md5.md5()
        self._handshake_sha = sha.sha()
        self._handshakeBuffer = []
        self.allegedSharedKeyUsername = None
        self.allegedSrpUsername = None
        self._refCount = 1

    def _handshakeDone(self, resumed):
        self.resumed = resumed
        self.closed = False

    def _calcPendingStates(self, clientRandom, serverRandom, implementations):
        if self.session.cipherSuite in CipherSuite.aes128Suites:
            macLength = 20
            keyLength = 16
            ivLength = 16
            createCipherFunc = createAES
        elif self.session.cipherSuite in CipherSuite.aes256Suites:
            macLength = 20
            keyLength = 32
            ivLength = 16
            createCipherFunc = createAES
        elif self.session.cipherSuite in CipherSuite.rc4Suites:
            macLength = 20
            keyLength = 16
            ivLength = 0
            createCipherFunc = createRC4
        elif self.session.cipherSuite in CipherSuite.tripleDESSuites:
            macLength = 20
            keyLength = 24
            ivLength = 8
            createCipherFunc = createTripleDES
        else:
            raise AssertionError()

        if self.version == (3,0):
            createMACFunc = MAC_SSL
        elif self.version in ((3,1), (3,2)):
            createMACFunc = hmac.HMAC

        outputLength = (macLength*2) + (keyLength*2) + (ivLength*2)

        #Calculate Keying Material from Master Secret
        if self.version == (3,0):
            keyBlock = PRF_SSL(self.session.masterSecret,
                               concatArrays(serverRandom, clientRandom),
                               outputLength)
        elif self.version in ((3,1), (3,2)):
            keyBlock = PRF(self.session.masterSecret,
                           "key expansion",
                           concatArrays(serverRandom,clientRandom),
                           outputLength)
        else:
            raise AssertionError()

        #Slice up Keying Material
        clientPendingState = _ConnectionState()
        serverPendingState = _ConnectionState()
        p = Parser(keyBlock)
        clientMACBlock = bytesToString(p.getFixBytes(macLength))
        serverMACBlock = bytesToString(p.getFixBytes(macLength))
        clientKeyBlock = bytesToString(p.getFixBytes(keyLength))
        serverKeyBlock = bytesToString(p.getFixBytes(keyLength))
        clientIVBlock  = bytesToString(p.getFixBytes(ivLength))
        serverIVBlock  = bytesToString(p.getFixBytes(ivLength))
        clientPendingState.macContext = createMACFunc(clientMACBlock,
                                                      digestmod=sha)
        serverPendingState.macContext = createMACFunc(serverMACBlock,
                                                      digestmod=sha)
        clientPendingState.encContext = createCipherFunc(clientKeyBlock,
                                                         clientIVBlock,
                                                         implementations)
        serverPendingState.encContext = createCipherFunc(serverKeyBlock,
                                                         serverIVBlock,
                                                         implementations)

        #Assign new connection states to pending states
        if self._client:
            self._pendingWriteState = clientPendingState
            self._pendingReadState = serverPendingState
        else:
            self._pendingWriteState = serverPendingState
            self._pendingReadState = clientPendingState

        if self.version == (3,2) and ivLength:
            #Choose fixedIVBlock for TLS 1.1 (this is encrypted with the CBC
            #residue to create the IV for each sent block)
            self.fixedIVBlock = getRandomBytes(ivLength)

    def _changeWriteState(self):
        self._writeState = self._pendingWriteState
        self._pendingWriteState = _ConnectionState()

    def _changeReadState(self):
        self._readState = self._pendingReadState
        self._pendingReadState = _ConnectionState()

    def _sendFinished(self):
        #Send ChangeCipherSpec
        for result in self._sendMsg(ChangeCipherSpec()):
            yield result

        #Switch to pending write state
        self._changeWriteState()

        #Calculate verification data
        verifyData = self._calcFinished(True)
        if self.fault == Fault.badFinished:
            verifyData[0] = (verifyData[0]+1)%256

        #Send Finished message under new state
        finished = Finished(self.version).create(verifyData)
        for result in self._sendMsg(finished):
            yield result

    def _getFinished(self):
        #Get and check ChangeCipherSpec
        for result in self._getMsg(ContentType.change_cipher_spec):
            if result in (0,1):
                yield result
        changeCipherSpec = result

        if changeCipherSpec.type != 1:
            for result in self._sendError(AlertDescription.illegal_parameter,
                                         "ChangeCipherSpec type incorrect"):
                yield result

        #Switch to pending read state
        self._changeReadState()

        #Calculate verification data
        verifyData = self._calcFinished(False)

        #Get and check Finished message under new state
        for result in self._getMsg(ContentType.handshake,
                                  HandshakeType.finished):
            if result in (0,1):
                yield result
        finished = result
        if finished.verify_data != verifyData:
            for result in self._sendError(AlertDescription.decrypt_error,
                                         "Finished message is incorrect"):
                yield result

    def _calcFinished(self, send=True):
        if self.version == (3,0):
            if (self._client and send) or (not self._client and not send):
                senderStr = "\x43\x4C\x4E\x54"
            else:
                senderStr = "\x53\x52\x56\x52"

            verifyData = self._calcSSLHandshakeHash(self.session.masterSecret,
                                                   senderStr)
            return verifyData

        elif self.version in ((3,1), (3,2)):
            if (self._client and send) or (not self._client and not send):
                label = "client finished"
            else:
                label = "server finished"

            handshakeHashes = stringToBytes(self._handshake_md5.digest() + \
                                            self._handshake_sha.digest())
            verifyData = PRF(self.session.masterSecret, label, handshakeHashes,
                             12)
            return verifyData
        else:
            raise AssertionError()

    #Used for Finished messages and CertificateVerify messages in SSL v3
    def _calcSSLHandshakeHash(self, masterSecret, label):
        masterSecretStr = bytesToString(masterSecret)

        imac_md5 = self._handshake_md5.copy()
        imac_sha = self._handshake_sha.copy()

        imac_md5.update(label + masterSecretStr + '\x36'*48)
        imac_sha.update(label + masterSecretStr + '\x36'*40)

        md5Str = md5.md5(masterSecretStr + ('\x5c'*48) + \
                         imac_md5.digest()).digest()
        shaStr = sha.sha(masterSecretStr + ('\x5c'*40) + \
                         imac_sha.digest()).digest()

        return stringToBytes(md5Str + shaStr)

