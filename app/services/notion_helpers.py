from typing import List
import os
import requests

# Lightweight Notion helpers so this module can operate standalone.
NOTION_API = os.getenv("NOTION_API", "https://api.notion.com/v1")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_VER = os.getenv("NOTION_VER", "2022-06-28")


def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json",
    }


def notion_get_page(page_id: str):
    r = requests.get(f"{NOTION_API}/pages/{page_id}", headers=notion_headers(), timeout=15)
    if r.status_code >= 400:
        raise RuntimeError(f"Notion get page failed: {r.status_code} {r.text}")
    return r.json()


def notion_update_page(page_id: str, props: dict):
    url = f"{NOTION_API}/pages/{page_id}"
    r = requests.patch(url, headers=notion_headers(), json={"properties": props}, timeout=20)
    if r.status_code >= 400:
        raise RuntimeError(f"Notion update failed: {r.status_code} {r.text}")
    return r.json()


def safe_set_props(page_id: str, props: dict) -> bool:
    """Wrapper around the low-level update that returns True/False on success."""
    try:
        notion_update_page(page_id, props)
        return True
    except Exception:
        return False


def relation_append(page_id: str, prop_name: str, new_ids: List[str]) -> bool:
    """
    Append relation IDs to a Notion page's relation property without clobbering existing ones.

    Returns True on success, False on failure.
    """
    try:
        page = notion_get_page(page_id)
        props = (page or {}).get("properties", {})
        rel = props.get(prop_name, {})
        if rel.get("type") != "relation":
            return False

        existing = rel.get("relation", []) or []
        existing_ids = {r.get("id") for r in existing if isinstance(r, dict) and r.get("id")}
        to_add = [{"id": rid} for rid in new_ids if rid and rid not in existing_ids]
        if not to_add:
            return True  # nothing to add

        return safe_set_props(page_id, {prop_name: {"relation": existing + to_add}})
    except Exception:
        return False
