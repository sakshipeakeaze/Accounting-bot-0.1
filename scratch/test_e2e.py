"""Quick end-to-end sanity check. Run from project root."""
import os, sys
sys.path.insert(0, os.path.abspath("."))

print("=" * 60)
print("Step 1: Testing raw hybrid search...")
from src.server.mcp_server import search_knowledge
result = search_knowledge("revenue growth Q1 2024")
print(result[:600])
print("=" * 60)

print("Step 2: Testing financial ratio calculation...")
from src.server.mcp_server import calculate_financial_ratio
print(calculate_financial_ratio(10.4, 14.1, "Debt-to-Equity"))
print("=" * 60)

print("Step 3: Running the PydanticAI agent end-to-end...")
import asyncio
from src.agent.finance_agent import finance_agent

async def run():
    res = await finance_agent.run("What was Acme Corp's total revenue in Q1 2024?")
    print(res.response)

asyncio.run(run())
print("=" * 60)
print("All tests passed!")
