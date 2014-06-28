#
#  randpool.py : Cryptographically strong random number generation
#
# Part of the Python Cryptography Toolkit
#
# Distribute and use freely; there are no restrictions on further
# dissemination and usage except those imposed by the laws of your
# country of residence.  This software is provided "as is" without
# warranty of fitness for use or suitability for any purpose, express
# or implied. Use at your own risk or not at all.
#

__revision__ = "$Id: randpool.py,v 1.14 2004/05/06 12:56:54 akuchling Exp $"

import time, array, types, warnings, os.path
from Crypto.Util.number import long_to_bytes
try:
    import Crypto.Util.winrandom as winrandom
except:
    winrandom = None

STIRNUM = 3

class RandomPool:
    """randpool.py : Cryptographically strong random number generation.

    The implementation here is similar to the one in PGP.  To be
    cryptographically strong, it must be difficult to determine the RNG's
    output, whether in the future or the past.  This is done by using
    a cryptographic hash function to "stir" the random data.

    Entropy is gathered in the same fashion as PGP; the highest-resolution
    clock around is read and the data is added to the random number pool.
    A conservative estimate of the entropy is then kept.

    If a cryptographically secure random source is available (/dev/urandom
    on many Unixes, Windows CryptGenRandom on most Windows), then use
    it.

    Instance Attributes:
    bits : int
      Maximum size of pool in bits
    bytes : int
      Maximum size of pool in bytes
    entropy : int
      Number of bits of entropy in this pool.

    Methods:
    add_event([s]) : add some entropy to the pool
    get_bytes(int) : get N bytes of random data
    randomize([N]) : get N bytes of randomness from external source
    """


    def __init__(self, numbytes = 160, cipher=None, hash=None):
        if hash is None:
            from Crypto.Hash import SHA as hash

        # The cipher argument is vestigial; it was removed from
        # version 1.1 so RandomPool would work even in the limited
        # exportable subset of the code
        if cipher is not None:
            warnings.warn("'cipher' parameter is no longer used")

        if isinstance(hash, types.StringType):
            # ugly hack to force __import__ to give us the end-path module
            hash = __import__('Crypto.Hash.'+hash,
                              None, None, ['new'])
            warnings.warn("'hash' parameter should now be a hashing module")

        self.bytes = numbytes
        self.bits = self.bytes*8
        self.entropy = 0
        self._hash = hash

        # Construct an array to hold the random pool,
        # initializing it to 0.
        self._randpool = array.array('B', [0]*self.bytes)

        self._event1 = self._event2 = 0
        self._addPos = 0
        self._getPos = hash.digest_size
        self._lastcounter=time.time()
        self.__counter = 0

        self._measureTickSize()        # Estimate timer resolution
        self._randomize()

    def _updateEntropyEstimate(self, nbits):
        self.entropy += nbits
        if self.entropy < 0:
            self.entropy = 0
        elif self.entropy > self.bits:
            self.entropy = self.bits

    def _randomize(self, N = 0, devname = '/dev/urandom'):
        """_randomize(N, DEVNAME:device-filepath)
        collects N bits of randomness from some entropy source (e.g.,
        /dev/urandom on Unixes that have it, Windows CryptoAPI
        CryptGenRandom, etc)
        DEVNAME is optional, defaults to /dev/urandom.  You can change it
        to /dev/random if you want to block till you get enough
        entropy.
        """
        data = ''
        if N <= 0:
            nbytes = int((self.bits - self.entropy)/8+0.5)
        else:
            nbytes = int(N/8+0.5)
        if winrandom:
            # Windows CryptGenRandom provides random data.
            data = winrandom.new().get_bytes(nbytes)
        elif os.path.exists(devname):
            # Many OSes support a /dev/urandom device
            try:
                f=open(devname)
                data=f.read(nbytes)
                f.close()
            except IOError, (num, msg):
                if num!=2: raise IOError, (num, msg)
                # If the file wasn't found, ignore the error
        if data:
            self._addBytes(data)
            # Entropy estimate: The number of bits of
            # data obtained from the random source.
            self._updateEntropyEstimate(8*len(data))
        self.stir_n()                   # Wash the random pool

    def randomize(self, N=0):
        """randomize(N:int)
        use the class entropy source to get some entropy data.
        This is overridden by KeyboardRandomize().
        """
        return self._randomize(N)

    def stir_n(self, N = STIRNUM):
        """stir_n(N)
        stirs the random pool N times
        """
        for i in xrange(N):
            self.stir()

    def stir (self, s = ''):
        """stir(s:string)
        Mix up the randomness pool.  This will call add_event() twice,
        but out of paranoia the entropy attribute will not be
        increased.  The optional 's' parameter is a string that will
        be hashed with the randomness pool.
        """

        entropy=self.entropy            # Save inital entropy value
        self.add_event()

        # Loop over the randomness pool: hash its contents
        # along with a counter, and add the resulting digest
        # back into the pool.
        for i in range(self.bytes / self._hash.digest_size):
            h = self._hash.new(self._randpool)
            h.update(str(self.__counter) + str(i) + str(self._addPos) + s)
            self._addBytes( h.digest() )
            self.__counter = (self.__counter + 1) & 0xFFFFffffL

        self._addPos, self._getPos = 0, self._hash.digest_size
        self.add_event()

        # Restore the old value of the entropy.
        self.entropy=entropy


    def get_bytes (self, N):
        """get_bytes(N:int) : string
        Return N bytes of random data.
        """

        s=''
        i, pool = self._getPos, self._randpool
        h=self._hash.new()
        dsize = self._hash.digest_size
        num = N
        while num > 0:
            h.update( self._randpool[i:i+dsize] )
            s = s + h.digest()
            num = num - dsize
            i = (i + dsize) % self.bytes
            if i<dsize:
                self.stir()
                i=self._getPos

        self._getPos = i
        self._updateEntropyEstimate(- 8*N)
        return s[:N]


    def add_event(self, s=''):
        """add_event(s:string)
        Add an event to the random pool.  The current time is stored
        between calls and used to estimate the entropy.  The optional
        's' parameter is a string that will also be XORed into the pool.
        Returns the estimated number of additional bits of entropy gain.
        """
        event = time.time()*1000
        delta = self._noise()
        s = (s + long_to_bytes(event) +
             4*chr(0xaa) + long_to_bytes(delta) )
        self._addBytes(s)
        if event==self._event1 and event==self._event2:
            # If events are coming too closely together, assume there's
            # no effective entropy being added.
            bits=0
        else:
            # Count the number of bits in delta, and assume that's the entropy.
            bits=0
            while delta:
                delta, bits = delta>>1, bits+1
            if bits>8: bits=8

        self._event1, self._event2 = event, self._event1

        self._updateEntropyEstimate(bits)
        return bits

    # Private functions
    def _noise(self):
        # Adds a bit of noise to the random pool, by adding in the
        # current time and CPU usage of this process.
        # The difference from the previous call to _noise() is taken
        # in an effort to estimate the entropy.
        t=time.time()
        delta = (t - self._lastcounter)/self._ticksize*1e6
        self._lastcounter = t
        self._addBytes(long_to_bytes(long(1000*time.time())))
        self._addBytes(long_to_bytes(long(1000*time.clock())))
        self._addBytes(long_to_bytes(long(1000*time.time())))
        self._addBytes(long_to_bytes(long(delta)))

        # Reduce delta to a maximum of 8 bits so we don't add too much
        # entropy as a result of this call.
        delta=delta % 0xff
        return int(delta)


    def _measureTickSize(self):
        # _measureTickSize() tries to estimate a rough average of the
        # resolution of time that you can see from Python.  It does
        # this by measuring the time 100 times, computing the delay
        # between measurements, and taking the median of the resulting
        # list.  (We also hash all the times and add them to the pool)
        interval = [None] * 100
        h = self._hash.new(`(id(self),id(interval))`)

        # Compute 100 differences
        t=time.time()
        h.update(`t`)
        i = 0
        j = 0
        while i < 100:
            t2=time.time()
            h.update(`(i,j,t2)`)
            j += 1
            delta=int((t2-t)*1e6)
            if delta:
                interval[i] = delta
                i += 1
                t=t2

        # Take the median of the array of intervals
        interval.sort()
        self._ticksize=interval[len(interval)/2]
        h.update(`(interval,self._ticksize)`)
        # mix in the measurement times and wash the random pool
        self.stir(h.digest())

    def _addBytes(self, s):
        "XOR the contents of the string S into the random pool"
        i, pool = self._addPos, self._randpool
        for j in range(0, len(s)):
            pool[i]=pool[i] ^ ord(s[j])
            i=(i+1) % self.bytes
        self._addPos = i

    # Deprecated method names: remove in PCT 2.1 or later.
    def getBytes(self, N):
        warnings.warn("getBytes() method replaced by get_bytes()",
                      DeprecationWarning)
        return self.get_bytes(N)

    def addEvent (self, event, s=""):
        warnings.warn("addEvent() method replaced by add_event()",
                      DeprecationWarning)
        return self.add_event(s + str(event))

