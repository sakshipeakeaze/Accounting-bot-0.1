"""
MCP Server for the Accounting RAG Agent.
Exposes two tools:
  - search_knowledge : Hybrid (dense + sparse) search over the Qdrant knowledge base
  - calculate_financial_ratio : Simple financial ratio calculator

This module is the single reusable "brain" of the project.
It can be run as a standalone MCP server (stdio) or imported by the PydanticAI agent.
"""
import os
import sys

# Ensure the project root is on the path when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mcp.server.fastmcp import FastMCP
from qdrant_client import QdrantClient, models
from fastembed import TextEmbedding, SparseTextEmbedding
from src.config import settings

# ── Initialise once at import time ────────────────────────────────────────────
mcp = FastMCP("AccountingAgent")
qdrant = QdrantClient(url=settings.QDRANT_URL)
dense_model = TextEmbedding(model_name=settings.DENSE_MODEL)
sparse_model = SparseTextEmbedding(model_name=settings.SPARSE_MODEL)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _reciprocal_rank_fusion(dense_hits, sparse_hits, k: int = 60) -> list:
    """
    Combine two ranked lists using Reciprocal Rank Fusion.
    Each hit's final score = sum of 1/(rank + k) across all lists it appears in.
    """
    scores: dict = {}
    all_hits: dict = {}

    for rank, hit in enumerate(dense_hits):
        scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (rank + k)
        all_hits[hit.id] = hit

    for rank, hit in enumerate(sparse_hits):
        scores[hit.id] = scores.get(hit.id, 0.0) + 1.0 / (rank + k)
        all_hits[hit.id] = hit

    sorted_ids = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
    return [all_hits[i] for i in sorted_ids[: settings.RERANK_TOP_K]]


# ── MCP Tools ─────────────────────────────────────────────────────────────────

@mcp.tool()
def search_knowledge(query: str) -> str:
    """
    Search the accounting and finance knowledge base using hybrid search.
    Use this tool for EVERY question about company financials, policies, or records.

    Args:
        query: The natural language question or search phrase.

    Returns:
        Formatted string of the most relevant document chunks.
    """
    # 1. Embed the query
    query_dense = list(dense_model.embed([query]))[0].tolist()
    sparse_obj = list(sparse_model.embed([query]))[0]
    query_sparse = models.SparseVector(
        indices=sparse_obj.indices.tolist(),
        values=sparse_obj.values.tolist(),
    )

    # 2. Hybrid search using the new query_points API (qdrant-client >= 1.9)
    dense_results = qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_dense,
        using="dense",
        limit=settings.HYBRID_TOP_K,
    ).points

    sparse_results = qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_sparse,
        using="sparse",
        limit=settings.HYBRID_TOP_K,
    ).points

    # 3. Fuse with RRF
    fused = _reciprocal_rank_fusion(dense_results, sparse_results)

    if not fused:
        return "No relevant information found in the knowledge base."

    # 4. Format output
    sections = []
    for hit in fused:
        payload = hit.payload or {}
        source = payload.get("source", "Unknown")
        context = payload.get("context", "")
        text = payload.get("text", "")
        sections.append(f"Source: {source}\nContext: {context}\nContent:\n{text}\n{'='*60}")

    return "\n\n".join(sections)


@mcp.tool()
def calculate_financial_ratio(numerator: float, denominator: float, ratio_name: str) -> str:
    """
    Calculate a named financial ratio.

    Args:
        numerator: The top number of the ratio.
        denominator: The bottom number of the ratio.
        ratio_name: A human-readable label, e.g. 'Debt-to-Equity'.

    Returns:
        A formatted result string.
    """
    if denominator == 0:
        return f"Cannot calculate '{ratio_name}': denominator is zero."
    return f"{ratio_name} = {numerator / denominator:.4f}"


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Run the MCP server over stdio (for use with Claude Desktop, Cursor, etc.)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
