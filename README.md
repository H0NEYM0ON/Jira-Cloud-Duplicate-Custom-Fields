
<div align="center"><img width="141" height="164" alt="Jira_attribution_center_light" src="https://github.com/user-attachments/assets/817dc1da-8c48-46dd-a61f-b9e01ccfc1ce" /></div>

# Jira Cloud custom fields fetch and compare

This tool fetches active (not trashed/inactive) custom fields from two Jira Cloud sites, writes one CSV per site, and creates a comparison CSV by field name.

- Per-site CSV columns: `name`, `status`, `type`, `customfield_id`
- Comparison CSV columns: `name`, `<site1>_status`, `<site1>_type`, `<site1>_customfield_id`, `<site2>_status`, `<site2>_type`, `<site2>_customfield_id`

The script calls Jira Cloud `/rest/api/3/field/search` (paginated). If unavailable, it falls back to `/rest/api/3/field`. It includes only custom fields and defensively filters out trashed/inactive ones when flags are present in your site.

# Requirements

- Python 3.9+
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Configuration

You can configure the two Jira sites and credentials in three ways. The script uses this precedence (top wins):

1) CLI flags
2) Environment variables
3) In-file defaults defined at the top of `jira_fields_compare.py`

### In-file defaults (easy for one-off use)
Edit these variables near the top of `jira_fields_compare.py` and fill in your values:
- `DEFAULT_SITE1_URL`, `DEFAULT_EMAIL1`, `DEFAULT_TOKEN1`
- `DEFAULT_SITE2_URL`, `DEFAULT_EMAIL2`, `DEFAULT_TOKEN2`
- Optional: `DEFAULT_OUTPUT_DIR` (folder where CSVs are written)
- Optional: `DEFAULT_VERIFY_SSL` (True/False). If left as `None`, normal flag/env behavior applies.

Note: Avoid committing API tokens to version control. Prefer environment variables for security in shared repos.

### Environment variables (fallback when flags are omitted)
- `JIRA_SITE1_URL`, `JIRA_SITE2_URL`
- `JIRA_EMAIL1`, `JIRA_TOKEN1`
- `JIRA_EMAIL2`, `JIRA_TOKEN2`
- Or shared defaults: `JIRA_EMAIL`, `JIRA_API_TOKEN`
- SSL verify override: `JIRA_VERIFY_SSL` ("true"/"false")

Generate an API token at Atlassian: `https://id.atlassian.com/manage-profile/security/api-tokens`.

### CLI flags (highest precedence)
- `--site1`, `--site2`: Jira base URLs, e.g. `https://example.atlassian.net`
- `--email1`, `--token1`: Email and API token for site 1
- `--email2`, `--token2`: Email and API token for site 2
- `--output-dir`: Directory for generated CSVs (defaults to current directory if not set anywhere)
- `--verify-ssl` / `--no-verify-ssl`: Force SSL verification on/off

## Usage (Windows PowerShell)

### 1) Setup (recommended: virtual environment)
```powershell
cd "C:\Duplicate Custom fields"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2) Run the script
- If you edited in-file defaults, you can just run:
```powershell
python .\jira_fields_compare.py --output-dir .
```

- Example with flags:
```powershell
python .\jira_fields_compare.py `
  --site1 https://your-first.atlassian.net `
  --email1 you@example.com `
  --token1 <API_TOKEN_1> `
  --site2 https://your-second.atlassian.net `
  --email2 you@example.com `
  --token2 <API_TOKEN_2> `
  --output-dir .
```

- Example with environment variables:
```powershell
$env:JIRA_SITE1_URL = "https://your-first.atlassian.net"
$env:JIRA_EMAIL1 = "you@example.com"
$env:JIRA_TOKEN1 = "<API_TOKEN_1>"
$env:JIRA_SITE2_URL = "https://your-second.atlassian.net"
$env:JIRA_EMAIL2 = "you@example.com"
$env:JIRA_TOKEN2 = "<API_TOKEN_2>"
python .\jira_fields_compare.py --output-dir .
```

### 3) Outputs
- `<site1-host>_fields.csv`
- `<site2-host>_fields.csv`
- `fields_comparison_<site1-host>_vs_<site2-host>.csv`

You should see console messages like:
- `Fetching active custom fields from https://...`
- `Wrote: <site>_fields.csv (N fields)`
- `Wrote: fields_comparison_<site1>_vs_<site2>.csv`

## Troubleshooting

- Path quoting / WinError 123:
  - Use balanced quotes and avoid a trailing unmatched quote or stray backslash.
  - Good examples:
```powershell
python .\jira_fields_compare.py --output-dir .
python .\jira_fields_compare.py --output-dir "C:\Duplicate Custom fields"
python .\jira_fields_compare.py --output-dir "C:\Duplicate Custom fields\Output"
```

- Missing dependency: `ModuleNotFoundError: No module named 'requests'`
  - Ensure you installed requirements into the same interpreter you run with:
```powershell
python -m pip install -r requirements.txt
python -c "import sys; print(sys.executable)"
python -m pip --version
```

- 401/403 errors (auth):
  - Verify the site URL, email, and API token belong to the same site.
  - Recreate the token if unsure and re-run.

- 429 Too Many Requests (rate limiting):
  - The script retries with backoff automatically. Re-run later if needed.

- SSL verification problems:
  - Try `--no-verify-ssl` (not recommended for production).

- Proxy environments:
  - Set `HTTPS_PROXY`/`HTTP_PROXY` environment variables if your network requires a proxy.

## Notes

- The script uses `/rest/api/3/field/search` when available, falling back to `/rest/api/3/field`.
- Only custom fields are included. Known trash/inactive flags are filtered defensively if present.
- Rate limits (HTTP 429) are handled with retry.





