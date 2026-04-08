import asyncio
import sys
from app.services.market_service import market_service
from app.services.indian_market_service import indian_market_service

async def test():
    res1 = await indian_market_service.get_indian_indices()
    print("Indices:", res1)
    
    res2 = await market_service.get_indices()
    print("\nMarket Indices:", res2)

    res3 = await indian_market_service.get_combined_market_overview()
    print("\nCombined Overview keys:", list(res3.keys()))
    
if __name__ == "__main__":
    asyncio.run(test())
