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

"""GAM GData resources

"""
API_DEPRECATED_MSG = 'Contacts API is being deprecated.'

# callGData throw errors
API_DEPRECATED = 612
BAD_GATEWAY = 601
BAD_REQUEST = 602
DOES_NOT_EXIST = 1301
ENTITY_EXISTS = 1300
FORBIDDEN = 603
GATEWAY_TIMEOUT = 612
INSUFFICIENT_PERMISSIONS = 604
INTERNAL_SERVER_ERROR = 1000
INVALID_DOMAIN = 605
INVALID_INPUT = 1317
INVALID_VALUE = 1801
NAME_NOT_VALID = 1303
NOT_FOUND = 606
NOT_IMPLEMENTED = 607
PRECONDITION_FAILED = 608
QUOTA_EXCEEDED = 609
SERVICE_NOT_APPLICABLE = 1410
SERVICE_UNAVAILABLE = 610
TOKEN_EXPIRED = 611
TOKEN_INVALID = 403
UNKNOWN_ERROR = 600
#
NON_TERMINATING_ERRORS = [API_DEPRECATED, BAD_GATEWAY, GATEWAY_TIMEOUT, QUOTA_EXCEEDED, SERVICE_UNAVAILABLE, TOKEN_EXPIRED]
EMAILSETTINGS_THROW_LIST = [INVALID_DOMAIN, DOES_NOT_EXIST, SERVICE_NOT_APPLICABLE, BAD_REQUEST, NAME_NOT_VALID, INTERNAL_SERVER_ERROR, INVALID_VALUE]
#
class apiDeprecated(Exception):
  pass
class badRequest(Exception):
  pass
class doesNotExist(Exception):
  pass
class entityExists(Exception):
  pass
class forbidden(Exception):
  pass
class insufficientPermissions(Exception):
  pass
class internalServerError(Exception):
  pass
class invalidDomain(Exception):
  pass
class invalidInput(Exception):
  pass
class invalidValue(Exception):
  pass
class nameNotValid(Exception):
  pass
class notFound(Exception):
  pass
class notImplemented(Exception):
  pass
class preconditionFailed(Exception):
  pass
class serviceNotApplicable(Exception):
  pass

ERROR_CODE_EXCEPTION_MAP = {
  API_DEPRECATED: apiDeprecated,
  BAD_REQUEST: badRequest,
  DOES_NOT_EXIST: doesNotExist,
  ENTITY_EXISTS: entityExists,
  FORBIDDEN: forbidden,
  INSUFFICIENT_PERMISSIONS: insufficientPermissions,
  INTERNAL_SERVER_ERROR: internalServerError,
  INVALID_DOMAIN: invalidDomain,
  INVALID_INPUT: invalidInput,
  INVALID_VALUE: invalidValue,
  NAME_NOT_VALID: nameNotValid,
  NOT_FOUND: notFound,
  NOT_IMPLEMENTED: notImplemented,
  PRECONDITION_FAILED: preconditionFailed,
  SERVICE_NOT_APPLICABLE: serviceNotApplicable,
  }
