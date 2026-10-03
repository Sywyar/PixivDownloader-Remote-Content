#!/usr/bin/env python3
"""检测公告索引是否临期，并只更新序号与有效期。签名由既有 CLI 完成。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from validate_content import INDEX_PATH, MAX_INDEX_VALIDITY, ValidationError, load_index_bytes, require, utc_timestamp


RENEWAL_WINDOW = timedelta(days=7)
VALIDITY = timedelta(days=30)
MAX_CLOCK_SKEW = timedelta(minutes=10)
MAX_SEQUENCE = 2**63 - 1


def renewal(index: dict, now: datetime) -> dict | None:
    sequence = index.get("sequence")
    require(isinstance(sequence, int) and not isinstance(sequence, bool)
            and 0 < sequence < MAX_SEQUENCE, "index.json: sequence cannot be renewed")
    generated = utc_timestamp(index.get("generatedAt"), "generatedAt")
    expires = utc_timestamp(index.get("expiresAt"), "expiresAt")
    require(generated < expires <= generated + MAX_INDEX_VALIDITY,
            "index.json: invalid validity window")
    require(generated <= now + MAX_CLOCK_SKEW, "index.json: generatedAt is in the future")
    if expires - now > RENEWAL_WINDOW:
        return None
    generated = now.astimezone(timezone.utc).replace(microsecond=0)
    return {**index, "sequence": sequence + 1,
            "generatedAt": generated.isoformat().replace("+00:00", "Z"),
            "expiresAt": (generated + VALIDITY).isoformat().replace("+00:00", "Z")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write the renewal after signature verification")
    parser.add_argument("--github-output", type=Path, help="Append the renewal decision to GITHUB_OUTPUT")
    args = parser.parse_args()
    try:
        candidate = renewal(load_index_bytes(INDEX_PATH.read_bytes(), "index.json"),
                            datetime.now(timezone.utc))
        if candidate is not None and args.write:
            INDEX_PATH.write_bytes((json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as output:
                output.write(f"due={str(candidate is not None).lower()}\n")
        print("Announcement renewal is due." if candidate else "Announcement renewal is not due.")
    except (OSError, ValidationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
