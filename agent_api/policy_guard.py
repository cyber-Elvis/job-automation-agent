import time, random, urllib.robotparser
from urllib.parse import urljoin
import yaml

class PolicyGuard:
    def __init__(self, policy_file="site_policy.yaml", user_agent=None):
        self.cfg = yaml.safe_load(open(policy_file, "r"))
        self.ua = user_agent or self.cfg["default"]["user_agent"]
        self.last_req = {}
        self.err_count = {}

    def site_rule(self, domain):
        return (self.cfg.get("sites", {}) or {}).get(domain, self.cfg["default"])

    def can_fetch(self, base_url, path="/"):
        robots_url = urljoin(base_url, "/robots.txt")
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
        except Exception:
            return True
        return rp.can_fetch(self.ua, urljoin(base_url, path))

    def polite_wait(self, domain):
        rule = self.site_rule(domain)
        dmin, dmax = rule["delay_seconds"]
        now = time.time()
        last = self.last_req.get(domain, 0)
        wait_for = max(0, dmin - (now - last))
        if wait_for > 0:
            time.sleep(wait_for)
        time.sleep(random.uniform(0, dmax - dmin))
        self.last_req[domain] = time.time()

    def allowed(self, domain):
        return self.site_rule(domain).get("allowed", True)

    def headers(self):
        return {"User-Agent": self.ua, "Accept": "text/html,application/json"}

    def note_error(self, domain, code_or_flag):
        self.err_count[domain] = self.err_count.get(domain, 0) + 1
        if str(code_or_flag) in self.site_rule(domain).get("stop_on", []):
            return False
        if self.err_count[domain] >= self.site_rule(domain)["max_consecutive_errors"]:
            return False
        return True
