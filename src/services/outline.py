from functools import lru_cache

from outline_vpn.outline_vpn import OutlineKey, OutlineVPN

from src import models


@lru_cache
def create_client(api_url: str) -> OutlineVPN:
    return OutlineVPN(api_url=api_url)


def create_key(key_name: str, server: models.Server) -> str:
    client = create_client(server.api_url)
    key = client.create_key(key_name=key_name)
    return key.access_url


def get_keys(key_name: str, server: models.Server) -> list[str]:
    client = create_client(server.api_url)
    keys: list[OutlineKey] = client.get_keys()

    return [
        outline_key.access_url
        for outline_key in keys if outline_key.name==key_name
    ]


def key_get_or_create(key_name: str, server: models.Server) -> str:
    keys = get_keys(key_name, server)
    if keys:
        # TODO: add support multiple keys per server
        return keys[0]
    return create_key(key_name, server)
