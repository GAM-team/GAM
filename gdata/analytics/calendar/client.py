#!/usr/bin/python
#
# Copyright (C) 2011 Google Inc.
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

"""CalendarClient extends the GDataService to streamline Google Calendar operations.

  CalendarService: Provides methods to query feeds and manipulate items. Extends
                GDataService.

  DictionaryToParamList: Function which converts a dictionary into a list of
                         URL arguments (represented as strings). This is a
                         utility function used in CRUD operations.
"""


__author__ = 'alainv (Alain Vongsouvanh)'


import urllib
import gdata.client
import gdata.calendar.data
import atom.data
import atom.http_core
import gdata.gauth


DEFAULT_BATCH_URL = ('https://www.google.com/calendar/feeds/default/private'
                     '/full/batch')


class CalendarClient(gdata.client.GDClient):
  """Client for the Google Calendar service."""
  api_version = '2'
  auth_service = 'cl'
  server = "www.google.com"
  contact_list = "default"
  auth_scopes = gdata.gauth.AUTH_SCOPES['cl']

  def __init__(self, domain=None, auth_token=None, **kwargs):
    """Constructs a new client for the Calendar API.

    Args:
      domain: string The Google Apps domain (if any).
      kwargs: The other parameters to pass to the gdata.client.GDClient
          constructor.
    """
    gdata.client.GDClient.__init__(self, auth_token=auth_token, **kwargs)
    self.domain = domain

  def get_calendar_feed_uri(self, feed='', projection='full', scheme="https"):
    """Builds a feed URI.

    Args:
      projection: The projection to apply to the feed contents, for example
        'full', 'base', 'base/12345', 'full/batch'. Default value: 'full'.
      scheme: The URL scheme such as 'http' or 'https', None to return a
          relative URI without hostname.

    Returns:
      A feed URI using the given scheme and projection.
      Example: '/calendar/feeds/default/owncalendars/full'.
    """
    prefix = scheme and '%s://%s' % (scheme, self.server) or ''
    suffix = feed and '/%s/%s' % (feed, projection) or ''
    return '%s/calendar/feeds/default%s' % (prefix, suffix)

  GetCalendarFeedUri = get_calendar_feed_uri

  def get_calendar_event_feed_uri(self, calendar='default', visibility='private',
                                  projection='full', scheme="https"):
    """Builds a feed URI.

    Args:
      projection: The projection to apply to the feed contents, for example
        'full', 'base', 'base/12345', 'full/batch'. Default value: 'full'.
      scheme: The URL scheme such as 'http' or 'https', None to return a
          relative URI without hostname.

    Returns:
      A feed URI using the given scheme and projection.
      Example: '/calendar/feeds/default/private/full'.
    """
    prefix = scheme and '%s://%s' % (scheme, self.server) or ''
    return '%s/calendar/feeds/%s/%s/%s' % (prefix, calendar,
                                           visibility, projection)

  GetCalendarEventFeedUri = get_calendar_event_feed_uri

  def get_calendars_feed(self, uri,
                         desired_class=gdata.calendar.data.CalendarFeed,
                         auth_token=None, **kwargs):
    """Obtains a calendar feed.

    Args:
      uri: The uri of the calendar feed to request.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_feed(uri, auth_token=auth_token,
                         desired_class=desired_class, **kwargs)

  GetCalendarsFeed = get_calendars_feed

  def get_own_calendars_feed(self,
                             desired_class=gdata.calendar.data.CalendarFeed,
                             auth_token=None, **kwargs):
    """Obtains a feed containing the calendars owned by the current user.

    Args:
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.GetCalendarsFeed(uri=self.GetCalendarFeedUri(feed='owncalendars'),
                                 desired_class=desired_class, auth_token=auth_token,
                                 **kwargs)

  GetOwnCalendarsFeed = get_own_calendars_feed

  def get_all_calendars_feed(self, desired_class=gdata.calendar.data.CalendarFeed,
                             auth_token=None, **kwargs):
    """Obtains a feed containing all the ccalendars the current user has access to.

    Args:
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.GetCalendarsFeed(uri=self.GetCalendarFeedUri(feed='allcalendars'),
                                 desired_class=desired_class, auth_token=auth_token,
                                 **kwargs)

  GetAllCalendarsFeed = get_all_calendars_feed

  def get_calendar_entry(self, uri, desired_class=gdata.calendar.data.CalendarEntry,
                         auth_token=None, **kwargs):
    """Obtains a single calendar entry.

    Args:
      uri: The uri of the desired calendar entry.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarEntry.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_entry(uri, auth_token=auth_token, desired_class=desired_class,
                          **kwargs)

  GetCalendarEntry = get_calendar_entry

  def get_calendar_event_feed(self, uri=None,
                              desired_class=gdata.calendar.data.CalendarEventFeed,
               auth_token=None, **kwargs):
    """Obtains a feed of events for the desired calendar.

    Args:
      uri: The uri of the desired calendar entry.
           Defaults to https://www.google.com/calendar/feeds/default/private/full.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarEventFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    uri = uri or self.GetCalendarEventFeedUri()
    return self.get_feed(uri, auth_token=auth_token,
                         desired_class=desired_class, **kwargs)

  GetCalendarEventFeed = get_calendar_event_feed

  def get_event_entry(self, uri, desired_class=gdata.calendar.data.CalendarEventEntry,
              auth_token=None, **kwargs):
    """Obtains a single event entry.

    Args:
      uri: The uri of the desired calendar event entry.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarEventEntry.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_entry(uri, auth_token=auth_token, desired_class=desired_class,
                          **kwargs)

  GetEventEntry = get_event_entry

  def get_calendar_acl_feed(self, uri='https://www.google.com/calendar/feeds/default/acl/full',
                            desired_class=gdata.calendar.data.CalendarAclFeed,
                            auth_token=None, **kwargs):
    """Obtains an Access Control List feed.

    Args:
      uri: The uri of the desired Acl feed.
           Defaults to https://www.google.com/calendar/feeds/default/acl/full.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarAclFeed.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_feed(uri, auth_token=auth_token, desired_class=desired_class,
                         **kwargs)

  GetCalendarAclFeed = get_calendar_acl_feed

  def get_calendar_acl_entry(self, uri, desired_class=gdata.calendar.data.CalendarAclEntry,
                             auth_token=None, **kwargs):
    """Obtains a single Access Control List entry.

    Args:
      uri: The uri of the desired Acl feed.
      desired_class: class descended from atom.core.XmlElement to which a
                     successful response should be converted. If there is no
                     converter function specified (desired_class=None) then the
                     desired_class will be used in calling the
                     atom.core.parse function. If neither
                     the desired_class nor the converter is specified, an
                     HTTP reponse object will be returned. Defaults to
                     gdata.calendar.data.CalendarAclEntry.
      auth_token: An object which sets the Authorization HTTP header in its
                  modify_request method. Recommended classes include
                  gdata.gauth.ClientLoginToken and gdata.gauth.AuthSubToken
                  among others. Represents the current user. Defaults to None
                  and if None, this method will look for a value in the
                  auth_token member of SpreadsheetsClient.
    """
    return self.get_entry(uri, auth_token=auth_token, desired_class=desired_class,
                          **kwargs)

  GetCalendarAclEntry = get_calendar_acl_entry

  def insert_calendar(self, new_calendar, insert_uri=None, auth_token=None, **kwargs):
    """Adds an new calendar to Google Calendar.

    Args:
      new_calendar: atom.Entry or subclass A new calendar which is to be added to
                Google Calendar.
      insert_uri: the URL to post new contacts to the feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the contact created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server,
         'reason': HTTP reason from the server,
         'body': HTTP body of the server's response}
    """
    insert_uri = insert_uri or self.GetCalendarFeedUri(feed='owncalendars')
    return self.Post(new_calendar, insert_uri,
                     auth_token=auth_token, **kwargs)

  InsertCalendar = insert_calendar

  def insert_calendar_subscription(self, calendar, insert_uri=None,
                                   auth_token=None, **kwargs):
    """Subscribes the authenticated user to the provided calendar.

    Args:
      calendar: The calendar to which the user should be subscribed.
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
    insert_uri = insert_uri or self.GetCalendarFeedUri(feed='allcalendars')
    return self.Post(calendar, insert_uri, auth_token=auth_token, **kwargs)

  InsertCalendarSubscription = insert_calendar_subscription

  def insert_event(self, new_event, insert_uri=None, auth_token=None, **kwargs):
    """Adds an new event to Google Calendar.

    Args:
      new_event: atom.Entry or subclass A new event which is to be added to
                Google Calendar.
      insert_uri: the URL to post new contacts to the feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the contact created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server,
         'reason': HTTP reason from the server,
         'body': HTTP body of the server's response}
    """
    insert_uri = insert_uri or self.GetCalendarEventFeedUri()
    return self.Post(new_event, insert_uri,
                     auth_token=auth_token, **kwargs)


  InsertEvent = insert_event

  def insert_acl_entry(self, new_acl_entry,
                       insert_uri = 'https://www.google.com/calendar/feeds/default/acl/full',
                       auth_token=None, **kwargs):
    """Adds an new Acl entry to Google Calendar.

    Args:
      new_acl_event: atom.Entry or subclass A new acl which is to be added to
                Google Calendar.
      insert_uri: the URL to post new contacts to the feed
      url_params: dict (optional) Additional URL parameters to be included
                  in the insertion request.
      escape_params: boolean (optional) If true, the url_parameters will be
                     escaped before they are included in the request.

    Returns:
      On successful insert,  an entry containing the contact created
      On failure, a RequestError is raised of the form:
        {'status': HTTP status code from server,
         'reason': HTTP reason from the server,
         'body': HTTP body of the server's response}
    """
    return self.Post(new_acl_entry, insert_uri, auth_token=auth_token, **kwargs)

  InsertAclEntry = insert_acl_entry

  def execute_batch(self, batch_feed, url, desired_class=None):
    """Sends a batch request feed to the server.

    Args:
      batch_feed: gdata.contacts.CalendarEventFeed A feed containing batch
          request entries. Each entry contains the operation to be performed
          on the data contained in the entry. For example an entry with an
          operation type of insert will be used as if the individual entry
          had been inserted.
      url: str The batch URL to which these operations should be applied.
      converter: Function (optional) The function used to convert the server's
          response to an object.

    Returns:
      The results of the batch request's execution on the server. If the
      default converter is used, this is stored in a ContactsFeed.
    """
    return self.Post(batch_feed, url, desired_class=desired_class)

  ExecuteBatch = execute_batch

  def update(self, entry, auth_token=None, **kwargs):
    """Edits the entry on the server by sending the XML for this entry.

    Performs a PUT and converts the response to a new entry object with a
    matching class to the entry passed in.

    Args:
      entry:
      auth_token:

    Returns:
      A new Entry object of a matching type to the entry which was passed in.
    """
    return gdata.client.GDClient.Update(self, entry, auth_token=auth_token,
                                        force=True, **kwargs)

  Update = update


