If you add some specific files to the same folder as GAM.exe (or gam.py), you can alter the behavior of GAM.  Each file has to exist to do its job - there is no specific content required in the file.

` nocache.txt `
The cache will be disabled at the cost of some performance.
https://groups.google.com/d/msg/google-apps-manager/j24xT9lGYYY/bn-m4kud-hoJ

` noupdatecheck.txt `
Update checks will be disabled.  (Helpful when running GAM from an unattended batch file.)
https://groups.google.com/d/msg/google-apps-manager/RAKFcr7Y7Vs/2obG5hU43hYJ

` nobrowser.txt `
Use during initial installation and configuration on a computer without a web browser. GAM will display a link which you can copy and open from a computer running a browser in order to manually authorize.

# Seeing HTTP API calls made by GAM
GAM can provide full HTTP API call details and headers. This can be useful if you are troubleshooting an issue with GAM and the APIs and Google Support would like to know the exact way GAM is talking to the Google API servers. Just create a file called `debug.gam` in the same folder as gam.exe (Windows) or gam.py / gam (MacOS/Linux). The file can be blank, GAM only checks for the existence of a file called `debug.gam`, it doesn’t care about file contents. Here’s a sample output from GAM with `debug.gam` in place. You can see the [Admin SDK Directory API users.insert()](https://developers.google.com/admin-sdk/directory/v1/reference/users/insert) API call is being utilized by GAM and you can see the request failed (because I tried to use a google.com domain which is not the domain I’m authenticated as). You also see exactly which API parameters GAM sent with the request.

```
$ gam create user user@google.com firstname Jay lastname Lee password P@ssw3rd
Creating account for user@google.com
connect: (www.googleapis.com, 443)
send: 'POST /admin/directory/v1/users?fields=primaryEmail&alt=json&prettyPrint=true HTTP/1.1\r\nHost: www.googleapis.com\r\ncontent-length: 233\r\naccept-encoding: gzip, deflate\r\naccept: application/json\r\nuser-agent: GAM 6.21 - https://github.com/GAM-team/GAM / Jay Lee <jay0lee@gmail.com> / Python 2.7.10 final / Linux-4.2.0-34-generic-x86_64-with-Ubuntu-15.10-wily x86_64 / google-api-python-client/1.5.0 (gzip)\r\ncontent-type: application/json\r\nauthorization: Bearer ya29.Ci4JA4DnhABG2sXcybdIJV7ALJuSRq9bvyxCIxm0vdXPchkOZGapecYozpKHOy-0\r\n\r\n{"primaryEmail": "user@google.com", "password": "$6$heoqb7mBLg0wV/xE$OTWfJtYq9/mKqtZBgtyr5J7lgtW.fANCimmioaGfcXQh7QlxiDNhv/atEm4qIaqsAsQVQBYP/q.6BSPj5V9Qf0", "hashFunction": "crypt", "name": {"givenName": "Jay", "familyName": "Lee"}}'
reply: 'HTTP/1.1 403 Forbidden\r\n'
header: Vary: Origin
header: Vary: X-Origin
header: Content-Type: application/json; charset=UTF-8
header: Content-Encoding: gzip
header: Date: Wed, 22 Jun 2016 17:48:48 GMT
header: Expires: Wed, 22 Jun 2016 17:48:48 GMT
header: Cache-Control: private, max-age=0
header: X-Content-Type-Options: nosniff
header: X-Frame-Options: SAMEORIGIN
header: X-XSS-Protection: 1; mode=block
header: Server: GSE
header: Alternate-Protocol: 443:quic
header: Alt-Svc: quic=":443"; ma=2592000; v="34,33,32,31,30,29,28,27,26,25"
header: Transfer-Encoding: chunked

ERROR: 403: Not Authorized to access this resource/api - forbidden
```

Here's some details on the debug logs above:

`$ gam create user user@google.com firstname Jay lastname Lee password P@ssw3rd`

this is the GAM command run by the admin.

`POST /admin/directory/v1/users?fields=primaryEmail&alt=json&prettyPrint=true HTTP/1.1\r\nHost: www.googleapis.com`

in order to create a user, GAM is making an [HTTP/1.1 POST request](https://en.wikipedia.org/wiki/POST_(HTTP)) to the URL https://www.googleapis.com/admin/directory/v1/users?fields=primaryEmail&alt=json&prettyPrint=true. HTTPS / 443 is always used by GAM and the Google APIs.

`user-agent: 6.21 - https://github.com/GAM-team/GAM / Jay Lee <jay0lee@gmail.com> / Python 2.7.10 final / Linux-4.2.0-34-generic-x86_64-with-Ubuntu-15.10-wily x86_64 / google-api-python-client/1.5.0 (gzip)`

GAM includes a User-Agent HTTP header with details about the GAM version and Python / System version in use.

`authorization: Bearer ya29.Ci4JA4DnhABG2sXcybdIJV7ALJuSRq9bvyxCIxm0vdXPchkOZGapecYozpKHOy-0`

GAM sends an "Authorization" HTTP header with the OAuth access token the admin authorized GAM to use to verify with Google that a G Suite admin is making this calls.

`{"primaryEmail": "user@google.com", "password": "$6$heoqb7mBLg0wV/xE$OTWfJtYq9/mKqtZBgtyr5J7lgtW.fANCimmioaGfcXQh7QlxiDNhv/atEm4qIaqsAsQVQBYP/q.6BSPj5V9Qf0", "hashFunction": "crypt", "name": {"givenName": "Jay", "familyName": "Lee"}}`

This is the HTTP body and POST data of the GAM request. It's in JSON format. Notice that GAM took the `P@ssw3rd` password the admin supplied GAM on the command line and pre-hashed it using the [sha-512 crypt algorithm](https://en.wikipedia.org/wiki/Crypt_(C)#SHA2-based_scheme) as [recommended by Google](https://developers.google.com/admin-sdk/directory/v1/reference/users#password:~:text=We%20recommend%20sending%20the%20password%20property%20value%20as%20a%20base%2016%20bit%2C%20hexadecimal%2Dencoded%20hash%20value.).

`HTTP/1.1 403 Forbidden`

Google servers responded with a 403 Forbidden response because the admin user is in my test domain and trying to create a @google.com user account which they are forbidden from doing.