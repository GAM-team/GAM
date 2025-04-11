# -*- coding: utf-8 -*-

# Copyright (C) 2024 Ross Scroggs All Rights Reserved.
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

"""GAM command line argument processing

"""

class GamCLArgs():

# GAM entity types as specified on the command line
  ENTITY_BROWSER = 'ids'
  ENTITY_BROWSER_OU = 'browserou'
  ENTITY_BROWSER_OUS = 'browserous'
  ENTITY_BROWSER_QUERIES = 'browserqueies'
  ENTITY_BROWSER_QUERY = 'browserquery'
  ENTITY_CIGROUP = 'cigroup'
  ENTITY_CIGROUPS = 'cigroups'
  ENTITY_CIGROUP_USERS = 'cigroup_users'
  ENTITY_COURSEPARTICIPANTS = 'courseparticipants'
  ENTITY_CROS = 'cros'
  ENTITY_CROS_QUERIES = 'crosqueries'
  ENTITY_CROS_QUERY = 'crosquery'
  ENTITY_CROS_OU = 'cros_ou'
  ENTITY_CROS_OU_AND_CHILDREN = 'cros_ou_and_children'
  ENTITY_CROS_OUS = 'cros_ous'
  ENTITY_CROS_OUS_AND_CHILDREN = 'cros_ous_and_children'
  ENTITY_CROS_OU_QUERY = 'cros_ou_query'
  ENTITY_CROS_OU_AND_CHILDREN_QUERY = 'cros_ou_and_children_query'
  ENTITY_CROS_OUS_QUERY = 'cros_ous_query'
  ENTITY_CROS_OUS_AND_CHILDREN_QUERY = 'cros_ous_and_children_query'
  ENTITY_CROS_OU_QUERIES = 'cros_ou_queries'
  ENTITY_CROS_OU_AND_CHILDREN_QUERIES = 'cros_ou_and_children_queries'
  ENTITY_CROS_OUS_QUERIES = 'cros_ous_queries'
  ENTITY_CROS_OUS_AND_CHILDREN_QUERIES = 'cros_ous_and_children_queries'
  ENTITY_CROS_SN = 'cros_sn'
  ENTITY_DOMAINS = 'domains'
  ENTITY_DOMAINS_NS = 'domains_ns'
  ENTITY_DOMAINS_SUSP = 'domains_susp'
  ENTITY_GROUP = 'group'
  ENTITY_GROUP_INDE = 'group_inde'
  ENTITY_GROUP_NS = 'group_ns'
  ENTITY_GROUP_SUSP = 'group_susp'
  ENTITY_GROUPS = 'groups'
  ENTITY_GROUPS_INDE = 'groups_inde'
  ENTITY_GROUPS_NS = 'groups_ns'
  ENTITY_GROUPS_SUSP = 'groups_susp'
  ENTITY_GROUP_USERS = 'group_users'
  ENTITY_GROUP_USERS_NS = 'group_users_ns'
  ENTITY_GROUP_USERS_SUSP = 'group_users_susp'
  ENTITY_GROUP_USERS_SELECT = 'group_users_select'
  ENTITY_LICENSES = 'licenses'
  ENTITY_OAUTHUSER = 'oauthuser'
  ENTITY_OU = 'ou'
  ENTITY_OU_NS = 'ou_ns'
  ENTITY_OU_SUSP = 'ou_susp'
  ENTITY_OU_AND_CHILDREN = 'ou_and_children'
  ENTITY_OU_AND_CHILDREN_NS = 'ou_and_children_ns'
  ENTITY_OU_AND_CHILDREN_SUSP = 'ou_and_children_susp'
  ENTITY_OUS = 'ous'
  ENTITY_OUS_NS = 'ous_ns'
  ENTITY_OUS_SUSP = 'ous_susp'
  ENTITY_OUS_AND_CHILDREN = 'ous_and_children'
  ENTITY_OUS_AND_CHILDREN_NS = 'ous_and_children_ns'
  ENTITY_OUS_AND_CHILDREN_SUSP = 'ous_and_children_susp'
  ENTITY_QUERIES = 'queries'
  ENTITY_QUERY = 'query'
  ENTITY_STUDENTS = 'students'
  ENTITY_TEACHERS = 'teachers'
  ENTITY_USER = 'user'
  ENTITY_USERS = 'users'
  ENTITY_USERS_NS = 'users_ns'
  ENTITY_USERS_NS_SUSP = 'users_ns_susp'
  ENTITY_USERS_SUSP = 'users_susp'
#
  BROWSER_ENTITIES = [
    ENTITY_BROWSER,
    ENTITY_BROWSER_QUERIES,
    ENTITY_BROWSER_QUERY,
    ENTITY_BROWSER_OU,
    ENTITY_BROWSER_OUS,
    ]
  CROS_ENTITIES = [
    ENTITY_CROS,
    ENTITY_CROS_QUERIES,
    ENTITY_CROS_QUERY,
    ENTITY_CROS_OU,
    ENTITY_CROS_OU_AND_CHILDREN,
    ENTITY_CROS_OUS,
    ENTITY_CROS_OUS_AND_CHILDREN,
    ENTITY_CROS_OU_QUERY,
    ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    ENTITY_CROS_OUS_QUERY,
    ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    ENTITY_CROS_OU_QUERIES,
    ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    ENTITY_CROS_OUS_QUERIES,
    ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    ENTITY_CROS_SN,
    ]
  USER_ENTITIES = [
    ENTITY_CIGROUP,
    ENTITY_CIGROUPS,
    ENTITY_CIGROUP_USERS,
    ENTITY_COURSEPARTICIPANTS,
    ENTITY_DOMAINS,
    ENTITY_DOMAINS_NS,
    ENTITY_DOMAINS_SUSP,
    ENTITY_GROUP,
    ENTITY_GROUP_INDE,
    ENTITY_GROUP_NS,
    ENTITY_GROUP_SUSP,
    ENTITY_GROUPS,
    ENTITY_GROUPS_INDE,
    ENTITY_GROUPS_NS,
    ENTITY_GROUPS_SUSP,
    ENTITY_GROUP_USERS,
    ENTITY_GROUP_USERS_NS,
    ENTITY_GROUP_USERS_SUSP,
    ENTITY_GROUP_USERS_SELECT,
    ENTITY_LICENSES,
    ENTITY_OAUTHUSER,
    ENTITY_OU,
    ENTITY_OU_NS,
    ENTITY_OU_SUSP,
    ENTITY_OU_AND_CHILDREN,
    ENTITY_OU_AND_CHILDREN_NS,
    ENTITY_OU_AND_CHILDREN_SUSP,
    ENTITY_OUS,
    ENTITY_OUS_NS,
    ENTITY_OUS_SUSP,
    ENTITY_OUS_AND_CHILDREN,
    ENTITY_OUS_AND_CHILDREN_NS,
    ENTITY_OUS_AND_CHILDREN_SUSP,
    ENTITY_QUERIES,
    ENTITY_QUERY,
    ENTITY_STUDENTS,
    ENTITY_TEACHERS,
    ENTITY_USER,
    ENTITY_USERS,
    ]
