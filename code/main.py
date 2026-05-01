from __future__ import annotations

import csv
import re
from pathlib import Path

from dotenv import load_dotenv

import agent
import classifier
import router
from logger import log as log_turn
from retriever import Retriever


ROOT_DIR = Path(__file__).resolve().parents[1]
SUPPORT_DIR_CANDIDATES = [ROOT_DIR / "support_issues", ROOT_DIR / "support_tickets"]
INPUT_FILENAME_CANDIDATES = ["support_issues.csv", "support_tickets.csv"]
OUTPUT_FILENAME = "output.csv"


def _resolve_support_dir() -> Path:
	for candidate in SUPPORT_DIR_CANDIDATES:
		if candidate.exists():
			return candidate
	return SUPPORT_DIR_CANDIDATES[-1]


def _resolve_input_path(support_dir: Path) -> Path:
	for filename in INPUT_FILENAME_CANDIDATES:
		candidate = support_dir / filename
		if candidate.exists():
			return candidate
	return support_dir / INPUT_FILENAME_CANDIDATES[0]


def _normalize_company(company: str | None) -> str | None:
	if company is None:
		return None

	normalized = company.strip()
	if not normalized or normalized.lower() == "none":
		return None

	return normalized


def _load_rows(input_path: Path) -> list[dict[str, str]]:
	with input_path.open("r", encoding="utf-8", newline="") as handle:
		reader = csv.DictReader(handle)
		return list(reader)


def _parse_agent_output(agent_output: object) -> tuple[str, str]:
	if isinstance(agent_output, dict):
		return str(agent_output.get("response", "")), str(agent_output.get("justification", ""))

	raw = str(agent_output or "")
	response_match = re.search(r'<response>(.*?)</response>', raw, re.DOTALL)
	justification_match = re.search(r'<justification>(.*?)</justification>', raw, re.DOTALL)

	response_text = response_match.group(1).strip() if response_match else ""
	justification_text = justification_match.group(1).strip() if justification_match else ""

	return response_text, justification_text


def main() -> None:
	load_dotenv(ROOT_DIR / ".env")

	support_dir = _resolve_support_dir()
	input_path = _resolve_input_path(support_dir)
	output_path = support_dir / OUTPUT_FILENAME

	rows = _load_rows(input_path)
	retriever = Retriever()
	output_rows: list[dict[str, str]] = []

	total = len(rows)
	for index, row in enumerate(rows, start=1):
		issue = (row.get("Issue") or "").strip()
		subject = (row.get("Subject") or "").strip()
		company = (row.get("Company") or "").strip()
		normalized_company = _normalize_company(company)
		domain = normalized_company.lower() if normalized_company is not None else None

		print(f"Processing ticket {index}/{total}...", flush=True)

		status = router.decide(issue, subject, company)
		query = f"{issue} {subject}"
		chunks = retriever.retrieve(query, domain)
		request_type = classifier.get_request_type(issue)
		product_area = classifier.get_product_area(issue, company, chunks)
		generated = agent.generate_response(
			issue=issue,
			subject=subject,
			company=company,
			status=status,
			request_type=request_type,
			product_area=product_area,
			retrieved_chunks=chunks,
		)

		response, justification = _parse_agent_output(generated)

		output_row = {
			"issue": issue,
			"subject": subject,
			"company": company,
			"response": response,
			"product_area": product_area,
			"status": status,
			"request_type": request_type,
			"justification": justification,
		}

		output_rows.append(output_row)
		log_turn(index, issue, output_row)

	with output_path.open("w", encoding="utf-8", newline="") as handle:
		fieldnames = [
			"issue",
			"subject",
			"company",
			"response",
			"product_area",
			"status",
			"request_type",
			"justification",
		]
		writer = csv.DictWriter(handle, fieldnames=fieldnames)
		writer.writeheader()
		writer.writerows(output_rows)

	relative_output = output_path.relative_to(ROOT_DIR)
	print(f"Done. Output written to {relative_output}")


if __name__ == "__main__":
	main()
