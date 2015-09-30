"""Classes for reading/writing binary data (such as TLS records)."""

from compat import *

class Writer:
    def __init__(self, length=0):
        #If length is zero, then this is just a "trial run" to determine length
        self.index = 0
        self.bytes = createByteArrayZeros(length)

    def add(self, x, length):
        if self.bytes:
            newIndex = self.index+length-1
            while newIndex >= self.index:
                self.bytes[newIndex] = x & 0xFF
                x >>= 8
                newIndex -= 1
        self.index += length

    def addFixSeq(self, seq, length):
        if self.bytes:
            for e in seq:
                self.add(e, length)
        else:
            self.index += len(seq)*length

    def addVarSeq(self, seq, length, lengthLength):
        if self.bytes:
            self.add(len(seq)*length, lengthLength)
            for e in seq:
                self.add(e, length)
        else:
            self.index += lengthLength + (len(seq)*length)


class Parser:
    def __init__(self, bytes):
        self.bytes = bytes
        self.index = 0

    def get(self, length):
        if self.index + length > len(self.bytes):
            raise SyntaxError()
        x = 0
        for count in range(length):
            x <<= 8
            x |= self.bytes[self.index]
            self.index += 1
        return x

    def getFixBytes(self, lengthBytes):
        bytes = self.bytes[self.index : self.index+lengthBytes]
        self.index += lengthBytes
        return bytes

    def getVarBytes(self, lengthLength):
        lengthBytes = self.get(lengthLength)
        return self.getFixBytes(lengthBytes)

    def getFixList(self, length, lengthList):
        l = [0] * lengthList
        for x in range(lengthList):
            l[x] = self.get(length)
        return l

    def getVarList(self, length, lengthLength):
        lengthList = self.get(lengthLength)
        if lengthList % length != 0:
            raise SyntaxError()
        lengthList = int(lengthList/length)
        l = [0] * lengthList
        for x in range(lengthList):
            l[x] = self.get(length)
        return l

    def startLengthCheck(self, lengthLength):
        self.lengthCheck = self.get(lengthLength)
        self.indexCheck = self.index

    def setLengthCheck(self, length):
        self.lengthCheck = length
        self.indexCheck = self.index

    def stopLengthCheck(self):
        if (self.index - self.indexCheck) != self.lengthCheck:
            raise SyntaxError()

    def atLengthCheck(self):
        if (self.index - self.indexCheck) < self.lengthCheck:
            return False
        elif (self.index - self.indexCheck) == self.lengthCheck:
            return True
        else:
            raise SyntaxError()