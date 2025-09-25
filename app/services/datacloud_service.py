"""Data Cloud Service - Manages Salesforce Data Cloud ingestion and Search operations."""

from __future__ import annotations

import logging
from typing import Dict, Any, List

import requests

from config import get_settings
from utils.sf_auth_client import AuthResult

logger = logging.getLogger(__name__)
settings = get_settings()

# Data Cloud Query Service endpoint
QUERY_SVC_ENDPOINT = 'services/data/v63.0/ssot/queryv2'


class DataCloudService:
    """Service class for managing Salesforce Data Cloud operations."""

    def __init__(self):
        """Initialize Data Cloud service."""
        logger.info("Initializing Data Cloud Service")

    def ingest_memory(self, data: Dict[str, Any], connector: str, dlo: str, token: AuthResult) -> Dict[str, Any]:
        """Ingest a memory payload into Data Cloud using Salesforce OAuth token.

        Args:
            data: Memory payload data to ingest
            connector: Data Cloud connector identifier
            dlo: Data Lake Object identifier
            token: Salesforce authentication token with tenant information

        Returns:
            Response from Data Cloud ingestion API

        Raises:
            ValueError: If required parameters are missing or invalid
            requests.HTTPError: If HTTP request fails
            requests.RequestException: If network error occurs
        """
        # Validate inputs
        if not connector or not connector.strip():
            raise ValueError("connector must be non-empty")
        if not dlo or not dlo.strip():
            raise ValueError("dlo must be non-empty")
        if not token or not token.instance_url:
            raise ValueError("token must be non-empty")

        # Build ingestion URL
        url = self._build_ingestion_url(token, connector, dlo)

        # Prepare headers
        headers = self._build_headers(token)

        # Make the request
        return self._make_ingestion_request(url, data, headers, connector, dlo, token)

    def _build_ingestion_url(self, token: AuthResult, connector: str, dlo: str) -> str:
        """Build the Data Cloud ingestion URL."""
        # Prefer tenant-scoped URL if available
        instance = token.dcTenantUrl.rstrip("/")

        # Ensure we do not double-prefix scheme
        if instance.startswith("http://") or instance.startswith("https://"):
            base = instance
        else:
            base = f"https://{instance}"

        ingestion_endpoint = "api/v1/ingest/sources"
        return f"{base}/{ingestion_endpoint}/{connector.strip()}/{dlo.strip()}"

    def _build_headers(self, token: AuthResult) -> Dict[str, str]:
        """Build HTTP headers for the Data Cloud request."""
        # Prefer tenant-scoped token if available
        bearer_token = token.dcTenantToken
        return {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_ingestion_request(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Dict[str, str],
        connector: str,
        dlo: str,
        token: AuthResult
    ) -> Dict[str, Any]:
        """Make the actual HTTP request to Data Cloud."""
        try:
            logger.info(
                "POST Data Cloud ingest: url=%s connector=%s dlo=%s using_tenant_token=%s",
                url,
                connector,
                dlo,
                bool(token.dcTenantToken),
            )

            response = requests.post(url, json=data, headers=headers, timeout=30)
            logger.info("Data Cloud ingest response: status=%s", response.status_code)
            response.raise_for_status()

            # Attempt to return JSON response; if none, return minimal dict
            try:
                return response.json()
            except Exception:
                return {"status_code": response.status_code, "text": response.text}

        except requests.HTTPError as e:  # HTTP status errors
            status = e.response.status_code if e.response is not None else 0
            body = e.response.text if e.response is not None else str(e)
            raise requests.HTTPError(f"HTTP error {status}: {body}", request=e.request, response=e.response)
        except requests.RequestException as e:
            logger.error("Network error during Data Cloud ingest: %s", str(e))
            raise requests.RequestException(f"Network error: {str(e)}")

    def _build_query_url(self, token: AuthResult) -> str:
        """Build the Data Cloud query service URL."""
        # Use standard instance URL for query service (not tenant-scoped)
        instance = token.instance_url.rstrip("/")

        # Ensure we do not double-prefix scheme
        if instance.startswith("http://") or instance.startswith("https://"):
            base = instance
        else:
            base = f"https://{instance}"

        return f"{base}/{QUERY_SVC_ENDPOINT}"

    def _build_query_headers(self, token: AuthResult) -> Dict[str, str]:
        """Build HTTP headers for the Data Cloud query request."""
        # Use standard access token for query service
        return {
            "Authorization": f"Bearer {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _make_query_request(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Dict[str, str],
        user_id: str,
        utterance: str
    ) -> Dict[str, Any]:
        """Make the actual HTTP request to Data Cloud Query Service."""
        try:
            logger.debug(
                "POST Data Cloud query: url=%s user_id=%s utterance=%s",
                url,
                user_id,
                utterance[:50] + "..." if len(utterance) > 50 else utterance
            )

            response = requests.post(url, json=data, headers=headers, timeout=30)
            logger.info("Data Cloud query response: status=%s", response.status_code)
            response.raise_for_status()

            # Return JSON response
            try:
                return response.json()
            except Exception:
                return {"status_code": response.status_code, "text": response.text}

        except requests.HTTPError as e:  # HTTP status errors
            status = e.response.status_code if e.response is not None else 0
            body = e.response.text if e.response is not None else str(e)
            logger.error("Data Cloud query HTTP error %s: %s", status, body)
            raise requests.HTTPError(f"HTTP error {status}: {body}", request=e.request, response=e.response)
        except requests.RequestException as e:
            logger.error("Network error during Data Cloud query: %s", str(e))
            raise requests.RequestException(f"Network error: {str(e)}")

    def validate_connection(self, token: AuthResult) -> bool:
        """Validate connection to Data Cloud (placeholder for future implementation)."""
        # TODO: Implement connection validation
        return token is not None and bool(token.dcTenantUrl)