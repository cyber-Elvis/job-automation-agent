from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List
from .models import Job, PrefillPayload
from .policy_guard import PolicyGuard
from .collectors import greenhouse, lever, rss_generic
from .extract.structured import extract_jobposting
from urllib.parse import urlparse
import os
app = FastAPI(title=os.getenv("APP_NAME","JobAgent"))
PG = PolicyGuard(user_agent=os.getenv("USER_AGENT", "JobAgent/1.0 (+https://example.com)"))
@app.get("/health")
def health(): return {"ok": True}
@app.get("/discover", response_model=List[Job])
def discover(company: Optional[str] = Query(default=None), lever_company: Optional[str] = None, greenhouse_company: Optional[str] = None, rss_url: Optional[str] = None, page_url: Optional[str] = None, limit: int = 50):
    ua = os.getenv("USER_AGENT", "JobAgent/1.0 (+https://example.com)")
    out: list[Job] = []
    if greenhouse_company: out += greenhouse.fetch(greenhouse_company, ua)
    if lever_company: out += lever.fetch(lever_company, ua)
    if rss_url: out += rss_generic.fetch(rss_url, company, ua)
    if page_url:
        domain = urlparse(page_url).netloc
        if not PG.allowed(domain): raise HTTPException(403, "Domain disallowed by policy.")
        if not PG.can_fetch("https://{0}".format(domain), "/"): raise HTTPException(403, "robots.txt forbids fetching this path.")
        PG.polite_wait(domain); out += extract_jobposting(page_url, ua)
    return out[:limit]
@app.post("/prefill")
def prefill(p: PrefillPayload):
    from .prefill.playwright_prefill import prefill_and_pause
    prefill_and_pause(apply_url=str(p.apply_url), ua=os.getenv("USER_AGENT", "JobAgent/1.0 (+https://example.com)"), fields={"name": p.name, "email": p.email, "phone": p.phone, "resume_path": p.resume_path, "cover_letter": p.cover_letter})
    return {"launched": True, "note": "A headed browser opened for manual review & submit."}