# Aliases for CL entity types
  ENTITY_ALIAS_MAP = {
    'browsers': ENTITY_BROWSER,
    'browserorg': ENTITY_BROWSER_OU,
    'browserorgs': ENTITY_BROWSER_OUS,
    'crosorg': ENTITY_CROS_OU,
    'crosorg_and_child': ENTITY_CROS_OU_AND_CHILDREN,
    'crosorg_and_children': ENTITY_CROS_OU_AND_CHILDREN,
    'crosorgs': ENTITY_CROS_OUS,
    'crosorgs_and_child': ENTITY_CROS_OUS_AND_CHILDREN,
    'crosorgs_and_children': ENTITY_CROS_OUS_AND_CHILDREN,
    'crosou_and_child': ENTITY_CROS_OU_AND_CHILDREN,
    'crosou_and_childen': ENTITY_CROS_OU_AND_CHILDREN,
    'crosous_and_child': ENTITY_CROS_OUS_AND_CHILDREN,
    'crosous_and_children': ENTITY_CROS_OUS_AND_CHILDREN,
    'cros_org': ENTITY_CROS_OU,
    'cros_org_and_child': ENTITY_CROS_OU_AND_CHILDREN,
    'cros_org_and_children': ENTITY_CROS_OU_AND_CHILDREN,
    'cros_orgs': ENTITY_CROS_OUS,
    'cros_orgs_and_child': ENTITY_CROS_OUS_AND_CHILDREN,
    'cros_orgs_and_children': ENTITY_CROS_OUS_AND_CHILDREN,
    'cros_ou_and_child': ENTITY_CROS_OU_AND_CHILDREN,
    'cros_ou_and_childen': ENTITY_CROS_OU_AND_CHILDREN,
    'cros_ous_and_child': ENTITY_CROS_OUS_AND_CHILDREN,
    'cros_ous_and_children': ENTITY_CROS_OUS_AND_CHILDREN,
    'crosorg_query': ENTITY_CROS_OU_QUERY,
    'crosorg_and_child_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'crosorg_and_children_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'crosorgs_query': ENTITY_CROS_OUS_QUERY,
    'crosorgs_and_child_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'crosorgs_and_children_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'crosou_and_child_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'crosou_and_childen_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'crosous_and_child_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'crosous_and_children_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'cros_org_query': ENTITY_CROS_OU_QUERY,
    'cros_org_and_child_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'cros_org_and_children_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'cros_orgs_query': ENTITY_CROS_OUS_QUERY,
    'cros_orgs_and_child_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'cros_orgs_and_children_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'cros_ou_and_child_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'cros_ou_and_childen_query': ENTITY_CROS_OU_AND_CHILDREN_QUERY,
    'cros_ous_and_child_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'cros_ous_and_children_query': ENTITY_CROS_OUS_AND_CHILDREN_QUERY,
    'crosorg_queries': ENTITY_CROS_OU_QUERIES,
    'crosorg_and_child_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'crosorg_and_children_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'crosorgs_queries': ENTITY_CROS_OUS_QUERIES,
    'crosorgs_and_child_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'crosorgs_and_children_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'crosou_and_child_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'crosou_and_childen_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'crosous_and_child_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'crosous_and_children_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'cros_org_queries': ENTITY_CROS_OU_QUERIES,
    'cros_org_and_child_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'cros_org_and_children_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'cros_orgs_queries': ENTITY_CROS_OUS_QUERIES,
    'cros_orgs_and_child_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'cros_orgs_and_children_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'cros_ou_and_child_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'cros_ou_and_childen_queries': ENTITY_CROS_OU_AND_CHILDREN_QUERIES,
    'cros_ous_and_child_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'cros_ous_and_children_queries': ENTITY_CROS_OUS_AND_CHILDREN_QUERIES,
    'license': ENTITY_LICENSES,
    'licence': ENTITY_LICENSES,
    'licences': ENTITY_LICENSES,
    'org': ENTITY_OU,
    'org_ns': ENTITY_OU_NS,
    'org_susp': ENTITY_OU_SUSP,
    'org_and_child': ENTITY_OU_AND_CHILDREN,
    'org_and_child_ns': ENTITY_OU_AND_CHILDREN_NS,
    'org_and_child_susp': ENTITY_OU_AND_CHILDREN_SUSP,
    'org_and_children': ENTITY_OU_AND_CHILDREN,
    'org_and_children_ns': ENTITY_OU_AND_CHILDREN_NS,
    'org_and_children_susp': ENTITY_OU_AND_CHILDREN_SUSP,
    'orgs': ENTITY_OUS,
    'orgs_ns': ENTITY_OUS_NS,
    'orgs_susp': ENTITY_OUS_SUSP,
    'orgs_and_child': ENTITY_OUS_AND_CHILDREN,
    'orgs_and_child_ns': ENTITY_OUS_AND_CHILDREN_NS,
    'orgs_and_child_susp': ENTITY_OUS_AND_CHILDREN_SUSP,
    'orgs_and_children': ENTITY_OUS_AND_CHILDREN,
    'orgs_and_children_ns': ENTITY_OUS_AND_CHILDREN_NS,
    'orgs_and_children_susp': ENTITY_OUS_AND_CHILDREN_SUSP,
    'ou_and_child': ENTITY_OU_AND_CHILDREN,
    'ou_and_child_ns': ENTITY_OU_AND_CHILDREN_NS,
    'ou_and_child_susp': ENTITY_OU_AND_CHILDREN_SUSP,
    'ous_and_child': ENTITY_OUS_AND_CHILDREN,
    'ous_and_child_ns': ENTITY_OUS_AND_CHILDREN_NS,
    'ous_and_child_susp': ENTITY_OUS_AND_CHILDREN_SUSP,
    }
# CL entity source selectors
  ENTITY_SELECTOR_ALL = 'all'
  ENTITY_SELECTOR_CSV = 'csv'
  ENTITY_SELECTOR_CSVDATAFILE = 'csvdatafile'
  ENTITY_SELECTOR_CSVFILE = 'csvfile'
  ENTITY_SELECTOR_FILE = 'file'
  ENTITY_SELECTOR_DATAFILE = 'datafile'
  ENTITY_SELECTOR_CROSCSV = 'croscsv'
  ENTITY_SELECTOR_CROSCSV_SN = 'croscsv_sn'
  ENTITY_SELECTOR_CROSCSVFILE = 'croscsvfile'
  ENTITY_SELECTOR_CROSCSVFILE_SN = 'croscsvfile_sn'
  ENTITY_SELECTOR_CROSFILE = 'crosfile'
  ENTITY_SELECTOR_CROSFILE_SN = 'crosfile_sn'
  ENTITY_SELECTOR_CSVKMD = 'csvkmd'
  ENTITY_SELECTOR_CSVSUBKEY = 'csvsubkey'
  ENTITY_SELECTOR_CSVDATA = 'csvdata'
  ENTITY_SELECTOR_CROSCSVDATA = 'croscsvdata'
#
  SERVICE_ACCOUNT_ONLY_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_CSVDATAFILE,
    ENTITY_SELECTOR_CSVKMD,
    ENTITY_SELECTOR_CSVSUBKEY,
    ENTITY_SELECTOR_DATAFILE,
    ]
  ENTITY_LIST_SELECTORS = [
    ENTITY_SELECTOR_CSVKMD,
    ENTITY_SELECTOR_CSVSUBKEY,
    ENTITY_SELECTOR_CSV,
    ENTITY_SELECTOR_CSVFILE,
    ENTITY_SELECTOR_FILE,
    ENTITY_SELECTOR_CSVDATA,
    ]
  BASE_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_ALL,
    ENTITY_SELECTOR_CSVDATAFILE,
    ENTITY_SELECTOR_CSVKMD,
    ENTITY_SELECTOR_CSVSUBKEY,
    ENTITY_SELECTOR_DATAFILE,
    ]
  BROWSER_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_CSV,
    ENTITY_SELECTOR_CSVFILE,
    ENTITY_SELECTOR_FILE,
    ]
  CROS_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_CROSCSV,
    ENTITY_SELECTOR_CROSCSV_SN,
    ENTITY_SELECTOR_CROSCSVFILE,
    ENTITY_SELECTOR_CROSCSVFILE_SN,
    ENTITY_SELECTOR_CROSFILE,
    ENTITY_SELECTOR_CROSFILE_SN,
    ]
  USER_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_CSV,
    ENTITY_SELECTOR_CSVFILE,
    ENTITY_SELECTOR_FILE,
    ]
  CROS_CSVDATA_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_CROSCSVDATA,
    ]
  USER_CSVDATA_ENTITY_SELECTORS = [
    ENTITY_SELECTOR_CSVDATA,
    ]
# Allowed values for CL source selector all
  CROS_ENTITY_SELECTOR_ALL_SUBTYPES = [
    ENTITY_CROS,
    ]
  USER_ENTITY_SELECTOR_ALL_SUBTYPES = [
    ENTITY_USERS,
    ENTITY_USERS_NS,
    ENTITY_USERS_NS_SUSP,
    ENTITY_USERS_SUSP,
    ]
