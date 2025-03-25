# -*- coding: utf-8 -*-

# Copyright (C) 2023 Ross Scroggs All Rights Reserved.
#
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Google SKUs

"""

# Products/SKUs
_PRODUCTS = {
  '101001': 'Cloud Identity',
  '101005': 'Cloud Identity Premium',
  '101031': 'Google Workspace for Education',
  '101033': 'Google Voice',
  '101034': 'Google Workspace Archived User',
  '101035': 'Cloud Search',
  '101036': 'Google Meet Global Dialing',
  '101037': 'Google Workspace for Education',
  '101038': 'AppSheet',
  '101039': 'Assured Controls',
  '101040': 'Chrome Enterprise',
  '101043': 'Google Workspace Additional Storage',
  '101047': 'Gemini',
  '101049': 'Education Endpoint Management',
  '101050': 'Colab',
  'Google-Apps': 'Google Workspace',
  'Google-Chrome-Device-Management': 'Google Chrome Device Management',
  'Google-Drive-storage': 'Google Drive Storage',
  'Google-Vault': 'Google Vault',
  }
_SKUS = {
  '1010010001': {
    'product': '101001', 'aliases': ['identity', 'cloudidentity'], 'displayName': 'Cloud Identity'},
  '1010050001': {
    'product': '101005', 'aliases': ['identitypremium', 'cloudidentitypremium'], 'displayName': 'Cloud Identity Premium'},
  '1010070001': {
    'product': 'Google-Apps', 'aliases': ['gwef', 'workspaceeducationfundamentals'], 'displayName': 'Google Workspace for Education Fundamentals'},
  '1010070004': {
    'product': 'Google-Apps', 'aliases': ['gwegmo', 'workspaceeducationgmailonly'], 'displayName': 'Google Workspace for Education Gmail Only'},
  '1010310002': {
    'product': '101031', 'aliases': ['gsefe', 'e4e', 'gsuiteenterpriseeducation'], 'displayName': 'Google Workspace for Education Plus - Legacy'},
  '1010310003': {
    'product': '101031', 'aliases': ['gsefes', 'e4es', 'gsuiteenterpriseeducationstudent'], 'displayName': 'Google Workspace for Education Plus - Legacy (Student)'},
  '1010310005': {
    'product': '101031', 'aliases': ['gwes', 'workspaceeducationstandard'], 'displayName': 'Google Workspace for Education Standard'},
  '1010310006': {
    'product': '101031', 'aliases': ['gwesstaff', 'workspaceeducationstandardstaff'], 'displayName': 'Google Workspace for Education Standard (Staff)'},
  '1010310007': {
    'product': '101031', 'aliases': ['gwesstudent', 'workspaceeducationstandardstudent'], 'displayName': 'Google Workspace for Education Standard (Extra Student)'},
  '1010310008': {
    'product': '101031', 'aliases': ['gwep', 'workspaceeducationplus'], 'displayName': 'Google Workspace for Education Plus'},
  '1010310009': {
    'product': '101031', 'aliases': ['gwepstaff', 'workspaceeducationplusstaff'], 'displayName': 'Google Workspace for Education Plus (Staff)'},
  '1010310010': {
    'product': '101031', 'aliases': ['gwepstudent', 'workspaceeducationplusstudent'], 'displayName': 'Google Workspace for Education Plus (Extra Student)'},
  '1010330002': {
    'product': '101033', 'aliases': ['gvpremier', 'voicepremier', 'googlevoicepremier'], 'displayName': 'Google Voice Premier'},
  '1010330003': {
    'product': '101033', 'aliases': ['gvstarter', 'voicestarter', 'googlevoicestarter'], 'displayName': 'Google Voice Starter'},
  '1010330004': {
    'product': '101033', 'aliases': ['gvstandard', 'voicestandard', 'googlevoicestandard'], 'displayName': 'Google Voice Standard'},
  '1010350001': {
    'product': '101035', 'aliases': ['cloudsearch'], 'displayName': 'Cloud Search'},
  '1010360001': {
    'product': '101036', 'aliases': ['meetdialing','googlemeetglobaldialing'], 'displayName': 'Google Meet Global Dialing'},
  '1010370001': {
    'product': '101037', 'aliases': ['gwetlu', 'workspaceeducationupgrade'], 'displayName': 'Google Workspace for Education: Teaching and Learning Upgrade'},
  '1010380001': {
    'product': '101038', 'aliases': ['appsheetcore'], 'displayName': 'AppSheet Core'},
  '1010380002': {
    'product': '101038', 'aliases': ['appsheetstandard', 'appsheetenterprisestandard'], 'displayName': 'AppSheet Enterprise Standard'},
  '1010380003': {
    'product': '101038', 'aliases': ['appsheetplus', 'appsheetenterpriseplus'], 'displayName': 'AppSheet Enterprise Plus'},
  '1010390001': {
    'product': '101039', 'aliases': ['assuredcontrols'], 'displayName': 'Assured Controls'},
  '1010390002': {
    'product': '101039', 'aliases': ['assuredcontrolsplus'], 'displayName': 'Assured Controls Plus'},
  '1010400001': {
    'product': '101040', 'aliases': ['beyondcorp', 'beyondcorpenterprise', 'bce', 'cep', 'chromeenterprisepremium'], 'displayName': 'Chrome Enterprise Premium'},
  '1010430001': {
    'product': '101043', 'aliases': ['gwas', 'plusstorage'], 'displayName': 'Google Workspace Additional Storage'},
  '1010470001': {
    'product': '101047', 'aliases': ['geminient', 'duetai'], 'displayName': 'Gemini Enterprise'},
  '1010470002': {
    'product': '101047', 'aliases': ['gwlabs', 'workspacelabs'], 'displayName': 'Google Workspace Labs'},
  '1010470003': {
    'product': '101047', 'aliases': ['geminibiz'], 'displayName': 'Gemini Business'},
  '1010470004': {
    'product': '101047', 'aliases': ['geminiedu'], 'displayName': 'Gemini Education'},
  '1010470005': {
    'product': '101047', 'aliases': ['geminiedupremium'], 'displayName': 'Gemini Education Premium'},
  '1010470006': {
    'product': '101047', 'aliases': ['aisecurity'], 'displayName': 'AI Security'},
  '1010470007': {
    'product': '101047', 'aliases': ['aimeetingsandmessaging'], 'displayName': 'AI Meetings and Messaging'},
  '1010490001': {
    'product': '101049', 'aliases': ['eeu'], 'displayName': 'Endpoint Education Upgrade'},
  '1010500001': {
    'product': '101050', 'aliases': ['colabpro'], 'displayName': 'Colab Pro'},
  '1010500002': {
    'product': '101050', 'aliases': ['colabpro+', 'colabproplus'], 'displayName': 'Colab Pro+'},
  'Google-Apps': {
    'product': 'Google-Apps', 'aliases': ['standard', 'free'], 'displayName': 'G Suite Legacy'},
  'Google-Apps-For-Business': {
    'product': 'Google-Apps', 'aliases': ['gafb', 'gafw', 'basic', 'gsuitebasic'], 'displayName': 'G Suite Basic'},
  'Google-Apps-For-Education': {
    'product': 'Google-Apps', 'aliases': ['gafe', 'gsuiteeducation', 'gsuiteedu'], 'displayName': 'Google Workspace for Education - Fundamentals'},
  'Google-Apps-For-Government': {
    'product': 'Google-Apps', 'aliases': ['gafg', 'gsuitegovernment', 'gsuitegov'], 'displayName': 'Google Workspace Government'},
  'Google-Apps-For-Postini': {
    'product': 'Google-Apps', 'aliases': ['gams', 'postini', 'gsuitegams', 'gsuitepostini', 'gsuitemessagesecurity'], 'displayName': 'Google Apps Message Security'},
  'Google-Apps-Lite': {
    'product': 'Google-Apps', 'aliases': ['gal', 'gsl', 'lite', 'gsuitelite'], 'displayName': 'G Suite Lite'},
  'Google-Apps-Unlimited': {
    'product': 'Google-Apps', 'aliases': ['gau', 'gsb', 'unlimited', 'gsuitebusiness'], 'displayName': 'G Suite Business'},
  '1010020020': {
    'product': 'Google-Apps', 'aliases': ['gae', 'gse', 'enterprise', 'gsuiteenterprise',
                                          'wsentplus', 'workspaceenterpriseplus'], 'displayName': 'Google Workspace Enterprise Plus (formerly G Suite Enterprise)'},
  '1010020025': {
    'product': 'Google-Apps', 'aliases': ['wsbizplus', 'workspacebusinessplus'], 'displayName': 'Google Workspace Business Plus'},
  '1010020026': {
    'product': 'Google-Apps', 'aliases': ['wsentstan', 'workspaceenterprisestandard'], 'displayName': 'Google Workspace Enterprise Standard'},
  '1010020027': {
    'product': 'Google-Apps', 'aliases': ['wsbizstart', 'wsbizstarter', 'workspacebusinessstarter'], 'displayName': 'Google Workspace Business Starter'},
  '1010020028': {
    'product': 'Google-Apps', 'aliases': ['wsbizstan', 'workspacebusinessstandard'], 'displayName': 'Google Workspace Business Standard'},
  '1010020029': {
    'product': 'Google-Apps', 'aliases': ['wes', 'wsentstarter', 'workspaceenterprisestarter'], 'displayName': 'Workspace Enterprise Starter'},
  '1010020030': {
    'product': 'Google-Apps', 'aliases': ['wsflw', 'workspacefrontline', 'workspacefrontlineworker'], 'displayName': 'Google Workspace Frontline Starter'},
  '1010020031': {
    'product': 'Google-Apps', 'aliases': ['wsflwstan', 'workspacefrontlinestan', 'workspacefrontlineworkerstan'], 'displayName': 'Google Workspace Frontline Standard'},
  '1010340001': {
    'product': '101034', 'aliases': ['gseau', 'enterprisearchived', 'gsuiteenterprisearchived'], 'displayName': 'Google Workspace Enterprise Plus - Archived User'},
  '1010340002': {
    'product': '101034', 'aliases': ['gsbau', 'businessarchived', 'gsuitebusinessarchived'], 'displayName': 'Google Workspace Business - Archived User'},
  '1010340003': {
    'product': '101034', 'aliases': ['wsbizplusarchived', 'workspacebusinessplusarchived'], 'displayName': 'Google Workspace Business Plus - Archived User'},
  '1010340004': {
    'product': '101034', 'aliases': ['wsentstanarchived', 'workspaceenterprisestandardarchived'], 'displayName': 'Google Workspace Enterprise Standard - Archived User'},
  '1010340005': {
    'product': '101034', 'aliases': ['wsbizstarterarchived', 'workspacebusinessstarterarchived'], 'displayName': 'Google Workspace Business Starter - Archived User'},
  '1010340006': {
    'product': '101034', 'aliases': ['wsbizstanarchived', 'workspacebusinessstanarchived'], 'displayName': 'Google Workspace Business Standard - Archived User'},
  '1010340007': {
    'product': '101034', 'aliases': ['gwefau', 'gwefarchived', 'workspaceeducationfundamentalsarchived'], 'displayName': 'Google Workspace for Education Fundamentals - Archived User'},
  '1010060001': {
    'product': '101006', 'aliases': ['gsuiteessentials', 'essentials',
                                     'd4e', 'driveenterprise', 'drive4enterprise',
                                     'wsess', 'workspaceesentials'], 'displayName': 'Google Workspace Essentials (formerly G Suite Essentials)'},
  '1010060003': {
    'product': 'Google-Apps', 'aliases': ['wsentess', 'workspaceenterpriseessentials'], 'displayName': 'Google Workspace Enterprise Essentials'},
  '1010060005': {
    'product': 'Google-Apps', 'aliases': ['wsessplus', 'workspaceessentialsplus'], 'displayName': 'Google Workspace Enterprise Essentials Plus'},
  'Google-Drive-storage-20GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive20gb', '20gb', 'googledrivestorage20gb'], 'displayName': 'Google Drive Storage 20GB'},
  'Google-Drive-storage-50GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive50gb', '50gb', 'googledrivestorage50gb'], 'displayName': 'Google Drive Storage 50GB'},
  'Google-Drive-storage-200GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive200gb', '200gb', 'googledrivestorage200gb'], 'displayName': 'Google Drive Storage 200GB'},
  'Google-Drive-storage-400GB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive400gb', '400gb', 'googledrivestorage400gb'], 'displayName': 'Google Drive Storage 400GB'},
  'Google-Drive-storage-1TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive1tb', '1tb', 'googledrivestorage1tb'], 'displayName': 'Google Drive Storage 1TB'},
  'Google-Drive-storage-2TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive2tb', '2tb', 'googledrivestorage2tb'], 'displayName': 'Google Drive Storage 2TB'},
  'Google-Drive-storage-4TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive4tb', '4tb', 'googledrivestorage4tb'], 'displayName': 'Google Drive Storage 4TB'},
  'Google-Drive-storage-8TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive8tb', '8tb', 'googledrivestorage8tb'], 'displayName': 'Google Drive Storage 8TB'},
  'Google-Drive-storage-16TB': {
    'product': 'Google-Drive-storage', 'aliases': ['drive16tb', '16tb', 'googledrivestorage16tb'], 'displayName': 'Google Drive Storage 16TB'},
  'Google-Vault': {
    'product': 'Google-Vault', 'aliases': ['vault', 'googlevault'], 'displayName': 'Google Vault'},
  'Google-Vault-Former-Employee': {
    'product': 'Google-Vault', 'aliases': ['vfe', 'googlevaultformeremployee'], 'displayName': 'Google Vault - Former Employee'},
  'Google-Chrome-Device-Management': {
    'product': 'Google-Chrome-Device-Management', 'aliases': ['chrome', 'cdm', 'googlechromedevicemanagement'], 'displayName': 'Google Chrome Device Management'}
  }

ARCHIVABLE_SKUS = {'1010020020', '1010020025', '1010020026', '1010020027', '1010020028', 'Google-Apps-Unlimited'}

def getProductAndSKU(sku):
  l_sku = sku.lower().replace('-', '').replace(' ', '').replace('"', '').replace("'", '').strip()
  if l_sku.startswith('nv:'):
    if ':' in sku[3:]:
      return sku[3:].split(':', 1)
    return (None, sku)
  for a_sku, sku_values in list(_SKUS.items()):
    if ((l_sku == a_sku.lower().replace('-', '')) or
        (l_sku in sku_values['aliases']) or
        (l_sku == sku_values['displayName'].lower().replace(' ', ''))):
      return (sku_values['product'], a_sku)
  return (None, sku)

def productIdToDisplayName(productId):
  return _PRODUCTS.get(productId, productId)

def formatProductIdDisplayName(productId):
  productIdDisplay = productIdToDisplayName(productId)
  if productId == productIdDisplay:
    return productId
  return f'{productId} ({productIdDisplay})'

def normalizeProductId(product):
  l_product = product.lower().replace('-', '').replace(' ', '').strip()
  if l_product.startswith('nv:'):
    return (True, product[3:])
  for a_sku, sku_values in list(_SKUS.items()):
    if ((l_product == sku_values['product'].lower().replace('-', '')) or
        (l_product == a_sku.lower().replace('-', '')) or
        (l_product in sku_values['aliases']) or
        (l_product == sku_values['displayName'].lower().replace(' ', ''))):
      return (True, sku_values['product'])
  return (False, product)

def getSortedProductList():
  return sorted(_PRODUCTS)

def skuIdToDisplayName(skuId):
  return _SKUS[skuId]['displayName'] if skuId in _SKUS else skuId

def formatSKUIdDisplayName(skuId):
  skuIdDisplay = skuIdToDisplayName(skuId)
  if skuId == skuIdDisplay:
    return skuId
  return f'{skuId} ({skuIdDisplay})'

def getSortedSKUList():
  return sorted(_SKUS)

def convertProductListToSKUList(productList):
  skuList = []
  for productId in productList:
    skuList += [(productId, skuId) for skuId in _SKUS if _SKUS[skuId]['product'] == productId]
  return skuList

def getAllSKUs():
  return convertProductListToSKUList(sorted(_PRODUCTS))

def getGSuiteSKUs():
  return convertProductListToSKUList(['Google-Apps', '101031'])
