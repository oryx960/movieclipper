def test_jellyfin_connection(url: str, api_key: str) -> bool:
    # Stub for now
    return url.startswith("http") and len(api_key) > 5
