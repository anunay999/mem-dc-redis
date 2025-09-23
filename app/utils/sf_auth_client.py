import sys
from typing import Dict

import requests
from config import Settings, get_settings


def _get_base_url(settings: Settings) -> str:
    explicit_base = settings.salesforce_base_url
    if explicit_base:
        return explicit_base.rstrip("/")

    my_domain_url = settings.my_domain_url
    if my_domain_url:
        return my_domain_url.rstrip("/")

    domain = settings.domain
    if domain:
        domain_stripped = domain.rstrip("/")
        if domain_stripped.startswith("http://") or domain_stripped.startswith("https://"):
            return domain_stripped
        return f"https://{domain_stripped}"

    env_name = (settings.env or "").lower()
    if env_name in {"sandbox", "test"}:
        return "https://test.salesforce.com"

    return "https://login.salesforce.com"


def _build_payload(settings: Settings) -> Dict[str, str]:
    grant_type = (settings.grant_type or "client_credentials").strip()
    if grant_type != "client_credentials":
        print(
            "Warning: GRANT_TYPE is not 'client_credentials'. Overriding to client_credentials for this script.",
            file=sys.stderr,
        )
    client_id = settings.client_id
    client_secret = settings.client_secret
    if not client_id or not client_secret:
        raise ValueError("CLIENT_ID and CLIENT_SECRET must be set in environment.")

    payload: Dict[str, str] = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    return payload


def get_authenticated_details() -> Dict[str, str]:
    settings = get_settings()

    token_url = f"{_get_base_url(settings)}/services/oauth2/token"
    payload = _build_payload(settings)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        response = requests.post(token_url, data=payload, headers=headers, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                details = response.json()
            except Exception:
                details = {"text": response.text}
            print(
                f"Token request failed: status={response.status_code} url={token_url} details={details}",
                file=sys.stderr,
            )
            return details

        try:
            data = response.json()
        except Exception:
            print("Token endpoint did not return JSON.", file=sys.stderr)
            print(response.text)
            return 0

        return data

    except requests.RequestException as err:
        print(f"HTTP error: {err}", file=sys.stderr)
        return 3
    except Exception as err:  # noqa: BLE001
        print(f"Error: {err}", file=sys.stderr)
        return 1

