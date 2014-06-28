#!/usr/bin/python
#
# Copyright (C) 2009 Google Inc.
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


"""Contains the data classes of the Google Calendar Data API"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import atom.data
import gdata.acl.data
import gdata.data
import gdata.geo.data
import gdata.opensearch.data


GCAL_NAMESPACE = 'http://schemas.google.com/gCal/2005'
GCAL_TEMPLATE = '{%s}%%s' % GCAL_NAMESPACE
WEB_CONTENT_LINK_REL = '%s/%s' % (GCAL_NAMESPACE, 'webContent')


class AccessLevelProperty(atom.core.XmlElement):
  """Describes how much a given user may do with an event or calendar"""
  _qname = GCAL_TEMPLATE % 'accesslevel'
  value = 'value'


class AllowGSync2Property(atom.core.XmlElement):
  """Whether the user is permitted to run Google Apps Sync"""
  _qname = GCAL_TEMPLATE % 'allowGSync2'
  value = 'value'


class AllowGSyncProperty(atom.core.XmlElement):
  """Whether the user is permitted to run Google Apps Sync"""
  _qname = GCAL_TEMPLATE % 'allowGSync'
  value = 'value'


class AnyoneCanAddSelfProperty(atom.core.XmlElement):
  """Whether anyone can add self as attendee"""
  _qname = GCAL_TEMPLATE % 'anyoneCanAddSelf'
  value = 'value'


class CalendarAclRole(gdata.acl.data.AclRole):
  """Describes the Calendar roles of an entry in the Calendar access control list"""
  _qname = gdata.acl.data.GACL_TEMPLATE % 'role'


class CalendarCommentEntry(gdata.data.GDEntry):
  """Describes an entry in a feed of a Calendar event's comments"""


class CalendarCommentFeed(gdata.data.GDFeed):
  """Describes feed of a Calendar event's comments"""
  entry = [CalendarCommentEntry]


class CalendarComments(gdata.data.Comments):
  """Describes a container of a feed link for Calendar comment entries"""
  _qname = gdata.data.GD_TEMPLATE % 'comments'


class CalendarExtendedProperty(gdata.data.ExtendedProperty):
  """Defines a value for the realm attribute that is used only in the calendar API"""
  _qname = gdata.data.GD_TEMPLATE % 'extendedProperty'


class CalendarWhere(gdata.data.Where):
  """Extends the base Where class with Calendar extensions"""
  _qname = gdata.data.GD_TEMPLATE % 'where'


class ColorProperty(atom.core.XmlElement):
  """Describes the color of a calendar"""
  _qname = GCAL_TEMPLATE % 'color'
  value = 'value'


class GuestsCanInviteOthersProperty(atom.core.XmlElement):
  """Whether guests can invite others to the event"""
  _qname = GCAL_TEMPLATE % 'guestsCanInviteOthers'
  value = 'value'


class GuestsCanModifyProperty(atom.core.XmlElement):
  """Whether guests can modify event"""
  _qname = GCAL_TEMPLATE % 'guestsCanModify'
  value = 'value'


class GuestsCanSeeGuestsProperty(atom.core.XmlElement):
  """Whether guests can see other attendees"""
  _qname = GCAL_TEMPLATE % 'guestsCanSeeGuests'
  value = 'value'


class HiddenProperty(atom.core.XmlElement):
  """Describes whether a calendar is hidden"""
  _qname = GCAL_TEMPLATE % 'hidden'
  value = 'value'


class IcalUIDProperty(atom.core.XmlElement):
  """Describes the UID in the ical export of the event"""
  _qname = GCAL_TEMPLATE % 'uid'
  value = 'value'


class OverrideNameProperty(atom.core.XmlElement):
  """Describes the override name property of a calendar"""
  _qname = GCAL_TEMPLATE % 'overridename'
  value = 'value'


class PrivateCopyProperty(atom.core.XmlElement):
  """Indicates whether this is a private copy of the event, changes to which should not be sent to other calendars"""
  _qname = GCAL_TEMPLATE % 'privateCopy'
  value = 'value'


class QuickAddProperty(atom.core.XmlElement):
  """Describes whether gd:content is for quick-add processing"""
  _qname = GCAL_TEMPLATE % 'quickadd'
  value = 'value'


class ResourceProperty(atom.core.XmlElement):
  """Describes whether gd:who is a resource such as a conference room"""
  _qname = GCAL_TEMPLATE % 'resource'
  value = 'value'
  id = 'id'


class EventWho(gdata.data.Who):
  """Extends the base Who class with Calendar extensions"""
  _qname = gdata.data.GD_TEMPLATE % 'who'
  resource = ResourceProperty


class SelectedProperty(atom.core.XmlElement):
  """Describes whether a calendar is selected"""
  _qname = GCAL_TEMPLATE % 'selected'
  value = 'value'


class SendAclNotificationsProperty(atom.core.XmlElement):
  """Describes whether to send ACL notifications to grantees"""
  _qname = GCAL_TEMPLATE % 'sendAclNotifications'
  value = 'value'


class CalendarAclEntry(gdata.acl.data.AclEntry):
  """Describes an entry in a feed of a Calendar access control list (ACL)"""
  send_acl_notifications = SendAclNotificationsProperty


class CalendarAclFeed(gdata.data.GDFeed):
  """Describes a Calendar access contorl list (ACL) feed"""
  entry = [CalendarAclEntry]


