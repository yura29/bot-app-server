from fastapi import Request
from fastapi.exceptions import HTTPException
from typing import Optional

from aiogram.utils.web_app import WebAppInitData, safe_parse_webapp_init_data

from config_reader import config


def auth(request: Request) -> Optional[WebAppInitData]:
    try:
        auth_string = request.headers.get("authorization", None)
        if auth_string:
            data = safe_parse_webapp_init_data(
                config.BOT_TOKEN.get_secret_value(), auth_string
            )
            return data
        else:
            print("Warning: X-Telegram-Auth header not found. Returning None for auth.")
            return None
    except Exception as e:
        print(f"Error parsing WebApp init data: {e}. Returning None for auth.")
        return None