
class IntegrationHelper:

    def __init__(self,
              username=None, password=None, sharedKey=None,
              certChain=None, privateKey=None,
              cryptoID=None, protocol=None,
              x509Fingerprint=None,
              x509TrustList=None, x509CommonName=None,
              settings = None):

        self.username = None
        self.password = None
        self.sharedKey = None
        self.certChain = None
        self.privateKey = None
        self.checker = None

        #SRP Authentication
        if username and password and not \
                (sharedKey or certChain or privateKey):
            self.username = username
            self.password = password

        #Shared Key Authentication
        elif username and sharedKey and not \
                (password or certChain or privateKey):
            self.username = username
            self.sharedKey = sharedKey

        #Certificate Chain Authentication
        elif certChain and privateKey and not \
                (username or password or sharedKey):
            self.certChain = certChain
            self.privateKey = privateKey

        #No Authentication
        elif not password and not username and not \
                sharedKey and not certChain and not privateKey:
            pass

        else:
            raise ValueError("Bad parameters")

        #Authenticate the server based on its cryptoID or fingerprint
        if sharedKey and (cryptoID or protocol or x509Fingerprint):
            raise ValueError("Can't use shared keys with other forms of"\
                             "authentication")

        self.checker = Checker(cryptoID, protocol, x509Fingerprint,
                               x509TrustList, x509CommonName)
        self.settings = settings