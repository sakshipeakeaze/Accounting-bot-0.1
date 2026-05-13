# Project Information: Smart Accounting RAG Agent

This document provides an overview of the current implementation, file structure, and planned next steps for the Peakvisory AI Assistant project.

## 🚀 Current Implementation

The project is a scalable, RAG-based accounting and finance agent utilizing advanced retrieval techniques.

### Key Features
*   **Hybrid Search**: Combines dense vector similarity (semantics) and sparse vector search (BM25 keyword match) using Qdrant.
*   **Contextual Retrieval**: Ingestion pipeline generates a brief context summary for each chunk to improve search precision.
*   **MCP-First Architecture**: Decouples agent logic into tools served via an MCP (Model Context Protocol) structure.
*   **Streamlit Chat Interface**: A user-friendly, dark-themed chat interface with suggestion chips and robust error handling.

---

## 📁 File Structure & Descriptions

### Core Application
*   **`app/main.py`**
    *   **Purpose**: The Streamlit frontend application.
    *   **Details**: Provides the chat UI, handles user input, executes the agent asynchronously, and extracts clean text responses while filtering out technical "gibberish" or raw tool calls.
*   **`src/agent/finance_agent.py`**
    *   **Purpose**: Defines the PydanticAI agent.
    *   **Details**: Configures the Groq model, sets the system prompt (enforcing clean text output), and registers tools by linking them to the MCP server functions.
*   **`src/server/mcp_server.py`**
    *   **Purpose**: The "Brain" and tool provider.
    *   **Details**: Initializes Qdrant and Embedding clients. Defines the `search_knowledge` tool (performing hybrid search and RRF fusion) and `calculate_financial_ratio`. Can be run as a standalone MCP server.
*   **`src/config.py`**
    *   **Purpose**: Configuration management.
    *   **Details**: Uses Pydantic Settings to load and validate environment variables from the `.env` file.

### Scripts
*   **`scripts/ingest.py`**
    *   **Purpose**: Data ingestion pipeline.
    *   **Details**: Reads Markdown files from the `knowledge/` directory, generates contextual summaries for chunks using Groq, creates dense and sparse embeddings, and upserts them to Qdrant.

### Knowledge Base
*   **`knowledge/entities/`**
    *   Contains the markdown files that serve as the ground truth for the agent.
    *   `accounting_fram.md`: Policies and standards.
    *   `coorporate_identity.md`: Vision, entities, and leadership.
    *   `generic_business_ops.md`: Marketing and admin services.
    *   `onboarding_and_sla.md`: SLAs and KYC requirements.
    *   `service_pricing_and_packages.md`: Tiered pricing details.
    *   `tech_stack_and_security.md`: Software and security standards.

---

## 🗺️ Next Steps (KB & Model Focus)

Based on the preference to focus on the knowledge base and model for now, here are the recommended next steps:

1.  **Expand the Knowledge Base**: Add more specific documents (e.g., sample reports, more detailed policy documents) to the `knowledge/` folder and run `py -3.13 scripts/ingest.py` to update the index.
2.  **Prompt Engineering**: Refine the system prompt in `finance_agent.py` to better handle edge cases or specific question types as they arise.
3.  **Chunking Optimization**: If answers are incomplete, we can adjust the chunk size or overlap in the `.env` file and re-ingest.
