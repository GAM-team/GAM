"""Network diagnostics, version display, and usage functions."""

import os
import platform
import socket
import ssl
import struct
import sys

import arrow
import httplib2
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from importlib.metadata import version as lib_version
from urllib.parse import urlparse

from gamlib import api as API
from gamlib import settings as GC
from gamlib import state as GM
from gamlib import msgs as Msg
from gamlib import verlibs

from gam.constants import (
    FN_GAMCOMMANDS_TXT, GAM, GAM_URL, GAM_WIKI,
    GOOGLE_TIMECHECK_LOCATION, MAX_LOCAL_GOOGLE_TIME_OFFSET, NETWORK_ERROR_RC,
    SECONDS_PER_DAY, SECONDS_PER_HOUR, SECONDS_PER_MINUTE,
)
from util.args import getArgument, getString, todaysTime
from util.output import ISOformatTimeStamp
from util.display import printBlankLine, printKeyValueList
from util.errors import unknownArgumentExit
from util.output import (
    createGreenText, createRedText, createYellowText,
    flushStdout, stderrWarningMsg, systemErrorExit, writeStdout,
)
from util.api import doGAMCheckForUpdates, getHttpObj, getService, handleServerError, waitOnFailure
from gam.constants import GAM_USER_AGENT, __author__, __version__
from gam.var import Cmd, Ent

# gam.__init__ attributes that can't be imported at module level
# (connection.py is imported BY __init__.py during init)


# --- Constants ---

def _buildTimeOffsetUnits():
  return [('day', SECONDS_PER_DAY), ('hour', SECONDS_PER_HOUR),
          ('minute', SECONDS_PER_MINUTE), ('second', 1)]

MACOS_CODENAMES = {
  10: {
    6:  'Snow Leopard',
    7:  'Lion',
    8:  'Mountain Lion',
    9:  'Mavericks',
    10: 'Yosemite',
    11: 'El Capitan',
    12: 'Sierra',
    13: 'High Sierra',
    14: 'Mojave',
    15: 'Catalina',
    16: 'Big Sur'
    },
  11: 'Big Sur',
  12: 'Monterey',
  13: 'Ventura',
  14: 'Sonoma',
  15: 'Sequoia',
  26: 'Tahoe',
  }

# --- Functions ---

def getLocalGoogleTimeOffset(testLocation=None):
  if testLocation is None:
    testLocation = GOOGLE_TIMECHECK_LOCATION
  TIME_OFFSET_UNITS = _buildTimeOffsetUnits()
  # If local time is well off, it breaks https because the server certificate will be seen as too old or new and thus invalid; http doesn't have that issue.
  # Try with http first, if time is close (<MAX_LOCAL_GOOGLE_TIME_OFFSET seconds), retry with https as it should be OK
  httpObj = getHttpObj()
  for prot in ['http', 'https']:
    try:
      headerData = httpObj.request(f'{prot}://'+testLocation, 'HEAD')
      googleUTC = arrow.Arrow.strptime(headerData[0]['date'], '%a, %d %b %Y %H:%M:%S %Z', tzinfo='UTC')
    except (httplib2.HttpLib2Error, RuntimeError) as e:
      handleServerError(e)
    except httplib2.socks.HTTPError as e:
      # If user has specified an HTTPS proxy, the http request will probably fail as httplib2
      # turns a GET into a CONNECT which is not valid for an http address
      if prot == 'http':
        continue
      handleServerError(e)
    except (ValueError, KeyError):
      if prot == 'http':
        continue
      systemErrorExit(NETWORK_ERROR_RC, Msg.INVALID_HTTP_HEADER.format(str(headerData)))
    offset = remainder = int(abs((arrow.utcnow()-googleUTC).total_seconds()))
    if offset < MAX_LOCAL_GOOGLE_TIME_OFFSET and prot == 'http':
      continue
    timeoff = []
    for tou in TIME_OFFSET_UNITS:
      uval, remainder = divmod(remainder, tou[1])
      if uval:
        timeoff.append(f'{uval} {tou[0]}{"s" if uval != 1 else ""}')
    if not timeoff:
      timeoff.append(Msg.LESS_THAN_1_SECOND)
    nicetime = ', '.join(timeoff)
    return (offset, nicetime)

