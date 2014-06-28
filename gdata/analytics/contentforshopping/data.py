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


"""GData definitions for Content API for Shopping"""


__author__ = 'afshar (Ali Afshar)'


import atom.core
import atom.data
import gdata.data


SC_NAMESPACE_TEMPLATE = ('{http://schemas.google.com/'
                        'structuredcontent/2009}%s')
SCP_NAMESPACE_TEMPLATE = ('{http://schemas.google.com/'
                         'structuredcontent/2009/products}%s')


class ProductId(atom.core.XmlElement):
  """sc:id element

  It is required that all inserted products are provided with a unique
  alphanumeric ID, in this element.
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'id'


class RequiredDestination(atom.core.XmlElement):
  """sc:required_destination element

  This element defines the required destination for a product, namely
  "ProductSearch", "ProductAds" or "CommerceSearch". It should be added to the
  app:control element (ProductEntry's "control" attribute) to specify where the
  product should appear in search APIs.

  By default, when omitted, the api attempts to upload to as many destinations
  as possible.
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'required_destination'
  dest = 'dest'


class ExcludedDestination(atom.core.XmlElement):
  """sc:excluded_destination element

  This element defines the required destination for a product, namely
  "ProductSearch", "ProductAds" or "CommerceSearch". It should be added to the
  app:control element (ProductEntry's "control" attribute) to specify where the
  product should not appear in search APIs.

  By default, when omitted, the api attempts to upload to as many destinations
  as possible.
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'excluded_destination'
  dest = 'dest'


class ProductControl(atom.data.Control):
  """
  app:control element

  overridden to provide additional elements in the sc namespace.
  """
  required_destination = RequiredDestination
  excluded_destination = ExcludedDestination


class ContentLanguage(atom.core.XmlElement):
  """
  sc:content_language element

  Language used in the item content for the product
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'content_language'


class TargetCountry(atom.core.XmlElement):
  """
  sc:target_country element

  The target country of the product
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'target_country'


class ImageLink(atom.core.XmlElement):
  """sc:image_link element

  This is the URL of an associated image for a product. Please use full size
  images (400x400 pixels or larger), not thumbnails.
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'image_link'


class ExpirationDate(atom.core.XmlElement):
  """sc:expiration_date

  This is the date when the product listing will expire. If omitted, this will
  default to 30 days after the product was created.
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'expiration_date'


class Adult(atom.core.XmlElement):
  """sc:adult element

  Indicates whether the content is targeted towards adults, with possible
  values of "true" or "false". Defaults to "false".
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'adult'


class Author(atom.core.XmlElement):
  """
  scp:author element

  Defines the author of the information, recommended for books.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'author'


class Availability(atom.core.XmlElement):
  """
  scp:availability element

  The retailer's suggested label for product availability. Supported values
  include: 'in stock', 'out of stock', 'limited availability'.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'availability'


class Brand(atom.core.XmlElement):
  """
  scp:brand element

  The brand of the product
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'brand'


class Color(atom.core.XmlElement):
  """scp:color element

  The color of the product.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'color'


class Condition(atom.core.XmlElement):
  """scp:condition element

  The condition of the product, one of "new", "used", "refurbished"
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'condition'


class Edition(atom.core.XmlElement):
  """scp:edition element

  The edition of the product. Recommended for products with multiple editions
  such as collectors' editions etc, such as books.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'edition'


class Feature(atom.core.XmlElement):
  """scp:feature element

  A product feature. A product may have multiple features, each being text, for
  example a smartphone may have features: "wifi", "gps" etc.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'feature'


class FeaturedProduct(atom.core.XmlElement):
  """scp:featured_product element

  Used to indicate that this item is a special, featured product; Supported
  values are: "true", "false".
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'featured_product'


class Genre(atom.core.XmlElement):
  """scp:genre element

  Describes the genre of a product, eg "comedy". Strongly recommended for media.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'genre'


class Gtin(atom.core.XmlElement):
  """scp:gtin element

  GTIN of the product (isbn/upc/ean)
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'gtin'


class Manufacturer(atom.core.XmlElement):
  """scp:manufacturer element

  Manufacturer of the product.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'manufacturer'


class Mpn(atom.core.XmlElement):
  """scp:mpn element

  Manufacturer's Part Number. A unique code determined by the manufacturer for
  the product.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'mpn'


class Price(atom.core.XmlElement):
  """scp:price element

  The price of the product. The unit attribute must be set, and should represent
  the currency.

  Note: Required Element
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'price'
  unit = 'unit'


class ProductType(atom.core.XmlElement):
  """scp:product_type element

  Describes the type of product. A taxonomy of available product types is
  listed at http://www.google.com/basepages/producttype/taxonomy.txt and the
  entire line in the taxonomy should be included, for example "Electronics >
  Video > Projectors".
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'product_type'


class Quantity(atom.core.XmlElement):
  """scp:quantity element

  The number of items available. A value of 0 indicates items that are
  currently out of stock.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'quantity'


class ShippingCountry(atom.core.XmlElement):
  """scp:shipping_country element

  The two-letter ISO 3166 country code for the country to which an item will
  ship.

  This element should be placed inside the scp:shipping element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'shipping_country'


class ShippingPrice(atom.core.XmlElement):
  """scp:shipping_price element

  Fixed shipping price, represented as a number. Specify the currency as the
  "unit" attribute".

  This element should be placed inside the scp:shipping element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'shipping_price'
  unit = 'unit'


class ShippingRegion(atom.core.XmlElement):
  """scp:shipping_region element

  The geographic region to which a shipping rate applies, e.g., in the US, the
  two-letter state abbreviation, ZIP code, or ZIP code range using * wildcard.

  This element should be placed inside the scp:shipping element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'shipping_region'


class ShippingService(atom.core.XmlElement):
  """scp:shipping_service element

  A free-form description of the service class or delivery speed.

  This element should be placed inside the scp:shipping element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'shipping_service'


class Shipping(atom.core.XmlElement):
  """scp:shipping element

  Container for the shipping rules as provided by the shipping_country,
  shipping_price, shipping_region and shipping_service tags.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'shipping'
  shipping_price = ShippingPrice
  shipping_country = ShippingCountry
  shipping_service = ShippingService
  shipping_region = ShippingRegion


class ShippingWeight(atom.core.XmlElement):
  """scp:shipping_weight element

  The shipping weight of a product. Requires a value and a unit using the unit
  attribute. Valid units include lb, pound, oz, ounce, g, gram, kg, kilogram.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'shipping_weight'
  unit = 'unit'


class Size(atom.core.XmlElement):
  """scp:size element

  Available sizes of an item.  Appropriate values include: "small", "medium",
  "large", etc. The product enttry may contain multiple sizes, to indicate the
  available sizes.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'size'


class TaxRate(atom.core.XmlElement):
  """scp:tax_rate element

  The tax rate as a percent of the item price, i.e., number, as a percentage.

  This element should be placed inside the scp:tax (Tax class) element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'tax_rate'


class TaxCountry(atom.core.XmlElement):
  """scp:tax_country element

  The country an item is taxed in (as a two-letter ISO 3166 country code).

  This element should be placed inside the scp:tax (Tax class) element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'tax_country'


class TaxRegion(atom.core.XmlElement):
  """scp:tax_region element

  The geographic region that a tax rate applies to, e.g., in the US, the
  two-letter state abbreviation, ZIP code, or ZIP code range using * wildcard.

  This element should be placed inside the scp:tax (Tax class) element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'tax_region'


class TaxShip(atom.core.XmlElement):
  """scp:tax_ship element

  Whether tax is charged on shipping for this product. The default value is
  "false".

  This element should be placed inside the scp:tax (Tax class) element.
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'tax_ship'


class Tax(atom.core.XmlElement):
  """scp:tax element

  Container for the tax rules for this product. Containing the tax_rate,
  tax_country, tax_region, and tax_ship elements
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'tax'
  tax_rate = TaxRate
  tax_country = TaxCountry
  tax_region = TaxRegion
  tax_ship = TaxShip


class Year(atom.core.XmlElement):
  """scp:year element

  The year the product was produced. Expects four digits
  """
  _qname = SCP_NAMESPACE_TEMPLATE % 'year'


class ProductEntry(gdata.data.BatchEntry):
  """Product entry containing product information

  The elements of this entry that are used are made up of five different
  namespaces. They are:

  atom: - Atom
  app: - Atom Publishing Protocol
  gd: - Google Data API
  sc: - Content API for Shopping, general attributes
  scp: - Content API for Shopping, product attributes

  Only the sc and scp namespace elements are defined here, but additional useful
  elements are defined in superclasses, and are documented here because they are
  part of the required Content for Shopping API.

  .. attribute:: title

    The title of the product.

    This should be a :class:`atom.data.Title` element, for example::

      entry = ProductEntry()
      entry.title = atom.data.Title(u'32GB MP3 Player')

  .. attribute:: author

    The author of the product.

    This should be a :class:`Author` element, for example::

      entry = ProductEntry()
      entry.author = atom.data.Author(u'Isaac Asimov')

  .. attribute:: availability

    The avilability of a product.

    This should be an :class:`Availability` instance, for example::

      entry = ProductEntry()
      entry.availability = Availability('in stock')

  .. attribute:: brand

    The brand of a product.

    This should be a :class:`Brand` element, for example::

      entry = ProductEntry()
      entry.brand = Brand(u'Sony')

  .. attribute:: color

    The color of a product.

    This should be a :class:`Color` element, for example::

      entry = ProductEntry()
      entry.color = Color(u'purple')

  .. attribute:: condition

    The condition of a product.

    This should be a :class:`Condition` element, for example::

      entry = ProductEntry()
      entry.condition = Condition(u'new')

  .. attribute:: content_language

    The language for the product.

    This should be a :class:`ContentLanguage` element, for example::

      entry = ProductEntry()
      entry.content_language = ContentLanguage('EN')

  .. attribute:: edition

    The edition of the product.

    This should be a :class:`Edition` element, for example::

      entry = ProductEntry()
      entry.edition = Edition('1')

  .. attribute:: expiration

    The expiration date of this product listing.

    This should be a :class:`ExpirationDate` element, for example::

      entry = ProductEntry()
      entry.expiration_date = ExpirationDate('2011-22-03')

  .. attribute:: feature

    A list of features for this product.

    Each feature should be a :class:`Feature` element, for example::

      entry = ProductEntry()
      entry.feature.append(Feature(u'wifi'))
      entry.feature.append(Feature(u'gps'))

  .. attribute:: featured_product

    Whether the product is featured.

    This should be a :class:`FeaturedProduct` element, for example::

      entry = ProductEntry()
      entry.featured_product = FeaturedProduct('true')

  .. attribute:: genre

    The genre of the product.

    This should be a :class:`Genre` element, for example::

      entry = ProductEntry()
      entry.genre = Genre(u'comedy')

  .. attribute:: image_link

    A list of links to images of the product. Each link should be an
    :class:`ImageLink` element, for example::

      entry = ProductEntry()
      entry.image_link.append(ImageLink('http://myshop/cdplayer.jpg'))

  .. attribute:: manufacturer

    The manufacturer of the product.

    This should be a :class:`Manufacturer` element, for example::

      entry = ProductEntry()
      entry.manufacturer = Manufacturer('Sony')

  .. attribute:: mpn

    The manufacturer's part number for this product.

    This should be a :class:`Mpn` element, for example::

      entry = ProductEntry()
      entry.mpn = Mpn('cd700199US')

  .. attribute:: price

    The price for this product.

    This should be a :class:`Price` element, including a unit argument to
    indicate the currency, for example::

      entry = ProductEntry()
      entry.price = Price('20.00', unit='USD')

  .. attribute:: gtin

    The gtin for this product.

    This should be a :class:`Gtin` element, for example::

      entry = ProductEntry()
      entry.gtin = Gtin('A888998877997')

  .. attribute:: product_type

    The type of product.

    This should be a :class:`ProductType` element, for example::

      entry = ProductEntry()
      entry.product_type = ProductType("Electronics > Video > Projectors")

  .. attribute:: publisher

    The publisher of this product.

    This should be a :class:`Publisher` element, for example::

      entry = ProductEntry()
      entry.publisher = Publisher(u'Oxford University Press')

  .. attribute:: quantity

    The quantity of product available in stock.

    This should be a :class:`Quantity` element, for example::

      entry = ProductEntry()
      entry.quantity = Quantity('100')

  .. attribute:: shipping

    The shipping rules for the product.

    This should be a :class:`Shipping` with the necessary rules embedded as
    elements, for example::

      entry = ProductEntry()
      entry.shipping = Shipping()
      entry.shipping.shipping_price = ShippingPrice('10.00', unit='USD')

  .. attribute:: shipping_weight

    The shipping weight for this product.

    This should be a :class:`ShippingWeight` element, including a unit parameter
    for the unit of weight, for example::

      entry = ProductEntry()
      entry.shipping_weight = ShippingWeight('10.45', unit='kg')

  .. attribute:: size

    A list of the available sizes for this product.

    Each item in this list should be a :class:`Size` element, for example::

      entry = ProductEntry()
      entry.size.append(Size('Small'))
      entry.size.append(Size('Medium'))
      entry.size.append(Size('Large'))

  .. attribute:: target_country

    The target country for the product.

    This should be a :class:`TargetCountry` element, for example::

      entry = ProductEntry()
      entry.target_country = TargetCountry('US')

  .. attribute:: tax

    The tax rules for this product.

    This should be a :class:`Tax` element, with the tax rule elements embedded
    within, for example::

      entry = ProductEntry()
      entry.tax = Tax()
      entry.tax.tax_rate = TaxRate('17.5')

  .. attribute:: year

    The year the product was created.

    This should be a :class:`Year` element, for example::

      entry = ProductEntry()
      entry.year = Year('2001')


    #TODO Document these atom elements which are part of the required API
    <title>
    <link>
    <entry>
    <id>
    <category>
    <content>
    <author>
    <created>
    <updated>
"""

  author = Author
  product_id = ProductId
  availability = Availability
  brand = Brand
  color = Color
  condition = Condition
  content_language = ContentLanguage
  edition = Edition
  expiration_date = ExpirationDate
  feature = [Feature]
  featured_product = FeaturedProduct
  genre = Genre
  image_link = [ImageLink]
  manufacturer = Manufacturer
  mpn = Mpn
  price = Price
  gtin = Gtin
  product_type = ProductType
  quantity = Quantity
  shipping = Shipping
  shipping_weight = ShippingWeight
  size = [Size]
  target_country = TargetCountry
  tax = Tax
  year = Year
  control = ProductControl


# opensearch needs overriding for wrong version
# see http://code.google.com/p/gdata-python-client/issues/detail?id=483
class TotalResults(gdata.data.TotalResults):

    _qname = gdata.data.TotalResults._qname[1]


class ItemsPerPage(gdata.data.ItemsPerPage):

    _qname = gdata.data.ItemsPerPage._qname[1]


class StartIndex(gdata.data.StartIndex):

    _qname = gdata.data.StartIndex._qname[1]


class ProductFeed(gdata.data.BatchFeed):
  """Represents a feed of a merchant's products."""
  entry = [ProductEntry]
  total_results = TotalResults
  items_per_page = ItemsPerPage
  start_index = StartIndex


def build_entry(product_id=None, title=None, content=None, link=None, condition=None,
                target_country=None, content_language=None, price=None,
                price_unit=None, tax_rate=None, shipping_price=None,
                shipping_price_unit=None, image_links=(), expiration_date=None,
                adult=None, author=None, brand=None, color=None, edition=None,
                features=(), featured_product=None, genre=None,
                manufacturer=None, mpn=None, gtin=None, product_type=None,
                quantity=None, shipping_country=None, shipping_region=None,
                shipping_service=None, shipping_weight=None,
                shipping_weight_unit=None, sizes=(), tax_country=None,
                tax_region=None, tax_ship=None, year=None, product=None):
  """Create a new product with the required attributes.

  This function exists as an alternative constructor to help alleviate the
  boilerplate involved in creating product definitions. You may well want to
  fine-tune your products after creating them.

  Documentation of each attribute attempts to explain the "long-hand" way of
  achieving the same goal.

  :param product_id: The unique ID for this product.

    This is equivalent to creating and setting an product_id element::

      entry = ProductEntry()
      entry.product_id = ProductId(product_id)

  :param title: The title of this product.

    This is equivalent to creating and setting a title element::

      entry = ProductEntry
      entry.title = atom.data.Title(title)

  :param content: The description of this product.

    This is equivalent to creating and setting the content element::

      entry.content = atom.data.Content(content)

  :param link: The uri of the link to a page describing the product.

    This is equivalent to creating and setting the link element::

      entry.link = atom.data.Link(href=link, rel='alternate',
                                  type='text/html')

  :param condition: The condition of the product.

    This is equivalent to creating and setting the condition element::

      entry.condition = Condition(condition)

  :param target_country: The target country of the product

    This is equivalent to creating and setting the target_country element::

      entry.target_country = TargetCountry(target_country)

  :param content_language: The language of the content

    This is equivalent to creating and setting the content_language element::

      entry.content_language = ContentLanguage(content_language)

  :param price: The price of the product

    This is equivalent to creating and setting the price element, using the
    price_unit parameter as the unit::

      entry.price = Price(price, unit=price_unit)

  :param price_unit: The price unit of the product

    See price parameter.

  :param tax_rate: The tax rate for this product

    This is equivalent to creating and setting the tax element and its required
    children::

      entry.tax = Tax()
      entry.tax.tax_rate = TaxRate(tax_rate)

  :param shipping_price: Thie price of shipping for this product

    This is equivalent to creating and setting the shipping element and its
    required children. The unit for the price is taken from the
    shipping_price_unit parameter::

      entry.shipping = Shipping()
      entry.shipping.shipping_price = ShippingPrice(shipping_price,
                                                    unit=shipping_price_unit)

  :param shipping_price_unit: The unit of the shipping price

    See shipping_price

  :param image_links: A sequence of links for images for this product.

    This is equivalent to creating a single image_link element for each image::

      for image_link in image_links:
        entry.image_link.append(ImageLink(image_link))

  :param expiration_date: The date that this product listing expires

    This is equivalent to creating and setting an expiration_date element::

      entry.expiration_date = ExpirationDate(expiration_date)

  :param adult: Whether this product listing contains adult content

    This is equivalent to creating and setting the adult element::

      entry.adult = Adult(adult)

  :param author: The author of the product

    This is equivalent to creating and setting the author element::

      entry.author = Author(author)

  :param brand: The brand of the product

    This is equivalent to creating and setting the brand element::

      entry.brand = Brand(brand)

  :param color: The color of the product

    This is equivalent to creating and setting the color element::

      entry.color = Color(color)

  :param edition: The edition of the product

    This is equivalent to creating and setting the edition element::

      entry.edition = Edition('1')

  :param features=(): Features for this product

    Each feature in the provided sequence will create a Feature element in the
    entry, equivalent to::

      for feature in features:
        entry.feature.append(Feature(feature)))

  :param featured_product: Whether this product is featured

    This is equivalent to creating and setting the featured_product element::

      entry.featured_product = FeaturedProduct(featured_product)

  :param genre: The genre of the product

    This is equivalent to creating and setting the genre element::

      entry.genre = Genre(genre)

  :param manufacturer: The manufacturer of the product

    This is equivalent to creating and setting the manufacturer element::

      entry.manufacturer = Manufacturer(manufacturer)

  :param mpn: The manufacturer's part number for a product

    This is equivalent to creating and setting the mpn element::

      entry.mpn = Mpn(mpn)

  :param gtin: The gtin for a product

    This is equivalent to creating and setting the gtin element::

      entry.gtin = Gtin(gtin)

  :param product_type: The type of a product

    This is equivalent to creating and setting the product_type element::

      entry.product_type = ProductType(product_type)

  :param quantity: The quantity of the product in stock

    This is equivalent to creating and setting the quantity element::

      entry.quantity = Quantity(quantity)

  :param shipping_country: The country that this product can be shipped to

    This is equivalent to creating a Shipping element, and creating and setting
    the required element within::

      entry.shipping = Shipping()
      entry.shipping.shipping_country = ShippingCountry(shipping_country)

  :param shipping_region: The region that this product can be shipped to

    This is equivalent to creating a Shipping element, and creating and setting
    the required element within::

      entry.shipping = Shipping()
      entry.shipping.shipping_region = ShippingRegion(shipping_region)

  :param shipping_service: The service for shipping.

    This is equivalent to creating a Shipping element, and creating and setting
    the required element within::

      entry.shipping = Shipping()
      entry.shipping.shipping_service = ShippingRegion(shipping_service)

  :param shipping_weight: The shipping weight of a product

    Along with the shipping_weight_unit, this is equivalent to creating and
    setting the shipping_weight element::

      entry.shipping_weight = ShippingWeight(shipping_weight,
                                             unit=shipping_weight_unit)

  :param shipping_weight_unit: The unit of shipping weight

    See shipping_weight.

  :param: The sizes that are available for this product.

    Each size of a list will add a size element to the entry, like so::

      for size in sizes:
        product.size.append(Size(size))

  :param tax_country: The country that tax rules will apply

    This is equivalent to creating a Tax element, and creating and setting the
    required sub-element::

      entry.tax = Tax()
      entry.tax.tax_country = TaxCountry(tax_country)

  :param tax_region: The region that the tax rule applies in

    This is equivalent to creating a Tax element, and creating and setting the
    required sub-element::

      entry.tax = Tax()
      entry.tax.tax_region = TaxRegion(tax_region)

  :param tax_ship: Whether shipping cost is taxable

    This is equivalent to creating a Tax element, and creating and setting the
    required sub-element::

      entry.tax = Tax()
      entry.tax.tax_ship = TaxShip(tax_ship)

  :param year: The year the product was created

    This is equivalent to creating and setting a year element::

      entry.year = Year('2001')
  """

  product = product or ProductEntry()
  if product_id is not None:
    product.product_id = ProductId(product_id)
  if content is not None:
    product.content = atom.data.Content(content)
  if title is not None:
    product.title = atom.data.Title(title)
  if condition is not None:
    product.condition = Condition(condition)
  if price is not None:
    product.price = Price(price, unit=price_unit)
  if content_language is not None:
    product.content_language = ContentLanguage(content_language)
  if target_country is not None:
    product.target_country = TargetCountry(target_country)
  if tax_rate is not None:
    product.tax = Tax()
    product.tax.tax_rate = TaxRate(tax_rate)
  if shipping_price is not None:
    if shipping_price_unit is None:
        raise ValueError('Must provide shipping_price_unit if '
                         'shipping_price is provided')
    product.shipping = Shipping()
    product.shipping.shipping_price = ShippingPrice(shipping_price,
                                                    unit=shipping_price_unit)
  if link is not None:
    product.link.append(atom.data.Link(href=link, type='text/html',
                                       rel='alternate'))
  for image_link in image_links:
    product.image_link.append(ImageLink(image_link))
  if expiration_date is not None:
    product.expiration_date = ExpirationDate(expiration_date)
  if adult is not None:
    product.adult = Adult(adult)
  if author is not None:
    product.author = Author(author)
  if brand is not None:
    product.brand = Brand(brand)
  if color is not None:
    product.color = Color(color)
  if edition is not None:
    product.edition = Edition(edition)
  for feature in features:
    product.feature.append(Feature(feature))
  if featured_product is not None:
    product.featured_product = FeaturedProduct(featured_product)
  if genre is not None:
    product.genre = Genre(genre)
  if manufacturer is not None:
    product.manufacturer = Manufacturer(manufacturer)
  if mpn is not None:
    product.mpn = Mpn(mpn)
  if gtin is not None:
    product.gtin = Gtin(gtin)
  if product_type is not None:
    product.product_type = ProductType(product_type)
  if quantity is not None:
    product.quantity = Quantity(quantity)
  if shipping_country is not None:
    product.shipping.shipping_country = ShippingCountry(
        shipping_country)
  if shipping_region is not None:
    product.shipping.shipping_region = ShippingRegion(shipping_region)
  if shipping_service is not None:
    product.shipping.shipping_service = ShippingService(
        shipping_service)
  if shipping_weight is not None:
    product.shipping_weight = ShippingWeight(shipping_weight)
  if shipping_weight_unit is not None:
    product.shipping_weight.unit = shipping_weight_unit
  for size in sizes:
    product.size.append(Size(size))
  if tax_country is not None:
    product.tax.tax_country = TaxCountry(tax_country)
  if tax_region is not None:
    product.tax.tax_region = TaxRegion(tax_region)
  if tax_ship is not None:
    product.tax.tax_ship = TaxShip(tax_ship)
  if year is not None:
    product.year = Year(year)
  return product


class Edited(atom.core.XmlElement):
  """sc:edited element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'edited'


class AttributeLanguage(atom.core.XmlElement):
  """sc:attribute_language element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'attribute_language'


class Channel(atom.core.XmlElement):
  """sc:channel element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'channel'


class FeedFileName(atom.core.XmlElement):
  """sc:feed_file_name element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'feed_file_name'


class FeedType(atom.core.XmlElement):
  """sc:feed_type element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'feed_type'


class UseQuotedFields(atom.core.XmlElement):
  """sc:use_quoted_fields element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'use_quoted_fields'


class FileFormat(atom.core.XmlElement):
  """sc:file_format element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'file_format'
  use_quoted_fields = UseQuotedFields
  format = 'format'


class ProcessingStatus(atom.core.XmlElement):
  """sc:processing_status element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'processing_status'


class DatafeedEntry(gdata.data.GDEntry):
  """An entry for a Datafeed
  """
  content_language = ContentLanguage
  target_country = TargetCountry
  feed_file_name = FeedFileName
  file_format = FileFormat
  attribute_language = AttributeLanguage
  processing_status = ProcessingStatus
  edited = Edited
  feed_type = FeedType


class DatafeedFeed(gdata.data.GDFeed):
  """A datafeed feed
  """
  entry = [DatafeedEntry]


class AdultContent(atom.core.XmlElement):
  """sc:adult_content element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'adult_content'


class InternalId(atom.core.XmlElement):
  """sc:internal_id element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'internal_id'


class ReviewsUrl(atom.core.XmlElement):
  """sc:reviews_url element
  """
  _qname = SC_NAMESPACE_TEMPLATE % 'reviews_url'


class ClientAccount(gdata.data.GDEntry):
  """A multiclient account entry
  """
  adult_content = AdultContent
  internal_id = InternalId
  reviews_url = ReviewsUrl


class ClientAccountFeed(gdata.data.GDFeed):
  """A multiclient account feed
  """
  entry = [ClientAccount]
