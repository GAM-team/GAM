- [About Admin Settings](#about-admin-settings)
- [Modify Domain Single Sign-on (SSO) Settings](#modify-domain-single-sign-on-sso-settings)
- [Uploading the SSO Key](#uploading-the-sso-key)
- [Outbound Email Gateway Settings](#outbound-email-gateway-settings)
- [Email Routing](#email-routing)

# About Admin Settings
```diff
- Google has deprecated the Admin Settings API and it has been removed from GAM 3.8 and newer.
- https://gsuite-developers.googleblog.com/2016/08/saying-goodbye-to-gdata-admin-settings.html
- If you still use these commands, keep a copy of GAM 3.72 or older around, the commands should
- continue to work until Google turns the API off.
```

# Modify Domain Single Sign-on (SSO) Settings
## Syntax
```
gam update domain sso_settings enabled true|false sign_on_uri <URI> sign_out_uri <URI> password_uri <URI> whitelist <IP list> use_domain_specific_issuer true|false
```
Updates the Google Apps SSO settings. enabled turns SSO on or off. sign\_on\_uri, sign\_out\_uri and password\_uri should be the full URI used for each of these SSO steps. whitelist is a list of IP addresses where SSO should be applied (other IP addresses will not use SSO). use\_domain\_specific\_issuer determines if a unique domain name is issued in the SAML request based on the Google Apps domain the user visited.

## Example
This example turns SSO on for the domain with the given URIs used for SSO.
```
gam update domain sso_settings enabled true sign_on_uri https://sso.acme.com sign_out_uri https://sso.acme.com/logout password_uri https://sso.acme.com/password use_domain_specific_issuer true
```

---


# Uploading the SSO Key
## Syntax
```
gam update domain sso_key <public key file>
```
Uploads the given public key file, replacing the existing key on Google's servers. It may be necessary to have SSO enabled before uploading the SSO key.

## Example
This example uploads the public-key.der file to Google's servers.
```
gam update domain sso_key public-key.der
```

---

# Outbound Email Gateway Settings
## Syntax
```
gam update domain outbound_gateway <SMTP Server Domain or IP> mode smtp|smtp_tls
```
Configures all outbound Google Apps mail to go directly to the given SMTP Server domain name or IP address. If smtp is specified, plain text smtp is used in the transfer. If smtp\_tls is specified, encryption will be used on the outgoing connection.

**Warning:** Be sure you know what you're doing with this setting. If you enter an invalid IP/domain or the host is not configured to accept mail properly, you could break outgoing mail for your entire Google Apps organization.

## Example
This example turns outbound gateway on, directs it to a Postini server and forces the use of encryption (smtp\_tls) for connections.
```
gam update domain outbound_gateway outbounds10.psmtp.com mode smtp_tls
```

---


# Email Routing
## Syntax
```
gam update domain email_route destination <SMTP Server Domain or IP> rewrite_to true|false enabled true|false bounce_notifications true|false  account_handling all_accounts|provisioned_account|unknown_accounts
```
Creates a new email route for incoming mail. destination is a valid domain or IP address that will accept the mail. rewrite\_to determines if the domain name of the message is replaced with the destination domain. enabled determines if the routing rule is turned on or off. bounce\_notifications determines if delivery failures are sent for messages not received by the destination server. account\_handling determines which set of users mail will be routed for, all, existing/provisioned or unknown.

## Example
This example routes all unknown mail to acme's legacy Exchange server.
```
gam update domain email_route destination exchange.acme.com rewrite_to false enabled true bounce_notifications false account_handling unknown_accounts
```

---
