"""GAM site verification and web resource management."""

import json
import sys

from gamlib import glaction
from gamlib import glapi as API
from gamlib import glcfg as GC
from gamlib import glclargs
from gamlib import glentity
from gamlib import glgapi as GAPI
from gamlib import glglobals as GM
from gamlib import glindent
from gamlib import glmsgs as Msg

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


def _getMain():
  return sys.modules['gam']

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

from urllib.parse import unquote
from urllib.parse import urlencode

def deprecatedUserSites(_):
  _getMain().deprecatedCommandExit()

def deprecatedDomainSites():
  _getMain().deprecatedCommandExit()

def doCreateSiteVerification():
  verif = _getMain().buildGAPIObject(API.SITEVERIFICATION)
  a_domain = _getMain().getString(Cmd.OB_DOMAIN_NAME)
  _getMain().checkForExtraneousArguments()
  txt_record = _getMain().callGAPI(verif.webResource(), 'getToken',
                        body={'site': {'type': 'INET_DOMAIN', 'identifier': a_domain},
                              'verificationMethod': 'DNS_TXT'})
  _getMain().printKeyValueList(['TXT Record Name ', a_domain])
  _getMain().printKeyValueList(['TXT Record Value', txt_record['token']])
  _getMain().printBlankLine()
  cname_record = _getMain().callGAPI(verif.webResource(), 'getToken',
                          body={'site': {'type': 'INET_DOMAIN', 'identifier': a_domain},
                                'verificationMethod': 'DNS_CNAME'})
  cname_token = cname_record['token']
  cname_list = cname_token.split(' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  _getMain().printKeyValueList(['CNAME Record Name ', f'{cname_subdomain}.{a_domain}'])
  _getMain().printKeyValueList(['CNAME Record Value', cname_value])
  _getMain().printBlankLine()
  webserver_file_record = _getMain().callGAPI(verif.webResource(), 'getToken',
                                   body={'site': {'type': 'SITE', 'identifier': f'http://{a_domain}/'},
                                         'verificationMethod': 'FILE'})
  webserver_file_token = webserver_file_record['token']
  _getMain().printKeyValueList(['Saving web server verification file to', webserver_file_token])
  _getMain().writeFile(webserver_file_token, f'google-site-verification: {webserver_file_token}', continueOnError=True)
  _getMain().printKeyValueList(['Verification File URL', f'http://{a_domain}/{webserver_file_token}'])
  _getMain().printBlankLine()
  webserver_meta_record = _getMain().callGAPI(verif.webResource(), 'getToken',
                                   body={'site': {'type': 'SITE', 'identifier': f'http://{a_domain}/'},
                                         'verificationMethod': 'META'})
  _getMain().printKeyValueList(['Meta URL', f'//{a_domain}/'])
  _getMain().printKeyValueList(['Meta HTML Header Data', webserver_meta_record['token']])
  _getMain().printBlankLine()

def _showSiteVerificationInfo(site, i=0, count=0):
  _getMain().printKeyValueListWithCount(['Site', site['site']['identifier']], i, count)
  Ind.Increment()
  _getMain().printKeyValueList(['ID', unquote(site['id'])])
  _getMain().printKeyValueList(['Type', site['site']['type']])
  _getMain().printKeyValueList(['All Owners', None])
  if 'owners' in site:
    Ind.Increment()
    for owner in sorted(site['owners']):
      _getMain().printKeyValueList([owner])
    Ind.Decrement()
  Ind.Decrement()

DNS_ERROR_CODES_MAP = {
  1: 'DNS Query Format Error',
  2: 'Server failed to complete the DNS request',
  3: 'Domain name does not exist',
  4: 'Function not implemented',
  5: 'The server refused to answer for the query',
  6: 'Name that should not exist, does exist',
  7: 'RRset that should not exist, does exist',
  8: 'Server not authoritative for the zone',
  9: 'Name not in zone'
  }

# gam update verify|verification <DomainName> cname|txt|text|file|site
def doUpdateSiteVerification():
  def showDNSrecords():
    try:
      verify_data = _getMain().callGAPI(verif.webResource(), 'getToken',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_PARAMETER],
                             body=body)
    except (GAPI.badRequest, GAPI.invalidParameter) as e:
      _getMain().printKeyValueList([_getMain().ERROR, str(e)])
      return
    _getMain().printKeyValueList(['Method', verify_data['method']])
    if verify_data['method'] in {'DNS_CNAME', 'DNS_TXT'}:
      if verify_data['method'] == 'DNS_CNAME':
        cname_subdomain, cname_target = verify_data['token'].split(' ')
        query_params = {'name': f'{cname_subdomain}.{a_domain}', 'type': 'cname'}
        _getMain().printKeyValueList(['Expected Record',
                           f'{query_params["name"]} IN CNAME {cname_target}'])
      else:
        query_params = {'name': f'{a_domain}', 'type': 'txt'}
        _getMain().printKeyValueList(['Expected Record',
                           f'{query_params["name"]} IN TXT {verify_data["token"]}'])
      _, content = _getMain().getHttpObj().request('https://dns.google/resolve?' + urlencode(query_params), 'GET')
      try:
        result = json.loads(content.decode(_getMain().UTF8))
        status = result['Status']
        if status == 0 and 'Answer' in result:
          if verify_data['method'] == 'DNS_CNAME':
            _getMain().printKeyValueList(['DNS      Record',
                               f'{result["Answer"][0]["name"].rstrip(".")} IN CNAME {result["Answer"][0]["data"]}'])
          else:
            found = False
            for answer in result['Answer']:
              answer['data'] = answer['data'].strip('"')
              if answer['data'].startswith('google-site-verification'):
                found = True
                _getMain().printKeyValueList(['DNS      Record',
                                   f'{answer["name"].rstrip(".")} IN TXT {answer["data"]}'])
            if not found:
              _getMain().printKeyValueList(['DNS      Record', 'No matching record found'])
        elif status == 0:
          _getMain().systemErrorExit(_getMain().NETWORK_ERROR_RC, Msg.DOMAIN_NOT_FOUND_IN_DNS)
        else:
          _getMain().systemErrorExit(_getMain().NETWORK_ERROR_RC, DNS_ERROR_CODES_MAP.get(status, f'Unknown error {status}'))
      except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
        _getMain().systemErrorExit(_getMain().INVALID_JSON_RC, Msg.INVALID_JSON_INFORMATION)

  verif = _getMain().buildGAPIObject(API.SITEVERIFICATION)
  a_domain = _getMain().getString(Cmd.OB_DOMAIN_NAME)
  verificationMethod = _getMain().getChoice(_getMain().SITEVERIFICATION_METHOD_CHOICE_MAP, mapChoice=True)
  if verificationMethod in {'DNS_TXT', 'DNS_CNAME'}:
    verify_type = 'INET_DOMAIN'
    identifier = a_domain
    showDNS = True
  else:
    verify_type = 'SITE'
    identifier = f'http://{a_domain}/'
    showDNS = False
  _getMain().checkForExtraneousArguments()
  body = {'site': {'type': verify_type, 'identifier': identifier},
          'verificationMethod': verificationMethod}
  try:
    verify_result = _getMain().callGAPI(verif.webResource(), 'insert',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_PARAMETER],
                             verificationMethod=verificationMethod, body=body)
  except GAPI.badRequest as e:
    _getMain().printKeyValueList([_getMain().ERROR, str(e)])
    if showDNS:
      showDNSrecords()
    return
  except GAPI.invalidParameter as e:
    _getMain().printKeyValueList([_getMain().ERROR, str(e)])
    return
  _getMain().printKeyValueList(['Verified!'])
  if showDNS:
    showDNSrecords()
  _showSiteVerificationInfo(verify_result)
  _getMain().printKeyValueList([Msg.YOU_CAN_ADD_DOMAIN_TO_ACCOUNT.format(a_domain, GC.Values[GC.DOMAIN])])

