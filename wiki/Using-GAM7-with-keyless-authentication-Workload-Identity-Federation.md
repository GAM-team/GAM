# Using GAM7 with Keyless Authentication - Workload Identity Federation

**Important**: This method is designed for running GAM7 **outside** of Google Cloud (on-premises, other cloud providers, CI/CD systems). If you're running GAM7 **inside** Google Cloud, use [attached service accounts on Google Compute Engine](Running-GAM7-securely-on-a-Google-Compute-Engine) instead, which provides the same keyless benefits with simpler configuration.

This guide explains how to configure GAM7 to use Google Cloud's Workload Identity Federation for keyless authentication. **This is Google's officially recommended authentication method** for enhanced security and simplified credential management.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup Steps](#setup-steps)
  - [1. Enable Required APIs](#1-enable-required-apis)
  - [2. Create Workload Identity Pool](#2-create-workload-identity-pool)
  - [3. Create or Use Existing Service Account](#3-create-or-use-existing-service-account)
  - [4. Grant Required Permissions](#4-grant-required-permissions)
- [AWS Configuration](#aws-configuration)
  - [1. Create Workload Identity Provider for AWS](#1-create-workload-identity-provider-for-aws)
  - [2. Allow AWS Identity to Impersonate Service Account](#2-allow-aws-identity-to-impersonate-service-account)
  - [3. Create Credential Configuration File](#3-create-credential-configuration-file)
  - [4. Configure GAM7 Environment for AWS](#4-configure-gam7-environment-for-aws)
  - [5. Initialize GAM7](#5-initialize-gam7)
- [GitHub Actions Configuration](#github-actions-configuration)
  - [1. Create Workload Identity Provider for GitHub Actions](#1-create-workload-identity-provider-for-github-actions)
  - [2. Allow GitHub Actions to Impersonate Service Account](#2-allow-github-actions-to-impersonate-service-account)
  - [3. GitHub Actions Workflow Configuration](#3-github-actions-workflow-configuration)
- [Clean Up](#clean-up)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)
- [Benefits](#benefits)
- [References](#references)

## Overview

Workload Identity Federation allows GAM7 to authenticate to Google Cloud services without storing long-lived service account keys. Instead, it uses short-lived tokens from external identity providers like AWS, Azure, or GitHub Actions, eliminating the security risks associated with managing static credentials.

## Prerequisites

- GAM7 [installed and configured](https://github.com/GAM-team/GAM/wiki/How-to-Install-GAM7)
  - Run `gam config` to generate the `gam.cfg` file
  - Run `gam create/use project` to generate the `oauth2service.json` file
  - Optionally enable [DASA](https://github.com/GAM-team/GAM/wiki/Using-GAM7-with-a-delegated-admin-service-account) `gam config enable_dasa true admin_email admin@domain.com customer_id domain domain.com save`
- Google Cloud CLI (gcloud) installed and configured
  - [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
  - Run `gcloud auth login` to authenticate
  - Run `gcloud config set project PROJECT_ID` to set your project
  - **Alternative**: Use the [Google Cloud Console](https://console.cloud.google.com) web interface to perform the same operations
- Google Cloud project with appropriate APIs enabled
- External identity provider (AWS, Azure, GitHub Actions, etc.)
- Appropriate permissions to create Workload Identity Pools and manage IAM

## Setup Steps

### 1. Enable Required APIs

```bash
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
```

### 2. Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create POOL_ID \
    --location="global" \
    --description="Pool for GAM authentication"
```

### 3. Create or Use Existing Service Account

You can either create a new service account or reuse an existing one that has the necessary permissions.

#### Option A: Create New Service Account
```bash
gcloud iam service-accounts create SERVICE_ACCOUNT_ID \
    --description="Service account for GAM operations" \
    --display-name="GAM Service Account"
```

#### Option B: Use Existing Service Account
If you already have a service account with appropriate Google Workspace permissions (typically the one created during GAM7 initial setup), you can reuse it. Just note the service account email for the next steps.

```bash
# List existing service accounts to find the one you want to use
gcloud iam service-accounts list
```

### 4. Grant Required Permissions

```bash
# Grant necessary Google Workspace permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.serviceAccountTokenCreator"
```

## AWS Configuration

### 1. Create Workload Identity Provider for AWS
```bash
gcloud iam workload-identity-pools providers create-aws PROVIDER_ID \
    --workload-identity-pool="POOL_ID" \
    --account-id="YOUR_AWS_ACCOUNT_ID" \
    --location="global"
```

### 2. Allow AWS Identity to Impersonate Service Account
```bash
gcloud iam service-accounts add-iam-policy-binding \
    SERVICE_ACCOUNT_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.aws_role/arn:aws:sts::YOUR_AWS_ACCOUNT:assumed-role/YOUR_ROLE_NAME"
```

### 3. Create Credential Configuration File

Create a JSON file with your Workload Identity Federation configuration:

#### For AWS [IMDSv1](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html#instance-metadata-retrieval-examples-imdsv1)
```bash
gcloud iam workload-identity-pools create-cred-config \
    projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID \
    --service-account=SERVICE_ACCOUNT_EMAIL \
    --service-account-token-lifetime-seconds=SERVICE_ACCOUNT_TOKEN_LIFETIME \
    --aws \
    --output-file=FILEPATH.json
```

#### For AWS [IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html#instance-metadata-retrieval-examples)
```bash
gcloud iam workload-identity-pools create-cred-config \
    projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID \
    --service-account=SERVICE_ACCOUNT_EMAIL \
    --aws \
    --enable-imdsv2 \
    --output-file=FILEPATH.json
```

### 4. Configure GAM7 Environment for AWS

Set the environment variable to use the credential file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credential-configurations.json"
```

Open the `oauth2service.json` file, and set the `key_type` to `signjwt`. 

```
...
  "key_type": "signjwt",
...
```

### 5. Initialize GAM7

```bash
gam version
gam info user
```

## GitHub Actions Configuration

### 1. Create Workload Identity Provider for GitHub Actions
```bash
gcloud iam workload-identity-pools providers create-oidc PROVIDER_ID \
    --workload-identity-pool="POOL_ID" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition="assertion.repository_owner=='YOUR_GITHUB_ORGANIZATION'"
    --location="global"
```

### 2. Allow GitHub Actions to Impersonate Service Account
```bash
gcloud iam service-accounts add-iam-policy-binding \
    SERVICE_ACCOUNT_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/attribute.repository/YOUR_GITHUB_ORG/YOUR_REPO"
```

### 3. GitHub Actions Workflow Configuration
.github/workflows/example.yml
```yaml
name: GAM Operations
on: [push]

jobs:
  gam-job:
    runs-on: ubuntu-24.04
    permissions:
      id-token: write
      contents: read

    steps:
    - uses: actions/checkout@v3

    - name: Download and install GAM
      run: |
        bash <(curl -s -S -L https://git.io/gam-install) -l

    - name: Copy GAM configs into target dir
      # Make sure to remove the private key from oauth2service.json and set `key_type` to `signjwt`
      run: |
        cp ./gam.cfg ~/.gam/gam.cfg
        cp ./oauth2service.json ~/.gam/oauth2service.json

    # # For debugging GitHub identity tokens
    # - name: Print out GitHub OIDC token
    #   uses: github/actions-oidc-debugger@2e9ba5d3f4bebaad1f91a2cede055115738b7ae8
    #   with:
    #     audience: https://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID

    - id: 'auth'
      name: 'Authenticate to Google Cloud'
      uses: 'google-github-actions/auth@v1'
      with:
        create_credentials_file: true
        workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID'
        service_account: 'SERVICE_ACCOUNT_EMAIL'

    - name: Run GAM commands
      run: |
        ~/bin/gam7/gam info user
```

## Clean Up 

After verifying that gam is working as expected, delete the old key if it's no longer in use.
```bash
gcloud iam service-accounts keys delete KEY_ID --iam-account=SERVICE_ACCOUNT_EMAIL
``` 
Also remove it from the `oauth2service.json` file.
```
...
  "private_key": "",
  "private_key_id": "",
...
```


## Security Best Practices

1. **Principle of Least Privilege**: Grant only necessary permissions to the service account
2. **Attribute Conditions**: Use attribute conditions to restrict access based on specific criteria
3. **Regular Auditing**: Regularly review and audit Workload Identity Federation configurations
4. **Token Lifetime**: Configure appropriate token lifetimes for your use case

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify the audience URL matches your Workload Identity Pool
   - Check that the external identity has permission to impersonate the service account

2. **Permission Denied**
   - Ensure the service account has necessary Google Workspace permissions
   - Verify domain-wide delegation is configured if required

3. **Token Expiration**
   - Tokens are automatically refreshed by the Google Auth libraries
   - Check network connectivity to Google STS endpoints

### Debug Commands

```bash
# Test authentication
gcloud auth print-access-token

# Verify service account impersonation
gcloud auth print-access-token --impersonate-service-account=SERVICE_ACCOUNT_EMAIL

# Check GAM authentication
gam info user
```

## Benefits

- **Reduced Attack Surface**: Short-lived tokens minimize exposure window if compromised
- **Reduced Operational Cost**: Eliminates the overhead of managing and rotating service account keys
- **Improved Scalability**: Easily scale across multiple environments without distributing keys
- **Better Integration**: Native integration with cloud provider identity systems (AWS IAM, GitHub OIDC)
- **Compliance**: Meets security requirements for keyless authentication

## References

- [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Workload Identity Federation With Other Clouds](https://cloud.google.com/iam/docs/workload-identity-federation-with-other-clouds)
- [Authenticate to Google Cloud from GitHub Actions](https://github.com/google-github-actions/auth/blob/main/README.md)
- [Service Account Impersonation](https://cloud.google.com/iam/docs/impersonating-service-accounts)
