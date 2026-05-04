"""
mint_partner_key.py — issue a new partner key for the checksubmit marketplace.

Run with:
    python scripts/mint_partner_key.py --name "checksubmit MCP server" [--wholesale] [--rate 60]

Prints the raw key ONCE, immediately, then never again. The DB stores only the
SHA-256 hash. If you lose the raw key, you must mint a new one.

Output format:
    eaiou_pk_<24 url-safe base64 chars>

Usage in the MCP server:
    export CHECKSUBMIT_PARTNER_KEY=eaiou_pk_<the-key>

Compliance:
* Partner keys live in the eaiou_partner_keys table (migration_007).
* Each call increments last_used_at; revocation is via revoked_at timestamp.
* The marketplace router validates the key on every request that arrives with
  the X-Partner-Key header.

Example:
    $ python scripts/mint_partner_key.py --name "checksubmit MCP self-test" --rate 60
    Partner key minted.

      partner_key_id: 7c4f9e2a-1b0d-4a5b-8c6d-3e8f9a2b1c4d
      display_name:   checksubmit MCP self-test
      prefix:         eaiou_pk_a8f3
      rate_limit:     60 / minute
      wholesale:      False

      RAW KEY (save this immediately — it will not be shown again):

        eaiou_pk_a8f3kj29Fl0vDE85ks7sLqW

    Add to your .env or environment:

        CHECKSUBMIT_PARTNER_KEY=eaiou_pk_a8f3kj29Fl0vDE85ks7sLqW
"""

import argparse
import hashlib
import secrets
import sys
import uuid
from pathlib import Path

EAIOU_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EAIOU_ROOT))

from sqlalchemy import text
from app.database import SessionLocal  # noqa: E402


def generate_raw_key() -> tuple[str, str]:
    """
    Generate a partner key.

    Returns (raw_key, prefix) where:
      raw_key is the full secret (eaiou_pk_<24 url-safe chars>)
      prefix is "eaiou_pk_<first-4-chars-of-suffix>" for visible identification
    """
    suffix = secrets.token_urlsafe(18)  # ~24 url-safe chars
    raw_key = f"eaiou_pk_{suffix}"
    prefix = raw_key[:13]  # eaiou_pk_ + 4 chars
    return raw_key, prefix


def mint(name: str, wholesale: bool = False, rate_limit: int | None = None) -> dict:
    """
    Insert a new partner key row and return the metadata + raw key.

    The caller must save the raw key immediately; it is NEVER stored in the DB.
    """
    raw_key, prefix = generate_raw_key()
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    partner_key_id = str(uuid.uuid4())

    with SessionLocal() as session:
        session.execute(text("""
            INSERT INTO `#__eaiou_partner_keys`
              (partner_key_id, display_name, key_hash, prefix,
               active, rate_limit_per_minute, wholesale_pricing)
            VALUES (:pkid, :name, :key_hash, :prefix,
                    1, :rate_limit, :wholesale)
        """), {
            "pkid": partner_key_id,
            "name": name,
            "key_hash": key_hash,
            "prefix": prefix,
            "rate_limit": rate_limit,
            "wholesale": 1 if wholesale else 0,
        })
        session.commit()

    return {
        "partner_key_id": partner_key_id,
        "display_name": name,
        "prefix": prefix,
        "rate_limit_per_minute": rate_limit,
        "wholesale_pricing": wholesale,
        "raw_key": raw_key,
    }


def main():
    parser = argparse.ArgumentParser(description="Mint a new checksubmit partner key.")
    parser.add_argument("--name", required=True, help="Human-readable name for this key (visible in admin logs)")
    parser.add_argument("--wholesale", action="store_true",
                        help="Bill at wholesale rates (default: retail)")
    parser.add_argument("--rate", type=int, default=None,
                        help="Rate limit (calls per minute). Default: unlimited.")
    args = parser.parse_args()

    info = mint(args.name, wholesale=args.wholesale, rate_limit=args.rate)

    print()
    print("Partner key minted.")
    print()
    print(f"  partner_key_id: {info['partner_key_id']}")
    print(f"  display_name:   {info['display_name']}")
    print(f"  prefix:         {info['prefix']}")
    print(f"  rate_limit:     {info['rate_limit_per_minute'] or 'unlimited'}")
    print(f"  wholesale:      {info['wholesale_pricing']}")
    print()
    print("  RAW KEY (save this immediately — it will not be shown again):")
    print()
    print(f"    {info['raw_key']}")
    print()
    print("  Add to your .env or environment:")
    print()
    print(f"    CHECKSUBMIT_PARTNER_KEY={info['raw_key']}")
    print()


if __name__ == "__main__":
    main()
