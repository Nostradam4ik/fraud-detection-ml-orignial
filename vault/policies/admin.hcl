# Vault Admin Policy
# Full access to fraud-detection secrets for administrators

# Full access to all fraud-detection secrets
path "secret/data/fraud-detection/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "secret/metadata/fraud-detection/*" {
  capabilities = ["list", "read", "delete"]
}

# Manage policies
path "sys/policies/acl/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# Create and manage tokens
path "auth/token/create" {
  capabilities = ["create", "update"]
}

path "auth/token/create-orphan" {
  capabilities = ["create", "update"]
}

# View audit logs
path "sys/audit" {
  capabilities = ["read", "list"]
}

# Health and status
path "sys/health" {
  capabilities = ["read"]
}

path "sys/seal-status" {
  capabilities = ["read"]
}
