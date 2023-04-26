import re
import sys

import gam
from gam.var import *
from gam import controlflow
from gam import display
from gam import gapi
from gam.gapi import errors as gapi_errors
from gam.gapi.directory import customer as gapi_directory_customer


def _get_customerid():
    ''' returns customerId with format C{customer_id}'''
    gapi_directory_customer.setTrueCustomerId()
    customer_id = GC_Values[GC_CUSTOMER_ID]
    if customer_id[0] != 'C':
        customer_id = 'C' + customer_id
    return customer_id

def build():
    return gam.buildGAPIObject('licensing')


def getProductAndSKU(sku):
    l_sku = sku.lower().replace('-', '').replace(' ', '')
    for a_sku, sku_values in list(SKUS.items()):
        if l_sku == a_sku.lower().replace(
                '-',
                '') or l_sku in sku_values['aliases'] or l_sku == sku_values[
                    'displayName'].lower().replace(' ', ''):
            return (sku_values['product'], a_sku)
    try:
        product = re.search('^([A-Z,a-z]*-[A-Z,a-z]*)', sku).group(1)
    except AttributeError:
        product = sku
    return (product, sku)


def user_lic_result(request_id, response, exception):
    if exception:
        http_status, reason, message = gapi_errors.get_gapi_error_detail(
                exception,
                soft_errors=True)
        print(f'ERROR: {request_id}: {http_status} - {reason} {message}')


def create(users, sku=None):
    lic = build()
    if not sku:
        sku = sys.argv[5]
    productId, skuId = getProductAndSKU(sku)
    sku_name = _formatSKUIdDisplayName(skuId)
    i = 6
    if len(sys.argv) > 6 and sys.argv[i].lower() in ['product', 'productid']:
        productId = sys.argv[i+1]
        i += 2
    for user in users:
        print(f'Adding license {sku_name} to {user}')
        gapi.call(lic.licenseAssignments(),
                  'insert',
                  soft_errors=True,
                  productId=productId,
                  skuId=skuId,
                  body={'userId': user})


def delete(users, sku=None):
    lic = build()
    if not sku:
        sku = sys.argv[5]
    productId, skuId = getProductAndSKU(sku)
    sku_name = _formatSKUIdDisplayName(skuId)
    i = 6
    if len(sys.argv) > 6 and sys.argv[i].lower() in ['product', 'productid']:
        productId = sys.argv[i+1]
        i += 2
    for user in users:
         print(f'Removing license {sku_name} from user {user}')
         gapi.call(lic.licenseAssignments(),
                   'delete',
                   soft_errors=True,
                   productId=productId,
                   skuId=skuId,
                   userId=user)


def sync(users):
    sku = sys.argv[5]
    current_licenses = gam.getUsersToModify(entity_type='license',
        entity=sku)
    users_to_license = [user for user in users if user not in current_licenses]
    users_to_unlicense = [user for user in current_licenses if user not in users]
    print(f'Need to remove license from {len(users_to_unlicense)} and add to ' \
          f'{len(users_to_license)} users...')
    # do the remove first to free up seats
    delete(users_to_unlicense, sku)
    create(users_to_license, sku)


def update(users, sku=None, old_sku=None):
    lic = build()
    if not sku:
        sku = sys.argv[5]
    productId, skuId = getProductAndSKU(sku)
    sku_name = _formatSKUIdDisplayName(skuId)
    i = 6
    if len(sys.argv) > 6 and sys.argv[i].lower() in ['product', 'productid']:
        productId = sys.argv[i+1]
        i += 2
    if not old_sku:
        try:
            old_sku = sys.argv[i]
            if old_sku.lower() == 'from':
                old_sku = sys.argv[i + 1]
        except KeyError:
            controlflow.system_error_exit(
                2,
                'You need to specify the user\'s old SKU as the last argument'
            )
        _, old_sku = getProductAndSKU(old_sku)
    old_sku_name = _formatSKUIdDisplayName(old_sku)
    for user in users:
        print(f'Changing user {user} from license {old_sku_name} to {sku_name}')
        gapi.call(lic.licenseAssignments(),
                  'patch',
                  soft_errors=True,
                  productId=productId,
                  skuId=old_sku,
                  userId=user,
                  body={'skuId': skuId})


