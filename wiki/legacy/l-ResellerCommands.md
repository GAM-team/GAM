- [Overview](#overview)
- [Create A Resold Customer](#create-a-resold-customer)
- [Update A Resold Customer](#update-a-resold-customer)
- [Get Info About A Resold Customer](#get-info-about-a-resold-customer)
- [Create A Resold Subscription](#create-a-resold-subscription)
- [Update A Resold Subscription](#update-a-resold-subscription)
- [Get Info About Resold Subscriptions](#get-info-about-resold-subscriptions)
- [Delete A Resold Subscription](#delete-a-resold-subscription)
- [Perform Admin Actions For A Resold Customer](#perform-admin-actions-for-a-resold-customer)
- [Perform User Data Actions For A Resold Customer](#perform-user-data-actions-for-a-resold-customer)

# Overview
GAM 4.12 and newer support the G Suite Reseller API. To use these GAM commands, you must authorize GAM using a reseller account.

# Create A Resold Customer
## Syntax
```
gam create resoldcustomer <domain> [alternateemail <email>] [phone <phone>] [address1 <address>] [address2 <address>] [address3 <address>] [contact <name>] [country <country>] [city <city>] [organizationname <name>] [postalcode <code>] [region <region>] [transfertoken <token>]
```
Create a new resold customer. The argument domain is required and specifies the primary domain of the new customer. The argument alternateemail specifies the email address of a contact at the customer and should not be the same domain as primary domain. The argument phone specifies a phone number for the customer. The arguments address1, address2 and address3 specify up to three lines of address for the customer. The argument contact specifies the name of a person contact at the customer. The arguments country, city, postalcode and region specify the location of the customer. The argument organizationname gives a full name for the customer. The optional argument transfertoken indicates the customer already has Google subscriptions from another reseller or direct and has provided the transfer token. Transfer token generation is explained in [Google's help article](https://support.google.com/work/reseller/answer/6182435?hl=en).

## Example
This example creates a new customer, acme.com.
```
gam create resoldcustomer acme.com alternateemail acmecorp@gmail.com phone 123-456-7890 address1 "10 Main St." contact "John Acme" country US city "New York" locality region "New York" organizationname "Acme Corp"
```
----

# Update A Resold Customer
## Syntax
```
gam update resoldcustomer <domain>  [alternateemail <email>] [phone <phone>] [address1 <address>] [address2 <address>] [address3 <address>] [contact <name>] [country <country>] [city <city>] [organizationname <name>] [postalcode <code>] [region <region>] [transfertoken <token>]
```
Update an existing resold customer. The argument domain is required and specifies the primary domain of the customer. The argument alternateemail specifies the email address of a contact at the customer and should not be the same domain as primary domain. The argument phone specifies a phone number for the customer. The arguments address1, address2 and address3 specify up to three lines of address for the customer. The argument contact specifies the name of a person contact at the customer. The arguments country, city, postalcode and region specify the location of the customer. The argument organizationname gives a full name for the customer. The optional argument transfertoken indicates the customer already has Google subscriptions from another reseller or direct and has provided the transfer token. Transfer token generation is explained in [Google's help article](https://support.google.com/work/reseller/answer/6182435?hl=en).

## Example
This example updates the customer acme.com with a new address and phone.
```
gam update resoldcustomer acme.com phone 987-654-3210 address1 "100 North St."
```
----

# Get Info About A Resold Customer
## Syntax
```
gam info resoldcustomer <domain>
```
Get information about a resold customer. The domain argument is required and specifies the domain of the customer.

## Example
This example displays information about the resold customer acme.com.
```
gam info resoldcustomer acme.com

 customerDomainVerified: False
 alternateEmail: acmecorp@gmail.com
 customerDomain: acme.com
 resourceUiUrl: https://www.google.com/a/cpanel/acme.com/AdminHome
 phoneNumber: +1 987-654-3210
 postalAddress: 

  organizationName: Acme Corp
  countryCode: US
  locality: New York
  region: NY
  contactName: John Acme
  addressLine1: 100 North St.
  postalCode: 10011
 customerId: C03ay2uag
```
----

# Create A Resold Subscription
## Syntax
```
gam create resoldsubscription <domain> [dealcode <code>] [plan <plan>] [purchaseorderid <po>] [seats <number> [max]] [sku <sku>] [transfertoken <token]
```
Create a new subscription for a resold customer. The domain argument specifies the domain of the resold customer. The optional dealcode argument specifies a special dealcode provided by Google. The plan argument specifies the plan for the subscription and can be one of ANNUAL_MONTHLY_PAY, ANNUAL_YEARLY_PAY, FLEXIBLE and TRIAL. The seats arguments specifies the number of seats and (optional) max number of seats. The SKU argument specifies the license SKU for the subscription. [SKUs are listed here](https://github.com/jay0lee/GAM/wiki/LicenseExamples#license-types). The optional argument transfertoken indicates the customer already has Google subscriptions from another reseller or direct and has provided the transfer token. Transfer token generation is explained in [Google's help article](https://support.google.com/work/reseller/answer/6182435?hl=en).

## Example
This example creates a trial G Suite Basic subscription for acme.com
```
gam create resoldsubscription acme.com plan TRIAL seats 10 sku "G Suite Basic"
```
----

# Update A Resold Subscription
## Syntax
```
gam update resoldsubscription <domain> <sku> [activate] [suspend] [startpaidservice] [renewal <renewaltype>] [seats <number> [max]] [plan <plan> [seats <number> [max]] [purchaseorderid <po>] [dealcode <code>]]
```
Updates an existing subscription for a resold customer. The domain argument specifies the customer's domain. The SKU argument specifies the license SKU of the existing subscription. [SKUs are listed here](https://github.com/jay0lee/GAM/wiki/LicenseExamples#license-types). The optional arguments activate, suspend and startpaidservice change the status of the subscription as indicated. The optional argument renewal sets the renewal type of the subscription with possible values AUTO_RENEW_MONTHLY_PAY, AUTO_RENEW_YEARLY_PAY, CANCEL, RENEW_CURRENT_USERS_MONTHLY_PAY, RENEW_CURRENT_USERS_YEARLY_PAY or SWITCH_TO_PAY_AS_YOU_GO. The optional argument seats sets the number of seats as well as an optional max number of seats. The optional argument plan changes the subscription plan. Plan types include ANNUAL_MONTHLY_PAY, ANNUAL_YEARLY_PAY, FLEXIBLE and TRIAL. When modifying the plan you must also set seats and can optional set purchaseorderid and dealcode.

## Example
This example suspend's acme.com's G Suite Basic trial
```
gam update resoldsubscription acme.com "G Suite Basic" suspend
```
----

# Get Info About Resold Subscriptions
## Syntax
```
gam info resoldsubscriptions <domain> [transfertoken <token>]
```
Prints detailed information about a resold customer's subscriptions. The domain argument specifies the domain of the customer. The optional argument transfertoken indicates the customer already has Google subscriptions from another reseller or direct and has provided the transfer token. Transfer token generation is explained in [Google's help article](https://support.google.com/work/reseller/answer/6182435?hl=en).

## Example
This example shows the subscriptions for acme.com.
```
gam info resoldsubscriptions acme.com

subscriptions: 

   status: ACTIVE
   skuId: Google-Apps-For-Business
   trialSettings: 

    trialEndTime: 1488403594252
    isInTrial: True
   resourceUiUrl: https://www.google.com/a/cpanel/acme.com/AdminHome#DomainSettings/notab=1&subtab=subscriptions
   creationTime: 1485811594377
   customerDomain: acme.com
   plan: 

    planName: TRIAL
    isCommitmentPlan: False
   seats: 

    maximumNumberOfSeats: 10
    licensedNumberOfSeats: 1
   subscriptionId: 86064838
   billingMethod: ONLINE
   customerId: C03rqrnca

   renewalSettings: 

    renewalType: SWITCH_TO_PAY_AS_YOU_GO
   skuId: Google-Chrome-Device-Management
   trialSettings: 

    trialEndTime: 1486223725958
    isInTrial: False
   resourceUiUrl: https://www.google.com/a/cpanel/acme.com/AdminHome#DomainSettings/notab=1&subtab=subscriptions
   purchaseOrderId: 1234
   creationTime: 1485824537320
   customerDomain: acme.com
   status: ACTIVE
   plan: 

    planName: ANNUAL
    commitmentInterval: 

     endTime: 1517759725958
     startTime: 1486223725958
    isCommitmentPlan: True
   seats: 

    numberOfSeats: 11
    maximumNumberOfSeats: 50000
    licensedNumberOfSeats: 11
   subscriptionId: 86079802
   billingMethod: ONLINE
   customerId: C03rqrnca
```
----

# Delete A Resold Subscription
## Syntax
```
gam delete resoldsubscription <domain> <sku> <deletiontype>
```
Delete's a resold subscription for a customer. The domain argument specifies the domain of the customer. The SKU argument specifies the license SKU of the subscription. The deletiontype argument specifies the deletion type and can be one of cancel, downgrade, suspend or transfer_to_direct.

## Example
This example cancels Chrome Device Management for acme.com.
```
gam delete resoldsubscription acme.com Google-Chrome-Device-Management cancel
```
----

# Perform Admin Actions For A Resold Customer
## Syntax
```
export CUSTOMER_ID=<customer id>
gam print users
```
If your customer has authorized you to [perform actions on their behalf in the admin console](https://support.google.com/work/reseller/answer/6182366?hl=en), you can perform some of these actions via GAM. When authorized as your admin account, use the "gam info resoldcustomer <domain>" command to learn the customerId of the customer. Then set the CUSTOMER_ID environment variable to that value. Once, set GAM admin commands you run will act against the customer's G Suite account instead of your reseller account.

## Example
This example allows you to act on behalf of acme.com and create a new admin for acme.com.
```
gam info resoldcustomer acme.com
 customerDomainVerified: False
 alternateEmail: acmecorp@gmail.com
 customerDomain: acme.com
 ...
 ...
 customerId: C03rqrnca

export CUSTOMER_ID=C03rqrnca
gam create user admin@acme.com firstname Admin lastname User password Sup3rS3cr3t admin on
```
----

# Perform User Data Actions For A Resold Customer
## Syntax
```
gam user <email> check serviceaccount
gam user <email> add drivefile localfile <filepath>
```
If your customer authorizes your service account, you can perform user data actions for your customer such as managing Gmail, Drive and Calendar. Use the gam user <email> check serviceaccount command to see if your service account has rights to manage customer user data. Follow the provided instructions to configure authorization. Then run regular user data GAM commands.