#!/bin/sh
# Initialize Vault with secrets for Fraud Detection

set -e

echo "Waiting for Vault to be ready..."
sleep 5

echo "Enabling KV secrets engine v2..."
vault secrets enable -path=secret kv-v2 || true

echo "Creating policies..."
vault policy write fraud-detection /vault/policies/fraud-detection.hcl
vault policy write admin /vault/policies/admin.hcl

echo "Writing development secrets..."

# Database credentials
vault kv put secret/fraud-detection/database \
  host="postgres" \
  port="5432" \
  name="fraud_detection" \
  username="fraud_admin" \
  password="dev_password_change_in_prod"

# Redis credentials
vault kv put secret/fraud-detection/redis \
  host="redis" \
  port="6379" \
  password=""

# JWT configuration
vault kv put secret/fraud-detection/jwt \
  secret_key="dev-jwt-secret-change-in-production-32chars" \
  algorithm="HS256" \
  access_token_expire_minutes="30" \
  refresh_token_expire_days="7"

# API keys (placeholder)
vault kv put secret/fraud-detection/api-keys \
  sendgrid_api_key="" \
  slack_webhook_url="" \
  sentry_dsn=""

# Email configuration
vault kv put secret/fraud-detection/email \
  smtp_host="smtp.example.com" \
  smtp_port="587" \
  smtp_user="" \
  smtp_password="" \
  from_email="noreply@fraud-detection.local"

# AWS credentials (for S3 backups)
vault kv put secret/fraud-detection/aws \
  access_key_id="" \
  secret_access_key="" \
  region="eu-west-1" \
  s3_bucket=""

echo "Creating app token..."
vault token create \
  -policy=fraud-detection \
  -ttl=720h \
  -renewable=true \
  -display-name="fraud-detection-app" \
  -format=json > /dev/null

echo "Vault initialization complete!"
echo ""
echo "To get started:"
echo "  export VAULT_ADDR='http://localhost:8200'"
echo "  export VAULT_TOKEN='dev-root-token'"
echo ""
echo "To create an app token:"
echo "  vault token create -policy=fraud-detection -ttl=720h"
