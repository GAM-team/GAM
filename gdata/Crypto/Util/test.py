#
#   test.py : Functions used for testing the modules
#
#  Part of the Python Cryptography Toolkit
#
# Distribute and use freely; there are no restrictions on further
# dissemination and usage except those imposed by the laws of your
# country of residence.  This software is provided "as is" without
# warranty of fitness for use or suitability for any purpose, express
# or implied. Use at your own risk or not at all.
#

__revision__ = "$Id: test.py,v 1.16 2004/08/13 22:24:18 akuchling Exp $"

import binascii
import string
import testdata

from Crypto.Cipher import *

def die(string):
    import sys
    print '***ERROR: ', string
#    sys.exit(0)   # Will default to continuing onward...

def print_timing (size, delta, verbose):
    if verbose:
        if delta == 0:
            print 'Unable to measure time -- elapsed time too small'
        else:
            print '%.2f K/sec' % (size/delta)
            
def exerciseBlockCipher(cipher, verbose):
    import string, time
    try:
        ciph = eval(cipher)
    except NameError:
        print cipher, 'module not available'
        return None
    print cipher+ ':'
    str='1'                             # Build 128K of test data
    for i in xrange(0, 17):
        str=str+str
    if ciph.key_size==0: ciph.key_size=16
    password = 'password12345678Extra text for password'[0:ciph.key_size]
    IV = 'Test IV Test IV Test IV Test'[0:ciph.block_size]

    if verbose: print '  ECB mode:',
    obj=ciph.new(password, ciph.MODE_ECB)
    if obj.block_size != ciph.block_size:
        die("Module and cipher object block_size don't match")

    text='1234567812345678'[0:ciph.block_size]
    c=obj.encrypt(text)
    if (obj.decrypt(c)!=text): die('Error encrypting "'+text+'"')
    text='KuchlingKuchling'[0:ciph.block_size]
    c=obj.encrypt(text)
    if (obj.decrypt(c)!=text): die('Error encrypting "'+text+'"')
    text='NotTodayNotEver!'[0:ciph.block_size]
    c=obj.encrypt(text)
    if (obj.decrypt(c)!=text): die('Error encrypting "'+text+'"')

    start=time.time()
    s=obj.encrypt(str)
    s2=obj.decrypt(s)
    end=time.time()
    if (str!=s2):
        die('Error in resulting plaintext from ECB mode')
    print_timing(256, end-start, verbose)
    del obj

    if verbose: print '  CFB mode:',
    obj1=ciph.new(password, ciph.MODE_CFB, IV)
    obj2=ciph.new(password, ciph.MODE_CFB, IV)
    start=time.time()
    ciphertext=obj1.encrypt(str[0:65536])
    plaintext=obj2.decrypt(ciphertext)
    end=time.time()
    if (plaintext!=str[0:65536]):
        die('Error in resulting plaintext from CFB mode')
    print_timing(64, end-start, verbose)
    del obj1, obj2

    if verbose: print '  CBC mode:',
    obj1=ciph.new(password, ciph.MODE_CBC, IV)
    obj2=ciph.new(password, ciph.MODE_CBC, IV)
    start=time.time()
    ciphertext=obj1.encrypt(str)
    plaintext=obj2.decrypt(ciphertext)
    end=time.time()
    if (plaintext!=str):
        die('Error in resulting plaintext from CBC mode')
    print_timing(256, end-start, verbose)
    del obj1, obj2

    if verbose: print '  PGP mode:',
    obj1=ciph.new(password, ciph.MODE_PGP, IV)
    obj2=ciph.new(password, ciph.MODE_PGP, IV)
    start=time.time()
    ciphertext=obj1.encrypt(str)
    plaintext=obj2.decrypt(ciphertext)
    end=time.time()
    if (plaintext!=str):
        die('Error in resulting plaintext from PGP mode')
    print_timing(256, end-start, verbose)
    del obj1, obj2

    if verbose: print '  OFB mode:',
    obj1=ciph.new(password, ciph.MODE_OFB, IV)
    obj2=ciph.new(password, ciph.MODE_OFB, IV)
    start=time.time()
    ciphertext=obj1.encrypt(str)
    plaintext=obj2.decrypt(ciphertext)
    end=time.time()
    if (plaintext!=str):
        die('Error in resulting plaintext from OFB mode')
    print_timing(256, end-start, verbose)
    del obj1, obj2

    def counter(length=ciph.block_size):
        return length * 'a'

    if verbose: print '  CTR mode:',
    obj1=ciph.new(password, ciph.MODE_CTR, counter=counter)
    obj2=ciph.new(password, ciph.MODE_CTR, counter=counter)
    start=time.time()
    ciphertext=obj1.encrypt(str)
    plaintext=obj2.decrypt(ciphertext)
    end=time.time()
    if (plaintext!=str):
        die('Error in resulting plaintext from CTR mode')
    print_timing(256, end-start, verbose)
    del obj1, obj2

    # Test the IV handling
    if verbose: print '  Testing IV handling'
    obj1=ciph.new(password, ciph.MODE_CBC, IV)
    plaintext='Test'*(ciph.block_size/4)*3
    ciphertext1=obj1.encrypt(plaintext)
    obj1.IV=IV
    ciphertext2=obj1.encrypt(plaintext)
    if ciphertext1!=ciphertext2:
        die('Error in setting IV')

    # Test keyword arguments
    obj1=ciph.new(key=password)
    obj1=ciph.new(password, mode=ciph.MODE_CBC)
    obj1=ciph.new(mode=ciph.MODE_CBC, key=password)
    obj1=ciph.new(IV=IV, mode=ciph.MODE_CBC, key=password)

    return ciph

