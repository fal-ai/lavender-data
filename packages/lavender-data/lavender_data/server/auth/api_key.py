import secrets


def generate_api_key_secret():
    return secrets.token_urlsafe(32)
