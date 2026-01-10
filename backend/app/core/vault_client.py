"""
HashiCorp Vault Client for Secret Management
Provides secure access to application secrets

Author: Zhmuryk Andrii
Copyright (c) 2024 - All Rights Reserved
"""

import os
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

import httpx

logger = logging.getLogger(__name__)


class VaultClient:
    """Client for HashiCorp Vault secret management"""

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        namespace: Optional[str] = None,
        mount_point: str = "secret",
        timeout: float = 10.0
    ):
        """
        Initialize Vault client

        Args:
            vault_addr: Vault server address (default: VAULT_ADDR env var)
            vault_token: Vault token (default: VAULT_TOKEN env var)
            namespace: Vault namespace (enterprise feature)
            mount_point: KV secrets engine mount point
            timeout: Request timeout in seconds
        """
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR", "http://localhost:8200")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.namespace = namespace or os.getenv("VAULT_NAMESPACE")
        self.mount_point = mount_point
        self.timeout = timeout

        self._client: Optional[httpx.Client] = None
        self._secrets_cache: Dict[str, Any] = {}

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client"""
        if self._client is None:
            headers = {
                "X-Vault-Token": self.vault_token,
                "Content-Type": "application/json"
            }
            if self.namespace:
                headers["X-Vault-Namespace"] = self.namespace

            self._client = httpx.Client(
                base_url=self.vault_addr,
                headers=headers,
                timeout=self.timeout
            )
        return self._client

    def is_available(self) -> bool:
        """Check if Vault is available and authenticated"""
        if not self.vault_token:
            logger.warning("Vault token not configured")
            return False

        try:
            client = self._get_client()
            response = client.get("/v1/sys/health")
            return response.status_code in [200, 429, 472, 473, 501]
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False

    def read_secret(self, path: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Read a secret from Vault

        Args:
            path: Secret path (e.g., 'fraud-detection/database')
            use_cache: Whether to use cached values

        Returns:
            Secret data or None if not found
        """
        cache_key = f"{self.mount_point}/{path}"

        # Check cache
        if use_cache and cache_key in self._secrets_cache:
            return self._secrets_cache[cache_key]

        try:
            client = self._get_client()
            url = f"/v1/{self.mount_point}/data/{path}"
            response = client.get(url)

            if response.status_code == 200:
                data = response.json()
                secret_data = data.get("data", {}).get("data", {})

                # Cache the secret
                self._secrets_cache[cache_key] = secret_data
                return secret_data

            elif response.status_code == 404:
                logger.warning(f"Secret not found: {path}")
                return None
            else:
                logger.error(f"Failed to read secret: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error reading secret {path}: {e}")
            return None

    def write_secret(self, path: str, data: Dict[str, Any]) -> bool:
        """
        Write a secret to Vault

        Args:
            path: Secret path
            data: Secret data to write

        Returns:
            True if successful
        """
        try:
            client = self._get_client()
            url = f"/v1/{self.mount_point}/data/{path}"
            response = client.post(url, json={"data": data})

            if response.status_code in [200, 204]:
                # Invalidate cache
                cache_key = f"{self.mount_point}/{path}"
                self._secrets_cache.pop(cache_key, None)
                return True

            logger.error(f"Failed to write secret: {response.status_code}")
            return False

        except Exception as e:
            logger.error(f"Error writing secret {path}: {e}")
            return False

    def delete_secret(self, path: str) -> bool:
        """
        Delete a secret from Vault

        Args:
            path: Secret path

        Returns:
            True if successful
        """
        try:
            client = self._get_client()
            url = f"/v1/{self.mount_point}/metadata/{path}"
            response = client.delete(url)

            if response.status_code in [200, 204]:
                # Invalidate cache
                cache_key = f"{self.mount_point}/{path}"
                self._secrets_cache.pop(cache_key, None)
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting secret {path}: {e}")
            return False

    def list_secrets(self, path: str = "") -> Optional[list]:
        """
        List secrets at a path

        Args:
            path: Path to list

        Returns:
            List of secret names
        """
        try:
            client = self._get_client()
            url = f"/v1/{self.mount_point}/metadata/{path}"
            response = client.request("LIST", url)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("keys", [])

            return None

        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return None

    def get_database_url(self) -> Optional[str]:
        """Get database URL from Vault"""
        secret = self.read_secret("fraud-detection/database")
        if secret:
            return (
                f"postgresql://{secret['username']}:{secret['password']}"
                f"@{secret['host']}:{secret['port']}/{secret['name']}"
            )
        return None

    def get_redis_url(self) -> Optional[str]:
        """Get Redis URL from Vault"""
        secret = self.read_secret("fraud-detection/redis")
        if secret:
            password = secret.get('password', '')
            auth = f":{password}@" if password else ""
            return f"redis://{auth}{secret['host']}:{secret['port']}"
        return None

    def get_jwt_secret(self) -> Optional[str]:
        """Get JWT secret from Vault"""
        secret = self.read_secret("fraud-detection/jwt")
        if secret:
            return secret.get('secret_key')
        return None

    def get_aws_credentials(self) -> Optional[Dict[str, str]]:
        """Get AWS credentials from Vault"""
        return self.read_secret("fraud-detection/aws")

    def clear_cache(self):
        """Clear the secrets cache"""
        self._secrets_cache.clear()

    def close(self):
        """Close the HTTP client"""
        if self._client:
            self._client.close()
            self._client = None


# Singleton instance
_vault_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    """Get the Vault client singleton"""
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
    return _vault_client


def get_secret(path: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get a secret"""
    return get_vault_client().read_secret(path)


class VaultSecretProvider:
    """
    Secret provider that falls back to environment variables
    when Vault is not available
    """

    def __init__(self):
        self.vault = get_vault_client()
        self._use_vault = self.vault.is_available()

        if self._use_vault:
            logger.info("Using HashiCorp Vault for secrets")
        else:
            logger.warning("Vault not available, falling back to environment variables")

    def get(self, vault_path: str, key: str, env_var: str, default: Any = None) -> Any:
        """
        Get a secret value

        Args:
            vault_path: Path in Vault (e.g., 'fraud-detection/database')
            key: Key within the secret
            env_var: Environment variable fallback
            default: Default value if not found

        Returns:
            Secret value
        """
        if self._use_vault:
            secret = self.vault.read_secret(vault_path)
            if secret and key in secret:
                return secret[key]

        return os.getenv(env_var, default)

    def get_database_url(self) -> str:
        """Get database URL from Vault or environment"""
        if self._use_vault:
            url = self.vault.get_database_url()
            if url:
                return url

        return os.getenv(
            "DATABASE_URL",
            "sqlite:///./fraud_detection.db"
        )

    def get_redis_url(self) -> str:
        """Get Redis URL from Vault or environment"""
        if self._use_vault:
            url = self.vault.get_redis_url()
            if url:
                return url

        return os.getenv("REDIS_URL", "redis://localhost:6379")

    def get_jwt_secret(self) -> str:
        """Get JWT secret from Vault or environment"""
        if self._use_vault:
            secret = self.vault.get_jwt_secret()
            if secret:
                return secret

        return os.getenv(
            "JWT_SECRET_KEY",
            "dev-secret-key-change-in-production"
        )


# Global secret provider instance
secret_provider = VaultSecretProvider()
