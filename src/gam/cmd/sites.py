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
from gam.util.api import (
    buildGAPIObject,
    buildGAPIServiceObject,
    callGAPI,
    callGAPIitems,
    callGAPIpages,
    getHttpObj,
)
from gam.util.args import (
    UTF8,
    checkForExtraneousArguments,
    getArgument,
    getChoice,
    getString,
)
from gam.util.csv_pf import CSVPrintFile, flattenJSON, showJSON
from gam.util.display import (
    entityPerformActionNumItems,
    getPageMessageForWhom,
    printBlankLine,
    printGettingAllEntityItemsForWhom,
    printKeyValueList,
    printKeyValueListWithCount,
)
from gam.util.entity import getEntityArgument
from gam.util.errors import INVALID_JSON_RC, deprecatedCommandExit, unknownArgumentExit
from gam.util.fileio import writeFile
from gam.util.output import ERROR, systemErrorExit
from gam.constants import NETWORK_ERROR_RC

Act = glaction.GamAction()
Ent = glentity.GamEntity()
Ind = glindent.GamIndent()
Cmd = glclargs.GamCLArgs()


from urllib.parse import unquote
from urllib.parse import urlencode

def deprecatedUserSites(_):
  deprecatedCommandExit()

def deprecatedDomainSites():
  deprecatedCommandExit()

def doCreateSiteVerification():
  verif = buildGAPIObject(API.SITEVERIFICATION)
  a_domain = getString(Cmd.OB_DOMAIN_NAME)
  checkForExtraneousArguments()
  txt_record = callGAPI(verif.webResource(), 'getToken',
                        body={'site': {'type': 'INET_DOMAIN', 'identifier': a_domain},
                              'verificationMethod': 'DNS_TXT'})
  printKeyValueList(['TXT Record Name ', a_domain])
  printKeyValueList(['TXT Record Value', txt_record['token']])
  printBlankLine()
  cname_record = callGAPI(verif.webResource(), 'getToken',
                          body={'site': {'type': 'INET_DOMAIN', 'identifier': a_domain},
                                'verificationMethod': 'DNS_CNAME'})
  cname_token = cname_record['token']
  cname_list = cname_token.split(' ')
  cname_subdomain = cname_list[0]
  cname_value = cname_list[1]
  printKeyValueList(['CNAME Record Name ', f'{cname_subdomain}.{a_domain}'])
  printKeyValueList(['CNAME Record Value', cname_value])
  printBlankLine()
  webserver_file_record = callGAPI(verif.webResource(), 'getToken',
                                   body={'site': {'type': 'SITE', 'identifier': f'http://{a_domain}/'},
                                         'verificationMethod': 'FILE'})
  webserver_file_token = webserver_file_record['token']
  printKeyValueList(['Saving web server verification file to', webserver_file_token])
  writeFile(webserver_file_token, f'google-site-verification: {webserver_file_token}', continueOnError=True)
  printKeyValueList(['Verification File URL', f'http://{a_domain}/{webserver_file_token}'])
  printBlankLine()
  webserver_meta_record = callGAPI(verif.webResource(), 'getToken',
                                   body={'site': {'type': 'SITE', 'identifier': f'http://{a_domain}/'},
                                         'verificationMethod': 'META'})
  printKeyValueList(['Meta URL', f'//{a_domain}/'])
  printKeyValueList(['Meta HTML Header Data', webserver_meta_record['token']])
  printBlankLine()

