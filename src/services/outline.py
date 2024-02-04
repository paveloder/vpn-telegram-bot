from outline_vpn.outline_vpn import OutlineVPN

from src import config

# Setup the access with the API URL (Use the one provided to you after the server setup)
client = OutlineVPN(api_url=config.OUTLINE_API_URL)


def create_key(key_name: str) -> str:
    key = client.create_key(key_name=key_name)
    return key.access_url

