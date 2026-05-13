"""
PydanticAI Finance Agent.

Uses the MCP Server tools directly (clean, no subprocess needed for the Streamlit demo).
In a full production deploy, replace the direct imports with MCPServerStdio/HTTP.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from src.config import settings
# Import the tool functions directly from the MCP server module for reuse
from src.server.mcp_server import search_knowledge, calculate_financial_ratio

# ── Model ─────────────────────────────────────────────────────────────────────
model = GroqModel(
    model_name=settings.AGENT_MODEL,
    provider=GroqProvider(api_key=settings.GROQ_API_KEY),
)

# ── Agent definition ──────────────────────────────────────────────────────────
finance_agent = Agent(
    model,
    system_prompt=(
        "You are a professional Accounting and Finance Assistant for Peakvisory & Peakeaze Group. "
        "You have access to EXACTLY TWO tools: 'search_kb' and 'calculate_ratio'. Do not attempt to use any other tools. "
        "ALWAYS call the 'search_kb' tool first to find relevant data before answering any question. "
        "ALWAYS respond in clean, plain English text. "
        "NEVER output code, raw objects, JSON, XML, or any technical syntax in your response (like <function...> tags). "
        "Structure your answer in short paragraphs or simple numbered lists. "
        "Show financial calculations step-by-step in plain text. "
        "If the query is about specific company data (like pricing, SLAs, or policies) and the knowledge base does not contain the answer, state that you could not find it in the knowledge base. "
        "However, for general accounting, finance, or other non-company-specific questions (like 'What is a ledger?' or 'What is a quadrant in finance?'), feel free to use your general knowledge to answer, while still being professional and accurate. "
        "For real-time data like current gold prices or stock prices, explain that you do not have live internet access."
    ),
)

# ── Register tools ─────────────────────────────────────────────────────────────

@finance_agent.tool
def search_kb(ctx: RunContext[None], query: str) -> str:
    """
    Search the accounting and finance knowledge base.
    Always call this before answering financial questions.
    """
    return search_knowledge(query)


@finance_agent.tool
def calculate_ratio(
    ctx: RunContext[None],
    numerator: float,
    denominator: float,
    ratio_name: str,
) -> str:
    """Calculate a common financial ratio (e.g. Debt-to-Equity, Current Ratio)."""
    return calculate_financial_ratio(numerator, denominator, ratio_name)
