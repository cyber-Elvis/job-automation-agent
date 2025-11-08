import httpx, re

async def detect_platform(domain_or_url: str) -> str:
    url = domain_or_url if domain_or_url.startswith("http") else f"https://{domain_or_url}"
    async with httpx.AsyncClient(timeout=10) as c:
        try:
            r = await c.get(url, follow_redirects=True)
        except Exception:
            return "generic"
        t = (r.text or "").lower()
        if "boards.greenhouse.io" in t: return "greenhouse"
        if "jobs.lever.co" in t: return "lever"
        if re.search(r"/workday/|/wd\\d?/", t): return "workday"
        return "generic"
