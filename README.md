# GLEAN

**AI-Native OSINT.** Gather public information bit by bit, reason about it, and produce a cited summary.

GLEAN orchestrates a set of open-source-intelligence collectors with an LLM 
(OpenAI `gpt-5.2`). The model plans which collectors to run, reasons over the
results, and writes a structured report where **every claim links to a source**.

Two modes:

- **Company mode** — due diligence before you accept a job or sign with a
  counterparty. Funding, news, leadership, public sentiment, tech footprint.
- **Person mode** — a public-footprint snapshot to decide whether to trust,
  hire, or simply get to know someone.

---

## ⚠️ Ethics & lawful use — read before running

GLEAN is built for **legitimate, lawful, public-source** intelligence. The
guardrails below are enforced in code (`glean/ethics.py`), not just documented.

1. **Public sources only.** No breach-dump credentials, no paywalled scraping,
   no authentication bypass. Collectors respect site terms and `robots.txt`.
2. **Purpose-limited.** Person mode **requires** a stated lawful purpose
   (`--purpose`). Queries phrased as stalking, locating someone who is hiding,
   harassment, or targeting a minor are refused.
3. **No real-time tracking.** GLEAN takes a snapshot. It does not monitor a
   person continuously and does not resolve live location.
4. **Audit log.** Every query and target is logged locally to `glean.db` for
   accountability.
5. **Confidence + caveats.** The report marks low-confidence and unverified
   claims. Identity matches are never asserted as fact.
6. **Public ≠ permission.** A finding being public does not make it lawful or
   ethical to act on. You are responsible for your use of this tool.

Do not use GLEAN to harass, intimidate, discriminate, or violate privacy law
(GDPR, CCPA, FCRA, etc.). FCRA note: GLEAN is **not** a consumer reporting
agency and its output must not be used for employment, credit, or housing
eligibility decisions covered by the FCRA.

---

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then add your OPENAI_API_KEY
```

## Usage

```bash
# Company due diligence
python -m glean.cli "Acme Robotics" --mode company

# Person snapshot
python -m glean.cli "Jane Q. Public" --mode person --output report.md

glean "Some Person" --mode person
```

## Configuration (environment variables)

| Variable          | Required | Purpose                                  |
| ----------------- | -------- | ---------------------------------------- |
| `OPENAI_API_KEY`  | yes      | OpenAI API access                        |
| `OPENAI_MODEL`    | no       | Override model (default `gpt-5.2`)       |
| `GITHUB_TOKEN`    | no       | Higher GitHub API rate limits            |
| `GLEAN_DB`        | no       | Audit DB path (default `glean.db`)       |
| `GLEAN_MAX_STEPS` | no       | Max agent tool-call iterations (default 12) |

## Architecture

```
query (entity + mode + purpose)
   -> ethics gate (refuse disallowed targets)
   -> planner (gpt-5.2, tool-use loop)
        collectors: web_search, github, whois  [pluggable]
   -> synthesizer (structured JSON: summary, findings, red_flags, sources)
   -> markdown report
   -> audit log
```

Collectors are pluggable: add a module to `glean/collectors/` exposing a `TOOL`
schema and a `run()` function, register it, done.

## License

MIT. See [LICENSE](LICENSE).

<!-- more collectors: news API, court records, Glassdoor sentiment, LinkedIn-public -->

<br>
