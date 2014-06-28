"""cryptomath module

This module has basic math/crypto code."""

import os
import sys
import math
import base64
import binascii
if sys.version_info[:2] <= (2, 4):
  from sha import sha as sha1
else:
  from hashlib import sha1

from compat import *


# **************************************************************************
# Load Optional Modules
# **************************************************************************

# Try to load M2Crypto/OpenSSL
try:
    from M2Crypto import m2
    m2cryptoLoaded = True

except ImportError:
    m2cryptoLoaded = False


# Try to load cryptlib
try:
    import cryptlib_py
    try:
        cryptlib_py.cryptInit()
    except cryptlib_py.CryptException, e:
        #If tlslite and cryptoIDlib are both present,
        #they might each try to re-initialize this,
        #so we're tolerant of that.
        if e[0] != cryptlib_py.CRYPT_ERROR_INITED:
            raise
    cryptlibpyLoaded = True

except ImportError:
    cryptlibpyLoaded = False

#Try to load GMPY
try:
    import gmpy
    gmpyLoaded = True
except ImportError:
    gmpyLoaded = False

#Try to load pycrypto
try:
    import Crypto.Cipher.AES
    pycryptoLoaded = True
except ImportError:
    pycryptoLoaded = False


# **************************************************************************
# PRNG Functions
# **************************************************************************

# Get os.urandom PRNG
try:
    os.urandom(1)
    def getRandomBytes(howMany):
        return stringToBytes(os.urandom(howMany))
    prngName = "os.urandom"

except:
    # Else get cryptlib PRNG
    if cryptlibpyLoaded:
        def getRandomBytes(howMany):
            randomKey = cryptlib_py.cryptCreateContext(cryptlib_py.CRYPT_UNUSED,
                                                       cryptlib_py.CRYPT_ALGO_AES)
            cryptlib_py.cryptSetAttribute(randomKey,
                                          cryptlib_py.CRYPT_CTXINFO_MODE,
                                          cryptlib_py.CRYPT_MODE_OFB)
            cryptlib_py.cryptGenerateKey(randomKey)
            bytes = createByteArrayZeros(howMany)
            cryptlib_py.cryptEncrypt(randomKey, bytes)
            return bytes
        prngName = "cryptlib"

    else:
        #Else get UNIX /dev/urandom PRNG
        try:
            devRandomFile = open("/dev/urandom", "rb")
            def getRandomBytes(howMany):
                return stringToBytes(devRandomFile.read(howMany))
            prngName = "/dev/urandom"
        except IOError:
            #Else get Win32 CryptoAPI PRNG
            try:
                import win32prng
                def getRandomBytes(howMany):
                    s = win32prng.getRandomBytes(howMany)
                    if len(s) != howMany:
                        raise AssertionError()
                    return stringToBytes(s)
                prngName ="CryptoAPI"
            except ImportError:
                #Else no PRNG :-(
                def getRandomBytes(howMany):
                    raise NotImplementedError("No Random Number Generator "\
                                              "available.")
            prngName = "None"

# **************************************************************************
# Converter Functions
# **************************************************************************

def bytesToNumber(bytes):
    total = 0L
    multiplier = 1L
    for count in range(len(bytes)-1, -1, -1):
        byte = bytes[count]
        total += multiplier * byte
        multiplier *= 256
    return total

def numberToBytes(n):
    howManyBytes = numBytes(n)
    bytes = createByteArrayZeros(howManyBytes)
    for count in range(howManyBytes-1, -1, -1):
        bytes[count] = int(n % 256)
        n >>= 8
    return bytes

def bytesToBase64(bytes):
    s = bytesToString(bytes)
    return stringToBase64(s)

def base64ToBytes(s):
    s = base64ToString(s)
    return stringToBytes(s)

def numberToBase64(n):
    bytes = numberToBytes(n)
    return bytesToBase64(bytes)

