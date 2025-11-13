"""Optional structured data extraction (JSON-LD JobPosting).

This module is resilient to missing optional dependencies (`extruct`, `w3lib`).
If they are not installed, `extract_jobposting` returns an empty list instead
of raising ImportError so the rest of the application can continue working.
"""

import requests
try:  # optional dependency
    import extruct  # type: ignore
except ImportError:  # pragma: no cover
    extruct = None  # sentinel

try:  # optional dependency
    from w3lib.html import get_base_url  # type: ignore
except ImportError:  # pragma: no cover
    def get_base_url(html: str, url: str) -> str:  # fallback – just return original url
        return url

from ..schemas import JobItem


def extract_jobposting(url: str, ua: str) -> list[JobItem]:
    """Extract JSON-LD JobPosting data from a page (single HTTP GET).

    Returns an empty list if optional parsing dependencies are missing.
    """
    if extruct is None:  # gracefully degrade when extruct not installed
        return []

    r = requests.get(url, headers={"User-Agent": ua}, timeout=15)
    r.raise_for_status()
    base = get_base_url(r.text, r.url)
    try:
        data = extruct.extract(r.text, base_url=base, syntaxes=["json-ld"])  # type: ignore[attr-defined]
    except Exception:
        return []

    jobs: list[JobItem] = []
    for item in data.get("json-ld", []) if isinstance(data, dict) else []:
        if isinstance(item, dict):
            types = item.get("@type")
            # @type can be a string or list; normalise
            if isinstance(types, list):
                is_job = "JobPosting" in types
            else:
                is_job = types == "JobPosting"
            if not is_job:
                continue
            title = str(item.get("title") or "").strip() or "(untitled)"
            company = (item.get("hiringOrganization") or {}).get("name") or None
            location = (item.get("jobLocation") or {}).get("address", {}).get("addressLocality") or None
            jobs.append(JobItem(
                source="generic",
                company=company,
                title=title,
                location=location,
                link=url,
            ))
    return jobs
