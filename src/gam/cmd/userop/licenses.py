"""User license management.

Part of the _userop_tmp sub-package."""

"""GAM user operations: Looker Studio, user groups, licenses, photos, profile, sheets, tokens, deprovision."""

import re
import sys

from gam.cmd.userop.usergroups import LICENSE_PREVIEW_TITLES

from gam.cmd.userop.usergroups import LICENSE_PRODUCT_SKUIDS

from gamlib import api as API
from gamlib import settings as GC
from gamlib import gapi as GAPI
from gamlib import state as GM
from gamlib import msgs as Msg
from gamlib import skus as SKU
from gam.util.access import entityUnknownWarning
from gam.util.api import buildGAPIObject, callGAPI
from gam.util.args import (
    checkArgumentPresent,
    getArgument,
    getGoogleProduct,
    getGoogleSKU,
    getGoogleSKUList,
    normalizeEmailAddressOrUID,
)
from gam.util.csv_pf import CSVPrintFile
from gam.util.display import entityActionFailedWarning, entityActionPerformed, entityModifierNewValueActionPerformed, entityPerformActionModifierNumItems
from gam.util.entity import getEntityArgument, getItemsToModify
from gam.util.errors import invalidChoiceExit, missingArgumentExit, unknownArgumentExit, usageErrorExit

from gam.var import Act, Cmd, Ent, Ind

def getLicenseParameters(operation):
  lic = buildGAPIObject(API.LICENSING)
  parameters = {LICENSE_PRODUCT_SKUIDS: [], 'csvPF': None, 'preview': False, 'syncOperation': 'addremove', 'syncACLsMode': None, 'archive': False}
  skuLocation = Cmd.Location()
  if operation != 'patch':
    parameters[LICENSE_PRODUCT_SKUIDS] = getGoogleSKUList(allowUnknownProduct=True)
  else:
    parameters[LICENSE_PRODUCT_SKUIDS] = [getGoogleSKU()]
  if checkArgumentPresent(['product', 'productid']):
    productId = getGoogleProduct()
    for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
      productSku = (productId, productSku[1])
  if operation == 'patch':
    checkArgumentPresent('from')
    productId, oldSkuId = getGoogleSKU()
    if not productId:
      invalidChoiceExit(oldSkuId, SKU.getSortedSKUList(), True)
    skuId = parameters[LICENSE_PRODUCT_SKUIDS][0][1]
    parameters[LICENSE_PRODUCT_SKUIDS] = [(productId, skuId, oldSkuId)]
  while Cmd.ArgumentsRemaining():
    myarg = getArgument()
    if operation == 'sync' and myarg in {'addonly', 'removeonly'}:
      parameters['syncOperation'] = myarg
    elif operation == 'sync' and myarg in {'allskus', 'onesku'}:
      parameters['syncACLsMode'] = myarg
    elif myarg == 'preview':
      parameters['preview'] = True
    elif myarg == 'actioncsv':
      titles = LICENSE_PREVIEW_TITLES
      if operation == 'patch':
        titles.insert(2, 'oldskuId')
      parameters['csvPF'] = CSVPrintFile(titles)
    elif operation == 'patch' and myarg == 'archive':
      if skuId not in SKU.ARCHIVABLE_SKUS:
        usageErrorExit(Msg.SKU_HAS_NO_MATCHING_ARCHIVED_USER_SKU.format(skuId))
      parameters['archive'] = True
    else:
      unknownArgumentExit()
  for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
    if not productSku[0]:
      Cmd.SetLocation(skuLocation)
      invalidChoiceExit(productSku[1], SKU.getSortedSKUList(), False)
  if operation == 'sync':
    if len(parameters[LICENSE_PRODUCT_SKUIDS]) > 1:
      if parameters['syncACLsMode'] is None:
        missingArgumentExit('allskus|onesku')
      if parameters['syncACLsMode'] == 'onesku':
        # With onesku, all SKU productIds must be the same
        baseProductId = parameters[LICENSE_PRODUCT_SKUIDS][0][0]
        baseSkuId = parameters[LICENSE_PRODUCT_SKUIDS][0][1]
        for i in range(1, len(parameters[LICENSE_PRODUCT_SKUIDS])):
          productId = parameters[LICENSE_PRODUCT_SKUIDS][i][0]
          if baseProductId != productId:
            skuId = parameters[LICENSE_PRODUCT_SKUIDS][i][1]
            Cmd.SetLocation(skuLocation)
            usageErrorExit(Msg.ALL_SKU_PRODUCTIDS_MUST_MATCH.format(f'{baseProductId}:{baseSkuId}', f'{productId}:{skuId}'))
    else:
      parameters['syncACLsMode'] = 'allskus'
  return (lic, parameters)

