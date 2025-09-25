#!/usr/bin/env python3

import argparse
import csv
import os
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

# -----------------------------------------------------------------------------
# User-configurable defaults (fill these to avoid passing flags/env)
# -----------------------------------------------------------------------------
DEFAULT_SITE1_URL = "https://norstella.atlassian.net"
DEFAULT_EMAIL1 = "prashant.sultania@norstella.com"
DEFAULT_TOKEN1 = "ATATT3xFfGF0Q_683onZ7lobj9RU9A0XO5vOhW7nb0VInnwwdipC8QRMELFeOG3hKxybivsPoO4XWLVav5UmfgpCj1nxxezH-_b8YocO4N6mqb2CkjqdfR1nsaSU4iUWQgn82xBB9MoLWNGU-7i_7ozRgxeC4KGbpIrW4wpAyFDQaL33bCOMyzM=0842432F"

DEFAULT_SITE2_URL = "https://evaluateltd.atlassian.net"
DEFAULT_EMAIL2 = "prashant.sultania@norstella.com"
DEFAULT_TOKEN2 = "ATATT3xFfGF0Q_683onZ7lobj9RU9A0XO5vOhW7nb0VInnwwdipC8QRMELFeOG3hKxybivsPoO4XWLVav5UmfgpCj1nxxezH-_b8YocO4N6mqb2CkjqdfR1nsaSU4iUWQgn82xBB9MoLWNGU-7i_7ozRgxeC4KGbpIrW4wpAyFDQaL33bCOMyzM=0842432F"

# If non-empty, used when --output-dir is not specified
DEFAULT_OUTPUT_DIR = ""

# If None, falls back to flags/env; otherwise True/False
DEFAULT_VERIFY_SSL: Optional[bool] = None


def parse_bool_env(var_name: str, default: bool = True) -> bool:
    value = os.environ.get(var_name)
    if value is None:
        return default
    value_lower = value.strip().lower()
    return value_lower in {"1", "true", "yes", "y"}


def coalesce(*values: Optional[str]) -> Optional[str]:
    for v in values:
        if v is not None and str(v).strip() != "":
            return v
    return None


def normalize_base_url(raw_url: str) -> str:
    url = raw_url.strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def host_slug_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc or url
    safe = host.replace(".", "-")
    return safe


def jira_request(
    method: str,
    url: str,
    auth: Tuple[str, str],
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    verify_ssl: bool = True,
    max_retries: int = 3,
) -> requests.Response:
    session = requests.Session()
    attempt = 0
    last_exc: Optional[Exception] = None

    while attempt <= max_retries:
        try:
            resp = session.request(method, url, auth=auth, headers=headers, params=params, timeout=60, verify=verify_ssl)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "2"))
                time.sleep(retry_after)
                attempt += 1
                continue
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            attempt += 1
            if attempt > max_retries:
                break
            time.sleep(2 * attempt)

    assert last_exc is not None
    raise last_exc


