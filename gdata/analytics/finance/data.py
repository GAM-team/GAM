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


"""Contains the data classes of the Google Finance Portfolio Data API"""


__author__ = 'j.s@google.com (Jeff Scudder)'


import atom.core
import atom.data
import gdata.data
import gdata.opensearch.data


GF_TEMPLATE = '{http://schemas.google.com/finance/2007/}%s'


class Commission(atom.core.XmlElement):
  """Commission for the transaction"""
  _qname = GF_TEMPLATE % 'commission'
  money = [gdata.data.Money]


class CostBasis(atom.core.XmlElement):
  """Cost basis for the portfolio or position"""
  _qname = GF_TEMPLATE % 'costBasis'
  money = [gdata.data.Money]


class DaysGain(atom.core.XmlElement):
  """Today's gain for the portfolio or position"""
  _qname = GF_TEMPLATE % 'daysGain'
  money = [gdata.data.Money]


class Gain(atom.core.XmlElement):
  """Total gain for the portfolio or position"""
  _qname = GF_TEMPLATE % 'gain'
  money = [gdata.data.Money]


class MarketValue(atom.core.XmlElement):
  """Market value for the portfolio or position"""
  _qname = GF_TEMPLATE % 'marketValue'
  money = [gdata.data.Money]


class PortfolioData(atom.core.XmlElement):
  """Data for the portfolio"""
  _qname = GF_TEMPLATE % 'portfolioData'
  return_overall = 'returnOverall'
  currency_code = 'currencyCode'
  return3y = 'return3y'
  return4w = 'return4w'
  market_value = MarketValue
  return_y_t_d = 'returnYTD'
  cost_basis = CostBasis
  gain_percentage = 'gainPercentage'
  days_gain = DaysGain
  return3m = 'return3m'
  return5y = 'return5y'
  return1w = 'return1w'
  gain = Gain
  return1y = 'return1y'


class PortfolioEntry(gdata.data.GDEntry):
  """Describes an entry in a feed of Finance portfolios"""
  portfolio_data = PortfolioData


class PortfolioFeed(gdata.data.GDFeed):
  """Describes a Finance portfolio feed"""
  entry = [PortfolioEntry]


class PositionData(atom.core.XmlElement):
  """Data for the position"""
  _qname = GF_TEMPLATE % 'positionData'
  return_y_t_d = 'returnYTD'
  return5y = 'return5y'
  return_overall = 'returnOverall'
  cost_basis = CostBasis
  return3y = 'return3y'
  return1y = 'return1y'
  return4w = 'return4w'
  shares = 'shares'
  days_gain = DaysGain
  gain_percentage = 'gainPercentage'
  market_value = MarketValue
  gain = Gain
  return3m = 'return3m'
  return1w = 'return1w'


class Price(atom.core.XmlElement):
  """Price of the transaction"""
  _qname = GF_TEMPLATE % 'price'
  money = [gdata.data.Money]


class Symbol(atom.core.XmlElement):
  """Stock symbol for the company"""
  _qname = GF_TEMPLATE % 'symbol'
  symbol = 'symbol'
  exchange = 'exchange'
  full_name = 'fullName'


class PositionEntry(gdata.data.GDEntry):
  """Describes an entry in a feed of Finance positions"""
  symbol = Symbol
  position_data = PositionData


class PositionFeed(gdata.data.GDFeed):
  """Describes a Finance position feed"""
  entry = [PositionEntry]


class TransactionData(atom.core.XmlElement):
  """Data for the transction"""
  _qname = GF_TEMPLATE % 'transactionData'
  shares = 'shares'
  notes = 'notes'
  date = 'date'
  type = 'type'
  commission = Commission
  price = Price


class TransactionEntry(gdata.data.GDEntry):
  """Describes an entry in a feed of Finance transactions"""
  transaction_data = TransactionData


class TransactionFeed(gdata.data.GDFeed):
  """Describes a Finance transaction feed"""
  entry = [TransactionEntry]


