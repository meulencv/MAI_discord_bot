import os
import aiohttp
import logging
import requests
import random

logger = logging.getLogger('ProxyManager')

def get_webshare_proxy_sync():
    """Synchronous version for bot initialization."""
    token = os.getenv('WEBSHARE_TOKEN') or os.getenv('PROXY')
    if not token:
        return None
    
    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct"
    headers = {"Authorization": f"Token {token}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                random.shuffle(results)
                p = results[0]
                return f"http://{p['username']}:{p['password']}@{p['proxy_address']}:{p['port']}"
    except:
        pass
    return None

async def get_webshare_proxy():
    """Fetches the first available proxy from Webshare API."""
    token = os.getenv('WEBSHARE_TOKEN') or os.getenv('PROXY')
    if not token:
        logger.error("WEBSHARE_TOKEN or PROXY not found in environment variables.")
        return None

    url = "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct"
    headers = {"Authorization": f"Token {token}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    if results:
                        random.shuffle(results)
                        p = results[0]  # Take a random one
                        proxy_url = f"http://{p['username']}:{p['password']}@{p['proxy_address']}:{p['port']}"
                        logger.info(f"Successfully fetched random proxy: {p['proxy_address']}")
                        return proxy_url
                    else:
                        logger.warning("No proxies found in Webshare account.")
                else:
                    logger.error(f"Webshare API error: {response.status} - {await response.text()}")
    except Exception as e:
        logger.error(f"Error fetching proxy from Webshare: {e}")
    
    return None
