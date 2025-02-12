#!/usr/bin/env python3
"""
Module containing the class definition for Redis-based caching.
"""

import redis
import uuid
from functools import wraps
from typing import Union, Callable, Optional


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts the number of times a method is called.

    Args:
        method (Callable): The function to be decorated.

    Returns:
        Callable: The wrapped function with call count tracking.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Increments the call count for the decorated method.

        Args:
            self: The object instance.
            *args: Positional arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            The return value of the decorated method.
        """
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)

    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator that records the inputs and outputs of a method.

    Args:
        method (Callable): The function to be decorated.

    Returns:
        Callable: The wrapped function with history tracking.
    """
    key = method.__qualname__
    inputs = key + ":inputs"
    outputs = key + ":outputs"

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Stores the function's inputs and outputs in Redis.

        Args:
            self: The object instance.
            *args: Positional arguments passed to the method.
            **kwargs: Keyword arguments passed to the method.

        Returns:
            The return value of the decorated method.
        """
        self._redis.rpush(inputs, str(args))
        data = method(self, *args, **kwargs)
        self._redis.rpush(outputs, str(data))
        return data

    return wrapper


def replay(method: Callable) -> None:
    """
    Displays the history of calls to a decorated function.

    Args:
        method (Callable): The function whose history is to be replayed.

    Returns:
        None
    """
    name = method.__qualname__
    cache = redis.Redis()
    calls = cache.get(name).decode("utf-8")
    print("{} was called {} times:".format(name, calls))
    inputs = cache.lrange(name + ":inputs", 0, -1)
    outputs = cache.lrange(name + ":outputs", 0, -1)
    for i, o in zip(inputs, outputs):
        print("{}(*{}) -> {}".format(name, i.decode('utf-8'), o.decode('utf-8')))


class Cache:
    """
    A Redis-based caching system with data storage and retrieval functionality.
    """
    def __init__(self) -> None:
        """
        Initializes the Redis client and clears the database.

        Attributes:
            self._redis (redis.Redis): Redis client instance.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Stores data in the Redis cache with a unique key.

        Args:
            data (Union[str, bytes, int, float]): The data to be stored.

        Returns:
            str: The generated key for the stored data.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieves data from the Redis cache and applies an optional conversion function.

        Args:
            key (str): The key associated with the stored data.
            fn (Optional[Callable]): An optional function to convert the retrieved data.

        Returns:
            Union[str, bytes, int, float, None]: The retrieved data, optionally transformed.
        """
        data = self._redis.get(key)
        if data is not None and fn is not None and callable(fn):
            return fn(data)
        return data

    def get_str(self, key: str) -> str:
        """
        Retrieves and decodes data as a string from the Redis cache.

        Args:
            key (str): The key associated with the stored data.

        Returns:
            str: The retrieved data as a string.
        """
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> int:
        """
        Retrieves and converts data to an integer from the Redis cache.

        Args:
            key (str): The key associated with the stored data.

        Returns:
            int: The retrieved data as an integer.
        """
        return self.get(key, int)
