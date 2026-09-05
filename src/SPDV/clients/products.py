import time
from urllib.parse import urlsplit

import requests

from SPDV.clients.auth import get_access_token, sign
from SPDV.config import ENV


def get_product_list(item_status: list) -> dict:
    """Retorna o id dos produtos"""
    url = f"{ENV['BASE_URL']}/api/v2/product/get_item_list"
    api_path = urlsplit(url).path
    timestamp = int(time.time())
    access_token = get_access_token()
    shop_id = int(ENV["SHOP_ID"])

    params = {
        "partner_id": int(ENV["PARTNER_ID"]),
        "timestamp": timestamp,
        "access_token": access_token,
        "shop_id": shop_id,
        "sign": sign(api_path, timestamp, access_token, shop_id),
        "offset": 0,
        "page_size": 100,
        "item_status": item_status,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()
