"""passlib.handlers.argon2 -- argon2 password hash wrapper

References
==========
* argon2
    - home: https://github.com/P-H-C/phc-winner-argon2
    - whitepaper: https://github.com/P-H-C/phc-winner-argon2/blob/master/argon2-specs.pdf
* argon2 cffi wrapper
    - pypi: https://pypi.python.org/pypi/argon2_cffi
    - home: https://github.com/hynek/argon2_cffi
* argon2 pure python
    - pypi: https://pypi.python.org/pypi/argon2pure
    - home: https://github.com/bwesterb/argon2pure
"""
#=============================================================================
# imports
#=============================================================================
from __future__ import with_statement, absolute_import
# core
import logging
log = logging.getLogger(__name__)
import re
import types
from warnings import warn
# site
_argon2_cffi = None  # loaded below
_argon2pure = None  # dynamically imported by _load_backend_argon2pure()
# pkg
from passlib import exc
from passlib.crypto.digest import MAX_UINT32
from passlib.utils import to_bytes
from passlib.utils.binary import b64s_encode, b64s_decode
from passlib.utils.compat import u, unicode, bascii_to_str
import passlib.utils.handlers as uh
# local
__all__ = [
    "argon2",
]

#=============================================================================
# import argon2 package (https://pypi.python.org/pypi/argon2_cffi)
#=============================================================================

# import package
try:
    import argon2 as _argon2_cffi
except ImportError:
    _argon2_cffi = None

# get default settings for hasher
_PasswordHasher = getattr(_argon2_cffi, "PasswordHasher", None)
if _PasswordHasher:
    # we have argon2_cffi >= 16.0, use their default hasher settings
    _default_settings = _PasswordHasher()
    _default_version = _argon2_cffi.low_level.ARGON2_VERSION
else:
    # use these as our fallback settings (for no backend, or argon2pure)
    class _default_settings:
        """
        dummy object to use as source of defaults when argon2 mod not present.
        synced w/ argon2 16.1 as of 2016-6-16
        """
        time_cost = 2
        memory_cost = 512
        parallelism = 2
        salt_len = 16
        hash_len = 16
    _default_version = 0x13

