from typing import Union, Optional, List
from . import exception, rdataclass, name, rdatatype

import socket
_gethostbyname = socket.gethostbyname
class NXDOMAIN(exception.DNSException):
    ...
def query(qname : str, rdtype : Union[int,str] = 0, rdclass : Union[int,str] = 0,
          tcp=False, source=None, raise_on_no_answer=True,
          source_port=0):
    ...
class LRUCache:
    def __init__(self, max_size=1000):
        ...
    def get(self, key):
        ...
    def put(self, key, val):
        ...
class Answer:
    def __init__(self, qname, rdtype, rdclass, response,
                 raise_on_no_answer=True):
        ...
def zone_for_name(name, rdclass : int = rdataclass.IN, tcp=False, resolver : Optional[Resolver] = None):
    ...

class Resolver:
    def __init__(self, configure):
        self.nameservers : List[str]
    def query(self, qname : str, rdtype : Union[int,str] = rdatatype.A, rdclass : Union[int,str] = rdataclass.IN,
              tcp : bool = False, source : Optional[str] = None, raise_on_no_answer=True, source_port : int = 0):
        ...
