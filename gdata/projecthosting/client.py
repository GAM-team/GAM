#!/usr/bin/env python
#
# Copyright 2009 Google Inc.
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

import atom.data
import gdata.client
import gdata.gauth
import gdata.projecthosting.data


class ProjectHostingClient(gdata.client.GDClient):
  """Client to interact with the Project Hosting GData API."""
  api_version = '1.0'
  auth_service = 'code'
  auth_scopes = gdata.gauth.AUTH_SCOPES['code']
  host = 'code.google.com'

  def get_issues(self, project_name,
                 desired_class=gdata.projecthosting.data.IssuesFeed, **kwargs):
    """Get a feed of issues for a particular project.

    Args:
      project_name str The name of the project.
      query Query Set returned issues parameters.

    Returns:
      data.IssuesFeed
    """
    return self.get_feed(gdata.projecthosting.data.ISSUES_FULL_FEED %
                         project_name, desired_class=desired_class, **kwargs)

  def add_issue(self, project_name, title, content, author,
                status=None, owner=None, labels=None, ccs=None, **kwargs):
    """Create a new issue for the project.

    Args:
      project_name str The name of the project.
      title str The title of the new issue.
      content str The summary of the new issue.
      author str The authenticated user's username.
      status str The status of the new issue, Accepted, etc.
      owner str The username of new issue's owner.
      labels [str] Labels to associate with the new issue.
      ccs [str] usernames to Cc on the new issue.
    Returns:
      data.IssueEntry
    """
    new_entry = gdata.projecthosting.data.IssueEntry(
        title=atom.data.Title(text=title),
        content=atom.data.Content(text=content),
        author=[atom.data.Author(name=atom.data.Name(text=author))])

    if status:
      new_entry.status = gdata.projecthosting.data.Status(text=status)

    if owner:
      owner = [gdata.projecthosting.data.Owner(
          username=gdata.projecthosting.data.Username(text=owner))]

    if labels:
      new_entry.label = [gdata.projecthosting.data.Label(text=label)
                         for label in labels]
    if ccs:
      new_entry.cc = [
          gdata.projecthosting.data.Cc(
              username=gdata.projecthosting.data.Username(text=cc))
          for cc in ccs]

    return self.post(
        new_entry,
        gdata.projecthosting.data.ISSUES_FULL_FEED % project_name,
        **kwargs)

  def update_issue(self, project_name, issue_id, author, comment=None,
                   summary=None, status=None, owner=None, labels=None, ccs=None,
                   **kwargs):
    """Update or comment on one issue for the project.

    Args:
      project_name str The name of the issue's project.
      issue_id str The issue number needing updated.
      author str The authenticated user's username.
      comment str A comment to append to the issue
      summary str Rewrite the summary of the issue.
      status str A new status for the issue.
      owner str The username of the new owner.
      labels [str] Labels to set on the issue (prepend issue with - to remove a
          label).
      ccs [str] Ccs to set on th enew issue (prepend cc with - to remove a cc).

    Returns:
      data.CommentEntry
    """
    updates = gdata.projecthosting.data.Updates()

    if summary:
      updates.summary = gdata.projecthosting.data.Summary(text=summary)

    if status:
      updates.status = gdata.projecthosting.data.Status(text=status)

    if owner:
      updates.ownerUpdate = gdata.projecthosting.data.OwnerUpdate(text=owner)

    if labels:
      updates.label = [gdata.projecthosting.data.Label(text=label)
                       for label in labels]
    if ccs:
      updates.ccUpdate = [gdata.projecthosting.data.CcUpdate(text=cc)
                          for cc in ccs]

    update_entry = gdata.projecthosting.data.CommentEntry(
        content=atom.data.Content(text=comment),
        author=[atom.data.Author(name=atom.data.Name(text=author))],
        updates=updates)

    return self.post(
        update_entry,
        gdata.projecthosting.data.COMMENTS_FULL_FEED % (project_name, issue_id),
        **kwargs)

  def get_comments(self, project_name, issue_id,
                   desired_class=gdata.projecthosting.data.CommentsFeed,
                   **kwargs):
    """Get a feed of all updates to an issue.

    Args:
      project_name str The name of the issue's project.
      issue_id str The issue number needing updated.

    Returns:
      data.CommentsFeed
    """
    return self.get_feed(
        gdata.projecthosting.data.COMMENTS_FULL_FEED % (project_name, issue_id),
        desired_class=desired_class, **kwargs)

  def update(self, entry, auth_token=None, force=False, **kwargs):
    """Unsupported GData update method.

    Use update_*() instead.
    """
    raise NotImplementedError(
        'GData Update operation unsupported, try update_*')

  def delete(self, entry_or_uri, auth_token=None, force=False, **kwargs):
    """Unsupported GData delete method.

    Use update_issue(status='Closed') instead.
    """
    raise NotImplementedError(
        'GData Delete API unsupported, try closing the issue instead.')


class Query(gdata.client.Query):

  def __init__(self, issue_id=None, label=None, canned_query=None, owner=None,
               status=None, **kwargs):
    """Constructs a Google Data Query to filter feed contents serverside.
    Args:
      issue_id: int or str The issue to return based on the issue id.
      label: str A label returned issues must have.
      canned_query: str Return issues based on a canned query identifier
      owner: str Return issues based on the owner of the issue. For Gmail users,
          this will be the part of the email preceding the '@' sign.
      status: str Return issues based on the status of the issue.
    """
    super(Query, self).__init__(**kwargs)
    self.label = label
    self.issue_id = issue_id
    self.canned_query = canned_query
    self.owner = owner
    self.status = status

  def modify_request(self, http_request):
    if self.issue_id:
      gdata.client._add_query_param('id', self.issue_id, http_request)
    if self.label:
      gdata.client._add_query_param('label', self.label, http_request)
    if self.canned_query:
      gdata.client._add_query_param('can', self.canned_query, http_request)
    if self.owner:
      gdata.client._add_query_param('owner', self.owner, http_request)
    if self.status:
      gdata.client._add_query_param('status', self.status, http_request)
    super(Query, self).modify_request(http_request)

  ModifyRequest = modify_request