#
  ENTITY_ALL_CROS = ENTITY_SELECTOR_ALL+' '+ENTITY_CROS
  ENTITY_ALL_USERS = ENTITY_SELECTOR_ALL+' '+ENTITY_USERS
  ENTITY_ALL_USERS_NS = ENTITY_SELECTOR_ALL+' '+ENTITY_USERS_NS
  ENTITY_ALL_USERS_NS_SUSP = ENTITY_SELECTOR_ALL+' '+ENTITY_USERS_NS_SUSP
  ENTITY_ALL_USERS_SUSP = ENTITY_SELECTOR_ALL+' '+ENTITY_USERS_SUSP
#
  ALL_USERS_QUERY_MAP = {
    ENTITY_ALL_USERS: 'isSuspended=False',
    ENTITY_ALL_USERS_NS: 'isSuspended=False',
    ENTITY_ALL_USERS_NS_SUSP: None,
    ENTITY_ALL_USERS_SUSP: 'isSuspended=True',
  }
#
  ENTITY_SELECTOR_ALL_SUBTYPES_MAP = {
    ENTITY_CROS: ENTITY_ALL_CROS,
    ENTITY_USERS: ENTITY_ALL_USERS,
    ENTITY_USERS_NS: ENTITY_ALL_USERS_NS,
    ENTITY_USERS_NS_SUSP: ENTITY_ALL_USERS_NS_SUSP,
    ENTITY_USERS_SUSP: ENTITY_ALL_USERS_SUSP,
    }
# Allowed values for CL source selector datafile, csvkmd
  CROS_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES = [
    ENTITY_CROS,
    ENTITY_CROS_OUS,
    ENTITY_CROS_OUS_AND_CHILDREN,
    ENTITY_CROS_SN,
    ]
  USER_ENTITY_SELECTOR_DATAFILE_CSVKMD_SUBTYPES = [
    ENTITY_USERS,
    ENTITY_CIGROUPS,
    ENTITY_CIGROUP_USERS,
    ENTITY_DOMAINS,
    ENTITY_DOMAINS_NS,
    ENTITY_DOMAINS_SUSP,
    ENTITY_GROUPS,
    ENTITY_GROUPS_INDE,
    ENTITY_GROUPS_NS,
    ENTITY_GROUPS_SUSP,
    ENTITY_GROUP_USERS,
    ENTITY_GROUP_USERS_NS,
    ENTITY_GROUP_USERS_SUSP,
    ENTITY_GROUP_USERS_SELECT,
    ENTITY_OUS,
    ENTITY_OUS_NS,
    ENTITY_OUS_SUSP,
    ENTITY_OUS_AND_CHILDREN,
    ENTITY_OUS_AND_CHILDREN_NS,
    ENTITY_OUS_AND_CHILDREN_SUSP,
    ENTITY_COURSEPARTICIPANTS,
    ENTITY_STUDENTS,
    ENTITY_TEACHERS,
    ]
# Batch file commands
  EXECUTE_CMD = 'execute'
  GAM_CMD = 'gam'
  COMMIT_BATCH_CMD = 'commit-batch'
  PRINT_CMD = 'print'
  SET_CMD = 'set'
  CLEAR_CMD = 'clear'
  SLEEP_CMD = 'sleep'
# Command line batch/csv/loop/tbatch keywords
  BATCH_CMD = 'batch'
  CSV_CMD = 'csv'
  CSVTEST_CMD = 'csvtest'
  LOOP_CMD = 'loop'
  TBATCH_CMD = 'tbatch'
# Command line select/showsections/selectfilter/selectoutputfilter/selectinputfilter/config/redirect arguments
  SELECT_CMD = 'select'
  SHOWSECTIONS_CMD = 'showsections'
  SELECTFILTER_CMD = 'selectfilter'
  SELECTOUTPUTFILTER_CMD = 'selectoutputfilter'
  SELECTINPUTFILTER_CMD = 'selectinputfilter'
  CONFIG_CMD = 'config'
  MULTIPROCESSEXIT_CMD = 'multiprocessexit'
  REDIRECT_CMD = 'redirect'
  GAM_META_COMMANDS = [SELECT_CMD, SHOWSECTIONS_CMD, SELECTFILTER_CMD, SELECTOUTPUTFILTER_CMD, SELECTINPUTFILTER_CMD,
                       CONFIG_CMD, MULTIPROCESSEXIT_CMD, REDIRECT_CMD]
