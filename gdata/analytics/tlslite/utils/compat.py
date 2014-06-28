"""Miscellaneous functions to mask Python version differences."""

import sys
import os

if sys.version_info < (2,2):
    raise AssertionError("Python 2.2 or later required")

if sys.version_info < (2,3):

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

        def __iter__(self):
            return iter(set.values.keys())


if os.name != "java":

    import array
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

    import math
    def numBits(n):
        if n==0:
            return 0
        s = "%x" % n
        return ((len(s)-1)*4) + \
        {'0':0, '1':1, '2':2, '3':2,
         '4':3, '5':3, '6':3, '7':3,
         '8':4, '9':4, 'a':4, 'b':4,
         'c':4, 'd':4, 'e':4, 'f':4,
         }[s[0]]
        return int(math.floor(math.log(n, 2))+1)

    BaseException = Exception
    import sys
    import traceback
    def formatExceptionTrace(e):
        newStr = "".join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
        return newStr

else:
    #Jython 2.1 is missing lots of python 2.3 stuff,
    #which we have to emulate here:
    #NOTE: JYTHON SUPPORT NO LONGER WORKS, DUE TO USE OF GENERATORS.
    #THIS CODE IS LEFT IN SO THAT ONE JYTHON UPDATES TO 2.2, IT HAS A
    #CHANCE OF WORKING AGAIN.

    import java
    import jarray

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

    #Adjust the string to an array of bytes
    def stringToJavaByteArray(s):
        bytes = jarray.zeros(len(s), 'b')
        for count, c in enumerate(s):
            x = ord(c)
            if x >= 128: x -= 256
            bytes[count] = x
        return bytes

    BaseException = java.lang.Exception
    import sys
    import traceback
    def formatExceptionTrace(e):
        newStr = "".join(traceback.format_exception(sys.exc_type, sys.exc_value, sys.exc_traceback))
        return newStr