#!/usr/bin/python
#
# Copyright (C) 2010-2011 Google Inc.
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


"""Extend the gdata client for the Content API for Shopping.

TODO:

1. Proper MCA Support.
2. Better datafeed Support.
"""


__author__ = 'afshar (Ali Afshar)'


import gdata.client
import atom.data

from gdata.contentforshopping.data import (ProductEntry, ProductFeed,
    DatafeedFeed, ClientAccountFeed, ClientAccount)


CFS_VERSION = 'v1'
CFS_HOST = 'content.googleapis.com'
CFS_URI = 'https://%s/content' % CFS_HOST
CFS_PROJECTION = 'generic'


class ContentForShoppingClient(gdata.client.GDClient):
  """Client for Content for Shopping API.

  :param account_id: Merchant account ID. This value will be used by default
                     for all requests, but may be overridden on a
                     request-by-request basis.
  :param api_version: The version of the API to target. Default value: 'v1'.
  :param **kwargs: Pass all addtional keywords to the GDClient constructor.
  """

  api_version = '1.0'

  def __init__(self, account_id=None, api_version=CFS_VERSION, **kwargs):
    self.cfs_account_id = account_id
    self.cfs_api_version = api_version
    gdata.client.GDClient.__init__(self, **kwargs)

  def _create_uri(self, account_id, resource, path=(), use_projection=True):
    """Create a request uri from the given arguments.

    If arguments are None, use the default client attributes.
    """
    account_id = account_id or self.cfs_account_id
    if account_id is None:
        raise ValueError('No Account ID set. '
                         'Either set for the client, or per request')
    segments = [CFS_URI, self.cfs_api_version, account_id, resource]
    if use_projection:
      segments.append(CFS_PROJECTION)
    segments.extend(path)
    return '/'.join(segments)

  def _create_product_id(self, id, country, language):
    return 'online:%s:%s:%s' % (language, country, id)

  def _create_batch_feed(self, entries, operation, feed=None):
    if feed is None:
      feed = ProductFeed()
    for entry in entries:
      entry.batch_operation = gdata.data.BatchOperation(type=operation)
      feed.entry.append(entry)
    return feed

  def get_products(self, start_index=None, max_results=None, account_id=None,
                   auth_token=None):
    """Get a feed of products for the account.

    :param max_results: The maximum number of results to return (default 25,
                        maximum 250).
    :param start_index: The starting index of the feed to return (default 1,
                        maximum 10000)
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    uri = self._create_uri(account_id, 'items/products')
    return self.get_feed(uri, auth_token=auth_token,
        desired_class=gdata.contentforshopping.data.ProductFeed)

  def get_product(self, id, country, language, account_id=None,
                  auth_token=None):
    """Get a product by id, country and language.

    :param id: The product ID
    :param country: The country (target_country)
    :param language: The language (content_language)
    """
    pid = self._create_product_id(id, country, language)
    uri = self._create_uri(account_id, 'items/products', [pid])
    return self.get_entry(uri, desired_class=ProductEntry,
                          auth_token=auth_token)

  def insert_product(self, product, account_id=None, auth_token=None):
    """Create a new product, by posting the product entry feed.

    :param product: A :class:`gdata.contentforshopping.data.ProductEntry` with
                    the required product data.
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    uri = self._create_uri(account_id, 'items/products')
    return self.post(product, uri=uri, auth_token=auth_token)

  def insert_products(self, products, account_id=None, auth_token=None):
    """Insert the products using a batch request

    :param products: A list of product entries
    """
    feed = self._create_batch_feed(products, 'insert')
    return self.batch(feed)

  def delete_products(self, products, account_id=None, auth_token=None):
    """Delete the products using a batch request.

    :param products: A list of product entries

    .. note:: Entries must have the atom:id element set.
    """
    feed = self._create_batch_feed(products, 'delete')
    return self.batch(feed)

  def update_products(self, products, account_id=None, auth_token=None):
    """Update the products using a batch request

    :param products: A list of product entries

    .. note:: Entries must have the atom:id element set.
    """
    feed = self._create_batch_feed(products, 'update')
    return self.batch(feed)

  def batch(self, feed, account_id=None, auth_token=None):
    """Send a batch request.

    :param feed: The feed of batch entries to send.
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    uri = self._create_uri(account_id, 'items/products', ['batch'])
    return self.post(feed, uri=uri, auth_token=auth_token,
                     desired_class=ProductFeed)

  def update_product(self, product, account_id=None,
                     auth_token=None):
    """Update a product, by putting the product entry feed.

    :param product: A :class:`gdata.contentforshopping.data.ProductEntry` with
                    the required product data.
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    pid = self._create_product_id(product.id.text, product.target_country.text,
                                  product.content_language.text)
    uri = self._create_uri(account_id, 'items/products', [pid])
    return self.update(product, uri=uri, auth_token=auth_token)

  def get_datafeeds(self, account_id=None):
    """Get the feed of datafeeds.
    """
    uri = self._create_uri(account_id, 'datafeeds/products',
                           use_projection=False)
    return self.get_feed(uri, desired_class=DatafeedFeed)

  def insert_datafeed(self, entry, account_id=None, auth_token=None):
    """Insert a datafeed.
    """
    uri = self._create_uri(account_id, 'datafeeds/products',
                           use_projection=False)
    return self.post(entry, uri=uri, auth_token=auth_token)

  def get_client_accounts(self, account_id=None, auth_token=None):
    """Get the feed of managed accounts

    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    uri = self._create_uri(account_id, 'managedaccounts/products',
                           use_projection=False)
    return self.get_feed(uri, desired_class=ClientAccountFeed,
                         auth_token=auth_token)

  def insert_client_account(self, entry, account_id=None, auth_token=None):
    """Insert a client account entry

    :param entry: An entry of type ClientAccount
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    uri = self._create_uri(account_id, 'managedaccounts/products',
                           use_projection=False)
    return self.post(entry, uri=uri, auth_token=auth_token)

  def update_client_account(self, entry, client_account_id, account_id=None, auth_token=None):
    """Update a client account

    :param entry: An entry of type ClientAccount to update to
    :param client_account_id: The client account ID
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """
    uri = self._create_uri(account_id, 'managedaccounts/products',
                           [client_account_id], use_projection=False)
    return self.update(entry, uri=uri, auth_token=auth_token)

  def delete_client_account(self, client_account_id, account_id=None,
                            auth_token=None):
    """Delete a client account

    :param client_account_id: The client account ID
    :param account_id: The Merchant Center Account ID. If ommitted the default
                       Account ID will be used for this client
    """

    uri = self._create_uri(account_id, 'managedaccounts/products',
                           [client_account_id], use_projection=False)
    return self.delete(uri, auth_token=auth_token)
