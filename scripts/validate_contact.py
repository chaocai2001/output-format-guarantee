#!/usr/bin/env python3
"""Validate contact info JSON (name, address, phone) against a pydantic model.

Usage:
    python3 validate_contact.py <file.json>
    echo '{"name": "...", "address": "...", "phone": "..."}' | python3 validate_contact.py

Exit code 0 and prints the normalized JSON on success.
Exit code 1 and prints human-readable validation errors on failure.
"""

import json
import re
import sys

from pydantic import BaseModel, Field, ValidationError, field_validator

PHONE_PATTERN = re.compile(r"^\+?[\d\s\-().]{5,25}$")


class ContactInfo(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=300)
    phone: str

    @field_validator("name", "address", mode="before")
    @classmethod
    def strip_and_check_str(cls, v):
        if not isinstance(v, str):
            raise ValueError("must be a string")
        v = v.strip()
        if not v:
            raise ValueError("must not be empty or whitespace only")
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def check_phone(cls, v):
        if not isinstance(v, str):
            v = str(v)
        v = v.strip()
        if not PHONE_PATTERN.match(v):
            raise ValueError(
                "invalid phone: use 5-25 chars of digits, spaces, '+', '-', '(', ')', '.'"
            )
        if not any(c.isdigit() for c in v):
            raise ValueError("phone must contain at least one digit")
        return v


def main() -> int:
    if len(sys.argv) > 1:
        with open(sys.argv[1], encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"INVALID JSON: {e}")
        return 1

    try:
        contact = ContactInfo.model_validate(data)
    except ValidationError as e:
        print("VALIDATION FAILED:")
        for err in e.errors():
            loc = ".".join(str(p) for p in err["loc"]) or "(root)"
            print(f"  - {loc}: {err['msg']} (got: {err.get('input')!r})")
        return 1

    print("VALID")
    print(contact.model_dump_json(indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
