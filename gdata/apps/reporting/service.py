#!/usr/bin/python2.4
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""ReportService simplifies Reporting API calls.

ReportService extends gdata.apps.service.PropertyService to ease interaction with
the Google Apps Reporting API.
"""

__author__ = 'Jay Lee <jay0lee@gmail.com>'

import gdata.apps
import gdata.apps.service
import gdata.service
import time

class ReportService(gdata.apps.service.PropertyService):
  """Service extension for the Google Reporting API service."""

  def __init__(self, email=None, password=None, domain=None, source=None,
               server='www.google.com', additional_headers=None,
               **kwargs):
    """Creates a client for the Reporting service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      domain: string (optional) The Google Apps domain name.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'apps-apis.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(
        self, email=email, password=password, service='apps', source=source,
        server=server, additional_headers=additional_headers, **kwargs)
    self.ssl = True
    self.port = 443
    self.domain = domain

  def retrieve_report(self, report, date=None):
    """Retrieves a report

    Args:
      report: string, accounts, activity, disk_space, email_clients or summary
      date: string: YYYY-MM-DD. If not specified, most recent day that has past 12pm PST will be used (in other words, today if it's after 12pm PST or yesterday if not)
      
    Returns:
      String, the report data
    """
    uri = '/hosted/services/v1.0/reports/ReportingData'
    if date == None:
      now = time.time()
      report_time = time.gmtime(now)
      if report_time.tm_hour < 20:
        report_time = time.gmtime(now - 60*60*24)
      date = '%s-%s-0%s' % (report_time.tm_year, report_time.tm_mon, report_time.tm_mday)
    page = 1
    report_data = ''
    while True:
      xml = '''<?xml version="1.0" encoding="UTF-8"?>
<rest xmlns="google:accounts:rest:protocol"
    xmlns:xsi=" http://www.w3.org/2001/XMLSchema-instance ">
    <type>Report</type>
    <domain>%s</domain>
    <date>%s</date>
	  <page>%s</page>
    <reportType>daily</reportType>
    <reportName>%s</reportName>
</rest>''' % (self.domain, date, page, report)
      try:
        report_page = self.Post(xml, uri, converter=str)
      except gdata.service.RequestError, e:
        raise gdata.apps.service.AppsForYourDomainException(e.args[0])
      if report_page == 'End-Of-Report':
        return report_data
      else:
        if page == 1:
          report_data += report_page # 1st page has headers
        else:
          report_data += report_page[report_page.find('\n')+1:] # remove header on additional pages
        page = page + 1

  RetrieveReport = retrieve_report
