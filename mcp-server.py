# mcp-server.py
# Run with:  uv run mcp-server.py
# Discovery URL:  http://127.0.0.1:8001/sse   (or next free port)

import logging
import os
import socket
import sys
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any

import requests
from dotenv import load_dotenv
from fastmcp import FastMCP
from simple_salesforce import Salesforce

load_dotenv()
API_VERSION = os.getenv("SF_API_VERSION", "60.0")

# ────────── logging ──────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger("sfmcp")


def _log_response(resp: requests.Response, *_, **__) -> None:
    body = resp.text
    if len(body) > 1_000:
        body = body[:1_000] + "...[truncated]"
    logger.debug("SFDC ⇦ %s %s → %s\n%s",
                 resp.request.method, resp.url, resp.status_code, body)


# ────────── helper ──────────
def login() -> Salesforce:
    """Return an authenticated `simple_salesforce.Salesforce` session."""
    token_resp = requests.post(
        os.getenv("SF_TOKEN_URL"),
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("SF_CLIENT_ID"),
            "client_secret": os.getenv("SF_CLIENT_SECRET"),
        },
        timeout=30,
    )
    token_resp.raise_for_status()
    tok = token_resp.json()
    logger.info("🔑 Got access token for %s", tok["instance_url"])

    sess = requests.Session()
    sess.hooks["response"] = [_log_response]

    return Salesforce(
        instance_url=tok["instance_url"],
        session_id=tok["access_token"],
        version=API_VERSION,
        session=sess,
    )


# ────────── lifespan ──────────
@asynccontextmanager
async def sf_lifespan(_server: FastMCP) -> AsyncIterator[dict]:
    # one login for the whole server lifetime
    globals()["_salesforce"] = login()
    try:
        yield {"sf": _salesforce}
    finally:
        logger.info("✅ Salesforce MCP server shutting down")


mcp = FastMCP("🚀 Salesforce MCP Server 🚀", lifespan=sf_lifespan)

# ────────── resources & tools ──────────
@mcp.resource("record://{sobject}/{record_id}")
def get_record(sobject: str, record_id: str) -> dict[str, Any]:
    """Return a full JSON record."""
    return _salesforce.__getattr__(sobject).get(record_id)


@mcp.tool(name="salesforce_query")
def salesforce_query(soql: str) -> list[dict[str, Any]]:
    """Run a SOQL query.  Example: `SELECT Id, Name FROM Account LIMIT 3`"""
    print(f"Salesforce READ: {soql}")
    return _salesforce.query_all(soql)["records"]


@mcp.tool(name="salesforce_create")
def salesforce_create(sobject: str, payload: dict[str, Any]) -> str:
    """Create a new record and return its Id."""
    print(f"Salesforce CREATE: {sobject}")
    print(f"Salesforce CREATE: {payload}")
    return _salesforce.__getattr__(sobject).create(payload)["id"]


@mcp.tool(name="salesforce_update")
def salesforce_update(
    sobject: str,
    record_id: str,
    payload: dict[str, Any],
) -> bool:
    """Update an existing record; returns True on success."""
    print(f"Salesforce UPDATE: {sobject}")
    print(f"Salesforce UPDATE: {record_id}")
    print(f"Salesforce UPDATE: {payload}")
    _salesforce.__getattr__(sobject).update(record_id, payload)
    return True


# ────────── launch ──────────
if __name__ == "__main__":
    port = 8001
    for _ in range(5):                # find a free port up to 8005
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
            break
        except OSError:
            logger.warning("Port %s in use – trying %s", port, port + 1)
            port += 1
    else:
        logger.error("No free port found in range 8001-8005 – aborting.")
        sys.exit(1)

    logger.info("Starting MCP server on port %s", port)
    mcp.run(transport="sse", host="127.0.0.1", port=port)