#=============================================================================
# handler
#=============================================================================
class _Argon2Common(uh.SubclassBackendMixin, uh.ParallelismMixin,
                    uh.HasRounds, uh.HasRawSalt, uh.HasRawChecksum,
                    uh.GenericHandler):
    """
    Base class which implements brunt of Argon2 code.
    This is then subclassed by the various backends,
    to override w/ backend-specific methods.

    When a backend is loaded, the bases of the 'argon2' class proper
    are modified to prepend the correct backend-specific subclass.
    """
    #===================================================================
    # class attrs
    #===================================================================

    #------------------------
    # PasswordHash
    #------------------------

    name = "argon2"
    setting_kwds = ("salt",
                    "salt_size",
                    "salt_len",  # 'salt_size' alias for compat w/ argon2 package
                    "rounds",
                    "time_cost",  # 'rounds' alias for compat w/ argon2 package
                    "memory_cost",
                    "parallelism",
                    "digest_size",
                    "hash_len",  # 'digest_size' alias for compat w/ argon2 package
                    )

    # TODO: could support the optional 'data' parameter,
    #       but need to research the uses, what a more descriptive name would be,
    #       and deal w/ fact that argon2_cffi 16.1 doesn't currently support it.
    #       (argon2_pure does though)

    #------------------------
    # GenericHandler
    #------------------------
    ident = u("$argon2i")
    checksum_size = _default_settings.hash_len

    # NOTE: from_string() relies on the ordering of these...
    ident_values = (u("$argon2i$"), u("$argon2d$"))

    #------------------------
    # HasSalt
    #------------------------
    default_salt_size = _default_settings.salt_len
    min_salt_size = 8
    max_salt_size = MAX_UINT32

    #------------------------
    # HasRounds
    # TODO: once rounds limit logic is factored out,
    #       make 'rounds' and 'cost' an alias for 'time_cost'
    #------------------------
    default_rounds = _default_settings.time_cost
    min_rounds = 1
    max_rounds = MAX_UINT32
    rounds_cost = "linear"

    #------------------------
    # ParalleismMixin
    #------------------------
    max_parallelism = (1 << 24) - 1  # from argon2.h / ARGON2_MAX_LANES

    #------------------------
    # custom
    #------------------------

    #: max version support
    #: NOTE: this is dependant on the backend, and initialized/modified by set_backend()
    max_version = _default_version

    #: minimum version before needs_update() marks the hash; if None, defaults to max_version
    min_desired_version = None

    #: minimum valid memory_cost
    min_memory_cost = 8  # from argon2.h / ARGON2_MIN_MEMORY

    #: maximum number of threads (-1=unlimited);
    #: number of threads used by .hash() will be min(parallelism, max_threads)
    max_threads = -1

    #: global flag signalling argon2pure backend to use threads
    #: rather than subprocesses.
    pure_use_threads = False

    #===================================================================
    # instance attrs
    #===================================================================

    #: parallelism setting -- class value controls the default
    parallelism = _default_settings.parallelism

    #: hash version (int)
    #: NOTE: this is modified by set_backend()
    version = _default_version

    #: memory cost -- class value controls the default
    memory_cost = _default_settings.memory_cost

    #: flag indicating a Type D hash
    type_d = False

    #: optional secret data
    data = None

    #===================================================================
    # variant constructor
    #===================================================================

    @classmethod
    def using(cls, memory_cost=None, salt_len=None, time_cost=None, digest_size=None,
              checksum_size=None, hash_len=None, max_threads=None, **kwds):
        # support aliases which match argon2 naming convention
        if time_cost is not None:
            if "rounds" in kwds:
                raise TypeError("'time_cost' and 'rounds' are mutually exclusive")
            kwds['rounds'] = time_cost

        if salt_len is not None:
            if "salt_size" in kwds:
                raise TypeError("'salt_len' and 'salt_size' are mutually exclusive")
            kwds['salt_size'] = salt_len

        if hash_len is not None:
            if digest_size is not None:
                raise TypeError("'hash_len' and 'digest_size' are mutually exclusive")
            digest_size = hash_len

        if checksum_size is not None:
            if digest_size is not None:
                raise TypeError("'checksum_size' and 'digest_size' are mutually exclusive")
            digest_size = checksum_size

        # create variant
        subcls = super(_Argon2Common, cls).using(**kwds)

        # set checksum size
        relaxed = kwds.get("relaxed")
        if digest_size is not None:
            if isinstance(digest_size, uh.native_string_types):
                digest_size = int(digest_size)
            # NOTE: this isn't *really* digest size minimum, but want to enforce secure minimum.
            subcls.checksum_size = uh.norm_integer(subcls, digest_size, min=16, max=MAX_UINT32,
                                                   param="digest_size", relaxed=relaxed)

        # set memory cost
        if memory_cost is not None:
            if isinstance(memory_cost, uh.native_string_types):
                memory_cost = int(memory_cost)
            subcls.memory_cost = subcls._norm_memory_cost(memory_cost, relaxed=relaxed)

        # validate constraints
        subcls._validate_constraints(subcls.memory_cost, subcls.parallelism)

        # set max threads
        if max_threads is not None:
            if isinstance(max_threads, uh.native_string_types):
                max_threads = int(max_threads)
            if max_threads < 1 and max_threads != -1:
                raise ValueError("max_threads (%d) must be -1 (unlimited), or at least 1." %
                                 (max_threads,))
            subcls.max_threads = max_threads

        return subcls

    @classmethod
    def _validate_constraints(cls, memory_cost, parallelism):
        # NOTE: this is used by class & instance, hence passing in via arguments.
        #       could switch and make this a hybrid method.
        min_memory_cost = 8 * parallelism
        if memory_cost < min_memory_cost:
            raise ValueError("%s: memory_cost (%d) is too low, must be at least "
                             "8 * parallelism (8 * %d = %d)" %
                             (cls.name, memory_cost,
                              parallelism, min_memory_cost))

    #===================================================================
    # public api
    #===================================================================

    @classmethod
    def identify(cls, hash):
        hash = uh.to_unicode_for_identify(hash)
        return hash.startswith(cls.ident_values)

    # hash(), verify(), genhash() -- implemented by backend subclass

    #===================================================================
    # hash parsing / rendering
    #===================================================================

    # info taken from source of decode_string() function in
    # <https://github.com/P-H-C/phc-winner-argon2/blob/master/src/encoding.c>
    #
    # hash format:
    #   $argon2<T>[$v=<num>]$m=<num>,t=<num>,p=<num>[,keyid=<bin>][,data=<bin>][$<bin>[$<bin>]]
    #
    # NOTE: as of 2016-6-17, the official source (above) lists the "keyid" param in the comments,
    #       but the actual source of decode_string & encode_string don't mention it at all.
    #       we're supporting parsing it, but throw NotImplementedError if encountered.
    #
    # sample hashes:
    #    v1.0: '$argon2i$m=512,t=2,p=2$5VtWOO3cGWYQHEMaYGbsfQ$AcmqasQgW/wI6wAHAMk4aQ'
    #    v1.3: '$argon2i$v=19$m=512,t=2,p=2$5VtWOO3cGWYQHEMaYGbsfQ$AcmqasQgW/wI6wAHAMk4aQ'

    #: regex to parse argon hash
    _hash_regex = re.compile(br"""
        ^
        \$argon2(?P<type>[id])\$
        (?:
            v=(?P<version>\d+)
            \$
        )?
        m=(?P<memory_cost>\d+)
        ,
        t=(?P<time_cost>\d+)
        ,
        p=(?P<parallelism>\d+)
        (?:
            ,keyid=(?P<keyid>[^,$]+)
        )?
        (?:
            ,data=(?P<data>[^,$]+)
        )?
        (?:
            \$
            (?P<salt>[^$]+)
            (?:
                \$
                (?P<digest>.+)
            )?
        )?
        $
    """, re.X)

    @classmethod
    def from_string(cls, hash):
        # NOTE: assuming hash will be unicode, or use ascii-compatible encoding.
        if isinstance(hash, unicode):
            hash = hash.encode("utf-8")
        if not isinstance(hash, bytes):
            raise exc.ExpectedStringError(hash, "hash")
        m = cls._hash_regex.match(hash)
        if not m:
            raise exc.MalformedHashError(cls)
        type, version, memory_cost, time_cost, parallelism, keyid, data, salt, digest = \
            m.group("type", "version", "memory_cost", "time_cost", "parallelism",
                    "keyid", "data", "salt", "digest")
        assert type in [b"i", b"d"], "unexpected type code: %r" % (type,)
        if keyid:
            raise NotImplementedError("argon2 'keyid' parameter not supported")
        return cls(
            type_d=(type == b"d"),
            version=int(version) if version else 0x10,
            memory_cost=int(memory_cost),
            rounds=int(time_cost),
            parallelism=int(parallelism),
            salt=b64s_decode(salt) if salt else None,
            data=b64s_decode(data) if data else None,
            checksum=b64s_decode(digest) if digest else None,
        )

    def to_string(self):
        ident = str(self.ident_values[self.type_d])
        version = self.version
        if version == 0x10:
            vstr = ""
        else:
            vstr = "v=%d$" % version
        data = self.data
        if data:
            kdstr = ",data=" + bascii_to_str(b64s_encode(self.data))
        else:
            kdstr = ""
        # NOTE: 'keyid' param currently not supported
        return "%s%sm=%d,t=%d,p=%d%s$%s$%s" % (ident, vstr, self.memory_cost,
                                               self.rounds, self.parallelism,
                                               kdstr,
                                               bascii_to_str(b64s_encode(self.salt)),
                                               bascii_to_str(b64s_encode(self.checksum)))

    #===================================================================
    # init
    #===================================================================
    def __init__(self, type_d=False, version=None, memory_cost=None, data=None, **kwds):

        # TODO: factor out variable checksum size support into a mixin.
        # set checksum size to specific value before _norm_checksum() is called
        checksum = kwds.get("checksum")
        if checksum is not None:
            self.checksum_size = len(checksum)

        # call parent
        super(_Argon2Common, self).__init__(**kwds)

        # init type
        # NOTE: we don't support *generating* type I hashes, but do support verifying them.
        self.type_d = type_d

        # init version
        if version is None:
            assert uh.validate_default_value(self, self.version, self._norm_version,
                                             param="version")
        else:
            self.version = self._norm_version(version)

        # init memory cost
        if memory_cost is None:
            assert uh.validate_default_value(self, self.memory_cost, self._norm_memory_cost,
                                             param="memory_cost")
        else:
            self.memory_cost = self._norm_memory_cost(memory_cost)

        # init data
        if data is None:
            assert self.data is None
        else:
            if not isinstance(data, bytes):
                raise uh.exc.ExpectedTypeError(data, "bytes", "data")
            self.data = data

    #-------------------------------------------------------------------
    # parameter guards
    #-------------------------------------------------------------------

    @classmethod
    def _norm_version(cls, version):
        if not isinstance(version, uh.int_types):
            raise uh.exc.ExpectedTypeError(version, "integer", "version")

        # minimum valid version
        if version < 0x13 and version != 0x10:
            raise ValueError("invalid argon2 hash version: %d" % (version,))

        # check this isn't past backend's max version
        backend = cls.get_backend()
        if version > cls.max_version:
            raise ValueError("%s: hash version 0x%X not supported by %r backend "
                             "(max version is 0x%X); try updating or switching backends" %
                             (cls.name, version, backend, cls.max_version))
        return version

    @classmethod
    def _norm_memory_cost(cls, memory_cost, relaxed=False):
        return uh.norm_integer(cls, memory_cost, min=cls.min_memory_cost,
                               param="memory_cost", relaxed=relaxed)

    #===================================================================
    # digest calculation
    #===================================================================

    # NOTE: _calc_checksum implemented by backend subclass

    #===================================================================
    # hash migration
    #===================================================================

    def _calc_needs_update(self, **kwds):
        cls = type(self)
        if self.type_d:
            # type 'd' hashes shouldn't be used for passwords.
            return True
        minver = cls.min_desired_version
        if minver is None or minver > cls.max_version:
            minver = cls.max_version
        if self.version < minver:
            # version is too old.
            return True
        if self.memory_cost != cls.memory_cost:
            return True
        if self.checksum_size != cls.checksum_size:
            return True
        return super(_Argon2Common, self)._calc_needs_update(**kwds)
    
    #===================================================================
    # backend loading
    #===================================================================

    _no_backend_suggestion = " -- recommend you install one (e.g. 'pip install argon2_cffi')"

    @classmethod
    def _finalize_backend_mixin(mixin_cls, name, dryrun):
        """
        helper called by from backend mixin classes' _load_backend_mixin() --
        invoked after backend imports have been loaded, and performs
        feature detection & testing common to all backends.
        """
        max_version = mixin_cls.max_version
        assert isinstance(max_version, int) and max_version >= 0x10
        if max_version < 0x13:
            warn("%r doesn't support argon2 v1.3, and should be upgraded" % name,
                 uh.exc.PasslibSecurityWarning)
        return True

    @classmethod
    def _adapt_backend_error(cls, err, hash=None, self=None):
        """
        internal helper invoked when backend has hash/verification error;
        used to adapt to passlib message.
        """
        backend = cls.get_backend()

        # parse hash to throw error if format was invalid, parameter out of range, etc.
        if self is None and hash is not None:
            self = cls.from_string(hash)

        # check constraints on parsed object
        # XXX: could move this to __init__, but not needed by needs_update calls
        if self is not None:
            self._validate_constraints(self.memory_cost, self.parallelism)

            # as of cffi 16.1, lacks support in hash_secret(), so genhash() will get here.
            # as of cffi 16.2, support removed from verify_secret() as well.
            if backend == "argon2_cffi" and self.data is not None:
                raise NotImplementedError("argon2_cffi backend doesn't support the 'data' parameter")

        # fallback to reporting a malformed hash
        text = str(err)
        if text not in [
            "Decoding failed"  # argon2_cffi's default message
            ]:
            reason = "%s reported: %s: hash=%r" % (backend, text, hash)
        else:
            reason = repr(hash)
        raise exc.MalformedHashError(cls, reason=reason)

    #===================================================================
    # eoc
    #===================================================================