# Command line arguments
  ARG_3LO = '3lo'
  ARG_ACL = 'acl'
  ARG_ACLS = 'acls'
  ARG_ADDRESSES = 'addresses'
  ARG_ADMIN = 'admin'
  ARG_ADMINS = 'admins'
  ARG_ADMINROLE = 'adminrole'
  ARG_ADMINROLES = 'adminroles'
  ARG_ALERT = 'alert'
  ARG_ALERTS = 'alerts'
  ARG_ALERTFEEDBACK = 'alertfeedback'
  ARG_ALERTFEEDBACKS = 'alertfeedbacks'
  ARG_ALERTSFEEDBACK = 'alertsfeedback'
  ARG_ALIAS = 'alias'
  ARG_ALIASES = 'aliases'
  ARG_ALIASDOMAIN = 'aliasdomain'
  ARG_ALIASDOMAINS = 'aliasdomains'
  ARG_ANALYTICACCOUNT = 'analyticaccount'
  ARG_ANALYTICACCOUNTS = 'analyticaccounts'
  ARG_ANALYTICACCOUNTSUMMARY = 'analyticaccountsummary'
  ARG_ANALYTICACCOUNTSUMMARIES = 'analyticaccountsummaries'
  ARG_ANALYTICDATASTREAM = 'analyticdatastream'
  ARG_ANALYTICDATASTREAMS = 'analyticdatastreams'
  ARG_ANALYTICPROPERTY = 'analyticproperty'
  ARG_ANALYTICPROPERTIES = 'analyticproperties'
  ARG_ANALYTICUAPROPERTY = 'analyticuaproperty'
  ARG_ANALYTICUAPROPERTIES = 'analyticuaproperties'
  ARG_API = 'api'
  ARG_APIS = 'apis'
  ARG_APIPROJECT = 'apiproject'
  ARG_APPACCESSSETTINGS = 'appaccesssettings'
  ARG_APPDETAILS = 'appdetails'
  ARG_APPLICATIONSPECIFICPASSWORDS = 'applicationspecificpasswords'
  ARG_ASP = 'asp'
  ARG_ASPS = 'asps'
  ARG_BACKUPCODE = 'backupcode'
  ARG_BACKUPCODES = 'backupcodes'
  ARG_BROWSER = 'browser'
  ARG_BROWSERS = 'browsers'
  ARG_BROWSERTOKEN = 'browsertoken'
  ARG_BROWSERTOKENS = 'browsertokens'
  ARG_BUCKET = 'bucket'
  ARG_BUCKETS = 'buckets'
  ARG_BUILDING = 'building'
  ARG_BUILDINGS = 'buildings'
  ARG_CAALEVEL = 'caalevel'
  ARG_CAALEVELS = 'caalevels'
  ARG_CALATTENDEES = 'calattendees'
  ARG_CALENDAR = 'calendar'
  ARG_CALENDARS = 'calendars'
  ARG_CALENDARACL = 'calendaracl'
  ARG_CALENDARACLS = 'calendaracls'
  ARG_CALENDARTRASH = 'calendartrash'
  ARG_CALSETTINGS = 'calsettings'
  ARG_CHANNELCUSTOMER = 'channelcustomer'
  ARG_CHANNELCUSTOMERS = 'channelcustomers'
  ARG_CHANNELCUSTOMERENTITLEMENT = 'channelcustomerentitlement'
  ARG_CHANNELCUSTOMERENTITLEMENTS = 'channelcustomerentitlements'
  ARG_CHANNELOFFER = 'channeloffer'
  ARG_CHANNELOFFERS = 'channeloffers'
  ARG_CHANNELPRODUCT = 'channelproduct'
  ARG_CHANNELPRODUCTS = 'channelproducts'
  ARG_CHANNELSKU = 'channelsku'
  ARG_CHANNELSKUS = 'channelskus'
  ARG_CHAT = 'chat'
  ARG_CHATEVENT = 'chatevent'
  ARG_CHATEVENTS = 'chatevents'
  ARG_CHATMEMBER = 'chatmember'
  ARG_CHATMEMBERS = 'chatmembers'
  ARG_CHATMESSAGE = 'chatmessage'
  ARG_CHATMESSAGES = 'chatmessages'
  ARG_CHATSPACE = 'chatspace'
  ARG_CHATSPACES = 'chatspaces'
  ARG_CHATSPACEDM = 'chatspacedm'
  ARG_CHROMEAPP = 'chromeapp'
  ARG_CHROMEAPPS = 'chromeapps'
  ARG_CHROMEAPPDEVICES = 'chromeappdevices'
  ARG_CHROMEAUES = 'chromeaues'
  ARG_CHROMEHISTORY = 'chromehistory'
  ARG_CHROMENEEDSATTN = 'chromeneedsattn'
  ARG_CHROMENETWORK = 'chromenetwork'
  ARG_CHROMENETWORKS = 'chromenetworks'
  ARG_CHROMEPOLICYIMAGE = 'chromepolicyimage'
  ARG_CHROMEPOLICY = 'chromepolicy'
  ARG_CHROMEPOLICIES = 'chromepolicies'
  ARG_CHROMEPROFILE = 'chromeprofile'
  ARG_CHROMEPROFILES = 'chromeprofiles'
  ARG_CHROMESCHEMA = 'chromeschema'
  ARG_CHROMESCHEMAS = 'chromeschemas'
  ARG_CHROMESNVALIDITY = 'chromesnvalidity'
  ARG_CHROMEVERSIONS = 'chromeversions'
  ARG_CIGROUP = 'cigroup'
  ARG_CIGROUPS = 'cigroups'
  ARG_CIGROUPMEMBERS = 'cigroupmembers'
  ARG_CIGROUPSMEMBERS = 'cigroupsmembers'
  ARG_CIMEMBER = 'cimember'
  ARG_CIMEMBERS = 'cimembers'
  ARG_CIPOLICY = 'policy'
  ARG_CIPOLICIES = 'policies'
  ARG_CLASSIFICATIONLABEL = 'classificationlabel'
  ARG_CLASSIFICATIONLABELS = 'classificationlabels'
  ARG_CLASSIFICATIONLABELPERMISSION = 'classificationlabelpermission'
  ARG_CLASSIFICATIONLABELPERMISSIONS = 'classificationlabelpermissions'
  ARG_CLASS = 'class'
  ARG_CLASSES = 'classes'
  ARG_CLASSPARTICIPANTS = 'classparticipants'
  ARG_CLASSROOMINVITATION = 'classroominvitation'
  ARG_CLASSROOMINVITATIONS = 'classroominvitations'
  ARG_CLASSROOMOAUTH2 = 'classroomoauth2'
  ARG_CLASSROOMPROFILE = 'classroomprofile'
  ARG_CONTACT = 'contact'
  ARG_CONTACTS = 'contacts'
  ARG_CONTACTDELEGATE = 'contactdelegate'
  ARG_CONTACTDELEGATES = 'contactdelegates'
  ARG_CONTACTGROUP = 'contactgroup'
  ARG_CONTACTGROUPS = 'contactgroups'
  ARG_CONTACTPHOTO = 'contactphoto'
  ARG_CONTACTPHOTOS = 'contactphotos'
  ARG_COUNT = 'count'
  ARG_COUNTS = 'counts'
  ARG_COURSE = 'course'
  ARG_COURSES = 'courses'
  ARG_COURSEANNOUNCEMENTS = 'courseannouncements'
  ARG_COURSEMATERIALS = 'coursematerials'
  ARG_COURSEPARTICIPANTS = 'courseparticipants'
  ARG_COURSESUBMISSIONS = 'coursesubmissions'
  ARG_COURSETOPICS = 'coursetopics'
  ARG_COURSEWORK = 'coursework'
  ARG_CROS = 'cros'
  ARG_CROSES = 'croses'
  ARG_CROSACTIVITY = 'crosactivity'
  ARG_CROSTELEMETRY = 'crostelemetry'
  ARG_CSEIDENTITY = 'cseidentity'
  ARG_CSEIDENTITIES = 'cseidentities'
  ARG_CSEKEYPAIR = 'csekeypair'
  ARG_CSEKEYPAIRS = 'csekeypairs'
  ARG_CURRENTPROJECTID = 'currentprojectid'
  ARG_CUSTOMER = 'customer'
  ARG_DATASTUDIOASSET = 'datastudioasset'
  ARG_DATASTUDIOASSETS = 'datastudioassets'
  ARG_DATASTUDIOPERMISSION = 'datastudiopermission'
  ARG_DATASTUDIOPERMISSIONS = 'datastudiopermissions'
  ARG_LOOKERSTUDIOASSET = 'lookerstudioasset'
  ARG_LOOKERSTUDIOASSETS = 'lookerstudioassets'
  ARG_LOOKERSTUDIOPERMISSION = 'lookerstudiopermission'
  ARG_LOOKERSTUDIOPERMISSIONS = 'lookerstudiopermissions'
  ARG_DATATRANSFER = 'datatransfer'
  ARG_DATATRANSFERS = 'datatransfers'
  ARG_DELEGATE = 'delegate'
  ARG_DELEGATES = 'delegates'
  ARG_DEVICE = 'device'
  ARG_DEVICES = 'devices'
  ARG_DEVICEFILE = 'devicefile'
  ARG_DEVICEFILES = 'devicefiles'
  ARG_DEVICEUSER = 'deviceuser'
  ARG_DEVICEUSERS = 'deviceusers'
  ARG_DEVICEUSERSTATE = 'deviceuserstate'
  ARG_DISKUSAGE = 'diskusage'
  ARG_DOCUMENT = 'document'
  ARG_DOMAIN = 'domain'
  ARG_DOMAINS = 'domains'
  ARG_DOMAINALIAS = 'domainalias'
  ARG_DOMAINALIASES = 'domainaliases'
  ARG_DOMAINCONTACT = 'domaincontact'
  ARG_DOMAINCONTACTS = 'domaincontacts'
  ARG_DOMAINCONTACTPHOTO = 'domaincontactphoto'
  ARG_DOMAINCONTACTPHOTOS = 'domaincontactphotas'
  ARG_DOMAINPROFILE = 'domainprofile'
  ARG_DOMAINPROFILES = 'domainprofiles'
  ARG_DRIVE = 'drive'
  ARG_DRIVEACTIVITY = 'driveactivity'
  ARG_DRIVEFILE = 'drivefile'
  ARG_DRIVEFILEACL = 'drivefileacl'
  ARG_DRIVEFILEACLS = 'drivefileacls'
  ARG_DRIVEFILESHORTCUT = 'drivefileshortcut'
  ARG_DRIVEFILESHORTCUTS = 'drivefileshortcuts'
  ARG_DRIVEFOLDERPATH = 'drivefolderpath'
  ARG_DRIVELABEL = 'drivelabel'
  ARG_DRIVELABELS = 'drivelabels'
  ARG_DRIVELABELPERMISSION = 'drivelabelpermission'
  ARG_DRIVELABELPERMISSIONS = 'drivelabelpermissions'
  ARG_DRIVELASTMODIFICATION = 'drivelastmodification'
  ARG_DRIVELASTMODIFICATIONS = 'drivelastmodifications'
  ARG_DRIVESETTINGS = 'drivesettings'
  ARG_DRIVETRASH = 'drivetrash'
  ARG_EMPTYDRIVEFOLDERS = 'emptydrivefolders'
  ARG_EVENT = 'event'
  ARG_EVENTS = 'events'
  ARG_EXPORT = 'export'
  ARG_EXPORTS = 'exports'
  ARG_FEATURE = 'feature'
  ARG_FEATURES = 'features'
  ARG_FILECOMMENT = 'filecomment'
  ARG_FILECOMMENTS = 'filecomments'
  ARG_FILECOUNT = 'filecount'
  ARG_FILECOUNTS = 'filecounts'
  ARG_FILEDRIVELABEL = 'filedrivelabel'
  ARG_FILEDRIVELABELS = 'filedrivelabels'
  ARG_FILEINFO = 'fileinfo'
  ARG_FILELIST = 'filelist'
  ARG_FILEPARENTTREE = 'fileparenttree'
  ARG_FILEPATH = 'filepath'
  ARG_FILEPATHS = 'filepaths'
  ARG_FILEREVISION = 'filerevision'
  ARG_FILEREVISIONS = 'filerevisions'
  ARG_FILESHARECOUNT = 'filesharecount'
  ARG_FILESHARECOUNTS = 'filesharecounts'
  ARG_FILETREE = 'filetree'
  ARG_FILTER = 'filter'
  ARG_FILTERS = 'filters'
  ARG_FOCUSTIME = 'focustime'
  ARG_FOCUSTIMES = 'focustimes'
  ARG_FORM = 'form'
  ARG_FORMS = 'forms'
  ARG_FORMRESPONSE = 'formresponse'
  ARG_FORMRESPONSES = 'formresponses'
  ARG_FORWARD = 'forward'
  ARG_FORWARDS = 'forwards'
  ARG_FORWARDINGADDRESS = 'forwardingaddress'
  ARG_FORWARDINGADDRESSES = 'forwardingaddresses'
  ARG_GAL = 'gal'
  ARG_GCPFOLDER = 'gcpfolder'
  ARG_GCPSERVICEACCOUNT = 'gcpserviceaccount'
  ARG_GMAIL = 'gmail'
  ARG_GMAILPROFILE = 'gmailprofile'
  ARG_GROUP = 'group'
  ARG_GROUPS = 'groups'
  ARG_GROUPLIST = 'grouplist'
  ARG_GROUPSLIST = 'groupslist'
  ARG_GROUPMEMBERS = 'groupmembers'
  ARG_GROUPSMEMBERS = 'groupsmembers'
  ARG_GROUPTREE = 'grouptree'
  ARG_GUARDIAN = 'guardian'
  ARG_GUARDIANS = 'guardians'
  ARG_GUARDIANINVITE = 'guardianinvite'
  ARG_GUARDIANINVITATION = 'guardianinvitation'
  ARG_GUARDIANINVITATIONS = 'guardianinvitations'
  ARG_HOLD = 'hold'
  ARG_HOLDS = 'holds'
  ARG_IMAP = 'imap'
  ARG_IMAP4 = 'imap4'
  ARG_INBOUNDSSOASSIGNMENT = 'inboundssoassignment'
  ARG_INBOUNDSSOASSIGNMENTS = 'inboundssoassignments'
  ARG_INBOUNDSSOCREDENTIAL = 'inboundssocredential'
  ARG_INBOUNDSSOCREDENTIALS = 'inboundssocredentials'
  ARG_INBOUNDSSOPROFILE = 'inboundssoprofile'
  ARG_INBOUNDSSOPROFILES = 'inboundssoprofiles'
  ARG_INSTANCE = 'instance'
  ARG_INVITEGUARDIAN = 'inviteguardian'
  ARG_ISINVITABLE = 'isinvitable'
  ARG_LABEL = 'label'
  ARG_LABELS = 'labels'
  ARG_LABELLIST = 'labellist'
  ARG_LABELID = 'labelid'
  ARG_LABELIDLIST = 'labelidlist'
  ARG_LABELSETTINGS = 'labelsettings'
  ARG_LANGUAGE = 'language'
  ARG_LICENCE = 'licence'
  ARG_LICENCES = 'licences'
  ARG_LICENSE = 'license'
  ARG_LICENSES = 'licenses'
  ARG_MATTER = 'matter'
  ARG_MATTERS = 'matters'
  ARG_MEETSPACE = 'meetspace'
  ARG_MEETSPACES = 'meetspaces'
  ARG_MEETCONFERENCE = 'meetconference'
  ARG_MEETCONFERENCES = 'meetconferences'
  ARG_MEETPARTICIPANT = 'meetparticipant'
  ARG_MEETPARTICIPANTS = 'meetparticipants'
  ARG_MEETRECORDING = 'meetrecording'
  ARG_MEETRECORDINGS = 'meetrecordings'
  ARG_MEETTRANSCRIPT = 'meettranscript'
  ARG_MEETTRANSCRIPTS = 'meettranscripts'
  ARG_MEMBER = 'member'
  ARG_MEMBERS = 'members'
  ARG_MESSAGE = 'message'
  ARG_MESSAGES = 'messages'
  ARG_MESSAGEHISTORY = 'messagehistory'
  ARG_MOBILE = 'mobile'
  ARG_MOBILES = 'mobiles'
  ARG_NICKNAME = 'nickname'
  ARG_NICKNAMES = 'nicknames'
  ARG_NOTE = 'note'
  ARG_NOTES = 'notes'
  ARG_NOTEACL = 'noteacl'
  ARG_NOTEACLS = 'noteacls'
  ARG_NOTESACL = 'notesacl'
  ARG_NOTESACLS = 'notesacls'
  ARG_NOTEATTACHMENT = 'noteattachment'
  ARG_NOTEATTACHMENTS = 'noteattachments'
  ARG_OAUTH = 'oauth'
  ARG_ORG = 'org'
  ARG_ORGS = 'orgs'
  ARG_ORGTREE = 'orgtree'
  ARG_ORGUNIT = 'orgunit'
  ARG_ORGUNITS = 'orgunits'
  ARG_ORGUNITSHAREDDRIVE = 'orgunitshareddrive'
  ARG_ORGUNITSHAREDDRIVES = 'orgunitshareddrives'
  ARG_ORPHANS = 'orphans'
  ARG_OTHERCONTACT = 'othercontact'
  ARG_OTHERCONTACTS = 'othercontacts'
  ARG_OU = 'ou'
  ARG_OUS = 'ous'
  ARG_OUSHAREDDRIVE = 'oushareddrive'
  ARG_OUSHAREDDRIVES = 'oushareddrives'
  ARG_OUTOFOFFICE = 'outofoffice'
  ARG_OUTOFOFFICES = 'outofoffices'
  ARG_OUTREE = 'outree'
  ARG_OWNERSHIP = 'ownership'
  ARG_PARTICIPANTS = 'participants'
  ARG_PEOPLE = 'people'
  ARG_PEOPLECONTACT = 'peoplecontact'
  ARG_PEOPLECONTACTS = 'peoplecontacts'
  ARG_PEOPLECONTACTGROUP = 'peoplecontactgroup'
  ARG_PEOPLECONTACTGROUPS = 'peoplecontactgroups'
  ARG_PEOPLECONTACTPHOTO = 'peoplecontactphoto'
  ARG_PEOPLECONTACTPHOTOS = 'peoplecontactphotos'
  ARG_PEOPLEOTHERCONTACT = 'peopleothercontact'
  ARG_PEOPLEOTHERCONTACTS = 'peopleothercontacts'
  ARG_PEOPLEPROFILE = 'peopleprofile'
  ARG_PEOPLEPROFILES = 'peopleprofiles'
  ARG_PERMISSION = 'permission'
  ARG_PERMISSIONS = 'permissions'
  ARG_PHOTO = 'photo'
  ARG_POP = 'pop'
  ARG_POP3 = 'pop3'
  ARG_PRINTER = 'printer'
  ARG_PRINTERS = 'printers'
  ARG_PRINTERMODEL = 'printermodel'
  ARG_PRINTERMODELS = 'printermodels'
  ARG_PRIVILEGES = 'privileges'
  ARG_PROFILE = 'profile'
  ARG_PROFILE_PHOTO = 'profilephoto'
  ARG_PROJECT = 'project'
  ARG_PROJECTS = 'projects'
  ARG_RESELLERCUSTOMER = 'resellercustomer'
  ARG_RESELLERCUSTOMERS = 'resellercustomers'
  ARG_RESELLERSUBSCRIPTION = 'resellersubscription'
  ARG_RESELLERSUBSCRIPTIONS = 'resellersubscriptions'
  ARG_RESETPIV = 'resetpiv'
  ARG_RESOLDCUSTOMER = 'resoldcustomer'
  ARG_RESOLDCUSTOMERS = 'resoldcustomers'
  ARG_RESOLDSUBSCRIPTION = 'resoldsubscription'
  ARG_RESOLDSUBSCRIPTIONS = 'resoldsubscriptions'
  ARG_RESOURCE = 'resource'
  ARG_RESOURCES = 'resources'
  ARG_ROLE = 'role'
  ARG_ROLES = 'roles'
  ARG_SAKEY = 'sakey'
  ARG_SAKEYS = 'sakeys'
  ARG_SCHEMA = 'schema'
  ARG_SCHEMAS = 'schemas'
  ARG_SECCALS = 'seccals'
  ARG_SENDAS = 'sendas'
  ARG_SERVICEACCOUNT = 'serviceaccount'
  ARG_SETTINGS = 'settings'
  ARG_SHAREDDRIVE = 'shareddrive'
  ARG_SHAREDDRIVES = 'shareddrives'
  ARG_SHAREDDRIVEACLS = 'shareddriveacls'
  ARG_SHAREDDRIVEINFO = 'shareddriveinfo'
  ARG_SHAREDDRIVETHEMES = 'shareddrivethemes'
  ARG_SHEET = 'sheet'
  ARG_SHEETS = 'sheets'
  ARG_SHEETRANGE = 'sheetrange'
  ARG_SHEETRANGES = 'sheetranges'
  ARG_SIG = 'sig'
  ARG_SIGNATURE = 'signature'
  ARG_SIGNJWTSERVICEACCOUNT = 'signjwtserviceaccount'
  ARG_SITE = 'site'
  ARG_SITES = 'sites'
  ARG_SITEACL = 'siteacl'
  ARG_SITEACLS = 'siteacls'
  ARG_SITEACTIVITY = 'siteactivity'
  ARG_SMIME = 'smime'
  ARG_SMIMES = 'smimes'
  ARG_STORAGEBUCKET = 'storagebucket'
  ARG_STORAGEBUCKETS = 'storagebuckets'
  ARG_STORAGEFILE = 'storagefile'
  ARG_STORAGEFILES = 'storagefiles'
  ARG_SVCACCT = 'svcacct'
  ARG_SVCACCTS = 'svcaccts'
  ARG_TASK = 'task'
  ARG_TASKS = 'tasks'
  ARG_TASKLIST = 'tasklist'
  ARG_TASKLISTS = 'tasklists'
  ARG_TEAMDRIVE = 'teamdrive'
  ARG_TEAMDRIVES = 'teamdrives'
  ARG_TEAMDRIVEACLS = 'teamdriveacls'
  ARG_TEAMDRIVEINFO = 'teamdriveinfo'
  ARG_TEAMDRIVETHEMES = 'teamdrivethemes'
  ARG_THREAD = 'thread'
  ARG_THREADS = 'threads'
  ARG_TOKEN = 'token'
  ARG_TOKENS = 'tokens'
  ARG_TRANSFER = 'transfer'
  ARG_TRANSFERS = 'transfers'
  ARG_TRANSFERAPPS = 'transferapps'
  ARG_TRUSTEDAPPS = 'trustedapps'
  ARG_USER = 'user'
  ARG_USERS = 'users'
  ARG_USERCOUNTSBYORGUNIT = 'usercountsbyorgunit'
  ARG_USERINVITATION = 'userinvitation'
  ARG_USERINVITATIONS = 'userinvitations'
  ARG_USERLIST = 'userlist'
  ARG_VACATION = 'vacation'
  ARG_VAULTCOUNT = 'vaultcount'
  ARG_VAULTCOUNTS = 'vaultcounts'
  ARG_VAULTEXPORT = 'vaultexport'
  ARG_VAULTEXPORTS = 'vaultexports'
  ARG_VAULTHOLD = 'vaulthold'
  ARG_VAULTHOLDS = 'vaultholds'
  ARG_VAULTMATTER = 'vaultmatter'
  ARG_VAULTMATTERS = 'vaultmatters'
  ARG_VAULTQUERY = 'vaultquery'
  ARG_VAULTQUERIES = 'vaultqueries'
  ARG_VERIFICATION = 'verification'
  ARG_VERIFICATIONCODES = 'verificationcodes'
  ARG_VERIFY = 'verify'
  ARG_WORKINGLOCATION = 'workinglocation'
  ARG_WORKINGLOCATIONS = 'workinglocations'
  ARG_YOUTUBECHANNEL = 'youtubechannel'
  ARG_YOUTUBECHANNELS = 'youtubechannels'
