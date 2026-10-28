# Intro to DPoP for GAM

> [!CAUTION]
> **Alpha Feature** — GAM DPoP support is currently in alpha and requires a
> special pre-release build. It is not ready for production use. APIs,
> configuration options, and behavior may change without notice.
>
> Do not enable DPoP on production GAM installations. Use a separate test
> environment with non-critical credentials.
>
> The latest alpha DPoP build is at:
> [pre-release](https://github.com/GAM-team/GAM/releases/tag/20261028.113254)

## What is DPoP?

**DPoP** (Demonstrating Proof-of-Possession, [RFC 9449](https://datatracker.ietf.org/doc/html/rfc9449)) is an OAuth 2.0 extension that binds OAuth tokens to a specific cryptographic key. Every time GAM uses a refresh token, it must also present a signed proof that it possesses the private key the token was bound to.

### The Problem DPoP Solves

Without DPoP, GAM's OAuth tokens are **bearer tokens** — anyone who has a copy can use them. A stolen `oauth2.txt` file gives an attacker full Google Workspace admin access until the token is revoked. Possible attack vectors include:

- Malware exfiltrating files from the GAM config directory
- Backup systems storing unencrypted copies of `oauth2.txt`
- Insider access to the machine's filesystem
- Accidental exposure in logs, screenshots, or support tickets

### How DPoP Fixes This

With DPoP enabled, GAM's refresh token is **bound to a private key** during the initial OAuth authorization flow. From that point on:

1. Every token refresh request must include a **DPoP proof** — a signed JWT proving possession of the private key.
2. Google's authorization server verifies the proof's signature against the public key the token was bound to.
3. A stolen `oauth2.txt` is cannot be refreshed without the corresponding private key.

If the private key is stored in hardware (TPM, Secure Enclave, YubiKey), it **cannot be extracted** — even with root/admin access to the machine. The token becomes bound to a physical device.

```
Without DPoP:       stolen oauth2.txt = full admin access

With DPoP:          stolen oauth2.txt = worthless
                    (attacker also needs the private key)

With hardware DPoP: stolen oauth2.txt = worthless
                    (attacker must also *physically steal hardware)
```

### What DPoP Does and Does Not Protect

Google's implementation of DPoP protects the **refresh token** — the long-lived credential stored in `oauth2.txt` that GAM uses to obtain short-lived access tokens. The DPoP proof is required when GAM exchanges the refresh token for a new access token. Usually this is needed once an hour.

**Google Access tokens themselves are not DPoP-bound.** Once GAM obtains an access token, it uses it as a normal bearer token for Google API calls. However, access tokens are short-lived (60 minutes or less), so the window of exposure is very limited compared to a refresh token that may be valid for months or years.

## Choosing a Backend

GAM supports multiple DPoP signer backends where the private key can be stored. Choose based on your operating system and security requirements:

| Backend | Platform | Key Storage | Hardware-Backed | Best For |
|---------|----------|-------------|-----------------|----------|
| [`macos_secureenclave`](#macos--secure-enclave-recommended-for-apple-silicon-macs) | macOS (Apple Silicon) | Secure Enclave | Yes | Mac admins with Apple Silicon |
| [`windows_tpm`](#windows--cngtpm-recommended-for-windows-with-tpm) | Windows | TPM via CNG | Yes (with TPM) | Windows admins with TPM |
| [`linux_tpm`](#linux--tpm-20-recommended-for-linux-servers) | Linux | TPM 2.0 | Yes | Linux servers with TPM |
| [`yubikey`](#yubikey--piv-cross-platform) | Any | YubiKey PIV | Yes | Cross-platform, portable key |
| [`software`](#software-key-testing-only) | Any | PEM file on disk | No | Testing or low-security environments |

> [!IMPORTANT]
> Hardware-backed keys provide the strongest security. The private key never
> leaves the hardware and cannot be extracted, even by an attacker with
> root/admin access.

> [!WARNING]
> The `software` backend stores the private key as a PEM file on disk. While
> it still prevents stolen `oauth2.txt` from being used on a different machine,
> an attacker with filesystem access to the same machine could copy both files.
> Use a hardware backend for production deployments.

---

## Setup Guides

### macOS — Secure Enclave (Recommended for Apple Silicon Macs)

The Secure Enclave is a dedicated security coprocessor in Apple Silicon Macs (M1 and later). Keys generated in the Secure Enclave cannot be exported or read — signing operations happen inside the chip.

**Requirements:**
- macOS 15 (Sequoia) or later
- Apple Silicon (M1/M2/M3/M4) Mac

#### Step 1: Create the Secure Enclave Key

```bash
sc_auth create-ctk-identity -l gam-dpop -k p-256-ne
```

This creates a P-256 key in the Secure Enclave with the label `gam-dpop`. The `-k p-256-ne` flag means "P-256, non-exportable."

To optionally require Touch ID for each signing operation (every `gam` command), add `-t bio`:

```bash
sc_auth create-ctk-identity -l gam-dpop -k p-256-ne -t bio
```

#### Step 2: Verify the Key Exists

```bash
sc_auth list-ctk-identities
```

You should see an entry with your label.

#### Step 3: Configure GAM

```bash
gam config dpop true dpop_backend macos_secureenclave dpop_backend_config "gam-dpop" save
```

> [!NOTE]
> `sc_auth create-ctk-identity` also generates a self-signed certificate with
> a 1-year validity. This does not matter — DPoP uses the raw private key,
> not the certificate. The key remains usable regardless of certificate expiry.

---

### Windows — CNG/TPM (Recommended for Windows with TPM)

On Windows, GAM uses CNG (Cryptography Next Generation) to access keys in the Windows certificate store. When a TPM is present and the correct provider is used, the private key is stored in the TPM.

**Requirements:**
- Windows 10/11 or Windows Server 2019+
- TPM 2.0 (for hardware-backed keys). Windows 11 requires a TPM 2.0 device.

#### Step 1: Generate a TPM-Backed Key

Open **PowerShell as Administrator** and run:

```powershell
New-SelfSignedCertificate `
    -Subject "CN=GAM DPoP Signing Key" `
    -KeyAlgorithm ECDSA_nistP256 `
    -CertStoreLocation Cert:\CurrentUser\My `
    -KeyExportPolicy NonExportable `
    -Provider "Microsoft Platform Crypto Provider" `
    -NotAfter (Get-Date).AddYears(30)
```

Key points:
- `"Microsoft Platform Crypto Provider"` routes the key to the TPM.
- `-KeyExportPolicy NonExportable` prevents extraction.
- The 30-year validity prevents certificate expiry from being an issue.

> [!TIP]
> If your machine does not have a TPM, you can use `"Microsoft Software Key
> Storage Provider"` instead. The key will be software-backed (not
> hardware-backed) but still non-exportable and protected by Windows DPAPI.

#### Step 2: Verify the Key

```powershell
Get-ChildItem Cert:\CurrentUser\My |
    Where-Object Subject -eq "CN=GAM DPoP Signing Key" |
    Format-List Subject, Thumbprint, NotAfter, HasPrivateKey
```

#### Step 3: Configure GAM

Configure by subject name (substring match):

```bash
gam config dpop true dpop_backend windows_tpm dpop_backend_config "GAM DPoP Signing Key" save
```

Or by certificate thumbprint (exact match):

```bash
gam config dpop true dpop_backend windows_tpm dpop_backend_config "thumbprint:A1B2C3D4E5..." save
```

---

### Linux — TPM 2.0 (Recommended for Linux Servers)

On Linux, GAM uses `tpm2-pytss` to sign directly with a persistent key in the TPM. No certificates or PKCS#11 middleware needed.

**Requirements:**
- Linux with TPM 2.0 (most modern servers and laptops)
- `tpm2-tools` and `libtss2-dev` system packages

#### Step 1: Install System Packages

Debian/Ubuntu:
```bash
sudo apt install tpm2-tools libtss2-dev
```

Fedora/RHEL:
```bash
sudo dnf install tpm2-tss-devel tpm2-tools
```

#### Step 2: Create and Persist a Signing Key

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

# Clean up temporary files
rm primary.ctx key.ctx key.pub key.priv
```

> [!IMPORTANT]
> Use `-G ecc:ecdsa-sha256` (not just `-G ecc256`) so the signing scheme is
> baked into the key. This ensures compatibility with all versions of the
> signer.

#### Step 3: Verify the Key

```bash
tpm2_readpublic -c 0x81000001
```

Confirm the output shows `type: ecc`, `curve-id: NIST p256`, and `scheme: ecdsa`.

#### Step 4: Configure GAM

```bash
gam config dpop true dpop_backend linux_tpm dpop_backend_config "0x81000001" save
```

#### Permissions

Access to `/dev/tpmrm0` typically requires membership in the `tss` group:

```bash
sudo usermod -aG tss $USER
# Log out and back in for the group change to take effect
```

> [!TIP]
> VMs running on VMWare, Proxmox, etc can create vTPM (virtual TPM)
> devices for guest VMs. These vTPMs protect the private key even if
> an attacker has root access to the guest VM but anyone with access
> to the host VM server can access the vTPM private keys directly.

---

### YubiKey — PIV (Cross-Platform)

YubiKey PIV stores a private key in the YubiKey's secure element. The key is generated on the YubiKey and never leaves it. Works on any OS where GAM runs.

**Requirements:**
- YubiKey 5 series or newer (with PIV support)
- [`ykman`](https://docs.yubico.com/software/yubikey/tools/ykman/) (YubiKey Manager) installed

#### Step 1: Generate a Key on the YubiKey

```bash
# Generate a P-256 key in slot 9c (Digital Signature)
ykman piv keys generate -a ECCP256 9c pubkey.pem

# Create a self-signed certificate (30-year validity)
ykman piv certificates generate \
    -s "CN=GAM DPoP Signing" \
    -d 10950 \
    9c pubkey.pem

# Clean up (public key is stored on the YubiKey)
rm pubkey.pem
```

Slot `9c` (Digital Signature) is recommended — it does not require touch confirmation after PIN entry.

#### Step 2: Verify

```bash
ykman piv info
```

#### Step 3: Configure GAM

```bash
# Default slot 9c, no serial filter (uses first YubiKey found)
gam config dpop true dpop_backend yubikey dpop_backend_config ",,123456" save
```

The `dpop_backend_config` format is: `serial,slot,pin`

- `serial` — YubiKey serial number (optional, leave blank for first YubiKey found)
- `slot` — PIV slot (default: `9c`)
- `pin` — PIV PIN (default PIV PIN is `123456` — change it!)

Examples:

```bash
# Explicit serial, default slot, custom PIN
gam config dpop_backend_config "12345678,,mypin" save

# Default serial, slot 9a, custom PIN
gam config dpop_backend_config ",9a,mypin" save
```

> [!TIP]
> Change the default PIV PIN: `ykman piv access change-pin`
> Even if the Yubikey is lost the attacker would need the PIN
> which is stored in the GAM config making the theft harder.

---

### Software Key (Testing Only)

The software backend uses a PEM private key file on disk. This provides token binding but **not** hardware protection — an attacker who can read the filesystem can copy the key.

#### Step 1: Generate a PEM Key

```bash
openssl ecparam -genkey -name prime256v1 -noout -out ~/.gam/dpop_key.pem
chmod 600 ~/.gam/dpop_key.pem
```

#### Step 2: Configure GAM

```bash
gam config dpop true dpop_backend software dpop_backend_config "dpop_key.pem" save
```

The path is relative to your GAM config directory (`~/.gam/` by default). You can also use an absolute path.

---

## Testing DPoP Before OAuth

Always verify your DPoP configuration is working before creating OAuth credentials. The `gam check dpop` command constructs a signer from your configuration, performs a test signature, and verifies everything works end-to-end — without touching any Google APIs.

### Step 1: Test Your Configuration

```bash
gam check dpop
```

Successful output looks like:

```
DPoP Configuration
  dpop: True
  dpop_backend: macos_secureenclave
  dpop_backend_config: gam-dpop

Constructing DPoP signer...
Signer created successfully.

Signer Details
  Backend: macos_secureenclave
  Algorithm: ES256
  Key ID: (auto)
  JWK Thumbprint: xK9m2q...

Performing test signature...
Signature succeeded.

Signature Details
  Signature length: 64 bytes
  Signature (base64url): m3Fz0x...
  Signing time: 12.3 ms

DPoP configuration is valid and working.
```

If there's a problem, GAM will print a clear error and exit with a non-zero exit code. Common issues:

| Error | Cause | Fix |
|-------|-------|-----|
| `DPoP software backend requires dpop_backend_config set to the path of a PEM private key file` | No key file configured | Set `dpop_backend_config` to a PEM file path |
| `DPoP software key file not found` | PEM file doesn't exist at the configured path | Check the path and generate the key |
| `DPoP macOS Secure Enclave error` | Key not found in Secure Enclave | Run `sc_auth list-ctk-identities` to check |
| `DPoP Windows CNG/TPM error` | Certificate not found in Windows cert store | Check with `Get-ChildItem Cert:\CurrentUser\My` |
| `DPoP Linux TPM error` | Can't connect to TPM or key not found | Check `/dev/tpmrm0` permissions and `tpm2_readpublic -c 0x81000001` |
| `DPoP YubiKey error` | YubiKey not plugged in or wrong PIN | Plug in YubiKey and verify PIN |

### Step 2: Create DPoP-Bound OAuth Credentials

Once `gam check dpop` passes, create your OAuth credentials. If you already have existing OAuth credentials, revoke them first:

```bash
gam oauth revoke
```

Then create new DPoP-bound credentials. The DPoP key will be bound to the tokens during the authorization flow:

```bash
gam oauth create
```

This opens a browser for Google authentication. The resulting refresh token in `oauth2.txt` will be bound to your DPoP key.

> [!CAUTION]
> After creating DPoP-bound credentials, the refresh token **requires** the
> DPoP key for every use. If you lose the key (e.g., hardware failure, key
> deletion), you must re-authorize with `gam oauth create`.

---

## Confirming DPoP Is Working

After creating DPoP-bound credentials, verify the binding is enforced with these three tests:

### Test 1: Normal Refresh (Should Succeed)

With DPoP enabled and your key available, a normal token refresh should work:

```bash
gam oauth refresh
```

Expected: Succeeds and prints the token info.

### Test 2: Refresh Without DPoP (Should Fail)

Temporarily disable DPoP and try to refresh. The server should reject the request because the token expects a DPoP proof:

```bash
gam config dpop false save
gam oauth refresh
```

Expected: **Fails** with an error from Google's token endpoint. This confirms the token is bound — it can't be used without DPoP.

```bash
# Re-enable DPoP
gam config dpop true save
```

### Test 3: Refresh With Wrong Key (Should Fail)

Create a temporary software key and try to use it instead of your real key. The server should reject the proof because the thumbprint doesn't match:

```bash
# Generate a throwaway key
openssl ecparam -genkey -name prime256v1 -noout -out /tmp/fake_dpop_key.pem

# Point GAM at the fake key
gam config dpop_backend software dpop_backend_config /tmp/fake_dpop_key.pem save
gam oauth refresh
```

Expected: **Fails** because the DPoP proof is signed with a different key than the one the token was bound to.

```bash
# Restore your real configuration
gam config dpop_backend macos_secureenclave dpop_backend_config "gam-dpop" save

# Clean up
rm /tmp/fake_dpop_key.pem
```

### Summary

| Test | DPoP Enabled | Key | Expected Result |
|------|-------------|-----|-----------------|
| Normal refresh | Yes | Correct key | Success |
| Without DPoP | No | N/A | **Fail** — token requires DPoP proof |
| Wrong key | Yes | Different key | **Fail** — thumbprint mismatch |

If all three tests produce the expected results, your DPoP setup is working correctly and your credentials are hardware-bound.

---

## Configuration Reference

All DPoP settings are stored in `gam.cfg`:

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `dpop` | `true` / `false` | `false` | Enable or disable DPoP |
| `dpop_backend` | `software`, `macos_secureenclave`, `windows_tpm`, `linux_tpm`, `yubikey`, `ecp` | `software` | Which signer backend to use |
| `dpop_backend_config` | *(varies by backend)* | *(empty)* | Backend-specific configuration |

### `dpop_backend_config` Format by Backend

| Backend | Format | Example |
|---------|--------|---------|
| `software` | Path to PEM private key file | `dpop_key.pem` |
| `macos_secureenclave` | `label[,application_tag]` | `gam-dpop` |
| `windows_tpm` | Subject CN substring, or `thumbprint:HEX` | `GAM DPoP Signing Key` |
| `linux_tpm` | `handle[,tcti[,auth]]` | `0x81000001` |
| `yubikey` | `serial,slot,pin` | `,,123456` |

---

## FAQ

**Q: What happens if my TPM/YubiKey/Mac dies?**

You'll need to re-authorize GAM with `gam oauth revoke` then `gam oauth create` using a new key on replacement hardware. The old refresh token becomes permanently unusable.

**Q: Can I use the same DPoP key for multiple GAM instances?**

Only if they share the same hardware. For example, multiple GAM configs on the same Mac can all use the same Secure Enclave key label. But you cannot share a TPM key across different machines.

**Q: Does DPoP affect GAM performance?**

No. GAM only generates a DPoP proof when refreshing its OAuth access token, which happens at most once per hour. Individual Google API calls are unaffected. A single ECDSA signature takes 10-50ms on hardware backends and sub-millisecond on software.

**Q: Can I switch from software to hardware backend later?**

Yes, but you must re-authorize. Run `gam config dpop_backend <new_backend> dpop_backend_config <config> save`, then `gam oauth revoke` and `gam oauth create` to create new tokens bound to the new key.

**Q: What if I disable DPoP after creating bound tokens?**

The existing refresh token will stop working (Google will reject requests without DPoP proofs). You would need to `gam oauth revoke`, disable DPoP, then `gam oauth create` to get an unbound token.

**Q: Does the self-signed certificate matter (Windows/YubiKey)?**

No. DPoP uses the raw private key for signing, not the certificate. The certificate is just the container Windows and YubiKey use to store and find keys. Certificate expiry does not affect DPoP functionality.
