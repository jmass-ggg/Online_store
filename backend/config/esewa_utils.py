import base64
import hashlib
import hmac
import json
from typing import Dict

def canonical_message(payload:Dict[str,str],signed_field_names:str)->str:
    fields = [f.strip() for f in signed_field_names.split(",") if f.strip()]
    return ",".join([f"{f}={payload[f]}" for f in fields])

def hmac_sha256_base64(message:str,secret_key:str)->str:
    digest=hmac.new(secret_key.encode(),message.encode(),hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")

def decode_esewa_data(data_b64: str) -> Dict[str, str]:
    padding = "=" * (-len(data_b64) % 4)
    raw = base64.b64decode(data_b64 + padding)
    obj = json.loads(raw.decode("utf-8"))
    return {k: str(v) for k, v in obj.items()}