# Lists of arguments for use in checkArgumentPresent
  CLEAR_NONE_ARGUMENT = ['clear', 'none',]

# Object BNF names
  OB_ACCESS_LEVEL_NAME = 'AccessLevelName'
  OB_ACCESS_TOKEN = 'AccessToken'
  OB_ACL_SCOPE = 'ACLScope'
  OB_ACL_SCOPE_ENTITY = 'ACLScopeEntity'
  OB_ALERT_ID = 'AlertID'
  OB_ALIAS_ENTITY = 'AliasEntity'
  OB_API_SCOPE_URL_LIST = 'APIScopeURLList'
  OB_APP_ID = 'AppID'
  OB_ARGUMENT = 'argument'
  OB_ASP_ID_LIST = 'ASPIDList'
  OB_ASSET_ID = 'AssetID'
  OB_BROWSER_ENROLLEMNT_TOKEN_ID = 'BrowserEnrollmentTokenID'
  OB_BROWSER_ENTITY = 'BrowserEntity'
  OB_BUILDING_ID = 'BuildingID'
  OB_CALENDAR_ENTITY = 'CalendarEntity'
  OB_CALENDAR_ITEM = 'CalendarItem'
  OB_CHANNEL_CUSTOMER_ID = 'ChannelCustomerID'
  OB_CHARACTER = 'Character'
  OB_CHAR_SET = 'CharacterSet'
  OG_CHAT_ATTACHMENT = 'ChatAttachment'
  OB_CHAT_EVENT = 'ChatEvent'
  OB_CHAT_MEMBER = 'ChatMember'
  OB_CHAT_MESSAGE = 'ChatMessage'
  OB_CHAT_MESSAGE_ID = 'ChatMessageID'
  OB_CHAT_SPACE = 'ChatSpace'
  OB_CHAT_THREAD = 'ChatThread'
  OB_CHROMEPROFILE_ID = 'ChromeProfileId'
  OB_CHROME_VERSION = 'ChromeVersion'
  OB_CIDR_NETMASK = 'CIDRnetmask'
  OB_CIGROUP_ALIAS_LIST = "CIGroupAliasList"
  OB_CIPOLICY_NAME_ENTITY = 'CIPolicyNameEntity'
  OB_CLASSIFICATION_LABEL_ID = 'ClassificationLabelID'
  OB_CLASSIFICATION_LABEL_NAME = 'ClassificationLabelName'
  OB_CLASSIFICATION_LABEL_PERMISSION_NAME = 'ClassificationLabelPermissionName'
  OB_CLASSIFICATION_LABEL_FIELD_ID = 'ClassificationLabelFieldID'
  OB_CLASSIFICATION_LABEL_SELECTION_ID_LIST = 'ClassificationLabelSelectionIDList'
  OB_CLASSROOM_INVITATION_ID_ENTITY = 'ClassroomInvitationIDEntity'
  OB_CLIENT_ID = 'ClientID'
  OB_COLLABORATOR_ITEM = 'CollaboratorItem'
  OB_COLLABORATOR_ENTITY = 'CollaboratorEntity'
  OB_COMMAND_ID = 'CommandID'
  OB_CONTACT_EMAIL_TYPE = 'ContactEmailType'
  OB_CONTACT_ENTITY = 'ContactEntity'
  OB_CONTACT_GROUP_ENTITY = 'ContactGroupEntity'
  OB_CONTACT_GROUP_ITEM = 'ContactGroupItem'
  OB_COURSE_ALIAS = 'CourseAlias'
  OB_COURSE_ALIAS_ENTITY = 'CourseAliasEntity'
  OB_COURSE_ANNOUNCEMENT_ID_ENTITY = "CourseAnnouncementIDEntity"
  OB_COURSE_ANNOUNCEMENT_STATE_LIST = "CourseAnnouncementStateList"
  OB_COURSE_ENTITY = 'CourseEntity'
  OB_COURSE_ID = 'CourseID'
  OB_COURSE_MATERIAL_ID_ENTITY = 'CourseMaterialIDEntity'
  OB_COURSE_MATERIAL_STATE_LIST = "CourseMaterialStateList"
  OB_COURSE_STATE_LIST = "CourseStateList"
  OB_COURSE_SUBMISSION_ID_ENTITY = "CourseSubmissionIDEntity"
  OB_COURSE_SUBMISSION_STATE_LIST = "CourseSubmissionStateList"
  OB_COURSE_TOPIC = 'CourseTopic'
  OB_COURSE_TOPIC_ENTITY = "CourseTopicEntity"
  OB_COURSE_TOPIC_ID = 'CourseTopicID'
  OB_COURSE_TOPIC_ID_ENTITY = "CourseTopicIDEntity"
  OB_COURSE_WORK_ID_ENTITY = 'CourseWorkIDEntity'
  OB_COURSE_WORK_STATE_LIST = "CourseWorkStateList"
  OB_CROS_DEVICE_ENTITY = 'CrOSDeviceEntity'
  OB_CROS_ENTITY = 'CrOSEntity'
  OB_CSE_KEYPAIR_ID = 'CSEKeyPairID'
  OB_CUSTOMER_ID = 'CustomerID'
  OB_CUSTOMER_AUTH_TOKEN = 'CustomerAuthToken'
  OB_DEVICE_FILE_ENTITY = 'DeviceFileEntity'
  OB_DEVICE_ENTITY = 'DeviceEntity'
  OB_DEVICE_ID = 'DeviceID'
  OB_DEVICE_ID_LIST = 'DeviceIDList'
  OB_DEVICE_USER_ENTITY = 'DeviceUserEntity'
  OB_DEVICE_USER_ID = 'DeviceUserID'
  OB_DOMAIN_ALIAS = 'DomainAlias'
  OB_DOMAIN_NAME = 'DomainName'
  OB_DOMAIN_NAME_ENTITY = 'DomainNameEntity'
  OB_DOMAIN_NAME_LIST = 'DomainNameList'
  OB_DRIVE_FILE_ENTITY = 'DriveFileEntity'
  OB_DRIVE_FILE_ID = 'DriveFileID'
  OB_DRIVE_FILE_NAME = 'DriveFileName'
  OB_DRIVE_FILE_PERMISSION_ENTITY = 'DriveFilePermissionEntity'
  OB_DRIVE_FILE_PERMISSION_ID = 'DriveFilePermissionID'
  OB_DRIVE_FILE_PERMISSION_ID_ENTITY = 'DriveFilePermissionIDEntity'
  OB_DRIVE_FILE_REVISION_ID = 'DriveFileRevisionID'
  OB_DRIVE_FOLDER_ID = 'DriveFolderID'
  OB_DRIVE_FOLDER_ID_LIST = 'DriveFolderIDList'
  OB_DRIVE_FOLDER_NAME = 'DriveFolderName'
  OB_DRIVE_FOLDER_NAME_LIST = 'DriveFolderNameList'
  OB_DRIVE_FOLDER_PATH = 'DriveFolderPath'
  OB_EMAIL_ADDRESS = 'EmailAddress'
  OB_EMAIL_ADDRESS_ENTITY = 'EmailAddressEntity'
  OB_EMAIL_ADDRESS_LIST = 'EmailAddressList'
  OB_EMAIL_ADDRESS_OR_UID = 'EmailAaddress|UniqueID'
  OB_EMAIL_REPLACEMENT = 'EmailReplacement'
  OB_ENTITY = 'Entity'
  OB_ENTITY_TYPE = 'EntityType'
  OB_EVENT_ID = 'EventID'
  OB_EVENT_ID_ENTITY = 'EventIDEntity'
  OB_EVENT_NAME_LIST = "EventNameList"
  OB_EXPORT_ITEM = 'ExportItem'
  OB_FIELD_NAME = 'FieldName'
  OB_FIELD_NAME_LIST = "FieldNameList"
  OB_FIELDS = 'Fields'
  OB_FILE_NAME = 'FileName'
  OB_FILE_NAME_FIELD_NAME = OB_FILE_NAME+'(:'+OB_FIELD_NAME+')+'
  OB_FILE_NAME_OR_URL = 'FileName|URL'
  OB_FILE_PATH = 'FilePath'
  OB_FILTER_ID_ENTITY = 'FilterIDEntity'
  OB_FORMAT_LIST = 'FormatList'
  OB_GAM_ARGUMENT_LIST = 'GAM argument list'
  OB_GROUP_ENTITY = 'GroupEntity'
  OB_GROUP_ITEM = 'GroupItem'
  OB_GROUP_ROLE_LIST = 'GroupRoleList'
  OB_GROUP_TYPE_LIST = 'GroupTypeList'
  OB_GUARDIAN_INVITATION_ID = 'GuardianInvitationID'
  OB_GUARDIAN_INVITATION_ID_ENTITY = 'GuardianInvitationIDEntity'
  OB_GUARDIAN_ENTITY = 'GuardianEntity'
  OB_GUARDIAN_ITEM = 'GuardianItem'
  OB_GUARDIAN_STATE_LIST = 'GuardianStateList'
  OB_HOLD_ITEM = 'HoldItem'
  OB_HOST_NAME = 'HostName'
  OB_ICALUID = 'iCalUID'
  OB_ID_TOKEN = 'IDToken'
  OB_JOB_ID = 'JobID'
  OB_JSON_DATA = 'JSONData'
  OB_LABEL_COLOR_HEX = 'LabelColorHex'
  OB_LABEL_ID = 'LabelID'
  OB_LABEL_ID_LIST = 'LabelIDLIst'
  OB_LABEL_NAME = 'LabelName'
  OB_LABEL_NAME_LIST = 'LabelNameList'
  OB_LANGUAGE_LIST = 'LanguageList'
  OB_LOOKERSTUDIO_PERMISSION_ENTITY = 'LookerStudioPermissionEntity'
  OB_MATTER_ITEM = 'MatterItem'
  OB_MATTER_ITEM_LIST = 'MatterItemList'
  OB_MEET_CONFERENCE_NAME = 'MeetConferenceName'
  OB_MESSAGE_ID = 'MessageID'
  OB_MIMETYPE = 'MimeType'
  OB_MIMETYPE_LIST = 'MimeTypeList'
  OB_MOBILE_DEVICE_ENTITY = 'MobileDeviceEntity'
  OB_MOBILE_ENTITY = 'MobileEntity'
  OB_NETWORK_ID = 'networkID'
  OB_NAME = 'Name'
  OB_ORGUNIT_ENTITY = 'OrgUnitEntity'
  OB_ORGUNIT_ITEM = 'OrgUnitItem'
  OB_ORGUNIT_PATH = 'OrgUnitPath'
  OB_PARAMETER_VALUE = 'ParameterValue'
  OB_PASSWORD = 'Password'
  OB_PERMISSION_ID_LIST = 'PermissionIDList'
  OB_PERMISSION_ROLE_LIST = 'PermissionRoleList'
  OB_PERMISSION_TYPE_LIST = 'PermissionTypeList'
  OB_PHOTO_FILENAME_PATTERN = 'FilenameNamePattern'
  OB_PRINTER_ID = 'PrinterID'
  OB_PRIVILEGE_LIST = 'PrivilegeList'
  OB_PRODUCT_ID = 'ProductID'
  OB_PRODUCT_ID_LIST = 'ProductIDList'
  OB_PROJECT_ID = 'ProjectID'
  OB_PROJECT_ID_ENTITY = 'ProjectIDEntity'
  OB_PROPERTY_KEY = 'PropertyKey'
  OB_PROPERTY_VALUE = 'PropertyValue'
  OB_QUERY = 'Query'
  OB_QUERY_ITEM = 'QueryItem'
  OB_QUERY_LIST = 'QueryList'
  OB_RECURRENCE = 'RRULE EXRULE RDATE and EXDATE lines'
  OB_REQUEST_ID = 'RequestID'
  OB_RESELLER_ID = 'ResellerID'
  OB_RESOURCE_ENTITY = 'ResourceEntity'
  OB_RESOURCE_ID = 'ResourceID'
  OB_RE_PATTERN = 'REPattern'
  OB_RE_SUBSTITUTION = 'RESubstitution'
  OB_ROLE_ASSIGNMENT_ID = 'RoleAssignmentID'
  OB_ROLE_ITEM = 'RoleItem'
  OB_ROLE_LIST = 'RoleList'
  OB_ROOM_LIST = 'RoomList'
  OB_SCHEMA_ENTITY = 'SchemaEntity'
  OB_SCHEMA_NAME = 'SchemaName'
  OB_SCHEMA_NAME_FIELD_NAME = 'SchemaName.FieldName'
  OB_SCHEMA_NAME_LIST = 'SchemaNameList'
  OB_SECTION_NAME = 'SectionName'
  OB_SERIAL_NUMBER = 'SerialNumber'
  OB_SERIAL_NUMBER_LIST = 'SerialNumberList'
  OB_SERVICE_NAME_LIST = 'ServiceNameList'
  OB_SERVICE_ACCOUNT_KEY_LIST = 'ServiceAccountKeyList'
  OB_SHAREDDRIVE_ID = 'SharedDriveID'
  OB_SHAREDDRIVE_ID_LIST = 'SharedDriveIDList'
  OB_SHAREDDRIVE_NAME = 'SharedDriveName'
  OB_SHEET_ENTITY = 'SheetEntity'
  OB_SITE_ENTITY = 'SiteEntity'
  OB_SKU_ID = 'SKUID'
  OB_SKU_ID_LIST = 'SKUIDList'
  OB_SMIME_ID = 'S/MIMEID'
  OB_SMTP_HOST_NAME = 'SMTPHostName'
  OB_SPREADSHEET_JSON_CREATEREQUEST = 'SpreadsheetJSONCreateRequest'
  OB_SPREADSHEET_JSON_RANGEVALUESLIST = 'SpreadsheetJSONRangeValuesList'
  OB_SPREADSHEET_JSON_UPDATEREQUEST = 'SpreadsheetJSONUpdateRequest'
  OB_SPREADSHEET_JSON_VALUES = 'SpreadsheetJSONValues'
  OB_SPREADSHEET_RANGE = 'SpreadsheetRange'
  OB_SPREADSHEET_RANGE_LIST = 'SpreadsheetRangeList'
  OB_STATE_NAME_LIST = "StateNameList"
  OB_STRING = 'String'
  OB_STRING_LIST = 'StringList'
  OB_STUDENT_ITEM = 'StudentItem'
  OB_TAG = 'Tag'
  OB_TASK_ID = 'TaskID'
  OB_TASKLIST_ID = 'TaskListID'
  OB_TASKLIST_ID_ENTITY = 'TaskListIDEntity'
  OB_TASKLIST_ID_TASK_ID = 'TaskListIDTaskID'
  OB_TASKLIST_ID_TASK_ID_ENTITY = 'TaskListIDTaskIDEntity'
  OB_THREAD_ID = 'ThreadID'
  OB_TIME_LIST = 'TimeList'
  OB_TRANSFER_ID = 'TransferID'
  OB_URI = 'URI'
  OB_URL = 'URL'
  OB_URL_LIST = 'URLList'
  OB_USER_ENTITY = 'UserEntity'
  OB_USER_ITEM = 'UserItem'
  OB_USER_NAME = 'UserName'
  OB_YOUTUBE_CHANNEL_ID_LIST = 'YouTubeChannelIDlist'

