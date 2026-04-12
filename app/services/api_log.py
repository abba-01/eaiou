"""
API call logging with SHA256 hash chain.
Every row: log_hash = SHA256(endpoint+method+request_hash+response_code+ts)
prior_hash = log_hash of previous row (NULL for first row)
Never raises — logging failure must never break the API.
"""
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text


def log_api_call(db: Session, endpoint: str, method: str,
                 request_hash: str, response_code: int) -> None:
    now = datetime.now(timezone.utc)
    ts  = now.isoformat()
    raw = f"{endpoint}|{method}|{request_hash}|{response_code}|{ts}"
    log_hash = hashlib.sha256(raw.encode()).hexdigest()
    try:
        prior = db.execute(text(
            "SELECT log_hash FROM `#__eaiou_api_logs` ORDER BY id DESC LIMIT 1"
        )).fetchone()
        prior_hash = prior[0] if prior else None
        db.execute(text(
            "INSERT INTO `#__eaiou_api_logs` "
            "(endpoint, method, request_data, response_code, log_hash, prior_hash, log_timestamp) "
            "VALUES (:ep, :m, :rh, :rc, :lh, :ph, :ts)"
        ), {"ep": endpoint, "m": method, "rh": request_hash,
            "rc": response_code, "lh": log_hash, "ph": prior_hash, "ts": now})
        db.commit()
    except Exception:
        pass  # Never let logging failure break the API