class SendEventNotificationsProperty(atom.core.XmlElement):
  """Describes whether to send event notifications to other participants of the event"""
  _qname = GCAL_TEMPLATE % 'sendEventNotifications'
  value = 'value'


class SequenceNumberProperty(atom.core.XmlElement):
  """Describes sequence number of an event"""
  _qname = GCAL_TEMPLATE % 'sequence'
  value = 'value'


class CalendarRecurrenceExceptionEntry(gdata.data.GDEntry):
  """Describes an entry used by a Calendar recurrence exception entry link"""
  uid = IcalUIDProperty
  sequence = SequenceNumberProperty


class CalendarRecurrenceException(gdata.data.RecurrenceException):
  """Describes an exception to a recurring Calendar event"""
  _qname = gdata.data.GD_TEMPLATE % 'recurrenceException'


class SettingsProperty(atom.core.XmlElement):
  """User preference name-value pair"""
  _qname = GCAL_TEMPLATE % 'settingsProperty'
  name = 'name'
  value = 'value'


class SettingsEntry(gdata.data.GDEntry):
  """Describes a Calendar Settings property entry"""
  settings_property = SettingsProperty


class CalendarSettingsFeed(gdata.data.GDFeed):
  """Personal settings for Calendar application"""
  entry = [SettingsEntry]


class SuppressReplyNotificationsProperty(atom.core.XmlElement):
  """Lists notification methods to be suppressed for this reply"""
  _qname = GCAL_TEMPLATE % 'suppressReplyNotifications'
  methods = 'methods'


class SyncEventProperty(atom.core.XmlElement):
  """Describes whether this is a sync scenario where the Ical UID and Sequence number are honored during inserts and updates"""
  _qname = GCAL_TEMPLATE % 'syncEvent'
  value = 'value'


class When(gdata.data.When):
  """Extends the gd:when element to add reminders"""
  reminder = [gdata.data.Reminder]


class CalendarEventEntry(gdata.data.BatchEntry):
  """Describes a Calendar event entry"""
  quick_add = QuickAddProperty
  send_event_notifications = SendEventNotificationsProperty
  sync_event = SyncEventProperty
  anyone_can_add_self = AnyoneCanAddSelfProperty
  extended_property = [CalendarExtendedProperty]
  sequence = SequenceNumberProperty
  guests_can_invite_others = GuestsCanInviteOthersProperty
  guests_can_modify = GuestsCanModifyProperty
  guests_can_see_guests = GuestsCanSeeGuestsProperty
  georss_where = gdata.geo.data.GeoRssWhere
  private_copy = PrivateCopyProperty
  suppress_reply_notifications = SuppressReplyNotificationsProperty
  uid = IcalUIDProperty
  where = [gdata.data.Where]
  when = [When]
  who = [gdata.data.Who]
  transparency = gdata.data.Transparency
  comments = gdata.data.Comments
  event_status = gdata.data.EventStatus
  visibility = gdata.data.Visibility
  recurrence = gdata.data.Recurrence
  recurrence_exception = [gdata.data.RecurrenceException]
  original_event = gdata.data.OriginalEvent
  reminder = [gdata.data.Reminder]


class TimeZoneProperty(atom.core.XmlElement):
  """Describes the time zone of a calendar"""
  _qname = GCAL_TEMPLATE % 'timezone'
  value = 'value'


class TimesCleanedProperty(atom.core.XmlElement):
  """Describes how many times calendar was cleaned via Manage Calendars"""
  _qname = GCAL_TEMPLATE % 'timesCleaned'
  value = 'value'


class CalendarEntry(gdata.data.GDEntry):
  """Describes a Calendar entry in the feed of a user's calendars"""
  timezone = TimeZoneProperty
  overridename = OverrideNameProperty
  hidden = HiddenProperty
  selected = SelectedProperty
  times_cleaned = TimesCleanedProperty
  color = ColorProperty
  where = [CalendarWhere]
  accesslevel = AccessLevelProperty


class CalendarEventFeed(gdata.data.BatchFeed):
  """Describes a Calendar event feed"""
  allow_g_sync2 = AllowGSync2Property
  timezone = TimeZoneProperty
  entry = [CalendarEventEntry]
  times_cleaned = TimesCleanedProperty
  allow_g_sync = AllowGSyncProperty


class CalendarFeed(gdata.data.GDFeed):
  """Describes a feed of Calendars"""
  entry = [CalendarEntry]


class WebContentGadgetPref(atom.core.XmlElement):
  """Describes a single web content gadget preference"""
  _qname = GCAL_TEMPLATE % 'webContentGadgetPref'
  name = 'name'
  value = 'value'


class WebContent(atom.core.XmlElement):
  """Describes a "web content" extension"""
  _qname = GCAL_TEMPLATE % 'webContent'
  height = 'height'
  width = 'width'
  web_content_gadget_pref = [WebContentGadgetPref]
  url = 'url'
  display = 'display'


class WebContentLink(atom.data.Link):
  """Describes a "web content" link"""
  def __init__(self, title=None, href=None, link_type=None,
               web_content=None):
    atom.data.Link.__init__(self, rel=WEB_CONTENT_LINK_REL, title=title, href=href,
        link_type=link_type)

  web_content = WebContent

