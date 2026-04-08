import httpx
import asyncio
import os
from dotenv import load_dotenv

# Load keys from .env
load_dotenv()

KEYS_TO_TEST = [
    os.getenv("GOOGLE_AI_API_KEY"),
    "AIzaSyAvlzrDV3OirF5H7MXl_HdwtNl8BgS6Mg0", # From youtube_live_detector_enhanced.py
    "AIzaSyD-9nrtQx2V8X1Y7Z2A3B4C5D6E7F8G9H0"  # From background_data_service.py
]

# Channels to verify
CHANNELS = {
    "Aaj Tak": "https://www.youtube.com/@aajtak",
    "ABP News": "https://www.youtube.com/@abpnews",
    "Zee News": "https://www.youtube.com/@ZeeNews",
    "India TV": "https://www.youtube.com/@IndiaTV",
    "NDTV 24x7": "https://www.youtube.com/@ndtv",
    "CNN-News18": "https://www.youtube.com/@CNNnews18",
    "Republic World": "https://www.youtube.com/@RepublicWorld",
    "Times Now": "https://www.youtube.com/@TimesNow",
    "WION": "https://www.youtube.com/@WIONews",
    "CNBC TV18": "https://www.youtube.com/@cnbctv18india",
    "CNN": "https://www.youtube.com/@CNN",
    "BBC News": "https://www.youtube.com/@BBCNews",
    "Al Jazeera English": "https://www.youtube.com/@aljazeeraenglish"
}

async def test_key(key):
    if not key: return False
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=news&type=video&eventType=live&key={key}&maxResults=1"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            if res.status_code == 200:
                print(f"Key {key[:10]}... is VALID")
                return True
            else:
                print(f"Key {key[:10]}... is INVALID (Status: {res.status_code})")
                return False
        except Exception as e:
            print(f"Key {key[:10]}... error: {e}")
            return False

async def get_channel_id(handle_url, key):
    handle = handle_url.split("@")[-1].split("/")[0]
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={handle}&type=channel&key={key}&maxResults=1"
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url)
            data = res.json()
            if data.get("items"):
                channel_id = data["items"][0]["snippet"]["channelId"]
                title = data["items"][0]["snippet"]["title"]
                print(f"Found {title}: {channel_id}")
                return channel_id
        except: pass
    return None

async def main():
    print("Testing keys...")
    working_key = None
    for key in KEYS_TO_TEST:
        if await test_key(key):
            working_key = key
            break
    
    if not working_key:
        print("No working YouTube API key found!")
        return

    print(f"\nUsing key: {working_key[:10]}...")
    results = {}
    for name, url in CHANNELS.items():
        cid = await get_channel_id(url, working_key)
        if cid:
            results[name] = cid
    
    print("\nCorrect Channel IDs:")
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
