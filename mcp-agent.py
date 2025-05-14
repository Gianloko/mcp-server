import asyncio
import os
import shutil
import subprocess
import time
from typing import Any

from agents import Agent, Runner, gen_trace_id, trace
from agents.mcp import MCPServer, MCPServerSse
from agents.model_settings import ModelSettings


async def run(mcp_server: MCPServer):
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to answer the questions.",
        mcp_servers=[mcp_server],
        model_settings=ModelSettings(tool_choice="required"),
    )

    # Use the `add` tool to add two numbers
    message = """
                Execute these actions in order: 
                    0) Read 10 Leads
                    1) Update lead 00QgL00000020fQUAQ – set LastName to "MCP Agent Action"
              """

    print(f"Initial user prompt: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(f"Result: {result.final_output}")

async def main():
    async with MCPServerSse(
        name="Salesforce MCP Server",
        params={
            "url": "http://127.0.0.1:8001/sse",
        },
    ) as server:
        trace_id = gen_trace_id()
        with trace(workflow_name="Salesforce MCP Server", trace_id=trace_id):
            print(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}\n")
            await run(server)


if __name__ == "__main__":
    # Let's make sure the user has uv installed
    if not shutil.which("uv"):
        raise RuntimeError(
            "uv is not installed. Please install it: https://docs.astral.sh/uv/getting-started/installation/"
        )

    # We'll run the SSE server in a subprocess. Usually this would be a remote server, but for this
    # demo, we'll run it locally at http://127.0.0.1:8001/sse
    process: subprocess.Popen[Any] | None = None
    try:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        server_file = os.path.join(this_dir, "mcp-server.py")

        # Run `uv run server.py` to start the SSE server
        process = subprocess.Popen(["uv", "run", server_file])
        # Give it 3 seconds to start
        time.sleep(3)

        print("SSE server started. Running example...\n\n")
    except Exception as e:
        print(f"Error starting SSE server: {e}")
        exit(1)

    try:
        asyncio.run(main())
    finally:
        if process:
            process.terminate()
