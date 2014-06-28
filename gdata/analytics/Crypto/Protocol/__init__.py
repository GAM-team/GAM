
"""Cryptographic protocols

Implements various cryptographic protocols.  (Don't expect to find
network protocols here.)

Crypto.Protocol.AllOrNothing   Transforms a message into a set of message
                               blocks, such that the blocks can be
                               recombined to get the message back.

Crypto.Protocol.Chaffing       Takes a set of authenticated message blocks
                               (the wheat) and adds a number of
                               randomly generated blocks (the chaff).
"""

__all__ = ['AllOrNothing', 'Chaffing']
__revision__ = "$Id: __init__.py,v 1.4 2003/02/28 15:23:21 akuchling Exp $"
