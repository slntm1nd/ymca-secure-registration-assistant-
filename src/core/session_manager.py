# JWT + Token revocation
import os
import secrets
import logging
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict
import redis
import jwt

logger = logging.getLogger(__name__)

# Скопируй сюда класс SessionManager полностью из app_security_core.py
