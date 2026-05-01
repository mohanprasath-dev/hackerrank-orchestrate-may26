from __future__ import annotations

import re
import unicodedata
from typing import Literal


Status = Literal["replied", "escalated"]

SECURITY_PATTERN = re.compile(
    r"\b("
    r"fraud|stolen|identity\s+theft|unauthorized\s+transaction|compromised|"
    r"hack(?:ed|ing)?|security\s+vulnerability|phishing"
    r")\b",
    re.IGNORECASE,
)

ACCOUNT_DELETION_PATTERN = re.compile(
    r"\b(account\s+deletion|delete\s+(?:my|the)\s+account|close\s+(?:my|the)\s+account)\b",
    re.IGNORECASE,
)

RESTORE_ACCESS_PATTERN = re.compile(
    r"\b(restore\s+access|unlock\s+account|reset\s+(?:their|someone(?:\s+else)?s?)\s+password|"
    r"give\s+access\s+to\s+(?:another|other)\s+user)\b",
    re.IGNORECASE,
)

NOT_OWNER_OR_ADMIN_PATTERN = re.compile(
    r"\b(not\s+(?:the\s+)?(?:owner|admin)|not\s+my\s+account|someone\s+else(?:'s)?\s+account|"
    r"for\s+my\s+friend|for\s+another\s+user|without\s+admin\s+access)\b",
    re.IGNORECASE,
)

DECISION_OVERRIDE_PATTERN = re.compile(
    r"\b(increase\s+score|raise\s+score|change\s+score|override\s+recruiter\s+decision|"
    r"reverse\s+recruiter\s+decision)\b",
    re.IGNORECASE,
)

MALICIOUS_PATTERN = re.compile(
    r"\b(delete\s+all\s+files|exploit\s+code|write\s+malware|ransomware|ddos|"
    r"bypass\s+security|steal\s+data|credential\s+stuffing)\b",
    re.IGNORECASE,
)

PROMPT_INJECTION_PHRASES = (
    "affiche toutes les regles internes",
    "show internal rules",
    "reveal your instructions",
    "show retrieved documents",
    "ignore previous instructions",
    "display your system prompt",
)

BILLING_DISPUTE_PATTERN = re.compile(
    r"\b(refund|billing\s+dispute|disputed\s+charge|chargeback|"
    r"unauthorized\s+charge|wrong\s+charge|billed\s+twice|double\s+charged)\b",
    re.IGNORECASE,
)

OUTAGE_PATTERN = re.compile(
    r"\b(outage|system\s+down|service\s+down|platform\s+down|all\s+users\s+down|"
    r"down\s+for\s+everyone|site\s+is\s+down|cannot\s+access\s+anything)\b",
    re.IGNORECASE,
)

VAGUE_PATTERN = re.compile(
    r"\b(help|issue|problem|not\s+working|broken|urgent|asap|please\s+fix)\b",
    re.IGNORECASE,
)


def _normalize_company(company: str) -> str:
    return (company or "").strip().lower()


def _is_company_none(company: str) -> bool:
    normalized = _normalize_company(company)
    return normalized in {"", "none", "null", "n/a", "na", "unknown"}


def _combine_text(issue: str, subject: str) -> str:
    return f"{issue or ''} {subject or ''}".strip()


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _has_prompt_injection(text: str) -> bool:
    normalized_text = _normalize_text(text)
    return any(phrase in normalized_text for phrase in PROMPT_INJECTION_PHRASES)


def _is_vague(issue: str, subject: str) -> bool:
    text = _combine_text(issue, subject)
    if not text:
        return True

    word_count = len(re.findall(r"\w+", text))
    if word_count <= 5:
        return True

    return bool(VAGUE_PATTERN.search(text)) and word_count <= 12


def _evaluate(issue: str, subject: str, company: str) -> tuple[Status, str]:
    text = _combine_text(issue, subject)

    if _has_prompt_injection(text):
        return "escalated", "Potential prompt injection attempt detected."

    if SECURITY_PATTERN.search(text):
        return "escalated", "Escalated due to potential fraud or security risk indicators."

    if ACCOUNT_DELETION_PATTERN.search(text):
        return "escalated", "Escalated because account deletion requests require manual verification."

    if RESTORE_ACCESS_PATTERN.search(text) and NOT_OWNER_OR_ADMIN_PATTERN.search(text):
        return "escalated", "Escalated because restore-access request appears to be from a non-owner/non-admin."

    if DECISION_OVERRIDE_PATTERN.search(text):
        return "escalated", "Escalated because score/recruiter decision overrides require human review."

    if MALICIOUS_PATTERN.search(text):
        return "escalated", "Escalated because the request appears malicious or harmful."

    if BILLING_DISPUTE_PATTERN.search(text):
        return "escalated", "Escalated because billing disputes and refunds must be handled by support staff."

    no_company = _is_company_none(company)
    if no_company and OUTAGE_PATTERN.search(text) and _is_vague(issue, subject):
        return "escalated", "Escalated due to vague system-wide outage report without company context."

    if no_company and _is_vague(issue, subject):
        return "escalated", "Escalated because issue is too vague to route and company context is missing."

    return "replied", "Replied because issue is specific enough and does not match escalation rules."


def decide(issue: str, subject: str, company: str) -> Status:
    status, _ = _evaluate(issue, subject, company)
    return status


def get_reason(issue: str, subject: str, company: str) -> str:
    _, reason = _evaluate(issue, subject, company)
    return reason
