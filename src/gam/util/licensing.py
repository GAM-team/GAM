"""Licensing API data-fetching utilities.

Pure data-fetching functions for the Google Licensing API.
These query the API and return structured data.  They contain no CLI argument
parsing or output formatting.
"""

from gamlib import gapi as GAPI
from gamlib import skus as SKU

from gam.util.api_call import callGAPIpages
from gam.util.display import entityActionNotPerformedWarning, getPageMessageForWhom

from gam.var import Ent


def _itemFieldsFromList(item, fieldsList):
  """Format a fields parameter string for a paginated API call."""
  return f"nextPageToken,{item}({','.join(set(fieldsList))})"


def fetchLicenseAssignments(lic, customerId, skus, returnFields, maxResults=1000):
  """Fetch license assignments from the Licensing API for given SKUs.

  Args:
    lic: A Licensing API service object.
    customerId: The Google Workspace customer ID.
    skus: A list of ``(productId, skuId)`` tuples to query.
    returnFields: A list of field names (e.g. ``['userId']`` or
        ``['userId', 'skuId']``) to include in the response.
    maxResults: Page size for the API call.

  Returns:
    A list of dicts, one per license assignment, with keys matching
    *returnFields*.
  """
  fields = _itemFieldsFromList('items', returnFields)
  feed = []
  for productId, skuId in skus:
    Ent.SetGetting(Ent.LICENSE)
    productDisplay = SKU.formatProductIdDisplayName(productId)
    skuIdDisplay = SKU.formatSKUIdDisplayName(skuId)
    try:
      feed += callGAPIpages(lic.licenseAssignments(), 'listForProductAndSku', 'items',
                            pageMessage=getPageMessageForWhom(forWhom=skuIdDisplay),
                            throwReasons=[GAPI.INVALID, GAPI.FORBIDDEN, GAPI.INVALID_ARGUMENT],
                            customerId=customerId, productId=productId, skuId=skuId,
                            maxResults=maxResults, fields=fields)
    except (GAPI.invalid, GAPI.forbidden, GAPI.invalidArgument) as e:
      entityActionNotPerformedWarning([Ent.PRODUCT, productDisplay, Ent.SKU, skuIdDisplay], str(e))
  return feed


def fetchLicensedUserIds(lic, customerId, skus, maxResults=1000):
  """Query the Licensing API and return user IDs holding the given SKUs.

  This is a convenience wrapper around :func:`fetchLicenseAssignments` that
  extracts and lowercases the ``userId`` field from each assignment.

  Returns:
    A list of lowercase email-address strings.
  """
  feed = fetchLicenseAssignments(lic, customerId, skus, ['userId'], maxResults)
  userIds = []
  for u_license in feed:
    userId = u_license.get('userId', '').lower()
    if userId:
      userIds.append(userId)
  return userIds


def fetchLicensedUserSkuIds(lic, customerId, skus, maxResults=1000):
  """Query the Licensing API and return a userId→[skuId] mapping.

  Returns:
    A dict mapping lowercase user IDs to lists of SKU IDs.
  """
  feed = fetchLicenseAssignments(lic, customerId, skus, ['userId', 'skuId'], maxResults)
  userSkuIds = {}
  for u_license in feed:
    userId = u_license.get('userId', '').lower()
    skuId = u_license.get('skuId')
    if userId and skuId:
      userSkuIds.setdefault(userId, [])
      userSkuIds[userId].append(skuId)
  return userSkuIds
