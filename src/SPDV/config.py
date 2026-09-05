import os
from pathlib import Path

from dotenv import dotenv_values, find_dotenv, load_dotenv

_ENV_PATH = find_dotenv()

load_dotenv(_ENV_PATH)

ENV: dict[str, str] = {key: os.environ[key] for key in dotenv_values(_ENV_PATH)}

# Raiz do projeto: diretório onde está o .env localizado acima
PROJECT_ROOT = Path(_ENV_PATH).resolve().parent

# Arquivo local (fora do git) com o access_token, o refresh_token e as expirações
# Configurável pela variável opcional TOKEN_FILE no .env
_TOKEN_FILE = Path(ENV.get("TOKEN_FILE") or "tmp_shopee_token.json")
TOKEN_PATH = _TOKEN_FILE if _TOKEN_FILE.is_absolute() else PROJECT_ROOT / _TOKEN_FILE