PROFILE_ACCOUNT_TYPE_MAP = {
  'locationgroup': 'LOCATION_GROUP',
  'organization': 'ORGANIZATION',
  'personal': 'PERSONAL',
  'usergroup': 'USER_GROUP',
  }

# gam <UserTypeEntity> show businessprofileaccounts
#	[type locationgroup|organization|personal|usergroup]
# gam <UserTypeEntity> print businessprofileaccounts [todrive <ToDriveAttribute>*]
#	[type locationgroup|organization|personal|usergroup]
def printShowBusinessProfileAccounts(users):
  csvPF = _getMain().CSVPrintFile(['User', 'name', 'accountName']) if Act.csvFormat() else None
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'type':
      kwargs['filter'] = f'type={getChoice(PROFILE_ACCOUNT_TYPE_MAP, mapChoice=True)}'
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, bp = _getMain().buildGAPIServiceObject(API.BUSINESSACCOUNTMANAGEMENT, user, i, count)
    if not bp:
      continue
    if csvPF:
      _getMain().printGettingAllEntityItemsForWhom(Ent.BUSINESS_PROFILE_ACCOUNT, user, i, count, query=kwargs.get('filter'))
      pageMessage = _getMain().getPageMessageForWhom()
    else:
      pageMessage = None
    try:
      accounts = _getMain().callGAPIpages(bp.accounts(), 'list', 'accounts',
                               pageMessage=pageMessage,
                               throwReasons=[GAPI.PERMISSION_DENIED],
                               **kwargs)
    except GAPI.permissionDenied as e:
      accessErrorExitNonDirectory(API.BUSINESSACCOUNTMANAGEMENT, str(e))
    if not csvPF:
      jcount = len(accounts)
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.BUSINESS_PROFILE_ACCOUNT, i, count)
      Ind.Increment()
      j = 0
      for account in sorted(accounts, key=lambda k: k['name']):
        j += 1
        _getMain().printKeyValueListWithCount(['Account', account['name']], j, jcount)
        Ind.Increment()
        _getMain().showJSON(None, account)
        Ind.Decrement()
      Ind.Decrement()
    else:
      for account in accounts:
        row = _getMain().flattenJSON(account, flattened={'User': user, 'name': account['name'], 'accountName': account['accountName']})
        csvPF.WriteRowTitles(row)
  if csvPF:
    csvPF.writeCSVfile('Business Profile Accounts')

