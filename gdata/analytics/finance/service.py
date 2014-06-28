#!/usr/bin/python
#
# Copyright (C) 2009 Tan Swee Heng
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


"""Classes to interact with the Google Finance server."""


__author__ = 'thesweeheng@gmail.com'


import gdata.service
import gdata.finance
import atom


class PortfolioQuery(gdata.service.Query):
  """A query object for the list of a user's portfolios."""

  def returns(self):
    return self.get('returns', False)

  def set_returns(self, value):
    if value is 'true' or value is True:
      self['returns'] = 'true'

  returns = property(returns, set_returns, doc="The returns query parameter")

  def positions(self):
    return self.get('positions', False)

  def set_positions(self, value):
    if value is 'true' or value is True:
      self['positions'] = 'true'

  positions = property(positions, set_positions,
      doc="The positions query parameter")


class PositionQuery(gdata.service.Query):
  """A query object for the list of a user's positions in a portfolio."""

  def returns(self):
    return self.get('returns', False)

  def set_returns(self, value):
    if value is 'true' or value is True:
      self['returns'] = 'true'

  returns = property(returns, set_returns,
      doc="The returns query parameter")

  def transactions(self):
    return self.get('transactions', False)

  def set_transactions(self, value):
    if value is 'true' or value is True:
      self['transactions'] = 'true'

  transactions = property(transactions, set_transactions,
      doc="The transactions query parameter")


