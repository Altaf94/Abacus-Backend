#!/usr/bin/env python3
"""Batch register users to the local Django server.

This script derives `username`, `first_name`, `last_name` from the email
local-part. The password is set equal to the derived `username` (as requested).
It uses urllib to avoid extra dependencies.
"""
import json
import re
import urllib.request

URL = "http://127.0.0.1:8000/api/auth/register/"

EMAILS = [
    "alishbauzair20@gmail.com",
    "anoushakhan55@gmail.com",
    "eruummsheikh@gmail.com",
    "syedfari99@gmail.com",
    "heranaz99@gmail.com",
    "inaarasultan@gmail.com",
    "nadeemnimra539@gmail.com",
]


def derive_names(localpart: str):
    # split on anything that's not a letter
    parts = [p for p in re.split(r'[^A-Za-z]+', localpart) if p]
    first = parts[0].capitalize() if parts else "User"
    last = parts[1].capitalize() if len(parts) > 1 else "User"
    username = localpart.replace('.', '')
    return username, first, last


def derive_roll(localpart: str):
    # try to extract digits from localpart
    m = re.search(r'(\d+)', localpart)
    if m:
        return m.group(1)
    # fallback: hash to a 4-digit number
    import hashlib
    h = hashlib.sha256(localpart.encode('utf-8')).hexdigest()
    return str(int(h[:8], 16) % 10000)


def register(email: str):
    localpart = email.split('@', 1)[0]
    username, first_name, last_name = derive_names(localpart)
    password = username
    roll_number = derive_roll(localpart)
    # default class_section; change if you have a specific mapping
    class_section = "A"

    payload = {
        "username": username,
        "email": email,
        "password": password,
        "confirm_password": password,
        "first_name": first_name,
        "last_name": last_name,
        "role": "student",
        "class_section": class_section,
        "roll_number": roll_number,
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode('utf-8')
            try:
                parsed = json.loads(body)
                print(f"✓ {email} HTTP {resp.status}")
                print(json.dumps(parsed, indent=2))
            except Exception:
                print(f"✓ {email} HTTP {resp.status} (non-JSON response)")
                print(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"✗ {email} HTTP {e.code}")
        print(err_body)
    except Exception as e:
        print(f"✗ {email} Error: {e}")


if __name__ == '__main__':
    for e in EMAILS:
        register(e)
        print()
