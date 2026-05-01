from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / "hackerrank_orchestrate" / "log.txt"


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).splitlines()).strip()


def log(ticket_id: int, issue: str, output_dict: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        f"[{timestamp}] Ticket {ticket_id}",
        f"Issue: {_stringify(issue)}",
    ]

    for key, value in output_dict.items():
        lines.append(f"{key}: {_stringify(value)}")

    lines.append("")
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
        handle.write("\n")