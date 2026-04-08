import httpx
import asyncio
import os
import re
from dotenv import load_dotenv

load_dotenv()

# Use the key the user insisted on
API_KEY = "AIzaSyAvlzrDV3OirF5H7MXl_HdwtNl8BgS6Mg0"

TEST_CHANNELS = [
    {"name": "Aaj Tak", "id": "UCZFMm1mW0Z81r3j3rN5cA"},
    {"name": "CNN", "id": "UCupvZG-5koHEi_75aLxfV0A"},
    {"name": "BBC News", "id": "UCK8sQmJBp8GCxrOtXWBpyEA"}
]

async def test_api_call(name, cid):
    print(f"\n--- Testing API for {name} ({cid}) ---")
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": cid,
        "eventType": "live",
        "type": "video",
        "key": API_KEY,
        "maxResults": 1
    }
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params)
            print(f"API Status: {res.status_code}")
            if res.status_code == 200:
                print("API Success!")
            else:
                print(f"API Failure: {res.text[:200]}")
        except Exception as e:
            print(f"API Error: {e}")

async def test_scrape(name, cid):
    print(f"--- Testing Scrape for {name} ---")
    url = f"https://www.youtube.com/channel/{cid}/live"
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = await client.get(url, headers=headers)
            content = res.text
            is_live = '"isLive":true' in content
            video_id_match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', content)
            video_id = video_id_match.group(1) if video_id_match else None
            
            if is_live and video_id:
                print(f"Scrape Success! Live: {video_id}")
            else:
                print(f"Scrape: Not Live (is_live={is_live})")
        except Exception as e:
            print(f"Scrape Error: {e}")

async def main():
    for chan in TEST_CHANNELS:
        await test_api_call(chan["name"], chan["id"])
        await test_scrape(chan["name"], chan["id"])

if __name__ == "__main__":
    asyncio.run(main())
