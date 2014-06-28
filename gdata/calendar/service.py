#!/usr/bin/python
#
# Copyright (C) 2006 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CalendarService extends the GDataService to streamline Google Calendar operations.

  CalendarService: Provides methods to query feeds and manipulate items. Extends 
                GDataService.

  DictionaryToParamList: Function which converts a dictionary into a list of 
                         URL arguments (represented as strings). This is a 
                         utility function used in CRUD operations.
"""


__author__ = 'api.vli (Vivian Li)'


import urllib
import gdata
import atom.service
import gdata.service
import gdata.calendar
import atom


DEFAULT_BATCH_URL = ('http://www.google.com/calendar/feeds/default/private'
                     '/full/batch')


class Error(Exception):
  pass


class RequestError(Error):
  pass


class CalendarService(gdata.service.GDataService):
  """Client for the Google Calendar service."""

  def __init__(self, email=None, password=None, source=None,
               server='www.google.com', additional_headers=None, **kwargs):
    """Creates a client for the Google Calendar service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'www.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='cl', source=source,
        server=server, additional_headers=additional_headers, **kwargs)

  def GetCalendarEventFeed(self, uri='/calendar/feeds/default/private/full'):
    return self.Get(uri, converter=gdata.calendar.CalendarEventFeedFromString)

  def GetCalendarEventEntry(self, uri):
    return self.Get(uri, converter=gdata.calendar.CalendarEventEntryFromString)

  def GetCalendarListFeed(self, uri='/calendar/feeds/default/allcalendars/full'):
    return self.Get(uri, converter=gdata.calendar.CalendarListFeedFromString)

  def GetCalendarSettingsFeed(self, uri='/calendar/feeds/default/settings'):
    return self.Get(uri)

  def GetAllCalendarsFeed(self, uri='/calendar/feeds/default/allcalendars/full'):
    return self.Get(uri, converter=gdata.calendar.CalendarListFeedFromString)

  def GetOwnCalendarsFeed(self, uri='/calendar/feeds/default/owncalendars/full'):
    return self.Get(uri, converter=gdata.calendar.CalendarListFeedFromString)

  def GetCalendarListEntry(self, uri):
    return self.Get(uri, converter=gdata.calendar.CalendarListEntryFromString)

  def GetCalendarAclFeed(self, uri='/calendar/feeds/default/acl/full'):
    return self.Get(uri, converter=gdata.calendar.CalendarAclFeedFromString)

  def GetCalendarAclEntry(self, uri):
    return self.Get(uri, converter=gdata.calendar.CalendarAclEntryFromString)

  def GetCalendarEventCommentFeed(self, uri):
    return self.Get(uri, converter=gdata.calendar.CalendarEventCommentFeedFromString)

  def GetCalendarEventCommentEntry(self, uri):
    return self.Get(uri, converter=gdata.calendar.CalendarEventCommentEntryFromString)
 
  def Query(self, uri, converter=None):
    """Performs a query and returns a resulting feed or entry.

    Args:
      feed: string The feed which is to be queried

    Returns:
      On success, a GDataFeed or Entry depending on which is sent from the 
        server.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    if converter:
      result = self.Get(uri, converter=converter)
    else:
      result = self.Get(uri)
    return result

  def CalendarQuery(self, query):
    if isinstance(query, CalendarEventQuery):
      return self.Query(query.ToUri(), 
          converter=gdata.calendar.CalendarEventFeedFromString)
    elif isinstance(query, CalendarListQuery):
      return self.Query(query.ToUri(), 
          converter=gdata.calendar.CalendarListFeedFromString)
    elif isinstance(query, CalendarEventCommentQuery):
      return self.Query(query.ToUri(), 
          converter=gdata.calendar.CalendarEventCommentFeedFromString)
    else:
      return self.Query(query.ToUri())
    
  def InsertEvent(self, new_event, insert_uri, url_params=None, 
                  escape_params=True):
    """Adds an event to Google Calendar.

    Args: 
      new_event: atom.Entry or subclass A new event which is to be added to 
                Google Calendar.
      insert_uri: the URL to post new events to the feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request. 
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the event created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    return self.Post(new_event, insert_uri, url_params=url_params,
                     escape_params=escape_params, 
                     converter=gdata.calendar.CalendarEventEntryFromString)

  def InsertCalendarSubscription(self, calendar, insert_uri='/calendar/feeds/default/allcalendars/full',
                                 url_params=None, escape_params=True):
    """Subscribes user to the provided calendar.
    
    Args: 
      calendar: The calendar to which the user should be subscribed.
      insert_uri: string The insert URL of the entry to be added.
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request. 
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the subscription created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    return self.Post(calendar, insert_uri, url_params=url_params,
                     escape_params=escape_params, 
                     converter=gdata.calendar.CalendarListEntryFromString)

  def InsertCalendar(self, new_calendar, url_params=None,
                                 escape_params=True):
    """Creates a new calendar.
    
    Args: 
      new_calendar: The calendar to be created
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request. 
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the calendar created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    insert_uri = '/calendar/feeds/default/owncalendars/full'
    response = self.Post(new_calendar, insert_uri, url_params=url_params,
                         escape_params=escape_params, 
                         converter=gdata.calendar.CalendarListEntryFromString)
    return response

  def UpdateCalendar(self, calendar, url_params=None,
                                 escape_params=True):
    """Updates a calendar.
    
    Args: 
      calendar: The calendar which should be updated
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request. 
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the calendar created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    update_uri = calendar.GetEditLink().href
    response = self.Put(data=calendar, uri=update_uri, url_params=url_params,
                         escape_params=escape_params,
                         converter=gdata.calendar.CalendarListEntryFromString)
    return response

  def InsertAclEntry(self, new_entry, insert_uri, url_params=None, 
                  escape_params=True):
    """Adds an ACL entry (rule) to Google Calendar.

    Args: 
      new_entry: atom.Entry or subclass A new ACL entry which is to be added to 
                Google Calendar.
      insert_uri: the URL to post new entries to the ACL feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request. 
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the ACL entry created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    return self.Post(new_entry, insert_uri, url_params=url_params,
                         escape_params=escape_params, 
                         converter=gdata.calendar.CalendarAclEntryFromString)

  def InsertEventComment(self, new_entry, insert_uri, url_params=None,
                  escape_params=True):
    """Adds an entry to Google Calendar.

    Args:
      new_entry: atom.Entry or subclass A new entry which is to be added to
                Google Calendar.
      insert_uri: the URL to post new entrys to the feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the comment created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    return self.Post(new_entry, insert_uri, url_params=url_params,
        escape_params=escape_params, 
        converter=gdata.calendar.CalendarEventCommentEntryFromString)

  def _RemoveStandardUrlPrefix(self, url):
    url_prefix = 'http://%s/' % self.server
    if url.startswith(url_prefix):
      return url[len(url_prefix) - 1:]
    return url

  def DeleteEvent(self, edit_uri, extra_headers=None, 
      url_params=None, escape_params=True):
    """Removes an event with the specified ID from Google Calendar.

    Args:
      edit_uri: string The edit URL of the entry to be deleted. Example:
               'http://www.google.com/calendar/feeds/default/private/full/abx'
      url_params: dict (optional) Additional URL parameters to be included
                  in the deletion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful delete,  a httplib.HTTPResponse containing the server's
        response to the DELETE request.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """
    
    edit_uri = self._RemoveStandardUrlPrefix(edit_uri)
    return self.Delete('%s' % edit_uri,
                       url_params=url_params, escape_params=escape_params)

  def DeleteAclEntry(self, edit_uri, extra_headers=None, 
      url_params=None, escape_params=True):
    """Removes an ACL entry at the given edit_uri from Google Calendar.

    Args:
      edit_uri: string The edit URL of the entry to be deleted. Example:
               'http://www.google.com/calendar/feeds/liz%40gmail.com/acl/full/default'
      url_params: dict (optional) Additional URL parameters to be included
                  in the deletion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful delete,  a httplib.HTTPResponse containing the server's
        response to the DELETE request.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """
   
    edit_uri = self._RemoveStandardUrlPrefix(edit_uri)
    return self.Delete('%s' % edit_uri,
                       url_params=url_params, escape_params=escape_params)

  def DeleteCalendarEntry(self, edit_uri, extra_headers=None,
      url_params=None, escape_params=True):
    """Removes a calendar entry at the given edit_uri from Google Calendar.

    Args:
      edit_uri: string The edit URL of the entry to be deleted. Example:
               'http://www.google.com/calendar/feeds/default/allcalendars/abcdef@group.calendar.google.com'
      url_params: dict (optional) Additional URL parameters to be included
                  in the deletion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful delete, True is returned
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    return self.Delete(edit_uri, url_params=url_params, 
                       escape_params=escape_params)

  def UpdateEvent(self, edit_uri, updated_event, url_params=None, 
                 escape_params=True):
    """Updates an existing event.

    Args:
      edit_uri: string The edit link URI for the element being updated
      updated_event: string, atom.Entry, or subclass containing
                    the Atom Entry which will replace the event which is 
                    stored at the edit_url 
      url_params: dict (optional) Additional URL parameters to be included
                  in the update request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful update,  a httplib.HTTPResponse containing the server's
        response to the PUT request.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    edit_uri = self._RemoveStandardUrlPrefix(edit_uri)
    return self.Put(updated_event, '%s' % edit_uri,
                    url_params=url_params, 
                    escape_params=escape_params, 
                    converter=gdata.calendar.CalendarEventEntryFromString)

  def UpdateAclEntry(self, edit_uri, updated_rule, url_params=None, 
                     escape_params=True):
    """Updates an existing ACL rule.

    Args:
      edit_uri: string The edit link URI for the element being updated
      updated_rule: string, atom.Entry, or subclass containing
                    the Atom Entry which will replace the event which is 
                    stored at the edit_url 
      url_params: dict (optional) Additional URL parameters to be included
                  in the update request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful update,  a httplib.HTTPResponse containing the server's
        response to the PUT request.
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server, 
         'reason': HTTP reason from the server, 
         'body': HTTP body of the server's response}
    """

    edit_uri = self._RemoveStandardUrlPrefix(edit_uri)
    return self.Put(updated_rule, '%s' % edit_uri,
                    url_params=url_params, 
                    escape_params=escape_params,
                    converter=gdata.calendar.CalendarAclEntryFromString)

  def ExecuteBatch(self, batch_feed, url, 
      converter=gdata.calendar.CalendarEventFeedFromString):
    """Sends a batch request feed to the server.

    The batch request needs to be sent to the batch URL for a particular 
    calendar. You can find the URL by calling GetBatchLink().href on the 
    CalendarEventFeed.

    Args:
      batch_feed: gdata.calendar.CalendarEventFeed A feed containing batch
          request entries. Each entry contains the operation to be performed 
          on the data contained in the entry. For example an entry with an 
          operation type of insert will be used as if the individual entry 
          had been inserted.
      url: str The batch URL for the Calendar to which these operations should
          be applied.
      converter: Function (optional) The function used to convert the server's
          response to an object. The default value is 
          CalendarEventFeedFromString.
     
    Returns:
      The results of the batch request's execution on the server. If the 
      default converter is used, this is stored in a CalendarEventFeed.
    """
    return self.Post(batch_feed, url, converter=converter)


class CalendarEventQuery(gdata.service.Query):

  def __init__(self, user='default', visibility='private', projection='full',
               text_query=None, params=None, categories=None):
    gdata.service.Query.__init__(self, 
        feed='http://www.google.com/calendar/feeds/%s/%s/%s' % (
            urllib.quote(user), 
            urllib.quote(visibility), 
            urllib.quote(projection)),
        text_query=text_query, params=params, categories=categories)
    
  def _GetStartMin(self):
    if 'start-min' in self.keys():
      return self['start-min']
    else:
      return None

  def _SetStartMin(self, val):
    self['start-min'] = val

  start_min = property(_GetStartMin, _SetStartMin, 
      doc="""The start-min query parameter""")

  def _GetStartMax(self):
    if 'start-max' in self.keys():
      return self['start-max']
    else:
      return None

  def _SetStartMax(self, val):
    self['start-max'] = val

  start_max = property(_GetStartMax, _SetStartMax, 
      doc="""The start-max query parameter""")

  def _GetOrderBy(self):
    if 'orderby' in self.keys():
      return self['orderby']
    else:
      return None

  def _SetOrderBy(self, val):
    if val is not 'lastmodified' and val is not 'starttime':
      raise Error, "Order By must be either 'lastmodified' or 'starttime'"
    self['orderby'] = val

  orderby = property(_GetOrderBy, _SetOrderBy, 
      doc="""The orderby query parameter""")

  def _GetSortOrder(self):
    if 'sortorder' in self.keys():
      return self['sortorder']
    else:
      return None

  def _SetSortOrder(self, val):
    if (val is not 'ascending' and val is not 'descending' 
        and val is not 'a' and val is not 'd' and val is not 'ascend'
        and val is not 'descend'):
      raise Error, "Sort order must be either ascending, ascend, " + (
          "a or descending, descend, or d")
    self['sortorder'] = val

  sortorder = property(_GetSortOrder, _SetSortOrder, 
      doc="""The sortorder query parameter""")

  def _GetSingleEvents(self):
    if 'singleevents' in self.keys():
      return self['singleevents']
    else:
      return None

  def _SetSingleEvents(self, val):
    self['singleevents'] = val

  singleevents = property(_GetSingleEvents, _SetSingleEvents, 
      doc="""The singleevents query parameter""")

  def _GetFutureEvents(self):
    if 'futureevents' in self.keys():
      return self['futureevents']
    else:
      return None

  def _SetFutureEvents(self, val):
    self['futureevents'] = val

  futureevents = property(_GetFutureEvents, _SetFutureEvents, 
      doc="""The futureevents query parameter""")

  def _GetRecurrenceExpansionStart(self):
    if 'recurrence-expansion-start' in self.keys():
      return self['recurrence-expansion-start']
    else:
      return None

  def _SetRecurrenceExpansionStart(self, val):
    self['recurrence-expansion-start'] = val

  recurrence_expansion_start = property(_GetRecurrenceExpansionStart, 
      _SetRecurrenceExpansionStart, 
      doc="""The recurrence-expansion-start query parameter""")

  def _GetRecurrenceExpansionEnd(self):
    if 'recurrence-expansion-end' in self.keys():
      return self['recurrence-expansion-end']
    else:
      return None

  def _SetRecurrenceExpansionEnd(self, val):
    self['recurrence-expansion-end'] = val

  recurrence_expansion_end = property(_GetRecurrenceExpansionEnd, 
      _SetRecurrenceExpansionEnd, 
      doc="""The recurrence-expansion-end query parameter""")

  def _SetTimezone(self, val):
    self['ctz'] = val

  def _GetTimezone(self):
    if 'ctz' in self.keys():
      return self['ctz']
    else:
      return None

  ctz = property(_GetTimezone, _SetTimezone, 
      doc="""The ctz query parameter which sets report time on the server.""")


class CalendarListQuery(gdata.service.Query): 
  """Queries the Google Calendar meta feed"""

  def __init__(self, userId=None, text_query=None,
               params=None, categories=None):
    if userId is None:
      userId = 'default'

    gdata.service.Query.__init__(self, feed='http://www.google.com/calendar/feeds/'
                           +userId,
                           text_query=text_query, params=params,
                           categories=categories)

class CalendarEventCommentQuery(gdata.service.Query): 
  """Queries the Google Calendar event comments feed"""

  def __init__(self, feed=None):
    gdata.service.Query.__init__(self, feed=feed)
