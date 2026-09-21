"""Shared SlowAPI limiter used by the application and endpoint decorators."""

from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(key_func=get_remote_address)