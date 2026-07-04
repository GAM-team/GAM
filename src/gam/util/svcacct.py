"""Service account API object construction.

Builds authenticated Google API service objects for domain-wide delegation
(service account) access. Separated from api.py to break the api↔uid
circular dependency — these functions need both api.py (for credentials/service
construction) and uid.py (for UID-to-email resolution).
"""

import time

import google.auth.exceptions
import httplib2

from gamlib import settings as GC
from gamlib import state as GM
from gam.constants import NETWORK_ERROR_RC
from util.api import (
    _getSvcAcctData,
    getHttpObj,
    getService,
    getSvcAcctCredentials,
    handleOAuthTokenError,
    handleServerError,
    transportAuthorizedHttp,
    transportCreateRequest,
    waitOnFailure,
)
from util.args import UTF8
from util.output import ERROR_PREFIX, writeStdout
from util.uid import convertUIDtoEmailAddress

HTML_TITLE_PATTERN = __import__('re').compile(r'.*<title>(.+)</title>')


def getSaUser(user):
  """Resolve a user UID to email, preserving current client API state.

  convertUIDtoEmailAddress may call buildGAPIObject as a side effect,
  which modifies GM.Globals[CURRENT_CLIENT_API/SCOPES]. This wrapper
  saves and restores those globals so service account authentication
  isn't disrupted.
  """
  currentClientAPI = GM.Globals[GM.CURRENT_CLIENT_API]
  currentClientAPIScopes = GM.Globals[GM.CURRENT_CLIENT_API_SCOPES]
  userEmail = convertUIDtoEmailAddress(user) if user else None
  GM.Globals[GM.CURRENT_CLIENT_API] = currentClientAPI
  GM.Globals[GM.CURRENT_CLIENT_API_SCOPES] = currentClientAPIScopes
  return userEmail


def chooseSaAPI(api1, api2):
  """Choose between two API versions based on service account scope availability."""
  _getSvcAcctData()
  if api1 in GM.Globals[GM.SVCACCT_SCOPES]:
    return api1
  return api2


def buildGAPIServiceObject(api, user, i=0, count=0, displayError=True):
  """Build an authenticated Google API service object for a service account user."""
  userEmail = getSaUser(user)
  if GM.Globals[GM.HTTP_OBJECT] is None:
    GM.Globals[GM.HTTP_OBJECT] = getHttpObj(cache=GM.Globals[GM.CACHE_DIR])
  httpObj = GM.Globals[GM.HTTP_OBJECT]
  service = getService(api, httpObj)
  credentials = getSvcAcctCredentials(api, userEmail)
  request = transportCreateRequest(httpObj)
  triesLimit = 3
  for n in range(1, triesLimit+1):
    try:
      credentials.refresh(request)
      service._http = transportAuthorizedHttp(credentials, http=httpObj)
      return (userEmail, service)
    except (httplib2.HttpLib2Error, google.auth.exceptions.TransportError, RuntimeError) as e:
      if n != triesLimit:
        httpObj.connections = {}
        waitOnFailure(n, triesLimit, NETWORK_ERROR_RC, str(e))
        continue
      handleServerError(e)
    except google.auth.exceptions.RefreshError as e:
      if isinstance(e.args, tuple):
        e = e.args[0]
      if n < triesLimit:
        if isinstance(e, str):
          eContent = e
        else:
          eContent = e.content.decode(UTF8) if isinstance(e.content, bytes) else e.content
        if eContent[0:15] == '<!DOCTYPE html>':
          if GC.Values[GC.DEBUG_LEVEL] > 0:
            writeStdout(f'{ERROR_PREFIX} HTTP: {str(eContent)}\n')
          lContent = eContent.lower()
          tg = HTML_TITLE_PATTERN.match(lContent)
          lContent = tg.group(1) if tg else ''
          if lContent.startswith('Error 502 (Server Error)'):
            time.sleep(30)
            continue
      handleOAuthTokenError(e, True, displayError, i, count)
      return (userEmail, None)
