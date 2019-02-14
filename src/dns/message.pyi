from typing import Optional, Dict, List, Tuple, Union
from . import name, rrset, tsig, rdatatype, entropy, edns, rdataclass
import hmac

class Message:
    def to_wire(self, origin : Optional[name.Name]=None, max_size=0, **kw) -> bytes:
        ...
    def find_rrset(self, section : List[rrset.RRset], name : name.Name, rdclass : int, rdtype : int,
                   covers=rdatatype.NONE, deleting : Optional[int]=None, create=False,
                   force_unique=False) -> rrset.RRset:
        ...
    def __init__(self, id : Optional[int] =None) -> None:
        self.id : int
        self.flags = 0
        self.question : List[rrset.RRset] = []
        self.answer : List[rrset.RRset] = []
        self.authority : List[rrset.RRset] = []
        self.additional : List[rrset.RRset] = []
        self.edns = -1
        self.ednsflags = 0
        self.payload = 0
        self.options : List[edns.Option] = []
        self.request_payload = 0
        self.keyring = None
        self.keyname = None
        self.keyalgorithm = tsig.default_algorithm
        self.request_mac = b''
        self.other_data = b''
        self.tsig_error = 0
        self.fudge = 300
        self.original_id = self.id
        self.mac = b''
        self.xfr = False
        self.origin = None
        self.tsig_ctx = None
        self.had_tsig = False
        self.multi = False
        self.first = True
        self.index : Dict[Tuple[rrset.RRset, name.Name, int, int, Union[int,str], int], rrset.RRset] = {}
def from_text(a : str) -> Message:
    ...

def from_wire(wire, keyring : Optional[Dict[name.Name,bytes]] = None, request_mac = b'', xfr=False, origin=None,
              tsig_ctx : Optional[hmac.HMAC] = None, multi=False, first=True,
              question_only=False, one_rr_per_rrset=False,
              ignore_trailing=False) -> Message:
    ...
def make_response(query : Message, recursion_available=False, our_payload=8192,
                  fudge=300) -> Message:
    ...

def make_query(qname : Union[name.Name,str], rdtype : Union[str,int], rdclass : Union[int,str] =rdataclass.IN, use_edns : Optional[bool] = None,
               want_dnssec=False, ednsflags : Optional[int] = None, payload : Optional[int] = None,
               request_payload : Optional[int] = None, options : Optional[List[edns.Option]] = None) -> Message:
    ...