#-----------------------------------------------------------------------
# stub backend
#-----------------------------------------------------------------------
class _NoBackend(_Argon2Common):
    """
    mixin used before any backend has been loaded.
    contains stubs that force loading of one of the available backends.
    """
    #===================================================================
    # primary methods
    #===================================================================
    @classmethod
    def hash(cls, secret):
        cls._stub_requires_backend()
        return cls.hash(secret)

    @classmethod
    def verify(cls, secret, hash):
        cls._stub_requires_backend()
        return cls.verify(secret, hash)

    @uh.deprecated_method(deprecated="1.7", removed="2.0")
    @classmethod
    def genhash(cls, secret, config):
        cls._stub_requires_backend()
        return cls.genhash(secret, config)

    #===================================================================
    # digest calculation
    #===================================================================
    def _calc_checksum(self, secret):
        # NOTE: since argon2_cffi takes care of rendering hash,
        #       _calc_checksum() is only used by the argon2pure backend.
        self._stub_requires_backend()
        # NOTE: have to use super() here so that we don't recursively
        #       call subclass's wrapped _calc_checksum
        return super(argon2, self)._calc_checksum(secret)

    #===================================================================
    # eoc
    #===================================================================

#-----------------------------------------------------------------------
# argon2_cffi backend
#-----------------------------------------------------------------------
class _CffiBackend(_Argon2Common):
    """
    argon2_cffi backend
    """
    #===================================================================
    # backend loading
    #===================================================================

    @classmethod
    def _load_backend_mixin(mixin_cls, name, dryrun):
        # we automatically import this at top, so just grab info
        if _argon2_cffi is None:
            return False
        max_version = _argon2_cffi.low_level.ARGON2_VERSION
        log.debug("detected 'argon2_cffi' backend, version %r, with support for 0x%x argon2 hashes",
                  _argon2_cffi.__version__, max_version)
        mixin_cls.version = mixin_cls.max_version = max_version
        return mixin_cls._finalize_backend_mixin(name, dryrun)

    #===================================================================
    # primary methods
    #===================================================================
    @classmethod
    def hash(cls, secret):
        # TODO: add in 'encoding' support once that's finalized in 1.8 / 1.9.
        uh.validate_secret(secret)
        secret = to_bytes(secret, "utf-8")
        # XXX: doesn't seem to be a way to make this honor max_threads
        try:
            return bascii_to_str(_argon2_cffi.low_level.hash_secret(
                type=_argon2_cffi.low_level.Type.I,
                memory_cost=cls.memory_cost,
                time_cost=cls.default_rounds,
                parallelism=cls.parallelism,
                salt=to_bytes(cls._generate_salt()),
                hash_len=cls.checksum_size,
                secret=secret,
            ))
        except _argon2_cffi.exceptions.HashingError as err:
            raise cls._adapt_backend_error(err)

    @classmethod
    def verify(cls, secret, hash):
        # TODO: add in 'encoding' support once that's finalized in 1.8 / 1.9.
        uh.validate_secret(secret)
        secret = to_bytes(secret, "utf-8")
        hash = to_bytes(hash, "ascii")
        if hash.startswith(b"$argon2d$"):
            type = _argon2_cffi.low_level.Type.D
        else:
            type = _argon2_cffi.low_level.Type.I
        # XXX: doesn't seem to be a way to make this honor max_threads
        try:
            result = _argon2_cffi.low_level.verify_secret(hash, secret, type)
            assert result is True
            return True
        except _argon2_cffi.exceptions.VerifyMismatchError:
            return False
        except _argon2_cffi.exceptions.VerificationError as err:
            raise cls._adapt_backend_error(err, hash=hash)

    # NOTE: deprecated, will be removed in 2.0
    @classmethod
    def genhash(cls, secret, config):
        # TODO: add in 'encoding' support once that's finalized in 1.8 / 1.9.
        uh.validate_secret(secret)
        secret = to_bytes(secret, "utf-8")
        self = cls.from_string(config)
        if self.type_d:
            type = _argon2_cffi.low_level.Type.D
        else:
            type = _argon2_cffi.low_level.Type.I
        # XXX: doesn't seem to be a way to make this honor max_threads
        try:
            result = bascii_to_str(_argon2_cffi.low_level.hash_secret(
                type=type,
                memory_cost=self.memory_cost,
                time_cost=self.rounds,
                parallelism=self.parallelism,
                salt=to_bytes(self.salt),
                hash_len=self.checksum_size,
                secret=secret,
                version=self.version,
            ))
        except _argon2_cffi.exceptions.HashingError as err:
            raise cls._adapt_backend_error(err, hash=config)
        if self.version == 0x10:
            # workaround: argon2 0x13 always returns "v=" segment, even for 0x10 hashes
            result = result.replace("$v=16$", "$")
        return result

    #===================================================================
    # digest calculation
    #===================================================================
    def _calc_checksum(self, secret):
        raise AssertionError("shouldn't be called under argon2_cffi backend")

    #===================================================================
    # eoc
    #===================================================================

