# https://modelcontextprotocol.io/docs/concepts/tools --> documentation
import os, requests
from dotenv import load_dotenv
from simple_salesforce import Salesforce
from contextlib import asynccontextmanager          # NEW
from collections.abc import AsyncIterator           # NEW
from fastmcp import FastMCP, Context

load_dotenv()

# ── helper ───────────────────────────────────────────────────────────────
def login() -> Salesforce:
    """OAuth client-credentials → Salesforce session"""
    resp = requests.post(
        os.getenv("SF_TOKEN_URL"),
        data={
            "grant_type": "client_credentials",
            "client_id": os.getenv("SF_CLIENT_ID"),
            "client_secret": os.getenv("SF_CLIENT_SECRET"),
        },
        timeout=30,
    )
    resp.raise_for_status()
    tok = resp.json()
    return Salesforce(
        instance_url=tok["instance_url"],
        session_id=tok["access_token"],
        version=os.getenv("SF_API_VERSION", "60.0"),
    )

# ── lifecycle hook (replaces @mcp.lifespan) ──────────────────────────────
@asynccontextmanager
async def sf_lifespan(_server: FastMCP) -> AsyncIterator[dict]:
    sf = login()                 # start-up
    try:
        yield {"sf": sf}         # handlers get it via ctx.request_context.lifespan_context["sf"]
    finally:
        pass                     # tear-down if you need one

# create the server **with** the lifespan
mcp = FastMCP("Local Salesforce MCP", lifespan=sf_lifespan)

# ── resources & tools stay exactly the same ──────────────────────────────
@mcp.resource("record://{sobject}/{record_id}")
def get_record(sobject: str, record_id: str, ctx: Context) -> dict:
    sf = ctx.request_context.lifespan_context["sf"]
    return sf.__getattr__(sobject).get(record_id)

@mcp.tool(name="salesforce_query")
def soql(soql: str, ctx: Context) -> list[dict]:
    sf = ctx.request_context.lifespan_context["sf"]
    print(sf.query_all(soql)["records"])
    return sf.query_all(soql)["records"]

@mcp.tool(name="salesforce_create")
def create(ctx: Context, sobject: str, payload: dict) -> str:
    sf = ctx.request_context.lifespan_context["sf"]
    return sf.__getattr__(sobject).create(payload)["id"]

@mcp.tool(name="salesforce_update")
def update(ctx: Context, sobject: str, record_id: str, payload: dict) -> bool:
    sf = ctx.request_context.lifespan_context["sf"]
    return sf.__getattr__(sobject).update(record_id, payload)

if __name__ == "__main__":
    mcp.run(transport="sse")