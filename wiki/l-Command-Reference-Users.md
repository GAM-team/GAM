# GAM Users Command Reference

Adapted with love from the [GAM Cheat Sheet](https://gamcheatsheet.com/)

***

## gam **create** | **update** user [\<user email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email) [options]

## gam [\<who\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#who) **update** user [options]

Common options:
* [firstname \<First Name\>]
* [lastname \<Last Name\>]  
* [password \<Password\>]
* [email \<New Email\>]  
* [gal on|off]
* [suspended on|off]
* [sha]
* [md5]
* [crypt]
* [nohash]  
* [changepassword on|off]
* [org \<Org Name\>]

Extended options:
* [relation \<relation type\> \<relation value\>]
* [externalid \<id type\> \<id value\>]
* [phone type \<phone type\> value \<phone value\> primary|notprimary]
* [organization
  * name \<org name\>
  * title \<org title\>
  * type \<org type\>
  * department \<org dept\>
  * symbol \<org symbol\>
  * costcenter \<org cost center\>
  * location \<org location\>
  * description \<org desc\>
  * domain \<org domain\>
  * primary|notprimary]
* [address
  * type \<address type\>
  * unstructured \<unstructered address\>
  * extendedaddress \<address extended address\>
  * streetaddress \<address street address\>
  * locality \<address locality\>
  * region \<address region\>
  * postalcode \<address postal code\>
  * pobox \<address pobox\>
  * countrycode \<address country code\>
  * primary|notprimary]
* [im type \<im type\> protocol \<im protocol\> primary \<im value\>]
* [location
  * type \<location type\>
  * area \<area\>
  * building \<building\>
  * desk \<desk\>
  * floor \<floor\>
  * section \<section\>
  * endlocation]
* [sshkeys
  * expires \<date\>
  * key \<keyvalue\>]
* [posixaccounts
  * gecos \<gecos\>
  * gid \<numeric gid\>
  * uid \<numeric uid\>
  * home \<home path\>
  * primary true|false
  * shell \<shell\>
  * system \<systemid\>
  * username \<username\>
  * endposix]
* [agreedtoterms on|off]
* [schemaname.fieldname \<fieldvalue\>]
* [schemaname.multivaluefieldname multivalued \<fieldvalue\>]

Extended options for update only:
* [customerid \<string\>]
* [otheremail home|work|other|\<custom\> \<email address\>]

## gam **info** user [\<user email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email)
* [nogroups]
* [noaliases]
* [nolicenses]
* [noschemas]
* [schemas list,of,schemas]
* [userview]
* [skus \<list,of,skus\>]

## gam delete user [\<user email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email)

## gam undelete user [\<user email\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#user-email) [org \<org Name\>]

## gam [\<who\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#who) print

## gam print users
* [allfields]
* [custom all|list,of,schemas]
* [userview]
* [ims]
* [emails]
* [externalids]
* [relations]
* [addresses]
* [organizations]
* [phones]
* [licenses]
* [photo]
* [firstname]
* [lastname]
* [emailparts]
* [deleted_only]
* [id]
* [orderby email|firstname|lastname]
* [query \<query\>]
* [ascending|descending]
* [domain \<Domain Name\>]
* [fullname]
* [ou]
* [suspended]
* [changepassword]
* [gal]
* [agreed2terms]
* [admin]
* [creationtime]
* [aliases]
* [lastlogintime]
* [groups]
* [ismailboxsetup]
* [todrive]

## gam [\<who\>](https://github.com/jay0lee/GAM/wiki/Command-Reference:-Definitions#who) show gmailprofile|gplusprofile [todrive]