def fetch_active_custom_fields(
    base_url: str,
    email: str,
    api_token: str,
    verify_ssl: bool = True,
) -> List[Dict[str, str]]:
    base_url = normalize_base_url(base_url)

    # Prefer /field/search for pagination and richer metadata
    start_at = 0
    max_results = 200
    more = True

    headers = {"Accept": "application/json"}
    auth = (email, api_token)

    results: List[Dict[str, str]] = []

    while more:
        params = {
            "startAt": str(start_at),
            "maxResults": str(max_results),
            "type": "custom",
            "orderBy": "name",
        }
        url = f"{base_url}/rest/api/3/field/search"
        resp = jira_request("GET", url, auth=auth, headers=headers, params=params, verify_ssl=verify_ssl)
        data = resp.json()

        values = data.get("values", data.get("fields", []))
        if not isinstance(values, list):
            values = []

        for field in values:
            schema = field.get("schema") or {}
            is_custom = bool(schema.get("custom")) or bool(field.get("custom", False))
            # Defensive checks for trash/inactive flags. Jira Cloud may expose these flags depending on rollout.
            trashed_flags = [
                field.get("isTrashed"),
                field.get("trashed"),
                field.get("deleted"),
                field.get("isDeleted"),
            ]
            inactive_flags = [
                field.get("isInactive"),
                field.get("inactive"),
                field.get("archived"),
                field.get("isArchived"),
            ]

            is_trashed = any(bool(x) for x in trashed_flags)
            is_inactive = any(bool(x) for x in inactive_flags)

            if not is_custom:
                continue
            if is_trashed or is_inactive:
                continue

            field_type = schema.get("custom") or schema.get("type") or ""
            results.append(
                {
                    "name": field.get("name", ""),
                    "status": "Active",
                    "type": field_type,
                    "customfield_id": field.get("id", ""),
                }
            )

        total = data.get("total")
        if total is None:
            # If no total provided, continue until a short page is received
            more = len(values) == max_results
            start_at += max_results
        else:
            start_at += len(values)
            more = start_at < int(total)

        # Fallback: If /field/search is unavailable, try /field once (no pagination)
        if start_at == 0 and len(values) == 0 and total in (None, 0):
            fallback_url = f"{base_url}/rest/api/3/field"
            resp2 = jira_request("GET", fallback_url, auth=auth, headers=headers, params=None, verify_ssl=verify_ssl)
            arr = resp2.json()
            if isinstance(arr, list):
                for field in arr:
                    schema = field.get("schema") or {}
                    is_custom = bool(schema.get("custom")) or bool(field.get("custom", False))
                    trashed_flags = [
                        field.get("isTrashed"),
                        field.get("trashed"),
                        field.get("deleted"),
                        field.get("isDeleted"),
                    ]
                    inactive_flags = [
                        field.get("isInactive"),
                        field.get("inactive"),
                        field.get("archived"),
                        field.get("isArchived"),
                    ]
                    if not is_custom:
                        continue
                    if any(bool(x) for x in trashed_flags) or any(bool(x) for x in inactive_flags):
                        continue
                    field_type = schema.get("custom") or schema.get("type") or ""
                    results.append(
                        {
                            "name": field.get("name", ""),
                            "status": "Active",
                            "type": field_type,
                            "customfield_id": field.get("id", ""),
                        }
                    )
            break

    # Ensure unique by name/id (some sites may have duplicates due to contexts; keep first occurrence)
    unique_by_id: Dict[str, Dict[str, str]] = {}
    for item in results:
        cid = item.get("customfield_id", "")
        if cid and cid not in unique_by_id:
            unique_by_id[cid] = item
    return list(unique_by_id.values())


