import asyncio
from src.server.mcp_server import search_knowledge

async def test_search():
    print("Testing search for 'revenue growth'...")
    results = await search_knowledge("revenue growth")
    print("\nResults:")
    print(results)

if __name__ == "__main__":
    asyncio.run(test_search())
