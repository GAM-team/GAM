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


"""Contains extensions to Atom objects used with Google Finance."""


__author__ = 'thesweeheng@gmail.com'


import atom
import gdata


GD_NAMESPACE = 'http://schemas.google.com/g/2005'
GF_NAMESPACE = 'http://schemas.google.com/finance/2007'


class Money(atom.AtomBase):
  """The <gd:money> element."""
  _tag = 'money'
  _namespace = GD_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['amount'] = 'amount'
  _attributes['currencyCode'] = 'currency_code'
  
  def __init__(self, amount=None, currency_code=None, **kwargs):
    self.amount = amount
    self.currency_code = currency_code
    atom.AtomBase.__init__(self, **kwargs)

  def __str__(self):
    return "%s %s" % (self.amount, self.currency_code)


def MoneyFromString(xml_string):
  return atom.CreateClassFromXMLString(Money, xml_string)


class _Monies(atom.AtomBase):
  """An element containing multiple <gd:money> in multiple currencies."""
  _namespace = GF_NAMESPACE
  _children = atom.AtomBase._children.copy()
  _children['{%s}money' % GD_NAMESPACE] = ('money', [Money])
  
  def __init__(self, money=None, **kwargs):
    self.money = money or []
    atom.AtomBase.__init__(self, **kwargs)

  def __str__(self):
    return " / ".join(["%s" % i for i in self.money])


class CostBasis(_Monies):
  """The <gf:costBasis> element."""
  _tag = 'costBasis'


def CostBasisFromString(xml_string):
  return atom.CreateClassFromXMLString(CostBasis, xml_string)


class DaysGain(_Monies):
  """The <gf:daysGain> element."""
  _tag = 'daysGain'


def DaysGainFromString(xml_string):
  return atom.CreateClassFromXMLString(DaysGain, xml_string)


class Gain(_Monies):
  """The <gf:gain> element."""
  _tag = 'gain'


def GainFromString(xml_string):
  return atom.CreateClassFromXMLString(Gain, xml_string)


class MarketValue(_Monies):
  """The <gf:marketValue> element."""
  _tag = 'gain'
  _tag = 'marketValue'


def MarketValueFromString(xml_string):
  return atom.CreateClassFromXMLString(MarketValue, xml_string)


class Commission(_Monies):
  """The <gf:commission> element."""
  _tag = 'commission'


def CommissionFromString(xml_string):
  return atom.CreateClassFromXMLString(Commission, xml_string)


class Price(_Monies):
  """The <gf:price> element."""
  _tag = 'price'


def PriceFromString(xml_string):
  return atom.CreateClassFromXMLString(Price, xml_string)


class Symbol(atom.AtomBase):
  """The <gf:symbol> element."""
  _tag = 'symbol'
  _namespace = GF_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['fullName'] = 'full_name'
  _attributes['exchange'] = 'exchange'
  _attributes['symbol'] = 'symbol'
  
  def __init__(self, full_name=None, exchange=None, symbol=None, **kwargs):
    self.full_name = full_name
    self.exchange = exchange
    self.symbol = symbol
    atom.AtomBase.__init__(self, **kwargs)

  def __str__(self):
    return "%s:%s (%s)" % (self.exchange, self.symbol, self.full_name)


def SymbolFromString(xml_string):
  return atom.CreateClassFromXMLString(Symbol, xml_string)


class TransactionData(atom.AtomBase):
  """The <gf:transactionData> element."""
  _tag = 'transactionData'
  _namespace = GF_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['type'] = 'type'
  _attributes['date'] = 'date'
  _attributes['shares'] = 'shares'
  _attributes['notes'] = 'notes'
  _children = atom.AtomBase._children.copy()
  _children['{%s}commission' % GF_NAMESPACE] = ('commission', Commission)
  _children['{%s}price' % GF_NAMESPACE] = ('price', Price)

  def __init__(self, type=None, date=None, shares=None,
      notes=None, commission=None, price=None, **kwargs):
    self.type = type 
    self.date = date
    self.shares = shares
    self.notes = notes
    self.commission = commission
    self.price = price
    atom.AtomBase.__init__(self, **kwargs)


def TransactionDataFromString(xml_string):
  return atom.CreateClassFromXMLString(TransactionData, xml_string)


class TransactionEntry(gdata.GDataEntry):
  """An entry of the transaction feed.

  A TransactionEntry contains TransactionData such as the transaction
  type (Buy,  Sell,  Sell Short, or  Buy to Cover), the number of units,
  the date, the price, any commission, and any notes.
  """
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy() 
  _children['{%s}transactionData' % GF_NAMESPACE] = (
      'transaction_data', TransactionData)

  def __init__(self, transaction_data=None, **kwargs):
    self.transaction_data = transaction_data
    gdata.GDataEntry.__init__(self, **kwargs)

  def transaction_id(self):
    return self.id.text.split("/")[-1]

  transaction_id = property(transaction_id, doc='The transaction ID.')


def TransactionEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(TransactionEntry, xml_string)


class TransactionFeed(gdata.GDataFeed):
  """A feed that lists all of the transactions that have been recorded for
  a particular position.
  
  A transaction is a collection of information about an instance of
  buying or selling a particular security. The TransactionFeed lists all
  of the transactions that have been recorded for a particular position
  as a list of TransactionEntries.
  """
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [TransactionEntry])


def TransactionFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(TransactionFeed, xml_string)


class TransactionFeedLink(atom.AtomBase):
  """Link to TransactionFeed embedded in PositionEntry.

  If a PositionFeed is queried with transactions='true', TransactionFeeds
  are inlined in the returned PositionEntries. These TransactionFeeds are
  accessible via TransactionFeedLink's feed attribute.
  """
  _tag = 'feedLink'
  _namespace = GD_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['href'] = 'href'
  _children = atom.AtomBase._children.copy() 
  _children['{%s}feed' % atom.ATOM_NAMESPACE] = (
      'feed', TransactionFeed)

  def __init__(self, href=None, feed=None, **kwargs):
    self.href = href
    self.feed = feed
    atom.AtomBase.__init__(self, **kwargs)


class PositionData(atom.AtomBase):
  """The <gf:positionData> element."""
  _tag = 'positionData'
  _namespace = GF_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['gainPercentage'] = 'gain_percentage'
  _attributes['return1w'] = 'return1w'
  _attributes['return4w'] = 'return4w'
  _attributes['return3m'] = 'return3m'
  _attributes['returnYTD'] = 'returnYTD'
  _attributes['return1y'] = 'return1y'
  _attributes['return3y'] = 'return3y'
  _attributes['return5y'] = 'return5y'
  _attributes['returnOverall'] = 'return_overall'
  _attributes['shares'] = 'shares'
  _children = atom.AtomBase._children.copy()
  _children['{%s}costBasis' % GF_NAMESPACE] = ('cost_basis', CostBasis)
  _children['{%s}daysGain' % GF_NAMESPACE] = ('days_gain', DaysGain)
  _children['{%s}gain' % GF_NAMESPACE] = ('gain', Gain)
  _children['{%s}marketValue' % GF_NAMESPACE] = ('market_value', MarketValue)

  def __init__(self, gain_percentage=None,
      return1w=None, return4w=None, return3m=None, returnYTD=None,
      return1y=None, return3y=None, return5y=None, return_overall=None,
      shares=None, cost_basis=None, days_gain=None,
      gain=None, market_value=None, **kwargs):
    self.gain_percentage = gain_percentage
    self.return1w = return1w
    self.return4w = return4w
    self.return3m = return3m
    self.returnYTD = returnYTD
    self.return1y = return1y
    self.return3y = return3y
    self.return5y = return5y
    self.return_overall = return_overall
    self.shares = shares
    self.cost_basis = cost_basis
    self.days_gain = days_gain
    self.gain = gain
    self.market_value = market_value
    atom.AtomBase.__init__(self, **kwargs)


def PositionDataFromString(xml_string):
  return atom.CreateClassFromXMLString(PositionData, xml_string)


class PositionEntry(gdata.GDataEntry):
  """An entry of the position feed.

  A PositionEntry contains the ticker exchange and Symbol for a stock,
  mutual fund, or other security, along with PositionData such as the
  number of units of that security that the user holds, and performance
  statistics.
  """
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy() 
  _children['{%s}positionData' % GF_NAMESPACE] = (
      'position_data', PositionData)
  _children['{%s}symbol' % GF_NAMESPACE] = ('symbol', Symbol)
  _children['{%s}feedLink' % GD_NAMESPACE] = (
    'feed_link', TransactionFeedLink)

  def __init__(self, position_data=None, symbol=None, feed_link=None,
      **kwargs):
    self.position_data = position_data
    self.symbol = symbol
    self.feed_link = feed_link
    gdata.GDataEntry.__init__(self, **kwargs)

  def position_title(self):
    return self.title.text

  position_title = property(position_title,
    doc='The position title as a string (i.e. position.title.text).')

  def ticker_id(self):
    return self.id.text.split("/")[-1]

  ticker_id = property(ticker_id, doc='The position TICKER ID.')

  def transactions(self):
    if self.feed_link.feed:
      return self.feed_link.feed.entry
    else:
      return None

  transactions = property(transactions, doc="""
      Inlined TransactionEntries are returned if PositionFeed is queried
      with transactions='true'.""")


def PositionEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(PositionEntry, xml_string)


class PositionFeed(gdata.GDataFeed):
  """A feed that lists all of the positions in a particular portfolio.

  A position is a collection of information about a security that the
  user holds. The PositionFeed lists all of the positions in a particular
  portfolio as a list of PositionEntries.
  """
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [PositionEntry])


def PositionFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(PositionFeed, xml_string)


