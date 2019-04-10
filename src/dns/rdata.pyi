from typing import Dict, Tuple, Any, Optional
from .name import Name
class Rdata:
    def __init__(self):
        self.address : str
    def to_wire(self, file, compress : Optional[Dict[Name,int]], origin : Optional[Name]) -> bytes:
        ...
    @classmethod
    def from_text(cls, rdclass : int, rdtype : int, tok, origin=None, relativize=True):
        ...
_rdata_modules : Dict[Tuple[Any,Rdata],Any]

def from_text(rdclass : int, rdtype : int, tok : Optional[str], origin : Optional[Name] = None, relativize : bool = True):
    ...

def from_wire(rdclass : int, rdtype : int, wire : bytes, current : int, rdlen : int, origin : Optional[Name] = None):
    ...
