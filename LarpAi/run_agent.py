import sys
import os
import asyncio
import logging

# Ensure UTF-8 output encoding for Windows terminal compatibility
sys.stdout.reconfigure(encoding='utf-8')

from research_agent import LarpAgent

# Suppress verbose debug logs for clean terminal output
logging.basicConfig(level=logging.WARNING)


async def run_research(query: str, format_type: str = "FULL"):
    print("\n============================================================")
    print(" Larp AI Orchestrator")
    print("============================================================")
    print(f"Research Query: \"{query}\"\n")

    agent = LarpAgent()
    report = await agent.run(query, format_type=format_type)

    print("============================================================\n")
    print(report.markdown_content)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = "Compare electric vehicles vs hydrogen fuel cell vehicles"

    asyncio.run(run_research(user_query))
