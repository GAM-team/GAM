# Intro to DPoP for GAM

> [!CAUTION]
> **Alpha Feature** — GAM DPoP support is currently in alpha and requires a
> special pre-release build. It is not ready for production use. APIs,
> configuration options, and behavior may change without notice.
>
> Do not enable DPoP on production GAM installations. Use a separate test
> environment with non-critical credentials.

----
The latest alpha DPoP build (Alpha 8) is at:

[https://github.com/GAM-team/GAM/releases/tag/20261121.024548](https://github.com/GAM-team/GAM/releases/tag/20261121.024548)
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

Setting up DPoP for GAM follows three stages:

1. **[Stage 1: Provision a Hardware Key & Configure GAM](#stage-1-provision-a-hardware-key--configure-gam)** — Choose the backend for your platform, safely provision a non-exportable signing key on real hardware, and save GAM's `dpop` settings.
2. **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)** — Verify signer initialization, hardware key storage, and local DPoP proof signing before touching OAuth credentials.
3. **[Stage 3: Recreate OAuth and Confirm with `gam oauth info`](#stage-3-recreate-oauth-and-confirm-with-gam-oauth-info)** — Revoke any existing bearer token, create new DPoP-bound credentials (`gam oauth create`), and confirm Google enforces key binding (`gam oauth info`).

---

## Stage 1: Provision a Hardware Key & Configure GAM

Choose a backend based on your operating system and security requirements:

| Backend | Platform | Key Storage | Hardware-Backed | Best For |
|---------|----------|-------------|-----------------|----------|
| [`macos_secureenclave`](#macos--secure-enclave-recommended-for-apple-silicon-macs) | macOS (Apple Silicon) | Secure Enclave | Yes | Mac admins with Apple Silicon |
| [`windows_certstore`](#windows--certificate-store--tpm-recommended-for-windows-with-tpm) | Windows | Windows Cert Store (TPM via CNG) | Yes (with TPM) | Windows admins with TPM |
| [`linux_tpm`](#linux--tpm-20-recommended-for-linux-servers) | Linux | TPM 2.0 | Yes | Linux servers with TPM |
| [`yubikey`](#yubikey--piv-cross-platform) | Any | YubiKey PIV | Yes | Cross-platform, portable key |
| [`fido2_previewsign`](#fido2-previewsign--security-key-experimental-cross-platform) | Any | YubiKey 5.8+ / CTAP 2.3 (`previewSign`) | Yes | Certificate-free FIDO2 hardware key (experimental) |
| [`pkcs11`](#pkcs11--hsm--smart-card-cross-platform) | Any | PKCS#11 token (HSM, smart card) | Yes (with HSM/smart card) | Hardware security modules (HSMs), smart cards |
| [`software`](#software-key-testing-only) | Any | PEM file on disk | No (`WARN` in GAM) | Testing or low-security environments |

> [!IMPORTANT]
> Hardware-backed keys provide the strongest protection because private key
> material never leaves the chip and cannot be exported. Both `gam check dpop`
> and `gam oauth info` inspect your keystore and display an orange `WARN` if a
> software-backed key is detected.

---

### macOS — Secure Enclave (Recommended for Apple Silicon Macs)

The [Apple Secure Enclave](https://support.apple.com/guide/security/the-secure-enclave-sec59b0b31ff/web) is a dedicated security coprocessor in Apple Silicon Macs (M1 and later). Keys generated in the Secure Enclave cannot be exported or read — signing operations happen inside the chip.

**Requirements & Real-World Hardware Notes:**
- **macOS 15 (Sequoia) or later on Apple Silicon (M1 or newer).** Intel Macs (even with T2) and macOS virtual machines without Secure Enclave passthrough cannot create CryptoTokenKit Secure Enclave identities with `sc_auth` — use a [YubiKey](#yubikey--piv-cross-platform) or [PKCS#11](#pkcs11--hsm--smart-card-cross-platform) token instead.
- **Per-user isolation:** Secure Enclave CryptoTokenKit identities live in the creating user's [Data Protection Keychain](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web) (see [Protecting Keys with the Secure Enclave](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave)). Create the key while logged in as the same macOS user that will run GAM — other users, `sudo` under another user, and `root` `LaunchDaemon`s cannot access your key.
- **Headless / SSH / `launchd` vs. Touch ID (`-t bio`):** Standard keys (without `-t bio`) work over SSH and in per-user `LaunchAgent` jobs. Keys created with `-t bio` prompt for Touch ID on token refresh (roughly hourly) and during `gam check dpop` / `gam oauth info`, which blocks SSH and background automation.
- **Duplicate labels:** Check `sc_auth list-ctk-identities` before creating a key. Running `sc_auth create-ctk-identity -l gam-dpop` multiple times creates multiple entries; remove stale ones (`sc_auth delete-ctk-identity -h <PublicKeyHash>`) so GAM resolves cleanly.

#### 1. Check Existing Identities and Create the Key

```bash
# Check what CryptoTokenKit identities already exist
sc_auth list-ctk-identities

# Create a P-256 non-exportable Secure Enclave key (SSH/automation friendly)
sc_auth create-ctk-identity -l gam-dpop -k p-256-ne

# Or require Touch ID confirmation when signing DPoP proofs (interactive desktop only)
# sc_auth create-ctk-identity -l gam-dpop -k p-256-ne -t bio

# Verify the new identity appears
sc_auth list-ctk-identities
```

> [!NOTE]
> `sc_auth create-ctk-identity` also generates a 1-year self-signed certificate.
> DPoP uses the underlying private key rather than the certificate, so the key
> continues working after certificate expiry.

#### 2. Configure GAM

```bash
gam config dpop true dpop_backend macos_secureenclave dpop_backend_config "gam-dpop" save
```

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

### Windows — Certificate Store / TPM (Recommended for Windows with TPM)

On Windows, GAM uses the `windows_certstore` backend ([CNG / CryptoAPI](https://learn.microsoft.com/en-us/windows/win32/seccng/cng-portal)) to sign with a certificate's private key in the Windows certificate store. Storing the key under `"Microsoft Platform Crypto Provider"` places the private key inside your hardware **TPM 2.0** chip where it cannot be extracted.

**Requirements & Real-World Hardware Notes:**
- **Windows 10/11 or Windows Server 2019+ with TPM 2.0 enabled in BIOS/UEFI.** Before provisioning, verify Windows sees a ready TPM and the Platform Crypto Provider:
  ```powershell
  Get-Tpm | Format-List TpmPresent, TpmReady
  certutil -csplist | Select-String "Platform Crypto"
  ```
  If `TpmPresent` or `TpmReady` is `False`, enable/initialize TPM 2.0 (Intel PTT or AMD fTPM) in UEFI firmware settings first.
- **`CurrentUser` vs. `LocalMachine` (SSH & Scheduled Tasks):**
  - `Cert:\CurrentUser\My` (default) works for interactive desktop/PowerShell sessions. However, over public-key OpenSSH sessions or Scheduled Tasks without a stored password (Network Logon Type 3), Windows does not unlock user DPAPI credentials and `gam` fails with `0x80090016` (`NTE_BAD_KEYSET`).
  - `Cert:\LocalMachine\My` (`,local_machine`) is required for SSH, Scheduled Tasks, and background services. Note that machine-store keys are accessible to local Administrators (or any non-Admin account granted Read access via Certificate Manager → *All Tasks → Manage Private Keys*); restrict NTFS permissions on your GAM config directory and `oauth2.txt` so unauthorized local users cannot read `oauth2.txt`.
- **Avoid duplicate subjects or orphaned keysets:** `dpop_backend_config` with a subject name matches by substring. If old or broken certificates with the same subject remain in the store, GAM may pick an old cert (or hit `Missing stored keyset` / `0x80090016`). Either delete stale certificates or reference the new certificate by exact `thumbprint:<HEX>`.

#### 1. Create and Verify the TPM-Backed Key

**Option A — PowerShell `New-SelfSignedCertificate`:**

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

Or for **Local Machine** (`Cert:\LocalMachine\My`, run **PowerShell as Administrator**):

```powershell
New-SelfSignedCertificate `
    -Subject "CN=GAM DPoP Signing Key" `
    -KeyAlgorithm ECDSA_nistP256 `
    -CertStoreLocation Cert:\LocalMachine\My `
    -KeyExportPolicy NonExportable `
    -Provider "Microsoft Platform Crypto Provider" `
    -NotAfter (Get-Date).AddYears(30)
```

**Option B — Fallback when `New-SelfSignedCertificate` fails with `0x80090017` (`NTE_PROV_TYPE_NOT_DEF`):**

Some TPM 2.0 / AMD fTPM / Pluton drivers reject PowerShell's `CertEnroll` ECC call with `0x80090017 NTE_PROV_TYPE_NOT_DEF`. Provision the TPM-backed P-256 key using `certreq -new` with `ProviderType = 0` instead (use `MachineKeySet = FALSE` for `CurrentUser`, or `MachineKeySet = TRUE` in an elevated PowerShell for `LocalMachine`):

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

**Verify the certificate AND healthy TPM key provider:**

```powershell
# Inspect certs in CurrentUser\My (or swap for Cert:\LocalMachine\My)
Get-ChildItem Cert:\CurrentUser\My |
    Where-Object Subject -like "*GAM DPoP Signing Key*" |
    Format-List Subject, Thumbprint, NotAfter, HasPrivateKey

# Confirm the key uses "Microsoft Platform Crypto Provider" without "Missing stored keyset"
certutil -user -store My "<THUMBPRINT>"
# (For LocalMachine, omit -user: certutil -store My "<THUMBPRINT>")
```

> [!WARNING]
> **Avoid `"Microsoft Software Key Storage Provider"` in production:** If a cert
> uses the Software KSP instead of `"Microsoft Platform Crypto Provider"`, the
> private key is stored in software rather than hardware. `gam check dpop` and
> `gam oauth info` inspect CNG provider `Impl Type` and will flag software keys
> with `WARN`.

#### 2. Configure GAM

For **Current User** (`Cert:\CurrentUser\My`):

```powershell
# Recommended: bind by exact thumbprint so extra certs never cause ambiguity
gam config dpop true dpop_backend windows_certstore dpop_backend_config "thumbprint:<THUMBPRINT>" save

# Or by unique subject substring:
# gam config dpop true dpop_backend windows_certstore dpop_backend_config "GAM DPoP Signing Key" save
```

For **Local Machine** (`Cert:\LocalMachine\My`, for SSH / Scheduled Tasks), append `,local_machine`:

```powershell
gam config dpop true dpop_backend windows_certstore dpop_backend_config "thumbprint:<THUMBPRINT>,local_machine" save
# Or: gam config dpop true dpop_backend windows_certstore dpop_backend_config "GAM DPoP Signing Key,local_machine" save
```

*(If a non-Administrator user runs GAM against a `LocalMachine` key, open `certlm.msc` → Personal → Certificates → right-click the cert → All Tasks → Manage Private Keys and grant that user Read permission.)*

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

### Linux — TPM 2.0 (Recommended for Linux Servers)

On Linux, GAM uses `tpm2-pytss` to sign directly with a persistent key inside the TPM 2.0 chip. No X.509 certificates or PKCS#11 middleware are required.

**Requirements & Real-World Hardware Notes:**
- **TPM 2.0 resource manager device (`/dev/tpmrm0`):** Verify with `ls -l /dev/tpmrm0`. If absent, enable TPM 2.0 / Intel PTT / AMD fTPM in BIOS/UEFI. TPM 1.2 hardware (`/dev/tpm0` only, no `/dev/tpmrm0`) is not supported — use a [YubiKey](#yubikey--piv-cross-platform) or [PKCS#11](#pkcs11--hsm--smart-card-cross-platform) token instead.
- **`tss` group access & services:** Add your GAM user to `tss` (`sudo usermod -aG tss $USER`) and log out/in (verify with `id`). Works over **SSH** and in **`cron`**. For `systemd` services, configure `SupplementaryGroups=tss` and do **not** enable `PrivateDevices=yes`.
- **Shared TPM handles & file permissions:** Any local user in `tss` (or `root`) can use persistent handles in `/dev/tpmrm0`, though they still need read access to `oauth2.txt`. Restrict `~/.gam` (`chmod 700 ~/.gam && chmod 600 ~/.gam/oauth2.txt ~/.gam/gam.cfg`).
- **Pre-existing TPM keys on real hardware (important):** Production laptops/servers often already have persistent keys at `0x81000001`, `0x81000002`, etc. (created by UEFI, Windows dual-boot/BitLocker, LUKS/`systemd-cryptenroll`, or `clevis`). The commands below inspect `tpm2_getcap handles-persistent` and pick the first unused handle automatically so you never collide with existing system keys.
- **Common real-world TPM provisioning errors:**
  - `0x14c` (`NV Index or persistent object already defined`): The handle you picked is already taken — use the `tpm2_getcap handles-persistent` lookup below to pick a free handle, or inspect existing handles with `tpm2_readpublic -c <handle>` (**never** evict `restricted|decrypt` Storage Root Keys used for disk encryption).
  - `TPM_RC_NV_SPACE` / `TPM_RC_OBJECT_MEMORY`: The TPM's persistent NVRAM slots are full (typically 3–7 slots on hardware TPMs). Inspect with `tpm2_getcap handles-persistent` and `tpm2_readpublic -c <handle>` to see if stale test keys (`0x810000xx`) can be freed (`tpm2_evictcontrol -C o -c <stale_handle>`).
  - Owner authorization failure (`TPM_RC_BAD_AUTH`) on dual-boot machines: Windows or another OS set an owner hierarchy password. You can supply `-P <owner_auth>` if known, or only run `tpm2_clear` if you are sure no BitLocker/LUKS keys reside in the TPM (**`tpm2_clear` permanently destroys all TPM-sealed keys**).
  - Dictionary-attack lockout (`TPM_RC_LOCKOUT`): Wait for the lockout cooldown or reset if authorized (`tpm2_dictionarylockout -c`).
  - **VMs (Proxmox / VMware / KVM):** Attach a vTPM device if needed; note that hypervisor admins can still access host-side vTPM state, and `swtpm` emulators are flagged as `WARN` (software TPM) by GAM.

#### 1. Install Packages, Inspect TPM, and Provision a Key

Debian/Ubuntu:
```bash
sudo apt install tpm2-tools libtss2-dev
```

Fedora/RHEL:
```bash
sudo dnf install tpm2-tss-devel tpm2-tools
```

Grant `/dev/tpmrm0` access if not already in `tss` (re-login afterwards so `id` shows `tss`):

```bash
ls -l /dev/tpmrm0
sudo usermod -aG tss "$USER"
```

Create an ECDSA P-256 signing key and persist it at the first unused handle found by `tpm2_getcap handles-persistent`:

```bash
# Find the first unused persistent handle (0x81000001..0x810000ff)
USED_HANDLES=$(tpm2_getcap handles-persistent)
TPM_HANDLE=""
for i in $(seq 1 255); do
  H=$(printf "0x810000%02x" "$i")
  if ! printf '%s\n' "$USED_HANDLES" | grep -Fqiw "$H"; then
    TPM_HANDLE="$H"
    break
  fi
done
echo "Using free handle: $TPM_HANDLE"

# Create a primary ECC key under the owner hierarchy
tpm2_createprimary -C o -g sha256 -G ecc256 -c primary.ctx

# Create an ECDSA P-256 signing child key with explicit scheme
# (Add -p "<key_password>" if you want per-key auth, then configure "$TPM_HANDLE,,<key_password>")
tpm2_create -C primary.ctx -g sha256 -G ecc:ecdsa-sha256 \
    -u key.pub -r key.priv \
    -a "fixedtpm|fixedparent|sensitivedataorigin|userwithauth|sign"

# Load and persist at $TPM_HANDLE
tpm2_load -C primary.ctx -u key.pub -r key.priv -c key.ctx
tpm2_evictcontrol -C o -c key.ctx "$TPM_HANDLE"

# Clean up temporary blobs
rm -f primary.ctx key.ctx key.pub key.priv

# Verify the key
tpm2_readpublic -c "$TPM_HANDLE"
```

Confirm `tpm2_readpublic` shows `type: ecc`, `curve-id: NIST p256`, `scheme: ecdsa`, and `sign` in `attributes`. If you open a new shell later, run `tpm2_getcap handles-persistent` and inspect candidates with `tpm2_readpublic -c <handle>`.

#### 2. Configure GAM

```bash
# Uses TPM_HANDLE from the commands above (or substitute the hex handle, e.g. 0x81000003)
gam config dpop true dpop_backend linux_tpm dpop_backend_config "$TPM_HANDLE" save
```

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

### YubiKey — PIV (Cross-Platform)

YubiKey PIV stores a non-exportable private key in the YubiKey's secure element. It works identically across Linux, macOS, and Windows and lets the bound key move physically between authorized workstations.

**Requirements & Real-World Hardware Notes:**
- **[YubiKey 5 series](https://www.yubico.com/products/yubikey-5-overview/)** (or PIV-capable YubiKey) and [`ykman`](https://docs.yubico.com/software/yubikey/tools/ykman/).
- **Check slot occupancy first (`ykman piv info`):** Generating a key into slot `9c` **permanently overwrites** any key/cert already in `9c`. If `9c` is already used (for SSH/GPG/code signing), pick a free PIV slot (`9a`, `9d`, `9e`) and specify it in `dpop_backend_config`.
- **Touch & PIN policy for automation:** Slot `9c` works well for automation, provided touch is not enforced (`--touch-policy=never`, the default when omitted). If you set `--touch-policy=always` or `--touch-policy=cached`, unattended cron/SSH jobs will time out waiting for a physical touch. **Never** test wrong PINs repeatedly — 3 failed attempts lock the PIV PIN (requiring PUK reset); change the default `123456` PIN and remember `dpop_backend_config` stores the PIN in `gam.cfg` (`chmod 600 ~/.gam/gam.cfg`).
- **Linux `pcscd` & GPG `scdaemon` conflicts:** On Linux, ensure `pcscd` is running (`sudo apt install pcscd && sudo systemctl enable --now pcscd`). On Linux/macOS, if `gpg-agent`/`scdaemon` holds an exclusive lock on the smart card reader, GAM cannot open the YubiKey — either add `disable-ccid` to `~/.gnupg/scdaemon.conf` (and restart `gpgconf --kill scdaemon`) or ensure other smartcard daemons aren't locking CCID.
- **Multiple YubiKeys:** Run `ykman list --serials` and include the YubiKey serial number in `dpop_backend_config` so GAM targets the exact device.

#### 1. Inspect PIV, Provision Key, and Verify

```bash
# List connected YubiKeys (note serial if using multiple keys) and check existing PIV slots
ykman list --serials
ykman piv info

# Change the default PIV PIN (123456) if not already changed
# ykman piv access change-pin

# Generate a P-256 key in slot 9c (use another free slot if 9c is already occupied)
ykman piv keys generate -a ECCP256 9c pubkey.pem

# Attach a 30-year self-signed certificate
ykman piv certificates generate -s "CN=GAM DPoP Signing" -d 10950 9c pubkey.pem
rm -f pubkey.pem

# Verify certificate and key appear in slot 9c
ykman piv info
```

#### 2. Configure GAM

The `dpop_backend_config` format is `serial,slot,pin` (blank `serial` = first YubiKey; blank `slot` = `9c`):

```bash
# Default serial and slot 9c, custom PIN:
gam config dpop true dpop_backend yubikey dpop_backend_config ",,<PIN>" save

# Or pinned to a specific YubiKey serial and slot:
# gam config dpop true dpop_backend yubikey dpop_backend_config "<SERIAL>,9c,<PIN>" save
```

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

### FIDO2 `previewSign` — Security Key (Experimental, Cross-Platform)

The `fido2_previewsign` backend uses the experimental FIDO2 / CTAP 2.3 [`previewSign`](https://github.com/yubicolabs/webauthn-sign-extension) extension to generate and use an on-chip ECDSA P-256 (`ES256`) key over USB HID without PIV management keys or X.509 certificates.

> [!WARNING]
> **`previewSign` is an experimental draft extension** and may change in future
> firmware or library releases. Tested on YubiKey 5 Series firmware **5.8+**.

**Requirements & Real-World Hardware Notes:**
- **Compatible CTAP 2.3 authenticator over USB HID:** Requires firmware with `previewSign` support (such as YubiKey 5 Series / Yubico Security Key **5.8+**; `ykman info`). Bluetooth and NFC are not supported for CTAP HID.
- **Unattended by default:** Key creation requires **one physical touch**, after which DPoP signatures run silently without prompts (`require_up=False` default; pass `require_up=True` or `require_uv=True` if you want touch or PIN/biometric per sign).
- **Provisioning Python dependency:** Because GAM does not provision keys, run the one-time key creation command using Python with `dpop-signer-fido2-previewsign` installed (`pip install dpop-signer-fido2-previewsign`), saving the public/wrapped credential descriptor into `dpop_backend_config` (no private key leaves the YubiKey). Once configured, standard GAM builds run `gam check dpop` and `gam` natively.
- **Windows WebAuthn caveat:** Windows may intercept direct FIDO2 USB HID access in some sessions (if HID fails with permission errors, run from an elevated shell or check Windows WebAuthn restrictions).

#### 1. Create the Key (One-Time Touch) & 2. Configure GAM

**Option A — Store directly in `gam.cfg` (`dpop_backend_config`):**

```bash
# Plug in your YubiKey 5.8+ and touch it once when prompted:
CRED=$(python3 -c 'import json; from dpop_signer_fido2_previewsign import generate_signing_credential; print(json.dumps(generate_signing_credential().to_dict(), separators=(",", ":")))')
gam config dpop true dpop_backend fido2_previewsign dpop_backend_config "$CRED" save
```

**Option B — Or save to a JSON file in `~/.gam`:**

```bash
python3 -c 'import json, os; from dpop_signer_fido2_previewsign import generate_signing_credential; open(os.path.expanduser("~/.gam/fido2_dpop_credential.json"), "w").write(json.dumps(generate_signing_credential().to_dict(), indent=2))'
chmod 600 ~/.gam/fido2_dpop_credential.json
gam config dpop true dpop_backend fido2_previewsign dpop_backend_config "fido2_dpop_credential.json" save
```

*(If your YubiKey uses a FIDO2 PIN and `require_uv=True`, append `,<PIN>` after the inline JSON or filename.)*

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

### PKCS#11 — HSM / Smart Card (Cross-Platform)

The `pkcs11` backend works with PKCS#11 (Cryptoki) hardware security modules and smart cards across Linux, macOS, and Windows using an [RFC 7512](https://www.rfc-editor.org/rfc/rfc7512) `pkcs11:` URI. Supports `ES256` (P-256), `ES384` (P-384), and `RS256` (RSA).

**Real-World Hardware Notes:**
- **Discover exact token/key attributes first:** Hardware tokens vary in how they populate `token`, `object` (`CKA_LABEL`), `id` (`CKA_ID`), and `slot-id`. Always inspect the initialized token with `pkcs11-tool` (from OpenSC) or your vendor CLI before configuring GAM:
  ```bash
  pkcs11-tool --module /path/to/libpkcs11.so --list-slots
  pkcs11-tool --module /path/to/libpkcs11.so --login --list-objects
  ```
  - Percent-encode special characters in URI path fields (for example `id=%01` for `CKA_ID` `01`, `#` → `%23`, space → `%20`).
  - Verify your token key is an unrestricted EC P-256/P-384 or RSA signing key (`CKA_SIGN = true`).
- **Protect your PIN & avoid lockouts:** Many HSMs/smart cards permanently lock the User PIN after 3–5 bad attempts. Test your URI/PIN with `pkcs11-tool --login --test` first, and prefer `pin-source=file:/path/to/pin` (`chmod 600`) over storing `pin-value=` directly in `gam.cfg`.
- **Smartcard reader locks:** On USB smart cards/HSMs, ensure `pcscd` is running (Linux) and conflicting daemons such as `gpg-agent`/`scdaemon` aren't holding exclusive CCID access.
- **Note on SoftHSM2:** Software PKCS#11 tokens such as SoftHSM2 work for testing, but GAM detects `SoftHSM` and prints `WARN`.

#### 1. Verify Key on Token (Example with OpenSC `pkcs11-tool`)

If you haven't created a key on the token yet, initialize/generate one using your HSM tools (or `pkcs11-tool --keypairgen --key-type EC:prime256v1 --id 01 --label dpop-key`), then verify:

```bash
pkcs11-tool --module /path/to/libpkcs11.so --login --list-objects
```

#### 2. Configure GAM

RFC 7512 `pkcs11:` URI attributes:
- **Path (`;`):** `token=`, `object=`, `id=`, `slot-id=`, `serial=`
- **Query (`&`):** `module-path=` (full path to `.so`/`.dylib`/`.dll`), `module-name=` (`p11-kit`), `pin-source=` (`file:/path/to/pin`), `pin-value=`

```bash
# HSM / PKCS#11 module with separate PIN file (recommended):
gam config dpop true dpop_backend pkcs11 \
    dpop_backend_config "pkcs11:token=hsm-slot;object=dpop-key;id=%01?module-path=/path/to/libpkcs11.so&pin-source=file:/home/$USER/.gam/pkcs11-pin.txt" save

# OpenSC smart card resolved via p11-kit module-name:
# gam config dpop true dpop_backend pkcs11 \
#     dpop_backend_config "pkcs11:token=MyToken;object=dpop-key?module-name=opensc-pkcs11&pin-value=<PIN>" save
```

*(If omitting `module-path=`/`module-name=`, set the `PKCS11_MODULE` environment variable.)*

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

### Software Key (Testing Only)

The `software` backend stores an unencrypted EC private key PEM file on disk. It binds `oauth2.txt` to that file, but an attacker with filesystem access can copy both files — **do not use for production**. GAM flags software keys with `WARN`.

#### 1. Generate a PEM Key

```bash
openssl ecparam -genkey -name prime256v1 -noout -out ~/.gam/dpop_key.pem
chmod 600 ~/.gam/dpop_key.pem
```

#### 2. Configure GAM

```bash
# Relative paths resolve inside your GAM config directory (~/.gam/ by default)
gam config dpop true dpop_backend software dpop_backend_config "dpop_key.pem" save
```

Proceed to **[Stage 2: Confirm Local Signing with `gam check dpop`](#stage-2-confirm-local-signing-with-gam-check-dpop)**.

---

## Stage 2: Confirm Local Signing with `gam check dpop`

Before recreating your OAuth token, run `gam check dpop`:

```bash
gam check dpop
```

When configured with a hardware-backed key, output looks like:

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

What each line checks:

| Check | `OK` | `WARN` | `ERROR` |
|-------|------|--------|---------|
| `Signer Initialization` | Backend loaded & key found | — | Missing key, wrong config/PIN, locked card, or permission error (exits non-zero) |
| `Key Storage` | Key resides in hardware (`Secure Enclave`, `Microsoft Platform Crypto Provider`, `TPM 2.0 (...)`, `YubiKey PIV`, `FIDO2 previewSign`, `PKCS#11 (...)`) | Key is software-backed (`Software TPM`, `Microsoft Software Key Storage Provider`, non-token macOS Keychain, `SoftHSM`, PEM file) or unverified (`ecp`) | — |
| `Public JWK & Thumbprint` | Valid public key, no private fields exposed, valid thumbprint | — | Invalid/corrupt JWK |
| `Local Test Signature` | Payload signed & signature verified against `public_jwk` | — | Signing failed or verification failed |
| `DPoP Proof & Signature Verification` | RFC 9449 `dpop+jwt` proof created & cryptographically verified | — | Proof creation or verification failed |

If you see `WARN` on `Key Storage` and `DPoP Local Signing`, your active key is software-backed — replace it with a hardware key in Stage 1 before proceeding to Stage 3.

Common `Signer Initialization` errors:

| Error | Cause / Fix |
|-------|-------------|
| `DPoP macOS Secure Enclave error` | Run `sc_auth list-ctk-identities` as the same macOS user running GAM and verify `dpop_backend_config` matches the label. |
| `DPoP Windows Certificate Store error` | Verify the cert exists (`Cert:\CurrentUser\My` or `Cert:\LocalMachine\My` with `,local_machine`), check `certutil` for `Missing stored keyset`, and use `thumbprint:<HEX>` if multiple certs match. |
| `DPoP Linux TPM error` | Check `ls -l /dev/tpmrm0`, `id` (`tss` group), `tpm2_getcap handles-persistent`, and `tpm2_readpublic -c <handle>`. |
| `DPoP YubiKey error` | Ensure the YubiKey is plugged in, `pcscd` is running / `scdaemon` isn't locking it, and `serial,slot,pin` is valid. |
| `DPoP FIDO2 previewSign error` | Ensure a FIDO2 key with firmware 5.8+ (`previewSign`) is plugged in over USB HID and `dpop_backend_config` holds valid `to_dict()` JSON (or JSON file path). |
| `DPoP PKCS#11 error` | Verify `module-path=`/`module-name=`, `token=`/`object=`/`id=`, and `pin-source=`/`pin-value=` with `pkcs11-tool`. |
| `DPoP software key error` | Verify the PEM file path and permissions (`chmod 600`). |

> [!NOTE]
> `gam check dpop` **only tests local DPoP signing** — it does not inspect
> `oauth2.txt` or contact Google's OAuth servers. Once `gam check dpop` reports
> `DPoP Local Signing  OK`, proceed to Stage 3.

---

## Stage 3: Recreate OAuth and Confirm with `gam oauth info`

### 1. Revoke Existing Bearer Credentials and Re-Authorize

Existing `oauth2.txt` refresh tokens created without DPoP remain bearer tokens until replaced. Revoke any existing token and create a new DPoP-bound token:

```bash
# Revoke existing unbound credentials (if present)
gam oauth revoke

# Authorize and bind oauth2.txt to your configured DPoP key
gam oauth create
```

This opens a browser (or prints an authorization URL) for Google authentication. During token exchange, GAM sends a DPoP proof signed by your configured key so Google binds the new refresh token in `oauth2.txt` to your key's JWK thumbprint.

> [!CAUTION]
> After creating DPoP-bound credentials, the refresh token **requires** that
> exact private key for every refresh. If the hardware key is lost, wiped, or
> replaced, you must re-authorize with `gam oauth revoke` and `gam oauth create`.

### 2. Confirm End-to-End Binding & Enforcement with `gam oauth info`

Run `gam oauth info`:

```bash
gam oauth info
```

Alongside `Client ID`, `Scopes`, `Google Workspace Admin`, and `Expires`, GAM verifies key backing, compares your configured signer against `oauth2.txt`, and executes live token-endpoint enforcement checks:

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

What each check verifies:

| Check | What It Verifies | Expected Result |
|-------|------------------|-----------------|
| `Key Storage` | Active key lives in hardware vs. software | `OK` for hardware (`WARN` if software-backed) |
| `Credential Binding` | Signer thumbprint matches `dpop_thumbprint` in `oauth2.txt` | `OK` (`ERROR` if missing or mismatched) |
| `Refresh With DPoP (<backend>)` | Configured key refreshes the token at Google's endpoint | `OK` |
| `Reject Refresh Without DPoP` | Google rejects an unbound bearer refresh attempt | `OK` (`ERROR` if accepted without proof) |
| `Reject Refresh With Wrong Key` | Google rejects a proof signed by an unrelated `ephemeral` key | `OK` (`ERROR` if wrong key accepted) |
| `DPoP Key Binding` | Overall status across metadata, hardware backing, and server enforcement | `OK` (`WARN` if software key; `ERROR` + `Fix:` instructions on failure) |

If `dpop = false` in `gam.cfg` while `oauth2.txt` has a `dpop_thumbprint`, `gam oauth info` prints `ERROR` with `Fix:` guidance; if `dpop = false` and `oauth2.txt` is unbound, it prints `WARN` recommending hardware DPoP setup.

### Optional: Manual Refresh Tests

You can also test Google's enforcement manually with `gam oauth refresh`:

- **Normal refresh:** `gam oauth refresh` succeeds.
- **Without DPoP:** `gam config dpop false oauth refresh` fails (`DPoP proof required`).
- **Wrong key:** GAM validates your signer's thumbprint locally against `oauth2.txt` before calling Google, so pointing `dpop_backend_config` at another key fails immediately in GAM. Use `gam oauth info` (`Reject Refresh With Wrong Key`) to verify Google's server-side wrong-key rejection.

---

## Configuration Reference

All DPoP settings are stored in `gam.cfg`:

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `dpop` | `true` / `false` | `false` | Enable or disable DPoP |
| `dpop_backend` | `software`, `macos_secureenclave`, `windows_certstore`, `linux_tpm`, `yubikey`, `fido2_previewsign`, `pkcs11`, `ecp`, `ephemeral` | `software` | Which signer backend to use |
| `dpop_backend_config` | *(varies by backend)* | *(empty)* | Backend-specific configuration |

### `dpop_backend_config` Format by Backend

| Backend | Format | Example |
|---------|--------|---------|
| `software` | Path to PEM private key file | `dpop_key.pem` |
| `macos_secureenclave` | `label[,application_tag]` | `gam-dpop` |
| `windows_certstore` | `<subject\|thumbprint:HEX>[,current_user\|local_machine]` | `thumbprint:A1B2C3...` |
| `linux_tpm` | `handle[,tcti[,auth]]` | `0x81000003` |
| `yubikey` | `serial,slot,pin` | `,,mypin` |
| `fido2_previewsign` | `<inline_json\|json_file_path>[,pin]` | `{"credential_id":...}` |
| `pkcs11` | RFC 7512 `pkcs11:` URI | `pkcs11:token=hsm-slot;object=dpop-key?module-path=/path/to/libpkcs11.so` |

---

## FAQ

**Q: What happens if my TPM/YubiKey/Mac dies?**

You'll need to provision a new key (Stage 1), verify local signing with `gam check dpop` (Stage 2), and re-authorize with `gam oauth revoke` then `gam oauth create` (Stage 3). The old refresh token cannot be used without the lost private key.

**Q: Can I use the same DPoP key for multiple GAM instances?**

Only if they share the same hardware. For example, multiple GAM configs on the same Mac can share one Secure Enclave key label, or multiple hosts can share a network PKCS#11 HSM / portable YubiKey. You cannot share a motherboard TPM key across different machines.

**Q: Does DPoP affect GAM performance?**

No. GAM only generates a DPoP proof when refreshing its OAuth access token, which happens at most once per hour. Normal Google API calls use the cached access token with zero overhead. A single hardware ECDSA signature takes ~10–75 ms.

**Q: Can I switch from software to hardware backend later?**

Yes, but you must re-authorize `oauth2.txt`. Provision your hardware key and update `gam.cfg` (Stage 1), confirm `OK` hardware storage with `gam check dpop` (Stage 2), then run `gam oauth revoke`, `gam oauth create`, and `gam oauth info` (Stage 3).

**Q: What if I disable DPoP after creating bound tokens?**

The existing refresh token will stop working (Google rejects refresh requests without matching DPoP proofs). Run `gam oauth revoke`, set `gam config dpop false save`, then run `gam oauth create` to obtain an unbound bearer token.

**Q: Does the self-signed certificate matter (Windows/YubiKey/macOS)?**

No. DPoP signs using the raw private key, not the X.509 certificate. The certificate is only the container used to store and locate the key; certificate expiry does not break DPoP signing.
