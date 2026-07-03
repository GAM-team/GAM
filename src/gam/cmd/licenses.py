"""GAM license management."""

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

from gamlib import glskus as SKU
from gam.util.api import buildGAPIObject, callGAPIpages
from gam.util.args import getArgument, getGoogleProductList, getGoogleSKUList, getInteger
from gam.util.csv_pf import CSVPrintFile, getItemFieldsFromFieldsList
from gam.util.display import entityActionNotPerformedWarning, getPageMessageForWhom, printEntityKVList
from gam.util.errors import unknownArgumentExit

def __getattr__(name):
  """Fall back to gam module for any undefined names."""
  main = _getMain()
  try:
    return getattr(main, name)
  except AttributeError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def doPrintLicenses(returnFields=None, skus=None, countsOnly=False, returnCounts=False):
  lic = buildGAPIObject(API.LICENSING)
  _getMain().setTrueCustomerId()
  customerId = _getMain()._getCustomerId()
  csvPF = CSVPrintFile()
  products = []
  feed = []
  licenseCounts = []
  maxResults = GC.Values[GC.LICENSE_MAX_RESULTS]
  if not returnFields:
    while Cmd.ArgumentsRemaining():
      myarg = getArgument()
      if not returnCounts and myarg == 'todrive':
        csvPF.GetTodriveParameters()
      elif myarg in {'products', 'product'}:
        products = getGoogleProductList()
        skus = []
      elif myarg in {'skus', 'sku'}:
        skus = getGoogleSKUList()
        products = []
      elif myarg == 'allskus':
        skus = SKU.getAllSKUs()
        products = []
      elif myarg == 'gsuite':
        skus = SKU.getGSuiteSKUs()
        products = []
      elif myarg == 'countsonly':
        countsOnly = True
      elif myarg == 'maxresults':
        maxResults = getInteger(minVal=10, maxVal=1000)
      else:
        unknownArgumentExit()
    if not skus and not products and GM.Globals[GM.LICENSE_SKUS]:
      skus = GM.Globals[GM.LICENSE_SKUS]
    if not countsOnly:
      fields = getItemFieldsFromFieldsList('items', ['productId', 'skuId', 'userId'])
      csvPF.SetTitles(['userId', 'productId', 'productDisplay', 'skuId', 'skuDisplay'])
    else:
      fields = getItemFieldsFromFieldsList('items', ['userId'])
      if not returnCounts:
        if skus:
          csvPF.SetTitles(['productId', 'productDisplay', 'skuId', 'skuDisplay', 'licenses'])
        else:
          csvPF.SetTitles(['productId', 'productDisplay', 'licenses'])
  else:
    fields = getItemFieldsFromFieldsList('items', returnFields)
  if skus:
    for sku in skus:
      Ent.SetGetting(Ent.LICENSE)
      productId = sku[0]
      skuId = sku[1]
      productDisplay = SKU.formatProductIdDisplayName(productId)
      skuIdDisplay = SKU.formatSKUIdDisplayName(skuId)
      try:
        feed += callGAPIpages(lic.licenseAssignments(), 'listForProductAndSku', 'items',
                              pageMessage=getPageMessageForWhom(forWhom=skuIdDisplay),
                              throwReasons=[GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_ARGUMENT],
                              customerId=customerId, productId=productId, skuId=skuId,
                              maxResults=maxResults, fields=fields)
        if countsOnly:
          licenseCounts.append([Ent.PRODUCT, productId, Ent.SKU, [skuId, skuIdDisplay][returnCounts], Ent.LICENSE, len(feed)])
          feed = []
      except (GAPI.invalid, GAPI.forbidden, GAPI.invalidArgument) as e:
        entityActionNotPerformedWarning([Ent.PRODUCT, productDisplay, Ent.SKU, skuIdDisplay], str(e))
  else:
    suppressErrorMsg = False
    if not products:
      suppressErrorMsg = True
      products = SKU.getSortedProductList()
    for productId in products:
      Ent.SetGetting(Ent.LICENSE)
      productDisplay = SKU.formatProductIdDisplayName(productId)
      try:
        feed += callGAPIpages(lic.licenseAssignments(), 'listForProduct', 'items',
                              pageMessage=getPageMessageForWhom(forWhom=productDisplay),
                              throwReasons=[GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_ARGUMENT],
                              customerId=customerId, productId=productId,
                              maxResults=maxResults, fields=fields)
        if countsOnly:
          licenseCounts.append([Ent.PRODUCT, [productId, productDisplay][returnCounts], Ent.LICENSE, len(feed)])
          feed = []
      except (GAPI.invalid, GAPI.forbidden, GAPI.invalidArgument) as e:
        if not suppressErrorMsg:
          entityActionNotPerformedWarning([Ent.PRODUCT, productDisplay], str(e))
  if countsOnly:
    if returnCounts:
      return licenseCounts
    if skus:
      for u_license in licenseCounts:
        csvPF.WriteRow({'productId': u_license[1], 'productDisplay': SKU.productIdToDisplayName(u_license[1]),
                        'skuId': u_license[3], 'skuDisplay': SKU.skuIdToDisplayName(u_license[3]), 'licenses': u_license[5]})
    else:
      for u_license in licenseCounts:
        csvPF.WriteRow({'productId': u_license[1], 'productDisplay': SKU.productIdToDisplayName(u_license[1]), 'licenses': u_license[3]})
    csvPF.writeCSVfile('Licenses')
    return
  if returnFields:
    if returnFields == ['userId']:
      userIds = []
      for u_license in feed:
        userId = u_license.get('userId', '').lower()
        if userId:
          userIds.append(userId)
      return userIds
    userSkuIds = {}
    for u_license in feed:
      userId = u_license.get('userId', '').lower()
      skuId = u_license.get('skuId')
      if userId and skuId:
        userSkuIds.setdefault(userId, [])
        userSkuIds[userId].append(skuId)
    return userSkuIds
  for u_license in feed:
    userId = u_license.get('userId', '').lower()
    productId = u_license.get('productId', '')
    skuId = u_license.get('skuId', '')
    csvPF.WriteRow({'userId': userId,
                    'productId': productId, 'productDisplay': SKU.productIdToDisplayName(productId),
                    'skuId': skuId, 'skuDisplay': SKU.skuIdToDisplayName(skuId)})
  csvPF.writeCSVfile('Licenses')

# gam show licenses
#	[(products|product <ProductIDList>)|(skus|sku <SKUIDList>)|allskus|gsuite]
#	[maxresults <Integer>]
def doShowLicenses():
  licenseCounts = doPrintLicenses(countsOnly=True, returnCounts=True)
  for u_license in licenseCounts:
    printEntityKVList(u_license[:-2], [Ent.Plural(u_license[-2]), u_license[-1]])

# gam delete alert <AlertID>
# gam undelete alert <AlertID>