def _writeLicenseAction(productId, skuId, oldSkuId, parameters, user, action, message):
  actionName = Act.PerformedName(action) if message == Act.SUCCESS else Act.ToPerformName(action)
  if action != Act.UPDATE:
    parameters['csvPF'].WriteRow({'user': user,
                                  'productId': productId,
                                  'skuId': skuId,
                                  'action': actionName,
                                  'message': message})
  else:
    parameters['csvPF'].WriteRow({'user': user,
                                  'productId': productId,
                                  'oldskuId': oldSkuId,
                                  'skuId': skuId,
                                  'action': actionName,
                                  'message': message})

def _createLicenses(lic, productId, skuId, parameters, jcount, users, i, count, returnDoneSet=False):
  Act.Set([Act.ADD, Act.ADD_PREVIEW][parameters['preview']])
  if parameters['preview']:
    message = Act.PREVIEW
  noAvailableLicenses = False
  doneSet = set()
  if not returnDoneSet:
    entityPerformActionModifierNumItems([Ent.LICENSE, SKU.skuIdToDisplayName(skuId)], Msg.TO_LC, jcount, Ent.USER, i, count)
  else:
    entityPerformActionModifierNumItems([Ent.LICENSE, SKU.skuIdToDisplayName(skuId)], Msg.TO_MAXIMUM_OF, jcount, Ent.USER, i, count)
  Ind.Increment()
  j = 0
  for user in users:
    j += 1
    if returnDoneSet:
      origUser = user
      doneSet.add(user)
    user = normalizeEmailAddressOrUID(user)
    if not noAvailableLicenses:
      try:
        if not parameters['preview']:
          callGAPI(lic.licenseAssignments(), 'insert',
                   bailOnInternalError=True,
                   throwReasons=[GAPI.INTERNAL_ERROR, GAPI.DUPLICATE, GAPI.CONDITION_NOT_MET, GAPI.INVALID,
                                 GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                   retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                   productId=productId, skuId=skuId, body={'userId': user}, fields='')
          message = Act.SUCCESS
        entityActionPerformed([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], j, jcount)
      except (GAPI.internalError, GAPI.duplicate, GAPI.invalid,
              GAPI.forbidden, GAPI.serviceNotAvailable) as e:
        message = str(e)
        entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], message, j, jcount)
      except (GAPI.conditionNotMet, GAPI.backendError) as e:
        message = str(e)
        entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], message, j, jcount)
        if ("there aren't enough available licenses" in message.lower() or
            "backend error" in message.lower()):
          noAvailableLicenses = True
          if returnDoneSet:
            doneSet.remove(origUser)
            break
      except GAPI.userNotFound as e:
        message = str(e)
        entityUnknownWarning(Ent.USER, user, j, jcount)
    else:
      entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], message, j, jcount)
    if parameters['csvPF']:
      _writeLicenseAction(productId, skuId, None, parameters, user, Act.ADD, message)
  Ind.Decrement()
  if returnDoneSet:
    return doneSet

# gam <UserTypeEntity> create license <SKUIDList> [product|productid <ProductID>] [preview] [actioncsv]
def createLicense(users):
  lic, parameters = getLicenseParameters('insert')
  _, jcount, users = getEntityArgument(users)
  count = len(parameters[LICENSE_PRODUCT_SKUIDS])
  i = 0
  for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
    i += 1
    _createLicenses(lic, productSku[0], productSku[1], parameters, jcount, users, i, count)
  if parameters['csvPF']:
    parameters['csvPF'].writeCSVfile('Create Licenses')