class PersistentRandomPool (RandomPool):
    def __init__ (self, filename=None, *args, **kwargs):
        RandomPool.__init__(self, *args, **kwargs)
        self.filename = filename
        if filename:
            try:
                # the time taken to open and read the file might have
                # a little disk variability, modulo disk/kernel caching...
                f=open(filename, 'rb')
                self.add_event()
                data = f.read()
                self.add_event()
                # mix in the data from the file and wash the random pool
                self.stir(data)
                f.close()
            except IOError:
                # Oh, well; the file doesn't exist or is unreadable, so
                # we'll just ignore it.
                pass

    def save(self):
        if self.filename == "":
            raise ValueError, "No filename set for this object"
        # wash the random pool before save, provides some forward secrecy for
        # old values of the pool.
        self.stir_n()
        f=open(self.filename, 'wb')
        self.add_event()
        f.write(self._randpool.tostring())
        f.close()
        self.add_event()
        # wash the pool again, provide some protection for future values
        self.stir()

# non-echoing Windows keyboard entry
_kb = 0
if not _kb:
    try:
        import msvcrt
        class KeyboardEntry:
            def getch(self):
                c = msvcrt.getch()
                if c in ('\000', '\xe0'):
                    # function key
                    c += msvcrt.getch()
                return c
            def close(self, delay = 0):
                if delay:
                    time.sleep(delay)
                    while msvcrt.kbhit():
                        msvcrt.getch()
        _kb = 1
    except:
        pass