class FinanceService(gdata.service.GDataService):

  def __init__(self, email=None, password=None, source=None,
               server='finance.google.com', **kwargs):
    """Creates a client for the Finance service.

    Args:
      email: string (optional) The user's email address, used for
          authentication.
      password: string (optional) The user's password.
      source: string (optional) The name of the user's application.
      server: string (optional) The name of the server to which a connection
          will be opened. Default value: 'finance.google.com'.
      **kwargs: The other parameters to pass to gdata.service.GDataService
          constructor.
    """
    gdata.service.GDataService.__init__(self,
        email=email, password=password, service='finance', server=server,
        **kwargs)

  def GetPortfolioFeed(self, query=None):
    uri = '/finance/feeds/default/portfolios'
    if query:
      uri = PortfolioQuery(feed=uri, params=query).ToUri()
    return self.Get(uri, converter=gdata.finance.PortfolioFeedFromString)

  def GetPositionFeed(self, portfolio_entry=None, portfolio_id=None,
      query=None):
    """
    Args:
      portfolio_entry: PortfolioEntry (optional; see Notes)
      portfolio_id: string (optional; see Notes) This may be obtained
          from a PortfolioEntry's portfolio_id attribute.
      query: PortfolioQuery (optional)

    Notes:
      Either a PortfolioEntry OR a portfolio ID must be provided.
    """
    if portfolio_entry:
      uri = portfolio_entry.GetSelfLink().href + '/positions'
    elif portfolio_id:
      uri = '/finance/feeds/default/portfolios/%s/positions' % portfolio_id
    if query:
      uri = PositionQuery(feed=uri, params=query).ToUri()
    return self.Get(uri, converter=gdata.finance.PositionFeedFromString)

  def GetTransactionFeed(self, position_entry=None,
      portfolio_id=None, ticker_id=None):
    """
    Args:
      position_entry: PositionEntry (optional; see Notes)
      portfolio_id: string (optional; see Notes) This may be obtained
          from a PortfolioEntry's portfolio_id attribute.
      ticker_id: string (optional; see Notes) This may be obtained from
          a PositionEntry's ticker_id attribute. Alternatively it can
          be constructed using the security's exchange and symbol,
          e.g. 'NASDAQ:GOOG'

    Notes:
      Either a PositionEntry OR (a portfolio ID AND ticker ID) must
      be provided.
    """
    if position_entry:
      uri = position_entry.GetSelfLink().href + '/transactions'
    elif portfolio_id and ticker_id:
      uri = '/finance/feeds/default/portfolios/%s/positions/%s/transactions' \
          % (portfolio_id, ticker_id)
    return self.Get(uri, converter=gdata.finance.TransactionFeedFromString)

  def GetPortfolio(self, portfolio_id=None, query=None):
    uri = '/finance/feeds/default/portfolios/%s' % portfolio_id
    if query:
      uri = PortfolioQuery(feed=uri, params=query).ToUri()
    return self.Get(uri, converter=gdata.finance.PortfolioEntryFromString)

  def AddPortfolio(self, portfolio_entry=None):
    uri = '/finance/feeds/default/portfolios'
    return self.Post(portfolio_entry, uri,
        converter=gdata.finance.PortfolioEntryFromString)

  def UpdatePortfolio(self, portfolio_entry=None):
    uri = portfolio_entry.GetEditLink().href
    return self.Put(portfolio_entry, uri,
        converter=gdata.finance.PortfolioEntryFromString)

  def DeletePortfolio(self, portfolio_entry=None):
    uri = portfolio_entry.GetEditLink().href
    return self.Delete(uri)

  def GetPosition(self, portfolio_id=None, ticker_id=None, query=None):
    uri = '/finance/feeds/default/portfolios/%s/positions/%s' \
        % (portfolio_id, ticker_id)
    if query:
      uri = PositionQuery(feed=uri, params=query).ToUri()
    return self.Get(uri, converter=gdata.finance.PositionEntryFromString)

  def DeletePosition(self, position_entry=None,
      portfolio_id=None, ticker_id=None, transaction_feed=None):
    """A position is deleted by deleting all its transactions.

    Args:
      position_entry: PositionEntry (optional; see Notes)
      portfolio_id: string (optional; see Notes) This may be obtained
          from a PortfolioEntry's portfolio_id attribute.
      ticker_id: string (optional; see Notes) This may be obtained from
          a PositionEntry's ticker_id attribute. Alternatively it can
          be constructed using the security's exchange and symbol,
          e.g. 'NASDAQ:GOOG'
      transaction_feed: TransactionFeed (optional; see Notes)

    Notes:
      Either a PositionEntry OR (a portfolio ID AND ticker ID) OR
      a TransactionFeed must be provided.
    """
    if transaction_feed:
      feed = transaction_feed
    else:
      if position_entry:
        feed = self.GetTransactionFeed(position_entry=position_entry)
      elif portfolio_id and ticker_id:
        feed = self.GetTransactionFeed(
            portfolio_id=portfolio_id, ticker_id=ticker_id)
    for txn in feed.entry:
      self.DeleteTransaction(txn)
    return True

  def GetTransaction(self, portfolio_id=None, ticker_id=None,
      transaction_id=None):
    uri = '/finance/feeds/default/portfolios/%s/positions/%s/transactions/%s' \
        % (portfolio_id, ticker_id, transaction_id)
    return self.Get(uri, converter=gdata.finance.TransactionEntryFromString)

  def AddTransaction(self, transaction_entry=None, transaction_feed = None,
      position_entry=None, portfolio_id=None, ticker_id=None):
    """
    Args:
      transaction_entry: TransactionEntry (required)
      transaction_feed: TransactionFeed (optional; see Notes)
      position_entry: PositionEntry (optional; see Notes)
      portfolio_id: string (optional; see Notes) This may be obtained
          from a PortfolioEntry's portfolio_id attribute.
      ticker_id: string (optional; see Notes) This may be obtained from
          a PositionEntry's ticker_id attribute. Alternatively it can
          be constructed using the security's exchange and symbol,
          e.g. 'NASDAQ:GOOG'

    Notes:
      Either a TransactionFeed OR a PositionEntry OR (a portfolio ID AND
      ticker ID) must be provided.
    """
    if transaction_feed:
      uri = transaction_feed.GetPostLink().href
    elif position_entry:
      uri = position_entry.GetSelfLink().href + '/transactions'
    elif portfolio_id and ticker_id:
      uri = '/finance/feeds/default/portfolios/%s/positions/%s/transactions' \
          % (portfolio_id, ticker_id)
    return self.Post(transaction_entry, uri,
        converter=gdata.finance.TransactionEntryFromString)

  def UpdateTransaction(self, transaction_entry=None):
    uri = transaction_entry.GetEditLink().href
    return self.Put(transaction_entry, uri,
        converter=gdata.finance.TransactionEntryFromString)

  def DeleteTransaction(self, transaction_entry=None):
    uri = transaction_entry.GetEditLink().href
    return self.Delete(uri)
