from typing import List
from ..schemas import DiscoverRequest, JobPosting


# ⚠️ Stub implementation — replace with your real logic later.
# Keep it simple to verify the stack works both locally & in Codespaces.


def discover_jobs(payload: DiscoverRequest) -> List[JobPosting]:
# Example static data to prove the API works
sample = [
JobPosting(
title="Network & Security Engineer",
company="Example Pty Ltd",
url="https://example.com/jobs/123",
location="Melbourne, VIC",
summary="Implement network security controls and automate monitoring."
),
JobPosting(
title="Cybersecurity Analyst",
company="Contoso AU",
url="https://contoso.example/jobs/42",
location="Geelong, VIC",
summary="Blue team monitoring, SIEM tuning, threat intel enrichment."
),
]
# In the future, use payload.query / payload.locations / payload.sources
return sample