# Salesforce MCP Demo

This repository shows **end‑to‑end plumbing between a Salesforce org and an LLM agent** using the [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol/spec).

* **`server.py`** — a FastMCP server running on *localhost* that exposes core Salesforce REST operations as MCP *tools* and *resources*.
* **`agent.py`** — a GPT‑4‑powered assistant that autodiscovers those tools (via SSE or streamable‑HTTP) and calls them when needed.

---

\## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Folder layout](#folder-layout)
3. [Salesforce Connected‑App setup](#salesforce-connected-app-setup)
4. [Environment variables](#environment-variables)
5. [Quick start](#quick-start)
6. [Testing the server](#testing-the-server)
7. [Troubleshooting](#troubleshooting)
8. [Deploying to production](#deploying-to-production)
9. [License](#license)

---

\## Prerequisites

| Tool / account                       | Why you need it                                          |
| ------------------------------------ | -------------------------------------------------------- |
| **Python 3.11 +**                    | Languages features & wheels for FastMCP / OpenAI Agents  |
| **Salesforce org** (prod or sandbox) | Where the MCP server will read/write data                |
| **OpenAI account & API key**         | The agent runs on GPT‑4‑o or any functions‑capable model |
| *(Optional)* **`uv`**                | Ultra‑fast Python package manager (can replace `pip`)    |

---

\## Folder layout

```
salesforce-mcp-demo/
├── server.py            # FastMCP server (localhost)
├── agent.py             # GPT‑4o agent
├── requirements.txt     # Python deps
├── .env.example         # copy → .env, add secrets
└── README.md            # this doc
```

---

\## Salesforce Connected‑App setup

1. **Setup → Apps → App Manager → New Connected App**
2. **OAuth settings**

   * Enable **OAuth 2.0** & choose **Client Credentials** (or JWT Bearer).
   * Add the **`api`** scope.
3. Click **Save**, then copy the *Consumer Key* & *Consumer Secret*.
4. Under *Manage → Edit Policies*

   * *Permitted Users* → **Admin approved users are pre‑authorized**
   * Assign a locked‑down **Integration User** permission set.

> 🛡️ **Least‑privilege matters.** Give the Integration User access only to the objects & fields you want the LLM to touch.

---

\## Environment variables
Create `.env` from the template and fill the blanks:

```dotenv
# ── Salesforce ───────────────────────────────
SF_CLIENT_ID=
SF_CLIENT_SECRET=
SF_TOKEN_URL=https://login.salesforce.com/services/oauth2/token   # sandbox? use https://test.salesforce.com/...
SF_API_VERSION=60.0

# ── OpenAI ───────────────────────────────────
OPENAI_API_KEY=sk‑...
OPENAI_MODEL=gpt-4o-mini      # any model that supports function calling
```

---

\## Quick start

```bash
# 1 · clone & enter folder
$ git clone https://github.com/your‑org/salesforce‑mcp‑demo.git
$ cd salesforce‑mcp‑demo

# 2 · create / activate virtual‑env
$ python -m venv .venv && source .venv/bin/activate   # PowerShell: .\.venv\Scripts\activate

# 3 · install deps (pip or uv)
$ pip install -r requirements.txt
#  or : uv pip install -r requirements.txt

# 4 · copy env file & add secrets
$ cp .env.example .env && nano .env

# 5 · start the MCP client (this will start also mcp-server as a subprocess
$ py mcp-agent.py
```

If everything is wired up you’ll see lines like:

```
=== Agent reply ===
Here are some Leads:

1. **Bertha Boxer**
   - Company: Farmers Coop. of Florida
   - Status: Working - Contacted

2. **Phyllis Cotton**
   - Company: Abbott Insurance
   - Status: Open - Not Contacted

3. **Jeff Glimpse**
   - Company: Jackson Controls
   - Status: Open - Not Contacted

4. **Mike Braund**
   - Company: Metropolitan Health Services
   - Status: Open - Not Contacted

5. **Patricia Feager**
   - Company: International Shipping Co.
   - Status: Working - Contacted
```

---

\## Deploying to production

1. **Dockerise** (see commented `Dockerfile` in repo) and push to Render / Fly.io / Cloud Run.
2. **Front with API Gateway** (NGINX, AWS ALB, Cloud Armor) for TLS, rate‑limits, WAF.
3. **Rotate tokens** — switch to OAuth 2.0 JWT Bearer or client‑credential flow with short‑lived tokens.
4. **Observability** — log every `tool.invoke` to Salesforce Event Monitoring or external SIEM.

---

\## License
MIT © 2025 Your Name / Your Company
