from settings import settings
import requests
from typing import Union, Optional, Dict
from urllib.parse import urlencode

def build_riot_url(
    region: str,
    endpoint: str,
    *paths: Union[str, int],
    params: Optional[Dict[str, str]] = None
) -> str:
    """
    Build a Riot API URL with optional path segments and query parameters.

    Args:
        region: platform region (e.g., 'na1', 'euw1')
        endpoint: base endpoint (e.g., 'lol/league/v4/challengerleagues')
        *paths: optional additional path segments (e.g., 'by-queue', 'RANKED_SOLO_5x5')
        params: optional query parameters as a dict

    Returns:
        Full URL as string
    """
    base = f"https://{region}.{settings.BASE_RIOT_API_URL}/{endpoint.lstrip('/')}"

    if paths:
        extra = "/".join(str(p).strip("/") for p in paths)
        base = f"{base}/{extra}"

    if params:
        query_string = urlencode(params)
        return f"{base}?{query_string}"

    return base

def request_riot_api(region: str, endpoint: str, params: Optional[Dict[str, str]] = None) -> dict:
    url = build_riot_url(region, endpoint, params=params)
    headers = {
        "X-Riot-Token": settings.RIOT_API_KEY
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()
