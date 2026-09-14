import os
from typing import Dict, List, Set

import requests
from dotenv import load_dotenv


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def get_api_key() -> str:
    key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SERVICE_ROL") or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    if not key:
        raise RuntimeError(
            "Missing API key. Set SUPABASE_SECRET_KEY or SERVICE_ROL or SUPABASE_PUBLISHABLE_KEY in .env"
        )
    return key


def build_headers(api_key: str) -> Dict[str, str]:
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
    }


def fetch_table_names(supabase_url: str, api_key: str) -> List[str]:
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/"
    headers = {**build_headers(api_key), "Accept": "application/openapi+json"}

    response = requests.get(endpoint, headers=headers, timeout=20)
    response.raise_for_status()

    spec = response.json()
    paths = spec.get("paths", {})

    table_names: Set[str] = set()
    for raw_path in paths:
        cleaned = raw_path.strip("/")
        if not cleaned:
            continue

        first_segment = cleaned.split("/")[0]
        if first_segment == "rpc":
            continue

        table_name = first_segment.split("(")[0].strip()
        if table_name:
            table_names.add(table_name)

    return sorted(table_names)


def fetch_rows(supabase_url: str, api_key: str, table_name: str, limit: int) -> List[Dict[str, object]]:
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/{table_name}"
    headers = build_headers(api_key)
    params = {
        "select": "*",
        "limit": str(limit),
    }

    response = requests.get(endpoint, headers=headers, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        return data
    return []


def main() -> None:
    load_dotenv()

    supabase_url = get_env("SUPABASE_URL")
    api_key = get_api_key()

    table_name = os.getenv("SUPABASE_TABLE")
    limit_raw = os.getenv("SUPABASE_LIMIT", "10")
    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 10
    limit = max(1, min(limit, 500))

    if not table_name:
        tables = fetch_table_names(supabase_url, api_key)
        print("Available tables:")
        for name in tables:
            print(f"- {name}")
        print("\nSet SUPABASE_TABLE in .env and run again to fetch rows.")
        return

    rows = fetch_rows(supabase_url, api_key, table_name, limit)
    print(f"Rows from '{table_name}' (limit {limit}):")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