def exerciseStreamCipher(cipher, verbose):
    import string, time
    try:
        ciph = eval(cipher)
    except (NameError):
        print cipher, 'module not available'
        return None
    print cipher + ':',
    str='1'                             # Build 128K of test data
    for i in xrange(0, 17):
        str=str+str
    key_size = ciph.key_size or 16
    password = 'password12345678Extra text for password'[0:key_size]

    obj1=ciph.new(password)
    obj2=ciph.new(password)
    if obj1.block_size != ciph.block_size:
        die("Module and cipher object block_size don't match")
    if obj1.key_size != ciph.key_size:
        die("Module and cipher object key_size don't match")

    text='1234567812345678Python'
    c=obj1.encrypt(text)
    if (obj2.decrypt(c)!=text): die('Error encrypting "'+text+'"')
    text='B1FF I2 A R3A11Y |<00L D00D!!!!!'
    c=obj1.encrypt(text)
    if (obj2.decrypt(c)!=text): die('Error encrypting "'+text+'"')
    text='SpamSpamSpamSpamSpamSpamSpamSpamSpam'
    c=obj1.encrypt(text)
    if (obj2.decrypt(c)!=text): die('Error encrypting "'+text+'"')

    start=time.time()
    s=obj1.encrypt(str)
    str=obj2.decrypt(s)
    end=time.time()
    print_timing(256, end-start, verbose)
    del obj1, obj2

    return ciph

def TestStreamModules(args=['arc4', 'XOR'], verbose=1):
    import sys, string
    args=map(string.lower, args)

    if 'arc4' in args:
        # Test ARC4 stream cipher
        arc4=exerciseStreamCipher('ARC4', verbose)
        if (arc4!=None):
                for entry in testdata.arc4:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=arc4.new(key)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('ARC4 failed on entry '+`entry`)

    if 'xor' in args:
        # Test XOR stream cipher
        XOR=exerciseStreamCipher('XOR', verbose)
        if (XOR!=None):
                for entry in testdata.xor:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=XOR.new(key)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('XOR failed on entry '+`entry`)


