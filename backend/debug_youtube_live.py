import httpx
import asyncio

API_KEY = "AIzaSyAvlzrDV3OirF5H7MXl_HdwtNl8BgS6Mg0"

TEST_CHANNELS = [
    {"name": "Aaj Tak", "id": "UCZFMm1mW0Z81r3j3rN5cA"},
    {"name": "CNN", "id": "UCupvZG-5koHEi_75aLxfV0A"},
    {"name": "BBC News", "id": "UCK8sQmJBp8GCxrOtXWBpyEA"}
]

async def debug_search(name, channel_id):
    print(f"\n--- Testing {name} ({channel_id}) ---")
    
    # 1. Standard search (what code uses)
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "eventType": "live",
        "type": "video",
        "key": API_KEY,
        "maxResults": 1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params)
            print(f"Status: {res.status_code}")
            data = res.json()
            if data.get("items"):
                print(f"✅ Found Live Video: {data['items'][0]['id']['videoId']}")
            else:
                print("❌ No Live Video found with standard search")
                print(f"Raw Response: {data}")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    for chan in TEST_CHANNELS:
        await debug_search(chan["name"], chan["id"])

if __name__ == "__main__":
    asyncio.run(main())