def base64ToNumber(s):
    bytes = base64ToBytes(s)
    return bytesToNumber(bytes)

def stringToNumber(s):
    bytes = stringToBytes(s)
    return bytesToNumber(bytes)

def numberToString(s):
    bytes = numberToBytes(s)
    return bytesToString(bytes)

def base64ToString(s):
    try:
        return base64.decodestring(s)
    except binascii.Error, e:
        raise SyntaxError(e)
    except binascii.Incomplete, e:
        raise SyntaxError(e)

def stringToBase64(s):
    return base64.encodestring(s).replace("\n", "")

def mpiToNumber(mpi): #mpi is an openssl-format bignum string
    if (ord(mpi[4]) & 0x80) !=0: #Make sure this is a positive number
        raise AssertionError()
    bytes = stringToBytes(mpi[4:])
    return bytesToNumber(bytes)

def numberToMPI(n):
    bytes = numberToBytes(n)
    ext = 0
    #If the high-order bit is going to be set,
    #add an extra byte of zeros
    if (numBits(n) & 0x7)==0:
        ext = 1
    length = numBytes(n) + ext
    bytes = concatArrays(createByteArrayZeros(4+ext), bytes)
    bytes[0] = (length >> 24) & 0xFF
    bytes[1] = (length >> 16) & 0xFF
    bytes[2] = (length >> 8) & 0xFF
    bytes[3] = length & 0xFF
    return bytesToString(bytes)



# **************************************************************************
# Misc. Utility Functions
# **************************************************************************

def numBytes(n):
    if n==0:
        return 0
    bits = numBits(n)
    return int(math.ceil(bits / 8.0))

def hashAndBase64(s):
    return stringToBase64(sha1(s).digest())

def getBase64Nonce(numChars=22): #defaults to an 132 bit nonce
    bytes = getRandomBytes(numChars)
    bytesStr = "".join([chr(b) for b in bytes])
    return stringToBase64(bytesStr)[:numChars]


# **************************************************************************
# Big Number Math
# **************************************************************************

def getRandomNumber(low, high):
    if low >= high:
        raise AssertionError()
    howManyBits = numBits(high)
    howManyBytes = numBytes(high)
    lastBits = howManyBits % 8
    while 1:
        bytes = getRandomBytes(howManyBytes)
        if lastBits:
            bytes[0] = bytes[0] % (1 << lastBits)
        n = bytesToNumber(bytes)
        if n >= low and n < high:
            return n

def gcd(a,b):
    a, b = max(a,b), min(a,b)
    while b:
        a, b = b, a % b
    return a

def lcm(a, b):
    #This will break when python division changes, but we can't use // cause
    #of Jython
    return (a * b) / gcd(a, b)

#Returns inverse of a mod b, zero if none
#Uses Extended Euclidean Algorithm
def invMod(a, b):
    c, d = a, b
    uc, ud = 1, 0
    while c != 0:
        #This will break when python division changes, but we can't use //
        #cause of Jython
        q = d / c
        c, d = d-(q*c), c
        uc, ud = ud - (q * uc), uc
    if d == 1:
        return ud % b
    return 0


if gmpyLoaded:
    def powMod(base, power, modulus):
        base = gmpy.mpz(base)
        power = gmpy.mpz(power)
        modulus = gmpy.mpz(modulus)
        result = pow(base, power, modulus)
        return long(result)

