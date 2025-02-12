#!/usr/bin/env python3
'''Module for request caching and tracking using Redis.
'''
import redis
import requests
from datetime import timedelta


def get_page(url: str) -> str:
    '''Fetches and caches the content of a URL while tracking request counts.

    Args:
        url (str): The URL to retrieve content from.

    Returns:
        str: The decoded content of the response.
    '''
    if url is None or len(url.strip()) == 0:
        return ''

    redis_store = redis.Redis()
    
    # Keys for storing cached response and request count
    res_key = 'result:{}'.format(url)
    req_key = 'count:{}'.format(url)
    
    # Check if the response is already cached
    result = redis_store.get(res_key)
    if result is not None:
        # Increment request count if cached data exists
        redis_store.incr(req_key)
        return result

    # Fetch content from the URL if not cached
    result = requests.get(url).content.decode('utf-8')

    # Cache the response for 10 seconds
    redis_store.setex(res_key, timedelta(seconds=10), result)

    return result
