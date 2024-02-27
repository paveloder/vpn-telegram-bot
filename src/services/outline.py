from functools import lru_cache

from outline_vpn.outline_vpn import OutlineVPN

from src import models


@lru_cache
def create_client(api_url: str) -> OutlineVPN:
    return OutlineVPN(api_url=api_url)


def create_key(key_name: str, server: models.Server) -> str:
    client = create_client(server.api_url)
    key = client.create_key(key_name=key_name)
    return key.access_url

