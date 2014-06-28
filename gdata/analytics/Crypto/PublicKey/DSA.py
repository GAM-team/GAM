
#
#   DSA.py : Digital Signature Algorithm
#
#  Part of the Python Cryptography Toolkit
#
# Distribute and use freely; there are no restrictions on further
# dissemination and usage except those imposed by the laws of your
# country of residence.  This software is provided "as is" without
# warranty of fitness for use or suitability for any purpose, express
# or implied. Use at your own risk or not at all.
#

__revision__ = "$Id: DSA.py,v 1.16 2004/05/06 12:52:54 akuchling Exp $"

from Crypto.PublicKey.pubkey import *
from Crypto.Util import number
from Crypto.Util.number import bytes_to_long, long_to_bytes
from Crypto.Hash import SHA

try:
    from Crypto.PublicKey import _fastmath
except ImportError:
    _fastmath = None

class error (Exception):
    pass

def generateQ(randfunc):
    S=randfunc(20)
    hash1=SHA.new(S).digest()
    hash2=SHA.new(long_to_bytes(bytes_to_long(S)+1)).digest()
    q = bignum(0)
    for i in range(0,20):
        c=ord(hash1[i])^ord(hash2[i])
        if i==0:
            c=c | 128
        if i==19:
            c= c | 1
        q=q*256+c
    while (not isPrime(q)):
        q=q+2
    if pow(2,159L) < q < pow(2,160L):
        return S, q
    raise error, 'Bad q value generated'

def generate(bits, randfunc, progress_func=None):
    """generate(bits:int, randfunc:callable, progress_func:callable)

    Generate a DSA key of length 'bits', using 'randfunc' to get
    random data and 'progress_func', if present, to display
    the progress of the key generation.
    """

    if bits<160:
        raise error, 'Key length <160 bits'
    obj=DSAobj()
    # Generate string S and prime q
    if progress_func:
        progress_func('p,q\n')
    while (1):
        S, obj.q = generateQ(randfunc)
        n=(bits-1)/160
        C, N, V = 0, 2, {}
        b=(obj.q >> 5) & 15
        powb=pow(bignum(2), b)
        powL1=pow(bignum(2), bits-1)
        while C<4096:
            for k in range(0, n+1):
                V[k]=bytes_to_long(SHA.new(S+str(N)+str(k)).digest())
            W=V[n] % powb
            for k in range(n-1, -1, -1):
                W=(W<<160L)+V[k]
            X=W+powL1
            p=X-(X%(2*obj.q)-1)
            if powL1<=p and isPrime(p):
                break
            C, N = C+1, N+n+1
        if C<4096:
            break
        if progress_func:
            progress_func('4096 multiples failed\n')

    obj.p = p
    power=(p-1)/obj.q
    if progress_func:
        progress_func('h,g\n')
    while (1):
        h=bytes_to_long(randfunc(bits)) % (p-1)
        g=pow(h, power, p)
        if 1<h<p-1 and g>1:
            break
    obj.g=g
    if progress_func:
        progress_func('x,y\n')
    while (1):
        x=bytes_to_long(randfunc(20))
        if 0 < x < obj.q:
            break
    obj.x, obj.y = x, pow(g, x, p)
    return obj

def construct(tuple):
    """construct(tuple:(long,long,long,long)|(long,long,long,long,long)):DSAobj
    Construct a DSA object from a 4- or 5-tuple of numbers.
    """
    obj=DSAobj()
    if len(tuple) not in [4,5]:
        raise error, 'argument for construct() wrong length'
    for i in range(len(tuple)):
        field = obj.keydata[i]
        setattr(obj, field, tuple[i])
    return obj

class DSAobj(pubkey):
    keydata=['y', 'g', 'p', 'q', 'x']

    def _encrypt(self, s, Kstr):
        raise error, 'DSA algorithm cannot encrypt data'

    def _decrypt(self, s):
        raise error, 'DSA algorithm cannot decrypt data'

    def _sign(self, M, K):
        if (K<2 or self.q<=K):
            raise error, 'K is not between 2 and q'
        r=pow(self.g, K, self.p) % self.q
        s=(inverse(K, self.q)*(M+self.x*r)) % self.q
        return (r,s)

    def _verify(self, M, sig):
        r, s = sig
        if r<=0 or r>=self.q or s<=0 or s>=self.q:
            return 0
        w=inverse(s, self.q)
        u1, u2 = (M*w) % self.q, (r*w) % self.q
        v1 = pow(self.g, u1, self.p)
        v2 = pow(self.y, u2, self.p)
        v = ((v1*v2) % self.p)
        v = v % self.q
        if v==r:
            return 1
        return 0

    def size(self):
        "Return the maximum number of bits that can be handled by this key."
        return number.size(self.p) - 1

    def has_private(self):
        """Return a Boolean denoting whether the object contains
        private components."""
        if hasattr(self, 'x'):
            return 1
        else:
            return 0

    def can_sign(self):
        """Return a Boolean value recording whether this algorithm can generate signatures."""
        return 1

    def can_encrypt(self):
        """Return a Boolean value recording whether this algorithm can encrypt data."""
        return 0

    def publickey(self):
        """Return a new key object containing only the public information."""
        return construct((self.y, self.g, self.p, self.q))

object=DSAobj

generate_py = generate
construct_py = construct

class DSAobj_c(pubkey):
    keydata = ['y', 'g', 'p', 'q', 'x']

    def __init__(self, key):
        self.key = key

    def __getattr__(self, attr):
        if attr in self.keydata:
            return getattr(self.key, attr)
        else:
            if self.__dict__.has_key(attr):
                self.__dict__[attr]
            else:
                raise AttributeError, '%s instance has no attribute %s' % (self.__class__, attr)

    def __getstate__(self):
        d = {}
        for k in self.keydata:
            if hasattr(self.key, k):
                d[k]=getattr(self.key, k)
        return d

    def __setstate__(self, state):
        y,g,p,q = state['y'], state['g'], state['p'], state['q']
        if not state.has_key('x'):
            self.key = _fastmath.dsa_construct(y,g,p,q)
        else:
            x = state['x']
            self.key = _fastmath.dsa_construct(y,g,p,q,x)

    def _sign(self, M, K):
        return self.key._sign(M, K)

    def _verify(self, M, (r, s)):
        return self.key._verify(M, r, s)

    def size(self):
        return self.key.size()

    def has_private(self):
        return self.key.has_private()

    def publickey(self):
        return construct_c((self.key.y, self.key.g, self.key.p, self.key.q))

    def can_sign(self):
        return 1

    def can_encrypt(self):
        return 0

def generate_c(bits, randfunc, progress_func=None):
    obj = generate_py(bits, randfunc, progress_func)
    y,g,p,q,x = obj.y, obj.g, obj.p, obj.q, obj.x
    return construct_c((y,g,p,q,x))

def construct_c(tuple):
    key = apply(_fastmath.dsa_construct, tuple)
    return DSAobj_c(key)

if _fastmath:
    #print "using C version of DSA"
    generate = generate_c
    construct = construct_c
    error = _fastmath.error
