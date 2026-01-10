# Vault Policy for Fraud Detection Application
# This policy grants access to secrets needed by the application

# Database credentials
path "secret/data/fraud-detection/database" {
  capabilities = ["read"]
}

# Redis credentials
path "secret/data/fraud-detection/redis" {
  capabilities = ["read"]
}

# JWT secrets
path "secret/data/fraud-detection/jwt" {
  capabilities = ["read"]
}

# API keys (external services)
path "secret/data/fraud-detection/api-keys" {
  capabilities = ["read"]
}

# Email configuration
path "secret/data/fraud-detection/email" {
  capabilities = ["read"]
}

# AWS credentials (for S3 backups)
path "secret/data/fraud-detection/aws" {
  capabilities = ["read"]
}

# Allow token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Allow looking up token info
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
