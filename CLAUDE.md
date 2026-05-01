# HackerRank Orchestrate: Support Ticket Triage Agent

**Reference:** See [AGENTS.md](AGENTS.md) for mandatory challenge rules, logging requirements, and submission guidelines.

## Quick Context

You are building a **terminal-based support triage agent** for the HackerRank Orchestrate 24-hour hackathon. Your agent must classify and respond to multi-domain support tickets using **only the provided corpus** (no web calls, no hallucinations).

- **Input:** `support_tickets/support_tickets.csv` — rows with `Issue`, `Subject`, `Company`
- **Output:** `support_tickets/output.csv` — rows with `Status`, `Product_Area`, `Response`, `Justification`, `Request_Type`
- **Corpus:** `data/` contains support articles from HackerRank, Claude, and Visa help centers (~325 articles total)
- **Constraints:** Terminal-only, grounded responses, explicit escalation logic

---

## Corpus Structure

**Three product domains:**

1. **Claude** (`data/claude/`) — 321 articles
   - Categories: Account management, Features, API/Console, Billing, Troubleshooting, etc.
   - Entry: `data/claude/index.md` (table of contents with links to all articles)

2. **HackerRank** (`data/hackerrank/`) — Support topics for assessments, interviews, platform
   - Categories: General help, Settings, Interviews, Skill tests, Integrations, etc.
   - Entry: `data/hackerrank/index.md`

3. **Visa** (`data/visa/`) — Consumer and small-business payment support
   - Entry: `data/visa/index.md` and `data/visa/support.md`

**Key:** Each domain has an `index.md` that maps categories to individual article files. Articles are markdown files with Q&A content.

---

## Agent Design Recommendations

### Architecture
- **Retrieval:** Parse corpus `index.md` files to build a searchable map of topics/articles. Use BM25 or semantic embeddings for retrieval.
- **Classification:** Identify product domain (`HackerRank`, `Claude`, `Visa`) and map issue to a support category (e.g., "Billing", "Feature Request").
- **Reasoning:** Decide whether the ticket can be answered from the corpus (`replied`) or should be escalated (`escalated`).
- **Grounding:** Extract relevant quotes/references from articles. Avoid claims not in the corpus.
- **Safety:** Flag high-risk categories (billing disputes, fraud, account lockouts) for escalation.

### Key Decisions
- **What triggers `escalated`?**
  - Sensitive topics: fraud, account security, billing disputes
  - Out-of-scope: requests for undocumented features, external integrations
  - Insufficient corpus match: issue too vague or no relevant articles found
  
- **What triggers `replied`?**
  - Clear FAQ match: issue maps directly to an article
  - General guidance: ticket can be safely answered with corpus content
  - Escalation unlikely: low-risk, well-documented scenario

- **Product Area classification:**
  - Use corpus structure (categories from index.md) or domain-specific categories
  - Map ambiguous issues to the most relevant product area

### Request Type
- `product_issue` — Bug report, technical problem with a product
- `feature_request` — Request for new capability
- `bug` — Confirmed product defect
- `invalid` — Out of scope, spam, nonsensical

---

## Entry Point

**File:** `code/main.py`

Expected behavior:
```
python main.py
# Reads: support_tickets/support_tickets.csv
# Writes: support_tickets/output.csv
# Format: CSV with columns [Issue, Subject, Company, Response, Product_Area, Status, Request_Type, Justification]
```

### Implementation with Google Gemini

**API & Models:**
- Use `google-generativeai` Python package
- Available models: `gemini-2.5-pro` (most capable), `gemini-3-pro`, or `gemini-3-flash` (fast)
- API key from env var: `GEMINI_API_KEY` (never hardcode)

**Setup:**
1. Create `.env` file: `GEMINI_API_KEY=<your-key>`
2. Add to `requirements.txt`: `google-generativeai`
3. Load corpus index on startup
4. Use Gemini for LLM-powered classification, routing, and response generation

### Implementation Tips
1. **Load corpus:** Parse `data/{domain}/index.md` files to build a retrieval index on startup
2. **Process tickets:** For each row in `support_tickets.csv`:
   - Identify domain (use `Company` field; infer if `None`)
   - Retrieve relevant articles using corpus index
   - Use Gemini to classify issue and decide routing (via structured prompts or function calling)
   - Generate response (quote + synthesis) or escalation reason
3. **Output:** Write CSV with consistent formatting
4. **Determinism:** Use seeded randomness; pin dependencies in `requirements.txt`
5. **Grounding:** Pass relevant corpus excerpts in prompts to avoid hallucination; use Gemini's structured output for consistent JSON responses

---

## Development Workflow

- **Sample data:** `support_tickets/sample_support_tickets.csv` includes expected outputs for all 5 columns. Use this to validate your agent.
- **Test frequently:** Run your agent on the sample tickets, compare output structure and reasoning.
- **Logging:** Every user conversation turn is auto-logged to `$HOME/hackerrank_orchestrate/log.txt` (see AGENTS.md §2 & §5).
- **Documentation:** Add a `code/README.md` explaining your architecture, retrieval method, and how to run it.

---

## Safety & Escalation

**Never hallucinate.** If the corpus doesn't contain a direct answer:
- Provide general guidance (if safe)
- Or escalate with clear reasoning

**High-risk escalation triggers:**
- Billing/payment issues → escalate (fraud risk, financial responsibility)
- Account access/security → escalate (authentication, locked accounts)
- Data privacy questions → escalate (PII, GDPR, compliance)
- Undocumented features → escalate or respond "out of scope"
- Contradictory / ambiguous issues → escalate

**Safe to reply:**
- FAQ-style questions (well-documented product features)
- General how-to (usage guidance found in corpus)
- Troubleshooting steps (from help articles)

---

## Evaluation Criteria Summary

Your submission is scored on:

1. **Agent Design** — code in `code/` directory: architecture clarity, corpus usage, escalation logic, reproducibility
2. **AI Judge Interview** — 30 min: explain design trade-offs, failure modes, honesty about AI assistance
3. **Output CSV** — accuracy of `Status`, `Product_Area`, `Response`, `Justification`, `Request_Type` on the main dataset
4. **AI Fluency** — `log.txt` transcript: evidence you directed the AI, not blindly accepted output

See `evalutation_criteria.md` for full details.