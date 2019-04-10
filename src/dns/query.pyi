from typing import Optional, Union, Dict, Generator, Any
from . import message, tsig, rdatatype, rdataclass, name, message
def tcp(q : message.Message, where : str, timeout : float = None, port=53, af : Optional[int] = None, source : Optional[str] = None, source_port : int = 0,
        one_rr_per_rrset=False) -> message.Message:
    pass

def xfr(where : None, zone : Union[name.Name,str], rdtype=rdatatype.AXFR, rdclass=rdataclass.IN,
        timeout : Optional[float] =None, port=53, keyring : Optional[Dict[name.Name, bytes]] =None, keyname : Union[str,name.Name]=None, relativize=True,
        af : Optional[int] =None, lifetime : Optional[float]=None, source : Optional[str] =None, source_port=0, serial=0,
        use_udp=False, keyalgorithm=tsig.default_algorithm) -> Generator[Any,Any,message.Message]:
    pass

def udp(q : message.Message, where : str, timeout : Optional[float] = None, port=53, af : Optional[int] = None, source : Optional[str] = None, source_port=0,
        ignore_unexpected=False, one_rr_per_rrset=False) -> message.Message:
    ...