class CalendarEventQuery(gdata.client.Query):
  """
  Create a custom Calendar Query

  Full specs can be found at: U{Calendar query parameters reference
  <http://code.google.com/apis/calendar/data/2.0/reference.html#Parameters>}
  """

  def __init__(self, feed=None, ctz=None, fields=None, futureevents=None,
               max_attendees=None, orderby=None, recurrence_expansion_start=None,
               recurrence_expansion_end=None, singleevents=None, showdeleted=None,
               showhidden=None, sortorder=None, start_min=None, start_max=None,
               updated_min=None, **kwargs):
    """
    @param max_results: The maximum number of entries to return. If you want
        to receive all of the contacts, rather than only the default maximum, you
        can specify a very large number for max-results.
    @param start-index: The 1-based index of the first result to be retrieved.
    @param updated-min: The lower bound on entry update dates.
    @param group: Constrains the results to only the contacts belonging to the
        group specified. Value of this parameter specifies group ID
    @param orderby:  Sorting criterion. The only supported value is
        lastmodified.
    @param showdeleted: Include deleted contacts in the returned contacts feed
    @pram sortorder: Sorting order direction. Can be either ascending or
        descending.
    @param requirealldeleted: Only relevant if showdeleted and updated-min
        are also provided. It dictates the behavior of the server in case it
        detects that placeholders of some entries deleted since the point in
        time specified as updated-min may have been lost.
    """
    gdata.client.Query.__init__(self, **kwargs)
    self.ctz = ctz
    self.fields = fields
    self.futureevents = futureevents
    self.max_attendees = max_attendees
    self.orderby = orderby
    self.recurrence_expansion_start = recurrence_expansion_start
    self.recurrence_expansion_end = recurrence_expansion_end
    self.singleevents = singleevents
    self.showdeleted = showdeleted
    self.showhidden = showhidden
    self.sortorder = sortorder
    self.start_min = start_min
    self.start_max = start_max
    self.updated_min = updated_min

  def modify_request(self, http_request):
    if self.ctz:
      gdata.client._add_query_param('ctz', self.ctz, http_request)
    if self.fields:
      gdata.client._add_query_param('fields', self.fields, http_request)
    if self.futureevents:
      gdata.client._add_query_param('futureevents', self.futureevents, http_request)
    if self.max_attendees:
      gdata.client._add_query_param('max-attendees', self.max_attendees, http_request)
    if self.orderby:
      gdata.client._add_query_param('orderby', self.orderby, http_request)
    if self.recurrence_expansion_start:
      gdata.client._add_query_param('recurrence-expansion-start',
                                    self.recurrence_expansion_start, http_request)
    if self.recurrence_expansion_end:
      gdata.client._add_query_param('recurrence-expansion-end',
                                    self.recurrence_expansion_end, http_request)
    if self.singleevents:
      gdata.client._add_query_param('singleevents', self.singleevents, http_request)
    if self.showdeleted:
      gdata.client._add_query_param('showdeleted', self.showdeleted, http_request)
    if self.showhidden:
      gdata.client._add_query_param('showhidden', self.showhidden, http_request)
    if self.sortorder:
      gdata.client._add_query_param('sortorder', self.sortorder, http_request)
    if self.start_min:
      gdata.client._add_query_param('start-min', self.start_min, http_request)
    if self.start_max:
      gdata.client._add_query_param('start-max', self.start_max, http_request)
    if self.updated_min:
      gdata.client._add_query_param('updated-min', self.updated_min, http_request)
    gdata.client.Query.modify_request(self, http_request)

  ModifyRequest = modify_request