def _showSiteVerificationInfo(site, i=0, count=0):
  printKeyValueListWithCount(['Site', site['site']['identifier']], i, count)
  Ind.Increment()
  printKeyValueList(['ID', unquote(site['id'])])
  printKeyValueList(['Type', site['site']['type']])
  printKeyValueList(['All Owners', None])
  if 'owners' in site:
    Ind.Increment()
    for owner in sorted(site['owners']):
      printKeyValueList([owner])
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
  from gam.cmd.sso import SITEVERIFICATION_METHOD_CHOICE_MAP
  def showDNSrecords():
    try:
      verify_data = callGAPI(verif.webResource(), 'getToken',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_PARAMETER],
                             body=body)
    except (GAPI.badRequest, GAPI.invalidParameter) as e:
      printKeyValueList([ERROR, str(e)])
      return
    printKeyValueList(['Method', verify_data['method']])
    if verify_data['method'] in {'DNS_CNAME', 'DNS_TXT'}:
      if verify_data['method'] == 'DNS_CNAME':
        cname_subdomain, cname_target = verify_data['token'].split(' ')
        query_params = {'name': f'{cname_subdomain}.{a_domain}', 'type': 'cname'}
        printKeyValueList(['Expected Record',
                           f'{query_params["name"]} IN CNAME {cname_target}'])
      else:
        query_params = {'name': f'{a_domain}', 'type': 'txt'}
        printKeyValueList(['Expected Record',
                           f'{query_params["name"]} IN TXT {verify_data["token"]}'])
      _, content = getHttpObj().request('https://dns.google/resolve?' + urlencode(query_params), 'GET')
      try:
        result = json.loads(content.decode(UTF8))
        status = result['Status']
        if status == 0 and 'Answer' in result:
          if verify_data['method'] == 'DNS_CNAME':
            printKeyValueList(['DNS      Record',
                               f'{result["Answer"][0]["name"].rstrip(".")} IN CNAME {result["Answer"][0]["data"]}'])
          else:
            found = False
            for answer in result['Answer']:
              answer['data'] = answer['data'].strip('"')
              if answer['data'].startswith('google-site-verification'):
                found = True
                printKeyValueList(['DNS      Record',
                                   f'{answer["name"].rstrip(".")} IN TXT {answer["data"]}'])
            if not found:
              printKeyValueList(['DNS      Record', 'No matching record found'])
        elif status == 0:
          systemErrorExit(NETWORK_ERROR_RC, Msg.DOMAIN_NOT_FOUND_IN_DNS)
        else:
          systemErrorExit(NETWORK_ERROR_RC, DNS_ERROR_CODES_MAP.get(status, f'Unknown error {status}'))
      except (IndexError, KeyError, SyntaxError, TypeError, ValueError):
        systemErrorExit(INVALID_JSON_RC, Msg.INVALID_JSON_INFORMATION)

  verif = buildGAPIObject(API.SITEVERIFICATION)
  a_domain = getString(Cmd.OB_DOMAIN_NAME)
  verificationMethod = getChoice(SITEVERIFICATION_METHOD_CHOICE_MAP, mapChoice=True)
  if verificationMethod in {'DNS_TXT', 'DNS_CNAME'}:
    verify_type = 'INET_DOMAIN'
    identifier = a_domain
    showDNS = True
  else:
    verify_type = 'SITE'
    identifier = f'http://{a_domain}/'
    showDNS = False
  checkForExtraneousArguments()
  body = {'site': {'type': verify_type, 'identifier': identifier},
          'verificationMethod': verificationMethod}
  try:
    verify_result = callGAPI(verif.webResource(), 'insert',
                             throwReasons=[GAPI.BAD_REQUEST, GAPI.INVALID_PARAMETER],
                             verificationMethod=verificationMethod, body=body)
  except GAPI.badRequest as e:
    printKeyValueList([ERROR, str(e)])
    if showDNS:
      showDNSrecords()
    return
  except GAPI.invalidParameter as e:
    printKeyValueList([ERROR, str(e)])
    return
  printKeyValueList(['Verified!'])
  if showDNS:
    showDNSrecords()
  _showSiteVerificationInfo(verify_result)
  printKeyValueList([Msg.YOU_CAN_ADD_DOMAIN_TO_ACCOUNT.format(a_domain, GC.Values[GC.DOMAIN])])

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
  csvPF = CSVPrintFile(['User', 'name', 'accountName']) if Act.csvFormat() else None
  kwargs = {}
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    elif myarg == 'type':
      kwargs['filter'] = f'type={getChoice(PROFILE_ACCOUNT_TYPE_MAP, mapChoice=True)}'
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, bp = buildGAPIServiceObject(API.BUSINESSACCOUNTMANAGEMENT, user, i, count)
    if not bp:
      continue
    if csvPF:
      printGettingAllEntityItemsForWhom(Ent.BUSINESS_PROFILE_ACCOUNT, user, i, count, query=kwargs.get('filter'))
      pageMessage = getPageMessageForWhom()
    else:
      pageMessage = None
    try:
      accounts = callGAPIpages(bp.accounts(), 'list', 'accounts',
                               pageMessage=pageMessage,
                               throwReasons=[GAPI.PERMISSION_DENIED],
                               **kwargs)
    except GAPI.permissionDenied as e:
      accessErrorExitNonDirectory(API.BUSINESSACCOUNTMANAGEMENT, str(e))
    if not csvPF:
      jcount = len(accounts)
      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.BUSINESS_PROFILE_ACCOUNT, i, count)
      Ind.Increment()
      j = 0
      for account in sorted(accounts, key=lambda k: k['name']):
        j += 1
        printKeyValueListWithCount(['Account', account['name']], j, jcount)
        Ind.Increment()
        showJSON(None, account)
        Ind.Decrement()
      Ind.Decrement()
    else:
      for account in accounts:
        row = flattenJSON(account, flattened={'User': user, 'name': account['name'], 'accountName': account['accountName']})
        csvPF.WriteRowTitles(row)
  if csvPF:
    csvPF.writeCSVfile('Business Profile Accounts')