def print_(returnFields=None,
                    skus=None,
                    countsOnly=False,
                    returnCounts=False):
    lic = build()
    customer_id = _get_customerid()
    products = []
    licenses = []
    licenseCounts = []
    if not returnFields:
        csvRows = []
        todrive = False
        i = 3
        while i < len(sys.argv):
            myarg = sys.argv[i].lower()
            if not returnCounts and myarg == 'todrive':
                todrive = True
                i += 1
            elif myarg in ['products', 'product']:
                products = sys.argv[i + 1].split(',')
                i += 2
            elif myarg in ['sku', 'skus']:
                skus = sys.argv[i + 1].split(',')
                i += 2
            elif myarg == 'allskus':
                skus = sorted(SKUS)
                products = []
                i += 1
            elif myarg == 'gsuite':
                skus = [
                    skuId for skuId in SKUS
                    if SKUS[skuId]['product'] in ['Google-Apps', '101031']
                ]
                products = []
                i += 1
            elif myarg == 'countsonly':
                countsOnly = True
                i += 1
            else:
                controlflow.invalid_argument_exit(sys.argv[i],
                                                  'gam print licenses')
        if not countsOnly:
            fields = 'nextPageToken,items(productId,skuId,userId)'
            titles = ['userId', 'productId', 'skuId']
        else:
            fields = 'nextPageToken,items(userId)'
            if not returnCounts:
                if skus:
                    titles = ['productId', 'skuId', 'licenses']
                else:
                    titles = ['productId', 'licenses']
    else:
        fields = f'nextPageToken,items({returnFields})'
    if skus:
        for sku in skus:
            if not products:
                product, sku = getProductAndSKU(sku)
            else:
                product = products[0]
            page_message = gapi.got_total_items_msg(
                f'Licenses for {SKUS.get(sku, {"displayName": sku})["displayName"]}',
                '...\n')
            try:
                licenses += gapi.get_all_pages(
                    lic.licenseAssignments(),
                    'listForProductAndSku',
                    'items',
                    throw_reasons=[
                        gapi_errors.ErrorReason.INVALID,
                        gapi_errors.ErrorReason.FORBIDDEN
                    ],
                    page_message=page_message,
                    customerId=customer_id,
                    maxResults=100,
                    productId=product,
                    skuId=sku,
                    fields=fields)
                if countsOnly:
                    licenseCounts.append([
                        'Product', product, 'SKU', sku, 'Licenses',
                        len(licenses)
                    ])
                    licenses = []
            except (gapi_errors.GapiInvalidError,
                    gapi_errors.GapiForbiddenError):
                pass
    else:
        if not products:
            products = sorted(PRODUCTID_NAME_MAPPINGS)
        for productId in products:
            page_message = gapi.got_total_items_msg(
                f'Licenses for {PRODUCTID_NAME_MAPPINGS.get(productId, productId)}',
                '...\n')
            try:
                licenses += gapi.get_all_pages(
                    lic.licenseAssignments(),
                    'listForProduct',
                    'items',
                    throw_reasons=[
                        gapi_errors.ErrorReason.INVALID,
                        gapi_errors.ErrorReason.FORBIDDEN
                    ],
                    page_message=page_message,
                    customerId=customer_id,
                    maxResults=100,
                    productId=productId,
                    fields=fields)
                if countsOnly:
                    licenseCounts.append(
                        ['Product', productId, 'Licenses',
                         len(licenses)])
                    licenses = []
            except (gapi_errors.GapiInvalidError,
                    gapi_errors.GapiForbiddenError):
                pass
    if countsOnly:
        if returnCounts:
            return licenseCounts
        if skus:
            for u_license in licenseCounts:
                csvRows.append({
                    'productId': u_license[1],
                    'skuId': u_license[3],
                    'licenses': u_license[5]
                })
        else:
            for u_license in licenseCounts:
                csvRows.append({
                    'productId': u_license[1],
                    'licenses': u_license[3]
                })
        display.write_csv_file(csvRows, titles, 'Licenses', todrive)
        return
    if returnFields:
        if returnFields == 'userId':
            userIds = []
            for u_license in licenses:
                userId = u_license.get('userId', '').lower()
                if userId:
                    userIds.append(userId)
            return userIds
        userSkuIds = {}
        for u_license in licenses:
            userId = u_license.get('userId', '').lower()
            skuId = u_license.get('skuId')
            if userId and skuId:
                userSkuIds.setdefault(userId, [])
                userSkuIds[userId].append(skuId)
        return userSkuIds
    for u_license in licenses:
        userId = u_license.get('userId', '').lower()
        skuId = u_license.get('skuId', '')
        csvRows.append({
            'userId': userId,
            'productId': u_license.get('productId', ''),
            'skuId': _skuIdToDisplayName(skuId)
        })
    display.write_csv_file(csvRows, titles, 'Licenses', todrive)


def show():
    licenseCounts = print_(countsOnly=True, returnCounts=True)
    for u_license in licenseCounts:
        line = ''
        for i in range(0, len(u_license), 2):
            line += f'{u_license[i]}: {u_license[i+1]}, '
        print(line[:-2])


def _skuIdToDisplayName(skuId):
    return SKUS[skuId]['displayName'] if skuId in SKUS else skuId


def _formatSKUIdDisplayName(skuId):
    skuIdDisplay = _skuIdToDisplayName(skuId)
    if skuId == skuIdDisplay:
        return skuId
    return f'{skuId} ({skuIdDisplay})'
