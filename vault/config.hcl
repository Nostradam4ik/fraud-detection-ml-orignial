# HashiCorp Vault Configuration
# For development and production use

ui = true
disable_mlock = true

storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = true  # Enable TLS in production
}

api_addr = "http://0.0.0.0:8200"

# Telemetry for monitoring
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
}

# Audit logging
# audit {
#   type   = "file"
#   path   = "/vault/logs/audit.log"
#   format = "json"
# }
