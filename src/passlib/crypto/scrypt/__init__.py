"""passlib.utils.scrypt -- scrypt hash frontend and help utilities"""
#==========================================================================
# imports
#==========================================================================
from __future__ import absolute_import
# core
import logging; log = logging.getLogger(__name__)
from warnings import warn
# pkg
from passlib import exc
from passlib.utils import to_bytes
from passlib.utils.compat import PYPY
# local
__all__ =[
    "validate",
    "scrypt",
]

#==========================================================================
# config validation
#==========================================================================

#: max output length in bytes
MAX_KEYLEN = ((1 << 32) - 1) * 32

#: max ``r * p`` limit
MAX_RP = (1 << 30) - 1

# TODO: unittests for this function
def validate(n, r, p):
    """
    helper which validates a set of scrypt config parameters.
    scrypt will take ``O(n * r * p)`` time and ``O(n * r)`` memory.
    limitations are that ``n = 2**<positive integer>``, ``n < 2**(16*r)``, ``r * p < 2 ** 30``.

    :param n: scrypt rounds
    :param r: scrypt block size
    :param p: scrypt parallel factor
    """
    if r < 1:
        raise ValueError("r must be > 0: r=%r" % r)

    if p < 1:
        raise ValueError("p must be > 0: p=%r" % p)

    if r * p > MAX_RP:
        # pbkdf2-hmac-sha256 limitation - it will be requested to generate ``p*(2*r)*64`` bytes,
        # but pbkdf2 can do max of (2**31-1) blocks, and sha-256 has 32 byte block size...
        # so ``(2**31-1)*32 >= p*r*128`` -> ``r*p < 2**30``
        raise ValueError("r * p must be < 2**30: r=%r, p=%r" % (r,p))

    if n < 2 or n & (n - 1):
        raise ValueError("n must be > 1, and a power of 2: n=%r" % n)

    return True

# TODO: configuration picker (may need psutil for full effect)

#==========================================================================
# hash frontend
#==========================================================================

#: backend function used by scrypt(), filled in by _set_backend()
_scrypt = None

#: name of backend currently in use, exposed for informational purposes.
backend = None

def scrypt(secret, salt, n, r, p=1, keylen=32):
    """run SCrypt key derivation function using specified parameters.

    :arg secret:
        passphrase string (unicode is encoded to bytes using utf-8).

    :arg salt:
        salt string (unicode is encoded to bytes using utf-8).

    :arg n:
        integer 'N' parameter

    :arg r:
        integer 'r' parameter

    :arg p:
        integer 'p' parameter

    :arg keylen:
        number of bytes of key to generate.
        defaults to 32 (the internal block size).

    :returns:
        a *keylen*-sized bytes instance

    SCrypt imposes a number of constraints on it's input parameters:

    * ``r * p < 2**30`` -- due to a limitation of PBKDF2-HMAC-SHA256.
    * ``keylen < (2**32 - 1) * 32`` -- due to a limitation of PBKDF2-HMAC-SHA256.
    * ``n`` must a be a power of 2, and > 1 -- internal limitation of scrypt() implementation

    :raises ValueError: if the provided parameters are invalid (see constraints above).

    .. warning::

        Unless the third-party ``scrypt <https://pypi.python.org/pypi/scrypt/>``_ package
        is installed, passlib will use a builtin pure-python implementation of scrypt,
        which is *considerably* slower (and thus requires a much lower / less secure
        ``n`` value in order to be usuable). Installing the :mod:`!scrypt` package
        is strongly recommended.
    """
    validate(n, r, p)
    secret = to_bytes(secret, param="secret")
    salt = to_bytes(salt, param="salt")
    if keylen < 1:
        raise ValueError("keylen must be at least 1")
    if keylen > MAX_KEYLEN:
        raise ValueError("keylen too large, must be <= %d" % MAX_KEYLEN)
    return _scrypt(secret, salt, n, r, p, keylen)


def _load_builtin_backend():
    """
    Load pure-python scrypt implementation built into passlib.
    """
    slowdown = 10 if PYPY else 100
    warn("Using builtin scrypt backend, which is %dx slower than is required "
         "for adequate security. Installing scrypt support (via 'pip install scrypt') "
         "is strongly recommended" % slowdown, exc.PasslibSecurityWarning)
    from ._builtin import ScryptEngine
    return ScryptEngine.execute


def _load_cffi_backend():
    """
    Try to import the ctypes-based scrypt hash function provided by the
    ``scrypt <https://pypi.python.org/pypi/scrypt/>``_ package.
    """
    try:
        from scrypt import hash
        return hash
    except ImportError:
        pass
    # not available, but check to see if package present but outdated / not installed right
    try:
        import scrypt
    except ImportError as err:
        if "scrypt" not in str(err):
            # e.g. if cffi isn't set up right
            # user should try importing scrypt explicitly to diagnose problem.
            warn("'scrypt' package failed to import correctly (possible installation issue?)",
                 exc.PasslibWarning)
        # else: package just isn't installed
    else:
        warn("'scrypt' package is too old (lacks ``hash()`` method)", exc.PasslibWarning)
    return None


#: list of potential backends
backend_values = ("scrypt", "builtin")

#: dict mapping backend name -> loader
_backend_loaders = dict(
    scrypt=_load_cffi_backend,  # XXX: rename backend constant to "cffi"?
    builtin=_load_builtin_backend,
)


def _set_backend(name, dryrun=False):
    """
    set backend for scrypt(). if name not specified, loads first available.

    :raises ~passlib.exc.MissingBackendError: if backend can't be found

    .. note:: mainly intended to be called by unittests, and scrypt hash handler
    """
    if name == "any":
        return
    elif name == "default":
        for name in backend_values:
            try:
                return _set_backend(name, dryrun=dryrun)
            except exc.MissingBackendError:
                continue
        raise exc.MissingBackendError("no scrypt backends available")
    else:
        loader = _backend_loaders.get(name)
        if not loader:
            raise ValueError("unknown scrypt backend: %r" % (name,))
        hash = loader()
        if not hash:
            raise exc.MissingBackendError("scrypt backend %r not available" % name)
        if dryrun:
            return
        global _scrypt, backend
        backend = name
        _scrypt = hash

# initialize backend
_set_backend("default")


def _has_backend(name):
    try:
        _set_backend(name, dryrun=True)
        return True
    except exc.MissingBackendError:
        return False

#==========================================================================
# eof
#==========================================================================