# gam <UserTypeEntity> update license <SKUID> [product|productid <ProductID>] [from] <SKUID>
#	[preview] [actioncsv] [archive]
def updateLicense(users):
  lic, parameters = getLicenseParameters('patch')
  j, jcount, users = getEntityArgument(users)
  Act.Set([Act.UPDATE, Act.UPDATE_PREVIEW][parameters['preview']])
  cd = None
  if parameters['preview']:
    message = Act.PREVIEW
  elif parameters['archive']:
    cd = buildGAPIObject(API.DIRECTORY)
  productId, skuId, oldSkuId = parameters[LICENSE_PRODUCT_SKUIDS][0]
  body = {'skuId': skuId}
  entityPerformActionModifierNumItems([Ent.LICENSE, SKU.skuIdToDisplayName(skuId)], Msg.FOR, jcount, Ent.USER)
  Ind.Increment()
  for user in users:
    j += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      if not parameters['preview']:
        callGAPI(lic.licenseAssignments(), 'patch',
                 bailOnInternalError=True,
                 throwReasons=[GAPI.INTERNAL_ERROR, GAPI.NOT_FOUND, GAPI.CONDITION_NOT_MET, GAPI.INVALID,
                               GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 productId=productId, skuId=oldSkuId, userId=user, body=body, fields='')
        message = Act.SUCCESS
      entityModifierNewValueActionPerformed([Ent.USER, user, Ent.LICENSE, SKU.skuIdToDisplayName(skuId)],
                                            Act.MODIFIER_FROM, SKU.skuIdToDisplayName(oldSkuId), j, jcount)
    except (GAPI.internalError, GAPI.notFound, GAPI.conditionNotMet, GAPI.invalid,
            GAPI.forbidden, GAPI.backendError, GAPI.serviceNotAvailable) as e:
      message = str(e)
      entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(oldSkuId)], message, j, jcount)
    except GAPI.userNotFound as e:
      message = str(e)
      entityUnknownWarning(Ent.USER, user, j, jcount)
    if parameters['archive'] and message == Act.SUCCESS:
      Act.Set(Act.ARCHIVE)
      try:
        callGAPI(cd.users(), 'update',
                 throwReasons=[GAPI.USER_NOT_FOUND, GAPI.DOMAIN_NOT_FOUND,
                               GAPI.FORBIDDEN, GAPI.BAD_REQUEST,
                               GAPI.INSUFFICIENT_ARCHIVED_USER_LICENSES],
                 retryReasons=[GAPI.INSUFFICIENT_ARCHIVED_USER_LICENSES],
                 userKey=user, body={'archived': True})
        entityActionPerformed([Ent.USER, user], j, jcount)
      except GAPI.userNotFound:
        entityUnknownWarning(Ent.USER, user, j, jcount)
      except (GAPI.domainNotFound, GAPI.domainCannotUseApis, GAPI.forbidden, GAPI.badRequest,
              GAPI.insufficientArchivedUserLicenses) as e:
        entityActionFailedWarning([Ent.USER, user], str(e), j, jcount)
      Act.Set(Act.UPDATE)
    if parameters['csvPF']:
      _writeLicenseAction(productId, skuId, oldSkuId, parameters, user, Act.UPDATE, message)
  Ind.Decrement()
  if parameters['csvPF']:
    parameters['csvPF'].writeCSVfile('Update Licenses')

def _deleteLicenses(lic, productId, skuId, parameters, jcount, users, i, count):
  Act.Set([Act.DELETE, Act.DELETE_PREVIEW][parameters['preview']])
  if parameters['preview']:
    message = Act.PREVIEW
  entityPerformActionModifierNumItems([Ent.LICENSE, SKU.skuIdToDisplayName(skuId)], Msg.FROM_LC, jcount, Ent.USER, i, count)
  Ind.Increment()
  j = 0
  for user in users:
    j += 1
    user = normalizeEmailAddressOrUID(user)
    try:
      if not parameters['preview']:
        callGAPI(lic.licenseAssignments(), 'delete',
                 throwReasons=[GAPI.INTERNAL_ERROR, GAPI.NOT_FOUND, GAPI.CONDITION_NOT_MET, GAPI.INVALID,
                               GAPI.USER_NOT_FOUND, GAPI.FORBIDDEN, GAPI.BACKEND_ERROR, GAPI.SERVICE_NOT_AVAILABLE],
                 retryReasons=GAPI.SERVICE_NOT_AVAILABLE_RETRY_REASONS,
                 productId=productId, skuId=skuId, userId=user)
        message = Act.SUCCESS
      entityActionPerformed([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], j, jcount)
    except (GAPI.internalError, GAPI.notFound, GAPI.conditionNotMet, GAPI.invalid,
            GAPI.forbidden, GAPI.backendError, GAPI.serviceNotAvailable) as e:
      message = str(e)
      entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, SKU.formatSKUIdDisplayName(skuId)], message, j, jcount)
    except GAPI.userNotFound as e:
      message = str(e)
      entityUnknownWarning(Ent.USER, user, j, jcount)
    if parameters['csvPF']:
      _writeLicenseAction(productId, skuId, None, parameters, user, Act.DELETE, message)
  Ind.Decrement()

