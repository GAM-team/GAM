"""OpenSSL/M2Crypto RSA implementation."""

from cryptomath import *

from RSAKey import *
from Python_RSAKey import Python_RSAKey

#copied from M2Crypto.util.py, so when we load the local copy of m2
#we can still use it
def password_callback(v, prompt1='Enter private key passphrase:',
                           prompt2='Verify passphrase:'):
    from getpass import getpass
    while 1:
        try:
            p1=getpass(prompt1)
            if v:
                p2=getpass(prompt2)
                if p1==p2:
                    break
            else:
                break
        except KeyboardInterrupt:
            return None
    return p1


if m2cryptoLoaded:
    class OpenSSL_RSAKey(RSAKey):
        def __init__(self, n=0, e=0):
            self.rsa = None
            self._hasPrivateKey = False
            if (n and not e) or (e and not n):
                raise AssertionError()
            if n and e:
                self.rsa = m2.rsa_new()
                m2.rsa_set_n(self.rsa, numberToMPI(n))
                m2.rsa_set_e(self.rsa, numberToMPI(e))

        def __del__(self):
            if self.rsa:
                m2.rsa_free(self.rsa)

        def __getattr__(self, name):
            if name == 'e':
                if not self.rsa:
                    return 0
                return mpiToNumber(m2.rsa_get_e(self.rsa))
            elif name == 'n':
                if not self.rsa:
                    return 0
                return mpiToNumber(m2.rsa_get_n(self.rsa))
            else:
                raise AttributeError

        def hasPrivateKey(self):
            return self._hasPrivateKey

        def hash(self):
            return Python_RSAKey(self.n, self.e).hash()

        def _rawPrivateKeyOp(self, m):
            s = numberToString(m)
            byteLength = numBytes(self.n)
            if len(s)== byteLength:
                pass
            elif len(s) == byteLength-1:
                s = '\0' + s
            else:
                raise AssertionError()
            c = stringToNumber(m2.rsa_private_encrypt(self.rsa, s,
                                                      m2.no_padding))
            return c

        def _rawPublicKeyOp(self, c):
            s = numberToString(c)
            byteLength = numBytes(self.n)
            if len(s)== byteLength:
                pass
            elif len(s) == byteLength-1:
                s = '\0' + s
            else:
                raise AssertionError()
            m = stringToNumber(m2.rsa_public_decrypt(self.rsa, s,
                                                     m2.no_padding))
            return m

        def acceptsPassword(self): return True

        def write(self, password=None):
            bio = m2.bio_new(m2.bio_s_mem())
            if self._hasPrivateKey:
                if password:
                    def f(v): return password
                    m2.rsa_write_key(self.rsa, bio, m2.des_ede_cbc(), f)
                else:
                    def f(): pass
                    m2.rsa_write_key_no_cipher(self.rsa, bio, f)
            else:
                if password:
                    raise AssertionError()
                m2.rsa_write_pub_key(self.rsa, bio)
            s = m2.bio_read(bio, m2.bio_ctrl_pending(bio))
            m2.bio_free(bio)
            return s

        def writeXMLPublicKey(self, indent=''):
            return Python_RSAKey(self.n, self.e).write(indent)

        def generate(bits):
            key = OpenSSL_RSAKey()
            def f():pass
            key.rsa = m2.rsa_generate_key(bits, 3, f)
            key._hasPrivateKey = True
            return key
        generate = staticmethod(generate)

        def parse(s, passwordCallback=None):
            if s.startswith("-----BEGIN "):
                if passwordCallback==None:
                    callback = password_callback
                else:
                    def f(v, prompt1=None, prompt2=None):
                        return passwordCallback()
                    callback = f
                bio = m2.bio_new(m2.bio_s_mem())
                try:
                    m2.bio_write(bio, s)
                    key = OpenSSL_RSAKey()
                    if s.startswith("-----BEGIN RSA PRIVATE KEY-----"):
                        def f():pass
                        key.rsa = m2.rsa_read_key(bio, callback)
                        if key.rsa == None:
                            raise SyntaxError()
                        key._hasPrivateKey = True
                    elif s.startswith("-----BEGIN PUBLIC KEY-----"):
                        key.rsa = m2.rsa_read_pub_key(bio)
                        if key.rsa == None:
                            raise SyntaxError()
                        key._hasPrivateKey = False
                    else:
                        raise SyntaxError()
                    return key
                finally:
                    m2.bio_free(bio)
            else:
                raise SyntaxError()

        parse = staticmethod(parse)
