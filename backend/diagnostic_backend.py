import asyncio
from app.services.scraping_engine import scraping_engine
from app.services.kg_engine import kg_engine

async def main():
    print("--- Testing Scraping Engine (Direct) ---")
    news = await scraping_engine.google_news_search("Reliance Industries news", limit=3)
    print(f"News Results: {len(news)}")
    for n in news:
        print(f" - {n['title'][:50]}")
        
    print("\n--- Testing AI Mode (Direct) ---")
    ai = await scraping_engine.google_ai_mode("Reliance Industries CEO")
    print(f"AI Answer: {ai.get('answer', 'NONE')[:100]}")

    print("\n--- Testing KG Engine (Direct) ---")
    kg = await kg_engine.build_dynamic_graph("Indian Banking Sector")
    print(f"KG Nodes: {len(kg.get('nodes', []))}")
    print(f"KG Edges: {len(kg.get('edges', []))}")

if __name__ == "__main__":
    asyncio.run(main())
