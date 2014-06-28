#
#   RSA.py : RSA encryption/decryption
#
#  Part of the Python Cryptography Toolkit
#
# Distribute and use freely; there are no restrictions on further
# dissemination and usage except those imposed by the laws of your
# country of residence.  This software is provided "as is" without
# warranty of fitness for use or suitability for any purpose, express
# or implied. Use at your own risk or not at all.
#

__revision__ = "$Id: RSA.py,v 1.20 2004/05/06 12:52:54 akuchling Exp $"

from Crypto.PublicKey import pubkey
from Crypto.Util import number

try:
    from Crypto.PublicKey import _fastmath
except ImportError:
    _fastmath = None

class error (Exception):
    pass

def generate(bits, randfunc, progress_func=None):
    """generate(bits:int, randfunc:callable, progress_func:callable)

    Generate an RSA key of length 'bits', using 'randfunc' to get
    random data and 'progress_func', if present, to display
    the progress of the key generation.
    """
    obj=RSAobj()

    # Generate the prime factors of n
    if progress_func:
        progress_func('p,q\n')
    p = q = 1L
    while number.size(p*q) < bits:
        p = pubkey.getPrime(bits/2, randfunc)
        q = pubkey.getPrime(bits/2, randfunc)

    # p shall be smaller than q (for calc of u)
    if p > q:
        (p, q)=(q, p)
    obj.p = p
    obj.q = q

    if progress_func:
        progress_func('u\n')
    obj.u = pubkey.inverse(obj.p, obj.q)
    obj.n = obj.p*obj.q

    obj.e = 65537L
    if progress_func:
        progress_func('d\n')
    obj.d=pubkey.inverse(obj.e, (obj.p-1)*(obj.q-1))

    assert bits <= 1+obj.size(), "Generated key is too small"

    return obj

def construct(tuple):
    """construct(tuple:(long,) : RSAobj
    Construct an RSA object from a 2-, 3-, 5-, or 6-tuple of numbers.
    """

    obj=RSAobj()
    if len(tuple) not in [2,3,5,6]:
        raise error, 'argument for construct() wrong length'
    for i in range(len(tuple)):
        field = obj.keydata[i]
        setattr(obj, field, tuple[i])
    if len(tuple) >= 5:
        # Ensure p is smaller than q 
        if obj.p>obj.q:
            (obj.p, obj.q)=(obj.q, obj.p)

    if len(tuple) == 5:
        # u not supplied, so we're going to have to compute it.
        obj.u=pubkey.inverse(obj.p, obj.q)

    return obj

class RSAobj(pubkey.pubkey):
    keydata = ['n', 'e', 'd', 'p', 'q', 'u']
    def _encrypt(self, plaintext, K=''):
        if self.n<=plaintext:
            raise error, 'Plaintext too large'
        return (pow(plaintext, self.e, self.n),)

    def _decrypt(self, ciphertext):
        if (not hasattr(self, 'd')):
            raise error, 'Private key not available in this object'
        if self.n<=ciphertext[0]:
            raise error, 'Ciphertext too large'
        return pow(ciphertext[0], self.d, self.n)

    def _sign(self, M, K=''):
        return (self._decrypt((M,)),)

    def _verify(self, M, sig):
        m2=self._encrypt(sig[0])
        if m2[0]==M:
            return 1
        else: return 0

    def _blind(self, M, B):
        tmp = pow(B, self.e, self.n)
        return (M * tmp) % self.n

    def _unblind(self, M, B):
        tmp = pubkey.inverse(B, self.n)
        return  (M * tmp) % self.n

    def can_blind (self):
        """can_blind() : bool
        Return a Boolean value recording whether this algorithm can
        blind data.  (This does not imply that this
        particular key object has the private information required to
        to blind a message.)
        """
        return 1

    def size(self):
        """size() : int
        Return the maximum number of bits that can be handled by this key.
        """
        return number.size(self.n) - 1

    def has_private(self):
        """has_private() : bool
        Return a Boolean denoting whether the object contains
        private components.
        """
        if hasattr(self, 'd'):
            return 1
        else: return 0

    def publickey(self):
        """publickey(): RSAobj
        Return a new key object containing only the public key information.
        """
        return construct((self.n, self.e))

class RSAobj_c(pubkey.pubkey):
    keydata = ['n', 'e', 'd', 'p', 'q', 'u']

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
        n,e = state['n'], state['e']
        if not state.has_key('d'):
            self.key = _fastmath.rsa_construct(n,e)
        else:
            d = state['d']
            if not state.has_key('q'):
                self.key = _fastmath.rsa_construct(n,e,d)
            else:
                p, q, u = state['p'], state['q'], state['u']
                self.key = _fastmath.rsa_construct(n,e,d,p,q,u)

    def _encrypt(self, plain, K):
        return (self.key._encrypt(plain),)

    def _decrypt(self, cipher):
        return self.key._decrypt(cipher[0])

    def _sign(self, M, K):
        return (self.key._sign(M),)

    def _verify(self, M, sig):
        return self.key._verify(M, sig[0])

    def _blind(self, M, B):
        return self.key._blind(M, B)

    def _unblind(self, M, B):
        return self.key._unblind(M, B)

    def can_blind (self):
        return 1

    def size(self):
        return self.key.size()

    def has_private(self):
        return self.key.has_private()

    def publickey(self):
        return construct_c((self.key.n, self.key.e))

def generate_c(bits, randfunc, progress_func = None):
    # Generate the prime factors of n
    if progress_func:
        progress_func('p,q\n')

    p = q = 1L
    while number.size(p*q) < bits:
        p = pubkey.getPrime(bits/2, randfunc)
        q = pubkey.getPrime(bits/2, randfunc)

    # p shall be smaller than q (for calc of u)
    if p > q:
        (p, q)=(q, p)
    if progress_func:
        progress_func('u\n')
    u=pubkey.inverse(p, q)
    n=p*q

    e = 65537L
    if progress_func:
        progress_func('d\n')
    d=pubkey.inverse(e, (p-1)*(q-1))
    key = _fastmath.rsa_construct(n,e,d,p,q,u)
    obj = RSAobj_c(key)

##    print p
##    print q
##    print number.size(p), number.size(q), number.size(q*p),
##    print obj.size(), bits
    assert bits <= 1+obj.size(), "Generated key is too small"
    return obj


def construct_c(tuple):
    key = apply(_fastmath.rsa_construct, tuple)
    return RSAobj_c(key)

object = RSAobj

generate_py = generate
construct_py = construct

if _fastmath:
    #print "using C version of RSA"
    generate = generate_c
    construct = construct_c
    error = _fastmath.error