# gam <UserTypeEntity> delete license <SKUIDList> [product|productid <ProductID>] [preview] [actioncsv]
def deleteLicense(users):
  lic, parameters = getLicenseParameters('delete')
  _, jcount, users = getEntityArgument(users)
  count = len(parameters[LICENSE_PRODUCT_SKUIDS])
  i = 0
  for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
    i += 1
    _deleteLicenses(lic, productSku[0], productSku[1], parameters, jcount, users, i, count)
  if parameters['csvPF']:
    parameters['csvPF'].writeCSVfile('Delete Licenses')

# gam <UserTypeEntity> sync license <SKUIDList> [product|productid <ProductID>]
#	[addonly|removeonly] [allskus|onesku] [preview] [actioncsv]
def syncLicense(users):
  lic, parameters = getLicenseParameters('sync')
  _, _, users = getEntityArgument(users)
  usersSet = set()
  currentLicenses = {}
  for user in users:
    usersSet.add(normalizeEmailAddressOrUID(user))
  for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
    skuId = productSku[1]
    currentLicenses[skuId] = set(getItemsToModify(Cmd.ENTITY_LICENSES, skuId))
  count = len(parameters[LICENSE_PRODUCT_SKUIDS])
  if parameters['syncACLsMode'] != 'onesku':
    i = 0
    for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
      i += 1
      if parameters['syncOperation'] != 'addonly':
        deleteSet = currentLicenses[skuId]-usersSet
        _deleteLicenses(lic, productSku[0], productSku[1], parameters, len(deleteSet), deleteSet, i, count)
      if parameters['syncOperation'] != 'removeonly':
        addSet = usersSet-currentLicenses[skuId]
        _createLicenses(lic, productSku[0], productSku[1], parameters, len(addSet), addSet, i, count)
  else: #parameters['syncACLsMode'] == 'onesku':
    if parameters['syncOperation'] != 'addonly':
      i = 0
      for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
        i += 1
        deleteSet = currentLicenses[productSku[1]]-usersSet
        _deleteLicenses(lic, productSku[0], productSku[1], parameters, len(deleteSet), deleteSet, i, count)
    if parameters['syncOperation'] != 'removeonly':
      addSet = usersSet.copy()
      for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
        addSet = addSet-currentLicenses[productSku[1]]
      i = 0
      for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
        if not addSet:
          break
        i += 1
        addSet -= _createLicenses(lic, productSku[0], productSku[1], parameters, len(addSet), addSet, i, count, returnDoneSet=True)
      if addSet:
        productId = productSku[0]
        skuIds = []
        for productSku in parameters[LICENSE_PRODUCT_SKUIDS]:
          skuIds.append(productSku[1])
        skuIdsList = GC.Values[GC.CSV_OUTPUT_FIELD_DELIMITER].join(skuIds)
        message = Msg.NO_AVAILABLE_LICENSES
        for user in addSet:
          user = normalizeEmailAddressOrUID(user)
          entityActionFailedWarning([Ent.USER, user, Ent.LICENSE, skuIdsList], message)
          if parameters['csvPF']:
            _writeLicenseAction(productId, skuIdsList, None, parameters, user, Act.ADD, message)
  if parameters['csvPF']:
    parameters['csvPF'].writeCSVfile('Sync Licenses')

# gam <UserTypeEntity> update photo
#	([<FileNamePattern>] |
#	 ([drivedir|(sourcefolder <FilePath>)] [filename <FileNamePattern>]) |
#	 (gphoto <EmailAddress> <DriveFileIDEntity>|<DriveFileNameEntity>))
# #user# and #email" will be replaced with user email address #username# will be replaced by portion of email address in front of @
# in <FileNamePattern> and <DriveFileNameEntity>