def _getServerTLSUsed(location):
  url = 'https://'+location
  _, netloc, _, _, _, _ = urlparse(url)
  conn = 'https:'+netloc
  httpObj = getHttpObj()
  triesLimit = 5
  for n in range(1, triesLimit+1):
    try:
      httpObj.request(url, headers={'user-agent': GAM_USER_AGENT})
      cipher_name, tls_ver, _ = httpObj.connections[conn].sock.cipher()
      return tls_ver, cipher_name
    except (httplib2.HttpLib2Error, RuntimeError) as e:
      if n != triesLimit:
        httpObj.connections = {}
        waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
        continue
      handleServerError(e)

def getOSPlatform():
  myos = platform.system()
  if myos == 'Linux':
    import distro
    pltfrm = ' '.join(distro.linux_distribution(full_distribution_name=False)).title()
  elif myos == 'Windows':
    pltfrm = ' '.join(platform.win32_ver())
  elif myos == 'Darwin':
    myos = 'macOS'
    mac_ver = platform.mac_ver()[0]
    major_ver = int(mac_ver.split('.')[0]) # macver 10.14.6 == major_ver 10
    minor_ver = int(mac_ver.split('.')[1]) # macver 10.14.6 == minor_ver 14
    if major_ver == 10:
      codename = MACOS_CODENAMES[major_ver].get(minor_ver, '')
    else:
      codename = MACOS_CODENAMES.get(major_ver, '')
    pltfrm = ' '.join([codename, mac_ver])
  else:
    pltfrm = platform.platform()
  return f'{myos} {pltfrm}'

