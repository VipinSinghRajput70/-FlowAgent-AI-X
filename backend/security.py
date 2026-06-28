import os
import time
import hmac
import hashlib
import base64
import json
import bcrypt

SECRET_KEY = os.environ.get("SECRET_KEY", "flowagent_secure_hackathon_token_secret_key_2026")

# -------------------------------------------------------------
# Password Hashing & Verification (bcrypt)
# -------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        # Fallback to simple secure comparison if bcrypt fails
        h = hashlib.sha256(plain_password.encode()).hexdigest()
        return h == hashed_password

# -------------------------------------------------------------
# Zero-Dependency JWT-like Token Encoder / Decoder (using HMAC)
# -------------------------------------------------------------

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).replace(b'=', b'').decode('utf-8')

def base64url_decode(data: str) -> bytes:
    # Add padding back if missing
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: dict, expires_in_seconds: int = 3600) -> str:
    """Creates a signed JWT-like token string."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in_seconds
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    
    # Signature
    signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_access_token(token: str) -> dict:
    """Decodes and validates a signed token. Returns payload dict or None if invalid."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
            
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), signing_input, hashlib.sha256).digest()
        expected_sig_b64 = base64url_encode(expected_sig)
        
        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None # Signature mismatch
            
        # Parse payload
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        
        # Check expiry
        if payload.get("exp", 0) < int(time.time()):
            return None # Expired
            
        return payload
    except Exception:
        return None

# -------------------------------------------------------------
# Rate Limiting Helper (In-memory token bucket)
# -------------------------------------------------------------
class TokenBucketLimiter:
    def __init__(self, rate: int, capacity: int):
        self.rate = rate # Tokens added per second
        self.capacity = capacity # Max tokens
        self.buckets = {} # IP -> [tokens, last_update_time]

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        if ip not in self.buckets:
            self.buckets[ip] = [self.capacity, now]
            return True
            
        tokens, last_update = self.buckets[ip]
        # Add new tokens based on elapsed time
        elapsed = now - last_update
        tokens = min(self.capacity, tokens + elapsed * self.rate)
        
        if tokens >= 1.0:
            self.buckets[ip] = [tokens - 1.0, now]
            return True
        else:
            self.buckets[ip] = [tokens, now]
            return False

# Limit to 5 API requests per second per IP
rate_limiter = TokenBucketLimiter(rate=5, capacity=10)
