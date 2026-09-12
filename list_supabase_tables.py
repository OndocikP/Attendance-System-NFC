import os
from typing import List, Set

import requests
from dotenv import load_dotenv


def get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


def fetch_table_names(supabase_url: str, api_key: str) -> List[str]:
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/openapi+json",
    }

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


def call_new_log(supabase_url: str, api_key: str, user_id: str, log_text: str) -> None:
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/rpc/new_log"
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "p_card_uid": user_id,
        "p_text": log_text,
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
    response.raise_for_status()
    print("Successfully called public.new_log")
    if response.content:
        try:
            print("RPC result:", response.json())
        except ValueError:
            print("RPC result:", response.text)
    else:
        print("RPC result: <empty response>")


def main() -> None:
    load_dotenv()

    supabase_url = get_env("SUPABASE_URL")
    api_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SERVICE_ROL") or os.getenv("SUPABASE_PUBLISHABLE_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing API key. Set SUPABASE_SECRET_KEY or SERVICE_ROL or SUPABASE_PUBLISHABLE_KEY in .env"
        )

    tables = fetch_table_names(supabase_url, api_key)

    if not tables:
        print("No table endpoints were found in the exposed Supabase REST schema.")
        return

    print("Supabase table names:")
    for name in tables:
        print(f"- {name}")

    call_new_log(
        supabase_url=supabase_url,
        api_key=api_key,
        user_id="550e8400-e29b-41d4-a716-446655440000",
        log_text="Python test",
    )


if __name__ == "__main__":
    main()
