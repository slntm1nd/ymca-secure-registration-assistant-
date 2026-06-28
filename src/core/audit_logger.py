# HIPAA/COPPA logging
import secrets
import json
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
import boto3

logger = logging.getLogger(__name__)

class EventType(Enum):
    PII_ENCRYPTED = "PII_ENCRYPTED"
    PII_DECRYPTED = "PII_DECRYPTED"
    SLOT_CHECKED = "SLOT_CHECKED"
    # and so on...

