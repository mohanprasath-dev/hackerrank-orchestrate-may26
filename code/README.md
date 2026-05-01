HackerRank Orchestrate — Agent Code README
=========================================

Architecture (ASCII)
--------------------

  +-------------+      +-------------+      +-------------+      +-----------+
  | support_tix | ---> |   retriever  | ---> |   agent /    | ---> |  Gemini   |
  |  CSV input  |      | (TF-IDF idx) |      |  generator   |      |  (LLM)    |
  +-------------+      +-------------+      +-------------+      +-----------+
        |                     ^  \                 |
        v                     |   \                v
  +-------------+             |    +----------+  +----------------+
  | classifier  |-------------+----| router   |--| output CSV      |
  | (type/area) |                  +----------+  +----------------+
  +-------------+

Module Responsibilities
-----------------------
- `classifier.py`: Classifies `Issue` into `request_type` (product_issue, feature_request, bug, invalid)
  and maps to `product_area`. Contains specific handling for team/employee management (now classified
  as `product_issue`).
- `retriever.py`: Loads Markdown corpus, chunks into paragraphs, builds TF-IDF matrix and retrieves
  nearest chunks by cosine similarity. Boosts troubleshooting chunks for Claude when queries match
  error patterns (e.g., "stopped working"). Returns `text`, `source_file`, and `score`.
- `agent.py`: Builds a grounded prompt that includes top retrieved excerpts and the top chunk's
  `retrieval_score`. Calls the Gemini model to generate a structured XML reply and justification.
- `router.py` / `main.py`: Orchestrate pipeline (read tickets, call classifier, retrieve, decide
  escalation, write `support_tickets/output.csv`).
- `logger.py`: Simple logging utilities and mandatory contest log handling (see AGENTS.md).

Escalation Trigger List
-----------------------
- Billing/payment disputes or charge-related questions
- Account access / authentication / locked accounts / credential compromise
- Fraud, data breach, or privacy/PII exposure requests
- Requests that are vague or out-of-scope for the corpus (no high-confidence retrieval)
- Legal / compliance / contract questions

Retrieval Approach
------------------
- Corpus is parsed into paragraph-sized chunks (min length threshold).
- TF-IDF vectorizer indexes chunks at startup (`sklearn.TfidfVectorizer`).
- Retrieval uses cosine similarity between query vector and chunk matrix; top chunks (with
  `score`) are returned. For Claude troubleshooting queries (error-like phrasing), chunks under
  `data/claude/claude/troubleshooting/` are boosted/prepended to results to prioritize troubleshooting docs.

Design Tradeoffs: TF-IDF vs Embeddings
-------------------------------------
- TF-IDF (current):
  - Pros: deterministic, fast, cheap (no external API), interpretable scores (cosine over TF-IDF),
    easy to reproduce for evaluation.
  - Cons: Limited semantic generalization; synonyms or paraphrases may be missed.
- Embeddings (semantic):
  - Pros: Better semantic matching, handles paraphrases and intent, often higher recall.
  - Cons: Requires embedding model and compute (or API), introduces nondeterminism unless seeded,
    and needs extra infra (vector DB) for scale.

Why TF-IDF here: The hackathon constraints emphasize determinism, reproducibility, and on-disk
corpus-only operation, so TF-IDF is a pragmatic choice.

How to Run (local)
-------------------
1. Create a virtualenv and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Set the Gemini API key (optional for dry-run; required for full generation):

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

3. Run the main pipeline:

```powershell
python code/main.py
```

Outputs:
- `support_tickets/output.csv` will be generated/updated with columns including `Response`, `Justification`,
  `Status`, `Product_Area`, `Request_Type`.

Environment / Setup
-------------------
- `GEMINI_API_KEY` — Gemini/Google generative API key if you want LLM responses. If not set, the
  agent will raise an error at generation time.
- Python 3.10+ recommended. Dependencies listed in `requirements.txt`.

Known Limitations
-----------------
- TF-IDF can miss semantically-relevant articles that use different wording.
- The justification relies on the model to echo the instructed `Retrieved with confidence` string;
  post-processing may be added to enforce exact formatting.
- Boosting is heuristic: it prepends troubleshooting docs for Claude for a few trigger phrases only.
  This may miss other manifestations of the same problem.
- No rate-limiting / batching when sending many queries to Gemini; monitor API usage when running at scale.

If you want, I can add a small unit test to validate the new team-member classification and the Claude
troubleshooting boosting behavior.
# Support Ticket Agent

Run the agent from this directory with:

```bash
python main.py
```

The script reads ticket rows from `../support_issues/support_issues.csv` when that folder exists, otherwise it falls back to `../support_tickets/support_tickets.csv`, then writes the completed `output.csv` back to the same folder.

Set `GEMINI_API_KEY` in `.env` before running.