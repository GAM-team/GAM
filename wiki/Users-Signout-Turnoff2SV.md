# Users - Signout and Turn off 2-Step Verification
- [API documentation](#api-documentation)
- [Definitions](#definitions)
- [Signout Users](#signout-users)
- [Turn off 2-Step Verification](#turn-off-2-step-verification)

## API documentation
* [Directory API - Signout](https://developers.google.com/admin-sdk/directory/reference/rest/v1/users/signOut)
* [Directory API - Turn off 2SV](https://developers.google.com/admin-sdk/directory/reference/rest/v1/twoStepVerification/turnOff)

## Definitions
* [`<UserTypeEntity>`](Collections-of-Users)

## Signout Users
Sign a user out of all web and device sessions and reset their sign-in cookies.
The user will have to sign in by authenticating again.
```
gam <UserTypeEntity> signout
```
## Turn off 2-Step Verification
Turn off 2-Step Verification for a user.
If successful, this call will turn off 2-Step Verification and also remove all registered second steps on the user account.
This call will fail if **any** of the following is true:
* the user is suspended
* the user is not enrolled in 2-Step Verification.
* the user has 2-Step Verification enforced.
* the user is enrolled in the Advanced Protection Program.
```
gam <UserTypeEntity> turnoff2sv
```
