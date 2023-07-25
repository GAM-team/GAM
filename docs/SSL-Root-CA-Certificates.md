# SSL Root CA Certificates

For an overall discussion of SSL, see: https://sites.google.com/site/x509certificateusage/

Google Internet Authority, see: https://pki.google.com/index.html

Trusted Roots, see: https://pki.google.com/faq.html What roots should we trust for connecting to Google?

GAM internally uses the PEM file mentioned in the previous link; it is also included in the GAM distribution
as `cacerts.pem`.

If your site uses a firewall that does SSL inspection/decryption, you will need a vendor specific certificate.
If your vendor's certificate is in DER format, you will have to convert it to PEM format.
* `openssl x509 -inform DER -in firewallcert.crt -out firewallcert.pem -outform PEM`

Copy cacerts.pem from the folder containing gam.exe/gam.py to the folder containing gam.cfg.

Append the contents of firewallcert.pem to cacerts.pem
* Linux/Mac OS - `cat firewallcert.pem >> cacerts.pem`
* Windows - `type firewallcert.pem >> cacerts.pem`

Tell GAM to use the new cacerts.pem:
```
gam config cacerts_pem cacerts.pem save
```

