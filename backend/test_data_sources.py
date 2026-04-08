#!/usr/bin/env python3
"""
Test script for AARAMBH data sources and API configuration
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_connectors():
    """Test all data source connectors"""
    print("🚀 Testing AARAMBH Data Sources Configuration")
    print("=" * 60)
    
    try:
        # Test PIB Connector
        from app.ingestion.connectors.pib_rss import pib_connector
        print("📰 Testing PIB RSS Connector...")
        pib_events = await pib_connector.fetch()
        print(f"   ✅ PIB: {len(pib_events)} events fetched")
        if pib_events:
            print(f"   📄 Sample: {pib_events[0].title[:80]}...")
        
        # Test GDELT Connector
        from app.ingestion.connectors.gdelt import gdelt_connector
        print("\n🌍 Testing GDELT Connector...")
        gdelt_events = await gdelt_connector.fetch()
        print(f"   ✅ GDELT: {len(gdelt_events)} events fetched")
        if gdelt_events:
            print(f"   📄 Sample: {gdelt_events[0].title[:80]}...")
        
        # Test World Bank Connector
        from app.ingestion.connectors.world_bank import world_bank_connector
        print("\n🏦 Testing World Bank Connector...")
        wb_events = await world_bank_connector.fetch()
        print(f"   ✅ World Bank: {len(wb_events)} events fetched")
        if wb_events:
            print(f"   📄 Sample: {wb_events[0].title[:80]}...")
        
        # Test MEA Connector
        from app.ingestion.connectors.mea_rss import mea_connector
        print("\n🎭 Testing MEA RSS Connector...")
        mea_events = await mea_connector.fetch()
        print(f"   ✅ MEA: {len(mea_events)} events fetched")
        if mea_events:
            print(f"   📄 Sample: {mea_events[0].title[:80]}...")
        
        # Test ACLED Connector
        from app.ingestion.connectors.acled import acled_connector
        print("\n⚔️ Testing ACLED Connector...")
        acled_events = await acled_connector.fetch()
        print(f"   ✅ ACLED: {len(acled_events)} events fetched")
        if acled_events:
            print(f"   📄 Sample: {acled_events[0].title[:80]}...")
        
        print("\n" + "=" * 60)
        print("✅ All connector tests completed successfully!")
        
        # Test Swarm Intelligence
        print("\n🤖 Testing Swarm Intelligence Engine...")
        from app.services.swarm_intelligence import swarm_intelligence
        print(f"   ✅ Swarm Engine: {len(swarm_intelligence.agents)} agents initialized")
        print(f"   🎯 Agent Types: {list(set([agent.role for agent in swarm_intelligence.agents[:5]]))}")
        
        # Test Configuration
        print("\n⚙️ Testing Configuration...")
        from app.config import settings
        print(f"   ✅ Kafka Servers: {settings.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"   ✅ Swarm Enabled: {settings.SWARM_ENGINE_ENABLED}")
        print(f"   ✅ Agent Count: {settings.AGENT_SIMULATION_COUNT}")
        
        print("\n🎉 AARAMBH Data Sources Setup Complete!")
        print("\nNext Steps:")
        print("1. Start backend: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("2. Test APIs: http://localhost:8000/docs")
        print("3. Start ingestion: POST /api/v1/ingestion/start")
        print("4. Run swarm simulation: POST /api/v1/swarm/simulate")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connectors())
