# Support Ticket Agent

Run the agent from this directory with:

```bash
python main.py
```

The script reads ticket rows from `../support_issues/support_issues.csv` when that folder exists, otherwise it falls back to `../support_tickets/support_tickets.csv`, then writes the completed `output.csv` back to the same folder.

Set `GEMINI_API_KEY` in `.env` before running.