"""Persistência local do token da Shopee (arquivo JSON fora do git)."""

import json
import os
from datetime import datetime, timedelta, timezone

from SPDV.config import ENV, TOKEN_PATH

# O refresh_token da Shopee vale 30 dias; a API não devolve essa expiração,
# então ela é calculada a partir do momento em que o token foi emitido.
REFRESH_TOKEN_TTL = timedelta(days=30)

# Renova um pouco antes de expirar, para não perder a corrida com o relógio da Shopee.
EXPIRY_SKEW = timedelta(seconds=60)

_REQUIRED_KEYS = ("access_token", "refresh_token", "expires_at", "refresh_expires_at")


def load() -> dict | None:
    """Lê o arquivo de token. Devolve None se ele não existir ou estiver inutilizável."""
    try:
        with open(TOKEN_PATH, encoding="utf-8") as file:
            record = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(record, dict) or not all(record.get(key) for key in _REQUIRED_KEYS):
        return None
    return record


def save(payload: dict, previous: dict | None = None) -> dict:
    """Converte a resposta da API no registro persistido e grava em TOKEN_PATH"""
    now = datetime.now(timezone.utc)

    shop_ids = payload.get("shop_id_list") or []
    # A Shopee rotaciona o refresh_token a cada renovação; se vier vazio, mantém o anterior.
    refresh_token = payload.get("refresh_token") or (previous or {}).get("refresh_token")

    record = {
        "access_token": payload["access_token"],
        "refresh_token": refresh_token,
        "expires_at": (now + timedelta(seconds=payload["expire_in"])).isoformat(),
        "refresh_expires_at": (now + REFRESH_TOKEN_TTL).isoformat(),
        "shop_id": shop_ids[0] if shop_ids else int(ENV["SHOP_ID"]),
        "obtained_at": now.isoformat(),
    }

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = TOKEN_PATH.with_name(TOKEN_PATH.name + ".part")
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(record, file, indent=2)
    os.replace(tmp_path, TOKEN_PATH)

    return record


def is_fresh(record: dict, key: str = "expires_at") -> bool:
    """True se a data guardada em `key` ainda estiver no futuro, descontada a margem."""
    try:
        expires_at = datetime.fromisoformat(record[key])
    except (KeyError, TypeError, ValueError):
        return False

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) + EXPIRY_SKEW < expires_at