class PositionFeedLink(atom.AtomBase):
  """Link to PositionFeed embedded in PortfolioEntry.

  If a PortfolioFeed is queried with positions='true', the PositionFeeds
  are inlined in the returned PortfolioEntries. These PositionFeeds are
  accessible via PositionFeedLink's feed attribute.
  """
  _tag = 'feedLink'
  _namespace = GD_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['href'] = 'href'
  _children = atom.AtomBase._children.copy() 
  _children['{%s}feed' % atom.ATOM_NAMESPACE] = (
      'feed', PositionFeed)

  def __init__(self, href=None, feed=None, **kwargs):
    self.href = href
    self.feed = feed
    atom.AtomBase.__init__(self, **kwargs)


class PortfolioData(atom.AtomBase):
  """The <gf:portfolioData> element."""
  _tag = 'portfolioData'
  _namespace = GF_NAMESPACE
  _attributes = atom.AtomBase._attributes.copy()
  _attributes['currencyCode'] = 'currency_code'
  _attributes['gainPercentage'] = 'gain_percentage'
  _attributes['return1w'] = 'return1w'
  _attributes['return4w'] = 'return4w'
  _attributes['return3m'] = 'return3m'
  _attributes['returnYTD'] = 'returnYTD'
  _attributes['return1y'] = 'return1y'
  _attributes['return3y'] = 'return3y'
  _attributes['return5y'] = 'return5y'
  _attributes['returnOverall'] = 'return_overall'
  _children = atom.AtomBase._children.copy()
  _children['{%s}costBasis' % GF_NAMESPACE] = ('cost_basis', CostBasis)
  _children['{%s}daysGain' % GF_NAMESPACE] = ('days_gain', DaysGain)
  _children['{%s}gain' % GF_NAMESPACE] = ('gain', Gain)
  _children['{%s}marketValue' % GF_NAMESPACE] = ('market_value', MarketValue)

  def __init__(self, currency_code=None, gain_percentage=None,
      return1w=None, return4w=None, return3m=None, returnYTD=None,
      return1y=None, return3y=None, return5y=None, return_overall=None,
      cost_basis=None, days_gain=None, gain=None, market_value=None, **kwargs):
    self.currency_code = currency_code
    self.gain_percentage = gain_percentage
    self.return1w = return1w
    self.return4w = return4w
    self.return3m = return3m
    self.returnYTD = returnYTD
    self.return1y = return1y
    self.return3y = return3y
    self.return5y = return5y
    self.return_overall = return_overall
    self.cost_basis = cost_basis
    self.days_gain = days_gain
    self.gain = gain
    self.market_value = market_value
    atom.AtomBase.__init__(self, **kwargs)


def PortfolioDataFromString(xml_string):
  return atom.CreateClassFromXMLString(PortfolioData, xml_string)


class PortfolioEntry(gdata.GDataEntry):
  """An entry of the PortfolioFeed.

  A PortfolioEntry contains the portfolio's title along with PortfolioData
  such as currency, total market value, and overall performance statistics.
  """
  _tag = 'entry'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataEntry._children.copy() 
  _children['{%s}portfolioData' % GF_NAMESPACE] = (
      'portfolio_data', PortfolioData)
  _children['{%s}feedLink' % GD_NAMESPACE] = (
    'feed_link', PositionFeedLink)

  def __init__(self, portfolio_data=None, feed_link=None, **kwargs):
    self.portfolio_data = portfolio_data
    self.feed_link = feed_link
    gdata.GDataEntry.__init__(self, **kwargs)

  def portfolio_title(self):
    return self.title.text

  def set_portfolio_title(self, portfolio_title):
    self.title = atom.Title(text=portfolio_title, title_type='text')

  portfolio_title = property(portfolio_title,  set_portfolio_title,
      doc='The portfolio title as a string (i.e. portfolio.title.text).')

  def portfolio_id(self):
    return self.id.text.split("/")[-1]

  portfolio_id = property(portfolio_id,
      doc='The portfolio ID. Do not confuse with portfolio.id.')

  def positions(self):
    if self.feed_link.feed:
      return self.feed_link.feed.entry
    else:
      return None

  positions = property(positions, doc="""
      Inlined PositionEntries are returned if PortfolioFeed was queried
      with positions='true'.""")


def PortfolioEntryFromString(xml_string):
  return atom.CreateClassFromXMLString(PortfolioEntry, xml_string)

    
class PortfolioFeed(gdata.GDataFeed):
  """A feed that lists all of the user's portfolios.

  A portfolio is a collection of positions that the user holds in various
  securities, plus metadata. The PortfolioFeed lists all of the user's
  portfolios as a list of PortfolioEntries.
  """
  _tag = 'feed'
  _namespace = atom.ATOM_NAMESPACE
  _children = gdata.GDataFeed._children.copy()
  _children['{%s}entry' % atom.ATOM_NAMESPACE] = ('entry', [PortfolioEntry])


def PortfolioFeedFromString(xml_string):
  return atom.CreateClassFromXMLString(PortfolioFeed, xml_string)