def inspect_untrusted_cert(url):
  """Bypasses validation momentarily to extract the untrusted Issuer."""
  parsed = urlparse(url if '://' in url else f'https://{url}')
  host = parsed.hostname
  port = parsed.port or 443
  # Create an unverified context purely for diagnostic extraction
  ctx = ssl.create_default_context()
  ctx.check_hostname = False
  ctx.verify_mode = ssl.CERT_NONE
  try:
    with socket.create_connection((host, port), timeout=5) as sock:
      with ctx.wrap_socket(sock, server_hostname=host) as ssock:
        der_cert = ssock.getpeercert(binary_form=True)
        cert = x509.load_der_x509_certificate(der_cert, default_backend())
        issuer = cert.issuer.rfc4514_string()
        subject = cert.subject.rfc4514_string()
        try:
          san_ext = cert.extensions.get_extension_for_oid(x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
          # Loop through the list of SANs (DNS names, IP addresses, etc.)
          sans = [str(name.value) for name in san_ext.value]
          san_str = ", ".join(sans)
        except x509.ExtensionNotFound:
          san_str = "None"
        return f"Untrusted Issuer: {issuer}\n    Server Subject: {subject}\n    SANs: {san_str}"
  except Exception as e:
    return f"Failed to retrieve diagnostic certificate: {e}"

# gam checkconnection
def doCheckConnection():

  def check_host(host):
    nonlocal try_count, okay, not_okay, success_count
    try_count += 1
    dns_err = None
    ip = 'unknown'
    try:
      ip = socket.getaddrinfo(host, None)[0][-1][0] # works with ipv6
    except socket.gaierror as e:
      dns_err = f'{not_okay}\n   DNS failure: {str(e)}\n'
    except Exception as e:
      dns_err = f'{not_okay}\n   Unknown DNS failure: {str(e)}\n'
    check_line = f'Checking {host} ({ip}) ({try_count})...'
    writeStdout(f'{check_line:<100}')
    flushStdout()
    if dns_err:
      writeStdout(dns_err)
      return
    gen_firewall = 'You probably have security software or a firewall on your machine or network that is preventing GAM from making Internet connections. Check your network configuration or try running GAM on a hotspot or home network to see if the problem exists only on your organization\'s network.'
    try:
      if host.startswith('http'):
        url = host
      else:
        url = f'https://{host}:443/'
      httpObj.request(url, 'HEAD', headers=headers)
      success_count += 1
      writeStdout(f'{okay}\n')
    except ConnectionRefusedError:
      writeStdout(f'{not_okay}\n    Connection refused. {gen_firewall}\n')
    except ConnectionResetError:
      writeStdout(f'{not_okay}\n    Connection reset by peer. {gen_firewall}\n')
    except httplib2.error.ServerNotFoundError:
      writeStdout(f'{not_okay}\n    Failed to find server. Your DNS is probably misconfigured.\n')
    except ssl.SSLCertVerificationError as e:
      diag_info = inspect_untrusted_cert(host)
      # e.verify_message contains the specific OpenSSL error string
      writeStdout(f'{not_okay}\n    Certificate verification failed: {e.verify_message}\n    Diagnostic Info:\n   {diag_info}\nIf you are behind a firewall / proxy server that does TLS / SSL inspection you may need to point GAM at your certificate authority file by setting cacerts_pem = /path/to/your/certauth.pem in gam.cfg.\n')
    except ssl.SSLError as e:
      if e.reason == 'SSLV3_ALERT_HANDSHAKE_FAILURE':
        writeStdout(f'{not_okay}\n    GAM expects to connect with TLS 1.3 or newer and that failed. If your firewall / proxy server is not compatible with TLS 1.3 then you can tell GAM to allow TLS 1.2 by setting tls_min_version = TLSv1.2 in gam.cfg.\n')
      elif e.reason == 'CERTIFICATE_VERIFY_FAILED':
        writeStdout(f'{not_okay}\n    Certificate verification failed. If you are behind a firewall / proxy server that does TLS / SSL inspection you may need to point GAM at your certificate authority file by setting cacerts_pem = /path/to/your/certauth.pem in gam.cfg.\n')
      elif e.strerror and e.strerror.startswith('TLS/SSL connection has been closed\n'):
        writeStdout(f'{not_okay}\n    TLS connection was closed. {gen_firewall}\n')
      else:
        writeStdout(f'{not_okay}\n    {str(e)}\n')
    except TimeoutError:
      writeStdout(f'{not_okay}\n    Timed out trying to connect to host\n')
    except Exception as e:
      writeStdout(f'{not_okay}\n    {str(e)}\n')

  try_count = 0
  httpObj = getHttpObj(timeout=30)
  httpObj.follow_redirects = False
  headers = {'user-agent': GAM_USER_AGENT}
  okay = createGreenText('OK')
  not_okay = createRedText('ERROR')
  success_count = 0
  initial_hosts = ['api.github.com',
           'raw.githubusercontent.com',
           'accounts.google.com',
           'oauth2.googleapis.com',
           'www.googleapis.com']
  for host in initial_hosts:
    check_host(host)
  api_hosts = ['apps-apis.google.com',
               'www.google.com']
  for host in api_hosts:
    check_host(host)
  # For v2 discovery APIs, GAM gets discovery file from <api>.googleapis.com so
  # add those domains.
  disc_hosts = []
  for api, config in API._INFO.items():
    if config.get('v2discovery') and not config.get('localdiscovery'):
      if mapped_api := config.get('mappedAPI'):
        api = mapped_api
      host = f'{api}.googleapis.com'
      if host not in disc_hosts:
        disc_hosts.append(host)
  for host in disc_hosts:
    check_host(host)
  checked_hosts = initial_hosts + api_hosts + disc_hosts
  # now we need to "build" each API and check it's base URL host
  # if we haven't already. This may not be any hosts at all but
  # to ensure we are checking all hosts GAM may use we should
  # keep this.
  for api in API._INFO:
    svc = getService(api, httpObj)
    base_url = svc._rootDesc.get('baseUrl')
    parsed_base_url = urlparse(base_url)
    base_host = parsed_base_url.netloc
    if base_host not in checked_hosts:
      writeStdout(f'Checking {base_host} for {api}\n')
      check_host(base_host)
      checked_hosts.append(base_host)
  if success_count == try_count:
    writeStdout(createGreenText('All hosts passed!\n'))
  else:
    systemErrorExit(3, createYellowText('Some hosts failed to connect! Please follow the recommendations for those hosts to correct any issues and try again.'))

# gam comment
def doComment():
  writeStdout(Cmd.QuotedArgumentList(Cmd.Remaining())+'\n')

# gam version [check|checkrc|simple|extended] [timeoffset] [nooffseterror] [location <HostName>]
def doVersion(checkForArgs=True):
  forceCheck = 0
  extended = noOffsetError = timeOffset = simple = False
  testLocation = GOOGLE_TIMECHECK_LOCATION
  if checkForArgs:
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if myarg == 'check':
        forceCheck = 1
      elif myarg == 'checkrc':
        forceCheck = -1
      elif myarg == 'simple':
        simple = True
      elif myarg == 'extended':
        extended = timeOffset = True
      elif myarg == 'timeoffset':
        timeOffset = True
      elif myarg == 'nooffseterror':
        noOffsetError = True
      elif myarg == 'location':
        testLocation = getString(Cmd.OB_HOST_NAME)
      else:
        unknownArgumentExit()
  if simple:
    writeStdout(__version__)
    return
  writeStdout(f'{GAM} {__version__} - {GAM_URL} - {GM.Globals[GM.GAM_TYPE]}\n'
               f'{__author__}\n'
               f'Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]} {struct.calcsize("P")*8}-bit {sys.version_info[3]}\n'
               f'{getOSPlatform()} {platform.machine()}\n'
               f'Path: {GM.Globals[GM.GAM_PATH]}\n'
               f'{Ent.Singular(Ent.CONFIG_FILE)}: {GM.Globals[GM.GAM_CFG_FILE]}, {Ent.Singular(Ent.SECTION)}: {GM.Globals[GM.GAM_CFG_SECTION_NAME]}, '
               f'{GC.CUSTOMER_ID}: {GC.Values[GC.CUSTOMER_ID]}, {GC.DOMAIN}: {GC.Values[GC.DOMAIN]}\n'
               f'Time: {ISOformatTimeStamp(todaysTime())}\n'
               )
  if sys.platform.startswith('win') and str(struct.calcsize('P')*8).find('32') != -1 and platform.machine().find('64') != -1:
    printKeyValueList([Msg.UPDATE_GAM_TO_64BIT])
  if timeOffset:
    offsetSeconds, offsetFormatted = getLocalGoogleTimeOffset(testLocation)
    printKeyValueList([Msg.YOUR_SYSTEM_TIME_DIFFERS_FROM_GOOGLE.format(testLocation, offsetFormatted)])
    if offsetSeconds > MAX_LOCAL_GOOGLE_TIME_OFFSET:
      if not noOffsetError:
        systemErrorExit(NETWORK_ERROR_RC, Msg.PLEASE_CORRECT_YOUR_SYSTEM_TIME)
      stderrWarningMsg(Msg.PLEASE_CORRECT_YOUR_SYSTEM_TIME)
  if forceCheck:
    doGAMCheckForUpdates(forceCheck)
  if extended:
    printKeyValueList([ssl.OPENSSL_VERSION])
    tls_ver, cipher_name = _getServerTLSUsed(testLocation)
    for lib in verlibs.GAM_VER_LIBS:
      try:
        writeStdout(f'{lib} {lib_version(lib)}\n')
      except:
        pass
    printKeyValueList([f'{testLocation} connects using {tls_ver} {cipher_name}'])

# gam help
def doUsage():
  printBlankLine()
  doVersion(checkForArgs=False)
  writeStdout(Msg.HELP_SYNTAX.format(os.path.join(GM.Globals[GM.GAM_PATH], FN_GAMCOMMANDS_TXT)))
  writeStdout(Msg.HELP_WIKI.format(GAM_WIKI))