def write_fields_csv(fields: List[Dict[str, str]], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    headers = ["name", "status", "type", "customfield_id"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in fields:
            writer.writerow({h: row.get(h, "") for h in headers})


def read_fields_csv(path: str) -> Dict[str, Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        result: Dict[str, Dict[str, str]] = {}
        for row in reader:
            name = row.get("name") or ""
            if name not in result:
                result[name] = row
        return result


def write_comparison_csv(
    site1_name: str,
    site2_name: str,
    site1_fields: Dict[str, Dict[str, str]],
    site2_fields: Dict[str, Dict[str, str]],
    output_path: str,
) -> None:
    headers = [
        "name",
        f"{site1_name}_status",
        f"{site1_name}_type",
        f"{site1_name}_customfield_id",
        f"{site2_name}_status",
        f"{site2_name}_type",
        f"{site2_name}_customfield_id",
    ]

    all_names = set(site1_fields.keys()) | set(site2_fields.keys())

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for name in sorted(all_names, key=lambda s: s.lower()):
            r1 = site1_fields.get(name)
            r2 = site2_fields.get(name)
            row = {"name": name}
            if r1:
                row[f"{site1_name}_status"] = r1.get("status", "")
                row[f"{site1_name}_type"] = r1.get("type", "")
                row[f"{site1_name}_customfield_id"] = r1.get("customfield_id", "")
            else:
                row[f"{site1_name}_status"] = "Not Present"
                row[f"{site1_name}_type"] = "Not Present"
                row[f"{site1_name}_customfield_id"] = "Not Present"

            if r2:
                row[f"{site2_name}_status"] = r2.get("status", "")
                row[f"{site2_name}_type"] = r2.get("type", "")
                row[f"{site2_name}_customfield_id"] = r2.get("customfield_id", "")
            else:
                row[f"{site2_name}_status"] = "Not Present"
                row[f"{site2_name}_type"] = "Not Present"
                row[f"{site2_name}_customfield_id"] = "Not Present"

            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch active Jira custom fields from two sites and compare by field name."
    )
    parser.add_argument("--site1", help="Base URL for Jira site 1, e.g. https://your1.atlassian.net")
    parser.add_argument("--site2", help="Base URL for Jira site 2, e.g. https://your2.atlassian.net")

    parser.add_argument("--email1", help="Email for Jira site 1 (or set JIRA_EMAIL1)")
    parser.add_argument("--token1", help="API token for Jira site 1 (or set JIRA_TOKEN1)")
    parser.add_argument("--email2", help="Email for Jira site 2 (or set JIRA_EMAIL2)")
    parser.add_argument("--token2", help="API token for Jira site 2 (or set JIRA_TOKEN2)")

    # Use None so we can detect if the user didn't pass the flag and allow DEFAULT_OUTPUT_DIR to apply
    parser.add_argument("--output-dir", default=None, help="Directory to write CSVs (default: current directory)")

    # Defer default resolution so DEFAULT_VERIFY_SSL can apply if neither flag/env is set
    parser.add_argument("--verify-ssl", action="store_true", default=None, help="Verify SSL certificates")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL verification")

    args = parser.parse_args()

    site1 = coalesce(
        args.site1,
        os.environ.get("JIRA_SITE1_URL"),
        DEFAULT_SITE1_URL,
    )
    site2 = coalesce(
        args.site2,
        os.environ.get("JIRA_SITE2_URL"),
        DEFAULT_SITE2_URL,
    )
    if not site1 or not site2:
        print("Error: Both --site1 and --site2 (or JIRA_SITE1_URL/JIRA_SITE2_URL or DEFAULT_* variables) are required.", file=sys.stderr)
        return 2

    email1 = coalesce(args.email1, os.environ.get("JIRA_EMAIL1"), os.environ.get("JIRA_EMAIL"), DEFAULT_EMAIL1)
    token1 = coalesce(args.token1, os.environ.get("JIRA_TOKEN1"), os.environ.get("JIRA_API_TOKEN"), DEFAULT_TOKEN1)
    email2 = coalesce(args.email2, os.environ.get("JIRA_EMAIL2"), os.environ.get("JIRA_EMAIL"), DEFAULT_EMAIL2)
    token2 = coalesce(args.token2, os.environ.get("JIRA_TOKEN2"), os.environ.get("JIRA_API_TOKEN"), DEFAULT_TOKEN2)

    if not email1 or not token1 or not email2 or not token2:
        print("Error: Missing credentials. Provide --email1/--token1 and --email2/--token2 or set env vars or DEFAULT_* variables in the script.", file=sys.stderr)
        return 2

    # Resolve SSL verification preference
    if args.no_verify_ssl:
        verify_ssl = False
    elif args.verify_ssl is True:
        verify_ssl = True
    else:
        # Neither flag set; use env if present, else DEFAULT_VERIFY_SSL, else True
        if os.environ.get("JIRA_VERIFY_SSL") is not None:
            verify_ssl = parse_bool_env("JIRA_VERIFY_SSL", True)
        elif DEFAULT_VERIFY_SSL is not None:
            verify_ssl = bool(DEFAULT_VERIFY_SSL)
        else:
            verify_ssl = True

    site1_url = normalize_base_url(site1)
    site2_url = normalize_base_url(site2)

    site1_slug = host_slug_from_url(site1_url)
    site2_slug = host_slug_from_url(site2_url)

    output_dir = coalesce(args.output_dir, DEFAULT_OUTPUT_DIR) or "."

    os.makedirs(output_dir, exist_ok=True)
    site1_csv = os.path.join(output_dir, f"{site1_slug}_fields.csv")
    site2_csv = os.path.join(output_dir, f"{site2_slug}_fields.csv")
    compare_csv = os.path.join(output_dir, f"fields_comparison_{site1_slug}_vs_{site2_slug}.csv")

    print(f"Fetching active custom fields from {site1_url} ...")
    fields1 = fetch_active_custom_fields(site1_url, email1, token1, verify_ssl=verify_ssl)
    write_fields_csv(fields1, site1_csv)
    print(f"Wrote: {site1_csv} ({len(fields1)} fields)")

    print(f"Fetching active custom fields from {site2_url} ...")
    fields2 = fetch_active_custom_fields(site2_url, email2, token2, verify_ssl=verify_ssl)
    write_fields_csv(fields2, site2_csv)
    print(f"Wrote: {site2_csv} ({len(fields2)} fields)")

    site1_rows = read_fields_csv(site1_csv)
    site2_rows = read_fields_csv(site2_csv)

    print("Generating comparison by field name ...")
    write_comparison_csv(site1_slug, site2_slug, site1_rows, site2_rows, compare_csv)
    print(f"Wrote: {compare_csv}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
