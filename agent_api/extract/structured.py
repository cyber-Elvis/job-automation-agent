import extruct, requests
from w3lib.html import get_base_url
from ..models import Job

def extract_jobposting(url: str, ua: str) -> list[Job]:
    """
    Extract JSON-LD JobPosting data from a page (policy-safe: single page fetch).
    Returns a list[Job] (usually 1).
    """
    r = requests.get(url, headers={"User-Agent": ua}, timeout=15)
    r.raise_for_status()
    base = get_base_url(r.text, r.url)
    data = extruct.extract(r.text, base_url=base, syntaxes=["json-ld"])
    jobs = []
    for item in data.get("json-ld", []):
        if isinstance(item, dict) and item.get("@type") in ("JobPosting", ["JobPosting"]):
            title = item.get("title")
            company = (item.get("hiringOrganization") or {}).get("name")
            location = (item.get("jobLocation") or {}).get("address", {}).get("addressLocality")
            jobs.append(Job(
                source="generic",
                company=company,
                title=title,
                location=location,
                url=url,
                raw=item
            ))
    return jobs