def TestBlockModules(args=['aes', 'arc2', 'des', 'blowfish', 'cast', 'des3',
                           'idea', 'rc5'],
                     verbose=1):
    import string
    args=map(string.lower, args)
    if 'aes' in args:
        ciph=exerciseBlockCipher('AES', verbose)        # AES
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.aes:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, ciph.MODE_ECB)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('AES failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        if verbose: print

                for entry in testdata.aes_modes:
                    mode, key, plain, cipher, kw = entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, mode, **kw)
                    obj2=ciph.new(key, mode, **kw)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('AES encrypt failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        if verbose: print

                    plain2=obj2.decrypt(ciphertext)
                    if plain2!=plain:
                        die('AES decrypt failed on entry '+`entry`)
                        for i in plain2:
                            if verbose: print hex(ord(i)),
                        if verbose: print


    if 'arc2' in args:
        ciph=exerciseBlockCipher('ARC2', verbose)           # Alleged RC2
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.arc2:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, ciph.MODE_ECB)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('ARC2 failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        print

    if 'blowfish' in args:
        ciph=exerciseBlockCipher('Blowfish',verbose)# Bruce Schneier's Blowfish cipher
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.blowfish:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, ciph.MODE_ECB)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('Blowfish failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        if verbose: print

    if 'cast' in args:
        ciph=exerciseBlockCipher('CAST', verbose)        # CAST-128
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.cast:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, ciph.MODE_ECB)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('CAST failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        if verbose: print

                if 0:
                    # The full-maintenance test; it requires 4 million encryptions,
                    # and correspondingly is quite time-consuming.  I've disabled
                    # it; it's faster to compile block/cast.c with -DTEST and run
                    # the resulting program.
                    a = b = '\x01\x23\x45\x67\x12\x34\x56\x78\x23\x45\x67\x89\x34\x56\x78\x9A'

                    for i in range(0, 1000000):
                        obj = cast.new(b, cast.MODE_ECB)
                        a = obj.encrypt(a[:8]) + obj.encrypt(a[-8:])
                        obj = cast.new(a, cast.MODE_ECB)
                        b = obj.encrypt(b[:8]) + obj.encrypt(b[-8:])

                    if a!="\xEE\xA9\xD0\xA2\x49\xFD\x3B\xA6\xB3\x43\x6F\xB8\x9D\x6D\xCA\x92":
                        if verbose: print 'CAST test failed: value of "a" doesn\'t match'
                    if b!="\xB2\xC9\x5E\xB0\x0C\x31\xAD\x71\x80\xAC\x05\xB8\xE8\x3D\x69\x6E":
                        if verbose: print 'CAST test failed: value of "b" doesn\'t match'

    if 'des' in args:
        # Test/benchmark DES block cipher
        des=exerciseBlockCipher('DES', verbose)
        if (des!=None):
            # Various tests taken from the DES library packaged with Kerberos V4
            obj=des.new(binascii.a2b_hex('0123456789abcdef'), des.MODE_ECB)
            s=obj.encrypt('Now is t')
            if (s!=binascii.a2b_hex('3fa40e8a984d4815')):
                die('DES fails test 1')
            obj=des.new(binascii.a2b_hex('08192a3b4c5d6e7f'), des.MODE_ECB)
            s=obj.encrypt('\000\000\000\000\000\000\000\000')
            if (s!=binascii.a2b_hex('25ddac3e96176467')):
                die('DES fails test 2')
            obj=des.new(binascii.a2b_hex('0123456789abcdef'), des.MODE_CBC,
                        binascii.a2b_hex('1234567890abcdef'))
            s=obj.encrypt("Now is the time for all ")
            if (s!=binascii.a2b_hex('e5c7cdde872bf27c43e934008c389c0f683788499a7c05f6')):
                die('DES fails test 3')
            obj=des.new(binascii.a2b_hex('0123456789abcdef'), des.MODE_CBC,
                        binascii.a2b_hex('fedcba9876543210'))
            s=obj.encrypt("7654321 Now is the time for \000\000\000\000")
            if (s!=binascii.a2b_hex("ccd173ffab2039f4acd8aefddfd8a1eb468e91157888ba681d269397f7fe62b4")):
                die('DES fails test 4')
            del obj,s

            # R. Rivest's test: see http://theory.lcs.mit.edu/~rivest/destest.txt
            x=binascii.a2b_hex('9474B8E8C73BCA7D')
            for i in range(0, 16):
                obj=des.new(x, des.MODE_ECB)
                if (i & 1): x=obj.decrypt(x)
                else: x=obj.encrypt(x)
            if x!=binascii.a2b_hex('1B1A2DDB4C642438'):
                die("DES fails Rivest's test")

            if verbose: print '  Verifying against test suite...'
            for entry in testdata.des:
                key,plain,cipher=entry
                key=binascii.a2b_hex(key)
                plain=binascii.a2b_hex(plain)
                cipher=binascii.a2b_hex(cipher)
                obj=des.new(key, des.MODE_ECB)
                ciphertext=obj.encrypt(plain)
                if (ciphertext!=cipher):
                    die('DES failed on entry '+`entry`)
            for entry in testdata.des_cbc:
                key, iv, plain, cipher=entry
                key, iv, cipher=binascii.a2b_hex(key),binascii.a2b_hex(iv),binascii.a2b_hex(cipher)
                obj1=des.new(key, des.MODE_CBC, iv)
                obj2=des.new(key, des.MODE_CBC, iv)
                ciphertext=obj1.encrypt(plain)
                if (ciphertext!=cipher):
                    die('DES CBC mode failed on entry '+`entry`)

    if 'des3' in args:
        ciph=exerciseBlockCipher('DES3', verbose)        # Triple DES
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.des3:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, ciph.MODE_ECB)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('DES3 failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        if verbose: print
                for entry in testdata.des3_cbc:
                    key, iv, plain, cipher=entry
                    key, iv, cipher=binascii.a2b_hex(key),binascii.a2b_hex(iv),binascii.a2b_hex(cipher)
                    obj1=ciph.new(key, ciph.MODE_CBC, iv)
                    obj2=ciph.new(key, ciph.MODE_CBC, iv)
                    ciphertext=obj1.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('DES3 CBC mode failed on entry '+`entry`)

    if 'idea' in args:
        ciph=exerciseBlockCipher('IDEA', verbose)       # IDEA block cipher
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.idea:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key, ciph.MODE_ECB)
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('IDEA failed on entry '+`entry`)

    if 'rc5' in args:
        # Ronald Rivest's RC5 algorithm
        ciph=exerciseBlockCipher('RC5', verbose)
        if (ciph!=None):
                if verbose: print '  Verifying against test suite...'
                for entry in testdata.rc5:
                    key,plain,cipher=entry
                    key=binascii.a2b_hex(key)
                    plain=binascii.a2b_hex(plain)
                    cipher=binascii.a2b_hex(cipher)
                    obj=ciph.new(key[4:], ciph.MODE_ECB,
                                 version =ord(key[0]),
                                 word_size=ord(key[1]),
                                 rounds  =ord(key[2]) )
                    ciphertext=obj.encrypt(plain)
                    if (ciphertext!=cipher):
                        die('RC5 failed on entry '+`entry`)
                        for i in ciphertext:
                            if verbose: print hex(ord(i)),
                        if verbose: print