else:
    #Copied from Bryan G. Olson's post to comp.lang.python
    #Does left-to-right instead of pow()'s right-to-left,
    #thus about 30% faster than the python built-in with small bases
    def powMod(base, power, modulus):
        nBitScan = 5

        """ Return base**power mod modulus, using multi bit scanning
        with nBitScan bits at a time."""

        #TREV - Added support for negative exponents
        negativeResult = False
        if (power < 0):
            power *= -1
            negativeResult = True

        exp2 = 2**nBitScan
        mask = exp2 - 1

        # Break power into a list of digits of nBitScan bits.
        # The list is recursive so easy to read in reverse direction.
        nibbles = None
        while power:
            nibbles = int(power & mask), nibbles
            power = power >> nBitScan

        # Make a table of powers of base up to 2**nBitScan - 1
        lowPowers = [1]
        for i in xrange(1, exp2):
            lowPowers.append((lowPowers[i-1] * base) % modulus)

        # To exponentiate by the first nibble, look it up in the table
        nib, nibbles = nibbles
        prod = lowPowers[nib]

        # For the rest, square nBitScan times, then multiply by
        # base^nibble
        while nibbles:
            nib, nibbles = nibbles
            for i in xrange(nBitScan):
                prod = (prod * prod) % modulus
            if nib: prod = (prod * lowPowers[nib]) % modulus

        #TREV - Added support for negative exponents
        if negativeResult:
            prodInv = invMod(prod, modulus)
            #Check to make sure the inverse is correct
            if (prod * prodInv) % modulus != 1:
                raise AssertionError()
            return prodInv
        return prod


#Pre-calculate a sieve of the ~100 primes < 1000:
def makeSieve(n):
    sieve = range(n)
    for count in range(2, int(math.sqrt(n))):
        if sieve[count] == 0:
            continue
        x = sieve[count] * 2
        while x < len(sieve):
            sieve[x] = 0
            x += sieve[count]
    sieve = [x for x in sieve[2:] if x]
    return sieve

sieve = makeSieve(1000)

def isPrime(n, iterations=5, display=False):
    #Trial division with sieve
    for x in sieve:
        if x >= n: return True
        if n % x == 0: return False
    #Passed trial division, proceed to Rabin-Miller
    #Rabin-Miller implemented per Ferguson & Schneier
    #Compute s, t for Rabin-Miller
    if display: print "*",
    s, t = n-1, 0
    while s % 2 == 0:
        s, t = s/2, t+1
    #Repeat Rabin-Miller x times
    a = 2 #Use 2 as a base for first iteration speedup, per HAC
    for count in range(iterations):
        v = powMod(a, s, n)
        if v==1:
            continue
        i = 0
        while v != n-1:
            if i == t-1:
                return False
            else:
                v, i = powMod(v, 2, n), i+1
        a = getRandomNumber(2, n)
    return True

def getRandomPrime(bits, display=False):
    if bits < 10:
        raise AssertionError()
    #The 1.5 ensures the 2 MSBs are set
    #Thus, when used for p,q in RSA, n will have its MSB set
    #
    #Since 30 is lcm(2,3,5), we'll set our test numbers to
    #29 % 30 and keep them there
    low = (2L ** (bits-1)) * 3/2
    high = 2L ** bits - 30
    p = getRandomNumber(low, high)
    p += 29 - (p % 30)
    while 1:
        if display: print ".",
        p += 30
        if p >= high:
            p = getRandomNumber(low, high)
            p += 29 - (p % 30)
        if isPrime(p, display=display):
            return p

#Unused at the moment...
def getRandomSafePrime(bits, display=False):
    if bits < 10:
        raise AssertionError()
    #The 1.5 ensures the 2 MSBs are set
    #Thus, when used for p,q in RSA, n will have its MSB set
    #
    #Since 30 is lcm(2,3,5), we'll set our test numbers to
    #29 % 30 and keep them there
    low = (2 ** (bits-2)) * 3/2
    high = (2 ** (bits-1)) - 30
    q = getRandomNumber(low, high)
    q += 29 - (q % 30)
    while 1:
        if display: print ".",
        q += 30
        if (q >= high):
            q = getRandomNumber(low, high)
            q += 29 - (q % 30)
        #Ideas from Tom Wu's SRP code
        #Do trial division on p and q before Rabin-Miller
        if isPrime(q, 0, display=display):
            p = (2 * q) + 1
            if isPrime(p, display=display):
                if isPrime(q, display=display):
                    return p