# non-echoing Posix keyboard entry
if not _kb:
    try:
        import termios
        class KeyboardEntry:
            def __init__(self, fd = 0):
                self._fd = fd
                self._old = termios.tcgetattr(fd)
                new = termios.tcgetattr(fd)
                new[3]=new[3] & ~termios.ICANON & ~termios.ECHO
                termios.tcsetattr(fd, termios.TCSANOW, new)
            def getch(self):
                termios.tcflush(0, termios.TCIFLUSH) # XXX Leave this in?
                return os.read(self._fd, 1)
            def close(self, delay = 0):
                if delay:
                    time.sleep(delay)
                    termios.tcflush(self._fd, termios.TCIFLUSH)
                termios.tcsetattr(self._fd, termios.TCSAFLUSH, self._old)
        _kb = 1
    except:
        pass

class KeyboardRandomPool (PersistentRandomPool):
    def __init__(self, *args, **kwargs):
        PersistentRandomPool.__init__(self, *args, **kwargs)

    def randomize(self, N = 0):
        "Adds N bits of entropy to random pool.  If N is 0, fill up pool."
        import os, string, time
        if N <= 0:
            bits = self.bits - self.entropy
        else:
            bits = N*8
        if bits == 0:
            return
        print bits,'bits of entropy are now required.  Please type on the keyboard'
        print 'until enough randomness has been accumulated.'
        kb = KeyboardEntry()
        s=''    # We'll save the characters typed and add them to the pool.
        hash = self._hash
        e = 0
        try:
            while e < bits:
                temp=str(bits-e).rjust(6)
                os.write(1, temp)
                s=s+kb.getch()
                e += self.add_event(s)
                os.write(1, 6*chr(8))
            self.add_event(s+hash.new(s).digest() )
        finally:
            kb.close()
        print '\n\007 Enough.  Please wait a moment.\n'
        self.stir_n()   # wash the random pool.
        kb.close(4)

if __name__ == '__main__':
    pool = RandomPool()
    print 'random pool entropy', pool.entropy, 'bits'
    pool.add_event('something')
    print `pool.get_bytes(100)`
    import tempfile, os
    fname = tempfile.mktemp()
    pool = KeyboardRandomPool(filename=fname)
    print 'keyboard random pool entropy', pool.entropy, 'bits'
    pool.randomize()
    print 'keyboard random pool entropy', pool.entropy, 'bits'
    pool.randomize(128)
    pool.save()
    saved = open(fname, 'rb').read()
    print 'saved', `saved`
    print 'pool ', `pool._randpool.tostring()`
    newpool = PersistentRandomPool(fname)
    print 'persistent random pool entropy', pool.entropy, 'bits'
    os.remove(fname)