# gam info verify|verification
def doInfoSiteVerification():
  verif = buildGAPIObject(API.SITEVERIFICATION)
  checkForExtraneousArguments()
  sites = callGAPIitems(verif.webResource(), 'list', 'items')
  if sites:
    count = len(sites)
    i = 0
    for site in sorted(sites, key=lambda k: (k['site']['type'], k['site']['identifier'])):
      i += 1
      _showSiteVerificationInfo(site, i, count)
  else:
    printKeyValueList(['No Sites Verified.'])

# gam <UserTypeEntity> show webresources
# gam <UserTypeEntity> print webresources [todrive <ToDriveAttribute>*]
def printShowWebResources(users):
  csvPF = CSVPrintFile(['User', 'site.identifier']) if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, verif = buildGAPIServiceObject(API.SITEVERIFICATION, user, i, count)
    if not verif:
      continue
    sites = callGAPIitems(verif.webResource(), 'list', 'items')
    if not csvPF:
      jcount = len(sites)
      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.WEB_RESOURCE, i, count)
      Ind.Increment()
      j = 0
      for site in sorted(sites, key=lambda k: (k['site']['type'], k['site']['identifier'])):
        j += 1
        _showSiteVerificationInfo(site, j, jcount)
      Ind.Decrement()
    elif sites:
      for site in sites:
        row = flattenJSON(site, flattened={'User': user})
        csvPF.WriteRowTitles(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Web Resources')

# gam <UserTypeEntity> show webmastersites
# gam <UserTypeEntity> print webmastersites [todrive <ToDriveAttribute>*]
def printShowWebMasterSites(users):
  csvPF = CSVPrintFile(['User', 'siteUrl']) if Act.csvFormat() else None
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if csvPF and myarg == 'todrive':
      csvPF.GetTodriveParameters()
    else:
      unknownArgumentExit()
  i, count, users = getEntityArgument(users)
  for user in users:
    i += 1
    user, searchconsole = buildGAPIServiceObject(API.SEARCHCONSOLE, user, i, count)
    if not searchconsole:
      continue
    try:
      sites = callGAPIitems(searchconsole.sites(), 'list', 'siteEntry',
                            throwReasons=[GAPI.PERMISSION_DENIED])
    except GAPI.permissionDenied as e:
      accessErrorExitNonDirectory(API.SEARCHCONSOLE, str(e))
    if not csvPF:
      jcount = len(sites)
      entityPerformActionNumItems([Ent.USER, user], jcount, Ent.WEB_MASTERSITE, i, count)
      Ind.Increment()
      j = 0
      for site in sorted(sites, key=lambda k: k['siteUrl']):
        j += 1
        printKeyValueListWithCount(['Site', site['siteUrl']], j, jcount)
        Ind.Increment()
        printKeyValueList(['permissionLevel', site['permissionLevel']])
        Ind.Decrement()
      Ind.Decrement()
    elif sites:
      for site in sites:
        row = flattenJSON(site, flattened={'User': user})
        csvPF.WriteRowTitles(row)
    elif GC.Values[GC.CSV_OUTPUT_USERS_AUDIT]:
      csvPF.WriteRowNoFilter({'User': user})
  if csvPF:
    csvPF.writeCSVfile('Web Master Sites')