#
# Error message types; keys into ARGUMENT_ERROR_NAMES; arbitrary values but must be unique
  ARGUMENT_BLANK = 'blnk'
  ARGUMENT_DEPRECATED = 'depr'
  ARGUMENT_EMPTY = 'empt'
  ARGUMENT_EXTRANEOUS = 'extr'
  ARGUMENT_INVALID = 'inva'
  ARGUMENT_INVALID_CHOICE = 'invc'
  ARGUMENT_MISSING = 'miss'
# ARGUMENT_ERROR_NAMES[0] is plural,ARGUMENT_ERROR_NAMES[1] is singular
# These values can be translated into other languages
  ARGUMENT_ERROR_NAMES = {
    ARGUMENT_BLANK: ['Blank arguments', 'Blank argument'],
    ARGUMENT_DEPRECATED: ['Deprecated arguments', 'Deprecated argument'],
    ARGUMENT_EMPTY: ['Empty arguments', 'Empty argument'],
    ARGUMENT_EXTRANEOUS: ['Extra arguments', 'Extra argument'],
    ARGUMENT_INVALID: ['Invalid arguments', 'Invalid argument'],
    ARGUMENT_INVALID_CHOICE: ['Invalid choices', 'Invalid choice ({0})'],
    ARGUMENT_MISSING: ['Missing arguments', 'Missing argument'],
    }

  def __init__(self):
    self.argv = []
    self.argvI = 0
    self.argvLen = 0
    self.argvIsave = 0
    self.origArgv = []
    self.origArgvI = 0
    self.origArgvLen = 0
    self.encoding = 'utf-8'