#-----------------------------------------------------------------------
# argon2pure backend
#-----------------------------------------------------------------------
class _PureBackend(_Argon2Common):
    """
    argon2pure backend
    """
    #===================================================================
    # backend loading
    #===================================================================

    @classmethod
    def _load_backend_mixin(mixin_cls, name, dryrun):
        # import argon2pure
        global _argon2pure
        try:
            import argon2pure as _argon2pure
        except ImportError:
            return False

        # get default / max supported version -- added in v1.2.2
        try:
            from argon2pure import ARGON2_DEFAULT_VERSION as max_version
        except ImportError:
            log.warning("detected 'argon2pure' backend, but package is too old "
                        "(passlib requires argon2pure >= 1.2.3)")
            return False

        log.debug("detected 'argon2pure' backend, with support for 0x%x argon2 hashes",
                  max_version)

        if not dryrun:
            warn("Using argon2pure backend, which is 100x+ slower than is required "
                 "for adequate security. Installing argon2_cffi (via 'pip install argon2_cffi') "
                 "is strongly recommended", exc.PasslibSecurityWarning)

        mixin_cls.version = mixin_cls.max_version = max_version
        return mixin_cls._finalize_backend_mixin(name, dryrun)

    #===================================================================
    # primary methods
    #===================================================================

    # NOTE: this backend uses default .hash() & .verify() implementations.

    #===================================================================
    # digest calculation
    #===================================================================
    def _calc_checksum(self, secret):
        # TODO: add in 'encoding' support once that's finalized in 1.8 / 1.9.
        uh.validate_secret(secret)
        secret = to_bytes(secret, "utf-8")
        if self.type_d:
            type = _argon2pure.ARGON2D
        else:
            type = _argon2pure.ARGON2I
        kwds = dict(
            password=secret,
            salt=self.salt,
            time_cost=self.rounds,
            memory_cost=self.memory_cost,
            parallelism=self.parallelism,
            tag_length=self.checksum_size,
            type_code=type,
            version=self.version,
        )
        if self.max_threads > 0:
            kwds['threads'] = self.max_threads
        if self.pure_use_threads:
            kwds['use_threads'] = True
        if self.data:
            kwds['associated_data'] = self.data
        # NOTE: should return raw bytes
        # NOTE: this may raise _argon2pure.Argon2ParameterError,
        #       but it if does that, there's a bug in our own parameter checking code.
        try:
            return _argon2pure.argon2(**kwds)
        except _argon2pure.Argon2Error as err:
            raise self._adapt_backend_error(err, self=self)

    #===================================================================
    # eoc
    #===================================================================

