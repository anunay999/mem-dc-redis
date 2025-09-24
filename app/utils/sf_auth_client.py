from __future__ import annotations

from typing import Dict, Optional

import requests
from pydantic import BaseModel, Field

from config import Settings, get_settings
import logging

logger = logging.getLogger(__name__)

class SalesforceTokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(alias="token_type")
    instance_url: str
    issued_at: Optional[str] = None
    signature: Optional[str] = None
    scope: Optional[str] = None

    class Config:
        populate_by_name = True
        extra = "allow"


class UserInfo(BaseModel):
    user_id: str = Field(alias="user_id")
    class Config:
        populate_by_name = True
        extra = "allow"


class AuthResult(BaseModel):
    access_token: str
    instance_url: str
    userId: str = Field(alias="userId")
    # Data Cloud tenant-scoped credentials
    dcTenantToken: Optional[str] = Field(default=None, alias="dcTenantToken")
    dcTenantUrl: Optional[str] = Field(default=None, alias="dcTenantUrl")


class SalesforceAuthClient:
    def __init__(self, settings: Optional[Settings] = None, timeout: float = 30.0, session: Optional[requests.Session] = None) -> None:
        self.settings = settings or get_settings()
        self.timeout = timeout
        self.session = session or requests.Session()

    def _get_base_url(self) -> str:
        base = self.settings.salesforce_base_url
        if not base:
            raise ValueError("SALESFORCE_BASE_URL must be set in environment.")
        return base.rstrip("/")

    def _build_payload(self) -> Dict[str, str]:
        client_id = self.settings.client_id
        client_secret = self.settings.client_secret
        if not client_id or not client_secret:
            raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment.")
        return {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

    def request_token(self) -> SalesforceTokenResponse:
        url = f"{self._get_base_url()}/services/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        logger.info("Requesting Salesforce core token: url=%s", url)
        response = self.session.post(url, data=self._build_payload(), headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        logger.info("Received Salesforce core token (details masked)")
        return SalesforceTokenResponse.model_validate(data)

    def fetch_dc_token(self, core_access_token: str, core_instance_url: str) -> Dict[str, str]:
        """Exchange a core access token for a Data Cloud tenant token.
        """
        if not core_access_token or not core_instance_url:
            raise ValueError("core_access_token and core_instance_url are required for DC tenant exchange")

        url = f"{core_instance_url.rstrip('/')}/services/a360/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "urn:salesforce:grant-type:external:cdp",
            "subject_token": core_access_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        }
        logger.info("Exchanging for DC tenant token: url=%s", url)
        response = self.session.post(url, data=data, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()
        # Expect at least access_token and instance_url in response
        if "access_token" not in payload or "instance_url" not in payload:
            raise requests.HTTPError(
                f"Unexpected DC tenant token response: {payload}", response=response
            )
        return {
            "access_token": payload["access_token"],
            "instance_url": payload["instance_url"],
        }

    def fetch_user_info(self, access_token: str, instance_url: str) -> UserInfo:
        url = f"{instance_url.rstrip('/')}/services/oauth2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        logger.info("Fetching user info: url=%s", url)
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        logger.info("Fetched user info for user_id=%s", data.get("user_id"))
        return UserInfo(user_id=data["user_id"])

    def get_token(self) -> AuthResult:
        token = self.request_token()
        user_info = self.fetch_user_info(access_token=token.access_token, instance_url=token.instance_url)

        # Exchange for Data Cloud tenant-scoped token
        try:
            dc = self.fetch_dc_token(
                core_access_token=token.access_token,
                core_instance_url=token.instance_url,
            )
            dc_token = dc.get("access_token")
            dc_url = dc.get("instance_url")
            logger.info(f"Obtained DC tenant token and URL (details masked) {dc_url}")
        except Exception as e:
            logger.warning("DC tenant token exchange failed: %s", str(e))
            raise e

        return AuthResult(
            access_token=token.access_token,
            instance_url=token.instance_url,
            userId=user_info.user_id,
            dcTenantToken=dc_token,
            dcTenantUrl=dc_url,
        )


def get_authenticated_details() -> AuthResult:
    client = SalesforceAuthClient()
    result = client.get_token()
    return result