# Initialize arguments
  def InitializeArguments(self, args):
    self.argv = args[:]
    self.argvI = 1
    self.argvLen = len(self.argv)

# Number of arguments remaining
  def NumArgumentsRemaining(self):
    return self.argvLen - self.argvI

# Any arguments remaining
  def ArgumentsRemaining(self):
    return self.argvI < self.argvLen

# Multiple arguments remaining
  def MultipleArgumentsRemaining(self):
    return not self.argvI+1 == self.argvLen

# All arguments
  def AllArguments(self):
    return self.argv

# Specific argument
  def Argument(self, index):
    return self.argv[index]

# Current argument
  def Current(self):
    return self.argv[self.argvI]

# Previous argument
  def Previous(self):
    return self.argv[self.argvI-1]

# Remaining arguments
  def Remaining(self):
    return self.argv[self.argvI:]

# Argument location
  def Location(self):
    return self.argvI

# Advance to next argument
  def Advance(self):
    self.argvI += 1

# Backup to previous argument
  def Backup(self):
    self.argvI -= 1

# Save argument location
  def SaveLocation(self):
    self.argvIsave = self.argvI

# Reset argument location
  def ResetLocation(self, offset):
    self.argvI = self.argvIsave+offset

# Set argument location
  def SetLocation(self, location):
    self.argvI = location