class argon2(_NoBackend, _Argon2Common):
    """
    This class implements the Argon2 password hash [#argon2-home]_, and follows the :ref:`password-hash-api`.
    (This class only supports generating "Type I" argon2 hashes).

    Argon2 supports a variable-length salt, and variable time & memory cost,
    and a number of other configurable parameters.

    The :meth:`~passlib.ifc.PasswordHash.replace` method accepts the following optional keywords:

    :type salt: str
    :param salt:
        Optional salt string.
        If specified, the length must be between 0-1024 bytes.
        If not specified, one will be auto-generated (this is recommended).

    :type salt_size: int
    :param salt_size:
        Optional number of bytes to use when autogenerating new salts.

    :type rounds: int
    :param rounds:
        Optional number of rounds to use.
        This corresponds linearly to the amount of time hashing will take.

    :type time_cost: int
    :param time_cost:
        An alias for **rounds**, for compatibility with underlying argon2 library.

    :param int memory_cost:
        Defines the memory usage in kibibytes.
        This corresponds linearly to the amount of memory hashing will take.

    :param int parallelism:
        Defines the parallelization factor.
        *NOTE: this will affect the resulting hash value.*

    :param int digest_size:
        Length of the digest in bytes.

    :param int max_threads:
        Maximum number of threads that will be used.
        -1 means unlimited; otherwise hashing will use ``min(parallelism, max_threads)`` threads.

        .. note::

            This option is currently only honored by the argon2pure backend.

    :type relaxed: bool
    :param relaxed:
        By default, providing an invalid value for one of the other
        keywords will result in a :exc:`ValueError`. If ``relaxed=True``,
        and the error can be corrected, a :exc:`~passlib.exc.PasslibHashWarning`
        will be issued instead. Correctable errors include ``rounds``
        that are too small or too large, and ``salt`` strings that are too long.

    .. todo::

        * Support configurable threading limits.
    """
    #=============================================================================
    # backend
    #=============================================================================

    # NOTE: the brunt of the argon2 class is implemented in _Argon2Common.
    #       there are then subclass for each backend (e.g. _PureBackend),
    #       these are dynamically prepended to this class's bases
    #       in order to load the appropriate backend.

    #: list of potential backends
    backends = ("argon2_cffi", "argon2pure")

    #: flag that this class's bases should be modified by SubclassBackendMixin
    _backend_mixin_target = True

    #: map of backend -> mixin class, used by _get_backend_loader()
    _backend_mixin_map = {
        None: _NoBackend,
        "argon2_cffi": _CffiBackend,
        "argon2pure": _PureBackend,
    }

    #=============================================================================
    #
    #=============================================================================

#=============================================================================
# eof
#=============================================================================
