"""Miscellaneous functions to mask Python/Jython differences."""

import os
import sha

if os.name != "java":
    BaseException = Exception

    from sets import Set
    import array
    import math

    def createByteArraySequence(seq):
        return array.array('B', seq)
    def createByteArrayZeros(howMany):
        return array.array('B', [0] * howMany)
    def concatArrays(a1, a2):
        return a1+a2

    def bytesToString(bytes):
        return bytes.tostring()

    def stringToBytes(s):
        bytes = createByteArrayZeros(0)
        bytes.fromstring(s)
        return bytes

    def numBits(n):
        if n==0:
            return 0
        return int(math.floor(math.log(n, 2))+1)

    class CertChainBase: pass
    class SelfTestBase: pass
    class ReportFuncBase: pass

    #Helper functions for working with sets (from Python 2.3)
    def iterSet(set):
        return iter(set)

    def getListFromSet(set):
        return list(set)

    #Factory function for getting a SHA1 object
    def getSHA1(s):
        return sha.sha(s)

    import sys
    import traceback

    def formatExceptionTrace(e):
        newStr = "".join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
        return newStr

else:
    #Jython 2.1 is missing lots of python 2.3 stuff,
    #which we have to emulate here:
    import java
    import jarray

    BaseException = java.lang.Exception

    def createByteArraySequence(seq):
        if isinstance(seq, type("")): #If it's a string, convert
            seq = [ord(c) for c in seq]
        return jarray.array(seq, 'h') #use short instead of bytes, cause bytes are signed
    def createByteArrayZeros(howMany):
        return jarray.zeros(howMany, 'h') #use short instead of bytes, cause bytes are signed
    def concatArrays(a1, a2):
        l = list(a1)+list(a2)
        return createByteArraySequence(l)

    #WAY TOO SLOW - MUST BE REPLACED------------
    def bytesToString(bytes):
        return "".join([chr(b) for b in bytes])

    def stringToBytes(s):
        bytes = createByteArrayZeros(len(s))
        for count, c in enumerate(s):
            bytes[count] = ord(c)
        return bytes
    #WAY TOO SLOW - MUST BE REPLACED------------

    def numBits(n):
        if n==0:
            return 0
        n= 1L * n; #convert to long, if it isn't already
        return n.__tojava__(java.math.BigInteger).bitLength()

    #This properly creates static methods for Jython
    class staticmethod:
        def __init__(self, anycallable): self.__call__ = anycallable

    #Properties are not supported for Jython
    class property:
        def __init__(self, anycallable): pass

    #True and False have to be specially defined
    False = 0
    True = 1

    class StopIteration(Exception): pass

    def enumerate(collection):
        return zip(range(len(collection)), collection)

    class Set:
        def __init__(self, seq=None):
            self.values = {}
            if seq:
                for e in seq:
                    self.values[e] = None

        def add(self, e):
            self.values[e] = None

        def discard(self, e):
            if e in self.values.keys():
                del(self.values[e])

        def union(self, s):
            ret = Set()
            for e in self.values.keys():
                ret.values[e] = None
            for e in s.values.keys():
                ret.values[e] = None
            return ret

        def issubset(self, other):
            for e in self.values.keys():
                if e not in other.values.keys():
                    return False
            return True

        def __nonzero__( self):
            return len(self.values.keys())

        def __contains__(self, e):
            return e in self.values.keys()

    def iterSet(set):
        return set.values.keys()

    def getListFromSet(set):
        return set.values.keys()

    """
    class JCE_SHA1:
        def __init__(self, s=None):
            self.md = java.security.MessageDigest.getInstance("SHA1")
            if s:
                self.update(s)

        def update(self, s):
            self.md.update(s)

        def copy(self):
            sha1 = JCE_SHA1()
            sha1.md = self.md.clone()
            return sha1

        def digest(self):
            digest = self.md.digest()
            bytes = jarray.zeros(20, 'h')
            for count in xrange(20):
                x = digest[count]
                if x < 0: x += 256
                bytes[count] = x
            return bytes
    """

    #Factory function for getting a SHA1 object
    #The JCE_SHA1 class is way too slow...
    #the sha.sha object we use instead is broken in the jython 2.1
    #release, and needs to be patched
    def getSHA1(s):
        #return JCE_SHA1(s)
        return sha.sha(s)


    #Adjust the string to an array of bytes
    def stringToJavaByteArray(s):
        bytes = jarray.zeros(len(s), 'b')
        for count, c in enumerate(s):
            x = ord(c)
            if x >= 128: x -= 256
            bytes[count] = x
        return bytes

    import sys
    import traceback

    def formatExceptionTrace(e):
        newStr = "".join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
        return newStr
