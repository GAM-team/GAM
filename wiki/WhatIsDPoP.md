# Intro to DPoP for GAM

> [!CAUTION]
> **Alpha Feature** — GAM DPoP support is currently in alpha and requires a
> special pre-release build. It is not ready for production use. APIs,
> configuration options, and behavior may change without notice.
>
> Do not enable DPoP on production GAM installations. Use a separate test
> environment with non-critical credentials.

----
The latest alpha DPoP build is at:

[https://github.com/GAM-team/GAM/releases/tag/20261113.220459](https://github.com/GAM-team/GAM/releases/tag/20261113.220459)
----

## What is DPoP?

**DPoP** (Demonstrating Proof-of-Possession, [RFC 9449](https://datatracker.ietf.org/doc/html/rfc9449)) is an OAuth 2.0 extension that binds OAuth tokens to a specific cryptographic key. Every time GAM uses a refresh token, it must also present a signed proof that it possesses the private key the token was bound to.

### The Problem with GAM `oauth2.txt`

GAM's OAuth tokens are **bearer tokens** — anyone who has a copy can use them. A stolen `oauth2.txt` file gives an attacker full Google Workspace admin access until the token is revoked. Possible attack vectors include:

- Malware exfiltrating files from the GAM config directory
- Backup systems storing unencrypted copies of `oauth2.txt`
- Insider access to the machine's filesystem
- Accidental exposure in logs, screenshots, or support tickets

### How DPoP Fixes This

With DPoP enabled, GAM binds the refresh token **to a private key on your machine** during the initial OAuth authorization flow. From that point on:

1. Every token refresh request (roughly hourly, or on the next GAM command after expiry) must include a **DPoP proof** — a signed JWT proving possession of the private key.
2. Google's authorization server verifies the proof's signature against the public key the token was bound to.
3. A stolen `oauth2.txt` file cannot be refreshed without the corresponding private key.

If the private key is stored in hardware (TPM, Secure Enclave, YubiKey, or HSM), it **cannot be extracted** — even with root/admin access to the machine. The refresh token becomes bound to a physical device and only that device can use the `oauth2.txt` refresh token.

```
Without DPoP:       stolen oauth2.txt = full admin access

With DPoP:          stolen oauth2.txt = worthless
                    (attacker also needs the private key)

With hardware DPoP: stolen oauth2.txt = worthless
                    (attacker must also physically steal hardware)
```

### What DPoP Does and Does Not Protect

Google's implementation of DPoP protects the **refresh token** — the long-lived credential stored in `oauth2.txt` that GAM uses to obtain short-lived access tokens. The DPoP proof is required whenever GAM exchanges the refresh token for a new access token (usually once per hour).

**Google Access tokens themselves are not DPoP-bound.** Once GAM obtains an access token, it uses it as a normal bearer token for Google API calls. However, access tokens are short-lived (60 minutes or less), limiting the exposure window compared to a refresh token valid for months or years.

## Setup Overview

Setting up DPoP for GAM takes three steps:

1. **[Step 1: Get a Hardware-Backed Key in Place](#step-1-get-a-hardware-backed-key-in-place)** — Provision a non-exportable P-256 (or RSA) signing key in your hardware keystore (Secure Enclave, TPM 2.0, YubiKey, or PKCS#11 HSM/smart card).
2. **[Step 2: Configure GAM and Confirm with `gam check dpop`](#step-2-configure-gam-and-confirm-with-gam-check-dpop)** — Point `gam.cfg` at your backend/key and confirm local signing, hardware backing, and proof verification before touching OAuth.
3. **[Step 3: Recreate OAuth and Confirm with `gam oauth info`](#step-3-recreate-oauth-and-confirm-with-gam-oauth-info)** — Revoke any unbound token, run `gam oauth create` to bind `oauth2.txt` to your key, and confirm end-to-end binding and Google enforcement with `gam oauth info`.

---

## Step 1: Get a Hardware-Backed Key in Place

Choose a backend based on your operating system and security requirements:

| Backend | Platform | Key Storage | Hardware-Backed | Best For |
|---------|----------|-------------|-----------------|----------|
| [`macos_secureenclave`](#macos--secure-enclave-recommended-for-apple-silicon-macs) | macOS (Apple Silicon) | Secure Enclave | Yes | Mac admins with Apple Silicon |
| [`windows_certstore`](#windows--certificate-store--tpm-recommended-for-windows-with-tpm) | Windows | Windows Cert Store (TPM via CNG) | Yes (with TPM) | Windows admins with TPM |
| [`linux_tpm`](#linux--tpm-20-recommended-for-linux-servers) | Linux | TPM 2.0 | Yes | Linux servers with TPM |
| [`yubikey`](#yubikey--piv-cross-platform) | Any | YubiKey PIV | Yes | Cross-platform, portable key |
| [`pkcs11`](#pkcs11--hsm--smart-card-cross-platform) | Any | PKCS#11 token (HSM, smart card) | Yes (with HSM/smart card) | Hardware security modules (HSMs), smart cards |
| [`software`](#software-key-testing-only) | Any | PEM file on disk | No (`WARN` in GAM) | Testing or low-security environments |

> [!IMPORTANT]
> Hardware-backed keys provide the strongest protection because private key
> material never leaves the chip and cannot be exported. Both `gam check dpop`
> and `gam oauth info` inspect key storage and will display an orange `WARN` if a
> software-backed key is detected.

---

### macOS — Secure Enclave (Recommended for Apple Silicon Macs)

The [Apple Secure Enclave](https://support.apple.com/guide/security/the-secure-enclave-sec59b0b31ff/web) is a dedicated security coprocessor in Apple Silicon Macs (M1 and later). Keys generated in the Secure Enclave cannot be exported or read — signing operations happen inside the chip.

**Requirements:**
- macOS 15 (Sequoia) or later
- Apple Silicon (M1 or newer) Mac

#### Permissions & Automation

Decide which macOS account and authentication mode you need before creating the key:

- **Per-user isolation:** Secure Enclave CryptoTokenKit identities are stored in the creating user's [Data Protection Keychain](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web) (see [Protecting Keys with the Secure Enclave](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave)). Create the key while logged in as the same macOS user that will run GAM — other local users (and `root` `LaunchDaemon`s or `sudo` sessions under a different user) cannot access your key.
- **SSH and scheduled tasks (`launchd`):** Standard `sc_auth` keys (without `-t bio`) work over **SSH** and in per-user **LaunchAgents** running as the user that created the key. Keys created with `-t bio` prompt for Touch ID on refresh (~hourly) and when running `gam check dpop` / `gam oauth info`, so omit `-t bio` for headless SSH or unattended jobs.

#### Create and Verify the Key

```bash
sc_auth create-ctk-identity -l gam-dpop -k p-256-ne
```

Or to require Touch ID confirmation when signing DPoP proofs:

```bash
sc_auth create-ctk-identity -l gam-dpop -k p-256-ne -t bio
```

Verify the identity exists:

```bash
sc_auth list-ctk-identities
```

> [!NOTE]
> `sc_auth create-ctk-identity` also creates a 1-year self-signed certificate.
> DPoP uses the underlying private key rather than the certificate, so the key
> remains usable even after that certificate expires.

---

### Windows — Certificate Store / TPM (Recommended for Windows with TPM)

On Windows, GAM uses the `windows_certstore` backend ([CNG / CryptoAPI](https://learn.microsoft.com/en-us/windows/win32/seccng/cng-portal)) to sign with a certificate's private key in the Windows certificate store. Creating the certificate with `"Microsoft Platform Crypto Provider"` stores the private key inside the hardware **TPM 2.0** chip where it cannot be extracted.

**Requirements:**
- Windows 10/11 or Windows Server 2019+
- TPM 2.0 (`"Microsoft Platform Crypto Provider"`). Windows 11 requires a TPM 2.0 device.

#### Choosing a Certificate Store Location (`current_user` vs `local_machine`)

- **Current User (`Cert:\CurrentUser\My`, default):** Isolated to your Windows user profile. Best for interactive desktop/PowerShell sessions by one user. **Note:** `CurrentUser` DPAPI/CNG keys are often locked over public-key SSH sessions or Scheduled Tasks without an interactive console login.
- **Local Machine (`Cert:\LocalMachine\My`):** Required if you run GAM over **SSH**, in **Scheduled Tasks**, or in background services. Append `,local_machine` to `dpop_backend_config` in Step 2.

> [!WARNING]
> **Security trade-off for `local_machine` keys:** A `local_machine` key is
> stored at the machine level rather than isolated to one user profile. An
> attacker who gains local access to that key **still needs read access to your
> `oauth2.txt` file**, so lock down NTFS permissions on your GAM config
> directory and `oauth2.txt` (and grant private-key Read access only to the
> intended service/user account if running as a non-Administrator).

#### Option A: Create the TPM Key with `New-SelfSignedCertificate`

Using PowerShell's [`New-SelfSignedCertificate`](https://learn.microsoft.com/en-us/powershell/module/pki/new-selfsignedcertificate?view=windowsserver2025-ps):

For **Current User** (`Cert:\CurrentUser\My`):

```powershell
New-SelfSignedCertificate `
    -Subject "CN=GAM DPoP Signing Key" `
    -KeyAlgorithm ECDSA_nistP256 `
    -CertStoreLocation Cert:\CurrentUser\My `
    -KeyExportPolicy NonExportable `
    -Provider "Microsoft Platform Crypto Provider" `
    -NotAfter (Get-Date).AddYears(30)
```

Or for **Local Machine** (`Cert:\LocalMachine\My`, open **PowerShell as Administrator**):

```powershell
New-SelfSignedCertificate `
    -Subject "CN=GAM DPoP Signing Key" `
    -KeyAlgorithm ECDSA_nistP256 `
    -CertStoreLocation Cert:\LocalMachine\My `
    -KeyExportPolicy NonExportable `
    -Provider "Microsoft Platform Crypto Provider" `
    -NotAfter (Get-Date).AddYears(30)
```

#### Option B: Systems Where `New-SelfSignedCertificate` Returns `NTE_PROV_TYPE_NOT_DEF` (`0x80090017`)

On some systems (including certain AMD fTPM / Windows 11 setups), `New-SelfSignedCertificate` with `-KeyAlgorithm ECDSA_nistP256 -Provider "Microsoft Platform Crypto Provider"` fails with `0x80090017 NTE_PROV_TYPE_NOT_DEF`. Use `certreq -new` with `ProviderType = 0` instead (set `MachineKeySet = FALSE` for `CurrentUser`, or `MachineKeySet = TRUE` in an elevated PowerShell for `LocalMachine`):

```powershell
@"
[Version]
Signature="`$Windows NT`$"

[NewRequest]
Subject = "CN=GAM DPoP Signing Key"
KeyAlgorithm = ECDSA_P256
KeyLength = 256
HashAlgorithm = sha256
ProviderName = "Microsoft Platform Crypto Provider"
ProviderType = 0
Exportable = FALSE
MachineKeySet = FALSE
RequestType = Cert
ValidityPeriod = Years
ValidityPeriodUnits = 30
"@ | Out-File -Encoding ascii "$env:TEMP\dpop-ec.inf"

certreq -new "$env:TEMP\dpop-ec.inf" "$env:TEMP\dpop-ec.cer"
Remove-Item "$env:TEMP\dpop-ec.inf", "$env:TEMP\dpop-ec.cer"
```

> [!WARNING]
> **Avoid `"Microsoft Software Key Storage Provider"` in production:** If you
> create a certificate using `"Microsoft Software Key Storage Provider"`, the
> private key is stored in software rather than a TPM. `gam check dpop` and
> `gam oauth info` inspect the underlying Windows CNG provider (`Impl Type`) and
> will report `WARN` whenever a software KSP is used.

#### Verify the Certificate Exists

For Current User (`Cert:\CurrentUser\My`) or Local Machine (`Cert:\LocalMachine\My`):

```powershell
Get-ChildItem Cert:\CurrentUser\My |
    Where-Object Subject -eq "CN=GAM DPoP Signing Key" |
    Format-List Subject, Thumbprint, NotAfter, HasPrivateKey
```

---

### Linux — TPM 2.0 (Recommended for Linux Servers)

On Linux, GAM uses `tpm2-pytss` to sign directly with a persistent key in the TPM 2.0 chip. No certificates or PKCS#11 middleware are needed.

**Requirements:**
- Linux with TPM 2.0 (`/dev/tpmrm0`)
- `tpm2-tools` and `libtss2-dev` system packages

#### Permissions & Automation

- **Device access (`/dev/tpmrm0`):** Add the account running GAM to the `tss` group and log out/back in:

  ```bash
  sudo usermod -aG tss $USER
  ```

- **Shared TPM device:** Any user in `tss` (or `root`) can use persistent TPM handles to sign, though they still need read access to `oauth2.txt`. Restrict `~/.gam` (`chmod 700 ~/.gam && chmod 600 ~/.gam/oauth2.txt ~/.gam/gam.cfg`).
- **SSH, `cron`, and `systemd`:** `tss` group membership works over **SSH** and in **`cron`**. For `systemd` services, ensure `SupplementaryGroups=tss` is set and do **not** set `PrivateDevices=yes`.
- **Optional key password (`auth`):** Add `-p <password>` during `tpm2_create` and configure `0x81000001,,<password>` in Step 2.

> [!TIP]
> VMs running on VMware, Proxmox, etc. can attach a vTPM (virtual TPM) so the
> private key is isolated from root inside the guest VM (though host admins
> with access to the hypervisor can still inspect vTPM state).

#### Install Packages, Create, and Verify the Persistent Key

Debian/Ubuntu:
```bash
sudo apt install tpm2-tools libtss2-dev
```

Fedora/RHEL:
```bash
sudo dnf install tpm2-tss-devel tpm2-tools
```

Create and persist a P-256 signing key at handle `0x81000001`:

```bash
# Create a primary ECC key under the owner hierarchy
tpm2_createprimary -C o -g sha256 -G ecc256 -c primary.ctx

# Create an ECDSA P-256 signing child key with explicit scheme
tpm2_create -C primary.ctx -g sha256 -G ecc:ecdsa-sha256 \
    -u key.pub -r key.priv \
    -a "fixedtpm|fixedparent|sensitivedataorigin|userwithauth|sign"

# Load and persist the key at handle 0x81000001
tpm2_load -C primary.ctx -u key.pub -r key.priv -c key.ctx
tpm2_evictcontrol -C o -c key.ctx 0x81000001

# Clean up temporary context/key blobs
rm primary.ctx key.ctx key.pub key.priv
```

Verify the persistent key:

```bash
tpm2_readpublic -c 0x81000001
```

Confirm the output shows `type: ecc`, `curve-id: NIST p256`, and `scheme: ecdsa`.

---

### YubiKey — PIV (Cross-Platform)

YubiKey PIV stores the private key inside the YubiKey's secure element. Works on any OS where GAM runs.

**Requirements:**
- [YubiKey 5 series](https://www.yubico.com/products/yubikey-5-overview/) or newer (with PIV support)
- [`ykman`](https://docs.yubico.com/software/yubikey/tools/ykman/) (YubiKey Manager) installed

```bash
# Generate a P-256 key in slot 9c (Digital Signature)
ykman piv keys generate -a ECCP256 9c pubkey.pem

# Create a self-signed certificate (30-year validity)
ykman piv certificates generate \
    -s "CN=GAM DPoP Signing" \
    -d 10950 \
    9c pubkey.pem

rm pubkey.pem
ykman piv info
```

Slot `9c` does not require touch confirmation after PIN verification. Change the default PIV PIN (`123456`) with `ykman piv access change-pin`.

---

### PKCS#11 — HSM / Smart Card (Cross-Platform)

The `pkcs11` backend works with hardware security modules (cloud/network/USB HSMs) and OpenSC smart cards across Linux, macOS, and Windows using an [RFC 7512](https://www.rfc-editor.org/rfc/rfc7512) `pkcs11:` URI. Provision an EC P-256 (or P-384 / RSA) signing key on your token with your vendor tool or `pkcs11-tool`, and note its token label (`token=`), key label (`object=`) or `CKA_ID` (`id=`), and PKCS#11 module path (`module-path=` or `module-name=`).

> [!TIP]
> Prefer `pin-source=file:/path/to/pin` (`chmod 600`) over embedding
> `pin-value=` directly in `gam.cfg`.

---

### Software Key (Testing Only)

For quick non-production testing without hardware, generate a local EC P-256 PEM key on disk:

```bash
openssl ecparam -genkey -name prime256v1 -noout -out ~/.gam/dpop_key.pem
chmod 600 ~/.gam/dpop_key.pem
```

Both `gam check dpop` and `gam oauth info` flag software keys with `WARN` so you can switch to hardware before production use.

---

## Step 2: Configure GAM and Confirm with `gam check dpop`

### Configure `gam.cfg` for Your Backend

Run the `gam config` command for the key you created in Step 1:

- **macOS Secure Enclave:**
  ```bash
  gam config dpop true dpop_backend macos_secureenclave dpop_backend_config "gam-dpop" save
  ```
- **Windows Certificate Store (Current User):**
  ```powershell
  # By certificate Subject substring or exact thumbprint:
  gam config dpop true dpop_backend windows_certstore dpop_backend_config "GAM DPoP Signing Key" save
  gam config dpop true dpop_backend windows_certstore dpop_backend_config "thumbprint:A1B2C3D4E5..." save
  ```
- **Windows Certificate Store (Local Machine — SSH / Scheduled Tasks):**
  ```powershell
  gam config dpop true dpop_backend windows_certstore dpop_backend_config "GAM DPoP Signing Key,local_machine" save
  gam config dpop true dpop_backend windows_certstore dpop_backend_config "thumbprint:A1B2C3D4E5...,local_machine" save
  ```
- **Linux TPM 2.0:**
  ```bash
  gam config dpop true dpop_backend linux_tpm dpop_backend_config "0x81000001" save
  ```
- **YubiKey PIV (`serial,slot,pin` — leave serial blank for first YubiKey, slot defaults to `9c`):**
  ```bash
  gam config dpop true dpop_backend yubikey dpop_backend_config ",,mypin" save
  ```
- **PKCS#11 HSM / Smart Card:**
  ```bash
  gam config dpop true dpop_backend pkcs11 \
      dpop_backend_config "pkcs11:token=hsm-slot;object=dpop-key;id=%01?module-path=/path/to/libpkcs11.so&pin-source=file:/home/$USER/.gam/pkcs11-pin.txt" save
  ```
- **Software Key (Testing Only):**
  ```bash
  gam config dpop true dpop_backend software dpop_backend_config "dpop_key.pem" save
  ```

### Confirm Local Signing with `gam check dpop`

Run `gam check dpop` before touching your OAuth credentials:

```bash
gam check dpop
```

When everything is working with a hardware-backed key, output looks like:

```text
DPoP: Enabled (macos_secureenclave)
DPoP Backend Config: gam-dpop
Local DPoP Checks:
  Signer Initialization (macos_secureenclave)                               OK
  Key Storage (Hardware: Secure Enclave)                                    OK
  Public JWK & Thumbprint (ES256, o-QZ2IXB6M6whv6s...)                      OK
  Local Test Signature (64 bytes, 10.9 ms)                                  OK
  DPoP Proof & Signature Verification (ES256)                               OK
DPoP Local Signing                                                          OK
Note: Tests local DPoP signing only; OAuth token binding and server enforcement checks run in "gam oauth info".
```

What each check tells you:

| Check | `OK` | `WARN` | `ERROR` |
|-------|------|--------|---------|
| `Signer Initialization` | Loaded configured backend & found the key | — | Missing key, wrong config/PIN, or permission error (exits non-zero) |
| `Key Storage` | Key lives in hardware (`Secure Enclave`, `Microsoft Platform Crypto Provider`, `TPM 2.0 (...)`, `YubiKey PIV`, `PKCS#11 (...)`) | Key is software-backed (`Software TPM`, `Microsoft Software Key Storage Provider`, non-token macOS Keychain, `SoftHSM`, PEM file) or unverified (`ecp`) | — |
| `Public JWK & Thumbprint` | Valid public key, no private fields exposed, valid thumbprint | — | Invalid/corrupt JWK |
| `Local Test Signature` | Test payload signed and signature verified against public JWK | — | Signing failed or signature failed verification |
| `DPoP Proof & Signature Verification` | Full RFC 9449 `dpop+jwt` proof created and cryptographically verified | — | Proof generation or verification failed |

If you see `WARN` on `Key Storage` and `DPoP Local Signing`, your key is software-backed — replace it with a hardware key from Step 1 before creating your OAuth token in Step 3.

Common `Signer Initialization` fixes:

| Error | Fix |
|-------|-----|
| `DPoP macOS Secure Enclave error` | Run `sc_auth list-ctk-identities` and match the label (`dpop_backend_config`). Create the key as the same macOS user running GAM. |
| `DPoP Windows Certificate Store error` | Confirm the cert exists in `Cert:\CurrentUser\My` (or `Cert:\LocalMachine\My` with `,local_machine`). Ensure `-NoExportable`/CNG key isn't orphaned (`NTE_BAD_KEYSET`). |
| `DPoP Linux TPM error` | Confirm membership in `tss`, `/dev/tpmrm0` access, and `tpm2_readpublic -c 0x81000001`. |
| `DPoP PKCS#11 error` | Verify `module-path=`/`module-name=`, `token=`/`object=`/`id=`, and `pin-source=`/`pin-value=` using `pkcs11-tool`. |
| `DPoP YubiKey error` | Ensure the YubiKey is inserted and the PIV slot/PIN are correct. |

> [!NOTE]
> `gam check dpop` **only verifies local DPoP signing** — it does not read
> `oauth2.txt` or contact Google's OAuth server. Do not stop at `gam check dpop`;
> proceed to Step 3 to bind `oauth2.txt` and verify enforcement with `gam oauth info`.

---

## Step 3: Recreate OAuth and Confirm with `gam oauth info`

### Revoke Existing Credentials and Re-Authorize

Existing `oauth2.txt` tokens created before enabling DPoP remain bearer-only until you replace them. Once `gam check dpop` succeeds:

```bash
# Revoke the existing unbound oauth2.txt token (if present)
gam oauth revoke

# Create new DPoP-bound credentials bound to your configured key
gam oauth create
```

This opens a browser (or displays the authorization URL) for Google authentication. During token exchange, GAM sends a DPoP proof signed by your hardware key so Google binds the new refresh token in `oauth2.txt` to your key's JWK thumbprint.

> [!CAUTION]
> After creating DPoP-bound credentials, the refresh token **requires** the
> DPoP key for every refresh. If the hardware key is lost or deleted, you must
> re-authorize with `gam oauth create`.

### Verify End-to-End Binding & Google Enforcement with `gam oauth info`

Run `gam oauth info`:

```bash
gam oauth info
```

Alongside your `Client ID`, `Scopes`, `Google Workspace Admin`, and `Expires` fields, GAM inspects key storage, compares your signer against `oauth2.txt`, and executes live token-endpoint enforcement checks:

```text
...
DPoP: Enabled (macos_secureenclave)
DPoP Backend Config: gam-dpop
DPoP Token Thumbprint: o-QZ2IXB6M6whv6sisQh8oexK6TXMS3xjIPUawxuHrA
DPoP Checks:
  Key Storage (Hardware: Secure Enclave)                                    OK
  Credential Binding (signer matches oauth2.txt thumbprint)                 OK
  Refresh With DPoP (macos_secureenclave)                                   OK
  Reject Refresh Without DPoP                                               OK
  Reject Refresh With Wrong Key                                             OK
DPoP Key Binding                                                            OK
```

What each `gam oauth info` check confirms:

| Check | What It Verifies | Expected Result |
|-------|------------------|-----------------|
| `Key Storage` | Whether the active key lives in hardware or software | `OK` for hardware (`WARN` if software-backed) |
| `Credential Binding` | Signer's JWK thumbprint matches `dpop_thumbprint` stored in `oauth2.txt` | `OK` (`ERROR` if missing from `oauth2.txt` or mismatched) |
| `Refresh With DPoP (<backend>)` | Configured key successfully refreshes the token at Google's endpoint | `OK` |
| `Reject Refresh Without DPoP` | Google rejects a plain bearer refresh without a DPoP proof | `OK` (`ERROR` if Google accepts an unbound refresh) |
| `Reject Refresh With Wrong Key` | Google rejects a proof signed by an unrelated `ephemeral` key | `OK` (`ERROR` if Google accepts a wrong key) |
| `DPoP Key Binding` | Overall summary across local metadata, hardware storage, and live server enforcement | `OK` (`WARN` if software-backed; `ERROR` with `Fix:` steps on failure) |

If `dpop = false` in `gam.cfg` while `oauth2.txt` is DPoP-bound, `gam oauth info` flags `ERROR` with `Fix:` instructions. If `dpop = false` and `oauth2.txt` is unbound (bearer-only), it reports `WARN` and recommends enabling DPoP with a hardware key and running `gam oauth create`.

### Optional: Manual Refresh Tests

You can also observe Google's enforcement directly with `gam oauth refresh`:

- **Normal refresh:** `gam oauth refresh` succeeds.
- **Without DPoP:** `gam config dpop false oauth refresh` is rejected by Google (`DPoP proof required`).
- **Wrong key:** GAM checks the signer's thumbprint locally against `oauth2.txt` before calling Google, so pointing `dpop_backend_config` at another key fails immediately in GAM. Use `gam oauth info` to test Google's server-side wrong-key rejection (`Reject Refresh With Wrong Key`).

---

## Configuration Reference

All DPoP settings are stored in `gam.cfg`:

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `dpop` | `true` / `false` | `false` | Enable or disable DPoP |
| `dpop_backend` | `software`, `macos_secureenclave`, `windows_certstore`, `linux_tpm`, `yubikey`, `pkcs11`, `ecp`, `ephemeral` | `software` | Which signer backend to use |
| `dpop_backend_config` | *(varies by backend)* | *(empty)* | Backend-specific configuration |

### `dpop_backend_config` Format by Backend

| Backend | Format | Example |
|---------|--------|---------|
| `software` | Path to PEM private key file | `dpop_key.pem` |
| `macos_secureenclave` | `label[,application_tag]` | `gam-dpop` |
| `windows_certstore` | `<subject\|thumbprint:HEX>[,current_user\|local_machine]` | `GAM DPoP Signing Key` |
| `linux_tpm` | `handle[,tcti[,auth]]` | `0x81000001` |
| `yubikey` | `serial,slot,pin` | `,,123456` |
| `pkcs11` | RFC 7512 `pkcs11:` URI | `pkcs11:token=hsm-slot;object=dpop-key?module-path=/path/to/libpkcs11.so` |

---

## FAQ

**Q: What happens if my TPM/YubiKey/Mac dies?**

You'll need to re-authorize GAM with `gam oauth revoke` then `gam oauth create` using a new key on replacement hardware. The old refresh token becomes permanently unusable.

**Q: Can I use the same DPoP key for multiple GAM instances?**

Only if they share the same hardware. For example, multiple GAM configs on the same Mac can all use the same Secure Enclave key label. But you cannot share a TPM key across different machines.

**Q: Does DPoP affect GAM performance?**

No. GAM only generates a DPoP proof when refreshing its OAuth access token, which happens at most once per hour. Individual Google API calls are unaffected. A single ECDSA signature takes ~10-75ms on hardware backends and sub-millisecond on software.

**Q: Can I switch from software to hardware backend later?**

Yes, but you must re-authorize. Provision your hardware key (Step 1), update `gam.cfg` and verify with `gam check dpop` (Step 2), then run `gam oauth revoke`, `gam oauth create`, and `gam oauth info` (Step 3).

**Q: What if I disable DPoP after creating bound tokens?**

The existing refresh token will stop working (Google will reject requests without DPoP proofs). You would need to `gam oauth revoke`, disable DPoP, then `gam oauth create` to get an unbound token.

**Q: Does the self-signed certificate matter (Windows/YubiKey/macOS)?**

No. DPoP uses the raw private key for signing, not the X.509 certificate. The certificate is only the container used to store and locate the key; certificate expiration does not affect DPoP functionality.