# gam info verify|verification
def doInfoSiteVerification():
  verif = _getMain().buildGAPIObject(API.SITEVERIFICATION)
  _getMain().checkForExtraneousArguments()
  sites = _getMain().callGAPIitems(verif.webResource(), 'list', 'items')
  if sites:
    count = len(sites)
    i = 0
    for site in sorted(sites, key=lambda k: (k['site']['type'], k['site']['identifier'])):
      i += 1
      _showSiteVerificationInfo(site, i, count)
  else:
    _getMain().printKeyValueList(['No Sites Verified.'])

# gam <UserTypeEntity> show webresources
# gam <UserTypeEntity> print webresources [todrive <ToDriveAttribute>*]
def printShowWebResources(users):
  csvPF = _getMain().CSVPrintFile(['User', 'site.identifier']) if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, verif = _getMain().buildGAPIServiceObject(API.SITEVERIFICATION, user, i, count)
    if not verif:
      continue
    sites = _getMain().callGAPIitems(verif.webResource(), 'list', 'items')
    if not csvPF:
      jcount = len(sites)
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.WEB_RESOURCE, i, count)
      Ind.Increment()
      j = 0
      for site in sorted(sites, key=lambda k: (k['site']['type'], k['site']['identifier'])):
        j += 1
        _showSiteVerificationInfo(site, j, jcount)
      Ind.Decrement()
    elif sites:
      for site in sites:
        row = _getMain().flattenJSON(site, flattened={'User': user})
        csvPF.WriteRowTitles(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Web Resources')

# gam <UserTypeEntity> show webmastersites
# gam <UserTypeEntity> print webmastersites [todrive <ToDriveAttribute>*]
def printShowWebMasterSites(users):
  csvPF = _getMain().CSVPrintFile(['User', 'siteUrl']) if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = _getMain().getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      _getMain().unknownArgumentExit()
  i, count, users = _getMain().getEntityArgument(users)
  for user in users:
    i += 1
    user, searchconsole = _getMain().buildGAPIServiceObject(API.SEARCHCONSOLE, user, i, count)
    if not searchconsole:
      continue
    try:
      sites = _getMain().callGAPIitems(searchconsole.sites(), 'list', 'siteEntry',
                            throwReasons=[GAPI.PERMISSION_DENIED])
    except GAPI.permissionDenied as e:
      accessErrorExitNonDirectory(API.SEARCHCONSOLE, str(e))
    if not csvPF:
      jcount = len(sites)
      _getMain().entityPerformActionNumItems([Ent.USER, user], jcount, Ent.WEB_MASTERSITE, i, count)
      Ind.Increment()
      j = 0
      for site in sorted(sites, key=lambda k: k['siteUrl']):
        j += 1
        _getMain().printKeyValueListWithCount(['Site', site['siteUrl']], j, jcount)
        Ind.Increment()
        _getMain().printKeyValueList(['permissionLevel', site['permissionLevel']])
        Ind.Decrement()
      Ind.Decrement()
    elif sites:
      for site in sites:
        row = _getMain().flattenJSON(site, flattened={'User': user})
        csvPF.WriteRowTitles(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Web Master Sites')

