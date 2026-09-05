import hashlib
import hmac
import time
from urllib.parse import urlsplit

import requests

from SPDV.clients import token_store
from SPDV.config import ENV


class ShopeeAuthError(RuntimeError):
    """A Shopee respondeu HTTP 200 com o campo `error` preenchido."""


def sign(
    api_path: str,
    timestamp: int,
    access_token: str | None = None,
    shop_id: int | None = None,
) -> str:
    """HMAC-SHA256 de partner_id + api_path + timestamp.

    Nas APIs de loja a base ainda recebe access_token + shop_id
    """
    base_string = f"{ENV['PARTNER_ID']}{api_path}{timestamp}"
    if access_token:
        base_string += f"{access_token}{shop_id}"
    return hmac.new(
        ENV["PARTNER_KEY"].encode(),
        base_string.encode(),
        hashlib.sha256,
    ).hexdigest()


def _post_auth(url: str, body: dict) -> dict:
    """POST numa API pública de auth, validando o erro que vem no corpo da resposta"""
    api_path = urlsplit(url).path
    timestamp = int(time.time())

    # Common parameters
    params = {
        "partner_id": int(ENV["PARTNER_ID"]),
        "timestamp": timestamp,
        "sign": sign(api_path, timestamp),
    }

    response = requests.post(url, params=params, json=body)

    try:
        payload = response.json()
    except ValueError:
        payload = None

    if payload and payload.get("error"):
        raise ShopeeAuthError(f"{payload['error']}: {payload.get('message', '')}")

    response.raise_for_status()

    if not payload:
        raise ShopeeAuthError(f"resposta inesperada de {api_path}: {response.text[:200]}")
    return payload


def _token_from_code() -> dict:
    """Troca o `code` do OAuth por um par access_token/refresh_token novo"""
    return _post_auth(
        f"{ENV['BASE_URL']}/api/v2/auth/token/get",
        {
            "code": ENV["AUTH_SHOP_CODE"],
            "partner_id": int(ENV["PARTNER_ID"]),
            "shop_id": int(ENV["SHOP_ID"]),
        },
    )


def _token_from_refresh(refresh_token: str) -> dict:
    """Renova o access_token a partir do refresh_token (que também é rotacionado)"""
    return _post_auth(
        f"{ENV['BASE_URL']}/api/v2/auth/access_token/get",
        {
            "refresh_token": refresh_token,
            "partner_id": int(ENV["PARTNER_ID"]),
            "shop_id": int(ENV["SHOP_ID"]),
        },
    )


def get_access_token(force_refresh: bool = False) -> str:
    """Devolve um access_token válido, renovando ou reautorizando quando necessário"""
    record = token_store.load()

    if record and not force_refresh and token_store.is_fresh(record):
        return record["access_token"]

    if record and token_store.is_fresh(record, "refresh_expires_at"):
        try:
            payload = _token_from_refresh(record["refresh_token"])
        except (ShopeeAuthError, requests.RequestException):
            pass  # refresh_token revogado ou inválido: cai no fluxo do code
        else:
            return token_store.save(payload, previous=record)["access_token"]

    return token_store.save(_token_from_code())["access_token"]