# Set encoding
  def SetEncoding(self, encoding):
    self.encoding = encoding

# Concatenate list members, any item containing spaces, commas or single quotes is enclosed in ""
  @staticmethod
  def QuotedArgumentList(items):
    return ' '.join([item if item and (item.find(' ') == -1) and (item.find(',') == -1) and (item.find("'") == -1) else '"'+item+'"' for item in items])

# Mark bad argument in command line
  def CommandLineWithBadArgumentMarked(self, extraneous):
    if extraneous:
      return f'Command: {self.QuotedArgumentList(self.argv[:self.argvI])} >>>{self.QuotedArgumentList(self.argv[self.argvI:])}<<<\n'
    if self.ArgumentsRemaining():
      return f'Command: {self.QuotedArgumentList(self.argv[:self.argvI])} >>>{self.QuotedArgumentList([self.argv[self.argvI]])}<<< {self.QuotedArgumentList(self.argv[self.argvI+1:])}\n'
    return f'Command: {self.QuotedArgumentList(self.argv)} >>><<<\n'

# Deprecated command
  def CommandDeprecated(self):
    return f'{self.QuotedArgumentList(self.argv)}\n'

# Peek to see if next argument is in choices
  def PeekArgumentPresent(self, choices):
    if self.ArgumentsRemaining():
      choiceList = choices if isinstance(choices, (list, set)) else [choices]
      choice = self.Current().strip().lower().replace('_', '')
      if choice and choice in choiceList:
        return True
    return False

# Look ahead to see if argument is present
  def ArgumentIsAhead(self, argument):
    self.SaveLocation()
    while self.ArgumentsRemaining():
      if argument == self.Current().strip().lower().replace('_', ''):
        self.ResetLocation(0)
        return True
      self.Advance()
    self.ResetLocation(0)
    return False

# Merge new arguments into current argument list
  def MergeArguments(self, arguments):
    self.origArgv = self.argv[:]
    self.origArgvI = self.argvI
    self.origArgvLen = self.argvLen
    self.argv = self.argv[0:self.argvI]+arguments+self.argv[self.argvI:]
    self.argvLen += len(arguments)

# Restore
  def RestoreArguments(self):
    self.argv = self.origArgv[:]
    self.argvI = self.origArgvI
    self.argvLen = self.origArgvLen
