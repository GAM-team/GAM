- [Getting Verification Codes For A Domain](#getting-verification-codes-for-a-domain)
- [Performing Domain Verification](#performing-domain-verification)
- [Getting info about existing successful domain verifications](#getting-info-about-existing-successful-domain-verifications)

GAM 3.04 and later allows admins to generate the details for domain verification as well as attempt the actual verify and print out existing verifications.

In order to use a domain with G Suite, all primary, secondary and alias domains must be verified. Once an admin verifies a domain, they will be able to add it and it's subdomains as secondary and alias domains in G Suite.

It's important to understand that the verification codes are unique to each user. If admin A generates the verification codes and admin B attempts to verify those codes, it will fail.

# Getting Verification Codes For A Domain
## Syntax
```
gam create verify <domain>
```
Displays the DNS and Web server verification codes that are needed in order to verify the given domain name.

## Example
This example shows the DNS and Web codes that would need to be created in order for the admin to verify the example.com domain.
```
gam create verify example.com

TXT Record Name:   example.com
TXT Record Value:  google-site-verification=ORsLMhIHCe2TFX3jeSgRpUk4A4WfywZ9znTS
sjfWDbE

CNAME Record Name:   3umntkhyge7x.example.com
CNAME Record Value:  gv-so2ram4atzoczj.dv.googlehosted.com

Saving web server verification file to: google38973a5e4d01f5ee.html
Verification File URL: http://example.com/google38973a5e4d01f5ee.html

Meta URL:               http://example.com/
Meta HTML Header Data:  <meta name="google-site-verification" content="ORsLMhIHC
e2TFX3jeSgRpUk4A4WfywZ9znTSsjfWDbE" />
```

---


# Performing Domain Verification
## Syntax
```
gam update verify <domain> <CNAME|TXT|SITE>
```
Attempt domain verification of the given domain using the given method (cname, txt or site). In order for verification to succeed, the domain's DNS or Web Server must have been updated to contain the correct record.

## Example
This example attempts DNS TXT record verification of the example.com domain (and is expected to fail).
```
gam update verify example.com txt

ERROR: The necessary verification token could not be found on your site.
Method:  DNS_TXT
Token:      google-site-verification=ORsLMhIHCe2TFX3jeSgRpUk4A4WfywZ9znTSsjfWDbE

DNS Record: $Id: example.com 1921 2013-10-21 04:00:39Z dknight $
DNS Record: v=spf1 -all
```

This example attempts DNS TXT record verification of the jay.powerposters.org domain and succeeds.
```
gam update verify jay.powerposters.org txt

SUCCESS!
Verified:  jay.powerposters.org
ID:  dns%3A%2F%2Fjay.powerposters.org
Type: INET_DOMAIN
All Owners:
 admin@jay.powerposters.org

You can now add jay.powerposters.org or it's subdomains as secondary or domain aliases of the jay.powerposters.org G Suite Account.
```

---


# Getting info about existing successful domain verifications
## Syntax
```
gam info verify
```
Prints out a list of the DNS domains that the given administrator has already successfully performed domain verification against.

## Example
This example prints out all the existing domain verifications for admin@jay.powerposters.org.
```
gam info verify

Site: secondary.ditoapps.com
Type: INET_DOMAIN
Owners:
 admin@jay.powerposters.org

Site: sdomain.jay.powerposters.org
Type: INET_DOMAIN
Owners:
 admin@jay.powerposters.org

Site: jay.powerposters.org
Type: INET_DOMAIN
Owners:
 admin@jay.powerposters.org

Site: jaylee.powerposters.org
Type: INET_DOMAIN
Owners:
 admin@jay.powerposters.org

Site: http://sites.google.com/a/jay.powerposters.org/my-site/
Type: SITE
Owners:
 jay@jay.powerposters.org
 admin@jay.powerposters.org

Site: http://sites.google.com/a/jay.powerposters.org/my-site2/
Type: SITE
Owners:
 jay@jay.powerposters.org
 admin@jay.powerposters.org

Site: vtest.powerposters.org
Type: INET_DOMAIN
Owners:
 admin@jay.powerposters.org
```

---
