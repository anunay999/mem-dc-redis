from __future__ import annotations

from typing import Dict, Optional

import requests
from pydantic import BaseModel, Field

from config import Settings, get_settings

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
        response = self.session.post(url, data=self._build_payload(), headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return SalesforceTokenResponse.model_validate(data)

    def fetch_user_info(self, access_token: str, instance_url: str) -> UserInfo:
        url = f"{instance_url.rstrip('/')}/services/oauth2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self.session.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return UserInfo.model_validate(response.json())

    def get_token(self) -> AuthResult:
        token = self.request_token()
        user_info = self.fetch_user_info(access_token=token.access_token, instance_url=token.instance_url)
        return AuthResult(access_token=token.access_token, instance_url=token.instance_url, userId=user_info.user_id)


def get_authenticated_details() -> Dict[str, str]:
    client = SalesforceAuthClient()
    result = client.get_token()
    return {
        "access_token": result.access_token,
        "instance_url": result.instance_url,
        "userId": result.userId,
    }
