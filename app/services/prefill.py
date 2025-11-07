from ..schemas import PrefillRequest, PrefillResponse


# ⚠️ Stub implementation — replace with form parsing + LLM enrichment, etc.


def prefill_application(payload: PrefillRequest) -> PrefillResponse:
	# Pretend we scraped the job URL and mapped fields
	fields = {
		"full_name": "Elvis N.",
		"email": "elvis@example.com",
		"cover_letter_intro": (
			"I am a Network & Cybersecurity Engineer with experience in Wazuh, MISP, "
			"Graylog, and Azure. I’m excited about the opportunity to contribute to your team."
		),
		"key_skills": ["Wazuh", "MISP", "Graylog", "Azure", "FastAPI", "Kubernetes"],
	}
	return PrefillResponse(status="ok", fields=fields)